# MyAI4 Ecosystem - Hybrid Architecture

# Project Overview

MyAI4 represents a revolutionary AI-first approach to digital services, creating a unified platform that seamlessly integrates multiple life domains through a single, intelligent interface. This repository contains the foundation for **MyAI4Stream.co.uk** (streaming service), designed as the first module in a hybrid architecture that will expand to **MyAI4Shopping.co.uk**, **MyAI4Planning.co.uk**, and other AI-powered life management services.

### Vision: Beyond Google's Service Model - AI-First Integration
While Google pioneered multi-service authentication, MyAI4 goes further by creating a **truly unified AI experience** where users interact with one intelligent assistant that seamlessly handles all aspects of their digital life. The platform uses a hybrid approach - appearing as specialized services while sharing:
- 🤖 **Unified AI Assistant** - One chatbot interface for all life domains
- 🧠 **Cross-Domain Intelligence** - AI learns from all user interactions
- 👤 **Integrated Life Profiles** - Complete user context across all services
- 🔧 **Shared Infrastructure** - Single authentication and data layer

### Core Functionality
- **Netflix-like UI**: Familiar interface for user adoption
- **Custom Algorithm Instructions**: Users can provide detailed preferences for movie recommendations
- **Instant Recommendations**: Fast, relevant suggestions (seconds, not minutes)
- **Multi-user Decision Support**: Help groups of 2+ people find common viewing preferences

### Profile Management
- **Individual Profiles**: Personal recommendation engines
- **Children's Profiles**: 
  - Truly safe, parent-approved content only
  - Parental controls for blocking:
    - Specific movies or series
    - Characters or actors
    - Entire production companies
    - Content based on family values/beliefs
- **Movie Night Profiles**: 
  - Group profiles for shared viewing
  - Customizable preferences for group decisions

### Core Philosophy: AI-First Hybrid Approach
Unlike traditional microservices architecture, MyAI4 adopts a **hybrid approach** - a single codebase with domain-specific modules that share:
- ✨ **Unified Authentication** - One login across all services
- 🧠 **Shared AI Intelligence** - Cross-service learning and recommendations  
- 👤 **Integrated User Profiles** - Consistent experience across domains
- 🔧 **Common Infrastructure** - Scalable, cost-effective resource sharing

### Key MyAI4 Architectural Decisions

#### 1. Hybrid Repository Strategy
**Decision**: Single repository with domain modules vs. separate microservices  
**Rationale**: 
- Unified AI learning requires shared codebase
- Consistent user experience across domains
- Simplified deployment and maintenance
- Better cross-service feature development

#### 2. Cross-Domain AI Intelligence
**Innovation**: Single AI assistant that understands user preferences across all life domains
- Movie preferences influence shopping recommendations
- Gaming interests affect streaming suggestions
- Family values apply consistently across all services
- Natural language interaction for all domains

#### 3. Family-First Approach
**Enhanced Parental Controls**:
- Content blocking by personal values/beliefs
- Character/actor/company restrictions
- Cross-service family safety
- Parent-approved content only for children
- PIN protection for child profile settings (ProfileSettings table)

#### 4. Customizable AI Experience
**Innovation**: Profile-specific AI settings
- Personalized AI recommendations per profile
- Custom system messages for AI interactions
- Subscription-based premium AI features
- User-controlled algorithm transparency

## Business Impact & Market Positioning

### Competitive Advantages
1. **First AI-Native Multi-Service Platform** - Unified intelligence across life domains
2. **Family-Centric Design** - Advanced parental controls beyond industry standard
3. **Transparent AI** - Users understand and control AI decisions
4. **Rapid Service Expansion** - Template-based new service deployment

### Market Positioning vs Netflix, Amazon, Google, Apple
- Adds AI customization and cross-service integration
- Focuses on family values and transparent AI
- Unified AI experience vs. fragmented services
- Open platform with user control over AI behavior

### Technical Benefits

#### Development Efficiency
- **90% Code Reuse** across new MyAI4 services
- **Shared Component Library** reduces development time
- **Unified Testing Strategy** across all domains
- **Single Infrastructure Stack** for all services

#### User Experience Excellence
- **One Login** for entire digital life management
- **Consistent Interface** across all MyAI4 services
- **Intelligent Cross-Recommendations** based on full user context
- **Family-Safe by Design** with value-based filtering

