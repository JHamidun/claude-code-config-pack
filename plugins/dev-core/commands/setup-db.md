---
description: Настройка database integration для любого фреймворка
argument-hint: "[database] (postgresql|mysql|mongodb|redis|sqlite) [framework] (fastapi|django|express|nestjs|go)"
---

# 🗄️ Setup Database: $ARGUMENTS

Настраиваю интеграцию базы данных с best practices!

## Supported Databases:

- **postgresql** - PostgreSQL (recommended for production)
- **mysql** - MySQL/MariaDB
- **mongodb** - MongoDB (NoSQL)
- **redis** - Redis (cache/queue)
- **sqlite** - SQLite (dev/testing)

## Supported Frameworks:

- **fastapi** - FastAPI + SQLAlchemy
- **django** - Django ORM
- **express** - Express + Mongoose/TypeORM/Prisma
- **nestjs** - NestJS + TypeORM/Prisma
- **go** - Go + GORM

---

## Process:

### 1. PostgreSQL Setup

#### FastAPI + SQLAlchemy

**Database Configuration:**
```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/dbname"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False,          # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Async Support (asyncpg):**
```python
# app/database_async.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/dbname"
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**Models Example:**
```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="posts")
```

**Alembic Migrations:**
```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic
```

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add your app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import user, post  # Import all models

config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

```bash
# Create migration
alembic revision --autogenerate -m "Create users and posts tables"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Seeds/Fixtures:**
```python
# scripts/seed.py
from app.database import SessionLocal, engine, Base
from app.models.user import User, Post
from app.auth.jwt import get_password_hash

def seed_database():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(User).first():
            print("Database already seeded")
            return

        # Create users
        users = [
            User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True
            ),
            User(
                email="user@example.com",
                username="user",
                hashed_password=get_password_hash("user123"),
                is_active=True
            ),
        ]

        db.add_all(users)
        db.commit()

        # Create posts
        posts = [
            Post(
                title="First Post",
                content="This is the first post",
                author_id=users[0].id
            ),
            Post(
                title="Second Post",
                content="This is the second post",
                author_id=users[1].id
            ),
        ]

        db.add_all(posts)
        db.commit()

        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
```

#### Django ORM

**Settings Configuration:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'mydb'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Connection pooling with django-db-geventpool
DATABASES['default']['ENGINE'] = 'django_db_geventpool.backends.postgresql_psycopg2'
DATABASES['default']['CONN_MAX_AGE'] = 0
DATABASES['default']['OPTIONS'] = {
    'MAX_CONNS': 20,
    'REUSE_CONNS': True
}
```

**Models:**
```python
# myapp/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]
```

**Migrations:**
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create custom migration
python manage.py makemigrations --empty myapp --name custom_migration
```

**Fixtures:**
```python
# myapp/fixtures/initial_data.json
[
  {
    "model": "myapp.user",
    "pk": 1,
    "fields": {
      "username": "admin",
      "email": "admin@example.com",
      "is_staff": true,
      "is_superuser": true
    }
  },
  {
    "model": "myapp.post",
    "pk": 1,
    "fields": {
      "title": "First Post",
      "content": "Content here",
      "author": 1
    }
  }
]
```

```bash
# Load fixtures
python manage.py loaddata initial_data

# Dump data
python manage.py dumpdata myapp --indent 2 > myapp/fixtures/data.json
```

#### Express + TypeORM (PostgreSQL)

**Database Configuration:**
```typescript
// src/config/database.ts
import { DataSource } from 'typeorm';
import { User } from '../entities/User';
import { Post } from '../entities/Post';

export const AppDataSource = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
  database: process.env.DB_NAME || 'mydb',
  synchronize: false, // Never true in production
  logging: process.env.NODE_ENV === 'development',
  entities: [User, Post],
  migrations: ['src/migrations/**/*.ts'],
  subscribers: [],
  extra: {
    max: 10, // Connection pool size
    min: 2,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  }
});

export const initDatabase = async () => {
  try {
    await AppDataSource.initialize();
    console.log('✅ Database connected');
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    process.exit(1);
  }
};
```

**Entities:**
```typescript
// src/entities/User.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
  Index
} from 'typeorm';
import { Post } from './Post';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  @Index()
  email: string;

  @Column({ unique: true })
  @Index()
  username: string;

  @Column()
  password: string;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @OneToMany(() => Post, post => post.author)
  posts: Post[];
}
```

```typescript
// src/entities/Post.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index
} from 'typeorm';
import { User } from './User';

