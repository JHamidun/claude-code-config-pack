---
name: senior-architect
description: Comprehensive software architecture skill for designing scalable, maintainable systems using ReactJS, NextJS, NodeJS, Express, React Native, Swift, Kotlin, Flutter, Postgres, GraphQL, Go, Python. Includes architecture diagram generation, system design patterns, tech stack decision frameworks, and dependency analysis. Use when designing system architecture, making technical decisions, creating architecture diagrams, evaluating trade-offs, or defining integration patterns.
type: actionable
---

# Senior Architect

Complete toolkit for senior architect with modern tools and best practices.

## Quick Start

### Main Capabilities

This skill provides three core capabilities through automated scripts:

```bash
# Script 1: Architecture Diagram Generator
python scripts/architecture_diagram_generator.py [options]

# Script 2: Project Architect
python scripts/project_architect.py [options]

# Script 3: Dependency Analyzer
python scripts/dependency_analyzer.py [options]
```

## Core Capabilities

### 1. Architecture Diagram Generator

Automated tool for architecture diagram generator tasks.

**Features:**
- Automated scaffolding
- Best practices built-in
- Configurable templates
- Quality checks

**Usage:**
```bash
python scripts/architecture_diagram_generator.py <project-path> [options]
```

### 2. Project Architect

Comprehensive analysis and optimization tool.

**Features:**
- Deep analysis
- Performance metrics
- Recommendations
- Automated fixes

**Usage:**
```bash
python scripts/project_architect.py <target-path> [--verbose]
```

### 3. Dependency Analyzer

Advanced tooling for specialized tasks.

**Features:**
- Expert-level automation
- Custom configurations
- Integration ready
- Production-grade output

**Usage:**
```bash
python scripts/dependency_analyzer.py [arguments] [options]
```

## Reference Documentation

### Architecture Patterns

Comprehensive guide available in `references/architecture_patterns.md`:

- Detailed patterns and practices
- Code examples
- Best practices
- Anti-patterns to avoid
- Real-world scenarios

### System Design Workflows

Complete workflow documentation in `references/system_design_workflows.md`:

- Step-by-step processes
- Optimization strategies
- Tool integrations
- Performance tuning
- Troubleshooting guide

### Tech Decision Guide

Technical reference guide in `references/tech_decision_guide.md`:

- Technology stack details
- Configuration examples
- Integration patterns
- Security considerations
- Scalability guidelines

## Tech Stack

**Languages:** TypeScript, JavaScript, Python, Go, Swift, Kotlin
**Frontend:** React, Next.js, React Native, Flutter
**Backend:** Node.js, Express, GraphQL, REST APIs
**Database:** PostgreSQL, Prisma, NeonDB, Supabase
**DevOps:** Docker, Kubernetes, Terraform, GitHub Actions, CircleCI
**Cloud:** AWS, GCP, Azure

## Development Workflow

### 1. Setup and Configuration

```bash
# Install dependencies
npm install
# or
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### 2. Run Quality Checks

```bash
# Use the analyzer script
python scripts/project_architect.py .

# Review recommendations
# Apply fixes
```

### 3. Implement Best Practices

Follow the patterns and practices documented in:
- `references/architecture_patterns.md`
- `references/system_design_workflows.md`
- `references/tech_decision_guide.md`

## Best Practices Summary

### Code Quality
- Follow established patterns
- Write comprehensive tests
- Document decisions
- Review regularly

### Performance
- Measure before optimizing
- Use appropriate caching
- Optimize critical paths
- Monitor in production

### Security
- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Keep dependencies updated

### Maintainability
- Write clear code
- Use consistent naming
- Add helpful comments
- Keep it simple

## Common Commands

```bash
# Development
npm run dev
npm run build
npm run test
npm run lint

# Analysis
python scripts/project_architect.py .
python scripts/dependency_analyzer.py --analyze

# Deployment
docker build -t app:latest .
docker-compose up -d
kubectl apply -f k8s/
```

## Troubleshooting

### Common Issues

Check the comprehensive troubleshooting section in `references/tech_decision_guide.md`.

### Getting Help

- Review reference documentation
- Check script output messages
- Consult tech stack documentation
- Review error logs

## Resources

- Pattern Reference: `references/architecture_patterns.md`
- Workflow Guide: `references/system_design_workflows.md`
- Technical Guide: `references/tech_decision_guide.md`
- Tool Scripts: `scripts/` directory

---

## Architecture Foundations

### SOLID Principles

#### S - Single Responsibility

```python
# ❌ Плохо - класс делает слишком много
class User:
    def save_to_db(self): pass
    def send_email(self): pass
    def generate_report(self): pass

# ✅ Хорошо - разделение ответственности
class User:
    def __init__(self, name, email): pass

