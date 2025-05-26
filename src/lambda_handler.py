"""
MyAI4 Centralized Lambda Handler
Handles all API operations for the MyAI4 ecosystem frontend
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Get table references from environment variables
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE')
SUBSCRIPTIONS_TABLE = os.environ.get('SUBSCRIPTIONS_TABLE')
SERVICE_PREFERENCES_TABLE = os.environ.get('SERVICE_PREFERENCES_TABLE')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')
FAMILY_GROUPS_TABLE = os.environ.get('FAMILY_GROUPS_TABLE')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Centralized Lambda handler for MyAI4 ecosystem operations
    """
    try:
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
            # User Profile Operations
            'getUserProfile': handle_get_user_profile,
            'createUserProfile': handle_create_user_profile,
            'updateUserProfile': handle_update_user_profile,
            
            # Subscription Operations
            'getUserSubscription': handle_get_user_subscription,
            'createSubscription': handle_create_subscription,
            'updateSubscription': handle_update_subscription,
            
            # Service Preferences Operations
            'getServicePreferences': handle_get_service_preferences,
            'createServicePreferences': handle_create_service_preferences,
            'updateServicePreferences': handle_update_service_preferences,
            
            # Family Management Operations
            'getFamilyGroup': handle_get_family_group,
            'createFamily': handle_create_family,
            'addFamilyMember': handle_add_family_member,
            
            # Usage Tracking Operations
            'recordUsage': handle_record_usage,
            'getUserUsage': handle_get_user_usage,
            
            # Movie & Content Operations
            'getMovieInfo': handle_get_movie_info,
            'searchMovies': handle_search_movies,
            'getRecommendations': handle_get_recommendations,
            'addToWatchlist': handle_add_to_watchlist,
            'removeFromWatchlist': handle_remove_from_watchlist,
            'getWatchlist': handle_get_watchlist,
            'recordWatchActivity': handle_record_watch_activity,
            'getWatchHistory': handle_get_watch_history,
            
            # Profile Operations
            'getProfiles': handle_get_profiles,
            'createProfile': handle_create_profile,
            'updateProfile': handle_update_profile,
            'deleteProfile': handle_delete_profile,
            'switchProfile': handle_switch_profile,
            
            # Test operation
            'test': handle_test,
        }
        
        handler = handlers.get(operation)
        if not handler:
            return create_response(400, {'error': f'Unknown operation: {operation}'})
            
        # Execute the handler
        result = handler(data)
        return create_response(200, result)
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def create_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Create a properly formatted API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }

# ============================================
# USER PROFILE HANDLERS
# ============================================

def handle_get_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get user profile by userId"""
    user_id = data.get('userId')
    if not user_id:
        raise ValueError('userId is required')
        
    table = dynamodb.Table(USER_PROFILES_TABLE)
    response = table.get_item(Key={'userId': user_id})
    
    if 'Item' not in response:
        raise ValueError('User profile not found')
        
    return response['Item']

def handle_create_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user profile"""
    user_id = data.get('userId')
    profile = data.get('profile')
    
    if not user_id or not profile:
        raise ValueError('userId and profile are required')
        
    # Add userId to profile
    profile['userId'] = user_id
    
    table = dynamodb.Table(USER_PROFILES_TABLE)
    table.put_item(Item=profile)
    
    return profile

def handle_update_user_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile"""
    user_id = data.get('userId')
    updates = data.get('updates')
    
    if not user_id or not updates:
        raise ValueError('userId and updates are required')
        
    # Add updatedAt timestamp
    updates['updatedAt'] = datetime.utcnow().isoformat()
    
    table = dynamodb.Table(USER_PROFILES_TABLE)
    
    # Build update expression
    update_expression = "SET "
    expression_values = {}
    
    for key, value in updates.items():
        update_expression += f"#{key} = :{key}, "
        expression_values[f":{key}"] = value
        
    update_expression = update_expression.rstrip(", ")
    
    expression_names = {f"#{key}": key for key in updates.keys()}
    
    table.update_item(
        Key={'userId': user_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values
    )
    
    return {'success': True}

# ============================================
# SUBSCRIPTION HANDLERS
# ============================================

def handle_get_user_subscription(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get user subscription by userId"""
    user_id = data.get('userId')
    if not user_id:
        raise ValueError('userId is required')
        
    table = dynamodb.Table(SUBSCRIPTIONS_TABLE)
    response = table.get_item(Key={'userId': user_id})
    
    return response.get('Item')

