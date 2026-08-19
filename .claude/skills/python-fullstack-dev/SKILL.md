---
name: python-fullstack-dev
description: "Python development: Django, FastAPI, Flask, data science, testing, deployment. Triggers: «write in python», «fix python code»."
---

# Python Full-Stack Development Expert

Complete Python development expertise covering Django, FastAPI, Flask, data science, testing, and deployment.

## When to Use This Skill

Use this skill when:
- Building Python web applications (Django, FastAPI, Flask)
- Designing REST APIs or GraphQL endpoints
- Working with databases and ORMs (SQLAlchemy, Django ORM)
- Implementing async/await patterns
- Setting up testing infrastructure
- Debugging Python applications
- Optimizing performance
- Deploying Python services

## Project Setup & Virtual Environments

### Modern Project Structure
```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── api/
│       ├── models/
│       ├── services/
│       └── utils/
├── tests/
├── docs/
├── .env.example
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

### Virtual Environment Best Practices
```bash
# Use venv (built-in)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Or use Poetry (recommended for modern projects)
poetry init
poetry add fastapi uvicorn
poetry add --group dev pytest black ruff

# Or use uv (fastest package installer)
pip install uv
uv venv
uv pip install -r requirements.txt
```

### pyproject.toml Configuration
```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
```

## Django: Complete Guide

### Models Best Practices

```python
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid

class TimeStampedModel(models.Model):
    """Abstract base class with created/modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractUser):
    """Custom user model with UUID primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Product(TimeStampedModel):
    """Product model with advanced features"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Order(TimeStampedModel):
    """Order with state machine pattern"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        SHIPPED = 'shipped', _('Shipped')
        DELIVERED = 'delivered', _('Delivered')
        CANCELLED = 'cancelled', _('Cancelled')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def can_transition_to(self, new_status):
        """Validate status transitions"""
        transitions = {
            self.Status.PENDING: [self.Status.PROCESSING, self.Status.CANCELLED],
            self.Status.PROCESSING: [self.Status.SHIPPED, self.Status.CANCELLED],
            self.Status.SHIPPED: [self.Status.DELIVERED],
        }
        return new_status in transitions.get(self.status, [])
```

### Django REST Framework Serializers

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Product, Order

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """User serializer with computed fields"""
    full_name = serializers.SerializerMethodField()
    orders_count = serializers.IntegerField(source='orders.count', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'avatar', 'bio', 'orders_count']
        read_only_fields = ['id', 'orders_count']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class ProductSerializer(serializers.ModelSerializer):
    """Product serializer with validation"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']

    def get_in_stock(self, obj):
        return obj.stock > 0

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        if attrs.get('stock', 0) > 0 and not attrs.get('is_active', True):
            raise serializers.ValidationError(
                "Cannot deactivate product with stock"
            )
        return attrs

class OrderItemSerializer(serializers.Serializer):
    """Nested order item"""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

class OrderCreateSerializer(serializers.ModelSerializer):
    """Order creation with nested items"""
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        # Calculate total and create order
        total = sum(
            item['quantity'] * Product.objects.get(id=item['product_id']).price
            for item in items_data
        )

        order = Order.objects.create(user=user, total=total)

        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price
            )

        return order
```

### Django Views (Class-Based & Function-Based)

```python
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """Product CRUD with filtering and search"""
    queryset = Product.objects.select_related('category').filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular products"""
        products = self.get_queryset().annotate(
            orders_count=Count('orderitem')
        ).order_by('-orders_count')[:10]

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle product active status"""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        return Response({'status': 'active' if product.is_active else 'inactive'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Create order from cart"""
    serializer = OrderCreateSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        order = serializer.save()
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Django Signals

```python
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Order, Product

@receiver(post_save, sender=Order)
def order_created_notification(sender, instance, created, **kwargs):
    """Send email when order is created"""
    if created:
        send_mail(
            subject=f'Order {instance.id} Created',
            message=f'Your order has been created. Total: ${instance.total}',
            from_email='noreply@example.com',
            recipient_list=[instance.user.email],
            fail_silently=True,
        )

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    """Track order status changes"""
    if instance.pk:
        old_instance = Order.objects.filter(pk=instance.pk).first()
        if old_instance and old_instance.status != instance.status:
            # Log status change
            print(f"Order {instance.id} status: {old_instance.status} -> {instance.status}")

@receiver(pre_delete, sender=Product)
def product_deleted_cleanup(sender, instance, **kwargs):
    """Cleanup when product is deleted"""
    # Delete associated images
    if instance.avatar:
        instance.avatar.delete(save=False)
```

## FastAPI: Async Patterns

### FastAPI Application Structure

```python
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import asyncio

app = FastAPI(
    title="My API",
    description="FastAPI Application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50)

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True  # Pydantic v2 (orm_mode in v1)

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: Optional[str] = None

    class Config:
        from_attributes = True

# Dependency Injection
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract and validate user from JWT token"""
    token = credentials.credentials
    # Validate token (simplified)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"id": 1, "email": "user@example.com"}

async def get_db():
    """Database session dependency"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from .database import async_session

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI"}

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@app.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List products with pagination and search"""
    from sqlalchemy import select
    from .models import Product

    query = select(Product)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()

    return products

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new product"""
    from .models import Product

    db_product = Product(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    # Background task
    background_tasks.add_task(send_notification, db_product.id)

    return db_product

async def send_notification(product_id: int):
    """Background task to send notification"""
    await asyncio.sleep(2)
    print(f"Notification sent for product {product_id}")

# WebSocket endpoint
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### SQLAlchemy 2.0 Async Patterns

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, select, func
from typing import Optional, List
from datetime import datetime

# Database setup
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=10,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

# Models with SQLAlchemy 2.0 syntax
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50))
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    orders: Mapped[List["Order"]] = relationship(back_populates="user")

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    price: Mapped[float]
    stock: Mapped[int] = mapped_column(default=0)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    category: Mapped[Optional["Category"]] = relationship()

# Repository pattern
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_active_users_count(self) -> int:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        return result.scalar()
```

## Testing with Pytest

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Product

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(test_db):
    """Create test client"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test user creation"""
    response = await client.post(
        "/users",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data

@pytest.mark.asyncio
async def test_get_products(client: AsyncClient, test_db: AsyncSession):
    """Test getting products"""
    # Create test products
    products = [
        Product(name=f"Product {i}", price=10.0 * i, stock=10)
        for i in range(5)
    ]
    test_db.add_all(products)
    await test_db.commit()

    response = await client.get("/products")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

# Fixtures
@pytest.fixture
def mock_user():
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True
    }

# Parametrized tests
@pytest.mark.parametrize("price,expected", [
    (10.0, True),
    (0.0, False),
    (-5.0, False),
])
def test_validate_price(price, expected):
    from app.validators import is_valid_price
    assert is_valid_price(price) == expected
```

## Common Bugs and Solutions

### 1. N+1 Query Problem
```python
# BAD: N+1 queries
products = Product.objects.all()
for product in products:
    print(product.category.name)  # Separate query for each product

# GOOD: Use select_related
products = Product.objects.select_related('category').all()
for product in products:
    print(product.category.name)  # Single query

# GOOD: Use prefetch_related for many-to-many
users = User.objects.prefetch_related('orders__items').all()
```

### 2. Race Conditions
```python
# BAD: Race condition
product = Product.objects.get(id=1)
if product.stock > 0:
    product.stock -= 1  # Another request might have reduced stock
    product.save()

# GOOD: Use F expressions
from django.db.models import F
Product.objects.filter(id=1, stock__gt=0).update(stock=F('stock') - 1)

# GOOD: Use select_for_update
with transaction.atomic():
    product = Product.objects.select_for_update().get(id=1)
    if product.stock > 0:
        product.stock -= 1
        product.save()
```

### 3. Memory Leaks with QuerySets
```python
# BAD: Loads all objects into memory
all_users = list(User.objects.all())  # Memory leak with millions of users

# GOOD: Use iterator()
for user in User.objects.iterator(chunk_size=1000):
    process_user(user)

# GOOD: Use pagination
from django.core.paginator import Paginator
paginator = Paginator(User.objects.all(), 100)
for page_num in paginator.page_range:
    page = paginator.page(page_num)
    for user in page.object_list:
        process_user(user)
```

## Performance Optimization

### Database Indexing
```python
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)  # Single index

    class Meta:
        indexes = [
            models.Index(fields=['name', 'is_active']),  # Composite index
            models.Index(fields=['-created_at']),  # Descending index
        ]
```

### Caching Strategies
```python
from django.core.cache import cache
from functools import wraps

def cache_result(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(cache_key)

            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)

            return result
        return wrapper
    return decorator

@cache_result(timeout=600)
def get_popular_products():
    return Product.objects.annotate(
        orders_count=Count('orderitem')
    ).order_by('-orders_count')[:10]
```

## Deployment

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./:/app
    command: uvicorn app.main:app --host 0.0.0.0 --reload

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

This skill provides comprehensive Python development expertise with production-ready patterns and solutions.