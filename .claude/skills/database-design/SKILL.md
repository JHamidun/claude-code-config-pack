---
name: database-design
description: Database schema design, migration planning, query optimization, and data modeling for SQL and NoSQL databases. Covers PostgreSQL, MongoDB, Redis, and includes normalization, indexing strategies, and performance tuning.
keywords: database, schema, migration, postgres, mongodb, redis, normalization, indexing, query-optimization
---

# Database Design & Optimization

## Purpose
Проектирование БД схем, планирование миграций, оптимизация запросов и data modeling для SQL и NoSQL баз данных.

## Capabilities

### 1. Schema Design

#### ER Diagram & Modeling

**User Management System Example:**

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│    users     │         │organizations │         │    roles     │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ id (PK)      │◄───┐    │ id (PK)      │    ┌───►│ id (PK)      │
│ email        │    │    │ name         │    │    │ name         │
│ name         │    │    │ created_at   │    │    │ permissions  │
│ password_hash│    │    └──────────────┘    │    └──────────────┘
│ created_at   │    │                        │
│ updated_at   │    │    ┌──────────────┐    │
└──────────────┘    └────┤ user_orgs    │────┘
                         ├──────────────┤
                         │ user_id (FK) │
                         │ org_id (FK)  │
                         │ role_id (FK) │
                         │ joined_at    │
                         └──────────────┘

Relations:
- users ←→ organizations (many-to-many через user_orgs)
- user_orgs → roles (many-to-one)
```

#### PostgreSQL Schema

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- for fuzzy search

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL  -- soft delete
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_uuid ON users(uuid);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_active ON users(id) WHERE deleted_at IS NULL;

-- Trigger для updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_settings ON organizations USING GIN (settings);

-- Roles table
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many junction table
CREATE TABLE user_organizations (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE RESTRICT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, org_id)
);

CREATE INDEX idx_user_orgs_user ON user_organizations(user_id);
CREATE INDEX idx_user_orgs_org ON user_organizations(org_id);
CREATE INDEX idx_user_orgs_role ON user_organizations(role_id);

-- Insert default roles
INSERT INTO roles (name, permissions) VALUES
    ('admin', '["users:read", "users:write", "users:delete", "orgs:write"]'),
    ('member', '["users:read", "orgs:read"]'),
    ('guest', '["orgs:read"]');
```

### 2. Normalization

#### Example: E-commerce Orders

**❌ Denormalized (1NF violation):**
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255),
    items TEXT,  -- "Product1:$10,Product2:$20"
    total DECIMAL(10,2)
);
```

**✅ Normalized (3NF):**
```sql
-- Users table (separate entity)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items (many-to-many)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,  -- snapshot price at order time
    subtotal DECIMAL(10,2) NOT NULL
);

-- Indexes
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
```

**Benefits of normalization:**
- ✅ No data duplication
- ✅ Easy to update product prices
- ✅ Maintain historical order prices
- ✅ Referential integrity

### 3. Indexing Strategy

#### Single Column Indexes
```sql
-- For exact matches and sorting
CREATE INDEX idx_users_email ON users(email);

-- For range queries
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Partial index (only index active records)
CREATE INDEX idx_active_users ON users(email) WHERE deleted_at IS NULL;
```

#### Composite Indexes
```sql
-- For multi-column WHERE clauses
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Query benefits:
-- ✅ WHERE user_id = 1 AND status = 'pending'
-- ✅ WHERE user_id = 1
-- ❌ WHERE status = 'pending' (only first column used)

-- Order matters! Put most selective column first
CREATE INDEX idx_orders_status_user ON orders(status, user_id);
-- Better if status is more selective than user_id
```

#### Full-Text Search Indexes
```sql
-- GIN index for full-text search
CREATE INDEX idx_products_name_fts ON products
    USING GIN (to_tsvector('english', name));

