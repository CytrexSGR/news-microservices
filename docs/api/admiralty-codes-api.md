# Admiralty Codes API Documentation

## Base Information

- **Service:** Feed Service
- **Base URL:** `http://localhost:8101/api/v1/admiralty-codes`
- **Authentication:** Required (Bearer JWT)
- **Version:** 1.0.0
- **Last Updated:** 2025-10-21

## Overview

The Admiralty Codes API provides endpoints for managing quality rating configuration:
- **Thresholds:** Configure A-F rating boundaries based on quality scores
- **Weights:** Configure category weights for quality score calculation
- **Validation:** Ensure configuration consistency

## Authentication

All endpoints require a valid JWT token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Endpoints

### Thresholds Management

#### GET /thresholds

Get all Admiralty Code thresholds (A-F ratings).

**Response:** `200 OK`
```json
[
  {
    "id": "78b53dbb-784e-4863-86fe-9b34319b4cea",
    "code": "A",
    "label": "Completely Reliable",
    "min_score": 90,
    "description": "Premium sources with exceptional credibility...",
    "color": "green",
    "created_at": "2025-10-21T15:39:17.089798Z",
    "updated_at": "2025-10-21T15:39:17.089798Z"
  },
  {
    "id": "33adeb29-e540-4a76-8ab3-d927f7482e62",
    "code": "B",
    "label": "Usually Reliable",
    "min_score": 75,
    "description": "Trusted sources with strong credibility...",
    "color": "blue",
    "created_at": "2025-10-21T15:39:17.089798Z",
    "updated_at": "2025-10-21T15:39:17.089798Z"
  }
  // ... C, D, E, F
]
```

**Errors:**
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Database error

---

#### GET /thresholds/{code}

Get a specific threshold by code (A, B, C, D, E, or F).

**Parameters:**
- `code` (path, string, required): Admiralty code letter (case-insensitive)

**Example Request:**
```bash
GET /api/v1/admiralty-codes/thresholds/B
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "33adeb29-e540-4a76-8ab3-d927f7482e62",
  "code": "B",
  "label": "Usually Reliable",
  "min_score": 75,
  "description": "Trusted sources with strong credibility, solid editorial practices...",
  "color": "blue",
  "created_at": "2025-10-21T15:39:17.089798Z",
  "updated_at": "2025-10-21T15:39:17.089798Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid code (not A-F)
- `404 Not Found` - Threshold not found
- `401 Unauthorized` - Invalid or missing JWT

---

#### PUT /thresholds/{code}

Update a threshold's configuration.

**Parameters:**
- `code` (path, string, required): Admiralty code letter

**Request Body:**
```json
{
  "min_score": 80,
  "label": "Very Reliable",
  "description": "Updated description",
  "color": "blue"
}
```

**Fields (all optional):**
- `min_score` (integer, 0-100): Minimum quality score for this rating
- `label` (string): Display label
- `description` (string): Detailed description
- `color` (string): Color name (green, blue, yellow, orange, red, gray)

**Example Request:**
```bash
PUT /api/v1/admiralty-codes/thresholds/B
Authorization: Bearer <token>
Content-Type: application/json

