"""
MyAI4 Profile AI Lambda Handler
This Lambda function handles AI-related profile operations for the myAI4 platform.
It provides functionality to manage AI preferences, recommendation settings, and user feedback.
"""
import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

# Environment variables - only those needed for profile AI operations
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # For account verification
PROFILE_TABLE = os.environ.get('PROFILE_TABLE')  # For profile verification
PROFILE_AI_TABLE = os.environ.get('PROFILE_AI_TABLE')  # Core table for this Lambda
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
        'ACCOUNTS_TABLE', 'PROFILE_TABLE', 'PROFILE_AI_TABLE',
        'USER_USAGE_TABLE', 'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT',
        'USER_POOL_ID', 'IDENTITY_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} not configured")
    
    # Check all tables
    for table_name, table_var in {
        'ACCOUNT_TABLE': ACCOUNT_TABLE,
        'PROFILE_TABLE': PROFILE_TABLE,
        'PROFILE_AI_TABLE': PROFILE_AI_TABLE,
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
        'message': 'MyAI4 Profile AI API is operational',
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
    Profile AI Lambda handler for myAI4 platform
    Handles operations related to AI preferences and personalized recommendations
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
        elif operation == 'getAiPreferences':
            result = handle_get_ai_preferences(data)
        elif operation == 'updateAiPreferences':
            result = handle_update_ai_preferences(data)
        elif operation == 'generateRecommendations':
            result = handle_generate_recommendations(data)
        elif operation == 'provideRecommendationFeedback':
            result = handle_provide_recommendation_feedback(data)
        elif operation == 'getGroupRecommendations':
            result = handle_get_group_recommendations(data)
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


def handle_get_ai_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getAiPreferences operation
    Retrieves AI preferences for a user profile
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to retrieve AI preferences for
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    
    if not PROFILE_AI_TABLE:
        return {'error': 'Profile AI table not configured', 'statusCode': 500}
    
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
        
        # Get AI preferences
        ai_table = dynamodb.Table(PROFILE_AI_TABLE)
        response = ai_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        if 'Item' in response:
            return {
                'preferences': response['Item'],
                'message': 'AI preferences retrieved successfully'
            }
        else:
            # If preferences don't exist, return default preferences
            default_preferences = {
                'accountId': accountId,
                'profileId': profileId,
                'algorithmSettings': {
                    'explainability': 'detailed',
                    'surpriseLevel': 'medium',
                    'diversityLevel': 'medium',
                    'noveltyWeight': 0.5,
                    'popularityWeight': 0.5
                },
                'preferredGenres': [],
                'dislikedGenres': [],
                'favoriteActors': [],
                'favoriteDirectors': [],
                'createdAt': datetime.utcnow().isoformat()
            }
            
            return {
                'preferences': default_preferences,
                'message': 'Default AI preferences retrieved (no custom preferences found)'
            }
    except ClientError as e:
        print(f"DynamoDB error in getAiPreferences: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getAiPreferences: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_update_ai_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateAiPreferences operation
    Updates AI preferences for a user profile
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to update AI preferences for
    - preferences (required): The AI preferences object to update
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    if not data.get('preferences'):
        return {'error': 'Missing required parameter: preferences', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    preferences = data['preferences']
    
    if not PROFILE_AI_TABLE:
        return {'error': 'Profile AI table not configured', 'statusCode': 500}
    
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
        
        # Update AI preferences
        ai_table = dynamodb.Table(PROFILE_AI_TABLE)
        
        # Add timestamp and required keys
        preferences['updatedAt'] = datetime.utcnow().isoformat()
        preferences['accountId'] = accountId
        preferences['profileId'] = profileId
        
        response = ai_table.put_item(Item=preferences)
        
        return {
            'message': 'AI preferences updated successfully',
            'preferences': {
                'accountId': accountId,
                'profileId': profileId,
                'updatedAt': preferences['updatedAt']
            }
        }
    except ClientError as e:
        print(f"DynamoDB error in updateAiPreferences: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in updateAiPreferences: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_generate_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for generateRecommendations operation
    Generates personalized movie recommendations based on AI preferences
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile to generate recommendations for
    - count (optional): The number of recommendations to generate (default: 10)
    - filters (optional): Additional filters for recommendations
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    count = int(data.get('count', 10))
    filters = data.get('filters', {})
    
    if not PROFILE_AI_TABLE:
        return {'error': 'Profile AI table not configured', 'statusCode': 500}
    
    try:
        # Get AI preferences
        ai_table = dynamodb.Table(PROFILE_AI_TABLE)
        response = ai_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        # Default preferences if none found
        if 'Item' in response:
            preferences = response['Item']
        else:
            preferences = {
                'algorithmSettings': {
                    'explainability': 'detailed',
                    'surpriseLevel': 'medium',
                    'diversityLevel': 'medium',
                    'noveltyWeight': 0.5,
                    'popularityWeight': 0.5
                },
                'preferredGenres': [],
                'dislikedGenres': []
            }
        
        # In a real implementation, this would call an AI/ML service to generate recommendations
        # For demo purposes, we'll return mock recommendations
        mock_recommendations = [
            {
                'movieId': f'movie{i}',
                'title': f'Recommended Movie {i}',
                'score': round(0.95 - (i * 0.05), 2),
                'reasonCode': 'GENRE_MATCH',
                'explanation': f'Based on your preference for {preferences.get("preferredGenres", ["action"])[0] if preferences.get("preferredGenres") else "popular"} movies'
            }
            for i in range(1, count + 1)
        ]
        
        # Track usage (simplified)
        if USER_USAGE_TABLE:
            try:
                usage_table = dynamodb.Table(USER_USAGE_TABLE)
                timestamp = datetime.utcnow().isoformat()
                usage_table.put_item(Item={
                    'accountId': accountId,
                    'timestamp': timestamp,
                    'serviceType': 'streaming',
                    'operation': 'generateRecommendations',
                    'profileId': profileId,
                    'count': count
                })
            except Exception as e:
                print(f"Error recording usage: {str(e)}")
        
        return {
            'recommendations': mock_recommendations,
            'requestDetails': {
                'accountId': accountId,
                'profileId': profileId,
                'count': count,
                'filters': filters
            },
            'message': 'Recommendations generated successfully'
        }
    except ClientError as e:
        print(f"DynamoDB error in generateRecommendations: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in generateRecommendations: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_provide_recommendation_feedback(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for provideRecommendationFeedback operation
    Records user feedback on recommendations to improve future suggestions
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (required): The ID of the profile providing feedback
    - movieId (required): The ID of the movie being rated
    - feedback (required): The feedback object (liked: boolean, rating: number, reason: string)
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileId'):
        return {'error': 'Missing required parameter: profileId', 'statusCode': 400}
    if not data.get('movieId'):
        return {'error': 'Missing required parameter: movieId', 'statusCode': 400}
    if not data.get('feedback'):
        return {'error': 'Missing required parameter: feedback', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data['profileId']
    movieId = data['movieId']
    feedback = data['feedback']
    
    if not PROFILE_AI_TABLE:
        return {'error': 'Profile AI table not configured', 'statusCode': 500}
    
    try:
        # Get AI preferences
        ai_table = dynamodb.Table(PROFILE_AI_TABLE)
        response = ai_table.get_item(
            Key={
                'accountId': accountId,
                'profileId': profileId
            }
        )
        
        # Initialize or get existing preferences
        if 'Item' in response:
            preferences = response['Item']
        else:
            preferences = {
                'accountId': accountId,
                'profileId': profileId,
                'algorithmSettings': {
                    'explainability': 'detailed',
                    'surpriseLevel': 'medium',
                    'diversityLevel': 'medium',
                    'noveltyWeight': 0.5,
                    'popularityWeight': 0.5
                },
                'preferredGenres': [],
                'dislikedGenres': [],
                'createdAt': datetime.utcnow().isoformat()
            }
        
        # Initialize feedback history if it doesn't exist
        if 'feedbackHistory' not in preferences:
            preferences['feedbackHistory'] = []
        
        # Add new feedback with timestamp
        feedback_entry = {
            'movieId': movieId,
            'timestamp': datetime.utcnow().isoformat(),
            'feedback': feedback
        }
        
        # Add to feedback history (keep only last 50 entries)
        preferences['feedbackHistory'].insert(0, feedback_entry)
        if len(preferences['feedbackHistory']) > 50:
            preferences['feedbackHistory'] = preferences['feedbackHistory'][:50]
        
        # Update last modified timestamp
        preferences['updatedAt'] = datetime.utcnow().isoformat()
        
        # Save updated preferences
        ai_table.put_item(Item=preferences)
        
        # In a real implementation, we might also update a machine learning model here
        
        return {
            'message': 'Recommendation feedback recorded successfully',
            'movieId': movieId,
            'profileId': profileId
        }
    except ClientError as e:
        print(f"DynamoDB error in provideRecommendationFeedback: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in provideRecommendationFeedback: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_get_group_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getGroupRecommendations operation
    Generates movie recommendations for a group of profiles
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileIds (required): List of profile IDs in the group
    - count (optional): The number of recommendations to generate (default: 10)
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('profileIds') or not isinstance(data.get('profileIds'), list):
        return {'error': 'Missing required parameter: profileIds (must be an array)', 'statusCode': 400}
    
    accountId = data['accountId']
    profile_ids = data['profileIds']
    count = int(data.get('count', 10))
    
    if not PROFILE_AI_TABLE:
        return {'error': 'Profile AI table not configured', 'statusCode': 500}
    
    try:
        # Verify all profiles exist and belong to the account
        if PROFILE_TABLE:
            profile_table = dynamodb.Table(PROFILE_TABLE)
            for profile_id in profile_ids:
                profile_response = profile_table.get_item(
                    Key={
                        'accountId': accountId,
                        'profileId': profile_id
                    }
                )
                if 'Item' not in profile_response:
                    return {'error': f'Profile {profile_id} not found', 'statusCode': 404}
        
        # Get AI preferences for all profiles
        ai_table = dynamodb.Table(PROFILE_AI_TABLE)
        all_preferences = []
        
        for profile_id in profile_ids:
            response = ai_table.get_item(
                Key={
                    'accountId': accountId,
                    'profileId': profile_id
                }
            )
            
            if 'Item' in response:
                all_preferences.append(response['Item'])
            else:
                # Use default preferences if none found
                all_preferences.append({
                    'accountId': accountId,
                    'profileId': profile_id,
                    'algorithmSettings': {
                        'explainability': 'detailed',
                        'surpriseLevel': 'medium',
                        'diversityLevel': 'medium'
                    },
                    'preferredGenres': [],
                    'dislikedGenres': []
                })
        
        # In a real implementation, this would perform a complex algorithm that balances preferences
        # For demo purposes, we'll return mock recommendations
        mock_recommendations = [
            {
                'movieId': f'movie{i}',
                'title': f'Group Recommendation {i}',
                'score': round(0.95 - (i * 0.05), 2),
                'matchScores': {profile_id: round(0.7 + (0.2 * (i % 3)), 2) for profile_id in profile_ids},
                'explanation': 'Recommended based on combined group preferences'
            }
            for i in range(1, count + 1)
        ]
        
        # Track usage (simplified)
        if USER_USAGE_TABLE:
            try:
                usage_table = dynamodb.Table(USER_USAGE_TABLE)
                timestamp = datetime.utcnow().isoformat()
                usage_table.put_item(Item={
                    'accountId': accountId,
                    'timestamp': timestamp,
                    'serviceType': 'streaming',
                    'operation': 'getGroupRecommendations',
                    'profileIds': profile_ids,
                    'count': count
                })
            except Exception as e:
                print(f"Error recording usage: {str(e)}")
        
        return {
            'recommendations': mock_recommendations,
            'groupSize': len(profile_ids),
            'profiles': profile_ids,
            'message': 'Group recommendations generated successfully'
        }
    except ClientError as e:
        print(f"DynamoDB error in getGroupRecommendations: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getGroupRecommendations: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }
