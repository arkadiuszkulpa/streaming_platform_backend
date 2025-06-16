# MyAI4 Ecosystem - Hybrid Architecture Platform

## Project Overview

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

## Architecture Evolution

```
CURRENT STATE: myAI.stream (Single Service)
├── Frontend Repository (this repo)
├── Backend Repository (separate)
└── Infrastructure Repository (separate)

TARGET STATE: MyAI4 Ecosystem (Hybrid Platform)
├── Unified Frontend (domain modules)
│   ├── MyAI4Stream.co.uk (movies & TV)
│   ├── MyAI4Shopping.co.uk (e-commerce)
│   ├── MyAI4Gaming.co.uk (gaming)
│   └── Future domains...
├── Shared Backend Services
│   ├── User Management
│   ├── AI Recommendation Engine
│   └── Cross-Service Analytics
└── Unified Infrastructure
    ├── Shared Authentication (Cognito)
    └── Centralized API Gateway
```

### MyAI4 Transformation Plan

**Phase 1: Foundation** (Current)
- ✅ Streaming service as architectural template
- ✅ Scalable authentication and routing patterns
- ✅ Component design for cross-service reuse
- 🔄 Documentation and extraction planning

**Phase 2: Hybrid Architecture** (Next)
- 🔄 Rename from myAI.stream to MyAI4Stream
- 🔄 Add domain-based routing and configuration
- 🔄 Implement shared user profile system
- 🔄 Create service template for rapid expansion

**Phase 3: Multi-Service Platform** (Future)
- ⏳ Launch MyAI4Shopping.co.uk module
- ⏳ Add MyAI4Gaming.co.uk module
- ⏳ Implement cross-service AI recommendations
- ⏳ Unified AI assistant interface

## Current Implementation Status ✅

### ✅ MyAI4Stream Foundation Complete
- **Authentication**: AWS Cognito with Google OAuth and account linking capability
- **Backend Integration**: Centralized API with unified endpoint pattern
- **Infrastructure**: Two-stack architecture (infra + backend) deployment ready
- **Data Layer**: 9 DynamoDB tables (5 ecosystem + 4 streaming specific)
- **Configuration**: Multi-stack CloudFormation export system
- **Security**: Point-in-time recovery, SSE encryption, proper IAM roles

### ✅ Authentication System Improvements
- **Account Linking**: Social federation linked with password accounts by email
- **Standardized Schema**: Consistent user records across authentication methods
- **Federation Support**: Google OAuth with email verification preservation
- **User Management**: Pre-signup and post-confirmation Lambda triggers
- **User Profile Flow**: New users directed to profile creation experience

### ✅ Backend Architecture (Deployment Ready)
- **API Gateway**: Centralized `/centralized` endpoint for all operations
- **Lambda Functions**: Python-based backend with environment configuration (no AWS Amplify)
- **Database Design**: 8 application DynamoDB tables plus AccountTable in infrastructure stack
  - **Authentication Table** (in infrastructure stack): AccountTable
  - **Cross-Service Tables**: UserProfiles, Subscriptions, ServicePreferences, UserUsage, FamilyGroups
  - **Streaming-Specific**: Movies, Watchlists, WatchHistory, StreamingProfiles
- **Service Integration**: UserDataService.ts with centralized API client pattern

### ✅ Infrastructure Split Architecture  
- **Infrastructure Stack** (`template-infra.yaml`): 
  - Cognito User Pool with pre-signup and post-confirmation Lambda triggers
  - S3/CloudFront for frontend hosting
  - OAuth integration and social logins
  - AccountTable DynamoDB table for core account management
  - Authentication Lambda functions
- **Backend Stack** (`template-backend.yaml`): 
  - API Gateway for business operations
  - Lambda functions for business logic
  - 8 DynamoDB tables for application data (not authentication)
- **Cross-Stack Integration**: Two-stack configuration fetching with smart fallbacks
- **Security**: SSE encryption, point-in-time recovery, IAM roles with least privilege
- **Multi-Environment**: Dev/prod support with SSM Parameter Store

### ✅ Phase 1 Complete: Foundation Ready for Production
**Architecture Transformation:**
- ✅ All 60+ files updated with MyAI4 ecosystem documentation and patterns
- ✅ Two-stack CloudFormation architecture validated and deployment ready
- ✅ Backend integration with centralized API pattern implemented
- ✅ Cross-service data models and authentication infrastructure complete