def handle_create_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new subscription"""
    user_id = data.get('userId')
    subscription = data.get('subscription')
    
    if not user_id or not subscription:
        raise ValueError('userId and subscription are required')
        
    subscription['userId'] = user_id
    
    table = dynamodb.Table(SUBSCRIPTIONS_TABLE)
    table.put_item(Item=subscription)
    
    return subscription

def handle_update_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update subscription"""
    user_id = data.get('userId')
    updates = data.get('updates')
    
    if not user_id or not updates:
        raise ValueError('userId and updates are required')
        
    updates['updatedAt'] = datetime.utcnow().isoformat()
    
    table = dynamodb.Table(SUBSCRIPTIONS_TABLE)
    
    # Build update expression (similar to profile update)
    update_expression = "SET "
    expression_values = {}
    expression_names = {}
    
    for key, value in updates.items():
        update_expression += f"#{key} = :{key}, "
        expression_values[f":{key}"] = value
        expression_names[f"#{key}"] = key
        
    update_expression = update_expression.rstrip(", ")
    
    table.update_item(
        Key={'userId': user_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values
    )
    
    return {'success': True}

# ============================================
# SERVICE PREFERENCES HANDLERS
# ============================================

def handle_get_service_preferences(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get service preferences"""
    user_id = data.get('userId')
    service_id = data.get('serviceId')
    
    if not user_id or not service_id:
        raise ValueError('userId and serviceId are required')
        
    table = dynamodb.Table(SERVICE_PREFERENCES_TABLE)
    response = table.get_item(Key={'userId': user_id, 'serviceId': service_id})
    
    return response.get('Item')

def handle_create_service_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create service preferences"""
    user_id = data.get('userId')
    service_id = data.get('serviceId')
    preferences = data.get('preferences')
    
    if not user_id or not service_id or not preferences:
        raise ValueError('userId, serviceId, and preferences are required')
        
    item = {
        'userId': user_id,
        'serviceId': service_id,
        **preferences
    }
    
    table = dynamodb.Table(SERVICE_PREFERENCES_TABLE)
    table.put_item(Item=item)
    
    return item

def handle_update_service_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update service preferences"""
    user_id = data.get('userId')
    service_id = data.get('serviceId')
    preferences = data.get('preferences')
    
    if not user_id or not service_id or not preferences:
        raise ValueError('userId, serviceId, and preferences are required')
        
    preferences['updatedAt'] = datetime.utcnow().isoformat()
    
    table = dynamodb.Table(SERVICE_PREFERENCES_TABLE)
    
    # Build update expression
    update_expression = "SET "
    expression_values = {}
    expression_names = {}
    
    for key, value in preferences.items():
        update_expression += f"#{key} = :{key}, "
        expression_values[f":{key}"] = value
        expression_names[f"#{key}"] = key
        
    update_expression = update_expression.rstrip(", ")
    
    table.update_item(
        Key={'userId': user_id, 'serviceId': service_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values
    )
    
    return {'success': True}

# ============================================
# FAMILY MANAGEMENT HANDLERS
# ============================================

def handle_get_family_group(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get family group by familyId"""
    family_id = data.get('familyId')
    if not family_id:
        raise ValueError('familyId is required')
        
    table = dynamodb.Table(FAMILY_GROUPS_TABLE)
    response = table.get_item(Key={'familyId': family_id})
    
    return response.get('Item')

def handle_create_family(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new family group"""
    family = data.get('family')
    if not family:
        raise ValueError('family data is required')
        
    # Generate family ID
    import uuid
    family_id = str(uuid.uuid4())
    family['familyId'] = family_id
    
    table = dynamodb.Table(FAMILY_GROUPS_TABLE)
    table.put_item(Item=family)
    
    return {'familyId': family_id}

def handle_add_family_member(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add member to family group"""
    family_id = data.get('familyId')
    user_id = data.get('userId')
    role = data.get('role')
    
    if not family_id or not user_id or not role:
        raise ValueError('familyId, userId, and role are required')
        
    # This would typically update the family group's members list
    # Implementation depends on your exact family data structure
    
    return {'success': True}

# ============================================
# USAGE TRACKING HANDLERS
# ============================================

def handle_record_usage(data: Dict[str, Any]) -> Dict[str, Any]:
    """Record user usage data"""
    user_id = data.get('userId')
    service_id = data.get('serviceId')
    usage = data.get('usage')
    
    if not user_id or not service_id or not usage:
        raise ValueError('userId, serviceId, and usage are required')
        
    # Create composite key for usage table
    date_service_id = f"{usage.get('date')}#{service_id}"
    
    item = {
        'userId': user_id,
        'dateServiceId': date_service_id,
        'serviceId': service_id,
        **usage
    }
    
    table = dynamodb.Table(USER_USAGE_TABLE)
    table.put_item(Item=item)
    
    return {'success': True}

def handle_get_user_usage(data: Dict[str, Any]) -> list:
    """Get user usage data"""
    user_id = data.get('userId')
    if not user_id:
        raise ValueError('userId is required')
        
    table = dynamodb.Table(USER_USAGE_TABLE)
    
    # This is a simplified query - you'd want to add filtering by service and date range
    response = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id))
    
    return response.get('Items', [])

# ============================================
# MOVIE & CONTENT OPERATION HANDLERS
# ============================================

def handle_get_movie_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information about a specific movie"""
    movie_id = data.get('movieId')
    if not movie_id:
        raise ValueError('movieId is required')
    
    # This would integrate with your movie database or external API
    # For now, return a mock response
    return {
        'movieId': movie_id,
        'title': 'Sample Movie',
        'description': 'A sample movie description',
        'genre': ['Action', 'Adventure'],
        'rating': '8.5',
        'duration': '120 minutes',
        'releaseYear': 2024,
        'streamingUrl': f'https://stream.myai4.co.uk/movie/{movie_id}',
        'thumbnailUrl': f'https://images.myai4.co.uk/movie/{movie_id}/thumb.jpg'
    }

def handle_search_movies(data: Dict[str, Any]) -> Dict[str, Any]:
    """Search for movies based on criteria"""
    query = data.get('query', '')
    genre = data.get('genre')
    year = data.get('year')
    limit = data.get('limit', 20)
    
    # This would integrate with your search service
    # For now, return a mock response
    return {
        'query': query,
        'results': [
            {
                'movieId': f'movie_{i}',
                'title': f'Search Result {i}',
                'genre': ['Action'] if i % 2 == 0 else ['Comedy'],
                'rating': '7.5',
                'thumbnailUrl': f'https://images.myai4.co.uk/movie/movie_{i}/thumb.jpg'
            }
            for i in range(1, min(limit + 1, 11))
        ],
        'totalResults': 100,
        'searchCriteria': {
            'query': query,
            'genre': genre,
            'year': year
        }
    }

def handle_get_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get personalized movie recommendations for a user"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    limit = data.get('limit', 10)
    
    if not user_id:
        raise ValueError('userId is required')
    
    # This would use your AI recommendation engine
    # For now, return a mock response
    return {
        'userId': user_id,
        'profileId': profile_id,
        'recommendations': [
            {
                'movieId': f'rec_{i}',
                'title': f'Recommended Movie {i}',
                'genre': ['Drama'] if i % 2 == 0 else ['Thriller'],
                'rating': '8.0',
                'confidenceScore': 0.95 - (i * 0.05),
                'reason': f'Based on your viewing history and preferences',
                'thumbnailUrl': f'https://images.myai4.co.uk/movie/rec_{i}/thumb.jpg'
            }
            for i in range(1, limit + 1)
        ],
        'algorithmVersion': '2.1.0',
        'generatedAt': datetime.utcnow().isoformat()
    }

def handle_add_to_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a movie to user's watchlist"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    movie_id = data.get('movieId')
    
    if not all([user_id, movie_id]):
        raise ValueError('userId and movieId are required')
    
    # This would update your watchlist storage
    # For now, return a success response
    return {
        'success': True,
        'message': f'Movie {movie_id} added to watchlist',
        'userId': user_id,
        'profileId': profile_id,
        'movieId': movie_id,
        'addedAt': datetime.utcnow().isoformat()
    }

def handle_remove_from_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove a movie from user's watchlist"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    movie_id = data.get('movieId')
    
    if not all([user_id, movie_id]):
        raise ValueError('userId and movieId are required')
    
    # This would update your watchlist storage
    # For now, return a success response
    return {
        'success': True,
        'message': f'Movie {movie_id} removed from watchlist',
        'userId': user_id,
        'profileId': profile_id,
        'movieId': movie_id,
        'removedAt': datetime.utcnow().isoformat()
    }

def handle_get_watchlist(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get user's watchlist"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    
    if not user_id:
        raise ValueError('userId is required')
    
    # This would query your watchlist storage
    # For now, return a mock watchlist
    return {
        'userId': user_id,
        'profileId': profile_id,
        'watchlist': [
            {
                'movieId': f'watch_{i}',
                'title': f'Watchlist Movie {i}',
                'genre': ['Sci-Fi'] if i % 2 == 0 else ['Romance'],
                'addedAt': datetime.utcnow().isoformat(),
                'thumbnailUrl': f'https://images.myai4.co.uk/movie/watch_{i}/thumb.jpg'
            }
            for i in range(1, 6)
        ],
        'totalItems': 5
    }

def handle_record_watch_activity(data: Dict[str, Any]) -> Dict[str, Any]:
    """Record user's watching activity"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    movie_id = data.get('movieId')
    watch_time = data.get('watchTime', 0)  # in seconds
    total_duration = data.get('totalDuration', 0)
    
    if not all([user_id, movie_id]):
        raise ValueError('userId and movieId are required')
    
    # This would record the activity in your analytics system
    # For now, return a success response
    return {
        'success': True,
        'userId': user_id,
        'profileId': profile_id,
        'movieId': movie_id,
        'watchTime': watch_time,
        'totalDuration': total_duration,
        'completionPercentage': (watch_time / total_duration * 100) if total_duration > 0 else 0,
        'recordedAt': datetime.utcnow().isoformat()
    }

def handle_get_watch_history(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get user's watch history"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    limit = data.get('limit', 20)
    
    if not user_id:
        raise ValueError('userId is required')
    
    # This would query your watch history storage
    # For now, return a mock history
    return {
        'userId': user_id,
        'profileId': profile_id,
        'history': [
            {
                'movieId': f'hist_{i}',
                'title': f'Watched Movie {i}',
                'genre': ['Action'] if i % 2 == 0 else ['Comedy'],
                'watchedAt': datetime.utcnow().isoformat(),
                'completionPercentage': 100 - (i * 10),
                'thumbnailUrl': f'https://images.myai4.co.uk/movie/hist_{i}/thumb.jpg'
            }
            for i in range(1, min(limit + 1, 11))
        ],
        'totalItems': 100
    }

# ============================================
# PROFILE OPERATION HANDLERS
# ============================================

def handle_get_profiles(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get all profiles for a user"""
    user_id = data.get('userId')
    
    if not user_id:
        raise ValueError('userId is required')
    
    # This would query your profiles storage
    # For now, return mock profiles
    return {
        'userId': user_id,
        'profiles': [
            {
                'profileId': f'profile_{i}',
                'name': f'Profile {i}',
                'isChild': i > 2,
                'avatarUrl': f'https://avatars.myai4.co.uk/profile_{i}.jpg',
                'preferences': {
                    'maturityRating': 'PG-13' if i > 2 else 'R',
                    'favoriteGenres': ['Action', 'Adventure'] if i % 2 == 0 else ['Comedy', 'Romance']
                },
                'createdAt': datetime.utcnow().isoformat()
            }
            for i in range(1, 5)
        ]
    }

def handle_create_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new profile for a user"""
    user_id = data.get('userId')
    name = data.get('name')
    is_child = data.get('isChild', False)
    
    if not all([user_id, name]):
        raise ValueError('userId and name are required')
    
    # This would create the profile in your storage
    # For now, return a success response
    profile_id = f'profile_{datetime.utcnow().timestamp()}'
    
    return {
        'success': True,
        'profileId': profile_id,
        'userId': user_id,
        'name': name,
        'isChild': is_child,
        'avatarUrl': f'https://avatars.myai4.co.uk/{profile_id}.jpg',
        'createdAt': datetime.utcnow().isoformat()
    }

def handle_update_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing profile"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    updates = data.get('updates', {})
    
    if not all([user_id, profile_id]):
        raise ValueError('userId and profileId are required')
    
    # This would update the profile in your storage
    # For now, return a success response
    return {
        'success': True,
        'profileId': profile_id,
        'userId': user_id,
        'updates': updates,
        'updatedAt': datetime.utcnow().isoformat()
    }

def handle_delete_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a profile"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    
    if not all([user_id, profile_id]):
        raise ValueError('userId and profileId are required')
    
    # This would delete the profile from your storage
    # For now, return a success response
    return {
        'success': True,
        'message': f'Profile {profile_id} deleted successfully',
        'profileId': profile_id,
        'userId': user_id,
        'deletedAt': datetime.utcnow().isoformat()
    }

def handle_switch_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Switch to a different profile"""
    user_id = data.get('userId')
    profile_id = data.get('profileId')
    
    if not all([user_id, profile_id]):
        raise ValueError('userId and profileId are required')
    
    # This would update the current active profile
    # For now, return a success response
    return {
        'success': True,
        'userId': user_id,
        'activeProfileId': profile_id,
        'switchedAt': datetime.utcnow().isoformat(),
        'message': f'Switched to profile {profile_id}'
    }

# ============================================
# TEST HANDLER
# ============================================

def handle_test(data: Dict[str, Any]) -> Dict[str, Any]:
    """Test handler for API connectivity"""
    return {
        'message': 'MyAI4 API is working!',
        'timestamp': datetime.utcnow().isoformat(),
        'data_received': data,
        'tables': {
            'USER_PROFILES_TABLE': USER_PROFILES_TABLE,
            'SUBSCRIPTIONS_TABLE': SUBSCRIPTIONS_TABLE,
            'SERVICE_PREFERENCES_TABLE': SERVICE_PREFERENCES_TABLE,
            'USER_USAGE_TABLE': USER_USAGE_TABLE,
            'FAMILY_GROUPS_TABLE': FAMILY_GROUPS_TABLE,
        }
    }
