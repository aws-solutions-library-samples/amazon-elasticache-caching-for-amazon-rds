# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as core
import aws_cdk.assertions as assertions
from cdk_nag import AwsSolutionsChecks
from infrastructure.rdbms_cache_stack import RdbmsCacheStack

# example tests. To run these tests, uncomment this file along with the example
# resource in infrastructure/infrastructure_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = RdbmsCacheStack(app, "infrastructure")
    template = assertions.Template.from_stack(stack)

    # template.has_resource_properties("AWS::SQS::Queue", {
    #     "VisibilityTimeout": 300
    # })

    core.Aspects.of(app).add(AwsSolutionsChecks())
