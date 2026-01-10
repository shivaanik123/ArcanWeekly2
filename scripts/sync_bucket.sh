#!/bin/bash
#
# Sync S3 bucket to local bucket_copy/ directory
# Usage: ./scripts/sync_bucket.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUCKET_COPY_DIR="$PROJECT_DIR/bucket_copy"

S3_BUCKET="s3://arcan-dashboard-data-dev-408312670144"
AWS_PROFILE="Arcan"

echo "=============================================="
echo "ARCAN S3 BUCKET SYNC"
echo "=============================================="
echo "Source: $S3_BUCKET"
echo "Destination: $BUCKET_COPY_DIR"
echo ""

# Create bucket_copy directory structure
mkdir -p "$BUCKET_COPY_DIR/data"
mkdir -p "$BUCKET_COPY_DIR/historicaldata"
mkdir -p "$BUCKET_COPY_DIR/logos"

echo "Syncing data/ folder..."
aws s3 sync "$S3_BUCKET/data/" "$BUCKET_COPY_DIR/data/" \
    --profile "$AWS_PROFILE" \
    --exclude "backups/*" \
    --exclude "*.DS_Store"

echo ""
echo "Syncing logos/ folder..."
aws s3 sync "$S3_BUCKET/logos/" "$BUCKET_COPY_DIR/logos/" \
    --profile "$AWS_PROFILE" \
    --exclude "*.DS_Store"

echo ""
echo "Syncing historicaldata/ folder (if exists)..."
aws s3 sync "$S3_BUCKET/historicaldata/" "$BUCKET_COPY_DIR/historicaldata/" \
    --profile "$AWS_PROFILE" \
    --exclude "*.DS_Store" 2>/dev/null || echo "  (historicaldata/ not yet created in S3)"

echo ""
echo "=============================================="
echo "SYNC COMPLETE"
echo "=============================================="
echo ""
echo "Local structure:"
echo "  $BUCKET_COPY_DIR/"
echo "  ├── data/          <- Weekly Yardi reports"
echo "  ├── historicaldata/ <- Aggregated historical data"
echo "  └── logos/          <- Property logos"
echo ""

# Show stats
echo "Statistics:"
echo "  Weeks: $(ls -d "$BUCKET_COPY_DIR/data"/*/ 2>/dev/null | grep -v backups | wc -l | tr -d ' ')"
echo "  Properties in latest week: $(ls -d "$BUCKET_COPY_DIR/data/$(ls "$BUCKET_COPY_DIR/data" | grep -v backups | sort | tail -1)"/*/ 2>/dev/null | wc -l | tr -d ' ')"
