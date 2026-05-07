---
name: manus
description: Manus AI autonomous agent platform - task automation, web browsing, code execution
---

# Manus AI Skill

## Overview

Manus - платформа автономных AI агентов. Выполняет сложные задачи: веб-браузинг, написание кода, исследования, автоматизация.

## API Configuration

```python
import requests
import os

MANUS_API_KEY = os.getenv('MANUS_API_KEY')
BASE_URL = "https://api.manus.ai/v1"

headers = {
    "API_KEY": MANUS_API_KEY,
    "accept": "application/json",
    "content-type": "application/json"
}
```

## When to Use

- Автономное выполнение сложных задач
- Web research с навигацией
- Автоматизация рутинных операций
- Выполнение кода в sandbox
- Работа с файлами и документами

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Web Browsing** | Навигация, клики, формы |
| **Code Execution** | Python, JS в sandbox |
| **File Operations** | Чтение, запись, конвертация |
| **Research** | Глубокий поиск + анализ |
| **Data Extraction** | Scraping + структурирование |
| **Task Planning** | Декомпозиция сложных задач |

## API Endpoints

### Create Task

```python
def create_task(prompt: str, tools: list = None):
    """Create autonomous task"""
    payload = {
        "prompt": prompt,
        "tools": tools or ["browser", "code", "files"],
        "settings": {
            "max_steps": 50,
            "timeout_minutes": 30,
            "sandbox": True
        }
    }

    response = requests.post(
        f"{BASE_URL}/tasks",
        headers=headers,
        json=payload
    )
    return response.json()

# Response:
# {
#   "task_id": "task_abc123",
#   "status": "running",
#   "created_at": "2024-01-15T10:30:00Z"
# }
```

### Get Task Status

```python
def get_task_status(task_id: str):
    """Check task progress"""
    response = requests.get(
        f"{BASE_URL}/tasks/{task_id}",
        headers=headers
    )
    return response.json()

# Response:
# {
#   "task_id": "task_abc123",
#   "status": "completed",  # running, completed, failed, paused
#   "progress": 100,
#   "steps_completed": 15,
#   "result": {...},
#   "artifacts": [...]
# }
```

### Get Task Steps

```python
def get_task_steps(task_id: str):
    """Get detailed step-by-step execution"""
    response = requests.get(
        f"{BASE_URL}/tasks/{task_id}/steps",
        headers=headers
    )
    return response.json()

# Response:
# {
#   "steps": [
#     {"step": 1, "action": "browse", "url": "https://...", "result": "..."},
#     {"step": 2, "action": "extract", "data": {...}},
#     {"step": 3, "action": "code", "language": "python", "output": "..."}
#   ]
# }
```

### Download Artifacts

```python
def download_artifact(task_id: str, artifact_id: str):
    """Download generated files"""
    response = requests.get(
        f"{BASE_URL}/tasks/{task_id}/artifacts/{artifact_id}",
        headers=headers
    )
    return response.content
```

## Tool Configurations

### Browser Tool

```python
browser_config = {
    "tool": "browser",
    "settings": {
        "headless": True,
        "screenshots": True,      # Capture screenshots
        "viewport": {"width": 1920, "height": 1080},
        "wait_for_network": True,
        "allowed_domains": None,   # None = all allowed
        "blocked_domains": ["ads.example.com"]
    }
}
```

### Code Execution Tool

```python
code_config = {
    "tool": "code",
    "settings": {
        "languages": ["python", "javascript", "bash"],
        "timeout_seconds": 60,
        "memory_limit_mb": 512,
        "packages": ["pandas", "requests", "beautifulsoup4"],
        "sandbox": True
    }
}
```

### File Tool

```python
file_config = {
    "tool": "files",
    "settings": {
        "allowed_operations": ["read", "write", "convert"],
        "max_file_size_mb": 100,
        "allowed_formats": ["pdf", "docx", "xlsx", "csv", "json"]
    }
}
```

## Complete Workflow