{
  "min_score": 80,
  "label": "Very Reliable"
}
```

**Response:** `200 OK`
```json
{
  "id": "33adeb29-e540-4a76-8ab3-d927f7482e62",
  "code": "B",
  "label": "Very Reliable",
  "min_score": 80,
  "description": "Trusted sources with strong credibility...",
  "color": "blue",
  "created_at": "2025-10-21T15:39:17.089798Z",
  "updated_at": "2025-10-21T16:45:30.123456Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid code or validation failed
- `404 Not Found` - Threshold not found
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Update failed

---

#### POST /thresholds/reset

Reset all thresholds to hardcoded defaults.

**⚠️ Warning:** This deletes all custom configurations and cannot be undone.

**Default Values:**
- A: 90 (Completely Reliable, green)
- B: 75 (Usually Reliable, blue)
- C: 60 (Fairly Reliable, yellow)
- D: 40 (Not Usually Reliable, orange)
- E: 20 (Unreliable, red)
- F: 0 (Cannot Be Judged, gray)

**Example Request:**
```bash
POST /api/v1/admiralty-codes/thresholds/reset
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  { "code": "A", "min_score": 90, ... },
  { "code": "B", "min_score": 75, ... },
  ...
]
```

**Errors:**
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Reset failed

---

### Weights Management

#### GET /weights

Get all category weights for quality score calculation.

**Response:** `200 OK`
```json
[
  {
    "id": "321312f2-8248-47b9-a5c5-4e42552ed25f",
    "category": "credibility",
    "weight": "0.40",
    "description": "Weight for credibility tier assessment...",
    "min_value": "0.00",
    "max_value": "1.00",
    "created_at": "2025-10-21T15:39:17.089798Z",
    "updated_at": "2025-10-21T15:39:17.089798Z"
  },
  {
    "id": "7e847e95-9c69-458e-8009-6afaa6bc563c",
    "category": "editorial",
    "weight": "0.25",
    "description": "Weight for editorial standards evaluation...",
    "min_value": "0.00",
    "max_value": "1.00",
    "created_at": "2025-10-21T15:39:17.089798Z",
    "updated_at": "2025-10-21T15:39:17.089798Z"
  }
  // ... trust (0.20), health (0.15)
]
```

**Errors:**
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Database error

---

#### GET /weights/{category}

Get a specific category weight.

**Parameters:**
- `category` (path, string, required): credibility, editorial, trust, or health

**Example Request:**
```bash
GET /api/v1/admiralty-codes/weights/credibility
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "321312f2-8248-47b9-a5c5-4e42552ed25f",
  "category": "credibility",
  "weight": "0.40",
  "description": "Weight for credibility tier assessment (tier_1/tier_2/tier_3)...",
  "min_value": "0.00",
  "max_value": "1.00",
  "created_at": "2025-10-21T15:39:17.089798Z",
  "updated_at": "2025-10-21T15:39:17.089798Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid category
- `404 Not Found` - Weight not found
- `401 Unauthorized` - Invalid or missing JWT

---

#### PUT /weights/{category}

Update a category weight.

**⚠️ Important:** After updating, all weights must sum to 1.00 (100%).
If they don't, the update will fail with validation error.

**Parameters:**
- `category` (path, string, required): credibility, editorial, trust, or health

**Request Body:**
```json
{
  "weight": 0.45,
  "description": "Updated weight for credibility assessment"
}
```

**Fields:**
- `weight` (number, required): New weight value (0.00-1.00)
- `description` (string, optional): Updated description

**Example Request:**
```bash
PUT /api/v1/admiralty-codes/weights/credibility
Authorization: Bearer <token>
Content-Type: application/json

{
  "weight": 0.45,
  "description": "Increased credibility importance"
}
```

**Response:** `200 OK`
```json
{
  "id": "321312f2-8248-47b9-a5c5-4e42552ed25f",
  "category": "credibility",
  "weight": "0.45",
  "description": "Increased credibility importance",
  "min_value": "0.00",
  "max_value": "1.00",
  "created_at": "2025-10-21T15:39:17.089798Z",
  "updated_at": "2025-10-21T16:50:15.789012Z"
}
```

**Errors:**
- `400 Bad Request` - Validation failed (weights don't sum to 1.00)
  ```json
  {
    "detail": "Weights must sum to 1.00 (100%). Please adjust other weights accordingly."
  }
  ```
- `404 Not Found` - Category not found
- `401 Unauthorized` - Invalid or missing JWT

**Workflow for updating weights:**
1. Get current weights: `GET /weights`
2. Calculate new distribution (must sum to 1.00)
3. Update each weight sequentially
4. Validate: `GET /weights/validate`

---

#### POST /weights/reset

Reset all weights to hardcoded defaults.

**⚠️ Warning:** This deletes all custom configurations.

**Default Values:**
- credibility: 0.40 (40%)
- editorial: 0.25 (25%)
- trust: 0.20 (20%)
- health: 0.15 (15%)

**Example Request:**
```bash
POST /api/v1/admiralty-codes/weights/reset
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  { "category": "credibility", "weight": "0.40", ... },
  { "category": "editorial", "weight": "0.25", ... },
  { "category": "trust", "weight": "0.20", ... },
  { "category": "health", "weight": "0.15", ... }
]
```

**Errors:**
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Reset failed

---

#### GET /weights/validate

Validate that all weights sum to 1.00 (100%).

**Example Request:**
```bash
GET /api/v1/admiralty-codes/weights/validate
Authorization: Bearer <token>
```

**Response (Valid):** `200 OK`
```json
{
  "is_valid": true,
  "total": "1.00",
  "message": "Weights are valid (sum to 1.00)"
}
```

**Response (Invalid):** `200 OK`
```json
{
  "is_valid": false,
  "total": "0.95",
  "message": "Weights are invalid (sum to 0.95, should be 1.00)"
}
```

**Errors:**
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Validation failed

---

### Status & Validation

#### GET /status

Get overall configuration status.

**Example Request:**
```bash
GET /api/v1/admiralty-codes/status
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "thresholds_count": 6,
  "weights_count": 4,
  "weights_valid": true,
  "using_defaults": false
}
```

**Fields:**
- `thresholds_count` (integer): Number of configured thresholds (should be 6)
- `weights_count` (integer): Number of configured weights (should be 4)
- `weights_valid` (boolean): Whether weights sum to 1.00
- `using_defaults` (boolean): Whether using hardcoded defaults (no DB records)

**Errors:**
- `401 Unauthorized` - Invalid or missing JWT
- `500 Internal Server Error` - Status check failed

---

## Feed Integration

When fetching feeds, the `admiralty_code` field is automatically populated:

### GET /api/v1/feeds

**Response includes:**
```json
{
  "id": "64c228ba-b534-4168-b779-b55762780eba",
  "name": "DW English",
  "url": "https://rss.dw.com/rdf/rss-en-all",
  "quality_score": 85,
  "admiralty_code": {
    "code": "B",
    "label": "Usually Reliable",
    "color": "blue"
  },
  "assessment": {
    "credibility_tier": "tier_1",
    "reputation_score": 90,
    ...
  },
  ...
}
```

### GET /api/v1/feeds/{id}

Same structure - `admiralty_code` included automatically.

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input/validation failed |
| 401 | Unauthorized | Missing/invalid JWT |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server/database error |

---

## Rate Limiting

- **Inherited from FastAPI middleware**
- Typical limits: 100 requests/minute per IP
- 429 Too Many Requests if exceeded

---

## Caching

### Backend Caching
- Thresholds cached in-memory after first load
- Weights cached in-memory after first load
- Cache invalidated on updates

### Client Caching Recommendations
- Cache GET responses for 10-60 seconds
- Invalidate on PUT/POST mutations
- Use ETags if available

---

## Examples

### Complete Configuration Update Workflow

```bash
# 1. Check current status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/admiralty-codes/status

