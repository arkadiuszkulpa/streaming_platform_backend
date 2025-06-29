"""
MyAI4 Profile Settings Lambda Handler
This Lambda function handles profile settings operations for the myAI4 platform.
It provides functionality to manage profile settings, including content restrictions and PIN protection.
"""
import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

# Environment variables - only those needed for profile settings operations
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # For account verification
PROFILE_TABLE = os.environ.get('PROFILE_TABLE')  # For profile verification
PROFILE_SETTINGS_TABLE = os.environ.get('PROFILE_SETTINGS_TABLE')  # Core table for this Lambda
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')  # For optional usage tracking

# Authentication-related environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')  # For verifying JWT tokens if handling auth directly
IDENTITY_POOL_ID = os.environ.get('IDENTITY_POOL_ID')  # For client-side authentication


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
        'ACCOUNT_TABLE', 'PROFILE_TABLE', 'PROFILE_SETTINGS_TABLE',
        'USER_USAGE_TABLE', 'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT',
        'USER_POOL_ID', 'IDENTITY_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} not configured")
    
    # Check all tables
    for table_name, table_var in {
        'ACCOUNT_TABLE': ACCOUNT_TABLE,
        'PROFILE_TABLE': PROFILE_TABLE,
        'PROFILE_SETTINGS_TABLE': PROFILE_SETTINGS_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
    }.items():
        if table_var:
            try:
                table = dynamodb.Table(table_var)
                item_count = table.scan(Select='COUNT')['Count']
                table_status[table_name] = {
                    'status': 'accessible',
                    'name': table_var,
                    'item_count': item_count
                }
                messages.append(f"Table {table_var} contains {item_count} items")
            except ClientError as e:
                table_status[table_name] = {
                    'status': 'error',
                    'name': table_var,
                    'error': str(e)
                }
                warnings.append(f"Error accessing table {table_var}: {str(e)}")
        else:
            table_status[table_name] = {
                'status': 'not_configured',
                'error': 'Environment variable not set'
            }
            warnings.append(f"Table {table_name} not configured (missing env variable)")
    
    # Check infrastructure resources
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
        'message': 'MyAI4 Profile Settings API is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'request_time': datetime.utcnow().isoformat(),
        'data_received': data,
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
    Profile Settings Lambda handler for myAI4 platform
    Handles operations related to profile settings, including content restrictions and PIN protection
    """
    try:
        # Check for OPTIONS request (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Parse the operation from query parameters or request body
        http_method = event.get('httpMethod', 'GET')
        
        if http_method == 'GET':
            # For GET requests, look for operation in query parameters
            query_params = event.get('queryStringParameters', {}) or {}
            operation = query_params.get('operation')
            data = query_params
        else:
            # For other HTTP methods, look for operation in body
            body = event.get('body', '{}')
            if isinstance(body, str):
                body_json = json.loads(body)
            else:
                body_json = body
                
            operation = body_json.get('operation')
            data = body_json
            
        if not operation:
            return create_response(400, {'error': 'Missing operation parameter'})
            
        # Route to appropriate handler
        if operation == 'test':
            result = handle_test(data)
        elif operation == 'getProfileSettings':
            result = handle_get_profile_settings(data)
        elif operation == 'updateProfileSettings':
            result = handle_update_profile_settings(data)
        elif operation == 'setProfilePin':
            result = handle_set_profile_pin(data)
        elif operation == 'verifyProfilePin':
            result = handle_verify_profile_pin(data)
        elif operation == 'getContentRestrictions':
            result = handle_get_content_restrictions(data)
        elif operation == 'updateContentRestrictions':
            result = handle_update_content_restrictions(data)
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
        error_message = str(e)
        print(f"Error in lambda_handler: {error_message}")
        return create_response(500, {
            'error': 'Internal server error',
            'details': error_message
        })


def handle_get_profile_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getProfileSettings operation
    Retrieves settings for a user profile
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to retrieve settings for
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    
    if not PROFILE_SETTINGS_TABLE:
        return {'error': 'Profile settings table not configured', 'statusCode': 500}
    
    try:
        # Check if profile exists first
        if PROFILE_TABLE:
            profile_table = dynamodb.Table(PROFILE_TABLE)
            profile_response = profile_table.get_item(
                Key={
                    'accountId': accountId,
                    'profileId': profileId
                }
            )
            if 'Item' not in profile_response:
                return {'error': 'Profile not found', 'statusCode': 404}
        
        # Get profile settings
        settings_table = dynamodb.Table(PROFILE_SETTINGS_TABLE)
        response = settings_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' in response:
            # Don't return PIN data in the response for security
            settings = response['Item']
            if 'pinHash' in settings:
                settings['pinProtected'] = True
                del settings['pinHash']
            
            return {
                'settings': settings,
                'message': 'Profile settings retrieved successfully'
            }
        else:
            # If settings don't exist, return default settings
            return {
                'settings': {
                    'accountId': accountId,
                    'profileId': profileId,
                    'pinProtected': False,
                    'contentRestrictions': {
                        'maxRating': 'PG-13',
                        'blockedGenres': [],
                        'blockedTitles': [],
                        'blockedActors': [],
                        'blockedDirectors': []
                    },
                    'createdAt': datetime.utcnow().isoformat()
                },
                'message': 'Default profile settings retrieved (no custom settings found)'
            }
    except ClientError as e:
        print(f"DynamoDB error in getProfileSettings: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getProfileSettings: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_update_profile_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateProfileSettings operation
    Updates settings for a user profile
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to update settings for
    - settings (required): The settings object to update
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    if not data.get('settings'):
        return {'error': 'Missing required parameter: settings', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    settings = data['settings']
    
    if not PROFILE_SETTINGS_TABLE:
        return {'error': 'Profile settings table not configured', 'statusCode': 500}
    
    try:
        # Check if profile exists first
        if PROFILE_TABLE:
            profile_table = dynamodb.Table(PROFILE_TABLE)
            profile_response = profile_table.get_item(
                Key={
                    'accountId': accountId,
                    'profileId': profileId
                }
            )
            if 'Item' not in profile_response:
                return {'error': 'Profile not found', 'statusCode': 404}
        
        # Update profile settings
        settings_table = dynamodb.Table(PROFILE_SETTINGS_TABLE)
        
        # Don't allow direct update of PIN hash for security
        if 'pinHash' in settings:
            del settings['pinHash']
        
        # Add timestamp
        settings['updatedAt'] = datetime.utcnow().isoformat()
        
        # Include key attributes
        settings['accountId'] = accountId
        settings['profileId'] = profileId
        
        response = settings_table.put_item(Item=settings)
        
        return {
            'message': 'Profile settings updated successfully',
            'settings': {
                'accountId': accountId,
                'profileId': profileId,
                'updatedAt': settings['updatedAt']
            }
        }
    except ClientError as e:
        print(f"DynamoDB error in updateProfileSettings: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in updateProfileSettings: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_set_profile_pin(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for setProfilePin operation
    Sets a PIN for a profile for parental controls
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to set PIN for
    - pin (required): The PIN to set (will be hashed before storage)
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    if not data.get('pin'):
        return {'error': 'Missing required parameter: pin', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    pin = data['pin']
    
    if not PROFILE_SETTINGS_TABLE:
        return {'error': 'Profile settings table not configured', 'statusCode': 500}
    
    try:
        # In a real implementation, we would hash the PIN
        # For demo purposes, we'll store a placeholder hash
        pin_hash = f"hashed_{pin}_value"
        
        settings_table = dynamodb.Table(PROFILE_SETTINGS_TABLE)
        
        # Get current settings first
        response = settings_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' in response:
            settings = response['Item']
        else:
            # Create default settings if none exist
            settings = {
                'accountId': accountId,
                'profileId': profileId,
                'contentRestrictions': {
                    'maxRating': 'PG-13',
                    'blockedGenres': [],
                    'blockedTitles': [],
                    'blockedActors': [],
                    'blockedDirectors': []
                },
                'createdAt': datetime.utcnow().isoformat()
            }
        
        # Update PIN settings
        settings['pinHash'] = pin_hash
        settings['pinProtected'] = True
        settings['updatedAt'] = datetime.utcnow().isoformat()
        
        # Save settings
        settings_table.put_item(Item=settings)
        
        return {
            'message': 'Profile PIN set successfully',
            'profileId': profileId,
            'pinProtected': True
        }
    except ClientError as e:
        print(f"DynamoDB error in setProfilePin: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in setProfilePin: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_verify_profile_pin(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for verifyProfilePin operation
    Verifies a PIN for a profile for parental controls
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to verify PIN for
    - pin (required): The PIN to verify
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    if not data.get('pin'):
        return {'error': 'Missing required parameter: pin', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    pin = data['pin']
    
    if not PROFILE_SETTINGS_TABLE:
        return {'error': 'Profile settings table not configured', 'statusCode': 500}
    
    try:
        settings_table = dynamodb.Table(PROFILE_SETTINGS_TABLE)
        
        # Get current settings
        response = settings_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' not in response or 'pinHash' not in response['Item']:
            return {
                'error': 'Profile is not PIN protected',
                'verified': False,
                'statusCode': 400
            }
        
        # In a real implementation, we would hash the PIN and compare
        # For demo purposes, we'll use our placeholder hash format
        pin_hash = f"hashed_{pin}_value"
        stored_hash = response['Item']['pinHash']
        
        if pin_hash == stored_hash:
            return {
                'message': 'PIN verified successfully',
                'verified': True
            }
        else:
            return {
                'message': 'Invalid PIN',
                'verified': False
            }
    except ClientError as e:
        print(f"DynamoDB error in verifyProfilePin: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in verifyProfilePin: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_get_content_restrictions(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getContentRestrictions operation
    Gets content restrictions for a profile
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to get restrictions for
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    
    if not PROFILE_SETTINGS_TABLE:
        return {'error': 'Profile settings table not configured', 'statusCode': 500}
    
    try:
        settings_table = dynamodb.Table(PROFILE_SETTINGS_TABLE)
        
        response = settings_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' in response and 'contentRestrictions' in response['Item']:
            return {
                'contentRestrictions': response['Item']['contentRestrictions'],
                'message': 'Content restrictions retrieved successfully'
            }
        else:
            # Return default restrictions if none found
            default_restrictions = {
                'maxRating': 'PG-13',
                'blockedGenres': [],
                'blockedTitles': [],
                'blockedActors': [],
                'blockedDirectors': []
            }
            
            return {
                'contentRestrictions': default_restrictions,
                'message': 'Default content restrictions retrieved (no custom restrictions found)'
            }
    except ClientError as e:
        print(f"DynamoDB error in getContentRestrictions: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getContentRestrictions: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_update_content_restrictions(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateContentRestrictions operation
    Updates content restrictions for a profile
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to update restrictions for
    - contentRestrictions (required): The content restrictions object to update
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    if not data.get('contentRestrictions'):
        return {'error': 'Missing required parameter: contentRestrictions', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    content_restrictions = data['contentRestrictions']
    
    if not PROFILE_SETTINGS_TABLE:
        return {'error': 'Profile settings table not configured', 'statusCode': 500}
    
    try:
        settings_table = dynamodb.Table(PROFILE_SETTINGS_TABLE)
        
        # Get existing settings
        response = settings_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' in response:
            settings = response['Item']
        else:
            # Create new settings if none exist
            settings = {
                'accountId': accountId,
                'profileId': profileId,
                'createdAt': datetime.utcnow().isoformat()
            }
        
        # Update content restrictions
        settings['contentRestrictions'] = content_restrictions
        settings['updatedAt'] = datetime.utcnow().isoformat()
        
        # Save settings
        settings_table.put_item(Item=settings)
        
        return {
            'message': 'Content restrictions updated successfully',
            'contentRestrictions': content_restrictions
        }
    except ClientError as e:
        print(f"DynamoDB error in updateContentRestrictions: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in updateContentRestrictions: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }
