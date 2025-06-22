"""
MyAI4 Centralized Lambda Handler
This Lambda function serves as the centralized backend for the MyAI4 ecosystem.
It implements a router pattern to handle various operations for the streaming platform
and other MyAI4 services.
"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')

# Environment variables - populated from CloudFormation template
PROFILE_TABLE = os.environ.get('PROFILE_TABLE')  # This points to the ProfileTable resource
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # Table for user accounts (imported from infrastructure stack)
SUBSCRIPTION_TABLE = os.environ.get('SUBSCRIPTION_TABLE')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')
MOVIE_TABLE = os.environ.get('MOVIE_TABLE')
WATCHLIST_TABLE = os.environ.get('WATCHLIST_TABLE')
WATCH_HISTORY_TABLE = os.environ.get('WATCH_HISTORY_TABLE')
# Cognito resources imported from infrastructure stack
USER_POOL_ID = os.environ.get('USER_POOL_ID')
IDENTITY_POOL_ID = os.environ.get('IDENTITY_POOL_ID')

# Mock RapidAPI key function - remove when integrating
def get_rapidapi_key():
    """Get RapidAPI key from AWS Secrets Manager"""
    secret_name = os.environ.get('RAPIDAPI_SECRET_NAME')
    if not secret_name:
        raise ValueError("RAPIDAPI_SECRET_NAME environment variable not set")
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as error:
        print(f"Error retrieving secret {secret_name}: {str(error)}")
        raise error
    
    # Depending on whether the secret is a string or binary, one of these fields will be populated
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        # Parse the JSON string
        secret_dict = json.loads(secret)
        # Return the specific key value
        return secret_dict.get('rapidapikey')
    else:
        raise ValueError("Secret value is not in string format")

def handle_test(data: Dict[str, Any]) -> Dict[str, Any]:
    """Test handler for API connectivity and diagnostics"""
    # Get the Lambda function name from the context
    function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown')
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    
    # Check if we can access DynamoDB tables
    table_status = {}
    warnings = []
    messages = []
    # Check for required environment variables
    for env_var in [
        'PROFILE_TABLE', 'SUBSCRIPTION_TABLE', 'SERVICE_PREFERENCES_TABLE',
        'USER_USAGE_TABLE', 'MOVIES_TABLE', 'WATCHLIST_TABLE', 'WATCH_HISTORY_TABLE', 
        'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT', 'USER_POOL_ID', 'IDENTITY_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'PROFILE_TABLE': PROFILE_TABLE,
        'SUBSCRIPTION_TABLE': SUBSCRIPTION_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
        'MOVIE_TABLE': MOVIE_TABLE,
        'WATCHLIST_TABLE': WATCHLIST_TABLE,
        'WATCH_HISTORY_TABLE': WATCH_HISTORY_TABLE,
    }.items():
        if table_var:
            try:
                table = dynamodb.Table(table_var)
                # Get more detailed table information
                table_details = table.meta.client.describe_table(TableName=table_var)
                
                table_status[table_name] = {
                    'status': 'accessible',
                    'name': table_var,
                    'details': {
                        'item_count': table_details['Table'].get('ItemCount', 'unknown'),
                        'table_status': table_details['Table'].get('TableStatus', 'unknown'),
                        'size_bytes': table_details['Table'].get('TableSizeBytes', 'unknown')
                    }
                }
            except Exception as e:
                table_status[table_name] = {
                    'status': 'error',
                    'name': table_var,
                    'error': str(e)
                }
        else:
            table_status[table_name] = {
                'status': 'missing',
                'name': 'Table name not configured'
            }

    # Check environment variables for infrastructure resources
    parameter_status = {}
    if IDENTITY_POOL_ID:
        parameter_status['IDENTITY_POOL_ID'] = {
            'status': 'accessible',
            'value': IDENTITY_POOL_ID
        }
    else:
        parameter_status['IDENTITY_POOL_ID'] = {
            'status': 'missing',
            'error': 'Environment variable not set'
        }
    else:
        parameter_status['IDENTITY_POOL_ID'] = {
            'status': 'missing',
            'parameter_name': 'Parameter path not configured'
        }
    
    # Check for RapidAPI key
    try:
        _ = get_rapidapi_key()
        messages.append("RapidAPI key is accessible")
    except Exception as e:
        warnings.append(f"Cannot access RapidAPI key: {str(e)}")
    
    # Get Lambda execution environment
    execution_env = os.environ.get('AWS_EXECUTION_ENV', 'unknown')
    
    return {
        'message': 'MyAI4 Centralized API is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'request_time': datetime.utcnow().isoformat(),
        'data_received': data,
        'parameter_status': parameter_status,
        'function': function_name,
        'lambda_name': function_name,
        'region': os.environ.get('AWS_REGION', 'unknown'),
        'version': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION', 'unknown'),
        'memory': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'unknown'),
        'execution_environment': execution_env,
        'environment': environment,
        'tables': table_status,
        'parameters': parameter_status,
        'api_version': '1.0.0',
        'warnings': warnings,
        'messages': messages
    }

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create an API Gateway response object"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # For CORS support
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Centralized Lambda handler for MyAI4 ecosystem operations
    """
    try:
        # Check for OPTIONS request (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
            
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
        if operation == 'test':
            result = handle_test(data)
        elif operation == 'getAccount':
            result = handle_get_account(data)
        elif operation == 'updateAccount':
            result = handle_update_account(data)
        elif operation == 'createAccount':
            result = handle_create_account(data)
        else:            
            result = {'error': f"Unknown operation: {operation}"}
            return create_response(400, result)
        
        if result.get('statusCode'):
            # If result already has a statusCode, use it
            status_code = result.pop('statusCode')
            return create_response(status_code, result)
        else:
            # Default to 200 OK
            return create_response(200, result)
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error', 'details': str(e)})