#### AI Innovation
- **Unified Learning Model** across all user interactions
- **Context-Aware Recommendations** using full life picture
- **Transparent Decision Making** with user-understandable explanations
- **Customizable AI Personality** for different family members
- **Profile-specific AI settings** stored in dedicated ProfileAI table
- **PIN-protected settings** for parent-controlled AI experiences

# ─────────────────────────────────────────────
# Architecture Overview

The MyAI4 platform is built on a modular, scalable architecture that separates concerns across three main repositories: frontend, backend, and infrastructure. This approach enables rapid service duplication, robust security, and efficient code reuse across all MyAI4 domain services.

### Frontend

- **Framework**: React 18 with TypeScript, serving as the template for all MyAI4 services.
- **Build Tool**: Vite for fast development and optimized builds.
- **Styling**: Tailwind CSS, customized with the MyAI4 design system.
- **Routing**: React Router v6, supporting domain-based navigation.
- **Authentication**: `react-oidc-context` integrated with a shared AWS Cognito User Pool for unified login across services.
- **Testing**: Vitest and React Testing Library for comprehensive unit and integration testing.
- **Service Integration**: Domain-specific API clients (e.g., `UserDataService.ts`) abstract backend communication, ensuring type safety and modularity.

### Backend

- **API Gateway**: Exposes domain-specific endpoints (e.g., `/account`, `/profile`, `/movie`, `/watchlist`, `/profile-settings`, `/profile-ai`, `/subscription`).
- **Lambda Functions**: Modular Python-based handlers for each domain, enabling separation of business logic:
  - Account management (`lambda_handler_account.py`)
  - Profile management (`lambda_handler_profiles.py`)
  - PIN-protected profile settings (`lambda_handler_profile_settings.py`)
  - AI customization per profile (`lambda_handler_profile_ai.py`)
  - Movie catalog (`lambda_handler_movies.py`)
  - Watchlist operations (`lambda_handler_watchlists.py`)
  - Subscription management (`lambda_handler_subscription.py`)
- **Database**: 11 DynamoDB tables for application data (including cross-service and streaming-specific tables), plus an AccountTable managed in the infrastructure stack.
  - Cross-service: Profile, Subscription, UserUsage
  - Profile enhancements: ProfileSettings (PIN protection), ProfileAI (custom AI settings)
  - Streaming-specific: Movie, Watchlist, WatchHistory

### Infrastructure

- **Infrastructure Stack** (`template-infra.yaml`):
  - AWS Cognito User Pool with Lambda triggers for pre-signup and post-confirmation workflows.
  - S3 and CloudFront for secure, global frontend hosting.
  - OAuth integration (including Google) and federated identity support.
  - AccountTable DynamoDB table for core account management.
  - Authentication Lambda functions for account linking and user record standardization.
- **Backend Stack** (`template-backend.yaml`):
  - API Gateway with domain-based routing.
  - Specialized Lambda functions for each service domain.
  - 11 DynamoDB tables for application data.
- **Security & Configuration**:
  - SSE encryption and point-in-time recovery enabled on all tables.
  - IAM roles follow least-privilege principles.
  - SSM Parameter Store for secure configuration, with backend stack importing values directly from the infrastructure stack for simplified deployment.
- **Cross-Stack Integration**:
  - Backend stack now directly imports all required outputs from the infrastructure stack, streamlining deployment and reducing operational complexity.

This architecture ensures a clear separation of concerns, high code reuse, and robust security, while supporting rapid expansion of new MyAI4 domain services with minimal overhead.

---
# 📊 Database Architecture

### MyAI4 Ecosystem Tables (Cross-Service)

1. **AccountTable** (Managed in Infrastructure Stack)
   - Stored in infrastructure stack as it's used by Cognito triggers
   - Primary Key: `accountId` (HASH)
   - Purpose: Core user identity across all MyAI4 services
   - Referenced by Lambda functions using imported value from infrastructure stack

2. **Profile** (`myai4-profile-${AWS::StackName}`)
   - Primary Key: `accountId` (HASH) + `profileId` (RANGE)
   - GSI: `ProfileIdIndex` on `profileId` (HASH)
   - Purpose: User profiles within accounts across MyAI4 services

