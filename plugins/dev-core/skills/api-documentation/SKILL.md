---
name: api-documentation
description: "API docs from code: OpenAPI/Swagger specs, Postman collections, examples for REST, GraphQL, gRPC. NOT whole-codebase docs -> openwiki."
keywords: api, documentation, openapi, swagger, postman, rest, graphql, api-docs
---

# API Documentation Generator

## Purpose
Автоматическая генерация профессиональной API документации из кода. Поддерживает REST, GraphQL, gRPC APIs и создаёт multiple formats для разных audiences.

## Capabilities

### 1. OpenAPI/Swagger Generation

#### From FastAPI (Auto-generation)
```python
from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="My API",
    description="Comprehensive API for managing users",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

class User(BaseModel):
    """User model with validation"""
    id: int
    name: str
    email: str
    age: Optional[int] = None

@app.get("/users/{user_id}", response_model=User, tags=["users"])
async def get_user(
    user_id: int = Path(..., description="User ID", ge=1),
    include_details: bool = Query(False, description="Include full details")
) -> User:
    """
    Get user by ID.

    Returns:
        User object with all details

    Raises:
        404: User not found
        401: Unauthorized
    """
    return User(id=user_id, name="John", email="john@example.com")
```

**Generated OpenAPI available at `/openapi.json`**

#### From Express/TypeScript
```typescript
import { z } from 'zod';
import { createExpressEndpoints, initOpenAPI } from '@your/openapi-gen';

const UserSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email()
});

initOpenAPI({
  title: 'My API',
  version: '1.0.0'
});

app.get('/users/:id',
  createExpressEndpoints(UserSchema, {
    summary: 'Get user by ID',
    parameters: [{
      name: 'id',
      in: 'path',
      required: true,
      schema: { type: 'integer' }
    }]
  }),
  async (req, res) => {
    // Handler
  }
);
```

#### Manual OpenAPI Spec
```yaml
openapi: 3.0.3
info:
  title: User Management API
  description: API for managing users, authentication, and profiles
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com
  license:
    name: MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

paths:
  /users:
    get:
      summary: List all users
      description: Returns a paginated list of users
      operationId: listUsers
      tags:
        - users
      parameters:
        - name: page
          in: query
          description: Page number for pagination
          required: false
          schema:
            type: integer
            default: 1
            minimum: 1
        - name: limit
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            default: 20
            minimum: 1
            maximum: 100
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  users:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
              examples:
                default:
                  value:
                    users:
                      - id: 1
                        name: "John Doe"
                        email: "john@example.com"
                      - id: 2
                        name: "Jane Smith"
                        email: "jane@example.com"
                    pagination:
                      page: 1
                      total: 100
                      pages: 5
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/ServerError'
      security:
        - BearerAuth: []

    post:
      summary: Create new user
      description: Creates a new user account
      operationId: createUser
      tags:
        - users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
            examples:
              default:
                value:
                  name: "John Doe"
                  email: "john@example.com"
                  password: "SecurePass123!"
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          description: User already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
          example: 1
        name:
          type: string
          example: "John Doe"
        email:
          type: string
          format: email
          example: "john@example.com"
        created_at:
          type: string
          format: date-time
      required:
        - id
        - name
        - email

    UserCreate:
      type: object
      properties:
        name:
          type: string
          minLength: 2
          maxLength: 100
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
          pattern: '^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
      required:
        - name
        - email
        - password

    Pagination:
      type: object
      properties:
        page:
          type: integer
        total:
          type: integer
        pages:
          type: integer

    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        details:
          type: object

  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error: "unauthorized"
            message: "Authentication token required"

    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    ServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT authentication token

security:
  - BearerAuth: []

tags:
  - name: users
    description: User management operations
  - name: auth
    description: Authentication endpoints
```

### 2. Postman Collection Generation

```json
{
  "info": {
    "name": "User Management API",
    "description": "Complete Postman collection for User API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{auth_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "https://api.example.com/v1"
    },
    {
      "key": "auth_token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"password123\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/auth/login",
              "host": ["{{base_url}}"],
              "path": ["auth", "login"]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "// Save token for subsequent requests",
                  "if (pm.response.code === 200) {",
                  "  const response = pm.response.json();",
                  "  pm.environment.set('auth_token', response.token);",
                  "}"
                ]
              }
            }
          ]
        }
      ]
    },
    {
      "name": "Users",
      "item": [
        {
          "name": "List Users",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/users?page=1&limit=20",
              "host": ["{{base_url}}"],
              "path": ["users"],
              "query": [
                {"key": "page", "value": "1"},
                {"key": "limit", "value": "20"}
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', () => {",
                  "  pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Response has users array', () => {",
                  "  const response = pm.response.json();",
                  "  pm.expect(response).to.have.property('users');",
                  "  pm.expect(response.users).to.be.an('array');",
                  "});"
                ]
              }
            }
          ]
        },
        {
          "name": "Get User",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/users/:id",
              "host": ["{{base_url}}"],
              "path": ["users", ":id"],
              "variable": [
                {"key": "id", "value": "1"}
              ]
            }
          }
        },
        {
          "name": "Create User",
          "request": {
            "method": "POST",
            "header": [
              {"key": "Content-Type", "value": "application/json"}
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"John Doe\",\n  \"email\": \"john@example.com\",\n  \"password\": \"SecurePass123!\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/users",
              "host": ["{{base_url}}"],
              "path": ["users"]
            }
          }
        }
      ]
    }
  ]
}
```

