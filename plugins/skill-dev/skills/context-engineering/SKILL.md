---
name: context-engineering
description: "Context Engineering Kit"
---

# Context Engineering Kit

Advanced patterns for optimizing context usage and minimizing token footprint.

## When to Use

- Working with large codebases
- Need to fit more info in context
- Optimizing long conversations
- Reducing API costs

## Core Principles

### 1. Progressive Disclosure
Load context incrementally, not all at once:

```
Level 1: File names and structure
Level 2: Function signatures and docstrings
Level 3: Implementation details (on demand)
```

### 2. Semantic Compression
Compress information without losing meaning:

```markdown
❌ Verbose:
"The function calculateTotalPrice takes a list of items as input,
iterates through each item, multiplies the price by quantity,
and returns the sum of all calculations."

✅ Compressed:
"calculateTotalPrice(items[]) → sum(price * qty)"
```

### 3. Structured References
Use compact references instead of full content:

```markdown
❌ Copy entire file
✅ Reference: "See auth.py:authenticate() lines 45-60"
```

## Patterns

### Pattern 1: Summary-First Context
```
<context>
<summary>
E-commerce app: FastAPI backend, React frontend, PostgreSQL.
Key files: api/routes.py, models/product.py, services/cart.py
</summary>

<current_task>
Fix cart total calculation bug
</current_task>

<relevant_code>
[Only the specific functions needed]
</relevant_code>
</context>
```

### Pattern 2: Layered Architecture Context
```
<architecture>
┌─────────────────────────────────────┐
│ API Layer: FastAPI routes           │
├─────────────────────────────────────┤
│ Service Layer: Business logic       │
├─────────────────────────────────────┤
│ Data Layer: SQLAlchemy models       │
└─────────────────────────────────────┘
</architecture>

<focus_layer>Service</focus_layer>
<adjacent_interfaces>
- API: POST /cart/add → add_to_cart(user_id, product_id, qty)
- Data: Cart.add_item(), Product.get_by_id()
</adjacent_interfaces>
```

### Pattern 3: Delta Context
Only include what changed:

```
<previous_state>
Cart total: sum of item prices
</previous_state>

<change>
Added: discount codes support
Modified: calculateTotal() now applies discounts
</change>

<current_issue>
Discount not applied to already-added items
</current_issue>
```

### Pattern 4: Contract-Based Context
Define interfaces instead of implementations:

```typescript
// Instead of full implementation, show contracts:
interface CartService {
  addItem(userId: string, productId: string, qty: number): Promise<Cart>;
  removeItem(userId: string, itemId: string): Promise<Cart>;
  getTotal(userId: string): Promise<{ subtotal: number; discount: number; total: number }>;
}
```

## Token Optimization Techniques

### 1. Use Abbreviations
```
func → function
param → parameter
ret → return
impl → implementation
```

### 2. Remove Redundancy
```markdown
❌ "The user wants to implement a feature that allows users to..."
✅ "Implement: user feature for..."
```

### 3. Structured Data Over Prose
```markdown
❌ "The function takes three parameters: name which is a string,
    age which is a number, and active which is a boolean"

✅ params: name(str), age(int), active(bool)
```

### 4. Code Comments as Context
```python
# CONTEXT: Part of auth flow, called after OAuth callback
# DEPS: UserService, TokenService
# RETURNS: JWT token or raises AuthError
def complete_oauth(code: str) -> str:
    ...
```

## Memory Patterns

### Session Memory
```json
{
  "session_context": {
    "project": "e-commerce",
    "current_branch": "feature/discounts",
    "recent_files": ["cart.py", "discount.py"],
    "decisions": [
      "Using percentage-based discounts",
      "Max one code per order"
    ]
  }
}
```

### Compact Summaries
After each major interaction, create a compact summary:
```
[Session 5 Summary]
- Fixed: cart total bug (missing tax calc)
- Added: discount code validation
- TODO: implement stacking discounts
- Key insight: discounts apply pre-tax
```

## Best Practices

1. **Front-load important context** - Put critical info first
2. **Use hierarchical structure** - Allow skipping irrelevant sections
3. **Reference, don't repeat** - Point to files/lines instead of copying
4. **Prune aggressively** - Remove context that's no longer relevant
5. **Checkpoint regularly** - Save state to avoid reloading
