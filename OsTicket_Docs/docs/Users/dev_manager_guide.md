# DEV Manager Guide

This guide explains how the DEV Manager controls the development handoff, implementation planning, QA outcome, and release readiness.

## DEV Manager responsibilities

The DEV Manager becomes active when a ticket requires a system change.

Typical responsibilities include:

- Reviewing tickets escalated from support
- Confirming the issue is change-worthy and technically actionable
- Assigning work to the correct developer
- Tracking progress during implementation
- Coordinating QA outcome and release readiness
- Returning failed work for correction when QA does not pass

## Staff interface used by DEV Manager

![Staff open queue](../assets/screenshots/staff-open-queue.png)

![Ticket detail view](../assets/screenshots/staff-ticket-detail.png)

The DEV Manager uses the same ticket detail screen, especially:

- **Assign** to hand work to a developer
- **Post Internal Note** to capture technical direction
- **Change Status** to move the ticket through development states

## Access and permission baseline

- Authentication is email-based in this environment.
- DEV Manager roles should include permissions for assignment, department transfer, and status transitions.
- Confirm developer accounts have the minimum rights needed for internal notes and status updates.

## DEV Manager flow

1. Review the ticket after support escalation
2. Confirm the defect, enhancement, or change request is well described
3. Add internal notes for scope, dependencies, or release constraints
4. Assign the ticket to the responsible developer
5. Update the status to the appropriate development state
6. Review feedback after implementation
7. Coordinate QA
8. Return failed work to development or approve the path to deployment

## Suggested status usage

The live system contains these implementation-related states:

- **In Development** — development work has been approved or initiated
- **Developers Assigned** — a named developer or developer group has ownership
- **Released** — implementation is complete and ready for QA/UAT review
- **Failed QA** — QA did not accept the release and rework is required
- **Deployed** — the approved fix has been promoted

## Developer assignment and workload balancing

When assigning developers, evaluate:

- Domain fit (BI, Customs, LMT/MST)
- Current workload and SLA risk
- Dependency expertise (database, integration, frontend)

Good practice:

- Put acceptance criteria in an internal note before assignment.
- Call out non-functional requirements (performance, security, audit logging).

## What good DEV Manager notes should include

Use internal notes to record:

- Root cause summary
- Expected fix approach
- Systems or modules affected
- Dependencies and testing expectations
- Release package or deployment window notes

## QA gate expectations

Before approving **Released** status, verify:

- Release package is complete and deployable
- Test instructions are reproducible
- Rollback path is documented

If QA fails, return to development with:

- Exact failed scenario
- Environment and data set used
- Logs/evidence references
- Target date for rework

## Example scenarios for DEV routing

| Scenario | Likely owner path |
|---|---|
| SAP iSupport report logic error | BI or application development |
| iCMS clearance page runtime issue | Customs application support/development |
| iTax PAYE submission defect | LMT/MST application development |
| Enhancement request for new process support | Development after BAS approval |

## DEV Manager checklist

- Confirm the change request is actionable
- Assign to the correct developer quickly
- Keep technical direction in internal notes
- Enforce QA feedback handling
- Approve deployment only when the ticket record is complete
- Balance developer workload across priority queues
- Enforce release package and rollback quality
