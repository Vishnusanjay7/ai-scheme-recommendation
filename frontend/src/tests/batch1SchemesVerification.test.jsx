import { describe, it, expect } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import EligibilityBadge from '../components/EligibilityBadge'
import DeadlineBadge from '../components/DeadlineBadge'
import DocumentRequirementBadge from '../components/DocumentRequirementBadge'

describe('Phase 11J: Frontend Verification for Batch 1 Schemes', () => {
  const sampleBatch1Scheme = {
    id: 'sample-batch1-id',
    slug: 'sogateakia',
    scheme_name: 'Scheme of Giving Awards to Eminent Artists - Tamil Nadu',
    government_level: 'STATE',
    state_id: 23,
    status: 'ACTIVE',
    last_date: null,
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    documents: [
      {
        document_name: 'Proof of Age',
        mandatory: true,
        description: 'MANDATORY_STATUS_UNKNOWN: Source text lists document without specifying mandatory vs optional.',
      },
      {
        document_name: 'Art and Culture Certificate',
        mandatory: true,
        description: 'Explicitly stated as mandatory in source documentation.',
      },
    ],
  }

  it('Verifies scheme status ACTIVE does not render as ELIGIBLE', () => {
    const markup = renderToStaticMarkup(<EligibilityBadge status={sampleBatch1Scheme.status} />)
    expect(markup).not.toContain('Eligible')
    expect(markup).toBe('')
  })

  it('Verifies deadline badge displays Open with No Deadline Specified', () => {
    const markup = renderToStaticMarkup(
      <DeadlineBadge
        deadlineStatus={sampleBatch1Scheme.activity.deadline_status}
        activityStatus={sampleBatch1Scheme.activity.status}
      />
    )
    expect(markup).toContain('Open')
    expect(markup).toContain('No Deadline Specified')
  })

  it('Verifies document with unknown mandatory status displays Required status not confirmed', () => {
    const unknownDoc = sampleBatch1Scheme.documents[0]
    const markup = renderToStaticMarkup(<DocumentRequirementBadge doc={unknownDoc} />)
    expect(markup).not.toContain('Mandatory')
    expect(markup).toContain('Required status not confirmed')
  })

  it('Verifies document with explicit mandatory status displays Mandatory', () => {
    const mandatoryDoc = sampleBatch1Scheme.documents[1]
    const markup = renderToStaticMarkup(<DocumentRequirementBadge doc={mandatoryDoc} />)
    expect(markup).toContain('Mandatory')
  })

  it('Verifies unconfirmed activityStatus with NO_DEADLINE does not assert Open', () => {
    const markup = renderToStaticMarkup(
      <DeadlineBadge deadlineStatus="NO_DEADLINE" activityStatus="UNKNOWN" />
    )
    expect(markup).not.toContain('Open')
    expect(markup).toContain('No Deadline Specified')
  })
})
