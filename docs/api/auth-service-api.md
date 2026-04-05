# Auth Service API Documentation

## Base URL

- Development: `http://localhost:8100`
- Production: `https://api.news-mcp.com/auth`

## Authentication

The Auth Service itself provides authentication for other services. Most endpoints require a valid JWT access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Types

- **Access Token**: Short-lived token for API access (default: 30 minutes)
- **Refresh Token**: Long-lived token for obtaining new access tokens (default: 7 days)
- **API Key**: Persistent key for service-to-service authentication (format: `nws_live_...` or `nws_test_...`)

### Authentication Methods

1. **JWT Bearer Token**: `Authorization: Bearer <access_token>`
2. **API Key**: `Authorization: ApiKey <api_key>`

## Endpoints

### Authentication

#### POST /api/v1/auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "string",        // Required: 3-50 chars, alphanumeric + underscore
  "email": "string",           // Required: valid email format
  "password": "string",        // Required: min 8 chars, mixed case, numbers, symbols
  "full_name": "string"        // Optional: user's full name
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:00:00Z",
  "roles": ["user"]
}
```

**Error Responses:**
- `400 Bad Request`: Validation error (weak password, invalid email, etc.)
- `409 Conflict`: Username or email already exists
- `500 Internal Server Error`: Registration failed

---

#### POST /api/v1/auth/login

Authenticate user and return access + refresh tokens.

**Request Body:**
```json
{
  "username": "string",    // Required: username or email
  "password": "string"     // Required
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800              // Seconds until access token expires
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `423 Locked`: Account locked due to failed login attempts
- `500 Internal Server Error`: Login failed

**Notes:**
- Failed login attempts are tracked and may result in account lockout
- Successful login resets failed attempt counter
- Login events are logged in audit trail

---

#### POST /api/v1/auth/refresh

Exchange refresh token for new access and refresh tokens.

**Request Body:**
```json
{
  "refresh_token": "string"    // Required: valid refresh token
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
- `401 Unauthorized`: User not found or inactive

**Notes:**
- Old refresh token is invalidated (refresh token rotation)
- Refresh tokens are single-use only

---

#### POST /api/v1/auth/logout

Logout user and blacklist current access token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token

**Notes:**
- Token is added to Redis blacklist with TTL matching token expiration
- Subsequent requests with blacklisted token will be rejected

---

#### GET /api/v1/auth/me

Get current authenticated user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:00:00Z",
  "last_login": "2025-01-19T12:00:00Z",
  "roles": ["user", "moderator"]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `401 Unauthorized`: Token blacklisted (user logged out)

---

### API Key Management

#### POST /api/v1/auth/api-keys

Create a new API key for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "string",              // Required: key identifier
  "description": "string",       // Optional: key purpose
  "expires_at": "2026-01-19T10:00:00Z"  // Optional: expiration date
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "key": "nws_live_abc123def456ghi789jkl012mno345pqr678stu901",  // Only shown once
  "prefix": "nws_live_abc",
  "name": "Production API",
  "description": "API key for production services",
  "created_at": "2025-01-19T10:00:00Z",
  "last_used_at": null,
  "expires_at": "2026-01-19T10:00:00Z",
  "is_active": true
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `400 Bad Request`: Invalid request data
- `500 Internal Server Error`: Key creation failed

**Notes:**
- The full API key is only returned once during creation
- Store the key securely - it cannot be retrieved later
- Key prefix format: `nws_{env}_{random}` where env is `live` or `test`

---

#### GET /api/v1/auth/api-keys

List all API keys for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "prefix": "nws_live_abc",
    "name": "Production API",
    "description": "API key for production services",
    "created_at": "2025-01-19T10:00:00Z",
    "last_used_at": "2025-01-19T12:30:00Z",
    "expires_at": "2026-01-19T10:00:00Z",
    "is_active": true
  },
  {
    "id": 2,
    "prefix": "nws_test_xyz",
    "name": "Development API",
    "description": "API key for development",
    "created_at": "2025-01-18T10:00:00Z",
    "last_used_at": "2025-01-19T09:15:00Z",
    "expires_at": null,
    "is_active": true
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token

**Notes:**
- Full API keys are never returned in list responses (only prefixes)
- Keys are ordered by creation date (newest first)

---

#### DELETE /api/v1/auth/api-keys/{key_id}

Delete (revoke) an API key.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `key_id` (integer): API key ID to delete

**Response:** `204 No Content`

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: API key not found or doesn't belong to user
- `500 Internal Server Error`: Deletion failed

**Notes:**
- Deleted keys are immediately revoked and cannot be used
- Deletion is permanent and cannot be undone

---

### User Management

#### GET /api/v1/users

List all users (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (integer, default: 1): Page number (≥1)
- `page_size` (integer, default: 50, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-01-19T10:00:00Z",
      "roles": ["user"]
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User is not admin
- `400 Bad Request`: Invalid query parameters

**Permissions:**
- Requires `admin` role or `is_superuser` flag

---

#### GET /api/v1/users/{user_id}

Get user by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `user_id` (integer): User ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:00:00Z",
  "last_login": "2025-01-19T12:00:00Z",
  "failed_login_attempts": 0,
  "locked_until": null,
  "roles": ["user", "moderator"]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User can only view own profile (unless admin)
- `404 Not Found`: User not found

**Permissions:**
- Users can view their own profile
- Admins can view any user profile

---

#### PUT /api/v1/users/{user_id}

Update user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `user_id` (integer): User ID

**Request Body:**
```json
{
  "full_name": "string",     // Optional
  "email": "string",         // Optional: must be valid email
  "is_active": boolean       // Optional: admin only
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john.new@example.com",
  "full_name": "John Michael Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T15:30:00Z",
  "roles": ["user"]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User can only update own profile (unless admin)
- `403 Forbidden`: Only admins can modify `is_active` status
- `404 Not Found`: User not found
- `400 Bad Request`: Invalid email format or other validation error
- `409 Conflict`: Email already in use

**Permissions:**
- Users can update their own profile (except `is_active`)
- Admins can update any user profile including `is_active`

---

### Health & Status

#### GET /health

Service health check endpoint.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "Auth Service",
  "version": "1.0.0",
  "timestamp": "2025-01-19T10:00:00Z",
  "database": "connected"
}
```

**Response when unhealthy:** `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "service": "Auth Service",
  "version": "1.0.0",
  "timestamp": "2025-01-19T10:00:00Z",
  "database": "disconnected"
}
```

**Notes:**
- Used by load balancers and monitoring systems
- Checks database connectivity
- No authentication required

---

#### GET /

Service information endpoint.

**Response:** `200 OK`
```json
{
  "service": "Auth Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

**Notes:**
- Returns basic service information
- No authentication required
- Links to OpenAPI documentation

---

## Data Models

### User

```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:00:00Z",
  "last_login": "2025-01-19T12:00:00Z",
  "failed_login_attempts": 0,
  "locked_until": null,
  "roles": ["user"]
}
```

### API Key

```json
{
  "id": 1,
  "prefix": "nws_live_abc",
  "name": "string",
  "description": "string",
  "created_at": "2025-01-19T10:00:00Z",
  "last_used_at": "2025-01-19T12:30:00Z",
  "expires_at": "2026-01-19T10:00:00Z",
  "is_active": true
}
```

### Role

```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "created_at": "2025-01-19T10:00:00Z"
}
```

## Error Codes

| HTTP Code | Meaning | When It Occurs |
|-----------|---------|----------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created (user, API key) |
| 204 | No Content | Resource deleted or action completed |
| 400 | Validation Error | Invalid payload, weak password, invalid email |
| 401 | Unauthorized | Missing or invalid credentials/token |
| 403 | Forbidden | Authenticated but lacks permission |
| 404 | Not Found | Resource not found (user, API key) |
| 409 | Conflict | Username/email already exists |
| 422 | Unprocessable Entity | Failed business rules |
| 423 | Locked | Account locked due to failed login attempts |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected failure |
| 503 | Service Unavailable | Service unhealthy (database down) |

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message description",
  "type": "error_type"
}
```

Examples:

```json
{
  "detail": "Incorrect username or password",
  "type": "authentication_error"
}
```

```json
{
  "detail": "Username already exists",
  "type": "conflict_error"
}
```

## Rate Limiting

- **Enabled by default**: `RATE_LIMIT_ENABLED=true`
- **Default limit**: 100 requests per hour per IP
- **Configurable**: `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`
- **Response**: `429 Too Many Requests` when limit exceeded

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642588800
```

## Versioning & Change Management

- **Current version**: API v1 (`/api/v1/`)
- **Version header**: Not required (version in URL path)
- **Deprecation policy**: 6 months notice before removing endpoints
- **Breaking changes**: New major version (v2, v3, etc.)
- **Change log**: See [CHANGELOG.md](../../CHANGELOG.md)

## OpenAPI Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8100/docs`
- ReDoc: `http://localhost:8100/redoc`
- OpenAPI JSON: `http://localhost:8100/openapi.json`

**Note**: Documentation endpoints are disabled in production (`DEBUG=false`)
