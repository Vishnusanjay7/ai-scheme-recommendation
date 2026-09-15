"""
Deterministic Scheme Registration & Deadline Engine
---------------------------------------------------
Pure, stateless, deterministic service for evaluating scheme activity and application deadlines.

Core Principles:
1. Timezone-Aware: Uses Indian Standard Time (Asia/Kolkata) for citizen-facing calculations.
2. Inclusive Last Date Rule: Application deadlines without explicit closing times remain valid
   through the entire calendar day (23:59:59.999999 IST).
3. Start Date Precision: Registration opens at 00:00:00 IST on start_date.
4. Deterministic Precedence:
   - Explicit INACTIVE -> INACTIVE
   - Explicit EXPIRED -> EXPIRED
   - Invalid Date Range (last_date < start_date) -> UNKNOWN
   - Future Start Date (current_date < start_date) -> NOT_YET_OPEN
   - Past Deadline (current_datetime > last_date) -> EXPIRED (even if db status is ACTIVE)
   - Valid Window -> OPEN
5. Separation of Concerns: Scheme activity (can the citizen apply now?) is completely decoupled
   from deterministic citizen eligibility (does the citizen qualify?).
"""

from datetime import date, datetime, time
from typing import Any, Dict, Optional, Tuple, Union
from zoneinfo import ZoneInfo

from app.models.deadline import (
    ActivityStatus,
    DeadlineClassification,
    SchemeActivityInfo,
)

# Indian Standard Time (UTC+05:30)
try:
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    from datetime import timezone
    IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


def get_current_ist_datetime() -> datetime:
    """Return current timestamp in Indian Standard Time (Asia/Kolkata)."""
    return datetime.now(IST)