# Removed SSM parameter functions and getter functions for environment variables
# Now directly using environment variables instead

def handle_get_account(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getAccount operation
    Gets account details for a user.
    
    Expected data:
    - accountId (required): The account ID (same as Cognito user ID/sub)
    - userId (deprecated): The Cognito user ID (for backward compatibility)
    """
    # Validate required parameters - support both accountId and userId for backward compatibility
    accountId = data.get('accountId') or data.get('userId')
    if not accountId:
        return {'error': 'accountId is required', 'statusCode': 400}
        
    # For working with the AccountTable, we use the accountId as userId
    userId = accountId  # The Cognito userId is the same as the accountId in our system
    
    # Use the accounts table directly from environment variables
    if not ACCOUNTS_TABLE:
        return {'error': 'Accounts table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(table_name)
        
        # Get the account from DynamoDB
        response = table.get_item(Key={'userId': userId})
        
        # Check if account exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'error': 'Account not found',
                'userId': userId
            }
        account = response['Item']
        
        # Always ensure accountId field exists for compatibility with the rest of the system
        # The Cognito userId is the same as the accountId in our system
        account['accountId'] = userId
        
        return {
            'statusCode': 200,
            'account': account,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error retrieving account: {str(e)}")
        return {
            'error': 'Failed to retrieve account',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getAccount: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_update_account(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateAccount operation
    Updates account details for a user.
    
    Expected data:
    - accountId (required): The account ID to update (same as Cognito user ID/sub)
    - userId (deprecated): The Cognito user ID (for backward compatibility)
    - updates (required): Object containing account updates, such as:
      - email (optional): The new email address
      - name (optional): The new name
      - preferences (optional): Updated preferences object
    """
    # Validate required parameters - support both accountId and userId for backward compatibility    accountId = data.get('accountId') or data.get('userId') 
    if not accountId:
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('updates'):
        return {'error': 'updates object is required', 'statusCode': 400}
    
    # For working with the AccountTable, we use the accountId as userId
    userId = accountId
    updates = data['updates']
      # Use the accounts table directly from environment variables
    if not ACCOUNT_TABLE:
        return {'error': 'Accounts table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(ACCOUNT_TABLE)
        
        # Build update expression
        update_expressions = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Update email if provided
        if 'email' in updates:
            update_expressions.append('#email = :email')
            expression_attribute_names['#email'] = 'email'
            expression_attribute_values[':email'] = updates['email']
            
        # Update name if provided
        if 'name' in updates:
            update_expressions.append('#name = :name')
            expression_attribute_names['#name'] = 'name'
            expression_attribute_values[':name'] = updates['name']
            
        # Update preferences if provided
        if 'preferences' in updates:
            update_expressions.append('#preferences = :preferences')
            expression_attribute_names['#preferences'] = 'preferences'
            expression_attribute_values[':preferences'] = updates['preferences']
        
        # Always update the updatedAt timestamp
        update_expressions.append('#updatedAt = :updatedAt')
        expression_attribute_names['#updatedAt'] = 'updatedAt'
        expression_attribute_values[':updatedAt'] = datetime.utcnow().isoformat()
        
        # If there's nothing to update, return early
        if len(update_expressions) == 1:  # Only has updatedAt
            return {
                'statusCode': 400,
                'error': 'No fields to update provided',
                'userId': userId
            }
        
        # Construct the update expression
        update_expression = 'SET ' + ', '.join(update_expressions)
        
        # Update the account
        response = table.update_item(
            Key={
                'userId': userId
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
          # Get the updated account
        updated_account = response.get('Attributes', {})
        
        # Ensure accountId is present in the response
        if 'accountId' not in updated_account:
            updated_account['accountId'] = userId
            
        # Return the updated account
        return {
            'statusCode': 200,
            'account': updated_account,
            'message': 'Account updated successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error updating account: {str(e)}")
        return {
            'error': 'Failed to update account',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in updateAccount: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_create_account(data: Dict[str, Any]) -> Dict[str, Any]:    
    """
    Create a new user account
    
    Expected data:
    - accountId (required): The account ID (same as Cognito user ID/sub)
    - userId (deprecated): The Cognito user ID (for backward compatibility)
    - email (required): User's email address
    - name (required): User's name
    """
    # Support both accountId and userId for backward compatibility
    accountId = data.get('accountId') or data.get('userId')
    
    # Check required fields
    if not accountId:
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('email'):
        return {'error': 'email is required', 'statusCode': 400}
    if not data.get('name'):
        return {'error': 'name is required', 'statusCode': 400}
    
    # For working with the AccountTable, we use accountId as userId
    userId = accountId
      # Use the accounts table directly from environment variables
    if not ACCOUNT_TABLE:
        return {'error': 'Accounts table not configured', 'statusCode': 500}
        
    try:
        table = dynamodb.Table(ACCOUNT_TABLE)
        
        # Create the account item
        account_item = {
            'userId': userId,  # For AccountTable key compatibility
            'accountId': accountId,  # Explicitly set accountId
            'email': data['email'],
            'name': data['name'],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'status': 'active',
            'subscriptionTier': data.get('subscriptionTier', 'free')
        }
        
        # Put the item in the table
        table.put_item(Item=account_item)
        
        return {
            'statusCode': 201,
            'account': account_item,
            'message': 'Account created successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error creating account: {str(e)}")
        return {
            'error': 'Failed to create account',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in createAccount: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }
