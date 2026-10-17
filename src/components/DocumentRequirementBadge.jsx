export default function DocumentRequirementBadge({ doc }) {
  const isMandatory = doc?.is_mandatory ?? doc?.mandatory ?? true

  if (isMandatory) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
        Mandatory
      </span>
    )
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
      Optional
    </span>
  )
}
