# Phase 8: Deadline Monitoring & Citizen Notifications

## Architecture Overview

The Deadline Monitoring & Notification subsystem monitors bookmarked welfare schemes and delivers timely alerts to citizens as statutory application deadlines approach.

```
                  ┌─────────────────────────────────────┐
                  │ Periodic Runner / check_deadlines.py │
                  └──────────────────┬──────────────────┘
                                     ↓
                  ┌─────────────────────────────────────┐
                  │     Query public.saved_schemes      │
                  └──────────────────┬──────────────────┘
                                     ↓
                  ┌─────────────────────────────────────┐
                  │ Re-evaluate Current User Profile    │
                  │ (evaluate_eligibility -> ELIGIBLE)  │
                  └──────────────────┬──────────────────┘
                                     ↓
                  ┌─────────────────────────────────────┐
                  │ Re-evaluate Activity & Deadline     │
                  │ (OPEN & CLOSING_TODAY / URGENT /    │
                  │  APPROACHING)                       │
                  └──────────────────┬──────────────────┘
                                     ↓
                  ┌─────────────────────────────────────┐
                  │ Check Duplicate / Cycle Idempotency │
                  └──────────────────┬──────────────────┘
                                     ↓
                  ┌─────────────────────────────────────┐
                  │   Insert into public.notifications  │
                  │        (status = 'PENDING')         │
                  └──────────────────┬──────────────────┘
                                     ↓
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
        ┌───────────────────┐                  ┌───────────────────┐
        │  In-App Bell /    │                  │  Email Dispatch   │
        │  /notifications   │                  │  (EmailService)   │
        └───────────────────┘                  └─────────┬─────────┘
                                                         │
                                             Success: status = 'SENT'
                                             Failure: status = 'PENDING'
```

---

## Eligibility Requirement

A notification is generated **only** if the citizen currently qualifies for the scheme:
- **Strict Requirement**: Deterministic evaluation via `evaluate_eligibility(profile, scheme, rules)` must return `EligibilityStatus.ELIGIBLE`.
- **Exclusions**:
  - `NOT_ELIGIBLE` schemes never generate notifications.
  - `POSSIBLY_ELIGIBLE` schemes (requiring verification) never generate notifications.
- **Dynamic Re-evaluation**: The system retrieves the citizen's current profile from `public.user_profiles` at evaluation time. Saving a scheme does not grant permanent notification rights if the citizen's age, income, or demographic status changes.
- **Deterministic**: No AI/LLMs are used to make eligibility or notification decisions.

---

## Deadline Windows & Classification

Deadline calculation is performed purely by `app.services.deadline_service` using Indian Standard Time (IST, UTC+05:30):

| Deadline Classification | Days Remaining | Notification Type | Message Example |
|---|---|---|---|
| `CLOSING_TODAY` | `0` days (inclusive end of day) | `DEADLINE_TODAY` | *"Your saved scheme 'X' closes today. Apply through the official government portal."* |
| `URGENT` | `1 – 7` days | `DEADLINE_URGENT` | *"Your saved scheme 'X' has an urgent application deadline. 3 day(s) remaining."* |
| `APPROACHING` | `8 – 15` days | `DEADLINE_APPROACHING` | *"Your saved scheme 'X' is approaching its application deadline. 12 days remaining."* |
| `MORE_THAN_15_DAYS` | `> 15` days | *(None)* | Suppressed until deadline enters window. |
| `NO_DEADLINE` | Continuous / Rolling | *(None)* | No notification generated. |
| `EXPIRED` | Past deadline | *(None)* | Suppressed. |

---

## Duplicate Prevention & Deadline Cycles

- **Idempotency**: The monitoring service queries `public.notifications` before creating any alert. If a notification of the same `notification_type` already exists for that citizen, scheme, and deadline cycle, it is skipped.
- **Deadline Cycle Recognition**: The scheme's `last_date` (parsed as end-of-day IST) is recorded in the `scheduled_at` column. If a welfare program is renewed or its deadline extended in a subsequent year or intake cycle, the new `scheduled_at` timestamp allows fresh alerts for the new cycle without manual intervention.

---

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/notifications` | Yes (`auth.uid()`) | List citizen's in-app notifications (newest first). |
| `GET` | `/api/notifications/unread` | Yes (`auth.uid()`) | Get unread notification count and items for navbar badge and dashboard widget. |
| `PATCH` | `/api/notifications/{id}/read` | Yes (`auth.uid()`) | Mark a single notification as read (ownership enforced). |
| `PATCH` | `/api/notifications/read-all` | Yes (`auth.uid()`) | Mark all notifications for current citizen as read. |
| `POST` | `/api/notifications/check-deadlines` | Yes (`auth.uid()`) | Trigger deadline monitoring run on demand. |

---

## Email Notification Architecture

- **Provider-Agnostic**: Handled by `app.integrations.email_service.EmailService`.
- **Environment Variables**: Reads `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `NOTIFICATION_FROM_EMAIL`.
- **Resilience**: If email configuration is absent or fails, in-app notifications are created normally with `status = 'PENDING'`. Notification creation never fails because of missing email credentials.
- **Truthful Delivery State**: Notifications are updated to `status = 'SENT'` and `sent_at = timestamp` **only** if the email provider successfully confirms delivery. Failed attempts remain `PENDING`.

---

## Row Level Security (RLS) & Security

- **Database Policies**:
  - `SELECT USING (auth.uid() = user_id)`
  - `UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)`
  - `DELETE USING (auth.uid() = user_id)`
- **Identity Isolation**: The backend extracts citizen identity exclusively from verified JWT bearer tokens (`auth.uid()`).
- **Cross-User Protection**: Attempting to view or mark another citizen's notification as read returns `403 Forbidden` or `404 Not Found`.

---

## CLI Monitoring Script

The monitoring job can be invoked from the command line or scheduled via cron / task scheduler:

```bash
python backend/scripts/check_deadlines.py
```

Output:
```
=== SchemeSetu Deadline Monitoring Run ===
Users checked: 0
Saved schemes checked: 0
Eligible saved schemes: 0
Notifications created: 0
Notifications skipped: 0
==========================================
```
- Completely safe to run in development or production.
- Operates properly when zero schemes exist in the database.
- Redacts/omits all private citizen details from stdout.
