# Troubleshooting Guide

This page lists common issues users may face when working with the SmartSupport osTicket portal.

## Requester issues

### I cannot open a new ticket
Check that:

- The portal is reachable at `http://10.153.1.189/`
- You entered a valid email address
- Required fields are completed
- Your browser session has not timed out

### I do not know which help topic to choose
Use the closest business area:

- BI and analytics issues → **BUSINESS & INTELLIGENCE SUPPORT**
- Customs platform issues → **CUSTOMS AND BORDER CONTROL**
- iTax, LMT, MST, or PAYE issues → **LMT AND MST**
- General service guidance → **General Inquiry**

If still unsure, select **General Inquiry** and explain the context clearly.

### I cannot track my ticket
Make sure you use:

- The same email used during submission
- The correct ticket number

If the ticket number is missing, open a new request and reference the original issue details.

## Staff issues

### The ticket is in the wrong queue
Use the transfer or assignment controls to route it to the correct owner.

### The requester has not provided enough detail
Use **Post Reply** to ask for:

- Exact steps followed
- Error message text
- Screenshot evidence
- Affected identifier, account, or transaction reference
- Time the issue occurred

### QA failed the fix
Record the defect outcome in an internal note, set the status to **Failed QA**, and assign the ticket back to the responsible technical owner.

### The ticket is ready but not yet closed
Confirm all three are complete:

1. Implementation or business response is complete
2. UAT or validation is complete where required
3. The requester has confirmed the outcome or no further action is needed

## Escalation tips

Escalate quickly when:

- SLA timelines are at risk
- The issue affects production operations
- The problem is reproducible and needs a code fix
- The issue spans multiple systems or teams
