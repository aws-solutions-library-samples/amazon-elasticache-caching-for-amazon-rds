#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import aws_cdk as cdk
from dotenv import load_dotenv
from infrastructure.rdbms_cache_stack import RdbmsCacheStack
load_dotenv()

app = cdk.App()
RdbmsCacheStack(app, "RdbmsCacheStack",
    env=cdk.Environment(account=os.getenv('AWS_ACCOUNT'), region=os.getenv('AWS_REGION')),)

app.synth()
