# Quick Lambda code refresh script for main API Lambda (lambda_handler.py)
$ErrorActionPreference = "Stop"

# Configuration
$region = "eu-west-2"
$lambdaSourceFile = "src/lambda_handler.py"
$zipFile = "lambda_handler.zip"

# Stack names - set these to match your actual CloudFormation stack names
$devStackName = "myai4-backend-dev"  # Default, change if needed
$prodStackName = "myai4-backend-prod"  # Default, change if needed

# Parse command-line arguments
param(
    [string]$dev = $devStackName,
    [string]$prod = $prodStackName
)

# Update stack names if provided as arguments
$devStackName = $dev
$prodStackName = $prod

Write-Host "Starting Lambda handler code refresh..."

# Get AWS Account ID
$accountId = (aws sts get-caller-identity --query Account --output text)
$bucketName = "lambda-artifacts-$region-$accountId"

Write-Host "Configuration:"
Write-Host "   Region: $region"
Write-Host "   Account ID: $accountId"
Write-Host "   Bucket: $bucketName"

# Step 1: Package Lambda function
Write-Host "Packaging Lambda function..."
if (Test-Path $zipFile) {
    Remove-Item $zipFile
}
Compress-Archive -Path $lambdaSourceFile -DestinationPath $zipFile -Update
Write-Host "Created: $zipFile"

# Step 2: Create bucket if needed (ignore errors if exists)
Write-Host "Ensuring S3 bucket exists..."
try {
    aws s3api create-bucket `
      --bucket $bucketName `
      --region $region `
      --create-bucket-configuration LocationConstraint=$region 2>$null
    Write-Host "Created bucket: $bucketName"
} catch {
    Write-Host "Bucket already exists: $bucketName"
}

# Step 3: Upload to S3
Write-Host "Uploading to S3..."
aws s3 cp $zipFile "s3://$bucketName/$zipFile" --region $region
Write-Host "Uploaded to S3"

# Step 4: Update Lambda function code with versioning
Write-Host "Updating Lambda function code..."

# Set your Lambda function names here
$prodFunctionName = "centralised-api-$prodStackName"
$devFunctionName = "centralised-api-$devStackName"

Write-Host "Using Lambda function names:"
Write-Host "   Dev: $devFunctionName"
Write-Host "   Prod: $prodFunctionName"

# Update dev function if it exists
try {
    aws lambda update-function-code `
      --function-name $devFunctionName `
      --s3-bucket $bucketName `
      --s3-key $zipFile `
      --publish `
      --region $region
    $version = (aws lambda get-function --function-name $devFunctionName --region $region --query 'Configuration.Version' --output text)
    Write-Host "Dev Lambda function updated to version: $version"
} catch {
    Write-Host "Dev function not found or could not be updated"
}

# Update prod function if it exists
try {
    aws lambda update-function-code `
      --function-name $prodFunctionName `
      --s3-bucket $bucketName `
      --s3-key $zipFile `
      --publish `
      --region $region
    $version = (aws lambda get-function --function-name $prodFunctionName --region $region --query 'Configuration.Version' --output text)
    Write-Host "Prod Lambda function updated to version: $version"
} catch {
    Write-Host "Prod function not found or could not be updated"
}

# Cleanup - Comment out if you want to keep the zip file
# Remove-Item $zipFile
Write-Host "Finished updating Lambda handler function"