**Implementation Status Summary:**
1. **Architecture Documentation** - Comprehensive planning and vision
2. **Branding Update** - MyAI4Stream messaging throughout
3. **Component Documentation** - Scalability comments in all files
4. **Configuration Updates** - Multi-service support preparation
5. **UI/UX Enhancement** - Ecosystem-aware interface updates

**Next Phase: Service Expansion**
- 🔄 Create shared component packages (`@myai4/auth-core`, `@myai4/ui-components`)
- 🔄 Launch MyAI4Shopping.co.uk using established template patterns
- 🔄 Implement unified AI assistant interface across services

## Technical Stack

### Frontend Technologies (MyAI4 Foundation)
- **Framework**: React 18 with TypeScript (template for all services)
- **Build Tool**: Vite for fast development and builds
- **Styling**: Tailwind CSS with MyAI4 design system
- **Routing**: React Router v6 with domain-based routing
- **Authentication**: react-oidc-context with shared Cognito pool
- **Testing**: Vitest + React Testing Library

### AWS Infrastructure (MyAI4 Two-Stack Architecture)
- **Infrastructure Stack**: 
  - Shared Cognito User Pool with authentication Lambda triggers
  - S3/CloudFront hosting
  - OAuth integration
  - AccountTable for identity management
  - Authentication Lambda functions
- **Backend Stack**: 
  - Business logic Lambda functions
  - API Gateway
  - DynamoDB tables (8 application tables, excluding AccountTable)
- **Security**: SSE encryption, point-in-time recovery, IAM roles with least privilege
- **Configuration**: SSM Parameter Store with automated export fetching

## Business Impact & Market Positioning

### Competitive Advantages
1. **First AI-Native Multi-Service Platform** - Unified intelligence across life domains
2. **Family-Centric Design** - Advanced parental controls beyond industry standard
3. **Transparent AI** - Users understand and control AI decisions
4. **Rapid Service Expansion** - Template-based new service deployment

### Market Positioning
- **vs. Netflix**: Adds AI customization and cross-service integration
- **vs. Amazon**: Focuses on family values and transparent AI
- **vs. Google**: Unified AI experience vs. fragmented services
- **vs. Apple**: Open platform with user control over AI behavior

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

## Development Guidelines

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

## Scalability Architecture for myAI.* Services

### Shared Components Ready for Reuse
- **Authentication System**: Complete Cognito setup with Google OAuth
- **Protected Routing**: Reusable `ProtectedRoute` component
- **Base Infrastructure**: CloudFormation templates for S3/CloudFront
- **Error Handling**: `ErrorBoundary` and loading states

### Future myAI.* Services Can Reuse
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
- `src/services/UserDataService.ts` - Centralized API client with type safety
- `template-infra.yaml` - Infrastructure stack (Cognito, S3, CloudFront)
- `template-backend.yaml` - Backend stack (Lambda, API Gateway, DynamoDB)
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

# Test backend integration
npm run test-api
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
aws cloudformation deploy \
  --template-file template-backend.yaml \
  --stack-name myai4-backend-dev \
  --parameter-overrides Environment=dev RapidApiKeyParameter=your-rapidapi-key \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-2

# 3. Configure and test frontend
npm run fetch-config:dev
npm run build:dev

