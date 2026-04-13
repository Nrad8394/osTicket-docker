# Developer Guide

This guide explains what the developer must do after a ticket enters the development path.

## Developer responsibilities

The developer is responsible for implementing and documenting the technical fix.

That includes:

- Reviewing the ticket thread and internal notes carefully
- Confirming the expected outcome before making changes
- Implementing the fix or enhancement
- Recording useful technical notes for QA and support
- Returning the ticket ready for QA or release review
- Supporting rework if QA fails

## Ticket detail view used by developers

![Ticket detail view](../assets/screenshots/staff-ticket-detail.png)

Developers usually work from the ticket detail page and use:

- **Post Internal Note** for technical implementation details
- **Post Reply** only when a user-facing update is required through support workflow
- **Change Status** to reflect implementation progress

## Authentication note

- Staff access in this environment is email-based.
- Ensure your account profile and notification preferences are correctly configured before taking ownership.

## Typical developer workflow

1. Open the assigned ticket
2. Read the original issue and all internal notes
3. Reproduce the defect or validate the requested change
4. Implement the code, configuration, or package change
5. Add internal notes describing what changed
6. Set the ticket to **Released** when ready for QA
7. If QA fails, pick the ticket back up and correct the issue
8. Support deployment and final verification as required

## What to record in internal notes

A good developer note should capture:

- Root cause in plain language
- Files, modules, or services changed
- Important assumptions or side effects
- Test evidence or checks performed
- Deployment or rollback considerations

## Release package discipline

Before moving to **Released**, ensure the package includes:

- Version/build identifier
- Deployment steps in exact order
- DB migration and rollback scripts (if applicable)
- Validation checklist for QA

Reference the process artefact: [Release Package](../processes/package.md).

## Handling Failed QA effectively

When a ticket returns as **Failed QA**:

1. Reproduce using QA's exact evidence
2. Identify root cause (not just symptom)
3. Update implementation notes with fix details
4. Re-release with updated test guidance

## Status guidance for developers

Use statuses consistently:

- **Developers Assigned** when ownership is confirmed
- **Released** when implementation is complete and ready for QA
- **Failed QA** indicates rework is required
- **Deployed** is used after approved promotion to the target environment

## Example development scenarios

### BI issue
A report query or service dependency causes an SAP support report to fail for users.

### Customs issue
A clearance lookup in iCMS returns incomplete or blank results after a workflow step.

### LMT/MST issue
PAYE validation passes, but submission fails before generating a confirmation number.

## Developer checklist

- Read the full ticket thread first
- Record technical implementation notes
- Keep status aligned with the real state of work
- Hand back clearly for QA and deployment
- Respond quickly when QA reports a failure
- Keep release package and rollback notes complete