3. **ProfileSettings** (`myai4-profile-settings-${AWS::StackName}`)
   - Primary Key: `profileId` (HASH)
   - Purpose: Cross-service profile settings including PIN protection for parental controls
   - Used for family safety features across all MyAI4 services

4. **ProfileAI** (`myai4-profile-ai-${AWS::StackName}`)
   - Primary Key: `profileId` (HASH) 
   - Purpose: Cross-service AI customization settings for each profile
   - Enables consistent AI personalization across all MyAI4 services

5. **Subscriptions** (`myai4-subscription-${AWS::StackName}`)
   - Primary Key: `accountId` (HASH) + `subscriptionId` (RANGE)
   - GSI: `ServiceTypeIndex` on `serviceType` (HASH) with `accountId` (RANGE)
   - Purpose: Cross-service subscription management

6. **UserUsage** (`myai4-user-usage-${AWS::StackName}`)
   - Primary Key: `accountId` (HASH) + `timestamp` (RANGE)
   - GSI: `ServiceTypeIndex` on `serviceType` (HASH) with `timestamp` (RANGE)
   - Purpose: Cross-service usage analytics and AI learning

### Streaming Platform Tables (Service-Specific)

7. **Movie** (`myai4-movie-${AWS::StackName}`)
   - Primary Key: `movieId` (HASH)
   - GSI: `GenreIndex` on `genre` (HASH) with `releaseYear` (RANGE)
   - GSI: `TitleIndex` on `title` (HASH)
   - Purpose: Movie catalog and metadata

8. **Watchlist** (`myai4-watchlists-${AWS::StackName}`)
   - Primary Key: `accountId` (HASH) + `movieId` (RANGE)
   - GSI: `ProfileIndex` on `profileId` (HASH) with `movieId` (RANGE)
   - Purpose: User watchlists and saved content

9. **WatchHistory** (`myai4-watch-history-${AWS::StackName}`)
   - Primary Key: `accountId` (HASH) + `watchedAt` (RANGE)
   - GSI: `ProfileIndex` on `profileId` (HASH) with `watchedAt` (RANGE)
   - GSI: `MovieIndex` on `movieId` (HASH) with `watchedAt` (RANGE)
   - Purpose: User viewing history and progress tracking

# ─────────────────────────────────────────────
# Development Guidelines & Quick Start

### Authentication Flow
1. User visits landing page
2. Single "Sign in / Sign up" button redirects to Cognito Hosted UI
3. After authentication, redirects to profiles selection
4. All internal routes are protected and require authentication

### Project Goals (Priority Order)
1. **Reproducibility**: Infrastructure as Code for easy service duplication
2. **Shared Components**: Reusable authentication and UI components
3. **Scalability**: AWS-native architecture that scales automatically
4. **Security**: Enterprise-grade security with AWS best practices
5. **Maintainability**: Single-developer friendly with minimal overhead

## Scalability Architecture for myAI4 Services

### Shared Components Ready for Reuse
- **Authentication System**: Complete Cognito setup with Google OAuth
- **Protected Routing**: Reusable `ProtectedRoute` component
- **Base Infrastructure**: CloudFormation templates for S3/CloudFront
- **Error Handling**: `ErrorBoundary` and loading states

### Future MyAI4 Services Can Reuse
```typescript
// Shared authentication configuration
const oidcConfig = {
  authority: `https://cognito-idp.us-east-1.amazonaws.com/${POOL_ID}`,
  client_id: CLIENT_ID,
  // ... other reusable config
};

// Shared protected route component
<ProtectedRoute>
  <YourServiceComponent />