def parse_scheme_datetime(
    date_val: Union[str, date, datetime, None],
    is_end_of_day: bool = False,
    tz: Any = IST,
) -> Optional[datetime]:
    """
    Parse a date, datetime, or ISO string into a timezone-aware datetime in target timezone.

    Parameters:
      date_val: String (YYYY-MM-DD or ISO timestamp), date object, or datetime object.
      is_end_of_day: If True and input has no time component, sets time to 23:59:59.999999 (inclusive rule).
                     If False and input has no time component, sets time to 00:00:00.000000.
      tz: Target ZoneInfo (defaults to Asia/Kolkata).
    """
    if date_val is None:
        return None

    if isinstance(date_val, datetime):
        if date_val.tzinfo is None:
            return date_val.replace(tzinfo=tz)
        return date_val.astimezone(tz)

    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        t = time(23, 59, 59, 999999) if is_end_of_day else time(0, 0, 0, 0)
        return datetime.combine(date_val, t, tzinfo=tz)

    val_str = str(date_val).strip()
    if not val_str:
        return None

    # Check for date-only format (YYYY-MM-DD)
    try:
        if len(val_str) == 10 and val_str.count("-") == 2:
            parsed_d = date.fromisoformat(val_str)
            t = time(23, 59, 59, 999999) if is_end_of_day else time(0, 0, 0, 0)
            return datetime.combine(parsed_d, t, tzinfo=tz)
    except ValueError:
        pass

    # Attempt standard ISO datetime parse
    try:
        dt = datetime.fromisoformat(val_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        return dt.astimezone(tz)
    except (ValueError, TypeError):
        return None


def calculate_days_remaining(
    last_date: Union[str, date, datetime, None],
    current_datetime: Optional[datetime] = None,
) -> Optional[int]:
    """
    Calculate calendar days remaining between current date and application deadline in IST.

    Returns:
      - None if last_date is None or unparseable.
      - 0 if deadline is today and time has not expired.
      - Positive integer for days remaining.
      - Negative integer if deadline has passed.
    """
    if last_date is None:
        return None

    now_ist = current_datetime if current_datetime is not None else get_current_ist_datetime()
    if now_ist.tzinfo is None:
        now_ist = now_ist.replace(tzinfo=IST)
    else:
        now_ist = now_ist.astimezone(IST)

    deadline_dt = parse_scheme_datetime(last_date, is_end_of_day=True, tz=IST)
    if deadline_dt is None:
        return None

    now_cal_date = now_ist.date()
    deadline_cal_date = deadline_dt.date()
    diff = (deadline_cal_date - now_cal_date).days

    # Same calendar date: verify if closing time has already elapsed
    if diff == 0:
        if now_ist > deadline_dt:
            return -1
        return 0

    return diff


def classify_deadline(
    last_date: Union[str, date, datetime, None],
    current_datetime: Optional[datetime] = None,
    start_date: Union[str, date, datetime, None] = None,
) -> Tuple[DeadlineClassification, Optional[int], Optional[str]]:
    """
    Classify application deadline urgency deterministically.

    Classifications:
      - >15 calendar days -> MORE_THAN_15_DAYS
      - 8–15 calendar days -> APPROACHING
      - 1–7 calendar days -> URGENT
      - 0 calendar days (inclusive today) -> CLOSING_TODAY
      - past deadline -> EXPIRED
      - last_date is NULL -> NO_DEADLINE
      - malformed / invalid date data -> UNKNOWN

    Returns:
      tuple of (DeadlineClassification, days_remaining, explanatory_reason)
    """
    if last_date is None:
        return (
            DeadlineClassification.NO_DEADLINE,
            None,
            "No application deadline specified; open until further official notice.",
        )

    # Check for invalid date range
    if start_date is not None:
        s_dt = parse_scheme_datetime(start_date, is_end_of_day=False, tz=IST)
        l_dt = parse_scheme_datetime(last_date, is_end_of_day=True, tz=IST)
        if s_dt is None or l_dt is None:
            return (
                DeadlineClassification.UNKNOWN,
                None,
                "Malformed or unparseable date format in scheme dates.",
            )
        if l_dt < s_dt:
            return (
                DeadlineClassification.UNKNOWN,
                None,
                "Invalid date data: application last_date cannot be earlier than start_date.",
            )

    days = calculate_days_remaining(last_date, current_datetime=current_datetime)
    if days is None:
        return (
            DeadlineClassification.UNKNOWN,
            None,
            "Unable to determine deadline; unparseable date format.",
        )

    if days < 0:
        return (
            DeadlineClassification.EXPIRED,
            days,
            f"Application deadline passed {abs(days)} day(s) ago.",
        )
    if days == 0:
        return (
            DeadlineClassification.CLOSING_TODAY,
            0,
            "Application window closes today (inclusive calendar date in IST).",
        )
    if 1 <= days <= 7:
        return (
            DeadlineClassification.URGENT,
            days,
            f"Application deadline is urgent: {days} calendar day(s) remaining.",
        )
    if 8 <= days <= 15:
        return (
            DeadlineClassification.APPROACHING,
            days,
            f"Application deadline is approaching: {days} calendar days remaining.",
        )

    return (
        DeadlineClassification.MORE_THAN_15_DAYS,
        days,
        f"Application window open: {days} calendar days remaining.",
    )


def get_scheme_activity(
    scheme: Union[Dict[str, Any], Any],
    current_datetime: Optional[datetime] = None,
) -> SchemeActivityInfo:
    """
    Evaluate effective registration activity and deadline status for a welfare scheme.
    Enforces deterministic precedence and ensures database status 'ACTIVE' cannot override
    an objectively expired deadline.
    """
    # Extract attributes safely from dict or object
    if isinstance(scheme, dict):
        status_val = scheme.get("status", "ACTIVE")
        start_date_val = scheme.get("start_date")
        last_date_val = scheme.get("last_date")
    else:
        status_val = getattr(scheme, "status", "ACTIVE")
        start_date_val = getattr(scheme, "start_date", None)
        last_date_val = getattr(scheme, "last_date", None)

    status_str = str(status_val or "ACTIVE").strip().upper()
    start_date_str = str(start_date_val) if start_date_val is not None else None
    last_date_str = str(last_date_val) if last_date_val is not None else None

    now_ist = current_datetime if current_datetime is not None else get_current_ist_datetime()
    if now_ist.tzinfo is None:
        now_ist = now_ist.replace(tzinfo=IST)
    else:
        now_ist = now_ist.astimezone(IST)

    # 1. Parse dates and check data quality
    start_dt = parse_scheme_datetime(start_date_val, is_end_of_day=False, tz=IST) if start_date_val else None
    last_dt = parse_scheme_datetime(last_date_val, is_end_of_day=True, tz=IST) if last_date_val else None

    # Invalid date format provided
    if start_date_val and start_dt is None:
        return SchemeActivityInfo(
            status=ActivityStatus.UNKNOWN,
            deadline_status=DeadlineClassification.UNKNOWN,
            days_remaining=None,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=False,
            reason="Scheme contains malformed or unparseable start_date.",
        )

    if last_date_val and last_dt is None:
        return SchemeActivityInfo(
            status=ActivityStatus.UNKNOWN,
            deadline_status=DeadlineClassification.UNKNOWN,
            days_remaining=None,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=False,
            reason="Scheme contains malformed or unparseable last_date.",
        )

    # Invalid range: last_date < start_date
    if start_dt and last_dt and last_dt < start_dt:
        return SchemeActivityInfo(
            status=ActivityStatus.UNKNOWN,
            deadline_status=DeadlineClassification.UNKNOWN,
            days_remaining=None,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=False,
            reason="Invalid date range: application last_date cannot be earlier than start_date.",
        )

    # Classify deadline
    deadline_class, days_remaining, deadline_reason = classify_deadline(
        last_date=last_date_val,
        current_datetime=now_ist,
        start_date=start_date_val,
    )

    # 2. Strict Precedence Evaluation
    # Rule 1: Explicit INACTIVE / CLOSED / DISABLED / SUSPENDED
    if status_str in {"INACTIVE", "CLOSED", "DISABLED", "SUSPENDED"}:
        return SchemeActivityInfo(
            status=ActivityStatus.INACTIVE,
            deadline_status=deadline_class,
            days_remaining=days_remaining,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=False,
            reason=f"Scheme is explicitly marked {status_str} by administrative authority.",
        )

    # Rule 2: Explicit EXPIRED
    if status_str == "EXPIRED":
        return SchemeActivityInfo(
            status=ActivityStatus.EXPIRED,
            deadline_status=DeadlineClassification.EXPIRED,
            days_remaining=days_remaining,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=False,
            reason="Scheme is explicitly marked EXPIRED by administrative authority.",
        )

    # Rule 3: Future start date (current date < start_date)
    if start_dt is not None:
        now_cal_date = now_ist.date()
        start_cal_date = start_dt.date()
        if now_cal_date < start_cal_date:
            return SchemeActivityInfo(
                status=ActivityStatus.NOT_YET_OPEN,
                deadline_status=deadline_class,
                days_remaining=days_remaining,
                start_date=start_date_str,
                last_date=last_date_str,
                is_actionable=False,
                reason=f"Registration has not opened yet; opens on {start_cal_date.isoformat()}.",
            )

    # Rule 4: Past deadline (current datetime > end of last_date)
    if last_dt is not None and (now_ist > last_dt or (days_remaining is not None and days_remaining < 0)):
        return SchemeActivityInfo(
            status=ActivityStatus.EXPIRED,
            deadline_status=DeadlineClassification.EXPIRED,
            days_remaining=days_remaining,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=False,
            reason=(
                f"Application deadline expired on {last_dt.date().isoformat()} "
                f"({abs(days_remaining)} day(s) ago). Database status cannot override an expired deadline."
            ),
        )

    # Rule 5: Valid current window
    if status_str == "ACTIVE":
        return SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=deadline_class,
            days_remaining=days_remaining,
            start_date=start_date_str,
            last_date=last_date_str,
            is_actionable=True,
            reason=f"Scheme is currently OPEN and actionable. {deadline_reason}",
        )

    # Rule 6: Unknown / unhandled status
    return SchemeActivityInfo(
        status=ActivityStatus.UNKNOWN,
        deadline_status=deadline_class,
        days_remaining=days_remaining,
        start_date=start_date_str,
        last_date=last_date_str,
        is_actionable=False,
        reason=f"Scheme status '{status_str}' is unverified.",
    )


def is_scheme_active(
    scheme: Union[Dict[str, Any], Any],
    current_datetime: Optional[datetime] = None,
) -> bool:
    """Return True if scheme's effective registration activity is OPEN."""
    info = get_scheme_activity(scheme, current_datetime=current_datetime)
    return info.status == ActivityStatus.OPEN


def is_scheme_actionable(
    scheme: Union[Dict[str, Any], Any],
    current_datetime: Optional[datetime] = None,
) -> bool:
    """
    Return True if scheme is actionable (effective status is OPEN and deadline has not expired).
    Actionability indicates the citizen can currently submit an application.
    """
    info = get_scheme_activity(scheme, current_datetime=current_datetime)
    return info.is_actionable