class UserRepository:
    def save(self, user): pass

class EmailService:
    def send(self, user, message): pass

class ReportGenerator:
    def generate(self, user): pass
```

#### O - Open/Closed

```python
# ❌ Плохо - изменение существующего кода
class PaymentProcessor:
    def process(self, payment_type):
        if payment_type == "card":
            # process card
        elif payment_type == "paypal":
            # process paypal
        # Нужно менять при добавлении нового типа

# ✅ Хорошо - расширение без изменения
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    @abstractmethod
    def process(self, amount): pass

class CardPayment(PaymentMethod):
    def process(self, amount): pass

class PayPalPayment(PaymentMethod):
    def process(self, amount): pass

class CryptoPayment(PaymentMethod):  # Новый тип без изменений
    def process(self, amount): pass
```

#### L - Liskov Substitution

```python
# ❌ Плохо - нарушение контракта
class Bird:
    def fly(self): pass

class Penguin(Bird):
    def fly(self):
        raise Exception("Penguins can't fly!")  # Нарушение!

# ✅ Хорошо - правильная иерархия
class Bird:
    def move(self): pass

class FlyingBird(Bird):
    def fly(self): pass

class Penguin(Bird):
    def move(self):
        self.swim()
```

#### I - Interface Segregation

```python
# ❌ Плохо - толстый интерфейс
class Worker(ABC):
    @abstractmethod
    def work(self): pass
    @abstractmethod
    def eat(self): pass
    @abstractmethod
    def sleep(self): pass

class Robot(Worker):
    def eat(self): pass   # Не нужен роботу!
    def sleep(self): pass  # Не нужен роботу!

# ✅ Хорошо - маленькие интерфейсы
class Workable(ABC):
    @abstractmethod
    def work(self): pass

class Eatable(ABC):
    @abstractmethod
    def eat(self): pass

class Human(Workable, Eatable):
    def work(self): pass
    def eat(self): pass

class Robot(Workable):
    def work(self): pass
```

#### D - Dependency Inversion

```python
# ❌ Плохо - зависимость от конкретики
class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Жёсткая связь

# ✅ Хорошо - зависимость от абстракции
class Database(ABC):
    @abstractmethod
    def query(self, sql): pass

class UserService:
    def __init__(self, db: Database):  # Инъекция
        self.db = db

# Использование
mysql = MySQLDatabase()
postgres = PostgresDatabase()
service = UserService(postgres)  # Легко менять
```

### Design Patterns

#### Creational Patterns

| Pattern | When to Use |
|---------|-------------|
| **Factory** | Создание объектов без указания класса |
| **Abstract Factory** | Семейства связанных объектов |
| **Builder** | Сложные объекты пошагово |
| **Singleton** | Единственный экземпляр (осторожно!) |
| **Prototype** | Клонирование объектов |

```python
# Factory
class NotificationFactory:
    @staticmethod
    def create(type: str) -> Notification:
        if type == "email":
            return EmailNotification()
        elif type == "sms":
            return SMSNotification()
        elif type == "push":
            return PushNotification()

# Builder
class QueryBuilder:
    def __init__(self):
        self._query = ""

    def select(self, *fields):
        self._query += f"SELECT {', '.join(fields)} "
        return self

    def from_table(self, table):
        self._query += f"FROM {table} "
        return self

    def where(self, condition):
        self._query += f"WHERE {condition} "
        return self

    def build(self):
        return self._query

query = QueryBuilder() \
    .select("id", "name") \
    .from_table("users") \
    .where("active = true") \
    .build()
```

#### Structural Patterns

| Pattern | When to Use |
|---------|-------------|
| **Adapter** | Несовместимые интерфейсы |
| **Decorator** | Добавление функциональности |
| **Facade** | Упрощение сложного API |
| **Proxy** | Контроль доступа |
| **Composite** | Древовидные структуры |

```python
# Decorator
from functools import wraps

def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Returned {result}")
        return result
    return wrapper

def cache(func):
    _cache = {}
    @wraps(func)
    def wrapper(*args):
        if args not in _cache:
            _cache[args] = func(*args)
        return _cache[args]
    return wrapper

@log_calls
@cache
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Facade
class VideoConverter:
    """Простой интерфейс для сложной системы"""
    def convert(self, filename, format):
        file = VideoFile(filename)
        codec = CodecFactory.extract(file)
        result = BitrateReader.read(filename, codec)
        result = AudioMixer.fix(result)
        return Encoder.encode(result, format)
```

#### Behavioral Patterns

| Pattern | When to Use |
|---------|-------------|
| **Strategy** | Взаимозаменяемые алгоритмы |
| **Observer** | Подписка на события |
| **Command** | Инкапсуляция действий |
| **State** | Поведение зависит от состояния |
| **Template Method** | Скелет алгоритма |

```python
# Strategy
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount): pass