</ProtectedRoute>
```

## Key Files & Their Purpose

### Core Application (Deployment Ready)
- `src/App.tsx` - Main app with routing and authentication
- `src/main.tsx` - OIDC setup with MyAI4 ecosystem configuration
- `src/services/UserDataService.ts` - Domain-specific API clients with type safety
- `template-infra.yaml` - Infrastructure stack (Cognito, S3, CloudFront)
- `template.yaml` - Backend stack (Lambda, API Gateway, DynamoDB)
- `src/lambda_handler_*.py` - Specialized domain handlers (account, profiles, movies, watchlists, profile_settings, profile_ai)
- `fetch-cloudformation-exports.js` - Two-stack configuration management

### Authentication & Security
- `src/components/layout/Header.tsx` - Navigation with sign-out functionality
- `src/pages/LandingPage.tsx` - Public page with authentication flow
- `src/pages/ProfilesScreen.tsx` - Profile selection after authentication
- **Infrastructure Stack Authentication**:
  - `pre_signup_account_linking.py` - Federated identity linking (in infrastructure repo)
  - `post_confirmation_account_creation.py` - User account creation in AccountTable (in infrastructure repo)
  - `AccountTable` - Core user identity table (managed by authentication lambdas)

### Reusable Components
- `src/components/common/LoadingScreen.tsx` - Loading states
- `src/components/common/ErrorBoundary.tsx` - Error handling
- `src/components/common/Button.tsx` - Shared button component
- `src/components/common/Input.tsx` - Shared input component

## Quick Start & Deployment

### Prerequisites
- AWS CLI configured with deployment permissions
- Node.js 18+ and npm installed
- Access to AWS infrastructure and backend stacks

### Local Development
```bash
# Install dependencies
npm install

# Fetch configuration from both CloudFormation stacks
npm run fetch-config:dev

# Start development server
npm run dev
```

### Deployment (Ready for Production)
```bash
# 1. Deploy infrastructure stack (Cognito, S3, CloudFront)
aws cloudformation deploy \
  --template-file template-infra.yaml \
  --stack-name myai4-infrastructure-dev \
  --parameter-overrides Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-2

# 2. Deploy backend stack (Lambda, API Gateway, DynamoDB)
# Ideally using AWS CodePipeline or similar CI/CD tool, but for manual deployment:
aws cloudformation deploy \
  --template-file template-backend.yaml \
  --stack-name myai4-backend-dev \
  --parameter-overrides Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-2
