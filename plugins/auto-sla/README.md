# Auto SLA by Type & Severity

osTicket plugin that automatically assigns an **SLA Plan** to a ticket based on
two custom fields — **Type** and **Severity** — from your own Custom Lists.

Both the list of types and the list of severities are fully configurable in the
plugin's config page; nothing is hardcoded.

e.g. _Minor Bug → 2 weeks_, _Major Enhancement → 6 months_.

---

## Prerequisites — do these first

### 1. Create the SLA Plans

**Admin Panel → Manage → SLA Plans → Add New SLA Plan.**

Grace Period is in **hours**. A typical starting matrix:

| Type \ Severity  | Major           | Medium          | Minor            |
|------------------|-----------------|-----------------|------------------|
| **Bug**          | 24 h (1 day)    | 120 h (5 days)  | 336 h (2 weeks)  |
| **Enhancement**  | 4 320 h (6 mo)  | 2 160 h (3 mo)  | 1 080 h (~6 wks) |
| **New System**   | 8 760 h (12 mo) | 4 320 h (6 mo)  | 2 160 h (3 mo)   |

Name them clearly (e.g. `Bug - Minor (2w)`, `Enhancement - Major (6m)`) so
they are easy to pick in the config dropdowns.

### 2. Add the two custom fields to the ticket form

**Admin Panel → Manage → Custom Lists** — create two lists:

| List Name | Choices                               |
|-----------|---------------------------------------|
| Type      | `Enhancement`, `Bug`, `New System`    |
| Severity  | `Major`, `Medium`, `Minor`            |

Then **Admin Panel → Manage → Forms → Ticket Details → Add New Field** (twice):

| Label    | Type    | Variable   | Source list |
|----------|---------|------------|-------------|
| Type     | Choices | `type`     | Type list   |
| Severity | Choices | `severity` | Severity list |

The **Variable** is what the plugin reads — it must match the value you enter
in the plugin config.

---

## Install

1. Copy this folder to `include/plugins/auto-sla/`:
   ```
   include/plugins/auto-sla/
     ├── plugin.php
     ├── autosla.php
     └── config.php
   ```
2. **Admin Panel → Manage → Plugins → Add New Plugin.**
3. Install → Enable → open **Config**.

---

## Configuration

| Field | Description |
|-------|-------------|
| **Custom field variable: Type** | Variable name of the Type field (default: `type`) |
| **Custom field variable: Severity** | Variable name of the Severity field (default: `severity`) |
| **Type values** | Comma-separated list of your Type choices — must match your Custom List labels exactly (default: `Enhancement,Bug,New System`) |
| **Severity values** | Comma-separated list of your Severity choices (default: `Major,Medium,Minor`) |
| **SLA Matrix** | For each Type × Severity combination, pick the SLA Plan to assign |
| **Overwrite an SLA that was already set** | If off (default), tickets with an SLA already set are left alone |
| **Post internal note when SLA is set** | Recommended on — creates an audit trail |
| **Write debug log** | Enable only when diagnosing issues |

### Changing your lists later

If you rename or add choices to your Custom Lists, update **Type values** /
**Severity values** in the plugin config to match, then re-map any new
combinations in the matrix. Old keys are orphaned (ignored) — they do not
cause errors.

---

## How it works

- Hooks `ticket.created` to set the SLA on new tickets.
- Hooks `model.updated` on `Ticket` to re-evaluate when the ticket is edited
  (covers an agent changing Type or Severity after creation).
- Reads field values via `Ticket::getAnswer()` (keyed by lowercase variable
  name), with a fallback that scans `loadDynamicData()` directly.
- Compares the raw field value against the admin-configured list using
  **exact case-insensitive matching** then **slug matching**
  (spaces ↔ underscores).
- Uses `Ticket::setSLAId()` — the proper osTicket 1.16+ API — to assign the
  SLA; osTicket recalculates the due date automatically from the grace period.
- Re-entrancy flag (`_autosla_in_progress`) prevents the `save()` call from
  looping `model.updated` back into the handler.

---

## Test

1. Create a ticket, set Type = `Bug`, Severity = `Minor` → SLA should become
   your "Bug - Minor" plan and an internal note should appear.
2. Edit the ticket, change Severity to `Major` → SLA should flip to
   "Bug - Major".
3. Manually override the SLA on a ticket, then change Severity with
   **Overwrite off** → SLA should *not* change.
4. Turn **Overwrite on**, repeat step 3 → SLA *should* change.
5. Create a ticket with an unmapped combo → no SLA change, no error.

---

## Notes / gotchas

- **SLA table uses a `flags` bitmask** — raw SQL `WHERE isactive=1` does not
  work in osTicket 1.16+. This plugin uses the ORM helper `SLA::getSLAs()`
  which reads flags correctly.
- The plugin does **not** create SLA Plans — it only assigns from existing
  ones.
- Plays well alongside **Auto Status on Allocation** — they hook different
  lifecycle moments.

