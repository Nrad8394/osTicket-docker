# User Acceptance Testing (UAT)

**UAT** confirms that the delivered fix/change works for business users in realistic scenarios.

---

## Purpose

UAT verifies:

- Business process outcomes, not only technical completion
- The issue is truly resolved for end users
- No critical regression is introduced in related flows

---

## Who Performs It

**Primary owner:** Requester / Business representative  
**QA role:** Gatekeeper and coordinator (authorizes UAT only after QA pass)  
**Supporting roles:** Support Analyst, DEV Manager, Developer

---

## When It Is Performed

Execute UAT after:

1. QA validates the release package and marks the build as **QA Pass**
2. Release package instructions are available
3. Test data and access are ready

---

## UAT Test Script Template

| Test Case ID | Scenario | Steps | Expected Result | Actual Result | Status (Pass/Fail) | Evidence |
|---|---|---|---|---|---|---|
| UAT-01 |  |  |  |  |  |  |
| UAT-02 |  |  |  |  |  |  |

---

## UAT Sign-off Template

```text
Ticket Reference:
UAT Environment:
Executed By:
Execution Date:

Summary Result: PASS / FAIL

Findings:
- 

Decision:
- [ ] Accept and proceed to deployment
- [ ] Reject and return for rework

Business Sign-off Name:
Signature/Approval Ref:
Date:
```

---

## Pass/Fail Decision Rules

- **PASS:** Core business scenarios succeed, no critical defects remain.
- **FAIL:** Any critical business path fails, data integrity concerns exist, or key requirements are unmet.

If UAT fails, update the ticket and return it for corrective development with QA tracking the re-validation cycle.

---

## Output to Next Stage

Support Analyst prepares a closure [Report](report.md) after QA/UAT outcome and deployment status are confirmed.