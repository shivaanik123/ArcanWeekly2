# Deployment Guide

## Quick Answer

**No, pushing to GitHub does NOT automatically deploy to AWS.**

You need to manually deploy the code to your Elastic Beanstalk environment.

---

## How to Deploy to AWS

### Method 1: Elastic Beanstalk CLI (Recommended)

If you have the EB CLI installed:

```bash
# 1. Create application bundle
zip -r app.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"

# 2. Deploy to Elastic Beanstalk
eb deploy

# OR specify environment name
eb deploy arcan-dashboard-dev  # Replace with your environment name
```

### Method 2: AWS Console (Manual Upload)

1. **Package the code:**
   ```bash
   zip -r arcan-dashboard.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x "*node_modules*"
   ```

2. **Upload to Elastic Beanstalk:**
   - Go to AWS Console → Elastic Beanstalk
   - Select your application
   - Click "Upload and Deploy"
   - Upload the `arcan-dashboard.zip` file
   - Click "Deploy"

### Method 3: From EC2 Instance (SSH)

If you SSH into the Elastic Beanstalk instance:

```bash
# 1. SSH to your instance
ssh ec2-user@your-instance-address

# 2. Navigate to application directory
cd /var/app/current

# 3. Pull latest code
git pull origin claude/review-s3-data-structure-bhk4t

# 4. Restart application
sudo systemctl restart web
```

---

## Deployment Checklist

Before deploying:

- [ ] All tests pass locally
- [ ] Code committed and pushed to GitHub
- [ ] Environment variables configured in EB (.env or EB environment)
- [ ] Dependencies listed in `requirements.txt`
- [ ] Migration scripts tested locally

After deploying:

- [ ] Check application logs for errors
- [ ] Verify dashboard loads
- [ ] Test upload functionality
- [ ] Run migration script if first deployment

---

## First Time Deployment (New Features)

Since you're adding new historical data features:

1. **Deploy the code:**
   ```bash
   eb deploy
   ```

2. **SSH to the instance:**
   ```bash
   eb ssh
   ```

3. **Run the migration script:**
   ```bash
   cd /var/app/current
   python scripts/migrate_from_weekly_reports.py
   ```

4. **Verify in dashboard:**
   - Open dashboard URL
   - Check graphs show historical data

---

## Environment Variables

Make sure these are set in Elastic Beanstalk:

```
S3_BUCKET_NAME=arcan-dashboard-data-{env}-{account}
S3_DATA_PREFIX=data/
AWS_REGION=us-east-1
```

Set via:
- AWS Console → EB → Configuration → Software → Environment Properties
- OR: `eb setenv KEY=VALUE`

---

## Checking Deployment Status

```bash
# View environment info
eb status

# View recent logs
eb logs

# Open dashboard in browser
eb open
```

---

## Rollback (If Something Breaks)

```bash
# List recent deployments
eb appversions

# Rollback to previous version
eb deploy --version <previous-version>
```

---

## Common Issues

### Issue: "Module not found" after deployment
**Solution:** Make sure `requirements.txt` includes all dependencies:
```bash
pip freeze > requirements.txt
```

### Issue: Changes not showing
**Solution:**
1. Clear Streamlit cache: Add `?clear_cache=true` to URL
2. Restart EB environment: `eb restart`

### Issue: Migration script not found
**Solution:** Make sure scripts are included in deployment:
```bash
# Check .ebignore doesn't exclude scripts/
cat .ebignore
```

---

## For Your Current Changes

To deploy the historical data system:

```bash
# 1. Make sure you're on the right branch
git checkout claude/review-s3-data-structure-bhk4t

# 2. Package and deploy
eb deploy

# 3. Wait for deployment (2-5 minutes)
# Watch status with: eb status

# 4. Once deployed, run migration
eb ssh
cd /var/app/current
python scripts/migrate_from_weekly_reports.py
exit

# 5. Test in browser
eb open
```

---

## Need Help?

- View deployment logs: `eb logs`
- SSH to instance: `eb ssh`
- Check EB console: AWS Console → Elastic Beanstalk
- Restart app: `eb restart`
