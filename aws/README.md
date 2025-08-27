# Arcan Dashboard AWS Deployment

Simple deployment guide for the Arcan Property Dashboard to AWS Elastic Beanstalk.

## Prerequisites

1. **AWS CLI configured**: `aws configure`
2. **Docker installed**: `docker --version`
3. **Node.js/npm installed**: `npm --version`
4. **AWS CDK installed**: `npm install -g aws-cdk`

## Step 1: Deploy Infrastructure

Deploy the AWS infrastructure (S3 bucket, Elastic Beanstalk environment, IAM roles):

```bash
cd aws/

# Install CDK dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r ../requirements.txt

# Bootstrap CDK (only needed once per AWS account/region)
cdk bootstrap

# Deploy the infrastructure
cdk deploy ArcanDashboard-dev --require-approval never
```

**Note the outputs:**
- `DataBucketName`: Your S3 bucket name
- `EnvironmentURL`: Your app URL (without custom domain)
- `EnvironmentName`: EB environment name for deployments

## Step 2: Deploy Python Application

Deploy your Python code directly to Elastic Beanstalk (much simpler!):

```bash
# Create deployment package
VERSION=$(date +%Y%m%d-%H%M%S)
zip -r arcan-dashboard-$VERSION.zip . -x "*.git*" "*/__pycache__/*" "*.pyc" ".venv/*" "aws/*" "data/*"

# Get environment name from CDK output
EB_ENV_NAME=$(aws cloudformation describe-stacks --stack-name ArcanDashboard-dev --query "Stacks[0].Outputs[?OutputKey=='EnvironmentName'].OutputValue" --output text)

# Create application version
aws elasticbeanstalk create-application-version \
    --application-name arcan-dashboard-dev \
    --version-label $VERSION \
    --source-bundle S3Bucket="elasticbeanstalk-$(aws configure get region)-$(aws sts get-caller-identity --query Account --output text)",S3Key="arcan-dashboard-$VERSION.zip"

# Upload source code to S3
aws s3 cp arcan-dashboard-$VERSION.zip s3://elasticbeanstalk-$(aws configure get region)-$(aws sts get-caller-identity --query Account --output text)/

# Deploy to environment
aws elasticbeanstalk update-environment \
    --environment-name $EB_ENV_NAME \
    --version-label $VERSION

# Clean up
rm arcan-dashboard-$VERSION.zip
```

## Step 3: Update Application (Future Deployments)

For subsequent deployments, just zip and deploy your code:

```bash
# Same commands as Step 2 - no rebuilding needed!
VERSION=$(date +%Y%m%d-%H%M%S)
zip -r arcan-dashboard-$VERSION.zip . -x "*.git*" "*/__pycache__/*" "*.pyc" ".venv/*" "aws/*" "data/*"
# ... rest of deployment commands
```

## Environment Configuration

The CDK automatically sets these environment variables in Elastic Beanstalk:
- `USE_S3_STORAGE=true`
- `S3_BUCKET_NAME=your-bucket-name`
- `S3_DATA_PREFIX=data/`
- `AWS_REGION=your-region`

## Adding a Custom Domain (Optional)

1. **Register domain** in Route 53 or external registrar
2. **Create CNAME record** pointing to your EB environment URL
3. **Add HTTPS** via AWS Certificate Manager:
   - Request SSL certificate in ACM
   - Update EB environment to use HTTPS listener
   - Configure redirect from HTTP to HTTPS

## Useful Commands

```bash
# Check deployment status
aws elasticbeanstalk describe-environments --environment-names $EB_ENV_NAME

# View application logs
aws elasticbeanstalk retrieve-environment-info --environment-name $EB_ENV_NAME --info-type tail

# Clean up everything
cdk destroy ArcanDashboard-dev
```

## Troubleshooting

**Docker build fails:**
- Check Dockerfile syntax
- Ensure requirements.txt is valid
- Try building locally first: `docker build -t test .`

**Deployment fails:**
- Check EB environment status in AWS Console
- Review application logs
- Verify S3 bucket permissions

**App not loading:**
- Check security groups allow port 80/443
- Verify environment variables are set
- Check application logs for errors

## Development vs Production

For production deployment:
1. Change stack name to `ArcanDashboard-prod`
2. Use production environment variables
3. Enable load balancer (edit CDK stack)
4. Set up proper monitoring and alerts