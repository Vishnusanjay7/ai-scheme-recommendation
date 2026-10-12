import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen, getConfirmedUserB } from '../fixtures/test-data.js'
import { loginUser } from '../utils/helpers.js'

test.describe('Security & Edge Cases', () => {
  test('direct URL access when unauthenticated redirects to login', async ({ page }) => {
    // Clear cookies/storage
    await page.context().clearCookies()
    
    const protectedRoutes = [
      '/dashboard',
      '/profile',
      '/recommendations',
      '/saved-schemes',
      '/notifications',
      '/chatbot',
    ]

    for (const route of protectedRoutes) {
      await page.goto(route)
      await expect(page).toHaveURL(/.*\/login/, { timeout: 7000 })
    }
  })

  test('localStorage does not store plaintext passwords or service keys', async ({ page }) => {
    const citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
    await page.goto('/profile')
    await expect(page).toHaveURL(/.*\/profile/, { timeout: 10000 })

    const storage = await page.evaluate(() => JSON.stringify(window.localStorage))

    // Check for plaintext password
    expect(storage).not.toContain(citizen.password)

    // Check for leaked keys/tokens that shouldn't be in localStorage
    expect(storage.toLowerCase()).not.toContain('service_role')
    expect(storage.toLowerCase()).not.toContain('parse_api_key')
    expect(storage.toLowerCase()).not.toContain('openai_api_key')
  })

  test('client bundle & DOM do not expose secret backend keys', async ({ page }) => {
    await page.goto('/login')

    // Inspect script contents and page HTML
    const pageHtml = await page.content()
    expect(pageHtml).not.toContain('service_role')
    expect(pageHtml).not.toContain('OPENAI_API_KEY')
    expect(pageHtml).not.toContain('PARSE_API_KEY')

    // Inspect window global properties
    const leakedGlobals = await page.evaluate(() => {
      const keys = Object.keys(window)
      return keys.filter(k => 
        k.toLowerCase().includes('secret') || 
        k.toLowerCase().includes('service_role') ||
        k.toLowerCase().includes('parse_api')
      )
    })
    expect(leakedGlobals).toEqual([])
  })

  test('session isolation ensures User A cannot see User B data', async ({ browser }) => {
    const userA = getConfirmedTestCitizen()
    const userB = getConfirmedUserB()

    // Context A for User A
    const contextA = await browser.newContext()
    const pageA = await contextA.newPage()
    await loginUser(pageA, userA.email, userA.password)
    await pageA.waitForURL('**/dashboard', { timeout: 15000 })
    await pageA.goto('/profile')
    await expect(pageA).toHaveURL(/.*\/profile/, { timeout: 10000 })
    const aEmail = await pageA.locator('#userEmail').inputValue().catch(() => '')
    expect(aEmail).toBe(userA.email)

    // Context B for User B
    const contextB = await browser.newContext()
    const pageB = await contextB.newPage()
    await loginUser(pageB, userB.email, userB.password)
    await pageB.waitForURL('**/dashboard', { timeout: 15000 })
    await pageB.goto('/profile')
    await expect(pageB).toHaveURL(/.*\/profile/, { timeout: 10000 })

    // Verify User B's profile form displays User B's email, strictly isolated from User A
    const bEmail = await pageB.locator('#userEmail').inputValue().catch(() => '')
    expect(bEmail).not.toBe(userA.email)
    expect(bEmail).toBe(userB.email)

    await contextA.close()
    await contextB.close()
  })

  test('XSS sanitization in profile inputs prevents script execution', async ({ page }) => {
    const citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
    await page.goto('/profile')
    await expect(page).toHaveURL(/.*\/profile/, { timeout: 10000 })

    let dialogFired = false
    page.on('dialog', async dialog => {
      dialogFired = true
      await dialog.dismiss()
    })

    const xssPayload = "<script>alert('xss')</script>"
    await page.fill('#fullName', xssPayload)
    await page.fill('#age', '30')
    await page.selectOption('#gender', 'MALE')
    await page.selectOption('#stateId', '23')
    await page.fill('#annualIncome', '200000')
    await page.selectOption('#occupation', 'Farmer')
    await page.selectOption('#education', "Graduate / Bachelor's")
    await page.selectOption('#category', 'General')
    await page.click('button[type="submit"]')

    await page.waitForTimeout(1000)
    expect(dialogFired).toBe(false)
  })

  test('form submit button behaves reliably during rapid clicks', async ({ page }) => {
    const citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
    await page.goto('/profile')
    await expect(page).toHaveURL(/.*\/profile/, { timeout: 10000 })

    await page.fill('#age', citizen.age)
    await page.selectOption('#gender', citizen.gender)
    await page.selectOption('#stateId', citizen.stateId)
    await page.fill('#annualIncome', citizen.annualIncome)
    await page.selectOption('#occupation', citizen.occupation)
    await page.selectOption('#education', citizen.education)
    await page.selectOption('#category', citizen.category)

    const submitBtn = page.locator('button[type="submit"]')
    // Click rapidly twice
    await submitBtn.click({ clickCount: 2, delay: 50 }).catch(() => {})

    await page.waitForTimeout(1500)
    // Verify page didn't crash or trigger unhandled error boundary
    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toContain('Application Error')
    expect(bodyText).not.toContain('Unhandled Runtime Error')
  })
})
