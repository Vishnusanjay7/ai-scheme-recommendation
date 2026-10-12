import { describe, it, expect, vi } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import Login from '../pages/Login'
import { AuthContext } from '../context/authContextInstance'

function renderLoginWithContext(authValue = {}, routerEntries = ['/login']) {
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
        <Login />
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('Login Page Unit Tests', () => {
  it('1. Renders Citizen Login title and subtitle', () => {
    const html = renderLoginWithContext()
    expect(html).toContain('Citizen Login')
    expect(html).toContain('Sign in to access your scheme recommendations and profile')
  })

  it('2. Renders email and password fields with correct autocomplete and name attributes', () => {
    const html = renderLoginWithContext()
    expect(html).toContain('id="login-email"')
    expect(html).toContain('name="email"')
    expect(html).toContain('autoComplete="email"')
    expect(html).toContain('id="login-password"')
    expect(html).toContain('name="password"')
    expect(html).toContain('autoComplete="current-password"')
  })

  it('3. Renders submit button and link to registration page', () => {
    const html = renderLoginWithContext()
    expect(html).toContain('Sign In')
    expect(html).toContain('New citizen?')
    expect(html).toContain('href="/register"')
  })

  it('4. Renders loading state spinner while verifying citizen session', () => {
    const html = renderLoginWithContext({ loading: true })
    expect(html).toContain('page-loading')
    expect(html).toContain('Verifying citizen session...')
    expect(html).not.toContain('Citizen Login')
  })
})
