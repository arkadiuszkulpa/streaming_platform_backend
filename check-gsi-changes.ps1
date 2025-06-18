#!/usr/bin/env pwsh
# Script to identify GSI changes between deployed stack and local template

param (
    [string]$StackName = "myai4-backend-dev",
    [string]$Region = $env:AWS_DEFAULT_REGION,
    [string]$LocalTemplate = "template.yaml"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking GSI changes between deployed stack and local template..."

# Create temporary directory
$tempDir = Join-Path $env:TEMP "gsi-check-$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Get deployed template
$deployedTemplatePath = Join-Path $tempDir "deployed-template.json"
Write-Host "Retrieving deployed template from $StackName..."
try {
    aws cloudformation get-template --stack-name $StackName --region $Region --query "TemplateBody" --output json | Out-File -FilePath $deployedTemplatePath
    Write-Host "Successfully retrieved deployed template"
} catch {
    Write-Host "Failed to retrieve deployed template: $_" -ForegroundColor Red
    Write-Host "The stack might not exist yet, or there might be an issue with AWS CLI access."
    exit 1
}

# Process the local template to extract GSI configurations
$localTemplateContent = Get-Content -Path $LocalTemplate -Raw
$tables = @()

# Simple pattern matching for DynamoDB tables in the YAML
$tablePattern = '(\w+):\s*\r?\n\s*Type:\s*AWS::DynamoDB::Table'
$tableMatches = [regex]::Matches($localTemplateContent, $tablePattern)

foreach ($match in $tableMatches) {
    $tableName = $match.Groups[1].Value
    $tables += $tableName
    
    Write-Host "Found table in local template: $tableName" -ForegroundColor Cyan
    
    # Look for GSIs in this table
    $tableStart = $localTemplateContent.IndexOf("${tableName}:", $match.Index)
    $tableEnd = $localTemplateContent.IndexOf("  # TABLE", $tableStart)
    if ($tableEnd -eq -1) {
        $tableEnd = $localTemplateContent.Length
    }
    
    $tableContent = $localTemplateContent.Substring($tableStart, $tableEnd - $tableStart)
    
    # Count GSIs
    $gsiMatch = [regex]::Match($tableContent, 'GlobalSecondaryIndexes:')
    if ($gsiMatch.Success) {
        $gsiContent = $tableContent.Substring($gsiMatch.Index)
        $gsiIndexes = [regex]::Matches($gsiContent, 'IndexName:\s*(\w+)')
        
        Write-Host "  GSIs found in ${tableName}:" -ForegroundColor Yellow
        foreach ($gsiIndex in $gsiIndexes) {
            $gsiName = $gsiIndex.Groups[1].Value
            Write-Host "    - $gsiName" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  No GSIs found in $tableName" -ForegroundColor DarkGray
    }
}

Write-Host "`nChecking GSI definitions in deployed template..."

# Parse the deployed template JSON (simplified approach)
$jsonContent = Get-Content -Path $deployedTemplatePath -Raw
$jsonContent = $jsonContent -replace '\\n', ' ' -replace '\\r', ' ' -replace '\\t', ' '

foreach ($tableName in $tables) {
    Write-Host "Checking deployed GSIs for table: $tableName" -ForegroundColor Cyan
    
    # Very simple pattern matching for GSIs in JSON (this is approximative)
    $deployedGsiPattern = "\\""${tableName}\\"".*?GlobalSecondaryIndexes.*?\\[(.*?)\\]"
    $gsiMatch = [regex]::Match($jsonContent, $deployedGsiPattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    
    if ($gsiMatch.Success) {
        $gsiContent = $gsiMatch.Groups[1].Value
        $gsiNameMatches = [regex]::Matches($gsiContent, '"IndexName"\s*:\s*"(\w+)"')
        
        Write-Host "  GSIs found in deployed ${tableName}:" -ForegroundColor Magenta
        foreach ($gsiNameMatch in $gsiNameMatches) {
            $gsiName = $gsiNameMatch.Groups[1].Value
            Write-Host "    - $gsiName" -ForegroundColor Magenta
        }
    } else {
        Write-Host "  No GSIs found in deployed $tableName or table doesn't exist yet" -ForegroundColor DarkGray
    }
}

Write-Host "`nAnalysis complete. Please review any differences in GSI configurations above.`n"
Write-Host "Important: This script uses simple pattern matching and may not catch all differences."
Write-Host "For a thorough comparison, review both templates in full detail."

# Clean up
Remove-Item -Path $tempDir -Recurse -Force