-- Query:
SELECT * FROM products
WHERE to_tsvector('english', name) @@ to_tsquery('english', 'laptop');

-- Fuzzy search with pg_trgm
CREATE INDEX idx_products_name_trgm ON products
    USING GIN (name gin_trgm_ops);

-- Query:
SELECT * FROM products WHERE name % 'laptop';  -- similarity search
```

#### JSONB Indexes
```sql
CREATE INDEX idx_users_settings ON users USING GIN (settings);

-- Query:
SELECT * FROM users WHERE settings @> '{"theme": "dark"}';
SELECT * FROM users WHERE settings ? 'notifications';
```

### 4. Migration Planning

#### Alembic (Python/SQLAlchemy)

**Generate migration:**
```bash
alembic revision --autogenerate -m "add users table"
```

**Migration file:**
```python
"""add users table

Revision ID: abc123
Revises:
Create Date: 2025-11-03 10:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create index
    op.create_index('idx_users_email', 'users', ['email'])

    # Insert seed data (if needed)
    op.execute("""
        INSERT INTO users (email, name) VALUES
        ('admin@example.com', 'Admin User')
    """)

def downgrade():
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

**Safe migrations for production:**
```python
def upgrade():
    # 1. Add column as nullable first
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))

    # 2. Backfill data
    op.execute("UPDATE users SET age = 0 WHERE age IS NULL")

    # 3. Make NOT NULL
    op.alter_column('users', 'age', nullable=False)
```

#### Django Migrations

```python
# python manage.py makemigrations

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # Add field
        migrations.AddField(
            model_name='user',
            name='age',
            field=models.IntegerField(null=True, blank=True),
        ),

        # Data migration
        migrations.RunPython(backfill_user_ages),

        # Create index
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='idx_users_email'),
        ),
    ]

def backfill_user_ages(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(age__isnull=True).update(age=0)
```

#### Prisma Migrations

```prisma
// schema.prisma
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String
  age       Int?
  createdAt DateTime @default(now())

  @@index([email])
}
```

```bash
# Generate and apply migration
npx prisma migrate dev --name add_age_to_users

# Deploy to production
npx prisma migrate deploy
```

### 5. Query Optimization

#### EXPLAIN ANALYZE

```sql
-- Before optimization
EXPLAIN ANALYZE
SELECT u.*, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.email = 'john@example.com';

/*
Seq Scan on users  (cost=0.00..1500.00 rows=1 width=100) (actual time=50.123..50.456 rows=1 loops=1)
  Filter: (email = 'john@example.com')
  Rows Removed by Filter: 99999
*/

-- Add index
CREATE INDEX idx_users_email ON users(email);

-- After optimization
EXPLAIN ANALYZE
SELECT u.*, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.email = 'john@example.com';

/*
Index Scan using idx_users_email on users  (cost=0.42..8.44 rows=1 width=100) (actual time=0.015..0.017 rows=1 loops=1)
  Index Cond: (email = 'john@example.com')
*/
```

#### N+1 Query Problem

**❌ Bad (N+1 queries):**
```python
# Gets all users (1 query)
users = User.query.all()

# For each user, gets orders (N queries)
for user in users:
    print(user.orders)  # Additional query for EACH user!
```

**✅ Good (2 queries with eager loading):**
```python
# SQLAlchemy
users = User.query.options(joinedload(User.orders)).all()

# Django ORM
users = User.objects.prefetch_related('orders').all()

# Prisma
users = await prisma.user.find_many(include={'orders': True})
```

#### Pagination Optimization

**❌ Bad (OFFSET becomes slow for large offsets):**
```sql
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 100000;  -- Scans and skips 100k rows!
```

**✅ Good (Cursor-based pagination):**
```sql
-- First page
SELECT * FROM users
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Next page (using last item's cursor)
SELECT * FROM users
WHERE (created_at, id) < ('2025-11-03 10:00:00', 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### 6. MongoDB Schema Design

#### Document Embedding vs Referencing

**Embedded (for 1-to-few, rarely changing):**
```javascript
// User with embedded addresses
{
  _id: ObjectId("..."),
  name: "John Doe",
  email: "john@example.com",
  addresses: [
    {
      type: "home",
      street: "123 Main St",
      city: "New York",
      zip: "10001"
    },
    {
      type: "work",
      street: "456 Office Blvd",
      city: "New York",
      zip: "10002"
    }
  ]
}
```

**Referenced (for 1-to-many, frequently changing):**
```javascript
// User
{
  _id: ObjectId("user1"),
  name: "John Doe",
  email: "john@example.com"
}

// Orders (separate collection)
{
  _id: ObjectId("order1"),
  user_id: ObjectId("user1"),  // Reference
  items: [...],
  total: 100.50,
  created_at: ISODate("2025-11-03")
}
```

#### Indexes in MongoDB

```javascript
// Create indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ "addresses.city": 1 });
db.users.createIndex({ created_at: -1 });

// Compound index
db.orders.createIndex({ user_id: 1, status: 1 });

// Text index for search
db.products.createIndex({ name: "text", description: "text" });

// Query with text search
db.products.find({ $text: { $search: "laptop" } });

// Explain query
db.users.find({ email: "john@example.com" }).explain("executionStats");
```

### 7. Caching Strategy (Redis)

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache(ttl=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Cache miss - call function
            result = func(*args, **kwargs)

            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator

@cache(ttl=300)
def get_user_profile(user_id):
    return User.query.get(user_id)
```

**Cache invalidation:**
```python
def update_user(user_id, data):
    # Update database
    user = User.query.get(user_id)
    user.update(data)
    db.session.commit()

    # Invalidate cache
    cache_key = f"get_user_profile:({user_id},):dict()"
    redis_client.delete(cache_key)
```

### 8. Sharding & Partitioning

#### PostgreSQL Table Partitioning

```sql
-- Partitioned table by date range
CREATE TABLE orders (
    id SERIAL,
    user_id INTEGER,
    total DECIMAL(10,2),
    created_at DATE NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE orders_2025_q1 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE orders_2025_q2 PARTITION OF orders
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

-- Queries automatically use correct partition
SELECT * FROM orders WHERE created_at >= '2025-01-01' AND created_at < '2025-02-01';
```

## Usage Examples

**Design database schema:**
```
"Используй database-design skill: спроектируй schema для multi-tenant SaaS:
- users, organizations, subscriptions
- Role-based access control
- Audit logs"
```

**Optimize slow query:**
```
"Используй database-design skill: оптимизируй этот query:
SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 100"
```

**Plan migration:**
```
"Используй database-design skill: создай Alembic migration для:
- Add soft-delete (deleted_at) к User model
- Migrate existing data
- Create index на active users"
```

**Fix N+1 problem:**
```
"Используй database-design skill: найди и исправь N+1 queries в src/api/users.py"
```

## Best Practices

1. **Always add indexes** на foreign keys
2. **Use UUIDs** for public IDs (не expose auto-increment IDs)
3. **Soft delete** вместо hard delete (добавь `deleted_at`)
4. **Timestamp everything** (`created_at`, `updated_at`)
5. **Plan for scale**: partitioning, sharding
6. **Use transactions** для multi-table updates
7. **Cache expensive queries** (Redis)
8. **Monitor slow queries** (pg_stat_statements)
9. **Regular VACUUM** в PostgreSQL
10. **Backup strategy** (daily + WAL archiving)

## Tools

- **PostgreSQL**: pgAdmin, DBeaver
- **MongoDB**: MongoDB Compass
- **Redis**: RedisInsight
- **Migrations**: Alembic, Prisma, Django
- **Monitoring**: pg_stat_statements, MongoDB Profiler
- **Schema visualization**: dbdiagram.io, DrawSQL