@Entity('posts')
@Index(['createdAt'])
export class Post {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  title: string;

  @Column('text')
  content: string;

  @ManyToOne(() => User, user => user.posts)
  @JoinColumn({ name: 'author_id' })
  author: User;

  @Column({ name: 'author_id' })
  @Index()
  authorId: number;

  @CreateDateColumn()
  createdAt: Date;
}
```

**Migrations:**
```typescript
// package.json scripts
{
  "scripts": {
    "typeorm": "typeorm-ts-node-commonjs",
    "migration:generate": "npm run typeorm migration:generate -- -d src/config/database.ts",
    "migration:run": "npm run typeorm migration:run -- -d src/config/database.ts",
    "migration:revert": "npm run typeorm migration:revert -- -d src/config/database.ts"
  }
}
```

```bash
# Generate migration
npm run migration:generate src/migrations/CreateUserAndPost

# Run migrations
npm run migration:run

# Revert last migration
npm run migration:revert
```

**Seeds:**
```typescript
// src/seeds/seed.ts
import { AppDataSource } from '../config/database';
import { User } from '../entities/User';
import { Post } from '../entities/Post';
import bcrypt from 'bcrypt';

export async function seed() {
  await AppDataSource.initialize();

  const userRepo = AppDataSource.getRepository(User);
  const postRepo = AppDataSource.getRepository(Post);

  // Check if already seeded
  const count = await userRepo.count();
  if (count > 0) {
    console.log('Database already seeded');
    return;
  }

  // Create users
  const admin = userRepo.create({
    email: 'admin@example.com',
    username: 'admin',
    password: await bcrypt.hash('admin123', 10),
    isActive: true,
  });

  const user = userRepo.create({
    email: 'user@example.com',
    username: 'user',
    password: await bcrypt.hash('user123', 10),
    isActive: true,
  });

  await userRepo.save([admin, user]);

  // Create posts
  const posts = [
    postRepo.create({
      title: 'First Post',
      content: 'This is the first post',
      author: admin,
    }),
    postRepo.create({
      title: 'Second Post',
      content: 'This is the second post',
      author: user,
    }),
  ];

  await postRepo.save(posts);

  console.log('✅ Database seeded successfully');
  await AppDataSource.destroy();
}

seed().catch(console.error);
```

#### Express + Prisma (PostgreSQL)

**Prisma Setup:**
```bash
npm install prisma @prisma/client
npx prisma init
```

**Schema:**
```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  username  String   @unique
  password  String
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  posts     Post[]

  @@index([email])
  @@index([username])
  @@map("users")
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String
  authorId  Int
  author    User     @relation(fields: [authorId], references: [id])
  createdAt DateTime @default(now())

  @@index([createdAt(sort: Desc)])
  @@index([authorId])
  @@map("posts")
}
```

**Client Configuration:**
```typescript
// src/config/prisma.ts
import { PrismaClient } from '@prisma/client';

const prismaClientSingleton = () => {
  return new PrismaClient({
    log: process.env.NODE_ENV === 'development'
      ? ['query', 'error', 'warn']
      : ['error'],
  });
};

declare global {
  var prisma: undefined | ReturnType<typeof prismaClientSingleton>;
}

export const prisma = globalThis.prisma ?? prismaClientSingleton();

if (process.env.NODE_ENV !== 'production') {
  globalThis.prisma = prisma;
}

export const connectDatabase = async () => {
  try {
    await prisma.$connect();
    console.log('✅ Database connected');
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    process.exit(1);
  }
};

export const disconnectDatabase = async () => {
  await prisma.$disconnect();
};
```

**Migrations:**
```bash
# Create migration
npx prisma migrate dev --name init

# Apply migrations (production)
npx prisma migrate deploy

# Reset database
npx prisma migrate reset

# Generate Prisma Client
npx prisma generate
```

**Seeds:**
```typescript
// prisma/seed.ts
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  // Clear existing data
  await prisma.post.deleteMany();
  await prisma.user.deleteMany();

  // Create users
  const admin = await prisma.user.create({
    data: {
      email: 'admin@example.com',
      username: 'admin',
      password: await bcrypt.hash('admin123', 10),
    },
  });

  const user = await prisma.user.create({
    data: {
      email: 'user@example.com',
      username: 'user',
      password: await bcrypt.hash('user123', 10),
    },
  });

  // Create posts
  await prisma.post.createMany({
    data: [
      {
        title: 'First Post',
        content: 'This is the first post',
        authorId: admin.id,
      },
      {
        title: 'Second Post',
        content: 'This is the second post',
        authorId: user.id,
      },
    ],
  });

  console.log('✅ Database seeded');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

