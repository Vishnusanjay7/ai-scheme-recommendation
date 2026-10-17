import { ShieldCheck, HelpCircle, XCircle } from 'lucide-react'

export default function EligibilityBadge({ status, isVerificationRequired = false }) {
  if (status === 'ELIGIBLE' || status === 'HIGH_MATCH') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <ShieldCheck className="w-3 h-3 text-emerald-600" aria-hidden="true" />
        <span>Eligible</span>
      </span>
    )
  }

  if (status === 'VERIFICATION_REQUIRED' || isVerificationRequired || status === 'POTENTIALLY_ELIGIBLE') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        <HelpCircle className="w-3 h-3 text-amber-600" aria-hidden="true" />
        <span>Check Criteria</span>
      </span>
    )
  }

  if (status === 'INELIGIBLE') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
        <XCircle className="w-3 h-3 text-rose-600" aria-hidden="true" />
        <span>Not Eligible</span>
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
      <span>{status || 'Recommended'}</span>
    </span>
  )
}
