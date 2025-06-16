# MyAI4 API Integration Guide

## Overview

This document provides a quick-start guide for developers working with the MyAI4 centralized API approach.

## Architecture

The MyAI4 ecosystem uses a centralized Lambda function approach rather than AWS Amplify:

```
Frontend (React) → API Gateway → Centralized Lambda → DynamoDB Tables
```

All API requests flow through the `CentralizedApiService` class, which handles:
- Formatting requests for the centralized endpoint
- Authentication via JWT tokens
- Error handling and response parsing

## Connecting to the API

### Basic Usage

The frontend connects to the backend through the `UserDataService` class:

```typescript
// Import the service
import { userDataService } from '../services/UserDataService';

// Set authentication token (after user logs in)
userDataService.setAuthToken(jwtToken);

// Call API methods
const userProfile = await userDataService.getUserProfile(userId);
```

### Adding New API Operations

To add a new API operation:

1. **Backend**: Add a new handler function in `lambda_handler.py`:

```python
def handle_my_new_operation(data):
    # Process the operation
    user_id = data.get('userId')
    # ... implementation ...
    return result_data
```

2. **Backend**: Register the handler in the handlers dictionary:

```python
handlers = {
    # Existing handlers...
    'myNewOperation': handle_my_new_operation,
}
```

3. **Frontend**: Add a new method to `UserDataService.ts`:

```typescript
async myNewOperation(userId: string, otherParams): Promise<ResultType> {
  return this.apiCall<ResultType>('myNewOperation', { userId, ...otherParams });
}
```

## Troubleshooting

### Common Issues

1. **CORS Issues**: Ensure API Gateway has CORS enabled for your frontend origin
2. **Authentication Errors**: Check that the JWT token is valid and properly set
3. **Operation Not Found**: Verify that the operation name matches between frontend and backend

### Helpful Commands

```bash
# Validate API configuration
npm run validate-api

# Test basic connectivity
npm run test-api

# Fetch configuration from CloudFormation
npm run fetch-config
```

## Best Practices

1. **Strongly Type API Responses**: Use TypeScript interfaces for all API responses
2. **Handle Errors Gracefully**: Always wrap API calls in try/catch blocks
3. **Use Proper HTTP Methods**: GET for retrievals, POST for actions
4. **Log Minimally**: Only log needed information, avoid logging sensitive data

## References

See the full [BACKEND_INTEGRATION_GUIDE.md](./documentation/BACKEND_INTEGRATION_GUIDE.md) for detailed information about our approach.
