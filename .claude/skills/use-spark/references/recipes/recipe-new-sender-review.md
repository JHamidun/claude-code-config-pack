> **spark-recipe-new-sender-review** v1.0.0 · access level: triage · base skill: use-spark · source: spark-cli-skills 1.3.0 (Readdle, MIT) — Process GateKeeper's new sender queue: review, accept legitimate contacts, and block unwanted senders.

# Recipe: New Sender Review

Process Spark's GateKeeper queue of new senders. Review each, accept legitimate contacts, and block unwanted ones.

**Prerequisite:** Read the `use-spark` base skill for command reference and filter syntax.

**Access level required:** triage.

## Steps

### Step 1: Check the new senders queue

```bash
spark emails Inbox --new-senders
```

This shows emails from senders that GateKeeper has quarantined (explicit mode). The normal inbox view filters these out automatically.

### Step 2: Review each sender

For each new sender email, read the content:

```bash
spark thread <id>
```

Decide: is this a legitimate contact or unwanted mail?

### Step 3: Accept legitimate senders

```bash
spark contact-action acceptContact sender@company.com
```

This moves the sender past GateKeeper - their future emails appear in the normal inbox.

To accept an entire domain:

```bash
spark contact-action acceptDomain company.com
```

### Step 4: Block unwanted senders

```bash
spark contact-action blockContact spammer@example.com
```

To block an entire domain:

```bash
spark contact-action blockDomain example.com
```

### Step 5: Verify

```bash
spark emails Inbox --new-senders
```

Confirm the queue is empty or report what's left.

## Tips

- GateKeeper only shows new sender emails when `--new-senders` is used - they're filtered from the normal inbox view.
- When in doubt, accept the contact first. You can always block them later.
- `acceptDomain` is useful for legitimate companies with multiple sender addresses (support@, billing@, etc.).
- `blockDomain` is aggressive - use it for clearly spammy domains, not for individual unwanted senders.
- Run this recipe regularly (daily or every few days) so legitimate contacts don't wait too long in the queue.
- The new senders count appears at the top of the inbox output when there are queued items.