```

### Troubleshooting Common Issues

- **Missing Exports**: Ensure both stacks are fully deployed before running `npm run fetch-config`
- **API Errors**: Check CloudWatch logs for Lambda function issues
- **CORS Issues**: Verify API Gateway CORS configuration in backend stack
- **Authentication**: Confirm Cognito setup in infrastructure stack exports
- **Email Verification**: Ensure Google identity provider has `email_verified` in attribute mapping

## Development and Testing

## Database Schema

A comprehensive database schema document is available in [documentation/database_schema.md](documentation/database_schema.md). This document outlines all tables used in the system, including:

- Cross-service tables (AccountTable, SubscriptionTable)
- Profile management tables (ProfileTable, ProfileSettingsTable, ProfileAITable)
- Streaming service tables (MovieTable, WatchlistTable, WatchHistoryTable)

The schema follows design principles of separation of concerns, where core entity data is kept separate from specialized data to support better scalability and performance.

## API Integration Testing

Run the app locally:
```powershell
cd C:\Projects\streaming_platform_frontend; npm run dev
```

### Profile Schema
Uses a simplified schema ([docs](documentation/profile_schema.md)) with:
- Core identity in the Profile table
- Extended settings in separate tables for better performance

## Security Considerations

- All routes except landing page require authentication
- User tokens are managed by react-oidc-context
- Logout properly clears local state and redirects to Cognito
- No sensitive data stored in localStorage
- CloudFront serves all assets over HTTPS
- Federated identities are properly linked to existing accounts
- User records follow standardized schema regardless of authentication method

## Authentication Flow & User Management

### Enhanced Authentication Strategy
1. **Multi-Provider Authentication**:
   - Email/Password authentication with verification
   - Google OAuth 2.0 federation
   - Account linking by email address

2. **Identity Consolidation**:
   - Prevents duplicate accounts for the same user
   - Pre-signup Lambda checks for existing users
   - Pre-signup Lambda links federated identities to existing password users
   - Pre-signup Lambda creates a new password user if federated identity tries to signup without one
   - This enables all users to have a single password user record in cognito user pool
   - Post-confirmation Lambda creates entry in AccountTable
   
3. **Profile Security**:
   - PIN-protected profile settings for child profiles
   - Parent-controlled AI settings for family safety
   - Profile-specific AI customization with subscription tiers
   - Links Google identities to existing password accounts
   - Maintains single user record in database regardless of auth method

3. **User Record Management**:
   - Pre-signup Lambda for federated account linking
   - Post-confirmation Lambda for standardized user records
   - Consistent schema across auth methods
   - DynamoDB integration with proper IAM permissions

4. **User Experience**:
   - Seamless login regardless of previous auth method
   - Profile management independent of auth method
   - Customizable user preferences preserved across login methods

## 🔒 Security & Compliance Specifications

• Encryption & Backup (SSE Encryption, Point-in-Time Recovery, DeletionPolicy)

• Access Control (Lambda Execution Role, DynamoDB Access, SSM Parameter Access, Cognito Federated Access)

• Data Privacy (SSM Parameters, CloudFormation Security, Credential Separation)

• Cross-Stack References (SSM Parameter Store, Decoupled Dependencies, Infrastructure Isolation)

## ⚡ Performance & Scalability Configuration

• DynamoDB Configuration (Billing Mode, Global Secondary Indexes, Key Schemas)

• Lambda Configuration (Runtime, Memory Allocation, Timeout, Concurrency)

• API Gateway Configuration (Environment-Specific Staging, Centralized Endpoint Design, Lambda Integration)

## ⚠️ CORS/Preflight Note for API Requests

- **Do not use GET requests with query parameters for complex payloads (e.g., operation/data objects) to API Gateway endpoints.**
- Browsers will include these query params in the preflight OPTIONS request URL, which can cause API Gateway to return 400 errors if the method expects no params.
- Use POST requests with a JSON body for all operations that require payloads or complex parameters to ensure CORS preflight works correctly.

## 🌐 CORS Configuration for Local Development

**Optimal Approach**: Lambda functions handle CORS for both OPTIONS and actual requests (POST/GET/etc.). This eliminates the need for separate CORS Lambda functions and reduces API Gateway complexity.

The backend stack includes a smart CORS handler that automatically supports both production and development environments:

- **Production**: Only allows the CloudFront domain
- **Development**: Allows localhost:5173, localhost:3000, and 127.0.0.1 variants for local testing

For non-simple requests (POST with JSON payloads), having the API Lambda functions handle both preflight (OPTIONS) and actual requests provides better control and single-point CORS management.

## AWS SAM Cognito Authorizer Configuration

**Important**: For Cognito User Pool authorizers, **do not specify Identity configuration**. Cognito automatically handles Authorization header validation, token extraction, and JWT verification. Adding explicit `Identity.Header` and `ValidationExpression` can break the standard OAuth2/OpenID Connect flow.

**Correct approach** - Let Cognito handle everything:
```yaml
Auth:
  DefaultAuthorizer: CognitoAuthorizer
  Authorizers:
    CognitoAuthorizer:
      UserPoolArn: !Sub "arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${UserPoolId}"
      AuthType: COGNITO_USER_POOLS
      # No Identity configuration needed - Cognito handles token validation
```

If you encounter persistent 401 Unauthorized errors even with correct tokens, ensure your SAM template properly configures explicit authorizers:

### Template Configuration
1. **Define the authorizer in API Gateway**:
```yaml
Auth:
  DefaultAuthorizer: CognitoAuthorizer
  Authorizers:
    CognitoAuthorizer:
      UserPoolArn: !Sub "arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${UserPoolId}"
      AuthType: COGNITO_USER_POOLS
```

2. **Add explicit Auth to each protected endpoint**:
```yaml
Events:
  ApiEvent:
    Type: Api
    Properties:
      RestApiId: !Ref ApiGateway
      Path: /profile
      Method: ANY
      Auth:
        Authorizer: CognitoAuthorizer
