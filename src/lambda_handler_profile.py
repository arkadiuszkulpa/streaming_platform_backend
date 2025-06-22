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
PROFILES_TABLE = os.environ.get('PROFILES_TABLE')  # This points to the ProfilesTable resource
ACCOUNTS_TABLE = os.environ.get('ACCOUNTS_TABLE')  # Table for user accounts (imported from infrastructure stack)
SUBSCRIPTIONS_TABLE = os.environ.get('SUBSCRIPTIONS_TABLE')
SERVICE_PREFERENCES_TABLE = os.environ.get('SERVICE_PREFERENCES_TABLE')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')
MOVIES_TABLE = os.environ.get('MOVIES_TABLE')
WATCHLISTS_TABLE = os.environ.get('WATCHLISTS_TABLE')
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
        'PROFILES_TABLE', 'SUBSCRIPTIONS_TABLE', 'SERVICE_PREFERENCES_TABLE',
        'USER_USAGE_TABLE', 'MOVIES_TABLE', 'WATCHLISTS_TABLE', 'WATCH_HISTORY_TABLE', 
        'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT', 'IDENTITY_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'PROFILES_TABLE': PROFILES_TABLE,
        'SUBSCRIPTIONS_TABLE': SUBSCRIPTIONS_TABLE,
        'SERVICE_PREFERENCES_TABLE': SERVICE_PREFERENCES_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
        'MOVIES_TABLE': MOVIES_TABLE,
        'WATCHLISTS_TABLE': WATCHLISTS_TABLE,
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
    """
    Handler for getUserProfile operation
    Retrieves a single user's profile from DynamoDB

    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to retrieve
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'profileId is required', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # Query for the specific profile
        response = table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        # Check if profile exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'error': 'Profile not found',
                'accountId': accountId,
                'profileId': profileId
            }
        
        profile = response['Item']
        
        return {
            'statusCode': 200,
            'profile': profile,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error retrieving user profile: {str(e)}")
        return {
            'error': 'Failed to retrieve profile',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getUserProfile: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_create_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for createUserProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'createUserProfile', 'data': data}

def handle_update_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updateUserProfile operation"""
    # TODO: Implement this handler
    return {'message': 'Not yet implemented', 'operation': 'updateUserProfile', 'data': data}

