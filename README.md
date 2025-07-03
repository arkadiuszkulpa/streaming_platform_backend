# MyAI4 Ecosystem - Hybrid Architecture

# Project Overview

MyAI4 represents a revolutionary AI-first approach to digital services, creating a unified platform that seamlessly integrates multiple life domains through a single, intelligent interface. This repository contains the foundation for **MyAI4Stream.co.uk** (streaming service), designed as the first module in a hybrid architecture that will expand to **MyAI4Shopping.co.uk**, **MyAI4Planning.co.uk**, and other AI-powered life management services.

### Vision: Beyond Google's Service Model - AI-First Integration
While Google pioneered multi-service authentication, MyAI4 goes further by creating a **truly unified AI experience** where users interact with one intelligent assistant that seamlessly handles all aspects of their digital life. The platform uses a hybrid approach - appearing as specialized services while sharing:
- 🤖 **Unified AI Assistant** - One chatbot interface for all life domains
- 🧠 **Cross-Domain Intelligence** - AI learns from all user interactions
- 👤 **Integrated Life Profiles** - Complete user context across all services
- 🔧 **Shared Infrastructure** - Single authentication and data layer

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


## License

This project is proprietary software for the MyAI4 ecosystem. All rights reserved.
