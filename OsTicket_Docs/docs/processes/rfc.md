# Request for Change (RFC)

An **RFC** documents the approved technical approach for implementing a ticket that requires a system change.

---

## Purpose

The RFC ensures all stakeholders agree on:

- What is changing
- Why the change is needed
- Risks and dependencies
- Rollback and deployment approach

---

## Who Creates It

**Primary owner:** DEV Manager  
**Contributors:** Support Analyst, Developer, QA (as needed)

---

## When It Is Created

Create the RFC after:

1. The issue is validated as a real defect/enhancement
2. BAS/Support agrees change is required
3. The ticket is moved into the development workflow (for example **In Development**)

---

## RFC Minimum Content

| Section | Description |
|---|---|
| **Ticket Reference** | Ticket number and title |
| **Problem Summary** | Short restatement of the issue |
| **Scope** | In scope / out of scope |
| **Proposed Solution** | Technical approach and affected components |
| **Impact Analysis** | Business, data, security, and operational impact |
| **Dependencies** | Systems, teams, windows, approvals |
| **Risk Assessment** | Key risks and mitigations |
| **Test Strategy** | Unit, integration, and UAT expectations |
| **Rollback Plan** | How to safely back out |
| **Approvals** | DEV Manager and business approval records |

---

## RFC Template

```text
Ticket Reference:
Problem Summary:

Scope:
- In scope:
- Out of scope:

Proposed Solution:

Impact Analysis:

Dependencies:

Risk Assessment:
- Risk:
  Mitigation:

Test Strategy:

Rollback Plan:

Approvals:
- DEV Manager:
- Business Owner:
- Date:
```

---

## Example (Summary)

**Ticket:** #1047 - iTax PAYE submission missing e-slip  
**Solution:** Fix post-submission event handler and ensure obligation write-back transaction commits successfully.  
**Risk:** Incorrect tax posting sequence if deployment script order is wrong.  
**Rollback:** Revert release package and restore previous stored procedure package version.

---

## Output to Next Stage

Once implementation is complete, the developer prepares the [Package](package.md) artefact.