# myAI.stream Database Schema

This document provides a comprehensive overview of the database schema used across the myAI.stream platform. The platform uses Amazon DynamoDB for all data storage needs.

## Design Principles

1. **Separation of Concerns**: Core entity data is separated from specialized data (settings, preferences, etc.)
2. **Scalability**: Tables are designed to support independent scaling
3. **Performance**: Access patterns are optimized with appropriate indexes
4. **Security**: All tables have server-side encryption and point-in-time recovery

## Cross-Service Tables

These tables are shared across all myAI services (stream, shopping, etc.).

### AccountTable

Core user account information, created during Cognito post-confirmation.

| Attribute   | Type   | Description                        | Required |
|-------------|--------|------------------------------------|----------|
| accountId   | String | Cognito user ID (HASH key)         | Yes      |
| email       | String | User's email address               | Yes      |
| firstName   | String | User's first name                  | No       |
| lastName    | String | User's last name                   | No       |
| createdAt   | String | ISO datetime of account creation   | Yes      |
| updatedAt   | String | ISO datetime of last update        | No       |

**Global Secondary Indexes:**
- **EmailIndex**: email (HASH) - For email lookups

**Access Patterns:**
1. Get account by accountId (HASH key)
2. Get account by email (GSI)

### SubscriptionTable

Manages subscription data across all myAI services.

| Attribute      | Type   | Description                             | Required |
|----------------|--------|-----------------------------------------|----------|
| accountId      | String | Cognito user ID (HASH key)              | Yes      |
| subscriptionId | String | Unique subscription identifier (RANGE key) | Yes      |
| serviceType    | String | Service identifier (stream, shop, etc.) | Yes      |
| plan           | String | Subscription plan type                  | Yes      |
| status         | String | Subscription status                     | Yes      |
| startDate      | String | ISO datetime of subscription start      | Yes      |
| endDate        | String | ISO datetime of subscription end        | No       |
| paymentDetails | Object | Payment processing information          | No       |
| trialEndDate   | String | ISO datetime of trial period end        | No       |
| createdAt      | String | ISO datetime of record creation         | Yes      |
| updatedAt      | String | ISO datetime of last update             | No       |

**Global Secondary Indexes:**
- **ServiceTypeIndex**: serviceType (HASH), accountId (RANGE) - For service-specific lookups

**Access Patterns:**
1. Get all subscriptions for an account
2. Get subscriptions for a specific service type

### UserUsageTable

Tracks user activity across services for analytics and AI learning.

| Attribute     | Type   | Description                            | Required |
|---------------|--------|----------------------------------------|----------|
| accountId     | String | Cognito user ID (HASH key)             | Yes      |
| timestamp     | String | ISO datetime of activity (RANGE key)   | Yes      |
| serviceType   | String | Service identifier                     | Yes      |
| activityType  | String | Type of activity performed             | Yes      |
| details       | Object | Activity-specific details              | No       |
| deviceInfo    | Object | User's device information              | No       |
| sessionId     | String | Unique session identifier              | No       |

**Global Secondary Indexes:**
- **ServiceTypeIndex**: serviceType (HASH), timestamp (RANGE) - For service-specific analytics

**Access Patterns:**
1. Get user activity history by time range
2. Get service-specific activity analytics

## Profile Management Tables

These tables manage user profiles and their settings.

### ProfileTable

Stores minimal profile information - the focus of our recent simplification.

| Attribute     | Type    | Description                                 | Required |
|---------------|---------|---------------------------------------------|----------|
| accountId     | String  | Cognito user ID (HASH key)                  | Yes      |
| profileId     | String  | Unique UUID for the profile (RANGE key)     | Yes      |
| name          | String  | Display name for the profile                | Yes      |
| avatar        | String  | Avatar identifier or URL                    | No       |
| isKidsProfile | Boolean | Flag indicating if this is a child profile  | No       |
| createdAt     | String  | ISO datetime of creation                    | Yes      |
| updatedAt     | String  | ISO datetime of last update                 | No       |

**Global Secondary Indexes:**
- **ProfileIdIndex**: profileId (HASH) - For direct profile lookups

**Access Patterns:**
1. Get all profiles for an account
2. Get a specific profile by accountId and profileId
3. Look up a profile directly by profileId

**Example Item:**
```json
{
  "accountId": "123e4567-e89b-12d3-a456-426614174000",
  "profileId": "98765432-abcd-efgh-ijkl-123456789012",
  "name": "John",
  "avatar": "avatar2",
  "isKidsProfile": false,
  "createdAt": "2025-06-23T14:15:22Z",
  "updatedAt": "2025-06-23T14:15:22Z"
}
```

### ProfileSettingsTable

Stores extended profile settings including parental controls.

