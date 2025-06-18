#!/usr/bin/env pwsh
# GSI Phased Deployment Script
# This script handles the DynamoDB Global Secondary Index (GSI) limitation
# by deploying CloudFormation changes in phases.

param (
    [string]$Environment = "dev",
    [string]$Region = $env:AWS_DEFAULT_REGION
)

$ErrorActionPreference = "Stop"

# Display help message
Write-Host "===== DynamoDB GSI Phased Deployment Helper =====" -ForegroundColor Cyan
Write-Host "This script deploys your stack in two phases to work around"
Write-Host "the DynamoDB limitation of one GSI modification at a time."
Write-Host ""

# Set stack names
$stackName = "myai4-backend-$Environment"
$infraStackName = "myai4-infrastructure-$Environment"

Write-Host "Starting deployment for:" -ForegroundColor Yellow
Write-Host "- Environment:        $Environment"
Write-Host "- Region:             $Region"
Write-Host "- Stack name:         $stackName"
Write-Host "- Infra stack name:   $infraStackName"
Write-Host ""

# Check for required tools
if (!(Get-Command sam -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS SAM CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Confirm with the user
Write-Host "This will deploy your CloudFormation template in two phases." -ForegroundColor Yellow
$confirmation = Read-Host "Do you want to proceed? (y/n)"
if ($confirmation -ne "y") {
    Write-Host "Deployment cancelled." -ForegroundColor Red
    exit 0
}

try {
    # Phase 1: Deploy without GSI changes (using --disable-rollback)
    Write-Host "`nPHASE 1: Deploying stack with --disable-rollback flag" -ForegroundColor Green
    sam deploy --template-file packaged-template.yaml `
            --stack-name $stackName `
            --parameter-overrides Environment=$Environment InfraStackName=$infraStackName `
            --capabilities CAPABILITY_NAMED_IAM `
            --no-confirm-changeset `
            --region $Region `
            --disable-rollback

    # Wait for stack to stabilize
    Write-Host "`nWaiting 30 seconds for stack to stabilize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    # Phase 2: Complete the deployment
    Write-Host "`nPHASE 2: Completing the deployment" -ForegroundColor Green
    sam deploy --template-file packaged-template.yaml `
            --stack-name $stackName `
            --parameter-overrides Environment=$Environment InfraStackName=$infraStackName `
            --capabilities CAPABILITY_NAMED_IAM `
            --no-confirm-changeset `
            --region $Region

    Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "`nERROR: Deployment failed: $_" -ForegroundColor Red
    Write-Host "`nYou may need to check the CloudFormation console for more details."
    exit 1
}

Write-Host "`nNOTE: If you continue to see GSI-related errors, you might need to:" -ForegroundColor Yellow
Write-Host "1. Run this script again (sometimes multiple phases are needed)"
Write-Host "2. Consider deleting and recreating the stack if this is a dev environment"
Write-Host "3. Manually modify your template to add only one GSI at a time"
