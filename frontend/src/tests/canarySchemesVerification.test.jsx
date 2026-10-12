import { describe, it, expect } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import EligibilityBadge from '../components/EligibilityBadge'
import DeadlineBadge from '../components/DeadlineBadge'
import DocumentRequirementBadge from '../components/DocumentRequirementBadge'

describe('Phase 11I: Verification against 5 Canary Schemes', () => {
  // Canary Scheme 1: mranmas1 (Moovalur Ramamirtham Ammaiyar Ninaivu Marriage Assistance Scheme-1)
  it('Canary 1 (mranmas1): status ACTIVE does not render as ELIGIBLE, documents with unknown status render safely', () => {
    const scheme = {
      id: 'a331c9af-aa84-49d7-89d7-8b33b91b1f9e',
      scheme_name: 'Moovalur Ramamirtham Ammaiyar Ninaivu Marriage Assistance Scheme-1',
      status: 'ACTIVE',
      activity: {
        status: 'OPEN',
        deadline_status: 'NO_DEADLINE',
        days_remaining: null,
      },
      documents: [
        {
          document_name: 'Marriage Invitation Card',
          mandatory: true,
          description: 'MANDATORY_STATUS_UNKNOWN: Source text lists document without specifying mandatory vs optional.',
        },
        {
          document_name: 'Aadhaar Card',
          mandatory: true,
          description: 'Explicitly stated as mandatory in source documentation.',
        },
      ],
    }

    // 1. Scheme status ACTIVE must not render as ELIGIBLE
    const eligibilityMarkup = renderToStaticMarkup(<EligibilityBadge status={scheme.status} />)
    expect(eligibilityMarkup).not.toContain('Eligible')
    expect(eligibilityMarkup).not.toContain('ELIGIBLE')

    // 2. Deadline badge with explicit OPEN activityStatus displays Open
    const deadlineMarkup = renderToStaticMarkup(
      <DeadlineBadge
        deadlineStatus={scheme.activity.deadline_status}
        activityStatus={scheme.activity.status}
      />
    )
    expect(deadlineMarkup).toContain('Open')

    // 3. Document 1 with unknown status must NOT render Mandatory
    const doc1Markup = renderToStaticMarkup(<DocumentRequirementBadge doc={scheme.documents[0]} />)
    expect(doc1Markup).not.toContain('Mandatory')
    expect(doc1Markup).toContain('Required status not confirmed')

    // 4. Document 2 with explicit mandatory renders Mandatory
    const doc2Markup = renderToStaticMarkup(<DocumentRequirementBadge doc={scheme.documents[1]} />)
    expect(doc2Markup).toContain('Mandatory')
  })

  // Canary Scheme 2: uyegp (Unemployed Youth Employment Generation Programme)
  it('Canary 2 (uyegp): NO_DEADLINE without confirmed OPEN does not claim Open', () => {
    const unconfirmedDeadline = renderToStaticMarkup(
      <DeadlineBadge deadlineStatus="NO_DEADLINE" activityStatus="UNKNOWN" />
    )
    expect(unconfirmedDeadline).not.toContain('Open')
    expect(unconfirmedDeadline).toContain('No Deadline Specified')
  })

  // Canary Scheme 3: atwsfww (Amma Two Wheeler Scheme for Working Women)
  it('Canary 3 (atwsfww): Unknown document mandatory status handled accurately', () => {
    const atwsfwwDoc = {
      document_name: 'Community Certificate',
      mandatory: true,
      description: 'MANDATORY_STATUS_UNKNOWN: Source text lists document without specifying mandatory vs optional.',
    }
    const docMarkup = renderToStaticMarkup(<DocumentRequirementBadge doc={atwsfwwDoc} />)
    expect(docMarkup).not.toContain('Mandatory')
    expect(docMarkup).toContain('Required status not confirmed')
  })

  // Canary Scheme 4: cmgcpsii (Chief Minister’s Girl Child Protection Scheme-II)
  it('Canary 4 (cmgcpsii): Deterministic eligibility evaluated result displays accurately', () => {
    // When citizen eligibility is evaluated:
    expect(renderToStaticMarkup(<EligibilityBadge status="ELIGIBLE" />)).toContain('Eligible')
    expect(renderToStaticMarkup(<EligibilityBadge status="POSSIBLY_ELIGIBLE" />)).toContain('Eligibility Needs Verification')
    expect(renderToStaticMarkup(<EligibilityBadge status="NOT_ELIGIBLE" />)).toContain('Not Eligible')
  })

  // Canary Scheme 5: gwwh (Government Working Women’s Hostel)
  it('Canary 5 (gwwh): Scheme details header does not map ACTIVE to ELIGIBLE', () => {
    // Before Phase 11I, SchemeDetails mapped scheme.status === 'ACTIVE' to ELIGIBLE.
    // Now, if scheme.eligibility_status is null/undefined, no eligibility badge renders:
    const rawStatus = 'ACTIVE'
    const eligibilityBadge = renderToStaticMarkup(<EligibilityBadge status={rawStatus} />)
    expect(eligibilityBadge).toBe('')
  })
})
