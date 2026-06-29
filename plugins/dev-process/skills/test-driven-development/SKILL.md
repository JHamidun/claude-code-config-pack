---
name: test-driven-development
description: Use when implementing any feature or bugfix - write the test first, watch it fail, write minimal code to pass; ensures tests actually verify behavior by requiring failure first
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Violating the letter of the rules is violating the spirit of the rules.**

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask your human partner):**
- Throwaway prototypes
- Generated code
- Configuration files

Thinking "skip TDD just this once"? Stop. That's rationalization.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

## Red-Green-Refactor

```
    ┌─────────────────┐
    │    RED          │
    │  Write failing  │
    │     test        │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  VERIFY RED     │
    │  Watch it fail  │
    │  for RIGHT reason│
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │    GREEN        │
    │  Write minimal  │
    │  code to pass   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  VERIFY GREEN   │
    │  All tests pass │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   REFACTOR      │
    │  Improve code   │
    │  (tests pass)   │
    └────────┬────────┘
             │
             └──────────► Repeat
```

### RED - Write Failing Test

Write one minimal test showing what should happen.

```typescript
// ✅ GOOD: Clear name, tests real behavior, one thing
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

```typescript
// ❌ BAD: Vague name, tests mock not code
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(2);
});
```

**Requirements:**
- One behavior
- Clear name
- Real code (no mocks unless unavoidable)

### VERIFY RED - Watch It Fail

**MANDATORY. Never skip.**

```bash
npm test path/to/test.test.ts
# или
pytest test_file.py::test_name
```

Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

**Test passes?** You're testing existing behavior. Fix test.
**Test errors?** Fix error, re-run until it fails correctly.

### GREEN - Minimal Code

Write simplest code to pass the test.

```typescript
// ✅ GOOD: Just enough to pass
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```

```typescript
// ❌ BAD: Over-engineered - YAGNI!
async function retryOperation<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number) => void;
  }
): Promise<T> {
  // Nobody asked for this
}
```

Don't add features, refactor other code, or "improve" beyond the test.

### VERIFY GREEN - Watch It Pass

**MANDATORY.**

```bash
npm test path/to/test.test.ts
```

Confirm:
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix code, not test.
**Other tests fail?** Fix now.

### REFACTOR - Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Don't add behavior.

## Test Patterns

### Arrange-Act-Assert (AAA)

```python
def test_user_creation():
    # Arrange
    email = "test@example.com"
    password = "secure123"

    # Act
    user = User.create(email, password)

    # Assert
    assert user.email == email
    assert user.is_active == True
```

### Test Doubles

```python
# Mock - проверяем вызовы
def test_sends_welcome_email(mocker):
    mock_email = mocker.patch('services.email.send')
    User.create("new@example.com")
    mock_email.assert_called_once_with(to="new@example.com", template="welcome")

# Stub - возвращаем заданные значения
def test_handles_payment_failure(mocker):
    mocker.patch('services.payment.charge', return_value=False)
    result = checkout_service.process(order)
    assert result.status == "payment_failed"
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("World", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert uppercase(input) == expected
```

## Common Rationalizations (ALL WRONG)

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is debt. |
| "Keep as reference" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |
| "Test hard = design unclear" | Listen to test. Hard to test = hard to use. |
| "TDD will slow me down" | TDD faster than debugging. |
| "This is different because..." | No it isn't. |

## Red Flags - STOP and Start Over

- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "It's about spirit not ritual"
- "Keep as reference"
- "Already spent X hours, deleting is wasteful"

**All of these mean: Delete code. Start over with TDD.**

## Bug Fix with TDD

```python
# 1. Воспроизводим баг тестом
def test_handles_null_user():
    # Этот тест должен падать, демонстрируя баг
    result = process_order(user=None)
    assert result.error == "User required"

# 2. Запускаем - тест падает ❌
# 3. Фиксим код
def process_order(user):
    if user is None:
        return Result(error="User required")
    # ... rest of logic

# 4. Тест проходит ✅
# 5. Баг никогда не вернётся!
```

**Never fix bugs without a test.**

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write wished-for API. Write assertion first. |
| Test too complicated | Design too complicated. Simplify interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify design. |

## Test Organization

```
tests/
├── unit/
│   ├── test_user.py
│   ├── test_order.py
│   └── test_calculator.py
├── integration/
│   ├── test_database.py
│   └── test_api.py
├── e2e/
│   └── test_checkout_flow.py
├── fixtures/
│   ├── conftest.py
│   └── factories.py
└── utils/
    └── helpers.py
```

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without your human partner's permission.
