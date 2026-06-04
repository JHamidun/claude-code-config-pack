# Workflow: Admin Tasks

> Административные задачи: оплаты, документы, заказы, подписки

## Keywords
`оплатить`, `заказать`, `подписать`, `документ`, `admin`, `pay`, `order`, `subscribe`, `cancel`

## Inputs
- **task**: описание задачи из Todoist
- **type**: payment | document | order | subscription | booking
- **urgency**: deadline-driven | flexible
- **amount**: если финансовое

## Steps

### 1. Parse Task Requirements
```
Extract:
- What exactly needs to be done
- Deadline (if any)
- Required information (account, credentials, etc.)
- Dependencies (need info from someone?)
```

### 2. Gather Required Information
```
Common needs:
- Login credentials
- Payment method
- Contact information
- Reference numbers
- Addresses
```

### 3. Execute by Type

#### Payment
```
1. Verify amount and recipient
2. Check payment method available
3. Execute payment
4. Save confirmation
5. Update budget tracking (if applicable)
6. Set reminder for recurring (if applicable)
```

#### Document
```
1. Identify document type
2. Gather required info
3. Fill/create document
4. Review for accuracy
5. Get signatures (if needed)
6. Submit/send
7. Save copy
```

#### Order
```
1. Confirm product/service needed
2. Compare options (if applicable)
3. Place order
4. Save confirmation
5. Track delivery
6. Create receipt task (if expense)
```

#### Subscription
```
1. Identify service
2. Choose plan
3. Set up payment
4. Configure settings
5. Set renewal reminder
6. Document in subscriptions tracker
```

#### Booking
```
1. Check availability
2. Confirm dates/times
3. Make reservation
4. Save confirmation
5. Add to calendar
6. Set reminder
```

### 4. Documentation
```
For each admin task:
- Save confirmation/receipt
- Update relevant tracker (expenses, subscriptions)
- Note any follow-up needed
```

### 5. Track Completion
```
Tool: Todoist
- Mark task done
- Create follow-up if needed (delivery, renewal)
- Update labels (expense, subscription, etc.)
```

## Quality Checks
- [ ] Task requirements understood
- [ ] All info gathered before action
- [ ] Confirmation saved
- [ ] Follow-up scheduled (if needed)
- [ ] Tracker updated (if applicable)

## Completion Criteria
- Action completed
- Confirmation/receipt saved
- Any follow-ups scheduled
- Todoist updated

## Time Estimate
- **Simple**: 5-10 minutes
- **With research**: 15-20 minutes
- **Complex**: 30+ minutes

## Common Admin Tasks

### Subscriptions Management
```
Tracking:
- Service name
- Cost
- Billing cycle
- Renewal date
- Payment method
- Cancellation terms

Actions:
- Review usage quarterly
- Cancel unused
- Negotiate renewal rates
```

### Expense Tracking
```
For each expense:
- Date
- Amount
- Category
- Receipt saved
- Reimbursable? (Y/N)
- Tax deductible? (Y/N)
```

### Document Types
```
Common:
- Contracts → Review, sign, save
- Invoices → Pay, save receipt
- Tax forms → Complete, submit
- Applications → Fill, submit
- Renewals → Process, save confirmation
```

## Automation Opportunities

### Recurring Tasks
```
Set up in Todoist:
- Monthly bill payments → recurring task
- Subscription renewals → annual reminder
- Document renewals → calendar reminder
- Tax deadlines → quarterly task
```

### Templates
```
For common admin:
- Create template in Todoist
- Use with quick-add
- Consistent tracking
```

## Integration Points

### Calendar
- Deadlines
- Appointments
- Renewal dates

### Email
- Confirmations
- Receipts
- Correspondence

### File Storage
- Receipts
- Contracts
- Important docs

## Notes
- Always save confirmations
- Set reminders for deadlines
- Batch similar admin tasks
- Review subscriptions quarterly
- Keep expense records organized