```

⚠️ **Important**: `DefaultAuthorizer` alone doesn't always work reliably. You must add explicit `Auth: Authorizer: CognitoAuthorizer` to each protected API event.

### Token Type Requirements
- Use `id_token` for API Gateway Cognito authorizers (not `access_token`)
- The `id_token` contains user identity claims that the authorizer validates
- Access tokens are for OAuth scopes and resource servers, not API Gateway

## Authentication: Access Token with OAuth 2.0 Scopes (Current Setup)

**CURRENT APPROACH**: Using access tokens with OAuth 2.0 scopes for scalable authorization.

### Access Token Approach (Current)
- **When to use**: Authorization Scopes are **SPECIFIED** on API Gateway method
- **Token**: Use `auth.user.access_token` from Cognito
- **Purpose**: Authorizes specific API operations based on scopes
- **Claims verified**:
  - `client_id` = App Client ID
  - `iss` (issuer) = User Pool
  - `scope` = OAuth 2.0 scopes (must match method scopes)
  - `token_use` = "access"
  - `exp` (expiration)
- **Prerequisites**: 
  - ✅ Resource Server defined in Cognito User Pool (`myai4-api`)
  - ✅ Custom scopes created (`myai4-api/read`, `myai4-api/write`, `myai4-api/admin`)
  - ✅ Scopes assigned to App Client
- **Configuration**:
  ```yaml
  Auth:
    Authorizer: CognitoAuthorizer
    AuthorizationScopes:
      - "myai4-api/read"
      - "myai4-api/write"
  ```

### OAuth 2.0 Scopes Defined
- `myai4-api/read`: Read access to user data and content
- `myai4-api/write`: Write access to user data and content  
- `myai4-api/admin`: Administrative access to all features

### ID Token Approach (Alternative)
- **When to use**: Authorization Scopes are **EMPTY** on API Gateway method
- **Token**: Use `auth.user.id_token` from Cognito
- **Purpose**: Authenticates the user's identity
- **Configuration**: 
  ```yaml
  Auth:
    Authorizer: CognitoAuthorizer
    # AuthorizationScopes: []  # MUST BE EMPTY
  ```

### Current Status
We're using **Access Token approach** with scopes for scalable authorization. All API Gateway methods require `myai4-api/read` and `myai4-api/write` scopes.

## Deployment Requirements

### Infrastructure Stack Changes (template-infra.yaml)
1. **Added Resource Server**: `UserPoolResourceServer` with identifier `myai4-api`
2. **Added OAuth Scopes**: 
   - `myai4-api/read` - Read access to user data and content
   - `myai4-api/write` - Write access to user data and content  
   - `myai4-api/admin` - Administrative access to all features
3. **Updated UserPoolClient**: Added resource server scopes to `AllowedOAuthScopes`

### Backend Stack Changes (template-backend.yaml)  
1. **Updated API Gateway Methods**: All Lambda functions now have `AuthorizationScopes` configured
2. **Required Scopes**: Each method requires both `myai4-api/read` and `myai4-api/write`

### Frontend Changes
1. **Updated Token Usage**: Changed from `id_token` to `access_token` in `useProfiles.ts`
2. **Updated Documentation**: README reflects access token approach

### Next Steps
1. Deploy infrastructure stack first (contains User Pool changes)
2. Deploy backend stack (contains API Gateway scope requirements)
3. Test authentication with new access token approach

The access token will now contain scopes that API Gateway validates against the method requirements.

### Debugging Tokens
Use the token debug utility:
```bash
node testing/token-debug.js <your-jwt-token>
```

This will show you token type, claims, and proper API Gateway configuration.

# MyStream.AI Frontend

## Navigation and Layout

### Header and Footer HUD (Heads-Up Display)

The application uses a fixed-position header and footer that serve as a HUD (Heads-Up Display) for navigation and controls. 

**HUD Visibility Rules:**
- Not shown on landing page (pre-authentication)
- Not shown on profile selection page
- Shown on all authenticated routes after profile selection
- Fixed position for easy access to navigation and controls
- Header uses transparency gradient for content visibility
- Footer provides quick access to key features and ecosystem navigation

**Header Features:**
- Brand logo and navigation
- Search functionality
- Community link
- Profile switcher
- Sign out option

**Footer Features:**
- My Watchlists
- My Settings
- My AI

Note: The header uses a gradient background to ensure content visibility, and both header and footer are fixed-position for consistent navigation access.

# Backend API Documentation

## Movie Lambda
The Movie Lambda handles all movie-related operations, including fetching movie details, searching by title, and managing watchlists. It integrates with the DynamoDB Movie table to provide fast access to movie metadata.

Each time a user searches for a movie or retrieves details, the movie lambda first queries the DynamoDB Movie table. If the movie is found it retrieves from the table, otherwise it uses various APIs to fetch the movie data form external sources. Some API elements need to be refreshed periodically to ensure the data is up-to-date (e.g. streaming-availability).

### Core Movie Data
- API used: advanced-movie-search

### Movie Scripts & Dialogues
- API used: opensubtitles-com

### Streaming Availability & New Releases
- API used: streaming-availability

## License

This project is proprietary software for the MyAI4 ecosystem. All rights reserved.