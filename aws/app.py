#!/usr/bin/env python3
"""
AWS CDK app for deploying Arcan Dashboard to Elastic Beanstalk
"""

import aws_cdk as cdk
from constructs import Construct

from arcan_dashboard_stack import ArcanDashboardStack

app = cdk.App()

# Get environment settings
env_name = app.node.try_get_context("env") or "dev"
account = app.node.try_get_context("account")
region = app.node.try_get_context("region") or "us-east-1"

# Create the stack
ArcanDashboardStack(
    app, 
    f"ArcanDashboard-{env_name}",
    env_name=env_name,
    env=cdk.Environment(
        account=account,
        region=region
    ),
    description=f"Arcan Property Dashboard - {env_name} environment"
)

app.synth()