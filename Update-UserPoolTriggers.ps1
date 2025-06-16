param (
    [Parameter(Mandatory=$true)]
    [string]$StackName,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("PreSignUp", "PostConfirmation", "Both")]
    [string]$TriggerType = "Both"
)

Write-Host "Configuring Cognito triggers for stack: $StackName" -ForegroundColor Green

# Get UserPoolId from CloudFormation outputs
$userPoolId = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?ExportName=='$StackName-UserPoolId'].OutputValue" --output text

if (!$userPoolId) {
    Write-Host "Failed to retrieve UserPoolId for stack $StackName" -ForegroundColor Red
    exit 1
}

Write-Host "Found UserPoolId: $userPoolId" -ForegroundColor Green

# Initialize empty lambda config
$lambdaConfig = '{}'

# Configure PreSignUp trigger if requested
if ($TriggerType -eq "PreSignUp" -or $TriggerType -eq "Both") {
    # Get PreSignUp Lambda ARN
    $preSignUpLambdaArn = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?ExportName=='$StackName-PreSignUpLambdaArn'].OutputValue" --output text
    
    if (!$preSignUpLambdaArn) {
        Write-Host "Failed to retrieve PreSignUp Lambda ARN for stack $StackName" -ForegroundColor Red
    } else {
        Write-Host "Found PreSignUp Lambda ARN: $preSignUpLambdaArn" -ForegroundColor Green
        $lambdaConfig = '{\"PreSignUp\": \"' + $preSignUpLambdaArn + '\"}'
    }
}

# Configure PostConfirmation trigger if requested
if ($TriggerType -eq "PostConfirmation" -or $TriggerType -eq "Both") {
    # Get PostConfirmation Lambda ARN
    $postConfirmationLambdaArn = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?ExportName=='$StackName-PostConfirmationLambdaArn'].OutputValue" --output text
    
    if (!$postConfirmationLambdaArn) {
        Write-Host "Failed to retrieve PostConfirmation Lambda ARN for stack $StackName" -ForegroundColor Red
    } else {
        Write-Host "Found PostConfirmation Lambda ARN: $postConfirmationLambdaArn" -ForegroundColor Green
        
        # If lambda config already has PreSignUp, add PostConfirmation
        if ($lambdaConfig -ne '{}') {
            $lambdaConfig = $lambdaConfig.TrimEnd('}')
            $lambdaConfig = $lambdaConfig + ', \"PostConfirmation\": \"' + $postConfirmationLambdaArn + '\"}'
        } else {
            $lambdaConfig = '{\"PostConfirmation\": \"' + $postConfirmationLambdaArn + '\"}'
        }
    }
}

# Only proceed if we have Lambda functions to configure
if ($lambdaConfig -eq '{}') {
    Write-Host "No Lambda functions found to configure as triggers" -ForegroundColor Red
    exit 1
}

Write-Host "Setting up Lambda triggers with config: $lambdaConfig..." -ForegroundColor Yellow

# Update the user pool with the Lambda triggers
aws cognito-idp update-user-pool --user-pool-id $userPoolId --lambda-config $lambdaConfig --auto-verified-attributes email

Write-Host "Trigger configuration complete!" -ForegroundColor Green

# Create the CloudWatch Log Groups if they don't exist
if ($TriggerType -eq "PreSignUp" -or $TriggerType -eq "Both") {
    $preSignUpLogGroup = "/aws/lambda/$StackName-pre-signup-account-linking"
    Write-Host "Ensuring log group exists: $preSignUpLogGroup" -ForegroundColor Yellow
    aws logs create-log-group --log-group-name $preSignUpLogGroup --region $env:AWS_REGION 2>&1 | Out-Null
}

if ($TriggerType -eq "PostConfirmation" -or $TriggerType -eq "Both") {
    $postConfirmationLogGroup = "/aws/lambda/$StackName-post-confirmation-account-creation"
    Write-Host "Ensuring log group exists: $postConfirmationLogGroup" -ForegroundColor Yellow
    aws logs create-log-group --log-group-name $postConfirmationLogGroup --region $env:AWS_REGION 2>&1 | Out-Null
}

Write-Host "Log group creation complete!" -ForegroundColor Green
