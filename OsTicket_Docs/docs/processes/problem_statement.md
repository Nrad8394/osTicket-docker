# Problem Statement

A **Problem Statement** is the structured description of an issue that a requester submits when opening a support ticket. It gives the support team enough context to assess, prioritise, and route the ticket without follow-up questions.

---

## When It Is Created

The requester fills in the problem statement as part of the **Open a New Ticket** form before the ticket is assigned a number or routed to the queue.

---

## Required Sections

| Section | What to Include |
|---|---|
| **System / Module** | The specific application or module affected (e.g. iTax, iCMS, SAP iSupport) |
| **Environment** | Production, UAT, or Staging |
| **Date & Time First Observed** | When the issue was first noticed |
| **Description of the Problem** | A clear, factual description of what is wrong or what is needed |
| **Expected Behaviour** | What should happen under normal conditions |
| **Actual Behaviour** | What is currently happening instead |
| **Business Impact** | Which teams, users, or processes are affected and to what degree |
| **Steps to Reproduce** | Numbered steps that consistently reproduce the issue (for bugs) |
| **Attachments** | Screenshots, error logs, or supporting files |

---

## Template

```
System / Module:
Environment:
Date & Time First Observed:

Description of the Problem:
[Describe what is wrong or what is needed]

Expected Behaviour:
[Describe what should happen]

Actual Behaviour:
[Describe what is happening instead]

Business Impact:
[Who is affected? What operations are blocked?]

Steps to Reproduce (for bugs):
1.
2.
3.

Attachments:
[List file names or paste screenshots inline]
```

---

## Example — Tax System Bug

```
System / Module: iTax – PAYE Module
Environment: Production
Date & Time First Observed: 2026-04-10 09:15 EAT

Description of the Problem:
PAYE returns submitted via iTax are not generating payment slips.
The submission completes without error, but no e-slip appears in
the taxpayer's account.

Expected Behaviour:
An e-slip is generated immediately after successful PAYE return
submission and appears under "Payment Obligations".

Actual Behaviour:
No e-slip appears. The section shows "No records found" even
after refreshing and waiting 24 hours.

Business Impact:
Affects all employers processing April 2026 payroll.
Approximately 200+ taxpayers at our organisation are blocked
from making timely payments, risking penalties.

Steps to Reproduce:
1. Log in to iTax as an employer.
2. Navigate to Returns > PAYE > File Return.
3. Upload the return file and click Submit.
4. Navigate to Payments > Payment Obligations.
5. Observe that no e-slip is listed.

Attachments:
- paye_submission_confirmation.png
- payment_obligations_empty.png
```

---

## Tips for a Good Problem Statement

- Be specific — "the system is slow" is not actionable; "the report generation page times out after 30 seconds for date ranges longer than 3 months" is.
- Separate the observed symptom from the suspected cause — do not diagnose in the problem statement.
- Always state the business impact; it drives priority assignment.
- For enhancement requests, replace "Steps to Reproduce" with "Current Workaround (if any)".

---

## Related Artefacts

| Artefact | Created By | When |
|---|---|---|
| [RFC](rfc.md) | DEV Manager | When development work is approved |
| [Package](package.md) | Developer | When implementation is complete |
| [UAT](uat.md) | Requester | When fix is deployed to test |
| [Report](report.md) | Support Analyst | After QA result |
