"""
MyAI4 Movie Lambda Handler
This Lambda function handles movie-related operations for the myAI4 platform.
It provides functionality to retrieve movie information, details, and search movies.
"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

# Environment variables - only those needed for movie operations
MOVIE_TABLE = os.environ.get('MOVIE_TABLE')  # Core table for this Lambda
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # For account verification
PROFILE_TABLE = os.environ.get('PROFILE_TABLE')  # For profile verification
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')  # For optional usage tracking

# Authentication-related environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')  # For verifying JWT tokens if handling auth directly

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
        'PROFILE_TABLE', 'SUBSCRIPTIONS_TABLE', 'SERVICE_PREFERENCES_TABLE',
        'USER_USAGE_TABLE', 'MOVIES_TABLE', 'WATCHLISTS_TABLE', 'WATCH_HISTORY_TABLE', 
        'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT', 'IDENTITY_POOL_PARAM_NAME'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'PROFILE_TABLE': PROFILE_TABLE,
        'SUBSCRIPTION_TABLE': SUBSCRIPTION_TABLE,
        'SERVICE_PREFERENCE_TABLE': SERVICE_PREFERENCE_TABLE,
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

def get_allowed_origin(request_origin: str) -> str:
    """Determine the appropriate CORS origin response"""
    environment = os.environ.get('ENVIRONMENT', 'dev')
    cloudfront_domain = os.environ.get('CLOUDFRONT_DOMAIN', '')
    local_origins_str = os.environ.get('LOCAL_ORIGINS', '')
    
    allowed_origins = set()
    
    # Production domains - always allow CloudFront and myai4 domains
    if environment == 'prod':
        # Add CloudFront domain
        if cloudfront_domain:
            allowed_origins.add(f"https://{cloudfront_domain}")
            
        # Add custom domains
        custom_domains = os.environ.get('CUSTOM_DOMAINS', '').split(',')
        for domain in custom_domains:
            if domain:
                allowed_origins.add(f"https://{domain.strip()}")
        
        print(f"🔍 Production mode - allowing domains: {allowed_origins}")
    
    # Development - allow CloudFront and localhost
    elif environment == 'dev':
        # Always add dev CloudFront
        if cloudfront_domain:
            allowed_origins.add(f"https://{cloudfront_domain}")
            
        # Add localhost origins
        if local_origins_str:
            local_origins = [o.strip() for o in local_origins_str.split(',') if o.strip()]
            allowed_origins.update(local_origins)
        print(f"🔍 Dev mode - allowing CloudFront and local: {allowed_origins}")
    
    print(f"🔍 Request Origin: {request_origin}")
    print(f"🔍 Allowed Origins: {allowed_origins}")
    
    # Return matching origin if found, otherwise default to CloudFront
    if request_origin and request_origin in allowed_origins:
        return request_origin
        
    # Default to CloudFront URL or * as last resort
    cloudfront_url = f"https://{cloudfront_domain}" if cloudfront_domain else "*"
    return cloudfront_url

def create_response(status_code: int, body: Dict[str, Any], event: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create an API Gateway response object with proper CORS headers"""
    # Get origin from request headers
    headers = event.get('headers', {}) if event else {}
    origin = headers.get('origin', headers.get('Origin', ''))
    
    # Determine allowed origin
    allowed_origin = get_allowed_origin(origin)
    
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': allowed_origin,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }
    
    # Add credentials header only if not using wildcard origin
    if allowed_origin != "*":
        response['headers']['Access-Control-Allow-Credentials'] = 'true'
    
    return response

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Movie Lambda handler"""
    try:
        # Log basic request info for debugging
        print(f"🔍 {event.get('httpMethod')} {event.get('path')}")
        
        # Handle OPTIONS requests for CORS preflight
        http_method = event.get('httpMethod', 'GET')
        if http_method == 'OPTIONS':
            print("✅ Handling OPTIONS preflight request")
            return create_response(200, {'message': 'CORS preflight response'}, event)
        
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
            return create_response(400, {'error': 'Operation parameter is required'}, event)
            
        # Route to appropriate handler
        handlers = {
            # Test operation
            'test': handle_test,
            
            # Account Operations
            'getAccount': handle_get_account,
            'updateAccount': handle_update_account,
            
            # User Profile Operations
            'getUserProfile': handle_get_user_profile,
            'createUserProfile': handle_create_user_profile,
            'updateUserProfile': handle_update_user_profile,
            
            # Streaming Operations
            'getMovies': handle_get_movies,
            'getMovieDetails': handle_get_movie_details,
            'getWatchlists': handle_get_watchlists,
            'getWatchlist': handle_get_watchlist,
            'addToWatchlist': handle_add_to_watchlist,
            'removeFromWatchlist': handle_remove_from_watchlist,
            'getWatchHistory': handle_get_watch_history,
            'recordWatch': handle_record_watch,
            
            # Profile Operations
            'getProfiles': handle_get_profiles,
            'getProfile': handle_get_profile,  # Added to match frontend
            'createProfile': handle_create_profile,
            'updateProfile': handle_update_profile,
            'deleteProfile': handle_delete_profile,
            'updateProfilePreferences': handle_update_profile_preferences,  # Added to match frontend

        }
        
        handler = handlers.get(operation)
        if not handler:
            return create_response(400, {'error': f'Unknown operation: {operation}'}, event)
            
        # Execute the handler
        result = handler(data)
        return create_response(200, result, event)
        
    except Exception as e:
        print(f"❌ Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Internal server error', 'details': str(e)}, event)

def handle_get_movies(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getMovies operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getMovies', 'data': data}

def handle_get_movie_details(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getMovieDetails operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getMovieDetails', 'data': data}
    return {'message': 'Not yet implemented', 'operation': 'getMovies', 'data': data}

def handle_get_movie_details(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for getMovieDetails operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'getMovieDetails', 'data': data}

# Removed SSM Parameter lookup functions - using direct environment variables now
