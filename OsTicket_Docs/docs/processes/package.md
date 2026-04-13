# Release Package

A **Release Package** is the delivery bundle prepared by the developer for QA and deployment.

---

## Purpose

The package provides everything required to:

- Deploy the change consistently
- Validate it in QA/UAT
- Trace exactly what was delivered

---

## Who Creates It

**Primary owner:** Developer  
**Reviewers:** DEV Manager, QA

---

## When It Is Created

Create the package when implementation is complete and the ticket is ready to move to **Released**.

---

## Package Contents Checklist

| Item | Required | Notes |
|---|---|---|
| Ticket reference | Yes | Ticket number and title |
| Version/build number | Yes | Semantic or release train version |
| Source changes summary | Yes | Modules/files changed |
| Deployment steps | Yes | Ordered and environment specific |
| Configuration changes | If applicable | Env vars, flags, cron, etc. |
| Database scripts | If applicable | Forward + rollback scripts |
| Test evidence | Yes | Unit/integration results |
| Known limitations | If applicable | Deferred issues or caveats |
| Rollback instructions | Yes | Step-by-step recovery |

---

## Package Template

```text
Ticket Reference:
Release Version:
Environment Target:

Components Changed:
- 

Deployment Steps:
1.
2.
3.

Database Changes:
- Forward:
- Rollback:

Validation Steps:
1.
2.

Known Limitations:

Rollback Procedure:
1.
2.
```

---

## Naming Convention (Recommended)

`TICKETNO_SYSTEM_YYYYMMDD_vX.Y.Z`

Example: `1047_ITAX_20260413_v1.8.4`

---

## Output to Next Stage

The requester executes structured validation using the [UAT](uat.md) artefact.