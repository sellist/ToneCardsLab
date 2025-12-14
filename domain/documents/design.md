## As a teacher in a high IT security school, I should be able to without an account, be able to create a flashcard deck easily, and view it immediately.
    - Considerations:
        - No account creation or login required.
            - can look into cache for storing flashcard decks temporarily
        - Simple and intuitive interface for creating flashcards.
        - Immediate access to the created flashcard deck.
        - Option to share the deck via a link or export it.
## As a teacher in a lower IT security school, I should be able to save a collection of flashcard decks I make, and save them for later use.
    - Considerations:
        - Account creation with email and password.
            - use 3rd party provider, maybe OAuth (Google, Microsoft, etc.)
            - look into firebase with its auth and realtime db for storing flashcard decks for certain OAuth login. learn about that for setting up db securely
            - 
        - Ability to create, edit, and delete flashcard decks for specified user
            - future: can look into adding other users to collaborate on decks/read only for students
                - think of way to update other users when deck is updated in read only view
        - Save decks to the user's account for future access.
            - per OAuth
                future: can have permissions to deck, including owners (can edit), and read only
        - Option to organize decks into categories or subjects.
            - can also provide premade decks for common subjects (like instrument ranges, chord names -> chords, etc.) 


## backend design
- logical design:
-  use Firebase Firestore to store flashcard decks
- each user has their own collection of decks, each deck has an uuid, title, description, list of card ids, owner, shared with (list of user ids with read only access)
- each card has an uuid, front text, back text, which renderer to use (markdown, abc.js, image, etc.), content (like image url or whatever)
- - renderers:
  - string renderer: just display text as is
  - markdown renderer: use a library like marked.js to render markdown text
  - abc.js renderer: use abc.js library to render abc notation
  - image renderer: use img tag to display image from url
  - future: can add more renderers like latex, mermaid, etc.

- flashcard deck:
    - uuid (PK)
    - title
    - description
    - public (boolean)
    - owner user id (FK on user table)
      - if user is deleted, transfer a copy to all read only users with owner as that user and NO view only users, and delete the original deck
    - shared with: list of user ids with read only access
    - list of card uuids (deck uuid + card uuid as composite pk in many to many table)
- card:
  -  uuid (PK)
  - front content
  - back content
  - front content renderer type (markdown, abc.js, image, etc.)
  - back content renderer type (markdown, abc.js, image, etc.)
- user:
    - uuid (PK)
    - email ? or key to get specific OAuth provider user info maybe, look safe ways to do this with firebase
    - list of deck uuids owned
    - list of deck uuids with read only access
## needed api endpoints + request/response 
## API Endpoints Organized by Controllers

### AuthController:
- OAuth login request:
    - permissions: none (public endpoint)
    - request: email, password
    - response: success/failure, user id, auth token
- token refresh request:
    - permissions: valid refresh token
    - request: refresh token
    - response: new access token or auth failure
- logout request:
    - permissions: authenticated user
    - request: auth token
    - response: success/failure (invalidate token server-side)

### UserController:
- get user profile request:
    - permissions: authenticated user (own profile only)
    - request: auth token
    - response: user profile data (email, name, preferences)
    - note: this may be gotten from the OAuth provider user info maybe, look safe ways to do this
- update user profile request:
    - permissions: authenticated user (own profile only)
    - request: auth token, updated profile data
    - response: success/failure
- delete account request:
    - permissions: authenticated user (own account only)
    - request: auth token, confirmation
    - response: success/failure (transfer decks to viewers, cleanup data)

### DeckController:
- create deck request:
    - permissions: authenticated user
    - request: auth token, deck object (cards, title, description)
    - response: success/failure, provided deck id if success, auth error otherwise
    - note: keep unsaved deck on client machine if auth error occurs!
- get deck request:
    - permissions: deck owner OR deck viewer OR public deck
    - request: auth token, deck id
    - response: success/failure, full deck data including cards, metadata if success, auth error otherwise
- view accessible decks request:
    - permissions: authenticated user
    - request: auth token, page number (optional), page size (optional), sort order (optional)
    - response: success/failure, paginated list of decks user has access to (split by owner or viewer) with total count, auth error if not logged in
- update deck request:
    - permissions: deck owner only
    - request: auth token, deck id, updated deck object (cards, title, description)
    - response: success/failure, confirmation of update, auth error if not authorized to edit
- delete deck request:
    - permissions: deck owner only
    - request: auth token, deck id
    - response: success/failure, confirmation of deletion, auth error if not authorized to delete
