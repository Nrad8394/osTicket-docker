# Phase 2: Seeding Implementation - Complete Guide

**Status:** ✅ COMPLETE (13 files created)  
**Last Updated:** 2025-01-16  
**RFC Reference:** S2025_195201

## Overview

Phase 2 implements the complete seeding system for osTicket database initialization. This includes 11 seeder classes, corresponding JSON data files, orchestration logic, and support infrastructure.

## Architecture

### Seeding Pipeline

```
main.py (orchestrator)
    ↓
    ├── RoleSeeder → roles.json (10 roles)
    ├── DepartmentSeeder → departments.json (8 depts)
    ├── SLASeeder → slas.json (10 SLAs)
    ├── TeamSeeder → teams.json (7 teams)
    ├── StaffSeeder → staff.json (12 staff) [depends: roles, departments]
    ├── ListSeeder → lists.json (5 lists)
    ├── ListItemSeeder → list_items.json (150+ items) [depends: lists]
    ├── FormFieldSeeder → form_fields.json (10 fields) [depends: lists]
    ├── HelpTopicSeeder → help_topics.json [depends: depts, teams, slas] Phase1
    ├── StatusSeeder → statuses.json (16 statuses)
    ├── FilterSeeder → filters.json (12 filters) [depends: help_topics]
    ├── SequenceSeeder → sequences.json (2 sequences)
    └── DemoTicketSeeder → demo_tickets.json [optional, depends: all above]
```

### Seeding Order (Non-Negotiable)

The seeding order is critical due to foreign key dependencies:

1. **Roles** (no dependencies)
2. **Departments** (no dependencies)
3. **SLAs** (no dependencies)
4. **Teams** (no dependencies)
5. **Staff** (depends: roles, departments)
6. **Lists** (no dependencies)
7. **List Items** (depends: lists)
8. **Form Fields** (depends: lists)
9. **Help Topics** (depends: departments, teams, slas) *Phase 1*
10. **Ticket Statuses** (no dependencies)
11. **Filters** (depends: help_topics)
12. **Sequences** (no dependencies)
13. **Demo Tickets** (optional; depends: staff, departments, help_topics)

## Files Created

### Seeder Classes (seeder/seeders/)

| File | Class | Purpose | Dependencies |
|------|-------|---------|--------------|
| `roles.py` | `RoleSeeder` | Load roles with permissions | None |
| `departments.py` | `DepartmentSeeder` | Load departments | None |
| `slas.py` | `SLASeeder` | Load SLA plans | None |
| `teams.py` | `TeamSeeder` | Load teams | None |
| `staff.py` | `StaffSeeder` | Load staff with password hashing | roles, departments |
| `lists.py` | `ListSeeder` | Load custom lists | None |
| `list_items.py` | `ListItemSeeder` | Load dropdown items (optimized bulk) | lists |
| `form_fields.py` | `FormFieldSeeder` | Load form fields with JSON config | lists |
| `statuses.py` | `StatusSeeder` | Load ticket statuses | None |
| `filters.py` | `FilterSeeder` | Load auto-assignment filters | help_topics |
| `sequences.py` | `SequenceSeeder` | Load ticket numbering patterns | None |
| `demo_tickets.py` | `DemoTicketSeeder` | Load demo tickets (optional) | All above |
| `__init__.py` | *Package* | Imports all seeders | - |

### Data Files (seeder/data/)

| File | Records | Purpose |
|------|---------|---------|
| `roles.json` | 10 | Role definitions with permission matrices |
| `departments.json` | 8 | Department definitions |
| `slas.json` | 10 | SLA plans with response times |
| `teams.json` | 7 | Team definitions |
| `staff.json` | 12 | Staff accounts with passwords |
| `lists.json` | 5 | Custom dropdown lists |
| `list_items.json` | 150+ | Dropdown items for 5 lists |
| `form_fields.json` | 10 | Ticket form fields with JSON config |
| `statuses.json` | 16 | Custom ticket workflow statuses |
| `filters.json` | 12 | Auto-assignment filter rules |
| `sequences.json` | 2 | Ticket numbering patterns |
| `demo_tickets.json` | 5 | Demo tickets for UAT |

