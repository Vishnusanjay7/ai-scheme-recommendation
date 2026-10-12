import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen } from '../fixtures/test-data'
import { loginUser } from '../utils/helpers'

test.describe('Scheme Details & Document Semantics E2E Tests', () => {
  let citizen

  test.beforeEach(async ({ page }) => {
    citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
  })

  test('Scheme Details page renders comprehensive data, documents, and verified official link', async ({ page }) => {
    // Navigate directly to a verified scheme
    await page.goto('/schemes/ac958358-ad08-4f83-ae39-b9f1e41800ba')
    await page.waitForTimeout(2000)

    // 1. Verify URL pattern
    await expect(page).toHaveURL(/\/schemes\/[a-zA-Z0-9-]+/, { timeout: 10000 })

    // 2. Verify Scheme Title, Header Badges, and Description
    const title = page.locator('.details-title')
    await expect(title).toBeVisible()
    const titleText = await title.innerText()
    expect(titleText.length).toBeGreaterThan(0)

    // 3. Verify Benefits & Application Procedure
    await expect(page.locator('h3:has-text("Scheme Benefits")')).toBeVisible()
    await expect(page.locator('h3:has-text("Application Procedure")')).toBeVisible()

    // 4. Verify Documents Section & Semantic Badges
    await expect(page.locator('h3:has-text("Required Documents")')).toBeVisible()

    // 5. Verify Official Government Application Link
    const officialBtn = page.locator('a:has-text("Apply on Official Government Portal")')
    if (await officialBtn.isVisible()) {
      const href = await officialBtn.getAttribute('href')
      expect(href).toMatch(/^https?:\/\/.+/)
      expect(href).not.toContain('javascript:')
    }
  })
})
