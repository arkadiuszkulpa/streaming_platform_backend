# MyAI4 Dependencies Guide

This document explains some of the key dependencies used in the MyAI4 ecosystem, their purposes, and how they fit into our architecture.

## Backend Integration Dependencies

### `aws-amplify`

**Note**: While AWS Amplify is included as a dependency in the package.json, it is **not used for backend API integration**. Our project uses a direct API Gateway integration with a centralized Lambda function instead. 

Amplify is included only for select utilities rather than its core API functionality. This gives us more control and flexibility with our backend communication. See [BACKEND_INTEGRATION_GUIDE.md](./BACKEND_INTEGRATION_GUIDE.md) for details on our API architecture.

### `aws-sdk`

Used for CloudFormation operations within the configuration fetching scripts, not for runtime API calls.

## Authentication Dependencies

### `react-oidc-context` and `oidc-client-ts`

These libraries provide OpenID Connect (OIDC) authentication integration with AWS Cognito. We use these rather than Amplify's authentication functionality for better control and customization.

## UI and Application Framework

### `react` and `react-dom`

The foundation of our UI layer.

### `react-router-dom`

Handles routing for our single-page application.

### `tailwindcss`

Our primary CSS framework for styling the application.

## Build System

### `vite`

Our build tool of choice for its speed and modern defaults.

## Testing

### `vitest` and related testing libraries

Used for unit and component testing.

## Configuration Management

### `dotenv`

Handles environment variable management for our application.

---

For detailed information about our backend connection approach, please see [BACKEND_INTEGRATION_GUIDE.md](./BACKEND_INTEGRATION_GUIDE.md).