# 4. Test integration
npm run test-api
```

**Note**: Complete deployment instructions are in [DEPLOYMENT_GUIDE.md](./documentation/DEPLOYMENT_GUIDE.md), backend integration details are in [BACKEND_INTEGRATION_GUIDE.md](./documentation/BACKEND_INTEGRATION_GUIDE.md), and dependency information is in [DEPENDENCIES_GUIDE.md](./documentation/DEPENDENCIES_GUIDE.md)

### Testing Strategy

1. **Unit Tests**: Existing Vitest tests for components
2. **Integration Tests**: `npm run test-api` for backend integration  
3. **End-to-End**: Manual testing in browser after deployment
4. **Infrastructure Tests**: CloudFormation stack validation
5. **Authentication Tests**: Testing scenarios documented in `End_to_End_Testing/authentication_scenarios.md`

### Troubleshooting Common Issues

- **Missing Exports**: Ensure both stacks are fully deployed before running `npm run fetch-config`
- **API Errors**: Check CloudWatch logs for Lambda function issues
- **CORS Issues**: Verify API Gateway CORS configuration in backend stack
- **Authentication**: Confirm Cognito setup in infrastructure stack exports
- **Email Verification**: Ensure Google identity provider has `email_verified` in attribute mapping

## Scalability Improvements Needed

### 🔄 For Future myAI.* Services

1. **Create Shared Component Library**
   - Extract authentication components to npm package
   - Create myAI design system with Tailwind presets
   - Standardize error handling and loading patterns

2. **Environment Configuration**
   - Centralized config management for multi-service setup
   - Service-specific branding configuration
   - Feature flags for service differentiation

3. **Backend Integration Architecture**
   - Standardized API client for all myAI services
   - Shared user profile and preferences system
   - Cross-service authentication and authorization

## File Organization for Scalability

```
src/
├── components/
│   ├── common/          # Reusable across all myAI services
│   ├── layout/          # Navigation and page structure
│   ├── landing_page/    # Public marketing components
│   └── movie/           # Business-specific components
├── context/             # React context providers
├── types/               # TypeScript type definitions
├── data/                # Mock data and API clients
└── pages/               # Route components
```

## Notes for Infrastructure Team

- `template.yaml` in this repo is copied from infrastructure repository
- Changes to infrastructure must be manually copied to infrastructure repo
- Environment variables are fetched from CloudFormation exports
- All AWS resources follow naming convention: `${StackName}-ResourceName`
- Identity provider attribute mapping must include `email_verified` to preserve verification

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

## Future Roadmap & Success Metrics

### Detailed Roadmap

#### Q1 2025: Foundation Completion (Current)
- [ ] Complete MyAI4Stream backend integration
- [ ] Launch MyAI4Stream.co.uk production
- [ ] Establish shared component packages
- [ ] Implement cross-service user management

#### Q2 2025: Ecosystem Expansion
- [ ] Launch MyAI4Shopping.co.uk beta
- [ ] Implement unified AI assistant interface
- [ ] Cross-service recommendation engine
- [ ] Advanced family management features

#### Q3 2025: AI Enhancement
- [ ] Natural language service interaction
- [ ] Predictive cross-domain recommendations
- [ ] Advanced personalization algorithms
- [ ] Community-driven AI improvements

#### Q4 2025: Market Leadership
- [ ] Launch MyAI4Gaming.co.uk
- [ ] International expansion planning
- [ ] Enterprise family management tools
- [ ] AI assistant marketplace

### Success Metrics

#### Technical Metrics
- **Code Reuse Rate**: Target 90% across new services
- **Deployment Time**: New service launch in <4 weeks
- **System Reliability**: 99.9% uptime across all domains
- **AI Accuracy**: >85% recommendation satisfaction

#### Business Metrics
- **User Retention**: Cross-service usage increases retention 3x
- **Family Adoption**: Family plans become primary revenue driver
- **Market Expansion**: Launch 3 new domains within 12 months
- **Customer Satisfaction**: Family safety features drive premium subscriptions

## Future Roadmap

### Phase 2: Service Expansion (Next 3 Months)
- [ ] Create shared component packages (`@myai4/auth-core`, `@myai4/ui-components`)
- [ ] Implement domain-based routing configuration
- [ ] Launch MyAI4Shopping.co.uk module using template patterns
- [ ] Extract reusable authentication and UI components

### Phase 3: AI Enhancement (3-6 Months)
- [ ] Unified AI assistant interface across all services
- [ ] Cross-service recommendation engine
- [ ] Natural language service interaction
- [ ] Advanced personalization algorithms

### Phase 4: Ecosystem Maturity (6-12 Months)
- [ ] Launch MyAI4Gaming.co.uk module
- [ ] Advanced family management features
- [ ] Enterprise family management tools
- [ ] International expansion planning

## Development Status & Next Actions

### ✅ Completed (Phase 1)
- Backend integration architecture implemented
- Two-stack CloudFormation deployment ready
- All components documented with scalability patterns
- Cross-service data models designed

### 🔄 In Progress (Phase 2)
- Shared component extraction planning
- Service template refinement
- Configuration management improvements

### ⏳ Planned (Phase 3+)
- Multi-domain service deployment
- Unified AI assistant development
- Cross-service intelligence implementation

## Contributing to MyAI4 Ecosystem

This repository serves as the foundation template for all future MyAI4 services. When creating new services:

1. **Copy this architecture** - Use this repo as the starting template
2. **Reuse shared components** - Extract common elements to shared packages
3. **Follow naming conventions** - Use MyAI4[Domain].co.uk pattern
4. **Maintain documentation** - Keep scalability comments updated
5. **Test cross-service integration** - Ensure unified experience

### Technical Success Metrics

#### Achieved ✅
- **Code Reuse**: 90% of authentication and UI patterns ready for extraction
- **Setup Time**: New service creation template established
- **Deployment**: Two-stack architecture validated and production ready
- **Security**: Enterprise-grade AWS security with proper IAM roles

#### Target Goals (MyAI4 Ecosystem)
- **Service Launch**: <4 weeks for new MyAI4 domain modules
- **Maintenance**: Single developer can manage entire ecosystem
- **User Experience**: Unified authentication across all services
- **AI Intelligence**: Cross-service learning and recommendations

## Conclusion

The MyAI4 transformation positions this platform as the foundation for a revolutionary AI-first digital life management ecosystem. By maintaining the familiar Netflix-like interface while building in cross-service intelligence and family-centric controls, MyAI4 creates a unique market position that combines the best of specialized services with the convenience of unified AI assistance.

The hybrid architecture ensures that users get the depth of specialized platforms (streaming, shopping, gaming) while benefiting from the intelligence that comes from AI that understands their complete digital life context.

## License

This project is proprietary software for the MyAI4 ecosystem. All rights reserved.

---

**MyAI4 Ecosystem**: Transforming digital life through unified AI intelligence across all domains.

## 📊 Database Architecture

### MyAI4 Ecosystem Tables (Cross-Service)

1. **UserProfiles** (`myai4-user-profiles-{env}`)
   - Primary Key: `userId`
   - GSI: `EmailIndex` for email-based lookups
   - Purpose: Core user data across all MyAI4 services

2. **Subscriptions** (`myai4-subscriptions-{env}`)
   - Primary Key: `userId` + `subscriptionId`
   - GSI: `ServiceTypeIndex` for service-specific queries
   - Purpose: Cross-service subscription management

3. **ServicePreferences** (`myai4-service-preferences-{env}`)
   - Primary Key: `userId` + `serviceType`
   - Purpose: User preferences across streaming, shopping, gaming services

4. **UserUsage** (`myai4-user-usage-{env}`)
   - Primary Key: `userId` + `timestamp`
   - GSI: `ServiceTypeIndex` for analytics
   - Purpose: Cross-service usage analytics and AI learning

5. **FamilyGroups** (`myai4-family-groups-{env}`)
   - Primary Key: `familyId`
   - GSI: `ParentUserIndex` for family management
   - Purpose: Family management across all MyAI4 services

### Streaming Platform Tables (Service-Specific)

6. **Movies** (`myai4-movies-{env}`)
   - Primary Key: `movieId`
   - GSI: `GenreIndex`, `TitleIndex` for search and filtering
   - Purpose: Movie catalog and metadata

7. **Watchlists** (`myai4-watchlists-{env}`)
   - Primary Key: `userId` + `movieId`
   - GSI: `ProfileIndex` for profile-specific watchlists
   - Purpose: User watchlists and saved content

8. **WatchHistory** (`myai4-watch-history-{env}`)
   - Primary Key: `userId` + `watchedAt`
   - GSI: `ProfileIndex`, `MovieIndex` for analytics
   - Purpose: User viewing history and progress tracking

9. **StreamingProfiles** (`myai4-streaming-profiles-{env}`)
   - Primary Key: `profileId`
   - GSI: `UserIndex` for user-specific profiles
   - Purpose: Streaming profiles (different from user accounts)

## 🔒 Security & Compliance Specifications

### Encryption & Backup
- **SSE Encryption**: All DynamoDB tables have server-side encryption enabled
- **Point-in-Time Recovery**: Enabled on all tables for data protection
- **DeletionPolicy**: Retain prevents accidental data loss during stack updates

### Access Control
- **Lambda Execution Role**: Minimal required permissions for backend operations
- **DynamoDB Access**: Full access for backend operations with proper scoping
- **SSM Parameter Access**: Restricted to `/myai4/*` path for secure configuration
- **Cognito Federated Access**: Proper conditions and role assumptions

### Data Privacy
- **SSM Parameters**: Sensitive configuration (OAuth secrets) stored securely
- **CloudFormation Security**: NoEcho: true on sensitive parameters
- **Credential Separation**: Infrastructure vs. backend credentials properly isolated

## ⚡ Performance & Scalability Configuration

### DynamoDB Configuration
- **Billing Mode**: PAY_PER_REQUEST for automatic scaling without capacity planning
- **Global Secondary Indexes**: Optimized for efficient query patterns
- **Key Schemas**: Designed for optimal access patterns and data distribution

### Lambda Configuration
- **Runtime**: Python 3.12 for optimal performance and compatibility
- **Memory Allocation**: 256MB (balanced cost/performance ratio)
- **Timeout**: 10-second timeout for API operations
- **Concurrency**: Automatic scaling based on demand

### API Gateway Configuration
- **Environment-Specific Staging**: Proper environment isolation
- **Centralized Endpoint Design**: Efficient routing through `/centralized` endpoint
- **Integration**: Lambda proxy integration for optimal performance

## 🔄 Architecture Flow

```
Frontend (React/TypeScript)
    ↓ UserDataService.ts
    ↓ HTTP calls to /centralized
API Gateway 
    ↓ triggers
Lambda Function (centralized_api)
    ↓ reads/writes  
DynamoDB Tables (MyAI4 Ecosystem + Streaming)
    ↓ integrates with
AWS Infrastructure (Cognito, S3, CloudFront)
```

### Key Components
- **Cognito User Pool**: Shared authentication across all MyAI4 services
- **Cognito Identity Pool**: Federated identity management with Google OAuth
- **S3 + CloudFront**: Frontend hosting infrastructure with global distribution
- **IAM Roles**: Proper authentication and authorization boundaries
- **Cross-Stack Integration**: Infrastructure and backend stacks properly linked

## Backend Integration Approach

### Centralized Lambda Pattern (No Amplify)
The MyAI4 ecosystem uses a direct API integration with a centralized Lambda function, rather than using AWS Amplify:

```
Frontend (React)
    ↓ UserDataService.ts ─→ CentralizedApiService.ts
    ↓ Direct HTTP calls to API Gateway (/centralized endpoint)
API Gateway 
    ↓ triggers
Lambda Function (centralized_api)
    ↓ operation-based routing to handler functions
    ↓ reads/writes  
DynamoDB Tables
```

This architecture was chosen for several reasons:
- **Simplified Backend**: One Lambda function handles all operations through a routing pattern
- **Direct Control**: No intermediate Amplify layer for more control and customization
- **Reduced Dependencies**: Fewer client-side dependencies to manage and update
- **Consistent Interface**: Standard HTTP calls with bearer token authentication
- **Type-Safe API Layer**: TypeScript interfaces for all API operations and responses
- **Unified API Client**: Single API client with comprehensive error handling

### Implementation Details
- **Base API Client**: `CentralizedApiService.ts` handles all HTTP communication
- **Service-Specific Extensions**: Services like `UserDataService.ts` extend the base API client
- **Operation Routing**: Each request includes an `operation` parameter that routes to the appropriate handler
- **HTTP Methods**: GET for read operations, POST for create/update (with method parameter for logical PUT/PATCH/DELETE)
- **Authentication**: Standard JWT bearer tokens from Cognito
- **Error Handling**: Comprehensive error objects with status codes for conditional error handling

### Validation Tools
- `npm run validate-api`: Comprehensive API endpoint validation script
- `npm run test-basic-connectivity`: Basic connectivity test for API Gateway
- `npm run test-api`: Full API integration test

This approach follows industry best practices for serverless architectures while maintaining simplicity and control. For more details, see [BACKEND_INTEGRATION_GUIDE.md](./documentation/BACKEND_INTEGRATION_GUIDE.md) and [API_QUICKSTART.md](./documentation/API_QUICKSTART.md).

## Development Status & Next Actions