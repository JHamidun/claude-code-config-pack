---
description: Комплексное тестирование Telegram бота с test scenarios
argument-hint: [путь к bot проекту или тип тестов]
---

# 🧪 Bot Test: $ARGUMENTS

Запусти комплексное тестирование для: **$ARGUMENTS**

## Test Categories:

### 1. Unit Tests
**Тестируй отдельные handlers и функции**

### 2. Integration Tests
**Тестируй взаимодействие компонентов**

### 3. E2E Tests
**Тестируй полные user flows**

### 4. Load Tests
**Тестируй производительность под нагрузкой**

## Process:

### 1. Generate Test Structure

```
tests/
├── unit/
│   ├── test_handlers.py
│   ├── test_validators.py
│   └── test_database.py
├── integration/
│   ├── test_scenes.py
│   └── test_middleware.py
├── e2e/
│   ├── test_onboarding_flow.py
│   └── test_full_user_journey.py
└── conftest.py
```

### 2. Unit Tests Template

```python
# tests/unit/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Message
from telegram.ext import ContextTypes

from handlers import start_handler, help_handler

@pytest.fixture
def mock_update():
    """Create mock Update object"""
    update = MagicMock(spec=Update)
    update.effective_user = User(id=123, first_name="Test", is_bot=False)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update

@pytest.fixture
def mock_context():
    """Create mock Context object"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot_data = {}
    return context

@pytest.mark.asyncio
async def test_start_handler(mock_update, mock_context):
    """Test /start command handler"""
    await start_handler(mock_update, mock_context)

    # Assert reply was sent
    mock_update.message.reply_text.assert_called_once()

    # Assert user data was initialized
    assert 'state' in mock_context.user_data
    assert mock_context.user_data['state'] == 'started'

@pytest.mark.asyncio
async def test_start_handler_with_existing_user(mock_update, mock_context):
    """Test /start for returning user"""
    mock_context.user_data['state'] = 'completed'

    await start_handler(mock_update, mock_context)

    # Should reset state
    assert mock_context.user_data['state'] == 'started'

@pytest.mark.asyncio
async def test_help_handler(mock_update, mock_context):
    """Test /help command"""
    await help_handler(mock_update, mock_context)

    # Check help text was sent
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert '/start' in call_args
    assert '/help' in call_args
```

### 3. Integration Tests Template

```python
# tests/integration/test_scenes.py
import pytest
from telegram.ext import Application, ConversationHandler

from handlers import create_conversation_handler
from database import Database

@pytest.fixture
async def app():
    """Create test application"""
    application = Application.builder().token("TEST_TOKEN").build()
    handler = create_conversation_handler()
    application.add_handler(handler)
    return application

@pytest.fixture
async def database():
    """Create test database"""
    db = Database("sqlite:///:memory:")
    await db.init()
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_onboarding_flow(app, database):
    """Test complete onboarding conversation"""
    # Simulate user messages
    updates = [
        create_message_update("/start"),
        create_message_update("John"),
        create_message_update("john@example.com"),
    ]

    for update in updates:
        await app.process_update(update)

    # Verify user was created
    user = await database.get_user(123)
    assert user.name == "John"
    assert user.email == "john@example.com"
    assert user.completed_onboarding == True

@pytest.mark.asyncio
async def test_scene_transitions(app):
    """Test scene state transitions"""
    # Start conversation
    await app.process_update(create_message_update("/start"))

    # Check state changed
    state = get_conversation_state(app, user_id=123)
    assert state == ONBOARDING

    # Send name
    await app.process_update(create_message_update("John"))

    # Check progressed to next state
    state = get_conversation_state(app, user_id=123)
    assert state == EMAIL_INPUT
```

### 4. E2E Tests Template

