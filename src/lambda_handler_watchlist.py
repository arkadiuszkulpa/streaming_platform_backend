"""
MyAI4 Watchlist Lambda Handler
This Lambda function handles watchlist-related operations for the myAI4 platform.
It provides functionality to add, remove, and retrieve watchlist items.
"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

# Environment variables - only those needed for watchlist operations
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # For account verification
PROFILE_TABLE = os.environ.get('PROFILE_TABLE')  # For profile verification
WATCHLISTS_TABLE = os.environ.get('WATCHLISTS_TABLE')  # Core table for this Lambda
WATCH_HISTORY_TABLE = os.environ.get('WATCH_HISTORY_TABLE')  # For recording watch history
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')  # For optional usage tracking

# Authentication-related environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')  # For verifying JWT tokens if handling auth directly

# Removed unused environment variables:
# - SUBSCRIPTIONS_TABLE
# - SERVICE_PREFERENCES_TABLE  
# - MOVIES_TABLE - Movie data should be fetched from movies Lambda
# - IDENTITY_POOL_ID - Not needed for server-side operations

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
    Watchlist Lambda handler for myAI4 platform
    Handles operations related to user watchlists and watch history
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
            
        # Route to appropriate handler - only watchlist related operations
        handlers = {
            # Test operation
            'test': handle_test,
            
            # Watchlist Operations
            'getWatchlist': handle_get_watchlist,
            'deleteWatchlist': handle_delete_watchlist,
            'updateWatchlist': handle_update_watchlist,
            
            # Watch History Operations
            'getWatchHistory': handle_get_watch_history,
            'deleteWatchHistory': handle_delete_watch_history,
            'updateWatchRecord': handle_update_watch_record
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

def handle_get_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getWatchlist operation
    Retrieves user's watchlist items
    
    Expected data:
    - accountId (required): The account ID of the user
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    
    accountId = data['accountId']
    
    if not WATCHLISTS_TABLE:
        return {'error': 'Watchlists table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)
        
        # Query for all watchlist items for this user
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId)
        )
        
        watchlist_items = response.get('Items', [])
        
        # Handle pagination if there are more results
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            watchlist_items.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'watchlist': watchlist_items,
            'count': len(watchlist_items),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except ClientError as e:
        print(f"Error retrieving watchlist: {str(e)}")
        return {
            'error': 'Failed to retrieve watchlist',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getWatchlist: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_add_to_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for addToWatchlist operation
    Adds a movie to a user's watchlist
    
    Expected data:
    - accountId (required): The account ID of the user
    - movieId (required): The ID of the movie to add to watchlist
    - profileId (optional): The profile for which to add the movie
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('movieId'):
        return {'error': 'movieId is required', 'statusCode': 400}
    
    accountId = data['accountId']
    movieId = data['movieId']
    profileId = data.get('profileId', '')
    
    if not WATCHLISTS_TABLE:
        return {'error': 'Watchlists table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)
        
        # Create or update watchlist entry
        watchlist_item = {
            'accountId': accountId,
            'movieId': movieId,
            'addedAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Add profileId if provided
        if profileId:
            watchlist_item['profileId'] = profileId
        
        # Add to watchlist
        table.put_item(Item=watchlist_item)
        
        return {
            'statusCode': 200,
            'message': 'Movie added to watchlist successfully',
            'watchlistItem': watchlist_item,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except ClientError as e:
        print(f"Error adding to watchlist: {str(e)}")
        return {
            'error': 'Failed to add movie to watchlist',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in addToWatchlist: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_remove_from_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for removeFromWatchlist operation
    Removes a movie from a user's watchlist
    
    Expected data:
    - accountId (required): The account ID of the user
    - movieId (required): The ID of the movie to remove from watchlist
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('movieId'):
        return {'error': 'movieId is required', 'statusCode': 400}
    
    accountId = data['accountId']
    movieId = data['movieId']
    
    if not WATCHLISTS_TABLE:
        return {'error': 'Watchlists table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)
        
        # Delete watchlist entry
        table.delete_item(
            Key={
                'accountId': accountId,
                'movieId': movieId
            }
        )
        
        return {
            'statusCode': 200,
            'message': 'Movie removed from watchlist successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except ClientError as e:
        print(f"Error removing from watchlist: {str(e)}")
        return {
            'error': 'Failed to remove movie from watchlist',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in removeFromWatchlist: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_delete_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for deleteWatchlist operation
    Deletes all watchlist items for a given user (and optionally a profile)

    Expected data:
    - accountId (required): The account ID of the user
    - profileId (optional): If provided, only delete items for this profile
    """
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}

    accountId = data['accountId']
    profileId = data.get('profileId')

    if not WATCHLISTS_TABLE:
        return {'error': 'Watchlists table not configured', 'statusCode': 500}

    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)

        # Query for all watchlist items for this user (and profile if provided)
        key_condition = boto3.dynamodb.conditions.Key('accountId').eq(accountId)
        filter_expression = None
        if profileId:
            filter_expression = boto3.dynamodb.conditions.Attr('profileId').eq(profileId)

        query_kwargs = {'KeyConditionExpression': key_condition}
        if filter_expression:
            query_kwargs['FilterExpression'] = filter_expression

        response = table.query(**query_kwargs)
        items_to_delete = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                **query_kwargs,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items_to_delete.extend(response.get('Items', []))

        # Batch delete items
        with table.batch_writer() as batch:
            for item in items_to_delete:
                batch.delete_item(
                    Key={
                        'accountId': item['accountId'],
                        'movieId': item['movieId']
                    }
                )

        return {
            'statusCode': 200,
            'message': 'Watchlist deleted successfully',
            'deletedCount': len(items_to_delete),
            'timestamp': datetime.utcnow().isoformat()
        }

    except ClientError as e:
        print(f"Error deleting watchlist: {str(e)}")
        return {
            'error': 'Failed to delete watchlist',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in deleteWatchlist: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_get_watch_history(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getWatchHistory operation
    Retrieves a user's watch history
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (optional): Filter history by specific profile
    - limit (optional): Number of items to return (default 50)
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    
    accountId = data['accountId']
    profileId = data.get('profileId')
    limit = int(data.get('limit', 50))
    
    if not WATCH_HISTORY_TABLE:
        return {'error': 'Watch History table not configured', 'statusCode': 500}
    
    try:
        table = dynamodb.Table(WATCH_HISTORY_TABLE)
        
        # Use profileId if provided, otherwise get all history for the user
        if profileId:
            # Query using GSI for specific profile
            response = table.query(
                IndexName='ProfileIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('profileId').eq(profileId),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
        else:
            # Query history for this user
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
        
        history_items = response.get('Items', [])
        
        # Handle pagination for GSI query if needed
        while 'LastEvaluatedKey' in response and len(history_items) < limit:
            if profileId:
                response = table.query(
                    IndexName='ProfileIndex',
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('profileId').eq(profileId),
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    Limit=limit - len(history_items),
                    ScanIndexForward=False
                )
            else:
                response = table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('accountId').eq(accountId),
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    Limit=limit - len(history_items),
                    ScanIndexForward=False
                )
            history_items.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'history': history_items,
            'count': len(history_items),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except ClientError as e:
        print(f"Error retrieving watch history: {str(e)}")
        return {
            'error': 'Failed to retrieve watch history',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getWatchHistory: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }

def handle_record_watch(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for recordWatch operation
    Records a movie watch event in the user's watch history
    
    Expected data:
    - accountId (required): The account ID of the user
    - movieId (required): The ID of the movie that was watched
    - profileId (optional): The profile that watched the movie
    - watchDuration (optional): Duration watched in seconds
    - watchPercentage (optional): Percentage of movie watched
    - watchedAt (optional): Timestamp when watched (defaults to now)
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('movieId'):
        return {'error': 'movieId is required', 'statusCode': 400}
    
    # TODO: Implement watch history recording functionality
    return {
        'message': 'Watch event recorded successfully (stub)',
        'operation': 'recordWatch',
        'statusCode': 200,
        'timestamp': datetime.utcnow().isoformat()
    }

def handle_delete_watch_history(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for deleteWatchHistory operation
    Deletes watch history records for a user
    
    Expected data:
    - accountId (required): The account ID of the user
    - profileId (optional): If provided, only delete history for this profile
    - movieId (optional): If provided, only delete history for this movie
    - watchId (optional): If provided, delete specific watch record by ID
    - before (optional): Delete history before this timestamp
    """
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    
    # TODO: Implement watch history deletion functionality
    return {
        'message': 'Watch history deleted successfully (stub)',
        'operation': 'deleteWatchHistory',
        'statusCode': 200,
        'timestamp': datetime.utcnow().isoformat()
    }

def handle_update_watch_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateWatchRecord operation
    Updates an existing watch record with new information
    
    Expected data:
    - accountId (required): The account ID of the user
    - watchId (required): The unique ID of the watch record
    - watchDuration (optional): Updated duration watched in seconds
    - watchPercentage (optional): Updated percentage of movie watched
    - notes (optional): User notes about the watch
    """
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('watchId'):
        return {'error': 'watchId is required', 'statusCode': 400}
    
    # TODO: Implement watch record update functionality
    return {
        'message': 'Watch record updated successfully (stub)',
        'operation': 'updateWatchRecord',
        'statusCode': 200,
        'timestamp': datetime.utcnow().isoformat()
    }

def handle_get_watch_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getWatchDetail operation
    Retrieves detailed information about a specific watch record
    
    Expected data:
    - accountId (required): The account ID of the user
    - watchId (required): The unique ID of the watch record
    """
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('watchId'):
        return {'error': 'watchId is required', 'statusCode': 400}
    
    # TODO: Implement get watch detail functionality
    return {
        'message': 'Retrieved watch detail successfully (stub)',
        'operation': 'getWatchDetail',
        'watchDetail': {'id': data.get('watchId'), 'status': 'stub'},
        'statusCode': 200,
        'timestamp': datetime.utcnow().isoformat()
    }

def handle_update_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateWatchlist operation
    Updates an existing watchlist item with additional metadata
    
    Expected data:
    - accountId (required): The account ID of the user
    - movieId (required): The ID of the movie in the watchlist
    - notes (optional): User notes about this watchlist item
    - priority (optional): User-defined priority for this item
    - tags (optional): User-defined tags for categorization
    """
    if not data.get('accountId'):
        return {'error': 'accountId is required', 'statusCode': 400}
    if not data.get('movieId'):
        return {'error': 'movieId is required', 'statusCode': 400}
    
    # TODO: Implement watchlist item update functionality
    return {
        'message': 'Watchlist item updated successfully (stub)',
        'operation': 'updateWatchlist',
        'statusCode': 200,
        'timestamp': datetime.utcnow().isoformat()
    }
