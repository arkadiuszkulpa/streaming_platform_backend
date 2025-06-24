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
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')

# Get allowed origins from environment variables
# This is set via CloudFormation in the function environment
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',')

# Environment variables - populated from CloudFormation template
PROFILE_TABLE = os.environ.get('PROFILE_TABLE')  # This points to the ProfilesTable resource
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # Table for user accounts (imported from infrastructure stack)
SUBSCRIPTIONS_TABLE = os.environ.get('SUBSCRIPTION_TABLE')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')

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
        'ACCOUNT_TABLE', 'PROFILE_TABLE', 'SUBSCRIPTION_TABLE', 'USER_USAGE_TABLE',
        'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT', 'IDENTITY_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'ACCOUNT_TABLE': ACCOUNT_TABLE,
        'PROFILE_TABLE': PROFILE_TABLE,
        'SUBSCRIPTION_TABLE': SUBSCRIPTIONS_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE
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

def is_origin_allowed(origin: str) -> bool:
    """Check if the provided origin is allowed"""
    if not origin:
        return False
        
    # Strip any trailing slash for comparison
    if origin.endswith('/'):
        origin = origin[:-1]
        
    # Direct match check
    if origin in ALLOWED_ORIGINS:
        return True
        
    # Handle wildcard domains like *.cloudfront.net
    for allowed_origin in ALLOWED_ORIGINS:
        if allowed_origin.startswith('https://*.'):
            # Extract the domain suffix pattern (e.g., 'cloudfront.net')
            domain_suffix = allowed_origin[10:]  # Remove 'https://*.' prefix
            
            # Check if origin matches the pattern
            if origin.startswith('https://') and origin[8:].endswith(domain_suffix):
                return True
                
    return False

def create_response(status_code: int, body: Dict[str, Any], origin: Optional[str] = None) -> Dict[str, Any]:
    """Create an API Gateway response object with proper CORS headers"""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
    
    # If origin is provided and allowed, add CORS headers with specific origin
    if origin and is_origin_allowed(origin):
        response['headers'].update({
            'Access-Control-Allow-Origin': origin,  # Echo back the specific allowed origin
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-CSRF-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Credentials': 'true'
        })
    
    return response

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Centralized Lambda handler for MyAI4 ecosystem operations
    """
    try:
        # Extract origin from request headers (case-insensitive)
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        origin = headers.get('origin')
        
        # Check for OPTIONS request (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'}, origin)
            
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
            return create_response(400, {'error': 'Operation parameter is required'}, origin)
            
        # Route to appropriate handler
        handlers = {
            # Test operation
            'test': handle_test,
            
            # Profile Operations
            'getProfiles': handle_get_profiles,
            'getProfile': handle_get_profile,
            'createProfile': handle_create_profile,
            'updateProfile': handle_update_profile,
            'deleteProfile': handle_delete_profile
        }
        
        handler = handlers.get(operation)
        if not handler:
            return create_response(400, {'error': f'Unknown operation: {operation}'}, origin)
            
        # Execute the handler
        result = handler(data)
        return create_response(200, result, origin)
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error', 'details': str(e)}, origin)

def handle_get_profiles(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getProfiles operation
    Retrieves all profiles associated with a specific user account
    
    Expected data:
    - accountId (required): The ID of the account whose profiles should be retrieved
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId'}
    
    accountId = data['accountId']
    
    if not PROFILE_TABLE:
        return {'error': 'PROFILES_TABLE environment variable is not configured'}
    
    try:
        # Query the profiles for this account
        table = dynamodb.Table(PROFILE_TABLE)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId)
        )
        
        if 'Items' not in response or not response['Items']:
            return {'profiles': []}
        
        # Return the profiles
        return {'profiles': response['Items']}
    
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return {'error': f'Database error: {str(e)}'}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': f'Unexpected error: {str(e)}'}

def handle_get_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getUserProfile operation
    Retrieves a single user's profile from DynamoDB

    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to retrieve
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId'}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId'}
    
    accountId = data['accountId']
    profileId = data['profileId']
    
    if not PROFILE_TABLE:
        return {'error': 'PROFILE_TABLE environment variable is not configured'}
    
    try:
        # Get the profile from DynamoDB
        table = dynamodb.Table(PROFILE_TABLE)
        response = table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' not in response:
            return {'error': f'Profile not found for accountId: {accountId}, profileId: {profileId}', 'statusCode': 404}
        
        # Return the profile
        return {'profile': response['Item']}
    
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return {'error': f'Database error: {str(e)}'}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': f'Unexpected error: {str(e)}'}

def handle_create_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for createProfile operation
    Creates a new profile for a user
    
    Expected data:
    - profile (required): Profile object containing:
      - accountId (required): The ID of the user account
      - name (required): The name of the profile
      - isKidsProfile (optional): Boolean indicating if this is a child profile
      - avatar (optional): Avatar identifier or URL
    """
    # Validate required parameters
    if not data.get('profile'):
        return {'error': 'Missing required parameter: profile'}
    
    profile_data = data['profile']
    
    if not profile_data.get('accountId'):
        return {'error': 'Missing required parameter: profile.accountId'}
    if not profile_data.get('name'):
        return {'error': 'Missing required parameter: profile.name'}
    
    accountId = profile_data['accountId']
    
    if not PROFILE_TABLE:
        return {'error': 'PROFILES_TABLE environment variable is not configured'}
    
    try:
        # Add timestamp if not provided
        if not profile_data.get('createdAt'):
            profile_data['createdAt'] = datetime.utcnow().isoformat()
        
        # Ensure profileId is present
        if not profile_data.get('profileId'):
            import uuid
            profile_data['profileId'] = str(uuid.uuid4())
            
        # Store the profile in DynamoDB
        table = dynamodb.Table(PROFILE_TABLE)
        table.put_item(Item=profile_data)
        
        # Return the created profile
        return {'profile': profile_data}
    
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return {'error': f'Database error: {str(e)}'}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': f'Unexpected error: {str(e)}'}

def handle_update_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updateProfile operation
    Updates an existing profile with new information
    
    Expected data:
    - accountId (required): The ID of the user account
    - profileId (required): The ID of the profile to update
    - updates (required): Dictionary of fields to update
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId'}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId'}
    if not data.get('updates'):
        return {'error': 'Missing required parameter: updates'}
    
    accountId = data['accountId']
    profileId = data['profileId']
    updates = data['updates']
    
    if not PROFILE_TABLE:
        return {'error': 'PROFILES_TABLE environment variable is not configured'}
    
    try:
        # First, check if the profile exists
        table = dynamodb.Table(PROFILE_TABLE)
        response = table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' not in response:
            return {'error': f'Profile not found for accountId: {accountId}, profileId: {profileId}', 'statusCode': 404}
        
        existing_profile = response['Item']
        
        # Add timestamp for update
        updates['updatedAt'] = datetime.utcnow().isoformat()
        
        # Merge updates with existing profile
        updated_profile = {**existing_profile, **updates}
        
        # Update the profile in DynamoDB
        table.put_item(Item=updated_profile)
        
        # Return the updated profile
        return {'profile': updated_profile}
    
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return {'error': f'Database error: {str(e)}'}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': f'Unexpected error: {str(e)}'}

def handle_delete_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for deleteProfile operation
    Deletes a profile from DynamoDB
    
    Expected data:
    - accountId (required): The ID of the user account
    - profileId (required): The ID of the profile to delete
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId'}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId'}
    
    accountId = data['accountId']
    profileId = data['profileId']
    
    if not PROFILE_TABLE:
        return {'error': 'PROFILES_TABLE environment variable is not configured'}
    
    try:
        # Delete the profile from DynamoDB
        table = dynamodb.Table(PROFILE_TABLE)
        table.delete_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        # Return success
        return {'message': f'Profile {profileId} deleted successfully'}
    
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return {'error': f'Database error: {str(e)}'}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {'error': f'Unexpected error: {str(e)}'}