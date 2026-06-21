---
name: writing-plans
description: Use when creating implementation plans for features - breaks down work into bite-sized TDD tasks with exact file paths, code examples, and verification steps
---

# Writing Plans

## Overview

Create detailed implementation plans that any engineer can follow without domain expertise.

**Core principle:** Plans should be so specific that execution is mechanical.

## Plan Structure

```markdown
# Implementation Plan: [Feature Name]

## Overview
[1-2 sentences describing the feature]

## Prerequisites
- [ ] [Any setup needed]
- [ ] [Dependencies to install]

## Tasks

### Task 1: [Descriptive Name]

**Goal:** [What this task accomplishes]

**Files:**
- Create: `src/new-file.ts`
- Modify: `src/existing.ts`

**Steps:**
1. [Exact step with code example]
2. [Next step]
3. [Verification step]

**Test:**
```typescript
test('should [behavior]', () => {
  // Exact test code
});
```

**Verify:**
```bash
npm test -- --grep "should [behavior]"
```

### Task 2: ...
```

## Writing Guidelines

### Be Extremely Specific

```markdown
# ❌ BAD: Vague
"Add user validation"

# ✅ GOOD: Specific
"Add email validation to User.create() in src/models/user.ts:45
that throws InvalidEmailError if email doesn't match /^[^\s@]+@[^\s@]+\.[^\s@]+$/"
```

### Include Exact Code

```markdown
# ❌ BAD: Abstract
"Implement the login endpoint"

# ✅ GOOD: Concrete
"Create POST /api/login endpoint in src/routes/auth.ts:

```typescript
router.post('/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await UserService.authenticate(email, password);
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  const token = generateToken(user);
  res.json({ token });
});
```
"
```

### Specify File Paths

Always include:
- Full path from project root
- Line numbers when modifying existing code
- Whether to create or modify

### Include Verification Steps

Every task needs verification:

```markdown
**Verify:**
```bash
# Run specific test
npm test -- --grep "login endpoint"

# Check no regressions
npm test

# Verify manually (if needed)
curl -X POST localhost:3000/api/login -d '{"email":"test@example.com"}'
```
```

## Task Breakdown Principles

### One Behavior Per Task

```markdown
# ❌ BAD: Multiple behaviors
"Task 1: Add login, logout, and password reset"

# ✅ GOOD: Single behavior
"Task 1: Add login endpoint"
"Task 2: Add logout endpoint"
"Task 3: Add password reset request"
"Task 4: Add password reset confirmation"
```

### TDD-Ready Tasks

Each task should be implementable with TDD:
1. Write test (from plan)
2. Watch it fail
3. Implement (from plan)
4. Watch it pass

### Include Edge Cases

```markdown
### Task 3: Handle login errors

**Test cases:**
- Invalid email format → 400 Bad Request
- User not found → 401 Unauthorized
- Wrong password → 401 Unauthorized
- Account locked → 403 Forbidden
```

## Plan Review Checklist

Before finalizing plan:

- [ ] Each task has a single, clear goal
- [ ] All file paths are exact
- [ ] Code examples are complete and runnable
- [ ] Tests are provided for each task
- [ ] Verification commands are specified
- [ ] Tasks are ordered by dependency
- [ ] No ambiguous steps
- [ ] Edge cases identified

## Integration with Execution

Plans are executed using:
- `executing-plans` - Batch execution with review checkpoints
- `subagent-driven-development` - Fresh subagent per task

## Example Plan Structure

```markdown
# Implementation Plan: User Authentication

## Overview
Add email/password authentication with JWT tokens.

## Prerequisites
- [ ] Install jsonwebtoken: `npm install jsonwebtoken`
- [ ] Install bcrypt: `npm install bcrypt`

## Tasks

### Task 1: Create User Model

**Goal:** Define User schema with password hashing

**Files:**
- Create: `src/models/user.ts`

**Steps:**
1. Create User interface
2. Add password hashing in pre-save hook
3. Add comparePassword method

**Code:**
```typescript
// src/models/user.ts
interface User {
  id: string;
  email: string;
  passwordHash: string;
  createdAt: Date;
}

export async function createUser(email: string, password: string): Promise<User> {
  const passwordHash = await bcrypt.hash(password, 10);
  return db.users.create({ email, passwordHash, createdAt: new Date() });
}
```

**Test:**
```typescript
test('hashes password on creation', async () => {
  const user = await createUser('test@example.com', 'password123');
  expect(user.passwordHash).not.toBe('password123');
  expect(await bcrypt.compare('password123', user.passwordHash)).toBe(true);
});
```

**Verify:**
```bash
npm test -- --grep "hashes password"
```
```
