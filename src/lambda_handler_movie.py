"""
MyAI4 Movie Lambda Handler
This Lambda function handles movie-related operations for the myAI4 platform.
It provides functionality to search movies via RapidAPI, store them in DynamoDB, 
and retrieve movie information and details.
"""

import os
import json
import boto3
import requests
import uuid
import traceback
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
        'ACCOUNT_TABLE', 'PROFILE_TABLE', 'MOVIE_TABLE',
        'USER_USAGE_TABLE', 'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT',
        'USER_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} not configured")
    
    # Check all tables
    for table_name, table_var in {
        'ACCOUNT_TABLE': ACCOUNT_TABLE,
        'PROFILE_TABLE': PROFILE_TABLE,
        'MOVIE_TABLE': MOVIE_TABLE,
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
    
    # Check for RapidAPI key
    try:
        _ = get_rapidapi_key()
        messages.append("RapidAPI key is accessible")
    except Exception as e:
        warnings.append(f"Cannot access RapidAPI key: {str(e)}")
    
    # Get Lambda execution environment
    execution_env = os.environ.get('AWS_EXECUTION_ENV', 'unknown')
    
    return {
        'message': 'MyAI4 Movie API is operational',
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
    """Create an API Gateway response object with proper CORS headers"""
    # Get environment and origin configuration
    environment = os.environ.get('ENVIRONMENT', 'dev')
    cloudfront_domain = os.environ.get('CLOUDFRONT_DOMAIN', '')
    local_origins_str = os.environ.get('LOCAL_ORIGINS', '')
    
    # Extract origin from the request (would need to be passed from lambda_handler)
    origin = '*'  # Default fallback
    
    # Build allowed origins list
    allowed_origins = []
    
    # Add CloudFront domain if available
    if cloudfront_domain:
        if cloudfront_domain.startswith('http'):
            allowed_origins.append(cloudfront_domain)
        else:
            allowed_origins.append(f"https://{cloudfront_domain}")
    
    # Add localhost origins for dev environment
    if local_origins_str:
        local_origins = [o.strip() for o in local_origins_str.split(',') if o.strip()]
        allowed_origins.extend(local_origins)
    
    # Use first allowed origin as fallback if no match (safer than '*')
    cors_origin = allowed_origins[0] if allowed_origins else '*'
    
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': cors_origin,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-CSRF-Token,X-Requested-With',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps(body)
    }
    return response

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Movie Lambda handler for myAI4 platform
    Handles operations related to movie search, storage, and retrieval
    Authentication is now fully handled by API Gateway
    """
    try:
        # Log basic request info for debugging
        print(f"🔍 {event.get('httpMethod')} {event.get('path')}")
        
        # Handle OPTIONS requests for CORS preflight
        http_method = event.get('httpMethod', 'GET')
        if http_method == 'OPTIONS':
            print("✅ Handling OPTIONS preflight request")
            return create_response(200, {'message': 'CORS preflight response'})
            
        # Parse operation from request body (all requests use POST method)
        try:
            body = json.loads(event.get('body', '{}'))
            operation = body.get('operation')
            data = body.get('data', {})
            print(f"✅ Operation: {operation}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {str(e)}")
            return create_response(400, {'error': 'Invalid JSON in request body'})
            
        if not operation:
            print("❌ No operation specified")
            return create_response(400, {'error': 'Operation parameter is required'})
            
        # Route to appropriate handler
        handlers = {
            # Test operation
            'test': handle_test,
            
            # Movie Operations
            'searchMovies': handle_search_movies,
            'getMovie': handle_get_movie,
            'getMovieDetails': handle_get_movie_details,
            'saveMovie': handle_save_movie
        }
        
        handler = handlers.get(operation)
        if not handler:
            print(f"❌ Unknown operation: {operation}")
            return create_response(400, {'error': f'Unknown operation: {operation}'})
            
        # Execute the handler
        print(f"✅ Executing: {operation}")
        result = handler(data)
        return create_response(200, result)
    except Exception as e:
        print(f"❌ Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Internal server error', 'details': str(e)})

def handle_search_movies(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for searchMovies operation
    Searches for movies using RapidAPI and stores the results in DynamoDB
    
    Expected data:
    - query (required): The search query for movies
    - accountId (optional): The account ID for usage tracking
    """
    # Validate required parameters
    if not data.get('query'):
        return {'error': 'Missing required parameter: query'}
    
    query = data['query']
    accountId = data.get('accountId')  # Optional for usage tracking
    
    if not MOVIE_TABLE:
        return {'error': 'Movie table not configured'}
    
    try:
        # Get RapidAPI key
        rapidapi_key = get_rapidapi_key()
        
        # Search movies using RapidAPI
        url = "https://advanced-movie-search.p.rapidapi.com/search/movie"
        querystring = {"query": query, "page": "1"}
        headers = {
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": "advanced-movie-search.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code != 200:
            return {
                'error': 'Failed to fetch movies from external API',
                'details': response.text
            }
        
        api_data = response.json()
        movies = []
        
        # Process and store each movie
        if 'results' in api_data:
            table = dynamodb.Table(MOVIE_TABLE)
            
            for movie_data in api_data['results']:
                # Create movie object with standardized fields
                movie = {
                    'movieId': str(movie_data.get('id', str(uuid.uuid4()))),
                    'title': movie_data.get('title', ''),
                    'overview': movie_data.get('overview', ''),
                    'release_date': movie_data.get('release_date', ''),
                    'poster_path': movie_data.get('poster_path', ''),
                    'backdrop_path': movie_data.get('backdrop_path', ''),
                    'vote_average': movie_data.get('vote_average', 0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0),
                    'genre_ids': movie_data.get('genre_ids', []),
                    'adult': movie_data.get('adult', False),
                    'original_language': movie_data.get('original_language', ''),
                    'original_title': movie_data.get('original_title', ''),
                    'video': movie_data.get('video', False),
                    # Additional tracking fields
                    'createdAt': datetime.utcnow().isoformat(),
                    'updatedAt': datetime.utcnow().isoformat(),
                    'searchQuery': query,
                    'source': 'rapidapi_advanced_movie_search'
                }
                
                # Store movie in DynamoDB
                table.put_item(Item=movie)
                movies.append(movie)
        
        # Track usage if accountId provided
        if accountId and USER_USAGE_TABLE:
            try:
                usage_table = dynamodb.Table(USER_USAGE_TABLE)
                usage_record = {
                    'accountId': accountId,
                    'timestamp': datetime.utcnow().isoformat(),
                    'operation': 'searchMovies',
                    'query': query,
                    'resultsCount': len(movies)
                }
                usage_table.put_item(Item=usage_record)
            except Exception as e:
                print(f"Failed to track usage: {str(e)}")  # Non-critical error
        
        return {
            'movies': movies,
            'total_results': len(movies),
            'query': query,
            'message': f'Found and stored {len(movies)} movies for query: {query}'
        }
        
    except requests.RequestException as e:
        print(f"API request error in searchMovies: {str(e)}")
        return {
            'error': 'External API request failed',
            'details': str(e)
        }
    except ClientError as e:
        print(f"DynamoDB error in searchMovies: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e)
        }
    except Exception as e:
        print(f"Unexpected error in searchMovies: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e)
        }


def handle_get_movie(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getMovie operation
    Retrieves a movie from DynamoDB by movieId
    
    Expected data:
    - movieId (required): The ID of the movie to retrieve
    """
    # Validate required parameters
    if not data.get('movieId'):
        return {'error': 'Missing required parameter: movieId'}
    
    movieId = data['movieId']
    
    if not MOVIE_TABLE:
        return {'error': 'Movie table not configured'}
    
    try:
        table = dynamodb.Table(MOVIE_TABLE)
        response = table.get_item(
            Key={'movieId': movieId}
        )
        
        if 'Item' not in response:
            return {'error': 'Movie not found'}
        
        return {
            'movie': response['Item'],
            'message': 'Movie retrieved successfully'
        }
        
    except ClientError as e:
        print(f"DynamoDB error in getMovie: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e)
        }
    except Exception as e:
        print(f"Unexpected error in getMovie: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e)
        }


def handle_get_movie_details(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getMovieDetails operation
    Gets detailed movie information from RapidAPI and stores/updates it in DynamoDB
    
    Expected data:
    - movieId (required): The ID of the movie to get details for
    """
    # Validate required parameters
    if not data.get('movieId'):
        return {'error': 'Missing required parameter: movieId'}
    
    movieId = data['movieId']
    
    if not MOVIE_TABLE:
        return {'error': 'Movie table not configured'}
    
    try:
        # Get RapidAPI key
        rapidapi_key = get_rapidapi_key()
        
        # Get detailed movie information from RapidAPI
        url = "https://advanced-movie-search.p.rapidapi.com/movies/getdetails"
        querystring = {"movie_id": movieId}
        headers = {
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": "advanced-movie-search.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code != 200:
            return {
                'error': 'Failed to fetch movie details from external API',
                'details': response.text
            }
        
        api_data = response.json()
        
        # Create detailed movie object
        movie_details = {
            'movieId': str(api_data.get('id', movieId)),
            'title': api_data.get('title', ''),
            'overview': api_data.get('overview', ''),
            'release_date': api_data.get('release_date', ''),
            'poster_path': api_data.get('poster_path', ''),
            'backdrop_path': api_data.get('backdrop_path', ''),
            'vote_average': api_data.get('vote_average', 0),
            'vote_count': api_data.get('vote_count', 0),
            'popularity': api_data.get('popularity', 0),
            'runtime': api_data.get('runtime', 0),
            'budget': api_data.get('budget', 0),
            'revenue': api_data.get('revenue', 0),
            'genres': api_data.get('genres', []),
            'production_companies': api_data.get('production_companies', []),
            'production_countries': api_data.get('production_countries', []),
            'spoken_languages': api_data.get('spoken_languages', []),
            'status': api_data.get('status', ''),
            'tagline': api_data.get('tagline', ''),
            'adult': api_data.get('adult', False),
            'original_language': api_data.get('original_language', ''),
            'original_title': api_data.get('original_title', ''),
            'video': api_data.get('video', False),
            'homepage': api_data.get('homepage', ''),
            'imdb_id': api_data.get('imdb_id', ''),
            # Additional tracking fields
            'updatedAt': datetime.utcnow().isoformat(),
            'detailsFetched': True,
            'source': 'rapidapi_advanced_movie_search'
        }
        
        # Check if movie already exists to preserve createdAt
        table = dynamodb.Table(MOVIE_TABLE)
        existing_response = table.get_item(Key={'movieId': movieId})
        
        if 'Item' in existing_response:
            movie_details['createdAt'] = existing_response['Item'].get('createdAt', datetime.utcnow().isoformat())
        else:
            movie_details['createdAt'] = datetime.utcnow().isoformat()
        
        # Store/update movie details in DynamoDB
        table.put_item(Item=movie_details)
        
        return {
            'movie': movie_details,
            'message': 'Movie details retrieved and stored successfully'
        }
        
    except requests.RequestException as e:
        print(f"API request error in getMovieDetails: {str(e)}")
        return {
            'error': 'External API request failed',
            'details': str(e)
        }
    except ClientError as e:
        print(f"DynamoDB error in getMovieDetails: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e)
        }
    except Exception as e:
        print(f"Unexpected error in getMovieDetails: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e)
        }


def handle_save_movie(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for saveMovie operation
    Manually saves a movie to DynamoDB (for custom movie data)
    
    Expected data:
    - movie (required): Movie object containing movie data
    """
    # Validate required parameters
    if not data.get('movie'):
        return {'error': 'Missing required parameter: movie'}
    
    movie_data = data['movie']
    
    if not movie_data.get('title'):
        return {'error': 'Missing required parameter: movie.title'}
    
    if not MOVIE_TABLE:
        return {'error': 'Movie table not configured'}
    
    try:
        # Ensure movieId exists
        if not movie_data.get('movieId'):
            movie_data['movieId'] = str(uuid.uuid4())
        
        # Add timestamps if not provided
        if not movie_data.get('createdAt'):
            movie_data['createdAt'] = datetime.utcnow().isoformat()
        
        movie_data['updatedAt'] = datetime.utcnow().isoformat()
        movie_data['source'] = movie_data.get('source', 'manual')
        
        # Store movie in DynamoDB
        table = dynamodb.Table(MOVIE_TABLE)
        table.put_item(Item=movie_data)
        
        return {
            'movie': movie_data,
            'message': 'Movie saved successfully'
        }
        
    except ClientError as e:
        print(f"DynamoDB error in saveMovie: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e)
        }
    except Exception as e:
        print(f"Unexpected error in saveMovie: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e)
        }