### Support Infrastructure

| File | Purpose |
|------|---------|
| `main.py` | Master orchestration script |
| `connection.py` | Database connection pooling |
| `utils/logger.py` | Logging configuration |
| `validators/schema_validation.py` | Database schema validation |

## Seeder Details

### RoleSeeder (roles.py)

Loads 10 roles with permission hierarchies:
- Admin, Senior Agent, Agent, Team Lead, Manager
- Analyst, Technician, Support Specialist, Supervisor, Guest

**Data Structure:**
```json
{
  "id": 1,
  "name": "Admin",
  "permissions": {
    "tickets": {"view": 1, "create": 1, ...},
    ...
  }
}
```

**Validation:**
- `id` and `name` required
- Permissions serialized to JSON

**Usage:** `python seeder/seeders/roles.py`

---

### DepartmentSeeder (departments.py)

Loads 8 departments:
- BAS (Business Application Services)
- BSD (Business Systems Development)
- QA (Quality Assurance)
- SA&DM (Systems & Data Management)
- I&O (Infrastructure & Operations)
- S&C (Security & Compliance)
- TS (Technical Support)
- Service Management

**Validation:**
- `id` and `name` required
- No foreign key dependencies

**Usage:** `python seeder/seeders/departments.py`

---

### SLASeeder (slas.py)

Loads 10 SLA plans with response times:
- Critical: 1hr, 4hr, 8hr
- High: 4hr, 8hr, 12hr
- Medium: 12hr, 24hr
- Low: 24hr, 48hr

**Data Structure:**
```json
{
  "id": 1,
  "name": "Critical - 1 Hour",
  "grace_period": 3600
}
```

**Validation:**
- `grace_period` in seconds (accepts int or string)

**Usage:** `python seeder/seeders/slas.py`

---

### TeamSeeder (teams.py)

Loads 7 teams:
- iTax, iCMS, iBid, iSCAN, WIMS, Database, Infrastructure

**Validation:**
- `id` and `name` required
- No dependencies

**Usage:** `python seeder/seeders/teams.py`

---

### StaffSeeder (staff.py) ⭐ PASSWORD HASHING

Loads 12 staff accounts with **bcrypt password hashing**.

**Critical Features:**
- Uses `passlib CryptContext(schemes=["bcrypt"], rounds=12)`
- Hashes `temp_password` field before insert
- Validates foreign keys: `role_id` → ost_role, `dept_id` → ost_department
- All passwords: "InitialPass123!" (must be changed on first login)

**Data Structure:**
```json
{
  "id": 1,
  "name": "Admin",
  "email": "admin@example.com",
  "username": "sadmin",
  "temp_password": "InitialPass123!",
  "role_id": 1,
  "dept_id": 1
}
```

**Staff Accounts:**
- admin (sadmin), jsmith, mjohnson, rdavis, landerson
- mbrown, jwilson, dmartinez, staylor, jgarcia, prodriguez, tmoore

**Validation:**
- FK: role_id ∈ [1-10]
- FK: dept_id ∈ [1-8]
- Hashes password with bcrypt

**Usage:** `python seeder/seeders/staff.py`

---

### ListSeeder (lists.py)

Loads 5 custom dropdown lists:
1. Priority Levels
2. Impact Levels
3. Urgency Levels
4. System Categories
5. Issue Types

**Validation:**
- `id` and `name` required
- No dependencies

**Usage:** `python seeder/seeders/lists.py`

---

### ListItemSeeder (list_items.py) ⭐ BULK OPTIMIZATION

Loads 150+ dropdown items with **bulk insert optimization**.

**Critical Features:**
- Uses `bulk_insert_ignore()` for batch operations (150+ records)
- Validates all `list_id` references before bulk insert
- Optimized for large datasets

**Data Structure:**
```json
{
  "id": 1,
  "list_id": 1,
  "value": "Critical",
  "sort_order": 1
}
```

