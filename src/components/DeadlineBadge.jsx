/**
 * Deadline Badge Component
 * Displays authoritative application deadline urgency from the backend:
 *   - CLOSING_TODAY: Closing Today (Urgent)
 *   - URGENT: Urgent — X days remaining
 *   - APPROACHING: X days remaining
 *   - MORE_THAN_15_DAYS: X days remaining
 *   - NO_DEADLINE: Open — No Deadline
 *   - EXPIRED: Expired
 */
import { AlertCircle, Calendar, Clock } from 'lucide-react'

export default function DeadlineBadge({ deadlineStatus, daysRemaining, activityStatus }) {
  if (activityStatus === 'EXPIRED' || deadlineStatus === 'EXPIRED') {
    return (
      <span className="badge badge-expired">
        <Clock className="h-3 w-3 shrink-0 inline-block mr-1 opacity-70" aria-hidden="true" />
        Expired
      </span>
    )
  }

  if (activityStatus === 'NOT_YET_OPEN') {
    return (
      <span className="badge badge-neutral">
        <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 opacity-70" aria-hidden="true" />
        Registration Not Yet Open
      </span>
    )
  }

  if (activityStatus === 'INACTIVE') {
    return (
      <span className="badge badge-neutral">
        <AlertCircle className="h-3 w-3 shrink-0 inline-block mr-1 opacity-70" aria-hidden="true" />
        Scheme Inactive
      </span>
    )
  }

  if (deadlineStatus === 'CLOSING_TODAY' || daysRemaining === 0) {
    return (
      <span className="badge badge-urgent animate-pulse" title="Valid through 23:59:59 IST tonight">
        <AlertCircle className="h-3 w-3 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Closing Today
      </span>
    )
  }

  if (deadlineStatus === 'CLOSING_SOON' || deadlineStatus === 'URGENT') {
    return (
      <span className="badge badge-urgent bg-amber-50 text-amber-900 border border-amber-300 px-2 py-0.5 rounded font-mono text-[11px] font-semibold">
        <Clock className="h-3 w-3 shrink-0 inline-block mr-1 text-amber-600" aria-hidden="true" />
        Closing Soon — {daysRemaining ?? 'Few'} {daysRemaining === 1 ? 'day' : 'days'} remaining
      </span>
    )
  }

  if (deadlineStatus === 'ROLLING_ANNUAL') {
    return (
      <span className="badge badge-info bg-blue-50 text-blue-900 border border-blue-200 px-2 py-0.5 rounded font-mono text-[11px] font-semibold" title="Rolling annual window verified daily">
        <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 text-blue-600" aria-hidden="true" />
        Active Enrollment ({daysRemaining ? `${daysRemaining}d left` : 'Rolling'})
      </span>
    )
  }

  if (deadlineStatus === 'APPROACHING') {
    return (
      <span className="badge badge-approaching">
        <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Approaching — {daysRemaining} days remaining
      </span>
    )
  }

  if (deadlineStatus === 'MORE_THAN_15_DAYS') {
    return (
      <span className="badge badge-info">
        <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        {daysRemaining} days remaining
      </span>
    )
  }

  if (deadlineStatus === 'NO_DEADLINE') {
    if (activityStatus === 'OPEN') {
      return (
        <span className="badge badge-open" title="Scheme registration is open with no fixed closing deadline">
          <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
          Open — No Deadline Specified
        </span>
      )
    }
    return (
      <span className="badge badge-neutral" title="No closing deadline specified in official source">
        <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 opacity-70" aria-hidden="true" />
        No Deadline Specified
      </span>
    )
  }

  if (activityStatus === 'OPEN') {
    return (
      <span className="badge badge-open">
        <Calendar className="h-3 w-3 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Open
      </span>
    )
  }

  return (
    <span className="badge badge-neutral">
      {deadlineStatus ? deadlineStatus.replace(/_/g, ' ') : 'Status Unspecified'}
    </span>
  )
}
