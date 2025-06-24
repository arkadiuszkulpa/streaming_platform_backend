# Lambda code refresh script for multiple API Lambda functions
param(
    [string]$environment = "dev",  # Default to dev environment
    [string]$stackName = "myai4-backend-dev", # Default stack name
    [string]$lambdaName = "all"    # Default to update all lambdas, can specify individual lambda
)

$ErrorActionPreference = "Stop"

# Configuration
$region = "eu-west-2"
$sourceDir = "src"
$zipDir = "temp_zip"
$zipBucket = "lambda-artifacts-$region-$((aws sts get-caller-identity --query Account --output text))"

# Define lambda functions from template.yaml
$lambdaFunctions = @{
    "account" = "lambda_handler_account.py"
    "profile" = "lambda_handler_profile.py"
    "profile-settings" = "lambda_handler_profile_settings.py"
    "profile-ai" = "lambda_handler_profile_ai.py"
    "movie" = "lambda_handler_movie.py"
    "subscription" = "lambda_handler_subscription.py"
    "watchlist" = "lambda_handler_watchlist.py"
}

Write-Host "Starting Lambda handler code refresh for stack: $stackName (Environment: $environment)" -ForegroundColor Cyan

# Create temporary directory for zip files if it doesn't exist
if (-not (Test-Path $zipDir)) {
    New-Item -ItemType Directory -Path $zipDir | Out-Null
}

# Create S3 bucket if needed (ignore errors if exists)
Write-Host "Ensuring S3 bucket exists: $zipBucket"
try {
    aws s3api create-bucket `
      --bucket $zipBucket `
      --region $region `
      --create-bucket-configuration LocationConstraint=$region 2>$null
    Write-Host "Created bucket: $zipBucket" -ForegroundColor Green
} catch {
    Write-Host "Bucket already exists: $zipBucket" -ForegroundColor Gray
}

# Process specified lambda or all lambdas
$lambdasToProcess = @()
if ($lambdaName -eq "all") {
    $lambdasToProcess = $lambdaFunctions.Keys
    Write-Host "Processing ALL Lambda functions" -ForegroundColor Yellow
} elseif ($lambdaFunctions.ContainsKey($lambdaName)) {
    $lambdasToProcess = @($lambdaName)
    Write-Host "Processing SINGLE Lambda function: $lambdaName" -ForegroundColor Yellow
} else {
    Write-Host "Error: Lambda function '$lambdaName' not found. Available functions:" -ForegroundColor Red
    $lambdaFunctions.Keys | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

# Process each lambda function
foreach ($lambda in $lambdasToProcess) {
    $handlerFile = $lambdaFunctions[$lambda]
    $zipFile = "$zipDir/$lambda.zip"
    
    Write-Host "`n===== Processing Lambda: $lambda ($handlerFile) =====" -ForegroundColor Cyan
    
    # Step 1: Package Lambda function
    Write-Host "Packaging Lambda function..."
    if (Test-Path $zipFile) {
        Remove-Item $zipFile
    }
    
    # Create zip file with all required dependencies
    Compress-Archive -Path "$sourceDir/$handlerFile" -DestinationPath $zipFile -Update
    Write-Host "Created: $zipFile" -ForegroundColor Gray
    
    # Step 2: Upload to S3
    Write-Host "Uploading to S3..."
    aws s3 cp $zipFile "s3://$zipBucket/$lambda.zip" --region $region
    Write-Host "Uploaded to S3: s3://$zipBucket/$lambda.zip" -ForegroundColor Gray
    
    # Step 3: Update Lambda function code
    $functionName = "${lambda}-api-$stackName"
    
    try {
        Write-Host "Updating function: $functionName..."
        aws lambda update-function-code `
          --function-name $functionName `
          --s3-bucket $zipBucket `
          --s3-key "$lambda.zip" `
          --publish `
          --region $region `
          --output text | Out-Null # Suppress verbose output from AWS CLI
        
        # Get just the version number instead of full function definition
        $version = (aws lambda get-function --function-name $functionName --region $region --query 'Configuration.Version' --output text)
        Write-Host "✅ Lambda function updated to version: $version" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error: Function not found or could not be updated: $functionName" -ForegroundColor Red
        Write-Host "Error details: $_" -ForegroundColor DarkYellow
    }
}

# Cleanup
Write-Host "`nCleaning up temporary files..." -ForegroundColor Gray
Remove-Item -Path $zipDir -Recurse -Force

Write-Host "`n✅ Finished updating Lambda handler functions" -ForegroundColor Green
Write-Host "`nTo test the APIs, use the following commands:" -ForegroundColor Yellow
Write-Host '$apiBaseUrl = aws cloudformation describe-stacks --stack-name ' -NoNewline
Write-Host $stackName -ForegroundColor Cyan -NoNewline
Write-Host ' --query "Stacks[0].Outputs[?OutputKey==''ApiUrl''].OutputValue" --output text'
Write-Host 'Invoke-RestMethod -Uri "${apiBaseUrl}/account?operation=test" -Method GET | ConvertTo-Json -Depth 10'
Write-Host ""
Write-Host "To update a single lambda function, specify the name:" -ForegroundColor Yellow
Write-Host ".\refresh-lambda_handler.ps1 -environment $environment -stackName $stackName -lambdaName account" -ForegroundColor Cyan