**Items by List:**
- Priority Levels (list_id=1): 30+ items
- Impact Levels (list_id=2): 30+ items
- Urgency Levels (list_id=3): 30+ items
- System Categories (list_id=4): 30+ items
- Issue Types (list_id=5): 30+ items

**Validation:**
- FK: list_id → ost_list

**Usage:** `python seeder/seeders/list_items.py`

---

### FormFieldSeeder (form_fields.py) ⭐⭐ JSON CONFIGURATION

Loads 10 custom form fields with **JSON configuration**.

**Critical Features:**
- `configuration` column stores JSON dict
- Dropdown fields must reference `list_id`
- Enforces `form_id=2` (Ticket Details form)
- Supports: text, textarea, dropdown, date, checkbox, radio, file, phone, email, url

**Data Structure:**
```json
{
  "id": 1,
  "form_id": 2,
  "label": "Priority",
  "type": "dropdown",
  "configuration": {
    "list_id": 1,
    "required": true,
    "default": "Medium"
  }
}
```

**Fields:**
1. Priority (dropdown → list_id=1)
2. Impact (dropdown → list_id=2)
3. Urgency (dropdown → list_id=3)
4. System Category (dropdown → list_id=4)
5. Issue Type (dropdown → list_id=5)
6. Description (textarea)
7. Steps to Reproduce (textarea)
8. Expected Result (text)
9. Actual Result (text)
10. Attachments (file)

**Validation:**
- Dropdowns must have `list_id`
- JSON serialization of `configuration`
- form_id always = 2

**Usage:** `python seeder/seeders/form_fields.py`

---

### StatusSeeder (statuses.py)

Loads 16 custom ticket statuses with workflow states.

**Data Structure:**
```json
{
  "id": 1,
  "name": "New",
  "state": "open",
  "color": "#3498db",
  "icon": "icon-file"
}
```

**Statuses:**
Open: New, Assigned, In Progress, On Hold, Waiting, Pending Review, Escalated, Info Needed  
Closed: Ready for Closure, Resolved, Closed, Not a Bug, Duplicate, Won't Fix, Unable to Reproduce, Reopened

**Validation:**
- `state` must be: open, closed, or resolved

**Usage:** `python seeder/seeders/statuses.py`

---

### FilterSeeder (filters.py) ⭐⭐ COMPLEX JSON

Loads 12 auto-assignment filter rules with **complex JSON** rule matching.

**Critical Features:**
- `rule_match`: Array of conditions with operator (AND/OR)
- `action_data`: Assignment targets (dept_id, sla_id, priority, etc.)
- Validates `help_topic_id` in rule conditions

**Data Structure:**
```json
{
  "id": 1,
  "name": "Route Password Resets to TS",
  "rule_match": {
    "operator": "AND",
    "conditions": [
      {"field": "help_topic_id", "operator": "=", "value": 100}
    ]
  },
  "action_data": {
    "dept_id": 7,
    "sla_id": 2,
    "priority": "Normal"
  }
}
```

**Filters:**
1. Route Password Resets to TS
2. Route System Outages to I&O
3. Route Database Issues to SA&DM
4. Route iTax Issues to BAS
5. Route Security Issues to S&C
6. Critical Severity → SLA1
7. High Severity → SLA2
8. Route Development Issues to BSD
9. Route Testing Issues to QA
10. Route iCMS Issues to BAS
11. Block Spam - Close Immediately
12. Override Low Priority to Medium

**Validation:**
- rule_match structure and operators
- action_data format
- JSON serialization

**Usage:** `python seeder/seeders/filters.py`

---

### SequenceSeeder (sequences.py)

Loads ticket numbering patterns.

**Data Structure:**
```json
{
  "id": 1,
  "name": "Default Ticket Number",
  "pattern": "KRA-%Y%M-{num}"
}
```

**Patterns:**
1. Default: "KRA-%Y%M-{num}" → KRA-202501-001
2. Simple: "{num}" → 1, 2, 3

