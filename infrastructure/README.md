
# Amazon RDS + Amazon ElastiCache CDK Infrastructure

The `cdk.json` file tells the CDK Toolkit how to execute your app.

To manually create a virtualenv on MacOS and Linux:

```bash
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```bash
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```bash
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```bash
pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```bash
cdk synth
```

Option 1: Deploy the Infrastructure to a new VPC, you will also need an [Amazon EC2 key pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html)

```bash
cdk deploy --profile your-aws-profile -c useDefaultVpc=true -c keyName=your-ssh-keyname
```

Option 2: If you would rather use the Default VPC you can do it as long as it has a Public Subnet to deploy the EC2 instance.

```bash
cdk deploy --profile your-aws-profile -c useDefaultVpc=true -c keyName=your-ssh-keyname
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
