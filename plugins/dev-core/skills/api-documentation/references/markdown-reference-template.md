# Шаблон: Markdown-референс API

Читать, когда собираешь человекочитаемый `docs/API.md` с нуля и нужен порядок
разделов + формат каждого блока. При дописывании эндпоинта в существующий файл
шаблон не нужен — повторяй формат соседних разделов.

Порядок разделов: Base URL → Authentication → Endpoints → Error Handling →
Rate Limiting → Webhooks → SDK examples → Changelog. Аутентификация идёт до
эндпоинтов, потому что без токена ни один пример из раздела Endpoints не
запускается.

---

## Base URL

```
https://api.example.com/v1
```

## Authentication

All requests require a Bearer token:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**Get token:**
```bash
curl -X POST https://api.example.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

**Response:**
```json
{ "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "expires_in": 3600 }
```

## Endpoints

### GET /users

List all users with pagination.

**Query parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (min: 1) |
| `limit` | integer | No | 20 | Items per page (min: 1, max: 100) |
| `sort` | string | No | `created_at` | Sort field |
| `order` | string | No | `desc` | `asc` or `desc` |

**Example request:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.example.com/v1/users?page=1&limit=20"
```

**Success (200 OK):**
```json
{
  "users": [
    { "id": 1, "name": "John Doe", "email": "john@example.com",
      "created_at": "2025-01-15T10:30:00Z" }
  ],
  "pagination": { "page": 1, "total": 100, "pages": 5,
                  "has_next": true, "has_prev": false }
}
```

**Errors:** `401` missing/invalid token · `400` invalid query params · `500` server error

### POST /users

Create a new user account.

**Request body:**
```json
{ "name": "John Doe", "email": "john@example.com",
  "password": "SecurePass123!", "age": 30 }
```

**Field validations:**
- `name` — string, 2-100 chars, required
- `email` — valid email, unique, required
- `password` — min 8 chars, at least 1 letter and 1 digit, required
- `age` — integer 13-120, optional

**Success (201 Created):**
```json
{ "id": 123, "name": "John Doe", "email": "john@example.com",
  "created_at": "2025-11-03T14:30:00Z" }
```

**Errors:**
- `400` validation failed — тело ошибки показывает, какое поле не прошло:
  ```json
  {
    "error": "validation_error",
    "message": "Invalid request data",
    "details": { "email": ["Email already exists"], "password": ["Password too weak"] }
  }
  ```
- `409` user with this email already exists
- `401` invalid authentication

## Error Handling

Единый формат для всех ошибок — иначе клиенту приходится писать парсер под каждый
эндпоинт:

```json
{ "error": "error_code", "message": "Human-readable message", "details": {} }
```

Коды: `unauthorized` · `forbidden` · `not_found` · `validation_error` ·
`rate_limit_exceeded` · `server_error`.

## Rate Limiting

- Authenticated: 1000 requests/hour
- Unauthenticated: 100 requests/hour

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1699027200
```

При превышении — `429` с `retry_after` в секундах.

## Webhooks

```bash
POST /webhooks
{ "url": "https://your-app.com/webhook", "events": ["user.created", "user.updated"] }
```

Payload:
```json
{ "event": "user.created", "data": { "id": 123, "name": "John Doe" },
  "timestamp": "2025-11-03T14:30:00Z" }
```

## SDK examples

```typescript
import { UserAPI } from '@example/api-client';
const api = new UserAPI({ token: 'YOUR_TOKEN' });
const users = await api.users.list({ page: 1, limit: 20 });
```

```python
from example_api import UserAPI
api = UserAPI(token='YOUR_TOKEN')
users = api.users.list(page=1, limit=20)
```

## Changelog

### v1.0.0 (2025-11-03)
- Initial API release
- User CRUD operations
- JWT authentication
