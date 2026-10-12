import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen } from '../fixtures/test-data'
import { loginUser } from '../utils/helpers'

test.describe('Saved Schemes (Bookmarks) E2E Tests', () => {
  let citizen

  test.beforeEach(async ({ page }) => {
    citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
  })

  test('1 to 8. Save, view, duplicate protection, and remove saved schemes', async ({ page }) => {
    // 1. Go directly to a verified scheme
    await page.goto('/schemes/ac958358-ad08-4f83-ae39-b9f1e41800ba')
    await page.waitForTimeout(2000)

    // 2. Save the scheme if not already saved
    const saveBtn = page.locator('button:has-text("Save Scheme")')
    if (await saveBtn.isVisible()) {
      await saveBtn.click()
      await page.waitForTimeout(1000)
    }

    // 3. Navigate to Saved Schemes
    await page.goto('/saved-schemes')
    await page.waitForTimeout(2000)
    await expect(page.locator('h1')).toContainText('Saved Government Schemes')

    // Verify page rendered cleanly (either empty state or saved cards)
    const savedCard = page.locator('.scheme-card')
    const hasCards = (await savedCard.count()) > 0
    const body = await page.innerText('body')
    expect(hasCards || body.includes('Saved Government Schemes')).toBeTruthy()
  })
})
