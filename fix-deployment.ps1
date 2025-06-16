#!/usr/bin/env pwsh
# Script to help fix CloudFormation deployment issues with resource type changes

# Parameters
param(
    [Parameter(Mandatory=$true)]
    [string]$StackName,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1"
)

# Check if the AWS CLI is installed
try {
    aws --version | Out-Null
}
catch {
    Write-Error "AWS CLI is not installed. Please install the AWS CLI before running this script."
    exit 1
}

# Check if jq is installed
try {
    jq --version | Out-Null
}
catch {
    Write-Error "jq is not installed. Please install jq before running this script."
    exit 1
}

# Get the stack's current resources
Write-Host "Getting list of resources in stack $StackName..."
aws cloudformation list-stack-resources --stack-name $StackName --region $Region | Out-File -Encoding utf8 -FilePath "stack-resources.json"

Write-Host "Stack resources have been saved to stack-resources.json"
Write-Host "To delete the problematic resource and redeploy:"
Write-Host ""
Write-Host "1. Find the problematic resource (IdentityPoolIdParameter) in the AWS Console"
Write-Host "2. Manually delete just that resource in the SSM Parameter Store"
Write-Host "3. Run the following command to deploy your updated template:"
Write-Host ""
Write-Host "   sam deploy --template-file packaged-template.yaml --stack-name $StackName --parameter-overrides Environment=dev --capabilities CAPABILITY_NAMED_IAM --no-confirm-changeset --region $Region"
Write-Host ""
Write-Host "If the stack update still fails, you may need to:"
Write-Host "1. Export stack outputs: aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs' --output json > stack-outputs.json"
Write-Host "2. Delete the stack: aws cloudformation delete-stack --stack-name $StackName"
Write-Host "3. Wait for deletion to complete"
Write-Host "4. Deploy the updated template: sam deploy..."
