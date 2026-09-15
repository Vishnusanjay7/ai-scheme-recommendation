/**
 * Eligibility Badge Component
 * Displays deterministic qualification status:
 *   - ELIGIBLE: 🟢 Eligible
 *   - POSSIBLY_ELIGIBLE: 🟡 Possibly Eligible / Eligibility Needs Verification
 *   - NOT_ELIGIBLE: 🔴 Not Eligible
 */
export default function EligibilityBadge({ status, isVerificationRequired = false }) {
  if (isVerificationRequired || status === 'POSSIBLY_ELIGIBLE') {
    return (
      <span className="badge badge-warning" title="Citizen must verify missing criteria before applying">
        <span className="badge-dot dot-warning"></span>
        Eligibility Needs Verification
      </span>
    )
  }

  if (status === 'ELIGIBLE') {
    return (
      <span className="badge badge-success" title="Citizen meets all statutory criteria">
        <span className="badge-dot dot-success"></span>
        Eligible
      </span>
    )
  }

  if (status === 'NOT_ELIGIBLE') {
    return (
      <span className="badge badge-danger" title="Citizen does not meet scheme criteria">
        <span className="badge-dot dot-danger"></span>
        Not Eligible
      </span>
    )
  }

  return (
    <span className="badge badge-neutral">
      <span className="badge-dot dot-neutral"></span>
      {status || 'Unknown Status'}
    </span>
  )
}