**Generate from OpenAPI:**
```bash
# Using openapi-to-postman
npx openapi-to-postman -s openapi.yaml -o postman-collection.json -p

# Or использу api-documentation skill:
# "Создай Postman collection из openapi.yaml с test scripts"
```

### 3. Markdown API Documentation

**Complete API Reference:**

```markdown
# User Management API Documentation

## Base URL
```
https://api.example.com/v1
```

## Authentication

All API requests require authentication via Bearer token:

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
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

---

## Endpoints

### Users

#### GET /users
List all users with pagination.

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (min: 1) |
| `limit` | integer | No | 20 | Items per page (min: 1, max: 100) |
| `sort` | string | No | `created_at` | Sort field |
| `order` | string | No | `desc` | Sort order (`asc` or `desc`) |

**Example Request:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.example.com/v1/users?page=1&limit=20"
```

**Success Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Server error

---

#### POST /users
Create a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "age": 30
}
```

**Field Validations:**
- `name`: String, 2-100 characters, required
- `email`: Valid email format, unique, required
- `password`: Minimum 8 characters, at least 1 letter and 1 number, required
- `age`: Integer, 13-120, optional

**Example Request:**
```bash
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Success Response (201 Created):**
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2025-11-03T14:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Validation failed
  ```json
  {
    "error": "validation_error",
    "message": "Invalid request data",
    "details": {
      "email": ["Email already exists"],
      "password": ["Password too weak"]
    }
  }
  ```
- `409 Conflict`: User with email already exists
- `401 Unauthorized`: Invalid authentication

---

## Error Handling

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

**Common Error Codes:**
- `unauthorized`: Authentication required or failed
- `forbidden`: Insufficient permissions
- `not_found`: Resource not found
- `validation_error`: Request validation failed
- `rate_limit_exceeded`: Too many requests
- `server_error`: Internal server error

---

## Rate Limiting

API requests are rate limited:
- **Authenticated**: 1000 requests/hour
- **Unauthenticated**: 100 requests/hour

**Rate limit headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1699027200
```

When exceeded:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded",
  "retry_after": 3600
}
```

---

## Webhooks

Subscribe to events:

```bash
POST /webhooks
{
  "url": "https://your-app.com/webhook",
  "events": ["user.created", "user.updated"]
}
```

**Webhook payload:**
```json
{
  "event": "user.created",
  "data": {
    "id": 123,
    "name": "John Doe"
  },
  "timestamp": "2025-11-03T14:30:00Z"
}
```

---

## SDK Examples

### JavaScript/TypeScript
```typescript
import { UserAPI } from '@example/api-client';

const api = new UserAPI({ token: 'YOUR_TOKEN' });

// List users
const users = await api.users.list({ page: 1, limit: 20 });

// Create user
const user = await api.users.create({
  name: 'John Doe',
  email: 'john@example.com',
  password: 'SecurePass123!'
});
```

### Python
```python
from example_api import UserAPI

api = UserAPI(token='YOUR_TOKEN')

# List users
users = api.users.list(page=1, limit=20)

# Create user
user = api.users.create(
    name='John Doe',
    email='john@example.com',
    password='SecurePass123!'
)
```

---

## Changelog

### v1.0.0 (2025-11-03)
- Initial API release
- User CRUD operations
- JWT authentication
```

### 4. Interactive Documentation

#### Swagger UI Setup
```python
# FastAPI (built-in)
app = FastAPI(docs_url="/docs")

# Flask
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/docs'
API_URL = '/static/openapi.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "My API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
```

#### ReDoc Setup
```html
<!DOCTYPE html>
<html>
<head>
  <title>API Documentation</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
  <style>
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <redoc spec-url='/openapi.json'></redoc>
  <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
</body>
</html>
```

## Usage Examples

**Generate OpenAPI from FastAPI app:**
```
"Используй api-documentation skill: создай OpenAPI spec из FastAPI app в src/api/main.py"
```

**Create Postman collection:**
```
"Используй api-documentation skill: генерируй Postman collection из openapi.yaml с test scripts для всех endpoints"
```

**Generate complete API docs:**
```
"Используй api-documentation skill: создай comprehensive API documentation:
- OpenAPI spec
- Postman collection
- Markdown reference
- SDK examples для Python и TypeScript"
```

**Update existing docs:**
```
"Используй api-documentation skill: обнови docs/API.md с новыми endpoints из src/api/users.py"
```

## Best Practices

1. **Include examples** для всех endpoints
2. **Document errors** с примерами error responses
3. **Provide SDK snippets** для популярных языков
4. **Keep OpenAPI spec** актуальным с кодом
5. **Use semantic versioning** для API versions
6. **Add rate limiting info** в docs
7. **Document authentication** clearly
8. **Include changelog** для API updates
9. **Test your examples** - убедись они работают
10. **Interactive docs** лучше static docs

## Tools Integration

- **OpenAPI validation**: `openapi-validator`
- **Postman**: Import/export collections
- **Swagger Editor**: Edit OpenAPI specs visually
- **ReDoc**: Beautiful API docs
- **Stoplight**: API design platform