# 2. Get current thresholds
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/admiralty-codes/thresholds

# 3. Update threshold B to 80
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"min_score": 80}' \
  http://localhost:8101/api/v1/admiralty-codes/thresholds/B

# 4. Get current weights
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/admiralty-codes/weights

# 5. Update credibility to 0.45
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"weight": 0.45}' \
  http://localhost:8101/api/v1/admiralty-codes/weights/credibility

# 6. Update editorial to 0.20 (to maintain sum = 1.00)
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"weight": 0.20}' \
  http://localhost:8101/api/v1/admiralty-codes/weights/editorial

# 7. Validate weights
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/admiralty-codes/weights/validate

# 8. Verify feed includes updated admiralty code
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/feeds/64c228ba-b534-4168-b779-b55762780eba
```

---

## Testing

### Endpoint Health Check

```bash
#!/bin/bash
TOKEN="your_jwt_token_here"
BASE_URL="http://localhost:8101/api/v1/admiralty-codes"

echo "=== Testing Admiralty Codes API ==="

echo -e "\n1. Status:"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/status" | jq

echo -e "\n2. Thresholds:"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/thresholds" | jq 'length'

echo -e "\n3. Weights:"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/weights" | jq 'length'

echo -e "\n4. Validation:"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/weights/validate" | jq '.is_valid'

echo -e "\n✅ All endpoints reachable"
```

---

## Changelog

### 2025-10-21 - v1.0.0
- Initial release
- 10 endpoints implemented
- Full CRUD for thresholds and weights
- Validation and status endpoints
- Feed integration

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/news-microservices/issues
- Internal Docs: `/docs/features/admiralty-code-system.md`
- Service Logs: `docker logs news-feed-service`
