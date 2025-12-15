```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE  -- For soft deletes
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
```

**Notes:**
- `preferences` stores user settings as JSON
- Soft delete pattern for account deletion
- Email must be unique and indexed for quick lookups

```sql
CREATE TABLE decks (
    deck_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(1000),
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE  -- For soft deletes
);

CREATE INDEX idx_decks_owner_id ON decks(owner_id);
CREATE INDEX idx_decks_is_public ON decks(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_decks_created_at ON decks(created_at DESC);
CREATE INDEX idx_decks_deleted_at ON decks(deleted_at) WHERE deleted_at IS NULL;
```

**Notes:**
- Foreign key to `users` table with CASCADE delete
- `is_public` flag for public deck discovery
---

### 3. **cards**
Stores individual flashcards within decks.

```sql
CREATE TYPE renderer_type AS ENUM (
    'string',
    'markdown', 
    'abc_js',
    'image',
    'latex',
    'mermaid'
);

CREATE TABLE cards (
    card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID NOT NULL REFERENCES decks(deck_id) ON DELETE CASCADE,
    front_content TEXT NOT NULL,
    back_content TEXT NOT NULL,
    front_renderer renderer_type NOT NULL DEFAULT 'string',
    back_renderer renderer_type NOT NULL DEFAULT 'string',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cards_deck_id ON cards(deck_id);
```

---

### 4. **deck_viewers**
Junction table for deck sharing (many-to-many between users and decks).

```sql
CREATE TABLE deck_viewers (
    deck_id UUID NOT NULL REFERENCES decks(deck_id) ON DELETE CASCADE,
    viewer_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    granted_by UUID REFERENCES users(user_id),  -- Who shared it
    PRIMARY KEY (deck_id, viewer_id)
);

CREATE INDEX idx_deck_viewers_viewer_id ON deck_viewers(viewer_id);
CREATE INDEX idx_deck_viewers_deck_id ON deck_viewers(deck_id);
```

**Notes:**
- Composite primary key prevents duplicate sharing
- Tracks who granted access and when
- Cascade deletes when deck or user is deleted

---

### 5. **deck_invitations**
Stores email-based deck sharing invitations.

```sql
CREATE TABLE deck_invitations (
    invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID NOT NULL REFERENCES decks(deck_id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipient_email VARCHAR(255) NOT NULL,
    message VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'sent',  -- sent, accepted, expired, revoked
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_deck_invitations_recipient_email ON deck_invitations(recipient_email);
CREATE INDEX idx_deck_invitations_deck_id ON deck_invitations(deck_id);
CREATE INDEX idx_deck_invitations_status ON deck_invitations(status);
CREATE INDEX idx_deck_invitations_expires_at ON deck_invitations(expires_at);
```

**Notes:**
- Tracks invitation lifecycle
- Expiration support for time-limited invites
- Status tracking for invitation management

---

### 6. **uploaded_files**
Stores metadata for user-uploaded files (images, etc.).

```sql
CREATE TABLE uploaded_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    deck_id UUID REFERENCES decks(deck_id) ON DELETE SET NULL,  -- Optional association
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_url TEXT NOT NULL,  -- Storage path/URL
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE  -- For soft deletes
);

CREATE INDEX idx_uploaded_files_user_id ON uploaded_files(user_id);
CREATE INDEX idx_uploaded_files_deck_id ON uploaded_files(deck_id);
CREATE INDEX idx_uploaded_files_deleted_at ON uploaded_files(deleted_at) WHERE deleted_at IS NULL;
```

**Notes:**
- Optional deck association (files can exist independently)
- Soft delete for file recovery
- Stores size for quota management

---

### 7. **content_reports**
Stores user reports of inappropriate deck content.

```sql
CREATE TABLE content_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID NOT NULL REFERENCES decks(deck_id) ON DELETE CASCADE,
    reporter_id UUID REFERENCES users(user_id) ON DELETE SET NULL,  -- Allow anonymous reports
    reason VARCHAR(100) NOT NULL,
    description VARCHAR(1000),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, reviewed, actioned, dismissed
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES users(user_id),
    moderator_notes TEXT
);

CREATE INDEX idx_content_reports_deck_id ON content_reports(deck_id);
CREATE INDEX idx_content_reports_status ON content_reports(status);
CREATE INDEX idx_content_reports_submitted_at ON content_reports(submitted_at DESC);
```

