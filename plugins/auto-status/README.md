# Auto Status on Allocation

osTicket plugin that updates a ticket's status automatically when it is
assigned or reassigned to an agent or team.

## Why

osTicket keeps assignment and status independent. Ticket filters only fire on
ticket *creation*, so reassignments don't trigger any status change. This
plugin hooks the `model.updated` signal so it catches every assignment change
— from the agent UI, ticket filters, the API, or other plugins — uniformly.

---

## Install

1. Copy this folder to `include/plugins/auto-status/`:
   ```
   include/plugins/auto-status/
     ├── plugin.php
     ├── autostatus.php
     └── config.php
   ```
2. **Admin Panel → Manage → Plugins → Add New Plugin.**
3. Install → Enable → open **Config**.

---

## Configuration — Workflow Rules

The plugin uses a rule engine. Rules are evaluated in order (Rule 1 first);
the **first enabled rule that matches wins**.

### Adding rules — no count to manage

The config form **auto-expands**: it always shows 3 empty rule slots below the
last filled rule. To add more rules, simply fill in the last empty slot and
save — three more empty slots will appear automatically. No need to set a
count or reload the page separately.

### Rule fields

Each rule has:

| Field | Description |
|-------|-------------|
| **Label** | Optional friendly name shown in the rule header |
| **Enable** | Must be ticked for the rule to fire |
| **Only if current status is** | Optional. Leave blank to match any status |
| **Assigned staff** | Optional. Match only when assigned to specific staff |
| **Assigned team** | Optional. Match only when assigned to a specific team |
| **Assignee role** | Optional. Match only when the assignee holds a specific role |
| **Set status to** | The target status when this rule matches |

Leave any filter field blank to match everything in that dimension.

### Example setup

| Rule | Trigger | Set status to |
|------|---------|---------------|
| Rule 1 | Any assignment, status = Open | `In Progress` |
| Rule 2 | Assigned to Support Team | `In Progress` |
| Rule 3 | Assigned to a specific escalation agent | `Escalated` |

Create custom statuses first under **Admin Panel → Manage → Ticket Statuses**
(state = Open).

---

## Diagnostics

Enable **Write debug log to `/tmp/autostatus-debug.log`** in the config to
trace rule evaluation. Disable this in production.

---

## How it works

- Connects to `Signal::connect('model.updated', …)` and
  `Signal::connect('object.edited', …)` in `bootstrap()`.
- On every model save, checks whether dirty fields include `staff_id` or
  `team_id`. If not, returns immediately — cheap no-op.
- Iterates enabled rules in order; applies the target status of the first
  matching rule.
- Skips when the ticket is not assigned after the change.
- Uses an in-memory re-entrancy flag (`_autostatus_in_progress`) to prevent
  `setStatus()` — which itself emits `model.updated` — from looping.
- Falls back to a direct DB update if `setStatus()` is blocked by role
  permissions on the current staff context.

---

## Test

1. Create a new ticket, leave it unassigned.
2. Assign it to an agent → status should flip to your configured target.
3. Reassign to a different agent or team → the matching rule's status applies.
4. Clear the assignment → status should not change.
5. If a rule has a "current status" filter, set the ticket to a status
   outside that filter and reassign — the rule should not fire.

---

## Notes / gotchas

- The `model.updated` signal passes `dirty` as `[field => oldValue]`. Rule
  evaluation uses the current (post-update) state of the ticket.
- If you also use ticket filters that set status on creation, those still run
  — this plugin only acts on assignment changes, so the two do not conflict.
- No core osTicket files are modified — survives upgrades.

