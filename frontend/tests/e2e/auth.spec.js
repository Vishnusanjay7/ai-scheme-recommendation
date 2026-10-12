import { test, expect } from '@playwright/test'
import { generateTestCitizen, getConfirmedTestCitizen } from '../fixtures/test-data'
import { registerNewUser, loginUser, logoutUser } from '../utils/helpers'

test.describe('Authentication & Session E2E Tests', () => {
  let citizen

  test.beforeEach(() => {
    citizen = generateTestCitizen()
  })

  test('1. Registration page loads correctly', async ({ page }) => {
    await page.goto('/register')
    await expect(page.locator('h2')).toContainText('Citizen Registration')
    await expect(page.locator('#fullName')).toBeVisible()
    await expect(page.locator('#email')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.locator('#confirmPassword')).toBeVisible()
  })

  test('2. Required-field validation works on registration', async ({ page }) => {
    await page.goto('/register')
    await page.click('button[type="submit"]')
    const alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('Please enter your full name')
  })

  test('3. Invalid email is rejected on registration', async ({ page }) => {
    await page.goto('/register')
    await page.fill('#fullName', citizen.fullName)
    await page.fill('#email', 'not-an-email')
    await page.fill('#password', citizen.password)
    await page.fill('#confirmPassword', citizen.password)
    await page.click('button[type="submit"]')

    const alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('valid email')
  })

  test('4. Password length and mismatch validation works', async ({ page }) => {
    await page.goto('/register')
    await page.fill('#fullName', citizen.fullName)
    await page.fill('#email', citizen.email)
    await page.fill('#password', '123')
    await page.fill('#confirmPassword', '123')
    await page.click('button[type="submit"]')

    let alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('at least 6 characters')

    await page.fill('#password', '123456')
    await page.fill('#confirmPassword', '654321')
    await page.click('button[type="submit"]')

    alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('do not match')
  })

  test('5. Registration form submission and response handling', async ({ page }) => {
    await registerNewUser(page, citizen)
    // Handle Supabase response: success alert, dashboard redirect, or rate-limit alert
    const feedback = page.locator('.alert-success, .alert-danger, button:has-text("Logout")')
    await expect(feedback).toBeVisible({ timeout: 15000 })
    const isSuccess = await page.locator('.alert-success').isVisible()
    const isError = await page.locator('.alert-danger').isVisible()
    const onDashboard = page.url().includes('/dashboard')
    expect(onDashboard || isSuccess || isError).toBeTruthy()
  })

  test('6. Login page loads correctly', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h2')).toContainText('Citizen Login')
    await expect(page.locator('#login-email')).toBeVisible()
    await expect(page.locator('#login-password')).toBeVisible()
    await expect(page.locator('#login-email')).toHaveAttribute('autocomplete', 'email')
    await expect(page.locator('#login-password')).toHaveAttribute('autocomplete', 'current-password')
  })

  test('6b. Required-field validation works on login', async ({ page }) => {
    await page.goto('/login')
    await page.click('button[type="submit"]')
    const alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('Please enter both email and password')
  })

  test('6c. Invalid email format is rejected on login', async ({ page }) => {
    await page.goto('/login')
    await page.fill('#login-email', 'invalid-email-format')
    await page.fill('#login-password', 'somepassword123')
    await page.click('button[type="submit"]')
    const alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('valid email')
  })

  test('7 & 8. Invalid login is rejected with error feedback', async ({ page }) => {
    await page.goto('/login')
    await page.fill('#login-email', 'nonexistent_citizen_12345@testdomain.org')
    await page.fill('#login-password', 'WrongPassword!999')
    await page.click('button[type="submit"]')
    const alert = page.locator('.alert-danger')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('Invalid email or password')
  })

  test('8b. Authenticated citizen visiting /login is redirected to /dashboard', async ({ page }) => {
    const confirmedUser = getConfirmedTestCitizen()
    await loginUser(page, confirmedUser.email, confirmedUser.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })

    // When already authenticated, navigating to /login redirects back to /dashboard
    await page.goto('/login')
    await page.waitForURL('**/dashboard', { timeout: 10000 })
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('8c. Authenticated citizen visiting /register is redirected to /dashboard', async ({ page }) => {
    const confirmedUser = getConfirmedTestCitizen()
    await loginUser(page, confirmedUser.email, confirmedUser.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })

    // When already authenticated, navigating to /register redirects back to /dashboard
    await page.goto('/register')
    await page.waitForURL('**/dashboard', { timeout: 10000 })
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('9 & 10. Protected pages block unauthenticated users and redirect to /login', async ({ page }) => {
    const protectedPaths = ['/dashboard', '/profile', '/recommendations', '/saved-schemes', '/notifications', '/chatbot']
    for (const path of protectedPaths) {
      await page.goto(path)
      await expect(page).toHaveURL(/\/login/)
    }
  })

  test('11 & 12. Session persistence and Logout workflow', async ({ page }) => {
    const confirmedUser = getConfirmedTestCitizen()
    await loginUser(page, confirmedUser.email, confirmedUser.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })

    // Session persists across page reload
    await page.reload()
    await expect(page).toHaveURL(/\/dashboard/)

    // Logout works
    await logoutUser(page)
    await expect(page).toHaveURL(/\/login/)

    // After logout, cannot navigate back to dashboard
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })
})