**Validation:**
- Pattern must contain `{num}` placeholder

**Usage:** `python seeder/seeders/sequences.py`

---

### DemoTicketSeeder (demo_tickets.py)

Loads 5 demo tickets for UAT and testing (optional).

**Data Structure:**
```json
{
  "id": 1,
  "number": "KRA-202501-001",
  "email": "john.doe@example.com",
  "dept_id": 1,
  "staff_id": 2,
  "topic_id": 100,
  "priority": "High",
  "subject": "Demo Ticket: ...",
  "description": "..."
}
```

**Demo Tickets:**
1. iTax Login Issue (Critical)
2. Database Performance (High)
3. System Outage (Critical)
4. UI Enhancement (Low)
5. Data Sync Error (High)

**Validation:**
- FK: staff_id, dept_id, topic_id

**Usage:** `python seeder/seeders/demo_tickets.py` or via main.py --demo

---

## Orchestration

### main.py

Master orchestration script that executes all seeders in dependency order.

**Features:**
- Dependency validation
- Translation management
- Error handling with critical vs. non-critical seeders
- Progress tracking and reporting
- Logging to both console and file

**Usage:**
```bash
# Run all seeders (no demo)
python seeder/main.py

# Run all seeders including demo
python seeder/main.py --demo

# Use custom config
python seeder/main.py --config /path/to/config.yaml --demo
```

**Output:**
- Console: Real-time progress with ✓/✗ indicators
- File: Detailed logs in `seeder/logs/main.log`
- Summary: Total records inserted/updated, duration, errors

---

## Support Infrastructure

### connection.py

Database connection pooling with transaction management.

**Classes:**
- `DatabaseConnection`: Connection wrapper with pooling
- `ConnectionContext`: Context manager for transactions

**Features:**
- Connection pooling (configurable size)
- Transaction management
- Repeated statements

**Usage:**
```python
from connection import DatabaseConnection, ConnectionContext

# Initialize pool
DatabaseConnection.initialize_pool(config)

# Get connection
with DatabaseConnection.get_connection() as conn:
    affected = conn.execute("INSERT INTO ost_role VALUES ...", params)
    conn.commit()

# Or with context manager
with ConnectionContext() as conn:
    rows = conn.fetch_all("SELECT * FROM ost_role")
    # Auto-commits on exit if no exception
```

---

### utils/logger.py

Centralized logging setup.

**Usage:**
```python
from utils import get_logger

logger = get_logger(__name__)
logger.info("Seeding started")
logger.error("Error occurred")
```

---

### validators/schema_validation.py

Database schema validation.

**Classes:**
- `SchemaValidator`: Validates osTicket schema

**Features:**
- Validates table existence
- Checks expected columns
- Validates foreign key constraints
- Pre-seeding state snapshot

**Usage:**
```python
from validators import SchemaValidator

validator = SchemaValidator(connection)
if validator.validate_schema():
    pre_state = validator.get_pre_seeding_state()
```

---

## Quick Start

### 1. Configure Database

Edit `seeder/config.yaml`:
```yaml
database:
  host: localhost
  user: root
  password: password
  database: osticket
```

### 2. Run Seeding

```bash
cd seeder/
python main.py --demo
```

### 3. Verify

```bash
# Check logs
tail -f logs/main.log

# Query database
mysql -u root -p osticket <<EOF
SELECT 'Roles' as table, COUNT(*) FROM ost_role
UNION ALL
SELECT 'Departments', COUNT(*) FROM ost_department
UNION ALL
SELECT 'Staff', COUNT(*) FROM ost_staff
-- etc.
EOF
```

---

## Testing

### Unit Testing

Test individual seeders:
```bash
python seeder/seeders/roles.py
python seeder/seeders/staff.py
python seeder/seeders/list_items.py
```

### Idempotency Testing

Run twice on same database:
```bash
python seeder/main.py
python seeder/main.py
```

Result: Same row counts (idempotent operations)

### Integration Testing

