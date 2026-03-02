# ID Reservation Strategy

## Overview

To prevent conflicts between osTicket system defaults and seeded custom data, we use **reserved ID ranges** for all tables. This ensures the seeder never overwrites critical system records.

## ID Range Allocation

| Table | System IDs (Reserved) | Seeder IDs (Safe to Use) | Notes |
|-------|----------------------|--------------------------|-------|
| **ost_staff** | 1 | 2-999 | ID 1 = initial admin account from Docker .env |
| **ost_department** | 1-3 | 10-999 | IDs 1-3 = default departments |
| **ost_team** | 1 | 10-999 | ID 1 = default team |
| **ost_role** | 1-4 | 10-999 | IDs 1-4 = default roles (Admin, Manager, Agent, Guest) |
| **ost_sla** | 1 | 10-999 | ID 1 = default SLA |
| **ost_form** | 1-6 | 10-999 | IDs 1-6 = system forms (Contact, Ticket, Company, Org, Task, Status) |
| **ost_form_field** | 1-35 | 50-999 | IDs 1-35 = default form fields (Subject, Message, Priority, etc.) |
| **ost_list** | 1 | 10-999 | ID 1 = default list |
| **ost_help_topic** | 1-10 | 100-9999 | IDs 1-10 = default help topics |
| **ost_ticket_status** | 1-5 | 20-999 | IDs 1-5 = default statuses (Open, Resolved, Closed, Archived, Deleted) |
| **ost_filter** | 1 | 10-999 | ID 1 = default filter |

## Current Seeder Data Files

✅ **Fixed for Safe ID Ranges:**
- `staff.json` - Starts at ID 2 (skips admin account ID 1), dept_id and role_id references updated
- `form_fields.json` - Uses IDs 50-59 (avoids system fields 1-35)
- `departments.json` - Uses IDs 10-17 (avoids system defaults 1-3)
- `teams.json` - Uses IDs 10-16 (avoids system default 1)
- `roles.json` - Uses IDs 10-19 (avoids system defaults 1-4)
- `slas.json` - Uses IDs 10-19 (avoids system default 1)
- `filters.json` - Uses IDs 10-21 (avoids system default 1), dept_id and sla_id references updated
- `help_topics.py` - Generated IDs start at 100+ (SAFE), dept_id/team_id/sla_id routing updated

## Best Practices

### 1. Always Use Safe ID Ranges

```json
❌ BAD - Will overwrite system record:
{
  "id": 1,
  "name": "Custom Department"
}

✅ GOOD - Uses safe range:
{
  "id": 10,
  "name": "Custom Department"
}
```

### 2. Let Database Auto-Increment When Possible

For new records without ID conflicts, omit the ID and let MySQL auto-assign:

```json
✅ BEST - Auto-incremented:
{
  "name": "Custom Department",
  "manager_id": null
}
```

### 3. Use INSERT IGNORE for Full Safety

The seeder's `insert_ignore()` method will skip existing IDs:

```python
# Skips if ID already exists
self.insert_ignore(table='department', data={
    'id': 5,
    'name': 'Custom Dept'
})
```

### 4. Document Custom ID Ranges

When adding new seeders, document the ID range in this file AND in the seeder's docstring:

```python
"""
Seeder for Custom Workflows

Seeds into table: ost_workflow
ID Range: 100-999 (system uses 1-99)
"""
```

## Migration Checklist

When updating existing seeder data files:

- [ ] Check current database max ID: `SELECT MAX(id) FROM ost_table;`
- [ ] Update JSON file IDs to safe range (usually max_id + 50)
- [ ] Update sort orders if needed (match ID or use separate sequence)
- [ ] Test with `--mode partial` (INSERT IGNORE) first
- [ ] Verify no system records overwritten
- [ ] Document the new ID range in this file

## Troubleshooting

### Problem: "Duplicate entry" error

**Cause:** Trying to insert ID that already exists

**Solution:** 
```bash
# Find the max ID currently in use
docker exec osticket_db mysql -u osticket -p0sT1ck3tPass! osticket -e \
  "SELECT MAX(id) FROM ost_table_name;"

# Update your JSON file to use ID = max_id + 10 or higher
```

### Problem: Seeder reports "updated" but expected "inserted"

**Cause:** Record with that ID already exists, so ON DUPLICATE KEY UPDATE triggered

**Solution:** This is actually SAFE behavior - existing data preserved. If you want fresh inserts, use higher IDs.

### Problem: System form fields disappeared

**Cause:** Seeder JSON had `form_id` wrong or IDs 1-35 overwritten

**Solution:**
```bash
# Restore from backup
docker exec -i osticket_db mysql -u osticket -p0sT1ck3tPass! osticket < backup.sql
```

## Reference: System Default Records

### Staff (ost_staff)
- ID 1: Admin account (username from .env OST_ADMIN_USER)

### Departments (ost_department)  
- ID 1: Support (default)
- ID 2: Sales (if created during setup)
- ID 3: Maintenance (if created during setup)

### Forms (ost_form)
- ID 1: Contact Information (type=U for User)
- ID 2: Ticket Details (type=T for Ticket)
- ID 3: Company Information (type=C for Company)
- ID 4: Organization Information (type=O for Organization)
- ID 5: Task Details (type=A for tAsk)
- ID 6: Ticket Status Properties (type=L1)

### Form Fields (ost_form_field)
Form ID 1 (Contact Information):
- ID 20: Issue Summary (text)
- ID 21: Issue Details (thread)
- ID 22: Priority Level (priority)

Form ID 2 (Ticket Details):
- ID 23-30: Various system fields

**IMPORTANT:** IDs 1-35 are reserved for system fields. Custom fields must use ID 50+.

### Help Topics (ost_help_topic)
- ID 1: General Inquiry
- ID 2: Feedback
- IDs 3-10: Reserved for future system defaults

Custom help topics should use ID 100+ to be completely safe.

## Update History

- **2026-03-02**: Initial ID reservation strategy
- **2026-03-02**: Fixed staff.json (removed ID 1)
- **2026-03-02**: Fixed form_fields.json (changed IDs 1-10 to 50-59)
- **2026-03-02**: Fixed form_fields.py (removed hardcoded form_id=2 override)
- **2026-03-02**: Fixed departments.json (changed IDs 1-8 to 10-17)
- **2026-03-02**: Fixed teams.json (changed IDs 1-7 to 10-16)
- **2026-03-02**: Fixed roles.json (changed IDs 1-10 to 10-19)
- **2026-03-02**: Fixed slas.json (changed IDs 1-10 to 10-19)
- **2026-03-02**: Fixed staff.json foreign keys (updated all dept_id and role_id references to new ranges)
- **2026-03-02**: Fixed help_topics.py (updated all dept_id, team_id, sla_id references and validation ranges)
- **2026-03-02**: Fixed filters.json (changed IDs 1-12 to 10-21, updated dept_id and sla_id references)
