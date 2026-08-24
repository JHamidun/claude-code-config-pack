# Шаблоны: OpenAPI 3.0.3 и Postman v2.1

Читать, когда пишешь спеку или коллекцию с нуля и нужен полный скелет со всеми
секциями сразу — `components/schemas`, переиспользуемые `responses`,
`securitySchemes`, примеры в ответах. Для правки уже существующего файла шаблон
не нужен.

## OpenAPI: полный скелет

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
      required: [id, name, email]

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
      required: [name, email, password]

    Pagination:
      type: object
      properties:
        page:    { type: integer }
        total:   { type: integer }
        pages:   { type: integer }

    Error:
      type: object
      properties:
        error:   { type: string }
        message: { type: string }
        details: { type: object }

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

## Postman: коллекция с авто-подстановкой токена

Ключевая часть — не структура запросов (её сгенерит `openapi-to-postman`), а
`event`-скрипты: login кладёт токен в environment, остальные запросы берут его из
`{{auth_token}}`. Без этого коллекцию нельзя прогнать целиком одним Runner'ом.

```json
{
  "info": {
    "name": "User Management API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [{ "key": "token", "value": "{{auth_token}}", "type": "string" }]
  },
  "variable": [
    { "key": "base_url", "value": "https://api.example.com/v1" },
    { "key": "auth_token", "value": "" }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [{ "key": "Content-Type", "value": "application/json" }],
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
                  "if (pm.response.code === 200) {",
                  "  pm.environment.set('auth_token', pm.response.json().token);",
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
            "url": {
              "raw": "{{base_url}}/users?page=1&limit=20",
              "host": ["{{base_url}}"],
              "path": ["users"],
              "query": [
                { "key": "page", "value": "1" },
                { "key": "limit", "value": "20" }
              ]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', () => pm.response.to.have.status(200));",
                  "pm.test('Response has users array', () => {",
                  "  pm.expect(pm.response.json().users).to.be.an('array');",
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
            "url": {
              "raw": "{{base_url}}/users/:id",
              "host": ["{{base_url}}"],
              "path": ["users", ":id"],
              "variable": [{ "key": "id", "value": "1" }]
            }
          }
        }
      ]
    }
  ]
}
```