- bulk delete decks request:
    - permissions: deck owner only (for each deck)
    - request: auth token, list of deck ids
    - response: success/failure for each deck
- duplicate deck request:
    - permissions: deck owner OR deck viewer OR public deck (to read), authenticated user (to create copy)
    - request: auth token, deck id to duplicate
    - response: success/failure, new deck id if success
- search decks request:
    - permissions: authenticated user
    - request: auth token, search query (title/description/tags)
    - response: filtered list of accessible decks
- import deck request:
    - permissions: authenticated user
    - request: auth token, deck data (JSON/CSV format)
    - response: success/failure, new deck id if success
- export deck request:
    - permissions: deck owner OR deck viewer OR public deck
    - request: auth token, deck id, format (JSON/CSV/PDF)
    - response: downloadable file or error
- get deck statistics request:
    - permissions: deck owner OR deck viewer OR public deck
    - request: auth token, deck id
    - response: card count, last modified, usage stats
- validate deck exists request:
    - permissions: none (public endpoint)
    - request: deck id
    - response: exists boolean, public status

### SharingController:
- view deck viewers request:
    - permissions: deck owner only
    - request: auth token, deck id
    - response: success/failure, list of user ids with read only access, auth error if not authorized
- edit viewers request:
    - permissions: deck owner only
    - request: auth token, deck id, list of user ids to add/remove from read only access
    - response: success/failure, confirmation of update, auth error if not authorized
- share deck by email request:
    - permissions: deck owner only
    - request: auth token, deck id, recipient email
    - response: success/failure (send invitation link)
- toggle deck public status request:
    - permissions: deck owner only
    - request: auth token, deck id, public boolean
    - response: success/failure

### PublicController:
- get premade decks request:
    - permissions: none (public endpoint)
    - request: none
    - response: success/failure, list of system premade and public deck uuids (cards, title, description)
- get public decks request:
    - permissions: none (public endpoint)
    - request: none
    - response: success/failure, paginated list of not premade and public deck uuids (cards, title, description)
- get public deck request:
    - permissions: none (public endpoint)
    - request: deck id
    - response: success/failure, deck object (cards, title, description), deck not found or not authorized error

### SystemController:
- get API health status request:
    - permissions: none (public endpoint)
    - request: none
    - response: service status, database connectivity
- rate limiting middleware:
    - permissions: none (applies to all endpoints)
    - implement per-endpoint rate limits to prevent API abuse

## Additional API Endpoint Considerations:

### CardController (individual card operations):
- create card request:
    - permissions: deck owner only
    - request: auth token, deck id, card object (front/back content, renderer types)
    - response: success/failure, new card id if success
- update card request:
    - permissions: deck owner only
    - request: auth token, deck id, card id, updated card object
    - response: success/failure
- delete card request:
    - permissions: deck owner only
    - request: auth token, deck id, card id
    - response: success/failure
- reorder cards request:
    - permissions: deck owner only
    - request: auth token, deck id, new card order array
    - response: success/failure

### FileUploadController:
- view image request:
    - permissions: none (public endpoint)
    - request: image URL
    - response: success/failure, image data if success
- view uploaded files request:
    - permissions: authenticated user
    - request: auth token
    - response: success/failure, list of user's uploaded file URLs
- upload image request:
    - permissions: authenticated user (if deck specified: deck owner only)
    - request: auth token, image file, deck id (optional)
    - response: success/failure, image URL if success
- delete uploaded file request:
    - permissions: file owner (user who uploaded it) OR admin
    - request: auth token, file URL
    - response: success/failure

### ReportingController:
- report inappropriate content request:
    - permissions: none (public endpoint, but rate limited)
    - request: deck id, reason, description
    - response: success/failure, report id
- get content moderation status request:
    - permissions: deck owner OR admin
    - request: auth token, deck id
    - response: success/failure, moderation status

## API Endpoints Organized by Permission Level

### Public Endpoints (No Authentication Required)
- `GET /api/v1/system/health` - Get API health status → service status, db connectivity
- `POST /api/v1/system/reports` - Report inappropriate content (deck_id, reason, description) → report id
- `POST /api/v1/auth/login` - OAuth login request (email, password) → user id, auth token
- `HEAD /api/v1/decks/{deck_id}` - Validate deck exists (deck_id) → exists boolean, public status
- `GET /api/v1/public/decks/premade` - Get premade decks → deck list
- `GET /api/v1/public/decks/public` - Get public decks (page, size) → paginated deck list
- `GET /api/v1/public/decks/{deck_id}` - Get public deck (deck_id) → deck object
- `GET /api/v1/files/images/{image_url}` - View image (image_url) → image data

