---
name: javascript-typescript-dev
description: "Разработка на JS/TS: React, Next.js, Node.js, тесты Jest/Vitest/Playwright. Триггеры: «напиши на typescript», «react-компонент», «типизируй»."
---

# JavaScript & TypeScript Development Skill

Modern JS/TS development including React, Next.js, Node.js, and testing.

## When to Use
- React applications (hooks, state management)
- Next.js 14 (App Router, Server Components)
- Node.js backends (Express, Nest.js)
- TypeScript patterns
- Testing (Jest, Vitest, Playwright)

## React Patterns

**Custom Hooks:**
\`\`\`typescript
// useAsync hook
function useAsync<T>(asyncFunction: () => Promise<T>) {
  const [state, setState] = useState<{
    loading: boolean;
    data: T | null;
    error: Error | null;
  }>({ loading: true, data: null, error: null });

  useEffect(() => {
    let mounted = true;
    asyncFunction()
      .then(data => mounted && setState({ loading: false, data, error: null }))
      .catch(error => mounted && setState({ loading: false, data: null, error }));
    return () => { mounted = false; };
  }, []);

  return state;
}
\`\`\`

## Next.js 14 Patterns

**Server Components:**
\`\`\`typescript
// app/posts/page.tsx
async function getPosts() {
  const res = await fetch('https://api.example.com/posts', {
    cache: 'no-store' // or 'force-cache'
  });
  return res.json();
}

export default async function PostsPage() {
  const posts = await getPosts();
  return <PostList posts={posts} />;
}
\`\`\`

**Server Actions:**
\`\`\`typescript
'use server'

export async function createPost(formData: FormData) {
  const title = formData.get('title');
  await db.posts.create({ title });
  revalidatePath('/posts');
}
\`\`\`

## Node.js Best Practices

**Express with TypeScript:**
\`\`\`typescript
import express, { Request, Response, NextFunction } from 'express';

const app = express();

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: err.message });
});
\`\`\`

## Testing

**Vitest:**
\`\`\`typescript
import { describe, it, expect, vi } from 'vitest';

describe('UserService', () => {
  it('should create user', async () => {
    const user = await UserService.create({ email: 'test@example.com' });
    expect(user).toBeDefined();
    expect(user.email).toBe('test@example.com');
  });
});
\`\`\`

**Playwright E2E:**
\`\`\`typescript
import { test, expect } from '@playwright/test';

test('should login successfully', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=password]', 'password123');
  await page.click('button[type=submit]');
  await expect(page).toHaveURL('/dashboard');
});
\`\`\`

## Performance Optimization

1. **Code splitting:** Use dynamic imports
2. **Memoization:** useMemo, React.memo
3. **Lazy loading:** React.lazy, Suspense
4. **Bundle analysis:** webpack-bundle-analyzer
5. **Image optimization:** Next.js Image component

## Common Pitfalls

**Dependency Array in useEffect:**
\`\`\`typescript
// ❌ Bad: missing dependency
useEffect(() => {
  fetchData(userId);
}, []);

// ✅ Good: include all dependencies
useEffect(() => {
  fetchData(userId);
}, [userId]);
\`\`\`

**State Updates:**
\`\`\`typescript
// ❌ Bad: mutating state
const handleAdd = () => {
  items.push(newItem);
  setItems(items);
};

// ✅ Good: creating new array
const handleAdd = () => {
  setItems([...items, newItem]);
};
\`\`\`
