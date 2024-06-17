# Guidance for boosting database performance reads with AWS ElastiCache

## Table of Content

1. [Overview](#overview)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
    - [Operating System](#operating-system)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)
8. [FAQ, known issues, additional considerations, and limitations](#faq-known-issues-additional-considerations-and-limitations)
9. [Notices](#notices)

## Overview

1. This guidance was created to help customers with database workloads that have high read:write (70:30) ratios and are looking to boost application performance, and at the same time reduce overall cost. Qualifying database workloads will see an increase in the number of transactions, a reduction in response time, and an overall reduction in cost. It is expected that two services together can perform a task faster. However, when AWS ElastiCache is paired with qualifying database workloads not only the performance increases but the total cost of the two services is lower than the cost of scaling the database alone to deliver a similar performance.

#### Architecture overview ####

<img width="676" alt="architecture-for-adding-caching-to-a-database" src="assets/images/architecture-diagram.png">

### Cost

You are responsible for the cost of the AWS services used while running this Guidance.

As of 03/28/2024, the cost for running this guidance with the default settings using AWS ElastiCache instance type cache.t2.x.small utilizing 1 primary, in the US East (N. Virginia) for on-demand pricing is approximately $24.82 USD total per month. AWS The RDS database cost is estimated at $14.71. However, cost will greatly depend on the, instance size, and RDS licensing model selected. Reserved instance pricing will reduce cost for both RDS and ElastiCache. ElastiCache is also available in a serverless offering where pay-per-consumption cost model is applicable. 

| Service               | Assumptions                                       | Estimated Cost Per Month |
| --------------------- | ------------------------------------------------- | ------------- | 
| Amazon ElastiCache    | 2 Instance (cache.t2.small) used for 730 hours	| $24.82 |
| Amazon RDS MySQL      | 1 Instance (db.t3.micro) used for 730 hours       | $14.71 |


## Prerequisites

This guidance is targeted towards those familiar with the AWS RDS Service. The users are expected to have a basic understanding of AWS RDS service and database access patterns. It guides users how to utilize AWS ElastiCache in addition to their existing relational database. Effectively paring your database with a caching service. It should be run in US East N.Virginia region. This guidance is not intended for production workloads. For example, recommended security configurations are not included. For production systems it is strongly recommended that data should be encrypted both in transit and at rest.


### Operating System

Tis guidance runs in the AWS cloud utilizing an AWS EC2 compute instance based on the Amazon Linux 2023 AMI. With network access to both AWS RDS database service and AWS ElastiCache (both are required). In addition the EC2 compute instance will require public access on port 8888. The included Cloud Formation template can be used to create such an EC2 instance. The sample code also includes two Jupyter notebooks to analyze and visually plot the performance results. Note that public access to the EC2 host on port 8888 should be enabled from your computer only not all end user computers.

### Software dependencies 

Install dependencies by executing the setup_host.sh script. This script will install gcc python3-devel at the host level. In addition to the two packages installed a python virtual environment is created with dependent modules installed from the requirements.txt file. The python modules are only committed to the virtual environment not the host. The includes commands are optimized to work on the EC2 instance created by the included CloudFormation template and are specific for the Amazon Linux 2023 AMI al2023-ami-2023.4.20240319.1-kernel-6.1-arm64. This image is specific to the us-east-1 region. Other OS or AMI configuration may require additional steps.

- At the OS prompt execute the setup_host.sh script to install and configure all necessary software and to create the Python virtual environment.

### Third-party tools

This guidance uses Jupyter lab and the included notebooks to visualize/plot the performance data captured in json logs.
For convenience reasons a Jupyter password has been set to 'test123'. 
Seed data is from the Airportdb sample database located here: https://dev.mysql.com/doc/airportdb/en/. However, by modifying the read and write queries, any seed data can be used. 

### AWS account requirements

Ability to create an EC2 instance and networking configuration to permit access to both the RDS server and the ElastiCache service and public access to the EC2 on port 8888 from the customer end computer only. (CIDR/32)

**Example resources:**
- RDS MySQL Database with the airportdb data loaded
- AWS ElastiCache
- VPC
- SSH key in your region of choice

### Supported Regions

All regions where AWS RDS MySQL and AWS ElastiCache are offered.

## Deployment Steps

1. Create an EC2 instance with at least 1GB of memory using the Amazon Linux 2023 image. For convenience reason the repository includes the cloud formation template called guidance-ec2.yaml. Use AWS CloudFormation and with this template to create and EC2 instance.
2. Log in to your instance from the AWS console via Session Manager or via SSH.
3. Clone the repository by executing ```git clone <repo name> ```
4. Change directory to the guidance directory ```cd guidance```
5. Execute the setup_host script ```./setup_host.sh```
6. Log in to the same instance from a separate session and navigate to the same directory and execute ```./setup_jupyter.sh``` script. Enter the initial password. Commit this to memory as you will have to enter it once the notebook is running.
7. In your computer browser enter the EC2's public IP address and port for example ```http://1.2.3.4:8888`` Note: that jupyter configuration is not a secured as it is running the http (no s) protocol. In order to secure jupyter notebook please configure https protocol as documented here: https://jupyter-notebook.readthedocs.io/en/6.2.0/public_server.html#running-a-public-notebook-server 
8. Enter the password for your Jupyter notebook. (The password entered at step 6)
9. In your first session edit the .env file and update it with your database and ElastiCache related information.
10. Source the .env file ```source .env``` to export the parameters.

## Deployment Validation

It is not part of this guidance to install and configure client applications for database and ElastiCache connectivity. However, at this point you can install client applications to validate connectivity to both the database and ElastiCache.

## Running the Guidance

* Execute the scenario01.py script. This workload accesses the database only and captures command level performance data in a logfile. In the directory where you executed the setup_host.sh and the Python virtual environment is activated, the first connection, execute: ```python scenario01.py --users 10 --queries 1000 --read_rate 80```
* If deployment was correct  you should see a response similar to this. (small sample execution)
  
(.venv) [ec2-user]$ python scenario01.py --users 1 --queries 10 --read_rate 80
Reads: 8
Writes: 2
Logfile located here: logs/scenario01_139007_mwae8c4k.json

* Open the Jupyter notebook plot_results_db_only.ipynb file and update the logfile name in the second cell. For example ```log_pattern = 'scenario01_139007_mwae8c4k.json```

* From the run option select run all cells. The output of the last cell will show both the number of executions per second and the average response time. 

* To compare the performance boost provided by ElastiCache repeat the above steps but use the scenario02.py script. For example execute ```python scenario02.py --users 1 --queries 10 --read_rate 80``` The output should be similar.

(.venv) [ec2-user]$ python scenario02.py --users 1 --queries 10 --read_rate 80
Connected to Database
Connected to ElastiCache
Reads: 10
Writes: 0
Cache hits: 10
Cache misses: 0
Logfile located here: logs/scenario02_176908_0y2qr55f.json

* Open the Jupyter notebook plot_results_db_and_cache.ipynb file and update the logfile name in the second cell. For example ```log_pattern = 'scenario02_176908_0y2qr55f.json```

Then select run all cells to plot the performance of the second scenario. Note that a small execution may not be sufficient to demonstrate the performance advantage of adding a cache. 

## Next Steps

To see the potential improvements ElastiCache can provide to your application. Replace the database connection parameters with your test database values and modify the READ_QUERY and WRITE_QUERY text parameters to fit your schema.

## Cleanup

To clean up your environment stop all services and delete the MySQL database and ElastiCache cluster. Finally delete the EC2 instance from where you executed the commands. 


## FAQ, known issues, additional considerations, and limitations

Caching is beneficial for databases that execute a high read to write ratio workloads. For example 80:20 read to write workloads. The sample data provided in the airportdb is subject to change and accepting end user licensing agreement.


**Additional considerations **

- This Guidance creates insecure Jupyter Notebook 
- Cashing is not applicable for workloads that are write intensive meaning that the majority of transactions are not repetitive read transactions.

For feedback please access the github page <here>

## Notices

Include a legal disclaimer

*Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.*

