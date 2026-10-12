/**
 * Eligibility Badge Component
 * Displays deterministic qualification status:
 *   - ELIGIBLE: 🟢 Eligible
 *   - POSSIBLY_ELIGIBLE: 🟡 Possibly Eligible / Eligibility Needs Verification
 *   - NOT_ELIGIBLE: 🔴 Not Eligible
 */
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'

export default function EligibilityBadge({ status, isVerificationRequired = false }) {
  if (isVerificationRequired || status === 'POSSIBLY_ELIGIBLE') {
    return (
      <span className="badge badge-warning" title="Citizen must verify missing criteria before applying">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Eligibility Needs Verification
      </span>
    )
  }

  if (status === 'ELIGIBLE') {
    return (
      <span className="badge badge-success" title="Citizen meets all statutory criteria">
        <CheckCircle2 className="h-3.5 w-3.5 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Eligible
      </span>
    )
  }

  if (status === 'NOT_ELIGIBLE') {
    return (
      <span className="badge badge-danger" title="Citizen does not meet scheme criteria">
        <XCircle className="h-3.5 w-3.5 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Not Eligible
      </span>
    )
  }

  // Scheme activity statuses (e.g. ACTIVE, OPEN) or missing evaluation must NEVER render as ELIGIBLE
  if (!status || status === 'ACTIVE' || status === 'OPEN') {
    return null
  }

  return (
    <span className="badge badge-neutral">
      <span className="badge-dot dot-neutral" aria-hidden="true"></span>
      {status}
    </span>
  )
}
