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
PROFILES_TABLE = os.environ.get('PROFILES_TABLE')  # This now points to the ProfilesTable resource
SUBSCRIPTIONS_TABLE = os.environ.get('SUBSCRIPTIONS_TABLE')
SERVICE_PREFERENCES_TABLE = os.environ.get('SERVICE_PREFERENCES_TABLE')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')
FAMILY_GROUPS_TABLE = os.environ.get('FAMILY_GROUPS_TABLE')
MOVIES_TABLE = os.environ.get('MOVIES_TABLE')
WATCHLISTS_TABLE = os.environ.get('WATCHLISTS_TABLE')
WATCH_HISTORY_TABLE = os.environ.get('WATCH_HISTORY_TABLE')
# SSM Parameter path for Identity Pool ID
IDENTITY_POOL_PARAM_NAME = os.environ.get('IDENTITY_POOL_PARAM_NAME')

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
        'USER_USAGE_TABLE', 'FAMILY_GROUPS_TABLE', 'MOVIES_TABLE',
        'WATCHLISTS_TABLE', 'WATCH_HISTORY_TABLE', 
        'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT', 'IDENTITY_POOL_PARAM_NAME'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'PROFILES_TABLE': PROFILES_TABLE,
        'SUBSCRIPTIONS_TABLE': SUBSCRIPTIONS_TABLE,
        'SERVICE_PREFERENCES_TABLE': SERVICE_PREFERENCES_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
        'FAMILY_GROUPS_TABLE': FAMILY_GROUPS_TABLE,
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

    # Check SSM Parameter access
    parameter_status = {}
    if IDENTITY_POOL_PARAM_NAME:
        try:
            identity_pool_id = get_identity_pool_id()
            parameter_status['IDENTITY_POOL_ID'] = {
                'status': 'accessible',
                'parameter_name': IDENTITY_POOL_PARAM_NAME,
                'value': identity_pool_id
            }
        except Exception as e:
            parameter_status['IDENTITY_POOL_ID'] = {
                'status': 'error',
                'parameter_name': IDENTITY_POOL_PARAM_NAME,
                'error': str(e)
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
    """
    Handler for getUserProfile operation
    Retrieves a single user's profile from DynamoDB

    Expected data:
    - userId (required): The ID of the user
    - profileId (required): The ID of the profile to retrieve
    """
    # Validate required parameters
    if not data.get('userId'):
        return {'error': 'userId is required', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'profileId is required', 'statusCode': 400}
    
    userId = data['userId']
    profileId = data['profileId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # Query for the specific profile
        response = table.get_item(
            Key={
                'userId': userId,
                'profileId': profileId
            }
        )
        
        # Check if profile exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'error': 'Profile not found',
                'userId': userId,
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
    """
    Handler for getProfiles operation
    Retrieves all profiles associated with a specific user account
    
    Expected data:
    - userId (required): The ID of the user whose profiles should be retrieved
    """
    # Validate required parameters
    if not data.get('userId'):
        return {'error': 'userId is required', 'statusCode': 400}
    
    userId = data['userId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # Query for all profiles belonging to this user
        # Assuming the table has a GSI on userId, or userId is the partition key
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(userId)
        )
        
        profiles = response.get('Items', [])
        
        # Handle pagination if there are more results
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(userId),
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
        print(f"Error retrieving user profiles: {str(e)}")
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
    - userId (required): The ID of the user
    - profileName (required): The name of the profile
    - isChild (optional): Boolean indicating if this is a child profile
    - preferences (optional): Dictionary of viewing preferences
    - avatarUrl (optional): URL to profile avatar image
    """
    # Validate required parameters
    if not data.get('userId'):
        return {'error': 'userId is required', 'statusCode': 400}
    if not data.get('profileName'):
        return {'error': 'profileName is required', 'statusCode': 400}
    
    userId = data['userId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # Generate a unique profileId
        profileId = f"profile_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{userId[-6:]}"
        
        # Prepare profile item
        profile_item = {
            'userId': userId,
            'profileId': profileId,
            'profileName': data['profileName'],
            'isChild': data.get('isChild', False),
            'preferences': data.get('preferences', {}),
            'avatarUrl': data.get('avatarUrl', ''),
            'createdAt': datetime.utcnow().isoformat(),
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
    - userId (required): The ID of the user
    - profileId (required): The ID of the profile to update
    - profileName (optional): The updated name of the profile
    - isChild (optional): Boolean indicating if this is a child profile
    - preferences (optional): Dictionary of updated viewing preferences
    - avatarUrl (optional): URL to profile avatar image
    """
    # Validate required parameters
    if not data.get('userId'):
        return {'error': 'userId is required', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'profileId is required', 'statusCode': 400}
    
    userId = data['userId']
    profileId = data['profileId']
    
    if not PROFILES_TABLE:
        return {'error': 'Profiles table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        
        # First check if the profile exists
        response = table.get_item(
            Key={
                'userId': userId,
                'profileId': profileId
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'error': 'Profile not found',
                'userId': userId,
                'profileId': profileId
            }
        
        # Build update expression
        update_expressions = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Update profileName if provided
        if 'profileName' in data:
            update_expressions.append('#profileName = :profileName')
            expression_attribute_names['#profileName'] = 'profileName'
            expression_attribute_values[':profileName'] = data['profileName']
            
        # Update isChild if provided
        if 'isChild' in data:
            update_expressions.append('#isChild = :isChild')
            expression_attribute_names['#isChild'] = 'isChild'
            expression_attribute_values[':isChild'] = data['isChild']
            
        # Update preferences if provided
        if 'preferences' in data:
            update_expressions.append('#preferences = :preferences')
            expression_attribute_names['#preferences'] = 'preferences'
            expression_attribute_values[':preferences'] = data['preferences']
            
        # Update avatarUrl if provided
        if 'avatarUrl' in data:
            update_expressions.append('#avatarUrl = :avatarUrl')
            expression_attribute_names['#avatarUrl'] = 'avatarUrl'
            expression_attribute_values[':avatarUrl'] = data['avatarUrl']
        
        # Always update the updatedAt timestamp
        update_expressions.append('#updatedAt = :updatedAt')
        expression_attribute_names['#updatedAt'] = 'updatedAt'
        expression_attribute_values[':updatedAt'] = datetime.utcnow().isoformat()
        
        # If there's nothing to update, return early
        if len(update_expressions) <= 1:  # Only has updatedAt
            return {
                'statusCode': 400,
                'error': 'No fields to update provided',
                'userId': userId,
                'profileId': profileId
            }
        
        # Construct the update expression
        update_expression = 'SET ' + ', '.join(update_expressions)
        
        # Update the profile
        response = table.update_item(
            Key={
                'userId': userId,
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