class CreditCard(PaymentStrategy):
    def pay(self, amount):
        return f"Paid {amount} via Credit Card"

class PayPal(PaymentStrategy):
    def pay(self, amount):
        return f"Paid {amount} via PayPal"

class ShoppingCart:
    def checkout(self, strategy: PaymentStrategy, amount):
        return strategy.pay(amount)

# Observer
class EventEmitter:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event, callback):
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def emit(self, event, data):
        for callback in self._subscribers.get(event, []):
            callback(data)

emitter = EventEmitter()
emitter.subscribe("user_created", lambda u: print(f"Welcome {u}"))
emitter.emit("user_created", "John")
```

### Clean Architecture

```
┌─────────────────────────────────────────┐
│           Frameworks & Drivers           │
│  (Web, DB, External APIs, UI)           │
├─────────────────────────────────────────┤
│         Interface Adapters               │
│  (Controllers, Gateways, Presenters)    │
├─────────────────────────────────────────┤
│          Application Layer               │
│  (Use Cases, Services)                  │
├─────────────────────────────────────────┤
│           Domain Layer                   │
│  (Entities, Value Objects)              │
└─────────────────────────────────────────┘
        ↑ Зависимости направлены внутрь
```

#### Project Structure

```
src/
├── domain/
│   ├── entities/
│   │   ├── user.py
│   │   └── order.py
│   ├── value_objects/
│   │   └── email.py
│   └── repositories/      # Interfaces only
│       └── user_repository.py
├── application/
│   ├── use_cases/
│   │   ├── create_user.py
│   │   └── place_order.py
│   └── services/
│       └── notification_service.py
├── infrastructure/
│   ├── repositories/      # Implementations
│   │   └── postgres_user_repository.py
│   ├── external/
│   │   └── stripe_payment.py
│   └── config/
│       └── database.py
└── presentation/
    ├── api/
    │   └── routes/
    └── web/
        └── controllers/
```

### Domain-Driven Design (DDD)

#### Key Concepts

| Concept | Description |
|---------|-------------|
| **Entity** | Объект с уникальным ID |
| **Value Object** | Объект без ID, сравнивается по значению |
| **Aggregate** | Кластер объектов с корнем |
| **Repository** | Абстракция хранилища |
| **Service** | Бизнес-логика без состояния |
| **Event** | Что-то произошло в домене |

```python
# Value Object
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)

# Entity
@dataclass
class Order:
    id: UUID
    customer_id: UUID
    items: list[OrderItem]
    status: OrderStatus

    def add_item(self, item: OrderItem):
        if self.status != OrderStatus.DRAFT:
            raise DomainError("Cannot modify confirmed order")
        self.items.append(item)

# Aggregate Root
class ShoppingCart:
    def __init__(self, customer_id: UUID):
        self.id = uuid4()
        self.customer_id = customer_id
        self._items: list[CartItem] = []
        self._events: list[DomainEvent] = []

    def add_product(self, product: Product, quantity: int):
        item = CartItem(product, quantity)
        self._items.append(item)
        self._events.append(ProductAddedToCart(self.id, product.id))

    def checkout(self) -> Order:
        order = Order.create(self.customer_id, self._items)
        self._events.append(CartCheckedOut(self.id, order.id))
        return order
```

### Microservices Patterns

| Pattern | Use Case |
|---------|----------|
| **API Gateway** | Single entry point |
| **Service Discovery** | Dynamic service location |
| **Circuit Breaker** | Fault tolerance |
| **Saga** | Distributed transactions |
| **CQRS** | Separate read/write models |
| **Event Sourcing** | State as events |

```python
# Circuit Breaker
class CircuitBreaker:
    def __init__(self, threshold=5, timeout=60):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure = None

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.timeout:
                self.state = "HALF-OPEN"
            else:
                raise CircuitOpenError()

        try:
            result = func(*args, **kwargs)
            self.failures = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = "OPEN"
            raise
```

### System Design Checklist

1. **Требования**
   - Функциональные
   - Нефункциональные (масштаб, latency, availability)

2. **High-Level Design**
   - Компоненты системы
   - Взаимодействие между ними

3. **Deep Dive**
   - Database schema
   - API design
   - Scaling strategy

4. **Trade-offs**
   - CAP theorem
   - Consistency vs Availability
   - Cost vs Performance

### Architecture Tips

1. **KISS** - Keep It Simple, Stupid
2. **YAGNI** - You Aren't Gonna Need It
3. **DRY** - Don't Repeat Yourself (но не преждевременно!)
4. **Composition > Inheritance**
5. **Program to interfaces**
6. **Fail fast**
7. **Make it work, make it right, make it fast**
