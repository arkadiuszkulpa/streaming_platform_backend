# MyAI4 Backend Integration Guide

## Overview

This document explains the backend integration approach used in the MyAI4 ecosystem. The platform uses a centralized Lambda function pattern accessed through a direct API Gateway integration, rather than using AWS Amplify.

> **CONSOLIDATION NOTICE**: This document now contains the complete implementation plan, testing procedures, and other information previously spread across multiple files including:
> - BACKEND_IMPLEMENTATION_PLAN.md
> - CENTRALIZED_LAMBDA_IMPLEMENTATION_SUMMARY.md

## Architecture

```
Frontend (React/TypeScript)
    ↓ UserDataService.ts
    ↓ HTTP calls to /centralized
API Gateway 
    ↓ triggers
Lambda Function (centralized_api)
    ↓ reads/writes  
DynamoDB Tables (MyAI4 Ecosystem + Streaming)
```

## Why Not Amplify?

AWS Amplify is a valuable tool for many projects, but the MyAI4 ecosystem requires a more tailored approach:

1. **Simplified Backend**: A centralized Lambda function provides sufficient functionality without the overhead of Amplify
2. **Direct Control**: More granular control over API behavior and error handling
3. **Reduced Dependencies**: Fewer client-side dependencies to manage and update
4. **Consistent Interface**: Standard HTTP calls with JWT bearer token authentication
5. **Cross-Service Standardization**: Unified API interface across all MyAI4 services

## Implementation Details

### API Design

- **Single Endpoint**: `/centralized` handles all operations
- **Operation Parameter**: Each request specifies an operation for backend routing
- **HTTP Methods**:
  - GET: For read operations (query parameters)
  - POST: For write operations (request body)
  - Method parameter for logical PUT/PATCH/DELETE
- **Authentication**: Bearer token authentication using JWT from Cognito

### UserDataService Implementation

```typescript
// Example from UserDataService.ts
private async apiCall<T>(
  operation: string, 
  data: any = {}, 
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE' = 'GET'
): Promise<T> {
  const url = `${this.apiBaseUrl}/centralized`;
  const headers = {
    'Content-Type': 'application/json',
    ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
  };

  const body = method === 'GET' ? undefined : JSON.stringify({
    operation,
    data,
    method,
  });

  // For GET requests, pass operation and data as query parameters
  const finalUrl = method === 'GET' 
    ? `${url}?operation=${encodeURIComponent(operation)}&data=${encodeURIComponent(JSON.stringify(data))}`
    : url;

  const response = await fetch(finalUrl, { 
    method: method === 'GET' ? 'GET' : 'POST', // Backend only supports GET and POST
    headers,
    body,
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
```

### Backend Lambda Structure

The backend Lambda function implements a router pattern:

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Centralized Lambda handler for MyAI4 ecosystem operations
    """
    try:
        # Parse the operation from query parameters or request body
        http_method = event.get('httpMethod', 'GET')
        
        if http_method == 'GET':
            # For GET requests, operation is in query parameters
            query_params = event.get('queryStringParameters') or {}
            operation = query_params.get('operation')
            data = json.loads(query_params.get('data', '{}'))
        else:
            # For POST/PATCH requests, operation is in request body
            body = json.loads(event.get('body', '{}'))
            operation = body.get('operation')
            data = body.get('data', {})
            
        if not operation:
            return create_response(400, {'error': 'Operation parameter is required'})
            
        # Route to appropriate handler
        handlers = {
            # User Profile Operations
            'getUserProfile': handle_get_user_profile,
            'createUserProfile': handle_create_user_profile,
            'updateUserProfile': handle_update_user_profile,
            
            # ... other operations
        }
        
        handler = handlers.get(operation)
        if not handler:
            return create_response(400, {'error': f'Unknown operation: {operation}'})
            
        # Execute the handler
        result = handler(data)
        return create_response(200, result)
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})
```

## Configuration

The frontend connects to the backend using environment variables populated by the `fetch-cloudformation-exports.js` script:

```javascript
VITE_API_BASE_URL=${getExport(`${backendStackName}-ApiUrl`, 'https://your-api-gateway.execute-api.eu-west-2.amazonaws.com/dev/centralized')}
```

## Implementation Plan for Backend Team

### Required Changes

#### 1. Update CloudFormation Template
Add the `ENVIRONMENT` variable to the Lambda function's environment variables:

```yaml
ENVIRONMENT: !Ref Environment # Added for enhanced test diagnostics
```

Note: The AWS_LAMBDA_FUNCTION_NAME environment variable is automatically provided by AWS Lambda runtime and does not need to be explicitly defined.

#### 2. Update Lambda Handler
Replace the current `handle_test` function in `lambda_handler.py` with the enhanced version from `enhanced_lambda_handler_test_function_complete.py` (located in `files_borrowed_from_infra_backend_repos_for_context/`).

The enhanced test function provides:
- Detailed table status including item counts and sizes
- Environment variable validation
- API version and execution environment details
- Warnings about missing or misconfigured resources

When integrating:
- Remove redundant imports
- Keep the existing global variables and functions (dynamodb, table names, etc.)
- Keep the implementation of `get_rapidapi_key()`

#### 3. Deploy the Updated Stack
Deploy the updated CloudFormation template with:

```powershell
aws cloudformation deploy `
  --template-file template-backend.yaml `
  --stack-name myai4-backend-dev `
  --parameter-overrides Environment=dev RapidApiKeyParameter=your-rapidapi-key `
  --capabilities CAPABILITY_NAMED_IAM `
  --region eu-west-2
```

## Testing API Connectivity

Use the provided test scripts to verify backend connectivity:

```powershell
# Validate API configuration and format
node validate-api-config.js

# Test basic connectivity
node test-basic-connectivity.js

# Test full API integration
node test-api-integration.js
```

The enhanced test function will provide comprehensive information:
- Table status including item count and size
- Warnings about missing environment variables
- API version and operation details
- Environment and execution information

## Troubleshooting

### Common Issues

1. **API Gateway CORS Configuration**: Ensure proper CORS headers are set in API Gateway
2. **Lambda Permissions**: Verify IAM roles allow access to required resources
3. **CloudWatch Logs**: Check Lambda logs for execution errors
4. **Authentication Token**: Ensure bearer token is properly set in UserDataService

### Debugging Commands

```powershell
# Test API Gateway directly
Invoke-RestMethod -Uri $env:VITE_API_BASE_URL -Method GET

# Run the API validation script
node validate-api-config.js
```

## Security Considerations

1. **Authorization**: Properly validate JWT tokens in Lambda function
2. **Input Validation**: Validate all input parameters and types
3. **Error Handling**: Return appropriate error codes without leaking implementation details
4. **Logging**: Log API access and errors for monitoring and troubleshooting

## Next Steps

1. **Backend Team**:
   - Implement CloudFormation and Lambda handler updates
   - Deploy updated CloudFormation template

2. **Frontend Team**:
   - Test connectivity with the updated backend
   - Verify that diagnostics information is complete
