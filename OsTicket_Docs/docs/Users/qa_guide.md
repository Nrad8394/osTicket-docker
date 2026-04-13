# QA Guide

The **QA role** is the decision gate between development completion and business validation.

---

## Primary Responsibilities

- Receive and review the developer release package
- Verify that the build/deployment artefacts are complete and testable
- Validate whether the implemented fix satisfies technical acceptance criteria
- Decide if development is complete for the submitted package
- Raise a QA failure report if validation fails
- Initiate and coordinate UAT if validation passes

---

## Typical Workflow

1. Confirm ticket is in **Released** (or equivalent ready-for-QA state)
2. Review package contents (version, deployment steps, rollback, evidence)
3. Execute QA checks in the test environment
4. Record findings and decision:
   - **Fail:** move ticket to **Failed QA**, attach failure report, return to developer
   - **Pass:** hand over to business/requester for UAT using agreed scenarios
5. Track UAT outcome and provide final QA recommendation for deployment

---

## QA Decision Checklist

- [ ] Package metadata is complete (ticket reference, version, environment)
- [ ] Deployment instructions are reproducible
- [ ] Rollback instructions are present and tested/validated
- [ ] Core functional scenarios pass
- [ ] No critical defects remain
- [ ] Evidence is attached (logs, screenshots, results)

---

## QA Failure Report Template

```text
Ticket Reference:
Release Version:
Environment Tested:
Tested By:
Date:

Result: FAIL

Failure Summary:
-

Defects Identified:
1.
2.

Reproduction Steps:
1.
2.

Evidence:
-

Required Rework:
-

Next Status: Failed QA
```

---

## UAT Handover (After QA Pass)

When QA passes, provide the requester/business representative with:

- Validated build/version information
- Scope of features/fixes to validate
- UAT script/reference ([UAT Process](../processes/uat.md))
- Known limitations/caveats (if any)
- Target timeline for sign-off

---

## Related Documents

- [Release Package](../processes/package.md)
- [User Acceptance Testing (UAT)](../processes/uat.md)
- [Resolution Report](../processes/report.md)
