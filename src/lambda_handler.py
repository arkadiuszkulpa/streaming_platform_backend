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

# Environment variables - populated from CloudFormation template
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')
SUBSCRIPTIONS_TABLE = os.environ.get('SUBSCRIPTIONS_TABLE')
SERVICE_PREFERENCES_TABLE = os.environ.get('SERVICE_PREFERENCES_TABLE')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')
FAMILY_GROUPS_TABLE = os.environ.get('FAMILY_GROUPS_TABLE')
MOVIES_TABLE = os.environ.get('MOVIES_TABLE')
WATCHLISTS_TABLE = os.environ.get('WATCHLISTS_TABLE')
WATCH_HISTORY_TABLE = os.environ.get('WATCH_HISTORY_TABLE')
PROFILES_TABLE = os.environ.get('STREAMING_PROFILES_TABLE')  # Aligned with ProfilesTable in template.yaml

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
        'USER_PROFILES_TABLE', 'SUBSCRIPTIONS_TABLE', 'SERVICE_PREFERENCES_TABLE',
        'USER_USAGE_TABLE', 'FAMILY_GROUPS_TABLE', 'MOVIES_TABLE',
        'WATCHLISTS_TABLE', 'WATCH_HISTORY_TABLE', 'STREAMING_PROFILES_TABLE',
        'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'USER_PROFILES_TABLE': USER_PROFILES_TABLE,
        'SUBSCRIPTIONS_TABLE': SUBSCRIPTIONS_TABLE,
        'SERVICE_PREFERENCES_TABLE': SERVICE_PREFERENCES_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
        'FAMILY_GROUPS_TABLE': FAMILY_GROUPS_TABLE,
        'MOVIES_TABLE': MOVIES_TABLE,
        'WATCHLISTS_TABLE': WATCHLISTS_TABLE,
        'WATCH_HISTORY_TABLE': WATCH_HISTORY_TABLE,
        'PROFILES_TABLE': PROFILES_TABLE,
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
                    'message': str(e),
                    'name': table_var
                }
                warnings.append(f"Cannot access table {table_var}: {str(e)}")
        else:
            table_status[table_name] = {
                'status': 'not_configured',
                'name': None
            }
            messages.append(f"Table {table_name} is not configured")
    
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
        'function': function_name,
        'lambda_name': function_name,
        'region': os.environ.get('AWS_REGION', 'unknown'),
        'version': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION', 'unknown'),
        'memory': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'unknown'),
        'execution_environment': execution_env,
        'environment': environment,
        'tables': table_status,
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
        handlers = {
            # Test operation
            'test': handle_test,
            
            # User Profile Operations
            'getUserProfile': handle_get_user_profile,
            'createUserProfile': handle_create_user_profile,
            'updateUserProfile': handle_update_user_profile,
            
            # Streaming Operations
            'getMovies': handle_get_movies,
            'getMovieDetails': handle_get_movie_details,
            'getWatchlist': handle_get_watchlist,
            'addToWatchlist': handle_add_to_watchlist,
            'removeFromWatchlist': handle_remove_from_watchlist,
            'getWatchHistory': handle_get_watch_history,
            'recordWatch': handle_record_watch,
            
            # Profile Operations
            'getProfiles': handle_get_profiles,
            'createProfile': handle_create_profile,
            'updateProfile': handle_update_profile,
            'deleteProfile': handle_delete_profile,
            
            # Family Group Operations
            'getFamilyGroup': handle_get_family_group,
            'createFamilyGroup': handle_create_family_group,
            'updateFamilyGroup': handle_update_family_group,
            'addFamilyMember': handle_add_family_member,
            'removeFamilyMember': handle_remove_family_member
        }
        
        handler = handlers.get(operation)
        if not handler:
            return create_response(400, {'error': f'Unknown operation: {operation}'})
            
        # Execute the handler
        result = handler(data)
        return create_response(200, result)
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error', 'details': str(e)})

# Placeholder handler functions - to be implemented
def handle_get_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getUserProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getUserProfile', 'data': data}

def handle_create_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for createUserProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'createUserProfile', 'data': data}

def handle_update_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updateUserProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'updateUserProfile', 'data': data}

def handle_get_movies(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getMovies operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getMovies', 'data': data}

def handle_get_movie_details(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getMovieDetails operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getMovieDetails', 'data': data}

def handle_get_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getWatchlist operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getWatchlist', 'data': data}

def handle_add_to_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for addToWatchlist operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'addToWatchlist', 'data': data}

def handle_remove_from_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for removeFromWatchlist operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'removeFromWatchlist', 'data': data}

def handle_get_watch_history(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getWatchHistory operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getWatchHistory', 'data': data}

def handle_record_watch(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for recordWatch operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'recordWatch', 'data': data}

def handle_get_profiles(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getProfiles operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getProfiles', 'data': data}

def handle_create_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for createProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'createProfile', 'data': data}

def handle_update_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updateProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'updateProfile', 'data': data}

def handle_delete_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for deleteProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'deleteProfile', 'data': data}

def handle_get_family_group(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getFamilyGroup operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getFamilyGroup', 'data': data}

def handle_create_family_group(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for createFamilyGroup operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'createFamilyGroup', 'data': data}

def handle_update_family_group(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updateFamilyGroup operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'updateFamilyGroup', 'data': data}

def handle_add_family_member(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for addFamilyMember operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'addFamilyMember', 'data': data}

def handle_remove_family_member(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for removeFamilyMember operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'removeFamilyMember', 'data': data}