```json
// package.json
{
  "prisma": {
    "seed": "ts-node prisma/seed.ts"
  },
  "scripts": {
    "seed": "prisma db seed"
  }
}
```

#### NestJS + TypeORM

**Module Configuration:**
```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { User } from './entities/user.entity';
import { Post } from './entities/post.entity';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        type: 'postgres',
        host: configService.get('DB_HOST', 'localhost'),
        port: configService.get('DB_PORT', 5432),
        username: configService.get('DB_USER', 'postgres'),
        password: configService.get('DB_PASSWORD'),
        database: configService.get('DB_NAME', 'mydb'),
        entities: [User, Post],
        synchronize: false,
        logging: configService.get('NODE_ENV') === 'development',
        extra: {
          max: 10,
          min: 2,
        },
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}
```

#### Go + GORM

**Database Configuration:**
```go
// config/database.go
package config

import (
    "fmt"
    "log"
    "os"
    "time"

    "gorm.io/driver/postgres"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

var DB *gorm.DB

func ConnectDatabase() {
    dsn := fmt.Sprintf(
        "host=%s user=%s password=%s dbname=%s port=%s sslmode=disable",
        os.Getenv("DB_HOST"),
        os.Getenv("DB_USER"),
        os.Getenv("DB_PASSWORD"),
        os.Getenv("DB_NAME"),
        os.Getenv("DB_PORT"),
    )

    database, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
    })

    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }

    sqlDB, err := database.DB()
    if err != nil {
        log.Fatal("Failed to get database instance:", err)
    }

    // Connection pool settings
    sqlDB.SetMaxIdleConns(10)
    sqlDB.SetMaxOpenConns(100)
    sqlDB.SetConnMaxLifetime(time.Hour)

    DB = database
    log.Println("✅ Database connected")
}

func MigrateDatabase() {
    DB.AutoMigrate(&User{}, &Post{})
    log.Println("✅ Database migrated")
}
```

**Models:**
```go
// models/user.go
package models

import (
    "time"
    "gorm.io/gorm"
)

type User struct {
    ID        uint           `gorm:"primarykey" json:"id"`
    Email     string         `gorm:"uniqueIndex;not null" json:"email"`
    Username  string         `gorm:"uniqueIndex;not null" json:"username"`
    Password  string         `gorm:"not null" json:"-"`
    IsActive  bool           `gorm:"default:true" json:"is_active"`
    CreatedAt time.Time      `json:"created_at"`
    UpdatedAt time.Time      `json:"updated_at"`
    DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
    Posts     []Post         `gorm:"foreignKey:AuthorID" json:"posts,omitempty"`
}

type Post struct {
    ID        uint           `gorm:"primarykey" json:"id"`
    Title     string         `gorm:"not null" json:"title"`
    Content   string         `gorm:"type:text" json:"content"`
    AuthorID  uint           `gorm:"index;not null" json:"author_id"`
    Author    User           `gorm:"foreignKey:AuthorID" json:"author,omitempty"`
    CreatedAt time.Time      `gorm:"index" json:"created_at"`
    DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
}
```

**Seeds:**
```go
// seeds/seed.go
package seeds

import (
    "log"
    "your-app/config"
    "your-app/models"
    "golang.org/x/crypto/bcrypt"
)

func SeedDatabase() {
    db := config.DB

    // Check if already seeded
    var count int64
    db.Model(&models.User{}).Count(&count)
    if count > 0 {
        log.Println("Database already seeded")
        return
    }

    // Hash passwords
    adminPass, _ := bcrypt.GenerateFromPassword([]byte("admin123"), 10)
    userPass, _ := bcrypt.GenerateFromPassword([]byte("user123"), 10)

    // Create users
    admin := models.User{
        Email:    "admin@example.com",
        Username: "admin",
        Password: string(adminPass),
        IsActive: true,
    }

    user := models.User{
        Email:    "user@example.com",
        Username: "user",
        Password: string(userPass),
        IsActive: true,
    }

    db.Create(&admin)
    db.Create(&user)

    // Create posts
    posts := []models.Post{
        {
            Title:    "First Post",
            Content:  "This is the first post",
            AuthorID: admin.ID,
        },
        {
            Title:    "Second Post",
            Content:  "This is the second post",
            AuthorID: user.ID,
        },
    }

    db.Create(&posts)

    log.Println("✅ Database seeded successfully")
}
```