### Authenticated User Endpoints (Valid Auth Token Required)
- `POST /api/v1/auth/refresh` - Token refresh request (refresh token) → new access token
- `POST /api/v1/auth/logout` - Logout request (auth token) → success/failure
- `GET /api/v1/users/profile` - Get user profile (auth token) → user profile data
- `PUT /api/v1/users/profile` - Update user profile (auth token, profile data) → success/failure
- `DELETE /api/v1/users/account` - Delete account (auth token, confirmation) → success/failure
- `POST /api/v1/decks/` - Create deck (auth token, deck object) → deck id
- `GET /api/v1/decks/` - View accessible decks (auth token, page, size, sort) → paginated deck list
- `GET /api/v1/decks/search` - Search decks (auth token, query) → filtered deck list
- `POST /api/v1/decks/import` - Import deck (auth token, deck data) → new deck id
- `GET /api/v1/files/` - View uploaded files (auth token) → file URL list
- `POST /api/v1/files/upload` - Upload image (auth token, image file, deck_id?) → image URL

### Resource Access Endpoints (Owner OR Viewer OR Public Deck)
- `GET /api/v1/decks/{deck_id}` - Get deck (auth token, deck_id) → deck object
- `POST /api/v1/decks/{deck_id}/duplicate` - Duplicate deck (auth token, deck_id) → new deck id
- `GET /api/v1/decks/{deck_id}/export` - Export deck (auth token, deck_id, format) → downloadable file
- `GET /api/v1/decks/{deck_id}/stats` - Get deck statistics (auth token, deck_id) → stats object

### Owner-Only Endpoints (Deck Owner Required)
- `PUT /api/v1/decks/{deck_id}` - Update deck (auth token, deck_id, deck object) → success/failure
- `DELETE /api/v1/decks/{deck_id}` - Delete deck (auth token, deck_id) → success/failure
- `DELETE /api/v1/decks/bulk` - Bulk delete decks (auth token, deck_ids[]) → success/failure per deck
- `POST /api/v1/decks/{deck_id}/cards` - Create card (auth token, deck_id, card object) → card id
- `PUT /api/v1/decks/{deck_id}/cards/{card_id}` - Update card (auth token, deck_id, card_id, card object) → success/failure
- `DELETE /api/v1/decks/{deck_id}/cards/{card_id}` - Delete card (auth token, deck_id, card_id) → success/failure
- `PUT /api/v1/decks/{deck_id}/cards/reorder` - Reorder cards (auth token, deck_id, card order[]) → success/failure
- `GET /api/v1/sharing/decks/{deck_id}/viewers` - View deck viewers (auth token, deck_id) → viewer list
- `PUT /api/v1/sharing/decks/{deck_id}/viewers` - Edit viewers (auth token, deck_id, user_ids[]) → success/failure
- `POST /api/v1/sharing/decks/{deck_id}/share` - Share deck by email (auth token, deck_id, email) → success/failure
- `PUT /api/v1/sharing/decks/{deck_id}/public` - Toggle deck public status (auth token, deck_id, public boolean) → success/failure
- `DELETE /api/v1/files/{file_url}` - Delete uploaded file (auth token, file_url) → success/failure

## API Endpoint Routes by Controller

### /api/v1/auth/
- `POST /login` - OAuth login request (email, password) → user id, auth token
- `POST /refresh` - Token refresh request (refresh token) → new access token
- `POST /logout` - Logout request (auth token) → success/failure

### /api/v1/users/
- `GET /profile` - Get user profile (auth token) → user profile data
- `PUT /profile` - Update user profile (auth token, profile data) → success/failure
- `DELETE /account` - Delete account (auth token, confirmation) → success/failure

### /api/v1/decks/
- `POST /` - Create deck (auth token, deck object) → deck id
- `GET /{deck_id}` - Get deck (auth token, deck_id) → deck object
- `GET /` - View accessible decks (auth token, page, size, sort) → paginated deck list
- `PUT /{deck_id}` - Update deck (auth token, deck_id, deck object) → success/failure
- `DELETE /{deck_id}` - Delete deck (auth token, deck_id) → success/failure
- `DELETE /bulk` - Bulk delete decks (auth token, deck_ids[]) → success/failure per deck
- `POST /{deck_id}/duplicate` - Duplicate deck (auth token, deck_id) → new deck id
- `GET /search` - Search decks (auth token, query) → filtered deck list
- `POST /import` - Import deck (auth token, deck data) → new deck id
- `GET /{deck_id}/export` - Export deck (auth token, deck_id, format) → downloadable file
- `GET /{deck_id}/stats` - Get deck statistics (auth token, deck_id) → stats object
- `HEAD /{deck_id}` - Validate deck exists (deck_id) → exists boolean, public status