| Attribute         | Type    | Description                              | Required |
|-------------------|---------|------------------------------------------|----------|
| profileId         | String  | Profile UUID (HASH key)                  | Yes      |
| parentalControls  | Object  | Parental control settings                | No       |
| contentSettings   | Object  | Content display preferences              | No       |
| languageSettings  | Object  | Language and subtitle preferences        | No       |
| pinProtected      | Boolean | Whether settings require PIN to modify   | No       |
| pinCode           | String  | Encrypted PIN for settings protection    | No       |
| maxContentRating  | String  | Maximum allowed content rating           | No       |
| blockedGenres     | Array   | List of blocked content genres           | No       |
| blockedCreators   | Array   | List of blocked creators/actors          | No       |
| createdAt         | String  | ISO datetime of creation                 | Yes      |
| updatedAt         | String  | ISO datetime of last update              | No       |

**Access Patterns:**
1. Get settings for a specific profile

### ProfileAITable

Stores AI customization preferences for each profile.

| Attribute            | Type   | Description                             | Required |
|----------------------|--------|-----------------------------------------|----------|
| profileId            | String | Profile UUID (HASH key)                 | Yes      |
| aiInstructions       | String | Custom instructions for AI              | No       |
| recommendationStyle  | String | AI recommendation approach              | No       |
| favoriteGenres       | Array  | Preferred content genres                | No       |
| dislikedGenres       | Array  | Disliked content genres                 | No       |
| contentFilters       | Object | Content filtering preferences           | No       |
| explicitContentLevel | String | Tolerance for explicit content          | No       |
| createdAt            | String | ISO datetime of creation                | Yes      |
| updatedAt            | String | ISO datetime of last update             | No       |

**Access Patterns:**
1. Get AI preferences for a specific profile

## Streaming Service Tables

These tables are specific to the myAI.stream video streaming service.

### MovieTable

Catalog of available movies and shows.

| Attribute    | Type   | Description                            | Required |
|--------------|--------|----------------------------------------|----------|
| movieId      | String | Unique movie identifier (HASH key)     | Yes      |
| title        | String | Movie title                            | Yes      |
| genre        | String | Primary genre                          | Yes      |
| releaseYear  | String | Year of release                        | Yes      |
| director     | String | Movie director                         | No       |
| cast         | Array  | List of cast members                   | No       |
| rating       | String | Content rating                         | No       |
| duration     | Number | Duration in minutes                    | No       |
| description  | String | Movie description                      | No       |
| imageUrl     | String | Poster image URL                       | No       |
| trailerUrl   | String | Trailer video URL                      | No       |
| streamUrl    | String | Video stream URL                       | No       |

**Global Secondary Indexes:**
- **GenreIndex**: genre (HASH), releaseYear (RANGE) - For genre-based browsing
- **TitleIndex**: title (HASH) - For title searches

**Access Patterns:**
1. Get movie by ID
2. Browse movies by genre and release year
3. Search movies by title

### WatchlistTable

Tracks movies saved to user watchlists.

| Attribute   | Type   | Description                         | Required |
|-------------|--------|-------------------------------------|----------|
| accountId   | String | Cognito user ID (HASH key)          | Yes      |
| movieId     | String | Movie ID (RANGE key)                | Yes      |
| profileId   | String | Profile that added the movie        | Yes      |
| dateAdded   | String | ISO datetime when added             | Yes      |
| addedFrom   | String | Source of addition (browse, recommendation) | No    |

**Global Secondary Indexes:**
- **ProfileIndex**: profileId (HASH), movieId (RANGE) - For profile-specific watchlists

**Access Patterns:**
1. Get all watchlist items for an account
2. Get watchlist items for a specific profile
3. Check if a movie is in a watchlist

### WatchHistoryTable

Records viewing history and progress for resuming playback.

| Attribute      | Type   | Description                           | Required |
|----------------|--------|---------------------------------------|----------|
| accountId      | String | Cognito user ID (HASH key)            | Yes      |
| watchedAt      | String | ISO datetime of viewing (RANGE key)   | Yes      |
| profileId      | String | Profile that watched the content      | Yes      |
| movieId        | String | Movie ID                              | Yes      |
| progressSeconds| Number | Playback position in seconds          | No       |
| completed      | Boolean| Whether viewing was completed         | No       |
| deviceType     | String | Type of device used for viewing       | No       |

**Global Secondary Indexes:**
- **ProfileIndex**: profileId (HASH), watchedAt (RANGE) - For profile viewing history
- **MovieIndex**: movieId (HASH), watchedAt (RANGE) - For movie popularity metrics

**Access Patterns:**
1. Get viewing history for an account
2. Get viewing history for a specific profile
3. Get watch count and most recent viewers for a movie

## Data Relationships

- **Account ➔ Profiles**: One-to-many relationship (accountId)
- **Profile ➔ Settings**: One-to-one relationship (profileId)
- **Profile ➔ AI Preferences**: One-to-one relationship (profileId)
- **Profile ➔ Watchlist Items**: One-to-many relationship (profileId)
- **Profile ➔ Watch History**: One-to-many relationship (profileId)

## Notes

- The design intentionally avoids direct relationships in the DynamoDB schema, using key references instead
- All tables have point-in-time recovery enabled for data resilience
- All tables use server-side encryption for security
- This schema supports the separation of core identity attributes from service-specific and settings data
