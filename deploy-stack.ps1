#!/usr/bin/env pwsh
# Staged deployment helper for CloudFormation stacks with resource type conflicts

# Parameters
param(
    [Parameter(Mandatory=$true)]
    [string]$StackName,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [switch]$ForceDelete = $false
)

# Set AWS region for this session
$env:AWS_DEFAULT_REGION = $Region

# Check for direct parameter path approach
$templateContent = Get-Content -Path "template.yaml" -Raw
$usingDirectParamPath = $templateContent -match "IDENTITY_POOL_PARAM_NAME: !Sub"

Write-Host "Using direct parameter path approach: $usingDirectParamPath"

if ($ForceDelete) {
    Write-Host "⚠️ Force delete requested. Backing up stack outputs first..."
    
    # Backup outputs
    try {
        aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs' --output json | Out-File -Encoding utf8 -FilePath "stack-outputs-$StackName.json"
        Write-Host "✅ Stack outputs saved to stack-outputs-$StackName.json"
    } catch {
        Write-Host "⚠️ Could not save stack outputs. The stack might not exist or there was an error."
    }
    
    # Delete stack
    Write-Host "🔥 Deleting stack $StackName..."
    aws cloudformation delete-stack --stack-name $StackName
    
    Write-Host "⏳ Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete --stack-name $StackName
    
    if ($?) {
        Write-Host "✅ Stack deletion complete. Proceeding with deployment..."
    } else {
        Write-Host "❌ Stack deletion failed or timed out. Please check the AWS Console."
        exit 1
    }
}

# Package the SAM template
Write-Host "📦 Packaging SAM template..."
sam package --template-file template.yaml --output-template-file packaged-template.yaml --region $Region

# Deploy the packaged template
Write-Host "🚀 Deploying updated template..."
sam deploy --template-file packaged-template.yaml --stack-name $StackName --parameter-overrides Environment=$Environment --capabilities CAPABILITY_NAMED_IAM --no-confirm-changeset --region $Region

if ($?) {
    Write-Host "✅ Deployment successful!"
} else {
    Write-Host "❌ Deployment failed. Check the AWS CloudFormation console for details."
    Write-Host ""
    Write-Host "Common Issues & Solutions:"
    Write-Host "-------------------------"
    Write-Host "1. Resource type change error:"
    Write-Host "   - Try running this script with -ForceDelete to recreate the stack"
    Write-Host ""
    Write-Host "2. Circular dependency:"
    Write-Host "   - Update template to use direct parameter paths instead of Ref"
    Write-Host ""
    Write-Host "3. Permission issues:"
    Write-Host "   - Check IAM permissions for your AWS user/role"
    exit 1
}
