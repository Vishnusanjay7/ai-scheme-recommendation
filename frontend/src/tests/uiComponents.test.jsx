import { describe, it, expect } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Input,
  Select,
  Badge,
  Alert,
  Skeleton,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
  SkeletonList,
  Dialog,
} from '../components/ui'

describe('Phase 19.2: Reusable UI Component Primitives', () => {
  // ---------------------------------------------------------------------------
  // 1. Button Tests
  // ---------------------------------------------------------------------------
  describe('Button Component', () => {
    it('renders default primary variant with children', () => {
      const html = renderToStaticMarkup(<Button>Submit Application</Button>)
      expect(html).toContain('Submit Application')
      expect(html).toContain('bg-gov-navy')
      expect(html).toContain('type="button"')
    })

    it('renders secondary, outline, danger, success, and ghost variants', () => {
      expect(renderToStaticMarkup(<Button variant="secondary">Secondary</Button>)).toContain('bg-gov-accent')
      expect(renderToStaticMarkup(<Button variant="outline">Outline</Button>)).toContain('border-gov-border')
      expect(renderToStaticMarkup(<Button variant="danger">Delete</Button>)).toContain('bg-gov-danger')
      expect(renderToStaticMarkup(<Button variant="success">Approve</Button>)).toContain('bg-gov-success')
      expect(renderToStaticMarkup(<Button variant="ghost">Cancel</Button>)).toContain('hover:bg-slate-100')
    })

    it('renders disabled state correctly', () => {
      const html = renderToStaticMarkup(<Button disabled>Disabled Button</Button>)
      expect(html).toContain('disabled=""')
      expect(html).toContain('disabled:opacity-50')
    })

    it('renders loading state with spinner and aria-busy without layout shift', () => {
      const html = renderToStaticMarkup(<Button isLoading>Saving...</Button>)
      expect(html).toContain('aria-busy="true"')
      expect(html).toContain('disabled=""')
      expect(html).toContain('animate-spin')
      expect(html).toContain('Saving...')
    })

    it('renders left and right icons', () => {
      const left = <span data-testid="left-icon">←</span>
      const right = <span data-testid="right-icon">→</span>
      const html = renderToStaticMarkup(
        <Button leftIcon={left} rightIcon={right}>Next Step</Button>
      )
      expect(html).toContain('data-testid="left-icon"')
      expect(html).toContain('data-testid="right-icon"')
      expect(html).toContain('Next Step')
    })
  })

  // ---------------------------------------------------------------------------
  // 2. Card Tests
  // ---------------------------------------------------------------------------
  describe('Card Component', () => {
    it('renders full card hierarchy cleanly', () => {
      const html = renderToStaticMarkup(
        <Card>
          <CardHeader>
            <CardTitle>Scheme Overview</CardTitle>
            <CardDescription>Official government guidelines.</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Direct benefit transfer information.</p>
          </CardContent>
          <CardFooter>
            <Button>Apply Now</Button>
          </CardFooter>
        </Card>
      )
      expect(html).toContain('Scheme Overview')
      expect(html).toContain('Official government guidelines.')
      expect(html).toContain('Direct benefit transfer information.')
      expect(html).toContain('Apply Now')
      expect(html).toContain('rounded-lg')
      expect(html).toContain('border-gov-border/80')
    })

    it('supports interactive hover state', () => {
      const html = renderToStaticMarkup(<Card interactive>Interactive Card</Card>)
      expect(html).toContain('hover:shadow-md')
      expect(html).toContain('hover:-translate-y-0.5')
      expect(html).toContain('cursor-pointer')
    })

    it('supports custom heading tag via as prop', () => {
      const html = renderToStaticMarkup(<CardTitle as="h2">Level 2 Heading</CardTitle>)
      expect(html).toContain('<h2')
      expect(html).toContain('Level 2 Heading')
    })
  })

  // ---------------------------------------------------------------------------
  // 3. Input Tests
  // ---------------------------------------------------------------------------
  describe('Input Component', () => {
    it('renders input with associated label and required asterisk', () => {
      const html = renderToStaticMarkup(
        <Input id="citizen-name" label="Full Legal Name" required />
      )
      expect(html).toContain('for="citizen-name"')
      expect(html).toContain('id="citizen-name"')
      expect(html).toContain('Full Legal Name')
      expect(html).toContain('*')
      expect(html).toContain('required=""')
    })

    it('renders error state with role="alert" and aria-invalid', () => {
      const html = renderToStaticMarkup(
        <Input id="email" label="Email" errorText="Please enter a valid government email." />
      )
      expect(html).toContain('aria-invalid="true"')
      expect(html).toContain('aria-describedby="email-error"')
      expect(html).toContain('role="alert"')
      expect(html).toContain('border-gov-danger')
      expect(html).toContain('Please enter a valid government email.')
    })

    it('renders helper text and associates with aria-describedby', () => {
      const html = renderToStaticMarkup(
        <Input id="aadhaar" label="Aadhaar" helperText="12 digit unique identification number." />
      )
      expect(html).toContain('aria-describedby="aadhaar-helper"')
      expect(html).toContain('12 digit unique identification number.')
    })

    it('renders disabled input', () => {
      const html = renderToStaticMarkup(<Input disabled placeholder="Readonly" />)
      expect(html).toContain('disabled=""')
      expect(html).toContain('disabled:cursor-not-allowed')
    })
  })

  // ---------------------------------------------------------------------------
  // 4. Select Component
  // ---------------------------------------------------------------------------
  describe('Select Component', () => {
    it('renders select with options and custom chevron', () => {
      const options = [
        { value: 'tn', label: 'Tamil Nadu' },
        { value: 'ka', label: 'Karnataka' },
      ]
      const html = renderToStaticMarkup(
        <Select id="state-select" label="Select State" options={options} />
      )
      expect(html).toContain('for="state-select"')
      expect(html).toContain('id="state-select"')
      expect(html).toContain('value="tn"')
      expect(html).toContain('Tamil Nadu')
      expect(html).toContain('value="ka"')
      expect(html).toContain('Karnataka')
    })

    it('renders select with error state and aria-invalid', () => {
      const html = renderToStaticMarkup(
        <Select id="district" label="District" errorText="District is mandatory." />
      )
      expect(html).toContain('aria-invalid="true"')
      expect(html).toContain('aria-describedby="district-error"')
      expect(html).toContain('District is mandatory.')
      expect(html).toContain('border-gov-danger')
    })
  })

  // ---------------------------------------------------------------------------
  // 5. Badge Component
  // ---------------------------------------------------------------------------
  describe('Badge Component', () => {
    it('strictly preserves exact existing semantic classes', () => {
      expect(renderToStaticMarkup(<Badge variant="success">Eligible</Badge>)).toContain('badge-success')
      expect(renderToStaticMarkup(<Badge variant="warning">Verification Needed</Badge>)).toContain('badge-warning')
      expect(renderToStaticMarkup(<Badge variant="danger">Not Eligible</Badge>)).toContain('badge-danger')
      expect(renderToStaticMarkup(<Badge variant="open">Open</Badge>)).toContain('badge-open')
      expect(renderToStaticMarkup(<Badge variant="urgent">Urgent Deadline</Badge>)).toContain('badge-urgent')
      expect(renderToStaticMarkup(<Badge variant="warning-subtle">Unconfirmed</Badge>)).toContain('badge-warning-subtle')
      expect(renderToStaticMarkup(<Badge variant="neutral">Status Unknown</Badge>)).toContain('badge-neutral')
      expect(renderToStaticMarkup(<Badge variant="gov">Central Scheme</Badge>)).toContain('badge-gov')
    })

    it('renders dot indicator with correct semantic color', () => {
      const html = renderToStaticMarkup(<Badge variant="success" dot>Eligible</Badge>)
      expect(html).toContain('badge-dot')
      expect(html).toContain('dot-success')
    })
  })

  // ---------------------------------------------------------------------------
  // 6. Alert Component
  // ---------------------------------------------------------------------------
  describe('Alert Component', () => {
    it('preserves existing alert classes and sets role="alert"', () => {
      expect(renderToStaticMarkup(<Alert variant="danger">Invalid credentials</Alert>)).toContain('alert-danger')
      expect(renderToStaticMarkup(<Alert variant="success">Profile saved</Alert>)).toContain('alert-success')
      expect(renderToStaticMarkup(<Alert variant="info">New notification</Alert>)).toContain('alert-info')
      expect(renderToStaticMarkup(<Alert variant="warning">Application closing soon</Alert>)).toContain('alert-warning')

      const alertMarkup = renderToStaticMarkup(<Alert variant="info">Information</Alert>)
      expect(alertMarkup).toContain('role="alert"')
    })

    it('renders title and description cleanly', () => {
      const html = renderToStaticMarkup(
        <Alert variant="info" title="Verification Notice" description="Please submit income certificate." />
      )
      expect(html).toContain('Verification Notice')
      expect(html).toContain('Please submit income certificate.')
    })

    it('renders dismiss button when dismissible', () => {
      const html = renderToStaticMarkup(
        <Alert variant="info" dismissible>Dismissible alert</Alert>
      )
      expect(html).toContain('aria-label="Dismiss alert"')
    })
  })

  // ---------------------------------------------------------------------------
  // 7. Skeleton Component
  // ---------------------------------------------------------------------------
  describe('Skeleton Component', () => {
    it('renders basic skeleton with motion-reduce-safe animation and aria-hidden', () => {
      const html = renderToStaticMarkup(<Skeleton className="h-6 w-32" />)
      expect(html).toContain('animate-pulse')
      expect(html).toContain('motion-reduce:animate-none')
      expect(html).toContain('aria-hidden="true"')
    })

    it('renders SkeletonText, SkeletonAvatar, SkeletonCard, and SkeletonList presets', () => {
      expect(renderToStaticMarkup(<SkeletonText lines={3} />)).toContain('aria-hidden="true"')
      expect(renderToStaticMarkup(<SkeletonAvatar size="md" />)).toContain('rounded-full')
      expect(renderToStaticMarkup(<SkeletonCard />)).toContain('border-gov-border/80')
      expect(renderToStaticMarkup(<SkeletonList count={3} />)).toContain('space-y-3')
    })
  })

  // ---------------------------------------------------------------------------
  // 8. Dialog Component
  // ---------------------------------------------------------------------------
  describe('Dialog Component', () => {
    it('renders nothing when isOpen is false', () => {
      const html = renderToStaticMarkup(
        <Dialog isOpen={false} title="Modal Title">
          Modal content
        </Dialog>
      )
      expect(html).toBe('')
    })

    it('renders dialog with accessible attributes when isOpen is true', () => {
      const html = renderToStaticMarkup(
        <Dialog
          isOpen={true}
          title="Confirm Application"
          description="Are you sure you want to proceed?"
        >
          <p>Application submission verification.</p>
        </Dialog>
      )
      expect(html).toContain('role="dialog"')
      expect(html).toContain('aria-modal="true"')
      expect(html).toContain('Confirm Application')
      expect(html).toContain('Are you sure you want to proceed?')
      expect(html).toContain('Application submission verification.')
      expect(html).toContain('aria-label="Close dialog"')
    })
  })
})
