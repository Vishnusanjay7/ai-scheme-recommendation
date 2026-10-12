/**
 * Document Requirement Badge Component
 * -------------------------------------
 * Renders document requirement status adhering to Phase 11I semantics:
 *   - UNKNOWN: "Required status not confirmed" if source metadata/description has MANDATORY_STATUS_UNKNOWN
 *   - MANDATORY: "Mandatory" for verified mandatory documents
 *   - OPTIONAL: "Optional" for verified optional documents
 */
import { FileCheck2, FileText, HelpCircle } from 'lucide-react'

export default function DocumentRequirementBadge({ doc }) {
  if (!doc) return null

  const desc = doc.description || ''
  const isUnknown = desc.includes('MANDATORY_STATUS_UNKNOWN') || doc.mandatory_status === 'UNKNOWN'

  if (isUnknown) {
    return (
      <span
        className="badge badge-warning-subtle text-xs ml-2"
        title="Source documentation lists this document without confirming if it is mandatory or optional"
      >
        <HelpCircle className="h-3 w-3 shrink-0 inline-block mr-1 opacity-80" aria-hidden="true" />
        Required status not confirmed
      </span>
    )
  }

  const isMandatory = doc.mandatory === true || doc.is_mandatory === true
  if (isMandatory) {
    return (
      <span className="badge badge-urgent text-xs ml-2" title="Mandatory document required for application">
        <FileCheck2 className="h-3 w-3 shrink-0 inline-block mr-1 text-current" aria-hidden="true" />
        Mandatory
      </span>
    )
  }

  return (
    <span className="badge badge-neutral text-xs ml-2" title="Optional or conditional document">
      <FileText className="h-3 w-3 shrink-0 inline-block mr-1 opacity-70" aria-hidden="true" />
      Optional
    </span>
  )
}