```python
# tests/e2e/test_full_user_journey.py
import pytest
from telethon import TelegramClient
from telethon.sessions import StringSession

@pytest.fixture
async def client():
    """Create Telegram client for E2E tests"""
    client = TelegramClient(
        StringSession(),
        api_id=TEST_API_ID,
        api_hash=TEST_API_HASH
    )
    await client.start(bot_token=TEST_BOT_TOKEN)
    yield client
    await client.disconnect()

@pytest.mark.e2e
async def test_new_user_journey(client):
    """Test complete new user experience"""
    bot_username = "your_bot"

    # 1. Send /start
    await client.send_message(bot_username, "/start")
    response = await client.get_messages(bot_username, limit=1)
    assert "Welcome" in response[0].text

    # 2. Enter name
    await client.send_message(bot_username, "John Doe")
    response = await client.get_messages(bot_username, limit=1)
    assert "email" in response[0].text.lower()

    # 3. Enter email
    await client.send_message(bot_username, "john@example.com")
    response = await client.get_messages(bot_username, limit=1)
    assert "complete" in response[0].text.lower()

    # 4. Test main menu
    await client.send_message(bot_username, "/help")
    response = await client.get_messages(bot_username, limit=1)
    assert response[0].buttons is not None

@pytest.mark.e2e
async def test_error_recovery(client):
    """Test error handling and recovery"""
    bot_username = "your_bot"

    # Send invalid command
    await client.send_message(bot_username, "/invalid")
    response = await client.get_messages(bot_username, limit=1)
    assert "unknown" in response[0].text.lower() or "help" in response[0].text.lower()

    # Should still be able to /start
    await client.send_message(bot_username, "/start")
    response = await client.get_messages(bot_username, limit=1)
    assert response[0].text is not None
```

### 5. Load Tests Template

```python
# tests/load/test_performance.py
import asyncio
import time
from locust import User, task, between

class BotUser(User):
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize bot user"""
        self.user_id = random.randint(100000, 999999)

    @task(3)
    def send_start(self):
        """Send /start command"""
        self.send_message("/start")

    @task(2)
    def send_help(self):
        """Send /help command"""
        self.send_message("/help")

    @task(1)
    def send_message(self, text):
        """Simulate message sending"""
        # Use Telegram Bot API
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": self.user_id,
                "text": text
            }
        )
        assert response.status_code == 200
```

### 6. Test Execution

**Run all tests:**
```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# E2E tests (requires running bot)
pytest tests/e2e -v -m e2e

# Load tests
locust -f tests/load/test_performance.py --host=http://localhost:8080
```

**With coverage:**
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

**CI/CD integration:**
```bash
# Run in CI
pytest tests/unit tests/integration --junitxml=test-results.xml
```

### 7. Test Scenarios Checklist

#### Basic Functionality
- [ ] /start command responds
- [ ] /help shows all commands
- [ ] Unknown commands handled
- [ ] Bot info retrievable

#### Conversation Flow
- [ ] Onboarding completes successfully
- [ ] Scene transitions work
- [ ] Fallback commands work in scenes
- [ ] /cancel exits conversation

#### Error Handling
- [ ] Invalid input handled gracefully
- [ ] Database errors caught
- [ ] Network errors retry
- [ ] User sees friendly error messages

#### Concurrent Users
- [ ] Multiple users don't interfere
- [ ] User data isolated (per_user=True)
- [ ] Callback queries work correctly
- [ ] Race conditions avoided

#### Performance
- [ ] Response time < 1s for commands
- [ ] Memory stable over time
- [ ] Database queries optimized
- [ ] No N+1 queries

#### Security
- [ ] SQL injection prevented
- [ ] XSS in user input handled
- [ ] Rate limiting works
- [ ] Authentication required where needed

### 8. Automated Test Report

**Generate test report:**
```python
# conftest.py
import pytest

def pytest_html_report_title(report):
    report.title = "Telegram Bot Test Report"

def pytest_configure(config):
    config._metadata['Bot'] = 'Your Bot v3'
    config._metadata['Environment'] = 'Test'
```

**Run with report:**
```bash
pytest --html=report.html --self-contained-html
```

## Output Format:

### Test Results Summary
```
🧪 Test Results for $ARGUMENTS

Total Tests: 45
✅ Passed: 42
❌ Failed: 2
⚠️ Skipped: 1

Coverage: 85%

Failed Tests:
1. test_callback_timeout - Callback query timeout
2. test_concurrent_users - Race condition detected

Recommendations:
- Fix callback query.answer() in button_handler
- Add locks for user_data access
- Increase test coverage for error scenarios
```

### Detailed Report
- HTML report with: test-report.html
- Coverage report: htmlcov/index.html
- JUnit XML: test-results.xml

## Examples:

```
/bot-test example-bot/src/bot
```

```
/bot-test unit tests only
```

```
/bot-test e2e full user journey
```

```
/bot-test load performance test
```

---

**Запускаю тесты! 🧪**