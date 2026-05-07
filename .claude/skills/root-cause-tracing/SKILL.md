---
name: root-cause-tracing
description: Use when errors occur deep in execution - systematically trace bugs backward through call stack, adding instrumentation when needed, to identify source of invalid data or incorrect behavior
---

# Root Cause Tracing

## Overview

Bugs manifest deep in call stacks (git init in wrong directory, files created in wrong location, database with wrong path). Fixing where errors appear treats symptoms, not causes.

**Core principle:** Trace backward through the call chain until you find the original trigger, then fix at the source.

**NEVER fix just where the error appears.**

## When to Use

- Errors occur deep in execution (not at entry point)
- Stack traces show long call chains
- Source of invalid data is unclear
- Need to identify which test/code triggers problems
- Непонятная ошибка в production
- Баг, который сложно воспроизвести
- Cascading failures

## The Five-Step Process

### Step 1: Observe the Symptom

Identify where error manifests:
```
Error: git init ran in $HOME/source-code
Expected: /tmp/test-workspace-xyz
```

### Step 2: Find Immediate Cause

Locate code directly causing failure:
```typescript
// In WorktreeManager.ts:42
async gitInit(directory: string) {
  await exec('git init', { cwd: directory });  // directory is wrong HERE
}
```

### Step 3: Ask "What Called This?"

Map the call chain upward:
```
gitInit(directory)        ← directory already wrong
  ↑ called by
createWorkspace(path)     ← path passed in wrong?
  ↑ called by
Project.initialize()      ← where does path come from?
  ↑ called by
test setup                ← ORIGIN: empty string passed
```

### Step 4: Keep Tracing Up

Follow parameter values backward:
```typescript
// Add instrumentation
async createWorkspace(path: string) {
  console.error('createWorkspace called with:', { path, stack: new Error().stack });
  // ...
}
```

### Step 5: Find Original Trigger

Locate the actual source:
```typescript
// FOUND: In test-setup.ts:15
const project = Project.create(name, '');  // Empty string! Root cause.
```

## Instrumentation Techniques

### Add Logging Before Operations

```typescript
async function gitInit(directory: string) {
  // Use console.error in tests (loggers may be suppressed)
  console.error('About to git init', {
    directory,
    cwd: process.cwd(),
    stack: new Error().stack,
  });

  await exec('git init', { cwd: directory });
}
```

### Capture Context

```python
import logging
import uuid

def process_request(request):
    request_id = str(uuid.uuid4())[:8]

    logger.info(f"[{request_id}] START processing")
    logger.debug(f"[{request_id}] Input: {request}")

    try:
        result = do_work(request)
        logger.info(f"[{request_id}] SUCCESS: {result}")
        return result
    except Exception as e:
        logger.error(f"[{request_id}] FAILED: {e}", exc_info=True)
        raise
```

## Defense-in-Depth Strategy

Beyond fixing the source, add validation at EVERY layer data passes through:

### Layer 1: Entry Point Validation

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  // ... proceed
}
```

### Layer 2: Business Logic Validation

```typescript
function initializeWorkspace(projectDir: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### Layer 3: Environment Guards

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

### Layer 4: Debug Instrumentation

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', { directory, cwd: process.cwd(), stack });
  // ... proceed
}
```

## 5 Whys Technique

```
Проблема: Сайт упал

Why 1: Почему сайт упал?
→ Сервер вернул 500 ошибку

Why 2: Почему сервер вернул 500?
→ База данных не отвечала

Why 3: Почему база не отвечала?
→ Закончились соединения в пуле

Why 4: Почему закончились соединения?
→ Запросы не закрывали соединения

Why 5: Почему не закрывали?
→ В новом коде забыли context manager

ROOT CAUSE: Отсутствие `with` statement в database.py:45
```

## Debugging Tools

### Git Bisect

```bash
git bisect start
git bisect bad HEAD           # Текущий - сломан
git bisect good v1.2.0        # Этот работал

# Git проверяет коммит посередине, тестируешь:
git bisect good  # или
git bisect bad

# Повторяй пока не найдёшь проблемный коммит
git bisect reset
```

### Stack Trace Analysis

```python
# Читай stack trace снизу вверх
Traceback (most recent call last):
  File "main.py", line 10           # 5. Точка входа
  File "processor.py", line 25      # 4. Вызов
  File "transformer.py", line 42    # 3. Вызов
  File "rules.py", line 18          # 2. Вызов
KeyError: 'key'                     # 1. ОШИБКА ТУТ

# Начни с line 18 - это место ошибки
# Но причина выше - откуда данные без 'key'?
```

### Python Debugging

```python
import pdb; pdb.set_trace()  # Breakpoint

# n - next line
# s - step into
# c - continue
# p variable - print
# w - where (stack trace)
```

## Common Root Causes

| Symptom | Possible Root Cause |
|---------|---------------------|
| KeyError, AttributeError | Missing/null data from upstream |
| TypeError | Wrong data type passed |
| Timeout | Connection pool exhausted |
| OOM | Memory leak |
| High CPU | Infinite loop, N+1 queries |
| Inconsistent data | Race condition |

## Investigation Checklist

```markdown
## Error Investigation Report

### 1. Symptoms
- Error message: ___
- When started: ___
- Frequency: ___

### 2. Reproduction
- [ ] Can reproduce locally?
- Steps: ___

### 3. Recent Changes
- Deployments: ___
- Config changes: ___

### 4. Evidence
- [ ] Logs collected
- [ ] Stack traces analyzed
- [ ] Call chain mapped

### 5. Root Cause
- First symptom: ___
- Chain of events: ___
- Original trigger: ___

### 6. Fix
- Immediate mitigation: ___
- Permanent fix: ___
- Defense-in-depth added: ___
```

## Key Insight

All four defense layers are necessary. During testing, each layer catches bugs the others miss:
- Different code paths bypass entry validation
- Mocks bypass business logic checks
- Edge cases need environment guards
- Debug logging identifies structural misuse

**Don't stop at one validation point. Add checks at every layer.**

## Tips

1. **Reproduce first** - не гадай, воспроизведи
2. **Read the error** - внимательно прочитай сообщение
3. **Trace backward** - от симптома к источнику
4. **Add instrumentation** - console.error с контекстом
5. **Ask "why" 5 times** - докопайся до причины
6. **Fix at source** - не маскируй проблему
7. **Add defense-in-depth** - валидация на каждом слое
