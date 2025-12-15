### 1. **Users Router** (`/api/users`)
6 endpoints for user account management:
- `POST /users/` - Create user
- `GET /users/{user_id}` - Get user by ID
- `GET /users/email/{email}` - Get user by email
- `PATCH /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Soft delete user
- `GET /users/` - List/search users

### 2. **Decks Router** (`/api/decks`)
9 endpoints for deck management:
- `POST /decks/` - Create deck with cards
- `GET /decks/{deck_id}` - Get full deck
- `GET /decks/` - List/filter decks
- `GET /decks/user/{user_id}/dashboard` - User dashboard
- `PATCH /decks/{deck_id}` - Update deck
- `DELETE /decks/{deck_id}` - Soft delete deck
- `POST /decks/bulk-delete` - Delete multiple decks
- `POST /decks/{deck_id}/toggle-public` - Toggle visibility

### 3. **Cards Router** (`/api/cards`)
9 endpoints for card management:
- `POST /cards/` - Create card
- `GET /cards/{card_id}` - Get card
- `GET /cards/deck/{deck_id}` - Get deck cards
- `PATCH /cards/{card_id}` - Update card
- `DELETE /cards/{card_id}` - Delete card
- `POST /cards/deck/{deck_id}/reorder` - Reorder cards
- `POST /cards/deck/{deck_id}/bulk-create` - Create multiple cards
- `DELETE /cards/deck/{deck_id}/all` - Delete all cards

### 4. **Sharing Router** (`/api/sharing`)
9 endpoints for collaboration:
- `GET /sharing/decks/{deck_id}/viewers` - Get viewers
- `POST /sharing/decks/{deck_id}/viewers` - Add/remove viewers
- `POST /sharing/decks/{deck_id}/share-by-email` - Send invitation
- `GET /sharing/invitations/{invitation_id}` - Get invitation
- `POST /sharing/invitations/{invitation_id}/accept` - Accept invitation
- `GET /sharing/invitations/email/{email}` - List user invitations
- `DELETE /sharing/invitations/{invitation_id}` - Revoke invitation
- `POST /sharing/decks/{deck_id}/viewers/{viewer_id}/remove` - Remove viewer

### 5. **Files Router** (`/api/files`)
8 endpoints for file management:
- `POST /files/upload` - Upload file
- `GET /files/{file_id}` - Get file metadata
- `GET /files/user/{user_id}` - Get user files
- `GET /files/deck/{deck_id}` - Get deck files
- `DELETE /files/{file_id}` - Soft delete file
- `DELETE /files/{file_id}/permanent` - Hard delete file
- `POST /files/bulk-upload` - Upload multiple files

---