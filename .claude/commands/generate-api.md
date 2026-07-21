---
description: Генерация полного CRUD API для ресурса
argument-hint: "[framework] [resource-name]"
---

# 🔌 Generate API: $ARGUMENTS

Генерирую полный CRUD API с best practices!

## Supported Frameworks:

- **fastapi** - FastAPI (Python async)
- **django-rest** - Django REST Framework
- **express** - Express.js (Node.js)
- **nest** - Nest.js (TypeScript)
- **gin** - Gin (Go)
- **actix** - Actix-web (Rust)
- **spring** - Spring Boot (Java)
- **laravel** - Laravel (PHP)
- **rails** - Rails API (Ruby)

## Process:

### 1. Parse Arguments
```bash
FRAMEWORK=$(echo "$ARGUMENTS" | awk '{print $1}')
RESOURCE=$(echo "$ARGUMENTS" | awk '{print $2}')
RESOURCE_PLURAL="${RESOURCE}s"
RESOURCE_UPPER=$(echo "$RESOURCE" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
```

### 2. Generate Model/Entity

**FastAPI Example:**
```python
# app/models/${RESOURCE}.py
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime

class ${RESOURCE_UPPER}(Base):
    __tablename__ = "${RESOURCE_PLURAL}"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Express/TypeScript Example:**
```typescript
// src/models/${RESOURCE}.model.ts
import { Schema, model, Document } from 'mongoose';

export interface I${RESOURCE_UPPER} extends Document {
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
}

const ${RESOURCE}Schema = new Schema({
  name: { type: String, required: true, index: true },
  description: { type: String },
}, { timestamps: true });

export default model<I${RESOURCE_UPPER}>('${RESOURCE_UPPER}', ${RESOURCE}Schema);
```

### 3. Generate Schema/DTO

**FastAPI Pydantic:**
```python
# app/schemas/${RESOURCE}.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ${RESOURCE_UPPER}Base(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ${RESOURCE_UPPER}Create(${RESOURCE_UPPER}Base):
    pass

class ${RESOURCE_UPPER}Update(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ${RESOURCE_UPPER}Response(${RESOURCE_UPPER}Base):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**NestJS DTO:**
```typescript
// src/${RESOURCE_PLURAL}/dto/create-${RESOURCE}.dto.ts
import { IsString, IsOptional, MinLength, MaxLength } from 'class-validator';

export class Create${RESOURCE_UPPER}Dto {
  @IsString()
  @MinLength(1)
  @MaxLength(100)
  name: string;

  @IsString()
  @IsOptional()
  @MaxLength(500)
  description?: string;
}

export class Update${RESOURCE_UPPER}Dto {
  @IsString()
  @IsOptional()
  @MinLength(1)
  @MaxLength(100)
  name?: string;

  @IsString()
  @IsOptional()
  @MaxLength(500)
  description?: string;
}
```

### 4. Generate CRUD Service

**FastAPI:**
```python
# app/services/${RESOURCE}.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.${RESOURCE} import ${RESOURCE_UPPER}
from app.schemas.${RESOURCE} import ${RESOURCE_UPPER}Create, ${RESOURCE_UPPER}Update
from typing import Optional

class ${RESOURCE_UPPER}Service:
    @staticmethod
    async def get_all(db: Session, skip: int = 0, limit: int = 100):
        stmt = select(${RESOURCE_UPPER}).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: Session, id: int) -> Optional[${RESOURCE_UPPER}]:
        return await db.get(${RESOURCE_UPPER}, id)

    @staticmethod
    async def create(db: Session, data: ${RESOURCE_UPPER}Create) -> ${RESOURCE_UPPER}:
        obj = ${RESOURCE_UPPER}(**data.dict())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def update(db: Session, id: int, data: ${RESOURCE_UPPER}Update) -> Optional[${RESOURCE_UPPER}]:
        obj = await db.get(${RESOURCE_UPPER}, id)
        if not obj:
            return None
        for key, value in data.dict(exclude_unset=True).items():
            setattr(obj, key, value)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete(db: Session, id: int) -> bool:
        obj = await db.get(${RESOURCE_UPPER}, id)
        if not obj:
            return False
        await db.delete(obj)
        await db.commit()
        return True
```

### 5. Generate Router/Controller

**FastAPI Router:**
```python
# app/routers/${RESOURCE}.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.${RESOURCE} import ${RESOURCE_UPPER}Create, ${RESOURCE_UPPER}Update, ${RESOURCE_UPPER}Response
from app.services.${RESOURCE} import ${RESOURCE_UPPER}Service

router = APIRouter(
    prefix="/${RESOURCE_PLURAL}",
    tags=["${RESOURCE_PLURAL}"]
)

@router.get("/", response_model=List[${RESOURCE_UPPER}Response])
async def list_${RESOURCE_PLURAL}(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all ${RESOURCE_PLURAL} with pagination"""
    return await ${RESOURCE_UPPER}Service.get_all(db, skip, limit)

@router.get("/{id}", response_model=${RESOURCE_UPPER}Response)
async def get_${RESOURCE}(id: int, db: Session = Depends(get_db)):
    """Get a single ${RESOURCE} by ID"""
    obj = await ${RESOURCE_UPPER}Service.get_by_id(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="${RESOURCE_UPPER} not found")
    return obj

@router.post("/", response_model=${RESOURCE_UPPER}Response, status_code=status.HTTP_201_CREATED)
async def create_${RESOURCE}(data: ${RESOURCE_UPPER}Create, db: Session = Depends(get_db)):
    """Create a new ${RESOURCE}"""
    return await ${RESOURCE_UPPER}Service.create(db, data)

@router.put("/{id}", response_model=${RESOURCE_UPPER}Response)
async def update_${RESOURCE}(id: int, data: ${RESOURCE_UPPER}Update, db: Session = Depends(get_db)):
    """Update a ${RESOURCE} by ID"""
    obj = await ${RESOURCE_UPPER}Service.update(db, id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="${RESOURCE_UPPER} not found")
    return obj

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_${RESOURCE}(id: int, db: Session = Depends(get_db)):
    """Delete a ${RESOURCE} by ID"""
    success = await ${RESOURCE_UPPER}Service.delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="${RESOURCE_UPPER} not found")
```

**Express Controller:**
```typescript
// src/controllers/${RESOURCE}.controller.ts
import { Request, Response } from 'express';
import ${RESOURCE_UPPER}Model from '../models/${RESOURCE}.model';

export class ${RESOURCE_UPPER}Controller {
  static async getAll(req: Request, res: Response) {
    try {
      const { page = 1, limit = 10 } = req.query;
      const skip = (Number(page) - 1) * Number(limit);

      const [items, total] = await Promise.all([
        ${RESOURCE_UPPER}Model.find().skip(skip).limit(Number(limit)),
        ${RESOURCE_UPPER}Model.countDocuments()
      ]);

      res.json({
        data: items,
        meta: {
          total,
          page: Number(page),
          limit: Number(limit),
          pages: Math.ceil(total / Number(limit))
        }
      });
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  }

  static async getById(req: Request, res: Response) {
    try {
      const item = await ${RESOURCE_UPPER}Model.findById(req.params.id);
      if (!item) {
        return res.status(404).json({ error: '${RESOURCE_UPPER} not found' });
      }
      res.json(item);
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  }

  static async create(req: Request, res: Response) {
    try {
      const item = new ${RESOURCE_UPPER}Model(req.body);
      await item.save();
      res.status(201).json(item);
    } catch (error) {
      res.status(400).json({ error: 'Bad request' });
    }
  }

  static async update(req: Request, res: Response) {
    try {
      const item = await ${RESOURCE_UPPER}Model.findByIdAndUpdate(
        req.params.id,
        req.body,
        { new: true, runValidators: true }
      );
      if (!item) {
        return res.status(404).json({ error: '${RESOURCE_UPPER} not found' });
      }
      res.json(item);
    } catch (error) {
      res.status(400).json({ error: 'Bad request' });
    }
  }

  static async delete(req: Request, res: Response) {
    try {
      const item = await ${RESOURCE_UPPER}Model.findByIdAndDelete(req.params.id);
      if (!item) {
        return res.status(404).json({ error: '${RESOURCE_UPPER} not found' });
      }
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
}
```

### 6. Generate Routes

**Express Routes:**
```typescript
// src/routes/${RESOURCE}.routes.ts
import { Router } from 'express';
import { ${RESOURCE_UPPER}Controller } from '../controllers/${RESOURCE}.controller';
import { validate } from '../middleware/validate';
import { ${RESOURCE}ValidationSchema } from '../validation/${RESOURCE}.validation';

const router = Router();

router.get('/', ${RESOURCE_UPPER}Controller.getAll);
router.get('/:id', ${RESOURCE_UPPER}Controller.getById);
router.post('/', validate(${RESOURCE}ValidationSchema.create), ${RESOURCE_UPPER}Controller.create);
router.put('/:id', validate(${RESOURCE}ValidationSchema.update), ${RESOURCE_UPPER}Controller.update);
router.delete('/:id', ${RESOURCE_UPPER}Controller.delete);

export default router;
```

### 7. Generate Tests

**FastAPI Tests:**
```python
# app/tests/test_${RESOURCE}.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_${RESOURCE}():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/${RESOURCE_PLURAL}/", json={
            "name": "Test ${RESOURCE_UPPER}",
            "description": "Test description"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test ${RESOURCE_UPPER}"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_${RESOURCE_PLURAL}():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/${RESOURCE_PLURAL}/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_${RESOURCE}():
    # Create a ${RESOURCE} first
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/${RESOURCE_PLURAL}/", json={
            "name": "Test"
        })
        id = create_response.json()["id"]

        # Get the ${RESOURCE}
        response = await client.get(f"/${RESOURCE_PLURAL}/{id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == id

@pytest.mark.asyncio
async def test_update_${RESOURCE}():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/${RESOURCE_PLURAL}/", json={
            "name": "Test"
        })
        id = create_response.json()["id"]

        response = await client.put(f"/${RESOURCE_PLURAL}/{id}", json={
            "name": "Updated Name"
        })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

@pytest.mark.asyncio
async def test_delete_${RESOURCE}():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/${RESOURCE_PLURAL}/", json={
            "name": "Test"
        })
        id = create_response.json()["id"]

        response = await client.delete(f"/${RESOURCE_PLURAL}/{id}")
    assert response.status_code == 204
```

### 8. Update API Documentation

**Register Router in main app:**
```python
# app/main.py
from app.routers import ${RESOURCE}

app.include_router(${RESOURCE}.router)
```

### 9. Create Migration (if applicable)

**Alembic Migration:**
```python
# alembic/versions/xxx_create_${RESOURCE_PLURAL}_table.py
"""create ${RESOURCE_PLURAL} table

Revision ID: xxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        '${RESOURCE_PLURAL}',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_${RESOURCE_PLURAL}_name', '${RESOURCE_PLURAL}', ['name'])

def downgrade():
    op.drop_index('ix_${RESOURCE_PLURAL}_name')
    op.drop_table('${RESOURCE_PLURAL}')
```

## Output:

```bash
✅ API generated for resource: ${RESOURCE}

Created files:
📄 models/${RESOURCE}.py
📄 schemas/${RESOURCE}.py
📄 services/${RESOURCE}.py
📄 routers/${RESOURCE}.py
📄 tests/test_${RESOURCE}.py
📄 migrations/xxx_create_${RESOURCE_PLURAL}.py

API Endpoints:
GET    /${RESOURCE_PLURAL}      - List all
GET    /${RESOURCE_PLURAL}/{id} - Get one
POST   /${RESOURCE_PLURAL}      - Create
PUT    /${RESOURCE_PLURAL}/{id} - Update
DELETE /${RESOURCE_PLURAL}/{id} - Delete

Next steps:
1. Run migrations: alembic upgrade head
2. Test API: pytest tests/test_${RESOURCE}.py
3. Check docs: http://localhost:8000/docs
```

## Examples:

```bash
/generate-api fastapi users
/generate-api express products
/generate-api nest orders
/generate-api django posts
```

**API ready! 🚀**