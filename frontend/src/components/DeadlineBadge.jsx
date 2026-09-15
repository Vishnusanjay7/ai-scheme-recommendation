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
export default function DeadlineBadge({ deadlineStatus, daysRemaining, activityStatus }) {
  if (activityStatus === 'EXPIRED' || deadlineStatus === 'EXPIRED') {
    return <span className="badge badge-expired">Expired</span>
  }

  if (activityStatus === 'NOT_YET_OPEN') {
    return <span className="badge badge-neutral">Registration Not Yet Open</span>
  }

  if (activityStatus === 'INACTIVE') {
    return <span className="badge badge-neutral">Scheme Inactive</span>
  }

  if (deadlineStatus === 'CLOSING_TODAY' || daysRemaining === 0) {
    return (
      <span className="badge badge-urgent animate-pulse" title="Valid through 23:59:59 IST tonight">
        Closing Today
      </span>
    )
  }

  if (deadlineStatus === 'URGENT') {
    return (
      <span className="badge badge-urgent">
        Urgent — {daysRemaining ?? 'Few'} {daysRemaining === 1 ? 'day' : 'days'} remaining
      </span>
    )
  }

  if (deadlineStatus === 'APPROACHING') {
    return (
      <span className="badge badge-approaching">
        Approaching — {daysRemaining} days remaining
      </span>
    )
  }

  if (deadlineStatus === 'MORE_THAN_15_DAYS') {
    return (
      <span className="badge badge-info">
        {daysRemaining} days remaining
      </span>
    )
  }

  if (deadlineStatus === 'NO_DEADLINE') {
    return <span className="badge badge-open">Open — No Deadline</span>
  }

  return (
    <span className="badge badge-neutral">
      {deadlineStatus ? deadlineStatus.replace(/_/g, ' ') : 'Active'}
    </span>
  )
}
