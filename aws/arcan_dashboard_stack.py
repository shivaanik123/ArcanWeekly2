"""
CDK Stack for Arcan Dashboard deployment to Elastic Beanstalk
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_elasticbeanstalk as eb,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class ArcanDashboardStack(Stack):
    """Stack for deploying Arcan Dashboard to Elastic Beanstalk"""

    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        # Create S3 bucket for data storage
        self.create_data_bucket()
        
        # Create IAM roles
        self.create_iam_roles()
        
        # Create Elastic Beanstalk application
        self.create_eb_application()
        
        # Create Elastic Beanstalk environment
        self.create_eb_environment()

    def create_data_bucket(self):
        """Create S3 bucket for storing dashboard data - simplified for dev"""
        self.data_bucket = s3.Bucket(
            self, 
            "DataBucket",
            bucket_name=f"arcan-dashboard-data-{self.env_name}-{self.account}",
            removal_policy=cdk.RemovalPolicy.DESTROY  # Easy cleanup for dev
        )

        # Output bucket name
        cdk.CfnOutput(
            self,
            "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="S3 bucket for dashboard data storage"
        )

    def create_iam_roles(self):
        """Create IAM roles for Elastic Beanstalk"""
        
        # Service role for Elastic Beanstalk - Administrator access for dev
        self.eb_service_role = iam.Role(
            self,
            "EBServiceRole",
            assumed_by=iam.ServicePrincipal("elasticbeanstalk.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ]
        )

        # Instance profile for EC2 instances - Administrator access for dev environment
        self.instance_role = iam.Role(
            self,
            "EC2InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ]
        )

        # Create instance profile
        self.instance_profile = iam.CfnInstanceProfile(
            self,
            "EC2InstanceProfile",
            roles=[self.instance_role.role_name]
        )

    def create_eb_application(self):
        """Create Elastic Beanstalk application"""
        self.eb_app = eb.CfnApplication(
            self,
            "ArcanDashboardApp",
            application_name=f"arcan-dashboard-{self.env_name}",
            description=f"Arcan Property Dashboard - {self.env_name} environment"
        )

    def create_eb_environment(self):
        """Create Elastic Beanstalk environment - simplified for dev"""
        
        # Minimal configuration - just the essentials
        option_settings = [
            # Instance type
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:launchconfiguration",
                option_name="InstanceType",
                value="t3.small"
            ),
            # IAM permissions
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:autoscaling:launchconfiguration",
                option_name="IamInstanceProfile",
                value=self.instance_profile.ref
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:elasticbeanstalk:application:environment",
                option_name="S3_BUCKET_NAME",
                value=self.data_bucket.bucket_name
            ),
            eb.CfnEnvironment.OptionSettingProperty(
                namespace="aws:elasticbeanstalk:application:environment",
                option_name="S3_DATA_PREFIX",
                value="data/"
            )
        ]

        # Create environment
        self.eb_env = eb.CfnEnvironment(
            self,
            "ArcanDashboardEnv",
            application_name=self.eb_app.ref,
            environment_name=f"arcan-dashboard-{self.env_name}",
            solution_stack_name="64bit Amazon Linux 2023 v4.7.1 running Python 3.13",
            option_settings=option_settings,
            tier=eb.CfnEnvironment.TierProperty(
                name="WebServer",
                type="Standard"
            )
        )

        # Output environment URL
        cdk.CfnOutput(
            self,
            "EnvironmentURL",
            value=f"http://{self.eb_env.attr_endpoint_url}",
            description="Elastic Beanstalk environment URL (add custom domain later)"
        )

        # Output environment name for deployment
        cdk.CfnOutput(
            self,
            "EnvironmentName", 
            value=self.eb_env.ref,
            description="Environment name for EB CLI deployment"
        )