**Notes:**
- Supports content moderation workflow
- Allows anonymous reports (nullable reporter_id)
- Tracks review status and moderator actions

---

### 8. **deck_moderation**
Stores moderation status for decks.

```sql
CREATE TABLE deck_moderation (
    deck_id UUID PRIMARY KEY REFERENCES decks(deck_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'approved',  -- approved, pending, flagged, removed
    reports_count INTEGER NOT NULL DEFAULT 0,
    last_reviewed TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES users(user_id),
    notes TEXT,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deck_moderation_status ON deck_moderation(status);
```

**Notes:**
- One-to-one relationship with decks
- Tracks aggregate report count
- Stores moderation decisions and notes

---

### 9. **auth_tokens** (Optional)
For token management and revocation (if not using stateless JWT).

```sql
CREATE TABLE auth_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,  -- Hashed token
    token_type VARCHAR(20) NOT NULL,  -- access, refresh
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX idx_auth_tokens_token_hash ON auth_tokens(token_hash);
CREATE INDEX idx_auth_tokens_expires_at ON auth_tokens(expires_at);
```

**Notes:**
- Store hashed tokens for revocation checking
- Supports token blacklisting
- Tracks token lifecycle

---

### 10. **deck_statistics** (Optional)
For tracking deck usage and analytics.

```sql
CREATE TABLE deck_statistics (
    stat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID NOT NULL REFERENCES decks(deck_id) ON DELETE CASCADE,
    view_count INTEGER NOT NULL DEFAULT 0,
    unique_viewers INTEGER NOT NULL DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    usage_data JSONB DEFAULT '{}',  -- Additional analytics
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deck_statistics_deck_id ON deck_statistics(deck_id);
CREATE INDEX idx_deck_statistics_view_count ON deck_statistics(view_count DESC);
```

**Notes:**
- Separate table for analytics to avoid locking main deck table
- JSONB field for flexible analytics data
- Can be periodically aggregated from events

---

## Helper Functions and Triggers

### Updated Timestamp Trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_decks_updated_at BEFORE UPDATE ON decks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deck_moderation_updated_at BEFORE UPDATE ON deck_moderation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deck_statistics_updated_at BEFORE UPDATE ON deck_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Refresh strategy:** Refresh periodically or after deck operations.

---

## Entity Relationship Summary

```
users (1) ──────< (many) decks
users (many) ────< deck_viewers >──── (many) decks
users (1) ──────< (many) uploaded_files
users (1) ──────< (many) content_reports
users (1) ──────< (many) deck_invitations

decks (1) ──────< (many) cards
decks (1) ────── (1) deck_moderation
decks (1) ────── (1) deck_statistics [optional]
decks (1) ──────< (many) content_reports
decks (1) ──────< (many) deck_invitations
```

---

## Additional Considerations

### 3. **Full-Text Search**
Add full-text search indexes for deck/card content:

```sql
ALTER TABLE decks ADD COLUMN search_vector tsvector;
CREATE INDEX idx_decks_search ON decks USING GIN(search_vector);

-- Update trigger to maintain search vector
CREATE TRIGGER decks_search_vector_update BEFORE INSERT OR UPDATE ON decks
FOR EACH ROW EXECUTE FUNCTION 
tsvector_update_trigger(search_vector, 'pg_catalog.english', title, description);
```

### 4. **Constraints**
Additional business logic constraints:

```sql
-- Ensure position uniqueness within a deck
CREATE UNIQUE INDEX idx_cards_unique_position ON cards(deck_id, position) 
WHERE position IS NOT NULL;

-- Ensure valid email format (basic check)
ALTER TABLE users ADD CONSTRAINT users_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
```

---

## Migration Notes

When implementing with Alembic:

1. **Order of table creation matters** due to foreign keys
2. Create ENUM types before tables that use them
3. Create tables before indexes and triggers
4. Use `alembic revision --autogenerate` to detect model changes
5. Always review auto-generated migrations before applying

---

## SQLAlchemy Models Reference

For Alembic migrations, you'll need to create SQLAlchemy ORM models that mirror this schema. The models should:

- Use UUID primary keys with `server_default=text("gen_random_uuid()")`
- Include relationship definitions for foreign keys
- Use `DateTime(timezone=True)` for timestamp fields
- Include soft delete filters where applicable
- Define ENUM types using SQLAlchemy's `Enum`

---

*Generated on 2025-12-14 based on Pydantic models in `/tcl-api/src/tcl_api/models/`*

