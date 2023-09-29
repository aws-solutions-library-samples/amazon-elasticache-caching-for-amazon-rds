# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import logging
from aws_cdk import (
    CfnOutput,
    CfnTag,
    # Duration,
    RemovalPolicy,
    SecretValue,
    Stack,
    aws_ec2 as ec2,
    aws_elasticache as elasticache,
    aws_iam as iam,
    aws_rds as rds,
    aws_s3 as s3,
    aws_secretsmanager as secrets_manager,
)
from constructs import Construct
from rich import print
logging.basicConfig()


SSH_PORT=22
HTTP_PORT=80
MYSQL_PORT=3306
REDIS_PORT=6379
EC2_CLIENTS=1
ELASTICACHE_NODE_TYPE="cache.m6g.xlarge"


class RdbmsCacheStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stack_prefix = f"B2G-"
        key_name = self.node.try_get_context('keyName')


        # Network infrastructure ==================================================================

        # Cretae VPC
        use_default_vpc = self.node.try_get_context('useDefaultVpc') == 'true'
        if use_default_vpc:
            vpc = ec2.Vpc.from_lookup(self, 'DefaultVPC', is_default=True)
        else:
            vpc = ec2.Vpc(self, f"{stack_prefix}VPC", max_azs=2, nat_gateways=1)

        # Create Security Group for EC2
        ec2_security_group = ec2.SecurityGroup(self, f"{stack_prefix}EC2-SG", vpc=vpc, description="Allow SSH Access", allow_all_outbound=True)

        # NOTE: The following is a security risk, please adjust appropietly
        ec2_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(), 
            connection=ec2.Port.tcp(SSH_PORT), 
            description="Allow SSH access fron anywhere")
        
        ec2_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(), 
            connection=ec2.Port.tcp(HTTP_PORT), 
            description="Allow HTTP access fron anywhere")
        
        # Unnecessary rules
        # ec2_security_group.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(), 
        #     connection=ec2.Port.tcp(MYSQL_PORT), 
        #     description="Allow MySQL access fron anywhere")
        
        # ec2_security_group.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(), 
        #     connection=ec2.Port.tcp(REDIS_PORT), 
        #     description="Allow Redis access fron anywhere")
        

        # Create RDS Database =====================================================================

        # Create a Security Group for RDS
        rds_security_group = ec2.SecurityGroup(self, f"{stack_prefix}RDS-SG", vpc=vpc, description="Allow MySQL access", allow_all_outbound=True)

        rds_security_group.add_ingress_rule(
            peer=ec2_security_group,
            connection=ec2.Port.tcp(MYSQL_PORT),
            description="Allow MySQL access from EC2 Security Group")
        
        # Cretae RDS MySQL Instance
        rds_mysql = rds.DatabaseInstance(
            self, f"{stack_prefix}RDS-MySQL",
            allocated_storage=100,
            database_name="airportdb",
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_33),
            vpc=vpc,
            security_groups=[rds_security_group],
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.M7G, ec2.InstanceSize.XLARGE),
            removal_policy=RemovalPolicy.DESTROY,
            multi_az=True,
            deletion_protection=True,
            iam_authentication=True,
            storage_encrypted=True,
            publicly_accessible=False
        )


        # Create ElastiCache Cluster ==============================================================

        # Get the list of private subnets in the VPC
        private_subnet_ids = [prsn.subnet_id for prsn in vpc.private_subnets]

        # Create an ElastiCache Subnet Group
        elasticache_subnet_group = elasticache.CfnSubnetGroup(
            scope=self, 
            id=f"{stack_prefix}EC-SNG",
            description="ElastiCache Subnet Group",
            subnet_ids=private_subnet_ids
        )

        # Create an Elasticache security group
        elasticache_security_group = ec2.SecurityGroup(scope=self, id="elasticache-redis-sg", vpc=vpc, allow_all_outbound=True)

        elasticache_security_group.add_ingress_rule(
            peer=ec2_security_group,
            description="Allow Redis connection",
            connection=ec2.Port.tcp(REDIS_PORT)
        )

        # Create an ElastiCache cluster mode enabled
        elasticache_cme = elasticache.CfnReplicationGroup(
            scope=self, 
            id=f"{stack_prefix}EC-Redis-CME",
            replication_group_description="ElastiCache Redis Cluster Mode Enabled",
            at_rest_encryption_enabled=True,
            automatic_failover_enabled=True,
            cache_node_type=ELASTICACHE_NODE_TYPE,
            cache_subnet_group_name=elasticache_subnet_group.ref,
            data_tiering_enabled=False,
            engine="redis",
            engine_version="7.0",
            multi_az_enabled=True,
            num_node_groups=2,          # Number of shards
            port=REDIS_PORT,
            replicas_per_node_group=1,  # Number of read replica nodes per shard
            security_group_ids=[elasticache_security_group.security_group_id],
            tags=[CfnTag(
                key="stack",
                value=stack_prefix
            )],
            transit_encryption_enabled=True
        )
        logging.debug(elasticache_cme)


        # Create S3 Bucket ========================================================================

        bucket = s3.Bucket(
            self, f"{stack_prefix}S3-Bucket",
            removal_policy=RemovalPolicy.DESTROY
        )


        # Create EC2 Resources ====================================================================

        # Create EC2 role
        role = iam.Role(
            self, f"{stack_prefix}EC2-Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )

        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")) 
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSCloudFormationReadOnlyAccess"))

        # The following inline policy makes sure we allow only retrieving the secret value, provided the secret is already known. 
        # It does not allow listing of all secrets.
        role.attach_inline_policy(iam.Policy(self, "secret-read-only",  
            statements=[iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=["arn:aws:secretsmanager:*"],
                effect=iam.Effect.ALLOW
            )]
        ))

        bucket.grant_read_write(role)

        # AMI definition for EC2 instances
        amazon_linux = ec2.MachineImage.latest_amazon_linux2(
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
        )

        with open("./infrastructure/user_data.sh") as file:
            user_data = file.read()

        root_volume = ec2.BlockDevice(device_name='/dev/xvda', volume=ec2.BlockDeviceVolume.ebs(50))

        # Create EC2 Instance
        instancy_type = ec2.InstanceType.of(ec2.InstanceClass.C6I, ec2.InstanceSize.XLARGE)
        ec2_instance = ec2.Instance(
            self, f"{stack_prefix}EC2-Instance",
            instance_type=instancy_type,
            key_name=key_name,
            machine_image=amazon_linux,
            role=role,
            security_group=ec2_security_group,
            user_data=ec2.UserData.custom(user_data),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            block_devices=[root_volume]
        )

        # Generate CloudFormation Outputs
        CfnOutput(scope=self, id=f"{stack_prefix}PublicIP", value=ec2_instance.instance_public_ip)
        CfnOutput(scope=self, id=f"{stack_prefix}PublicURL", value=ec2_instance.instance_public_dns_name)
        CfnOutput(scope=self, id=f"{stack_prefix}RDS_SECRET", value=rds_mysql.secret.secret_name)
