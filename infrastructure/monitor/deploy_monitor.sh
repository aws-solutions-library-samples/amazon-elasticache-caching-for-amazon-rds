#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

ID=$(date '+%H%M%S')
START_TIME=$(date +%s)
echo "`date '+%H:%M:%S'` -  ## DBTop Monitoring Solution - Creating AWS Cloudformation StackID : ${ID} "
TEMPLATE="DBTopMonitoringSolution.template"

if ! test -f ${TEMPLATE}; then
  echo "File does not exist."
  wget "https://raw.githubusercontent.com/${GITHUB_REPO}/db-top-monitoring/master/conf/DBTopMonitoringSolution.template"
fi

aws cloudformation create-stack --stack-name "db-top-solution-${ID}" \
	--template-body file://${TEMPLATE} \
	--parameters ParameterKey=Username,ParameterValue=${POOL_EMAIL} \
	ParameterKey=VPCParam,ParameterValue=${VPC_ID} \
	ParameterKey=SubnetParam,ParameterValue=${SUBNET_ID} \
	ParameterKey=InstanceType,ParameterValue=${INSTANCE_TYPE} \
	ParameterKey=PublicAccess,ParameterValue=true \
	ParameterKey=SGInboundAccess,ParameterValue=0.0.0.0/0 \
	ParameterKey=GitHubRepository,ParameterValue=${GITHUB_REPO} \
	--region "${AWS_REGION}" --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete \
	--stack-name "db-top-solution-${ID}" --region "${AWS_REGION}"

export $(aws cloudformation describe-stacks --stack-name "db-top-solution-${ID}" --output text --query 'Stacks[0].Outputs[].join(`=`, [join(`_`, [`CF`, `OUT`, OutputKey]), OutputValue ])' --region "${AWS_REGION})"

END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
eval "echo Elapsed time: $(date -ud "@${ELAPSED}" +'$((%s/3600/24)) days %H hr %M min %S sec')"

echo -e "\n\n\n --############### Connection Information ###############-- \n\n"
echo " StackID\t: ${ID}"
echo " PublicAppURL\t: $CF_OUT_PublicAppURL"
echo " PrivateAppURL\t: $CF_OUT_PrivateAppURL"

rm delete.sh
echo -e "\n\n\n --############### Stack Deletion ###############-- \n\n"
echo "#!/bin/bash" >> delete.sh
echo "aws cloudformation delete-stack --stack-name db-top-solution-${ID} --region ${AWS_REGION}" >> delete.sh
echo "aws cloudformation wait stack-delete-complete --stack-name db-top-solution-${ID} --region ${AWS_REGION}" >> delete.sh
echo "$ ./delete.sh"
chmod +x delete.sh