def handle_get_profiles(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getProfiles operation
    Retrieves all profiles associated with a specific user account
    
    Expected data:
    - accountId (required): The ID of the account whose profiles should be retrieved
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    
    accountId = data['accountId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # Query for all profiles belonging to this account using accountId as partition key
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId)
        )
        
        profiles = response.get('Items', [])
        
        # Handle pagination if there are more results
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            profiles.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'profiles': profiles,
            'count': len(profiles),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error retrieving account profiles: {str(e)}")
        return {
            'error': 'Failed to retrieve profiles',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getProfiles: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

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
      - preferences (optional): Dictionary of viewing preferences
      - parentalControls (optional): Dictionary of parental control settings
    """
    # Validate required parameters
    if not data.get('profile'):
        return {'error': 'profile object is required', 'statusCode': 400}
    
    profile_data = data['profile']
    
    if not profile_data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not profile_data.get('name'):
        return {'error': 'name is required', 'statusCode': 400}
    
    accountId = profile_data['accountId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # Use the provided profileId or generate a new one
        profileId = profile_data.get('profileId', f"profile_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{accountId[-6:]}")
        
        # Set default preferences if none provided
        default_preferences = {
            'preferredGenres': [],
            'dislikedGenres': [],
            'contentFilters': []
        }
        
        # Prepare profile item with structure matching frontend Profile type
        profile_item = {
            'accountId': accountId,
            'profileId': profileId,
            'name': profile_data['name'],
            'avatar': profile_data.get('avatar', ''),
            'isKidsProfile': profile_data.get('isKidsProfile', False),
            'parentalControls': profile_data.get('parentalControls', {}),
            'preferences': profile_data.get('preferences', default_preferences),
            'createdAt': profile_data.get('createdAt', datetime.utcnow().isoformat()),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Add the profile to DynamoDB
        table.put_item(Item=profile_item)
        
        return {
            'statusCode': 201,  # Created
            'profile': profile_item,
            'message': 'Profile created successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error creating user profile: {str(e)}")
        return {
            'error': 'Failed to create profile',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in createProfile: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_update_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateProfile operation
    Updates an existing profile for a user
    
    Expected data:
    - profileId (required): The ID of the profile to update
    - updates (required): Object containing profile updates with any of these fields:
      - name (optional): The updated name of the profile
      - isKidsProfile (optional): Boolean indicating if this is a child profile
      - preferences (optional): Dictionary of updated viewing preferences
      - avatar (optional): Avatar identifier or URL
      - parentalControls (optional): Dictionary of parental control settings
    """
    # Validate required parameters
    if not data.get('profileId'):
        return {'error': 'profileId is required', 'statusCode': 400}
    if not data.get('updates'):
        return {'error': 'updates object is required', 'statusCode': 400}
    
    profileId = data['profileId']
    updates = data['updates']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # First get the profile to access its accountId
        response = table.query(
            IndexName='ProfileIdIndex',  # Add this GSI in the CloudFormation template
            KeyConditionExpression=boto3.dynamodb.conditions.Key('profileId').eq(profileId),
            Limit=1
        )
        
        if not response.get('Items'):
            return {
                'statusCode': 404,
                'error': 'Profile not found',
                'profileId': profileId
            }
            
        profile = response['Items'][0]
        accountId = profile['accountId']
        
        # Build update expression
        update_expressions = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Update name if provided
        if 'name' in updates:
            update_expressions.append('#name = :name')
            expression_attribute_names['#name'] = 'name'
            expression_attribute_values[':name'] = updates['name']
            
        # Update isKidsProfile if provided
        if 'isKidsProfile' in updates:
            update_expressions.append('#isKidsProfile = :isKidsProfile')
            expression_attribute_names['#isKidsProfile'] = 'isKidsProfile'
            expression_attribute_values[':isKidsProfile'] = updates['isKidsProfile']
            
        # Update preferences if provided
        if 'preferences' in updates:
            update_expressions.append('#preferences = :preferences')
            expression_attribute_names['#preferences'] = 'preferences'
            expression_attribute_values[':preferences'] = updates['preferences']
            
        # Update avatar if provided
        if 'avatar' in updates:
            update_expressions.append('#avatar = :avatar')
            expression_attribute_names['#avatar'] = 'avatar'
            expression_attribute_values[':avatar'] = updates['avatar']
            
        # Update parentalControls if provided
        if 'parentalControls' in updates:
            update_expressions.append('#parentalControls = :parentalControls')
            expression_attribute_names['#parentalControls'] = 'parentalControls'
            expression_attribute_values[':parentalControls'] = updates['parentalControls']
        
        # Always update the updatedAt timestamp
        update_expressions.append('#updatedAt = :updatedAt')
        expression_attribute_names['#updatedAt'] = 'updatedAt'
        expression_attribute_values[':updatedAt'] = datetime.utcnow().isoformat()
        
        # If there's nothing to update, return early
        if len(update_expressions) <= 1:  # Only has updatedAt
            return {
                'statusCode': 400,
                'error': 'No fields to update provided',
                'profileId': profileId
            }
        
        # Construct the update expression
        update_expression = 'SET ' + ', '.join(update_expressions)
        
        # Update the profile
        response = table.update_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # Return the updated profile
        return {
            'statusCode': 200,
            'profile': response.get('Attributes', {}),
            'message': 'Profile updated successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except ClientError as e:
        print(f"Error updating user profile: {str(e)}")
        return {
            'error': 'Failed to update profile',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in updateProfile: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

# Removed SSM Parameter lookup function - using direct environment variables now