```python
import time

def run_autonomous_task(prompt: str, wait: bool = True):
    """Execute task and wait for completion"""

    # 1. Create task
    result = create_task(prompt)
    task_id = result['task_id']
    print(f"Task started: {task_id}")

    if not wait:
        return task_id

    # 2. Poll for completion
    while True:
        status = get_task_status(task_id)
        print(f"Progress: {status['progress']}% - {status['status']}")

        if status['status'] == 'completed':
            return {
                "task_id": task_id,
                "result": status['result'],
                "artifacts": status.get('artifacts', [])
            }
        elif status['status'] == 'failed':
            raise Exception(f"Task failed: {status.get('error')}")

        time.sleep(5)

# Usage
result = run_autonomous_task(
    "Research the top 10 AI startups in 2024, "
    "create a comparison table with funding, products, and team size"
)
print(result)
```

## Use Case Examples

### Web Research

```python
# Deep research with sources
result = run_autonomous_task("""
Research: "Best practices for microservices architecture in 2024"
Requirements:
1. Find at least 5 authoritative sources
2. Extract key recommendations
3. Create a summary document
4. Include source URLs
""")
```

### Data Extraction

```python
# Scrape and structure data
result = run_autonomous_task("""
Extract product data from https://example-store.com/products:
- Product name
- Price
- Rating
- Number of reviews

Output as CSV file.
""")

# Download artifact
csv_data = download_artifact(
    result['task_id'],
    result['artifacts'][0]['id']
)
```

### Code Generation & Execution

```python
# Generate and run code
result = run_autonomous_task("""
Task: Analyze the sentiment of customer reviews

1. Read reviews from the attached CSV
2. Use a sentiment analysis library
3. Calculate average sentiment by product category
4. Create a visualization chart
5. Save results as PNG and JSON
""")
```

### Workflow Automation

```python
# Multi-step automation
result = run_autonomous_task("""
Daily report automation:
1. Go to analytics.example.com
2. Download yesterday's sales report
3. Extract key metrics (revenue, orders, top products)
4. Format as executive summary
5. Save as PDF
""")
```

## Advanced Features

### Conditional Logic

```python
task_with_conditions = {
    "prompt": "Check competitor prices",
    "conditions": [
        {
            "if": "price_difference > 10%",
            "then": "alert_slack",
            "params": {"channel": "#pricing"}
        }
    ]
}
```

### Scheduled Tasks

```python
def schedule_task(prompt: str, cron: str):
    """Schedule recurring task"""
    payload = {
        "prompt": prompt,
        "schedule": {
            "cron": cron,  # "0 9 * * 1" = every Monday 9am
            "timezone": "UTC"
        }
    }
    return requests.post(
        f"{BASE_URL}/tasks/scheduled",
        headers=headers,
        json=payload
    ).json()
```

### Human-in-the-loop

```python
task_with_approval = {
    "prompt": "Draft and send email to client",
    "require_approval": True,
    "approval_steps": ["before_send"],
    "notification_webhook": "https://your-app.com/webhooks/manus"
}
```

## Integration with Other Agents

```python
# Manus для research → другие агенты для реализации

# 1. Manus: исследование и анализ
research = run_autonomous_task(
    "Research best authentication libraries for Python FastAPI"
)

# 2. Kimi: code review плана
# Task(subagent_type="kimi-code-reviewer", prompt=research['result'])

# 3. Backend-dev: реализация
# Task(subagent_type="backend-dev", prompt="Implement auth based on research")
```

## Comparison with Other Tools

| Feature | Manus | Browser MCP | n8n |
|---------|-------|-------------|-----|
| Autonomous | ✅ | ❌ | ❌ |
| Code execution | ✅ | ❌ | Limited |
| Web browsing | ✅ | ✅ | Via nodes |
| Planning | ✅ | ❌ | Manual |
| Best for | Complex autonomous | Simple scraping | Workflows |

## Pricing

| Plan | Tasks/month | Features |
|------|-------------|----------|
| Free | 10 | Basic tools |
| Pro | 100 | All tools + priority |
| Team | 500 | Collaboration + API |
| Enterprise | Unlimited | Custom + SLA |

## Tips

1. **Чёткие инструкции** - детальный prompt = лучший результат
2. **Разбивай сложное** - несколько простых задач лучше одной сложной
3. **Проверяй результат** - автономность ≠ безошибочность
4. **Используй sandbox** - для безопасного выполнения кода
5. **Комбинируй с n8n** - Manus для сложного, n8n для рутинного
