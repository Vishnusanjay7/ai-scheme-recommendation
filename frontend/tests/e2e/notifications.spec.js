import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen } from '../fixtures/test-data'
import { loginUser } from '../utils/helpers'

test.describe('Notifications & Deadline Alerts E2E Tests', () => {
  let citizen

  test.beforeEach(async ({ page }) => {
    citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
  })

  test('1 to 6. Notifications page loads, displays user alerts, and handles empty state cleanly', async ({ page }) => {
    await page.goto('/notifications')
    await page.waitForTimeout(2000)

    // Verify header
    await expect(page.locator('h1')).toContainText('Citizen Notifications')

    // For a citizen, either empty state or list of alerts appears
    const emptyState = page.locator('.empty-notif-state')
    const notifItems = page.locator('.notif-item')

    const hasEmpty = await emptyState.isVisible()
    const hasItems = (await notifItems.count()) > 0

    expect(hasEmpty || hasItems).toBeTruthy()

    if (hasItems) {
      // Check first notification message content
      const firstMsg = page.locator('.notif-content, .notif-item').first()
      await expect(firstMsg).toBeVisible()

      // Mark as read button
      const markBtn = page.locator('button:has-text("Mark Read"), button:has-text("Mark as Read")').first()
      if (await markBtn.isVisible()) {
        await markBtn.click()
        await page.waitForTimeout(500)
      }
    }
  })
})
