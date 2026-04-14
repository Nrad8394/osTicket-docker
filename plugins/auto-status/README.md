# Auto Status on Allocation

osTicket plugin that updates a ticket's status automatically when it is
assigned (allocated) or reassigned.

## Why

osTicket keeps assignment and status independent. Filters only fire on ticket
*creation*, so reassignments don't trigger any status change. This plugin
hooks the `model.updated` signal so it catches every assignment change —
from the agent UI, ticket filters, the API, or other plugins — uniformly.

## Install

1. Copy this folder to `include/plugins/auto-status/` on your osTicket server:
   ```
   include/plugins/auto-status/
     ├── plugin.php
     ├── autostatus.php
     └── config.php
   ```
2. In the staff control panel: **Admin Panel → Manage → Plugins → Add New Plugin**.
   osTicket scans `include/plugins/` and the new plugin appears in the list.
3. Install it, then click into it and **Enable**.
4. Open its **Config** tab and set:
   - **Status on first allocation** — e.g. `In Progress`
   - **Status on reassignment** — e.g. `In Progress` or a custom `Reassigned`
   - **Only change if current status is one of** — optional allow-list, e.g.
     `Open, Pending`. Leave blank to apply regardless.
   - **Post internal note on status change** — recommended on, for audit.

If you want a distinct `Reassigned` status, create it first under
**Admin Panel → Manage → Ticket Statuses** (state = Open).

## How it works

- Connects to `Signal::connect('model.updated', ...)` in `bootstrap()`.
- On every model save, checks whether the dirty fields include `staff_id` or
  `team_id`. If not, returns immediately — cheap.
- Determines whether the previous state was unassigned (first allocation) or
  already assigned (reassignment), and picks the configured target status.
- Skips when the new state is unassigned (someone clearing the assignment).
- Uses an in-memory re-entrancy flag (`_autostatus_in_progress`) because
  `setStatus()` itself emits `model.updated` and would otherwise loop.
- Wraps `setStatus()` in try/catch so the parent assignment flow is never
  broken by a status-change error.

## Test

1. Create a new ticket, leave it unassigned.
2. Assign it to an agent → status should flip to your "first allocation"
   status, and (if enabled) an internal note is posted.
3. Reassign to a different agent or team → status should flip to your
   "reassignment" status.
4. Clear the assignment → status should not change.
5. If you set an allow-list, change the ticket status to something outside
   the list and reassign — status should *not* change.

## Notes / gotchas

- The `model.updated` signal passes `dirty` as `[field => oldValue]`. We rely
  on key presence, not value, to detect the change.
- If you also use ticket filters that set status on creation, those still run
  — this plugin only acts on assignment changes, so the two don't fight.
- Tested mentally against osTicket 1.18 / 1.17 internals. If your fork has
  patched `Ticket::assign()` heavily, double-check that it still calls the
  base save path that emits `model.updated`.
- Survives osTicket upgrades — no core files are modified.
