# Support Analyst Guide

This guide covers how a support analyst works tickets from initial assignment through investigation, user communication, QA coordination, and resolution.

## Support analyst responsibilities

The support analyst is the first operational owner after BAS review.

You are expected to:

- Pick up tickets assigned for investigation
- Validate the reported issue and reproduce it where possible
- Communicate with the requester using ticket replies
- Resolve straightforward incidents directly
- Escalate change-related work to the development path
- Coordinate QA and UAT feedback
- Mark the ticket **Resolved** after successful deployment and validation

## Open queue view

![Staff open queue](../assets/screenshots/staff-open-queue.png)

From the staff panel, the analyst works mainly from:

- **Open** queue
- **My Tickets** queue
- Individual ticket records

The queue shows the ticket number, subject, requester, priority, and current assignee.

## Login and profile basics

- Staff authentication in this environment is **email-based** (not username-based).
- After sign-in, open **Profile** to keep your details and alert settings current.
- Use your profile to manage signature, notification preferences, and availability.

## Ticket detail view

![Ticket detail view](../assets/screenshots/staff-ticket-detail.png)

Inside a ticket, the analyst should use these main controls:

- **Assign** to set ownership
- **Post Reply** to communicate with the requester
- **Post Internal Note** for staff-only coordination
- **Change Status** to move the ticket through the workflow
- **Transfer** if the department or routing is wrong

## Standard analyst flow

1. Open the ticket from the **Open** or **My Tickets** queue
2. Review the subject, help topic, requester details, and ticket thread
3. Confirm whether the issue is complete enough to act on
4. Reply to the requester if more information is needed
5. Investigate and attempt first-line resolution
6. If it needs a code or configuration change, hand it off through the development path
7. Track QA and deployment feedback
8. After successful validation, update the ticket to **Resolved**

## When to escalate to development

Escalate when:

- The issue requires a code fix
- The issue requires a release or package deployment
- The problem is reproducible but not solvable through support actions
- The request is actually an enhancement or change request

## Expected status progression

The live system currently exposes these workflow statuses:

- **Open**
- **Assigned**
- **In Development**
- **Developers Assigned**
- **Released**
- **Failed QA**
- **Deployed**
- **Resolved**
- **Closed**

For analyst-owned work, the most common actions are:

- Move to **Assigned** when picked up by support
- Move to **Resolved** after successful deployment and user confirmation
- Reopen coordination if QA or UAT fails

## Internal notes vs requester replies

Use **Post Internal Note** for:

- Staff handover comments
- Investigation details
- Release or deployment coordination
- QA observations not intended for the requester

Use **Post Reply** for:

- Clarification questions
- Progress updates
- Test instructions for UAT
- Resolution confirmation

## Vacation mode (Out of Office)

Vacation mode prevents tickets from silently stalling when you are unavailable.

1. Go to **Profile** from the staff panel.
2. Set your temporary absence period and return date.
3. Add a short out-of-office note for internal visibility.
4. Ensure active tickets are reassigned before leave.

Recommended practice:

- Reassign all high-priority tickets before enabling vacation mode.
- Add an internal note listing who is covering your queue.
- Disable vacation mode immediately when you return.

## Working with canned responses

Canned responses help analysts reply consistently and faster.

- Use canned replies for common updates: acknowledgement, clarification request, testing instructions, and closure confirmation.
- Personalize placeholders (ticket number, impacted service, next action date) before sending.
- Never send sensitive internal-only details in requester replies.

If you cannot see canned responses, ask BAS/DEV manager to confirm your role permissions.

## Queue filters and smart working

Use queue filters to reduce noise:

- **My Tickets** for owned workload
- **Overdue** for SLA-risk tickets
- **High priority** for operationally critical issues

Tip: start with highest business impact tickets and oldest open tickets first.

## Practical examples

### Example 1: General inquiry
- Confirm whether it is informational or operational
- Reply with guidance if no system defect exists
- Resolve once the requester confirms the answer is sufficient

### Example 2: BI incident
- Validate the affected report, extract, or dashboard
- Capture exact filters, users, and error behavior
- Escalate if the issue requires a data or application fix

### Example 3: LMT/MST production issue
- Confirm business impact and deadlines
- Record screenshots, affected identifiers, and timestamps
- Coordinate with BAS manager and DEV manager if a change is required

## Analyst checklist

- Review ticket thread before acting
- Keep requester communication clear and professional
- Use internal notes for technical handoffs
- Keep status current
- Confirm QA and UAT outcomes before resolving
- Configure vacation mode before planned absence
- Use canned responses consistently with role permissions
