import { describe, it, expect } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import EligibilityBadge from '../components/EligibilityBadge'
import DeadlineBadge from '../components/DeadlineBadge'
import DocumentRequirementBadge from '../components/DocumentRequirementBadge'

describe('Phase 11I: Frontend Semantic Badge Corrections', () => {
  // ---------------------------------------------------------------------------
  // BUG 1 & Requirements A - D: Eligibility vs Scheme Status
  // ---------------------------------------------------------------------------
  describe('Bug 1: EligibilityBadge Semantics', () => {
    it('A. ACTIVE or OPEN scheme status does NOT display ELIGIBLE', () => {
      const activeMarkup = renderToStaticMarkup(<EligibilityBadge status="ACTIVE" />)
      expect(activeMarkup).not.toContain('Eligible')
      expect(activeMarkup).not.toContain('ELIGIBLE')

      const openMarkup = renderToStaticMarkup(<EligibilityBadge status="OPEN" />)
      expect(openMarkup).not.toContain('Eligible')
      expect(openMarkup).not.toContain('ELIGIBLE')
    })

    it('B. ELIGIBLE result displays ELIGIBLE', () => {
      const markup = renderToStaticMarkup(<EligibilityBadge status="ELIGIBLE" />)
      expect(markup).toContain('Eligible')
      expect(markup).toContain('badge-success')
    })

    it('C. POSSIBLY_ELIGIBLE displays POSSIBLY_ELIGIBLE / Needs Verification', () => {
      const markup = renderToStaticMarkup(<EligibilityBadge status="POSSIBLY_ELIGIBLE" />)
      expect(markup).toContain('Eligibility Needs Verification')
      expect(markup).toContain('badge-warning')

      const verificationMarkup = renderToStaticMarkup(<EligibilityBadge isVerificationRequired={true} />)
      expect(verificationMarkup).toContain('Eligibility Needs Verification')
    })

    it('D. NOT_ELIGIBLE displays NOT_ELIGIBLE', () => {
      const markup = renderToStaticMarkup(<EligibilityBadge status="NOT_ELIGIBLE" />)
      expect(markup).toContain('Not Eligible')
      expect(markup).toContain('badge-danger')
    })
  })

  // ---------------------------------------------------------------------------
  // BUG 2 & Requirements E - F: DeadlineBadge Semantics
  // ---------------------------------------------------------------------------
  describe('Bug 2: DeadlineBadge Semantics', () => {
    it('E. NO_DEADLINE does NOT display OPEN when activityStatus is unconfirmed', () => {
      const markup = renderToStaticMarkup(<DeadlineBadge deadlineStatus="NO_DEADLINE" />)
      expect(markup).toContain('No Deadline Specified')
      expect(markup).not.toContain('Open')
      expect(markup).not.toContain('OPEN')

      const unknownActivityMarkup = renderToStaticMarkup(
        <DeadlineBadge deadlineStatus="NO_DEADLINE" activityStatus="UNKNOWN" />
      )
      expect(unknownActivityMarkup).toContain('No Deadline Specified')
      expect(unknownActivityMarkup).not.toContain('Open')
    })

    it('F. explicitly confirmed OPEN can display OPEN', () => {
      const openNoDeadlineMarkup = renderToStaticMarkup(
        <DeadlineBadge deadlineStatus="NO_DEADLINE" activityStatus="OPEN" />
      )
      expect(openNoDeadlineMarkup).toContain('Open')
      expect(openNoDeadlineMarkup).toContain('No Deadline Specified')

      const openOnlyMarkup = renderToStaticMarkup(
        <DeadlineBadge activityStatus="OPEN" />
      )
      expect(openOnlyMarkup).toContain('Open')
      expect(openOnlyMarkup).toContain('badge-open')
    })

    it('Correctly renders deadline urgency states', () => {
      expect(renderToStaticMarkup(<DeadlineBadge deadlineStatus="EXPIRED" />)).toContain('Expired')
      expect(renderToStaticMarkup(<DeadlineBadge activityStatus="NOT_YET_OPEN" />)).toContain('Registration Not Yet Open')
      expect(renderToStaticMarkup(<DeadlineBadge activityStatus="INACTIVE" />)).toContain('Scheme Inactive')
      expect(renderToStaticMarkup(<DeadlineBadge deadlineStatus="CLOSING_TODAY" daysRemaining={0} />)).toContain('Closing Today')
      expect(renderToStaticMarkup(<DeadlineBadge deadlineStatus="URGENT" daysRemaining={3} />)).toContain('Urgent — 3 days remaining')
      expect(renderToStaticMarkup(<DeadlineBadge deadlineStatus="APPROACHING" daysRemaining={10} />)).toContain('Approaching — 10 days remaining')
      expect(renderToStaticMarkup(<DeadlineBadge deadlineStatus="MORE_THAN_15_DAYS" daysRemaining={25} />)).toContain('25 days remaining')
    })
  })

  // ---------------------------------------------------------------------------
  // BUG 3 & Requirements G - H: Document Requirement Semantics
  // ---------------------------------------------------------------------------
  describe('Bug 3: DocumentRequirementBadge Semantics', () => {
    it('G. document with MANDATORY_STATUS_UNKNOWN does NOT display Mandatory', () => {
      const unknownDoc = {
        document_name: 'Community Certificate',
        mandatory: true, // DB schema NOT NULL constraint
        description: 'MANDATORY_STATUS_UNKNOWN: Source text lists document without specifying mandatory vs optional.',
      }

      const markup = renderToStaticMarkup(<DocumentRequirementBadge doc={unknownDoc} />)
      expect(markup).not.toContain('Mandatory')
      expect(markup).toContain('Required status not confirmed')
      expect(markup).toContain('badge-warning-subtle')
    })

    it('H. explicitly mandatory document displays Mandatory', () => {
      const mandatoryDoc = {
        document_name: 'Aadhaar Card',
        mandatory: true,
        description: 'Explicitly stated as mandatory in source documentation.',
      }

      const markup = renderToStaticMarkup(<DocumentRequirementBadge doc={mandatoryDoc} />)
      expect(markup).toContain('Mandatory')
      expect(markup).toContain('badge-urgent')
    })

    it('Explicitly optional document displays Optional', () => {
      const optionalDoc = {
        document_name: 'Driving License',
        mandatory: false,
        description: 'Stated as optional / conditional in source documentation.',
      }

      const markup = renderToStaticMarkup(<DocumentRequirementBadge doc={optionalDoc} />)
      expect(markup).toContain('Optional')
      expect(markup).toContain('badge-neutral')
      expect(markup).not.toContain('Mandatory')
    })
  })
})
