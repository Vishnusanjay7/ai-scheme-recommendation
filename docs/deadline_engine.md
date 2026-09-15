# Active/Open Registration & Deadline Engine

## 1. Overview & Architecture

The **Deadline and Activity Engine** provides deterministic evaluation of government scheme registration availability and application deadline urgency.

A core architectural principle of this platform is the strict separation between:
- **Eligibility Engine (Phase 3)**: *"Does the citizen qualify for this scheme based on profile criteria (age, income, caste, state, occupation, etc.)?"*
- **Deadline & Activity Engine (Phase 4)**: *"Is the scheme currently open for registration, what is its deadline urgency, and can a citizen take action today?"*

This clean decoupling guarantees that a citizen's qualification never gets conflated with whether the scheme portal is actively accepting applications.

---

## 2. Scheme Activity Status Values & Meanings

The `ActivityStatus` enum defines the current operational availability of a scheme:

| Status | Meaning | Actionable? |
|---|---|---|
| `OPEN` | Scheme is currently accepting applications. Current date/time falls within `[start_date, last_date]`, and database status is not inactive. | **Yes** (`is_actionable=True`) |
| `NOT_YET_OPEN` | Scheme application window has not started yet (`current_datetime < start_date`). | No (`is_actionable=False`) |
| `EXPIRED` | Application window has closed (`current_datetime > last_date`), or scheme is explicitly marked as expired in database. | No (`is_actionable=False`) |
| `INACTIVE` | Scheme has been explicitly deactivated, suspended, or discontinued in the database (`status.lower() in {"inactive", "closed", "disabled", "suspended"}`). | No (`is_actionable=False`) |
| `UNKNOWN` | Scheme data is malformed (e.g. invalid date ranges where `last_date < start_date` or unparseable dates). | No (`is_actionable=False`) |

---

## 3. Deadline Status Classifications & Rules

The `DeadlineClassification` enum categorizes the urgency of the application deadline:

| Deadline Classification | Days Remaining (`days_remaining`) | Description |
|---|---|---|
| `MORE_THAN_15_DAYS` | `> 15` | Deadline is comfortably in the future (> 15 days). |
| `APPROACHING` | `8` to `15` (inclusive) | Deadline is coming up soon (approximately 2 weeks). |
| `URGENT` | `1` to `7` (inclusive) | Deadline is critical (1 week or less remaining). |
| `CLOSING_TODAY` | `0` | Today is the final day to submit an application before 23:59:59 IST. |
| `EXPIRED` | `< 0` | The deadline has passed. |
| `NO_DEADLINE` | `None` (open-ended) | Scheme is ongoing with no specific closing date / rolling admissions. |
| `UNKNOWN` | `None` (malformed) | Date calculation cannot be performed due to invalid date ranges. |

---

## 4. Timezone Handling (`Asia/Kolkata`)

All government schemes in India operate under **Indian Standard Time (IST)**, equivalent to UTC+05:30.
- All calculations, date parsing, and comparisons explicitly localize to `ZoneInfo("Asia/Kolkata")`.
- Naive datetime inputs are localized to IST without shifting the calendar day.
- Aware datetime inputs in other timezones (e.g., UTC) are converted directly to IST before comparison.
- This ensures consistency regardless of server runtime location or user browser local time.

---

## 5. Inclusive Last-Date Rule

Official government deadlines stated as a calendar date (e.g. `2026-03-31`) remain valid throughout the entire day:
- A `last_date` provided as a calendar date (e.g., `2026-03-31` or ISO date string `2026-03-31T00:00:00`) is parsed and interpreted as ending at **23:59:59.999999 IST** on that calendar day.
- Applications submitted on `2026-03-31` at 18:00 IST are fully active (`days_remaining = 0`, `CLOSING_TODAY`).
- The scheme expires at `2026-04-01 00:00:00 IST` (`days_remaining = -1`, `EXPIRED`).

---

## 6. Start-Date Behavior

The scheme registration window begins at midnight of the start date:
- A `start_date` provided as a calendar date is interpreted as starting at **00:00:00.000000 IST** on that calendar day.
- If `current_datetime < start_date`, the scheme status is `NOT_YET_OPEN` and `is_actionable = False`.
- Citizens cannot submit applications prior to the opening date, even if the database status field states "active".

---

## 7. Missing Deadline Handling (Open-Ended Schemes)

Many national social welfare programs (e.g., PM Kisan, Ayushman Bharat, PMAY) are perennial:
- If `last_date` is `None` or empty, the scheme is treated as **open-ended / ongoing**.
- If the scheme is open (`start_date <= current_datetime` and status is active), its activity status is `OPEN`.
- The deadline status is classified as `NO_DEADLINE`.
- `days_remaining` is returned as `None`.
- `is_actionable` is `True`.

---

## 8. Invalid Date Handling

Data pipelines or source portals may occasionally present corrupted date data:
- If `last_date < start_date`, this is a logical impossibility and invalid range.
- Handled gracefully: `status = ActivityStatus.UNKNOWN`, `deadline_status = DeadlineClassification.UNKNOWN`, `is_actionable = False`, with a descriptive explanation in `reason`.
- If a date string cannot be parsed into a valid ISO date, it defaults safely to `UNKNOWN` rather than raising uncaught 500 errors.

---

## 9. Status Precedence Rules

To prevent stale database values from presenting expired schemes as active to citizens, the engine applies strict evaluation precedence:

1. **Invalid Date Range Check**: If `start_date` and `last_date` are both present and `last_date < start_date`, return `ActivityStatus.UNKNOWN` (`is_actionable = False`).
2. **Explicit Deactivation**: If database `status` is explicitly `"inactive"`, `"closed"`, `"disabled"`, or `"suspended"`, return `ActivityStatus.INACTIVE` (`is_actionable = False`).
3. **Explicit Database Expiration**: If database `status` is `"expired"`, return `ActivityStatus.EXPIRED` (`is_actionable = False`).
4. **Future Opening Check**: If `start_date` is in the future (`current_datetime < start_date`), return `ActivityStatus.NOT_YET_OPEN` (`is_actionable = False`).
5. **Deadline Expiration Check**: If `last_date` has passed (`current_datetime > last_date`), return `ActivityStatus.EXPIRED` (`is_actionable = False`).
   *Crucial Rule*: A database `status` of `"active"` **CANNOT** override an expired `last_date`.
6. **Open Registration Window**: If within date bounds (or open-ended) and not deactivated, return `ActivityStatus.OPEN` (`is_actionable = True`).

---

## 10. Definition of an Actionable Scheme

A scheme is defined as **Actionable** (`is_actionable = True`) if and only if:
1. `activity.status == ActivityStatus.OPEN`
2. The current datetime is on or after the `start_date` (if specified)
3. The current datetime is on or before the `last_date` (if specified, up to 23:59:59.999999 IST)
4. The scheme is not deactivated or suspended

The endpoint `GET /api/schemes/active` returns strictly actionable schemes (`is_actionable == True`).

---

## 11. Decoupling Eligibility and Activity

Eligibility and Activity are isolated at every layer:

| Dimension | Eligibility Engine | Activity Engine |
|---|---|---|
| **Question** | Can the citizen qualify? | Is the portal accepting applications? |
| **Inputs** | Citizen profile (age, income, state, caste, occupation) | Scheme start date, last date, operational status |
| **Output** | `ELIGIBLE`, `INELIGIBLE`, `NEED_MORE_INFO` | `OPEN`, `NOT_YET_OPEN`, `EXPIRED`, `INACTIVE` |
| **Location** | `app/services/eligibility_engine.py` | `app/services/deadline_service.py` |

An individual may be `ELIGIBLE` for a scholarship whose application window is `EXPIRED`. Presenting both transparently allows the citizen to prepare documents for the next application cycle without false hopes of immediate submission.

---

## 12. Support for Future Notification Features

The deadline classification model directly empowers future notification triggers without architectural coupling:
- Cron jobs or scheduled tasks can query schemes with `activity.deadline_status == DeadlineClassification.URGENT` (e.g. 7 days or 3 days remaining) or `CLOSING_TODAY`.
- User alert preferences (e.g., SMS, email, push) can subscribe to schemes transitioning from `MORE_THAN_15_DAYS` to `APPROACHING` or `URGENT`.
- Because `calculate_days_remaining` and `classify_deadline` are pure functions accepting an explicit `current_datetime`, backtesting, future event simulation, and time-travel testing can be performed deterministically without modifying database state.