### /api/v1/cards/
- `POST /decks/{deck_id}/cards` - Create card (auth token, deck_id, card object) → card id
- `PUT /decks/{deck_id}/cards/{card_id}` - Update card (auth token, deck_id, card_id, card object) → success/failure
- `DELETE /decks/{deck_id}/cards/{card_id}` - Delete card (auth token, deck_id, card_id) → success/failure
- `PUT /decks/{deck_id}/cards/reorder` - Reorder cards (auth token, deck_id, card order[]) → success/failure

### /api/v1/sharing/
- `GET /decks/{deck_id}/viewers` - View deck viewers (auth token, deck_id) → viewer list
- `PUT /decks/{deck_id}/viewers` - Edit viewers (auth token, deck_id, user_ids[]) → success/failure
- `POST /decks/{deck_id}/share` - Share deck by email (auth token, deck_id, email) → success/failure
- `PUT /decks/{deck_id}/public` - Toggle deck public status (auth token, deck_id, public boolean) → success/failure

### /api/v1/public/
- `GET /decks/premade` - Get premade decks () → deck list
- `GET /decks/public` - Get public decks (page, size) → paginated deck list
- `GET /decks/{deck_id}` - Get public deck (deck_id) → deck object

### /api/v1/files/
- `GET /images/{image_url}` - View image (image_url) → image data
- `GET /` - View uploaded files (auth token) → file URL list
- `POST /upload` - Upload image (auth token, image file, deck_id?) → image URL
- `DELETE /{file_url}` - Delete uploaded file (auth token, file_url) → success/failure

### /api/v1/system/
- `GET /health` - Get API health status () → service status, db connectivity
- `POST /reports` - Report inappropriate content (deck_id, reason, description) → report id
- `GET /reports/{deck_id}` - Get content moderation status (auth token, deck_id) → moderation status

## fastapi backend architecture

```
├── main.py                # FastAPI application entry point
├── routers/              # API route handlers (FastAPI routers)
│   ├── __init__.py
│   ├── auth.py           # AuthController equivalent
│   ├── users.py          # UserController equivalent
│   ├── decks.py          # DeckController equivalent
│   ├── cards.py          # CardController equivalent
│   ├── sharing.py        # SharingController equivalent
│   ├── public.py         # PublicController equivalent
│   ├── files.py          # FileUploadController equivalent
│   └── system.py         # SystemController equivalent
├── services/             # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   ├── deck_service.py
│   ├── card_service.py
│   ├── sharing_service.py
│   ├── file_service.py
│   ├── system_service.py
│   └── cache_service.py
├── repositories/         # Data access layer
│   ├── __init__.py
│   ├── user_repository.py
│   ├── deck_repository.py
│   ├── card_repository.py
│   ├── file_repository.py
│   └── system_repository.py
├── middleware/           # FastAPI middleware
│   ├── __init__.py
│   ├── auth_middleware.py
│   ├── permission_middleware.py
│   ├── rate_limit_middleware.py
│   └── error_handler.py
├── models/              # Pydantic models
│   ├── __init__.py
│   ├── user.py          # User schemas
│   ├── deck.py          # Deck schemas
│   ├── card.py          # Card schemas
│   ├── file.py          # File schemas
│   ├── system.py        # System/health schemas
│   └── responses.py     # API response models
├── config/              # Configuration
│   ├── __init__.py
│   ├── firebase.py      # Firebase Admin SDK setup
│   ├── database.py      # Firestore configuration
│   ├── redis.py         # Redis configuration
│   └── settings.py      # Environment settings
├── core/                # Core utilities
│   ├── __init__.py
│   ├── dependencies.py  # FastAPI dependencies
│   ├── security.py      # Authentication utilities
│   └── exceptions.py    # Custom exceptions
├── utils/               # Helper utilities
│   ├── __init__.py
│   ├── validators.py    # Custom validators
│   ├── permissions.py   # Permission checking
│   └── cache.py         # Caching utilities
└── tests/               # Test suite
    ├── __init__.py
    ├── conftest.py      # Test configuration
    ├── test_auth.py
    ├── test_decks.py
    └── test_cards.py
```