```bash
python seeder/main.py --demo
# Then check:
# - All 12 seeders completed
# - Total records inserted/updated correct
# - No FK constraint violations
# - Demo tickets created (optional)
```

---

## Data Specifications

All data sourced from **RFC S2025_195201**:

| Section | Content | File |
|---------|---------|------|
| 3.2 | Departments | departments.json |
| 4.2 | SLAs | slas.json |
| 5.2 | Teams | teams.json |
| 6.2 | User Matrix (Roles) | roles.json |
| 6.3 | Staff Accounts | staff.json |
| 7.2 | Custom Statuses | statuses.json |
| 8 | Custom Lists | lists.json, list_items.json |
| 8.1-8.6 | Dropdown Items | list_items.json |
| 9.2 | Form Fields | form_fields.json |
| 11.2-11.3 | Auto-Assignment Rules | filters.json |
| 12.2 | Ticket Numbering | sequences.json |

---

## Database Schema

### Tables Seeded

- `ost_role` (roles)
- `ost_department` (departments)
- `ost_sla` (slas)
- `ost_team` (teams)
- `ost_staff` (staff)
- `ost_list` (lists)
- `ost_list_items` (list items)
- `ost_form_field` (form fields)
- `ost_help_topic` (help topics) *Phase 1*
- `ost_ticket_status` (statuses)
- `ost_filter` (filters)
- `ost_sequence` (sequences)
- `ost_ticket` (demo tickets, optional)

### Foreign Key Dependencies

```
ost_staff.role_id → ost_role.id
ost_staff.dept_id → ost_department.id
ost_list_items.list_id → ost_list.id
ost_form_field.list_id → ost_list.id (for dropdowns)
ost_help_topic.dept_id → ost_department.id
ost_filter.help_topic_id → ost_help_topic.id
```

---

## Error Handling

### Critical vs. Non-Critical

**Critical Seeders** (stop on failure):
- Roles, Departments, SLAs, Teams, Staff, Lists, List Items, Form Fields, Help Topics, Statuses, Sequences

**Non-Critical Seeders** (skip on failure):
- Filters, Demo Tickets

### Rollback on Error

If any critical seeder fails:
1. Current transaction rolled back
2. Remaining seeders skipped
3. Summary reported
4. Exit code: 1

---

## Performance Metrics

Expected seeding times (first run):

| Seeder | Time | Records |
|--------|------|---------|
| Roles | <1s | 10 |
| Departments | <1s | 8 |
| SLAs | <1s | 10 |
| Teams | <1s | 7 |
| Staff | 2-3s | 12 (bcrypt hashing) |
| Lists | <1s | 5 |
| List Items | 3-5s | 150+ (bulk insert) |
| Form Fields | <1s | 10 |
| Help Topics | <1s | varies |
| Statuses | <1s | 16 |
| Filters | <1s | 12 |
| Sequences | <1s | 2 |
| **Total** | **~10-15s** | **~250+ records** |

---

## Troubleshooting

### Connection Failed
```
Error: Failed to get connection from pool
Solution: Check config.yaml database credentials
```

### FK Constraint Violation
```
Error: Foreign key constraint fails
Solution: Ensure parent rows created first (seeding order)
```

### Duplicate Key Error
```
Error: Duplicate entry for key 'id'
Solution: Clear tables and re-run, or use --idempotent flag
```

### Schema Validation Failed
```
Error: Table ost_role does not exist
Solution: Ensure osTicket installed and database initialized
```

---

## Next Steps (Phase 3)

- [ ] Create comprehensive test suite (unit, integration, idempotency)
- [ ] Implement backup/restore utilities
- [ ] Create migration tools for existing data
- [ ] Build progress tracking and resumption
- [ ] Document rollback procedures

---

## References

- RFC S2025_195201: osTicket Seeding & Implementation
- BaseSeeder (Phase 1): seeder/base.py
- Configuration: seeder/config.py
- Database Schema: osTicket v1.18.3

---

**Built with ❤️ for osTicket Implementation**
