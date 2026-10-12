import { describe, it, expect, vi } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { AuthContext } from '../context/authContextInstance'

function renderWithContext(component, authValue = {}, routerEntries = ['/']) {
  const defaultAuth = {
    user: null,
    session: null,
    token: null,
    loading: false,
    authError: null,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    isAuthenticated: false,
    ...authValue,
  }

  return renderToStaticMarkup(
    <AuthContext.Provider value={defaultAuth}>
      <MemoryRouter initialEntries={routerEntries}>
        {component}
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('Navbar Component Unit Tests', () => {
  it('1. Renders SchemeSetu brand wordmark, prototype tag, and portal subtitle', () => {
    const html = renderWithContext(<Navbar />)
    expect(html).toContain('SchemeSetu')
    expect(html).toContain('Prototype')
    expect(html).toContain('Government Scheme Discovery Portal')
    expect(html).toContain('brand-logo')
  })

  it('2. Renders Login and Register links for unauthenticated visitors', () => {
    const html = renderWithContext(<Navbar />, { isAuthenticated: false })
    expect(html).toContain('href="/login"')
    expect(html).toContain('href="/register"')
    expect(html).toContain('btn-nav-cta')
    expect(html).not.toContain('btn-logout')
    expect(html).not.toContain('href="/saved-schemes"')
  })

  it('3. Renders citizen navigation links, user name, and logout button when authenticated', () => {
    const mockUser = {
      email: 'citizen.kumar@example.com',
      user_metadata: { full_name: 'Rajesh Kumar' },
    }
    const html = renderWithContext(
      <Navbar />,
      {
        isAuthenticated: true,
        user: mockUser,
        session: { access_token: 'fake-token' },
      },
      ['/dashboard']
    )

    expect(html).toContain('href="/dashboard"')
    expect(html).toContain('href="/recommendations"')
    expect(html).toContain('href="/saved-schemes"')
    expect(html).toContain('href="/chatbot"')
    expect(html).toContain('href="/notifications"')
    expect(html).toContain('href="/profile"')
    expect(html).toContain('Rajesh Kumar')
    expect(html).toContain('btn-logout')
    expect(html).not.toContain('href="/register"')
  })

  it('4. Renders mobile toggle button with accessible aria attributes', () => {
    const html = renderWithContext(<Navbar />)
    expect(html).toContain('id="mobile-nav-toggle"')
    expect(html).toContain('aria-label="Open navigation menu"')
    expect(html).toContain('aria-controls="mobile-nav-menu"')
  })
})

describe('Footer Component Unit Tests', () => {
  it('1. Renders academic prototype disclaimer and no-endorsement notice', () => {
    const html = renderWithContext(<Footer />)
    expect(html).toContain('portal-footer')
    expect(html).toContain('footer-inner')
    expect(html).toContain('academic capstone prototype')
    expect(html).toContain('Independent Academic Project')
  })

  it('2. Renders official government reference portals with security attributes', () => {
    const html = renderWithContext(<Footer />)
    expect(html).toContain('https://www.india.gov.in')
    expect(html).toContain('https://www.myscheme.gov.in')
    expect(html).toContain('https://dbtbharat.gov.in')
    expect(html).toContain('https://digitalindia.gov.in')
    expect(html).toContain('target="_blank"')
    expect(html).toContain('rel="noopener noreferrer"')
  })

  it('3. Renders deterministic rule engine invariant description', () => {
    const html = renderWithContext(<Footer />)
    expect(html).toContain('Deterministic Rules')
    expect(html).toContain('Verification Mandate')
  })

  it('4. Renders current dynamic year in copyright notice', () => {
    const currentYear = new Date().getFullYear().toString()
    const html = renderWithContext(<Footer />)
    expect(html).toContain(currentYear)
  })
})
