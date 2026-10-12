import { describe, it, expect, vi } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import Register from '../pages/Register'
import { AuthContext } from '../context/authContextInstance'

function renderRegisterWithContext(authValue = {}, routerEntries = ['/register']) {
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
        <Register />
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('Register Page Unit Tests', () => {
  it('1. Renders Citizen Registration title and subtitle', () => {
    const html = renderRegisterWithContext()
    expect(html).toContain('Citizen Registration')
    expect(html).toContain('Create an account to discover verified welfare schemes tailored to you')
  })

  it('2. Renders all fields with correct IDs, names, and autocomplete attributes', () => {
    const html = renderRegisterWithContext()
    expect(html).toContain('id="fullName"')
    expect(html).toContain('name="fullName"')
    expect(html).toContain('autoComplete="name"')

    expect(html).toContain('id="email"')
    expect(html).toContain('name="email"')
    expect(html).toContain('autoComplete="email"')

    expect(html).toContain('id="password"')
    expect(html).toContain('name="password"')
    expect(html).toContain('autoComplete="new-password"')

    expect(html).toContain('id="confirmPassword"')
    expect(html).toContain('name="confirmPassword"')
  })

  it('3. Renders submit button and link to login page', () => {
    const html = renderRegisterWithContext()
    expect(html).toContain('Register')
    expect(html).toContain('Already have an account?')
    expect(html).toContain('href="/login"')
  })

  it('4. Renders loading state spinner while verifying citizen session', () => {
    const html = renderRegisterWithContext({ loading: true })
    expect(html).toContain('page-loading')
    expect(html).toContain('Verifying citizen session...')
    expect(html).not.toContain('Citizen Registration')
  })
})
