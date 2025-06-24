# Project Action Checklist

## Frontend Development Tasks

- [ ] Remove all mock data in frontend and replace with empty placeholders
  - Single example placeholder text for movie card/tile that populates with real details when API call succeeds

- [ ] Improve error handling by integrating with AWS CloudWatch
  - Currently uses basic error boundary without reporting or recovery mechanisms

## API Implementation Tasks

- [ ] Create frontend API services with Cognito JWT token authentication
  - Implement at least one call for each API service

- [ ] Profile API (CRUD)
  - Empty profile screen for new users
  - Profile creation functionality
  - Profile fetching on refresh (handle first login with no error)
  - Profile selection login
  - Edit/delete functionality

- [ ] Account API
  - Users cannot create accounts (handled by post confirmation lambda at signup)
  - Account details amendment
  - Account deletion

- [ ] Profile Settings API
  - Child profile setting
  - Future: PIN creation/amendment/deletion (compulsory for child profiles)
  - Service-specific settings (loved/liked/disliked/hated actors, directors, etc.)

- [ ] Movie API
  - Search functionality
  - Movie fetching

- [ ] Watchlist API (CRUD)

- [ ] Subscription API
  - Single tier plan initially

- [ ] Setting AI API
  - Custom message for LLM assistant

## Testing Tasks (After MVP Development)

- [ ] Implement unit tests
- [ ] Implement integration tests
- [ ] Implement end-to-end tests
- [ ] Integrate with CI/CD

## Feature Development Tasks

- [ ] Implement dropdown for swapping main screen functionality
  - Streaming: displays tiles from watchlists
  - Future: Shopping (display suggested items from Amazon)
  - Each service will have unique screen design
  - My Settings and My AI sections will have categories for each service

## Future Service Integration Plans

- [ ] MyAI4Learning
  - Same tile/card structure with recommended courses
  - Based on CV information and hobbies data from shopping

- [ ] MyAI4Planning
  - Task list main screen with AI-generated recommendations
  - Kanban style with AI-generated backlog
  - Prioritized based on user preferences

- [ ] MyAI4Shop
  - Tile system similar to movies
  - Displays items of interest based on user history

- [ ] MyAI4Gaming
  - Game recommendations based on values and beliefs

- [ ] Assistant bot
  - Enable My AI settings page and functionality