---

### 2. MongoDB Setup

#### Express + Mongoose

**Connection:**
```typescript
// src/config/mongodb.ts
import mongoose from 'mongoose';

export const connectMongoDB = async () => {
  try {
    const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mydb';

    await mongoose.connect(uri, {
      maxPoolSize: 10,
      minPoolSize: 2,
      socketTimeoutMS: 45000,
      serverSelectionTimeoutMS: 5000,
    });

    console.log('✅ MongoDB connected');

    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
    });

    mongoose.connection.on('disconnected', () => {
      console.log('MongoDB disconnected');
    });

  } catch (error) {
    console.error('❌ MongoDB connection failed:', error);
    process.exit(1);
  }
};

export const disconnectMongoDB = async () => {
  await mongoose.disconnect();
};
```

**Schemas:**
```typescript
// src/models/User.ts
import { Schema, model, Document } from 'mongoose';

interface IUser extends Document {
  email: string;
  username: string;
  password: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const userSchema = new Schema<IUser>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
      index: true,
    },
    username: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      index: true,
    },
    password: {
      type: String,
      required: true,
      select: false, // Don't include in queries by default
    },
    isActive: {
      type: Boolean,
      default: true,
    },
  },
  {
    timestamps: true,
    collection: 'users',
  }
);

// Indexes
userSchema.index({ email: 1 });
userSchema.index({ username: 1 });

export const User = model<IUser>('User', userSchema);
```

```typescript
// src/models/Post.ts
import { Schema, model, Document, Types } from 'mongoose';

interface IPost extends Document {
  title: string;
  content: string;
  author: Types.ObjectId;
  createdAt: Date;
}

const postSchema = new Schema<IPost>(
  {
    title: {
      type: String,
      required: true,
      trim: true,
    },
    content: {
      type: String,
      required: true,
    },
    author: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
  },
  {
    timestamps: { createdAt: true, updatedAt: false },
    collection: 'posts',
  }
);

// Indexes
postSchema.index({ createdAt: -1 });
postSchema.index({ author: 1 });

export const Post = model<IPost>('Post', postSchema);
```

**Seeds:**
```typescript
// src/seeds/mongo-seed.ts
import { connectMongoDB, disconnectMongoDB } from '../config/mongodb';
import { User } from '../models/User';
import { Post } from '../models/Post';
import bcrypt from 'bcrypt';

async function seed() {
  await connectMongoDB();

  // Clear existing data
  await User.deleteMany({});
  await Post.deleteMany({});

  // Create users
  const admin = await User.create({
    email: 'admin@example.com',
    username: 'admin',
    password: await bcrypt.hash('admin123', 10),
  });

  const user = await User.create({
    email: 'user@example.com',
    username: 'user',
    password: await bcrypt.hash('user123', 10),
  });

  // Create posts
  await Post.insertMany([
    {
      title: 'First Post',
      content: 'This is the first post',
      author: admin._id,
    },
    {
      title: 'Second Post',
      content: 'This is the second post',
      author: user._id,
    },
  ]);

  console.log('✅ MongoDB seeded');
  await disconnectMongoDB();
}

seed().catch(console.error);
```

#### FastAPI + Motor (Async MongoDB)

**Connection:**
```python
# app/database_mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os

MONGODB_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mydb")

class MongoDB:
    client: AsyncIOMotorClient = None

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        mongodb.client = AsyncIOMotorClient(
            MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=2,
            serverSelectionTimeoutMS=5000
        )
        # Verify connection
        await mongodb.client.admin.command('ping')
        print("✅ MongoDB connected")
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        print("MongoDB disconnected")

def get_database():
    return mongodb.client[DB_NAME]
```

**Models (Pydantic):**
```python
# app/models/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

---

### 3. Redis Setup

**Express + Redis:**
```typescript
// src/config/redis.ts
import { createClient } from 'redis';

export const redisClient = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379',
  socket: {
    reconnectStrategy: (retries) => {
      if (retries > 10) {
        return new Error('Max reconnection attempts reached');
      }
      return retries * 1000;
    },
  },
});

export const connectRedis = async () => {
  try {
    await redisClient.connect();
    console.log('✅ Redis connected');

    redisClient.on('error', (err) => {
      console.error('Redis error:', err);
    });

    redisClient.on('reconnecting', () => {
      console.log('Redis reconnecting...');
    });

  } catch (error) {
    console.error('❌ Redis connection failed:', error);
    process.exit(1);
  }
};

export const disconnectRedis = async () => {
  await redisClient.quit();
};

// Cache helper functions
export const cache = {
  async get<T>(key: string): Promise<T | null> {
    const data = await redisClient.get(key);
    return data ? JSON.parse(data) : null;
  },

  async set(key: string, value: any, expiresIn?: number): Promise<void> {
    const data = JSON.stringify(value);
    if (expiresIn) {
      await redisClient.setEx(key, expiresIn, data);
    } else {
      await redisClient.set(key, data);
    }
  },

  async del(key: string): Promise<void> {
    await redisClient.del(key);
  },

  async exists(key: string): Promise<boolean> {
    return (await redisClient.exists(key)) === 1;
  },
};
```

**FastAPI + Redis:**
```python
# app/cache.py
import redis.asyncio as redis
import json
from typing import Optional, Any
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisCache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self.redis = await redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            await self.redis.ping()
            print("✅ Redis connected")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            raise

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        data = json.dumps(value)
        if expire:
            await self.redis.setex(key, expire, data)
        else:
            await self.redis.set(key, data)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.redis.exists(key) == 1

cache = RedisCache()
```

---

### 4. Docker Compose

**PostgreSQL + Redis:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: postgres_db
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
      POSTGRES_DB: ${DB_NAME:-mydb}
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis_cache
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  mongodb:
    image: mongo:7
    container_name: mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-root}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-password}
    ports:
      - "${MONGO_PORT:-27017}:27017"
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  mysql:
    image: mysql:8
    container_name: mysql_db
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-mydb}
      MYSQL_USER: ${MYSQL_USER:-user}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-password}
    ports:
      - "${MYSQL_PORT:-3306}:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  mongo_data:
  mysql_data:
```

**Start services:**
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f postgres
docker-compose down
```

---

### 5. Environment Configuration

**.env Template:**
```bash
# .env.example

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=mydb

# MySQL
MYSQL_URL=mysql://user:password@localhost:3306/mydb
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_DATABASE=mydb

# MongoDB
MONGODB_URI=mongodb://localhost:27017/mydb
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=root
MONGO_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# SQLite (for development)
SQLITE_DB_PATH=./data/app.db

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Application
NODE_ENV=development
PORT=3000
```

---

### 6. Best Practices

**Connection Pooling:**
- PostgreSQL: Use `pool_size=5-10` for most apps
- MongoDB: `maxPoolSize=10, minPoolSize=2`
- Redis: Use connection pool for high traffic

**Migrations:**
- Always use migrations (never `synchronize: true` in production)
- Version control all migration files
- Test migrations on staging before production

**Indexes:**
- Add indexes on frequently queried fields
- Monitor slow queries and add indexes accordingly
- Don't over-index (impacts write performance)

**Security:**
- Never commit `.env` files
- Use environment variables for credentials
- Enable SSL/TLS for production databases
- Use read-only users for reporting queries

**Monitoring:**
- Set up connection pool monitoring
- Track slow queries
- Monitor database CPU/memory usage
- Set up alerts for connection issues

---

## Output:

```bash
✅ Database setup complete!

Database: ${DATABASE}
Framework: ${FRAMEWORK}

Created files:
📄 config/database.{py|ts|go}
📄 models/user.{py|ts|go}
📄 models/post.{py|ts|go}
📄 migrations/
📄 seeds/seed.{py|ts|go}
📄 docker-compose.yml
📄 .env.example

Next steps:
1. Copy .env.example to .env and update credentials
2. Start database: docker-compose up -d ${DATABASE}
3. Run migrations
4. Seed database (optional)
5. Test connection

Commands:
- Start DB: docker-compose up -d
- Run migrations: [see framework-specific commands above]
- Seed DB: npm run seed / python scripts/seed.py
- View logs: docker-compose logs -f
```

---

## Examples:

```bash
/setup-db postgresql fastapi
/setup-db mongodb express
/setup-db postgresql nestjs
/setup-db mysql django
/setup-db redis express
/setup-db sqlite fastapi
```

**Database ready! 🗄️**