### MyAI4 Backend Deployment Commands

## Initial Deployment (First Time)
# Local development deployment with packaging
sam build
sam package --s3-bucket myai4-deployment-artifacts --output-template-file packaged-template.yaml
sam deploy --template-file packaged-template.yaml --stack-name myai4-backend-dev --parameter-overrides Environment=dev --capabilities CAPABILITY_NAMED_IAM

# Alternative using samconfig.toml (after updating it)
sam deploy --config-env dev --config-file samconfig.toml

# Quick local deployment (works locally but not in CodePipeline)
sam deploy --template-file template.yaml --stack-name myai4-backend-dev --parameter-overrides Environment=dev --capabilities CAPABILITY_NAMED_IAM --resolve-s3

# Create Secrets Manager secret for RapidAPI key (only needed once)
aws secretsmanager create-secret --name "myai4/rapidapi/keys/" --secret-string "{\"rapidapikey\":\"your-api-key-here\"}" --description "RapidAPI Key for MyAI4 ecosystem services"

# Update secret if needed
aws secretsmanager update-secret --secret-id "myai4/rapidapi/keys/" --secret-string "{\"rapidapikey\":\"your-updated-api-key-here\"}"

## Quick Lambda Update (After Deployment)
# Update Lambda code only (much faster than full deployment)
# Update all functions in dev environment (default)
cd c:\Projects\streaming_platform_backend; .\refresh-lambda_handler.ps1 -environment dev -stackName myai4-backend-dev

# Update a specific lambda function in dev
cd c:\Projects\streaming_platform_backend; .\refresh-lambda_handler.ps1 -environment dev -stackName myai4-backend-dev -lambdaName profile

# Update for production (only when dev is fully tested)
cd c:\Projects\streaming_platform_backend; .\refresh-lambda_handler.ps1 -environment prod -stackName myai4-backend-prod

## Test API Connectivity
# Get API URL from CloudFormation outputs
aws cloudformation describe-stacks --stack-name myai4-backend-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text

# Test with PowerShell (full diagnostic information)
$apiUrl = aws cloudformation describe-stacks --stack-name myai4-backend-dev --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
Invoke-RestMethod -Uri "$apiUrl`?operation=test" -Method GET | ConvertTo-Json -Depth 10

# Delete the stack if needed
aws cloudformation delete-stack --stack-name myai4-backend-dev

# Create S3 bucket for deployment artifacts (one-time setup)
aws s3 mb s3://myai4-deployment-artifacts
