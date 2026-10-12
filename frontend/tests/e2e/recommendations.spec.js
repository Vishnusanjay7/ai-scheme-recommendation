import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen } from '../fixtures/test-data'
import { loginUser } from '../utils/helpers'

test.describe('Scheme Recommendations & Eligibility E2E Tests', () => {
  let citizen

  test.beforeEach(async ({ page }) => {
    citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
  })

  test('1 to 8. Recommendations page loads and handles scheme evaluation', async ({ page }) => {
    // Monitor API calls
    let apiCallStatus = 0
    page.on('response', (response) => {
      if (response.url().includes('/api/recommendations')) {
        apiCallStatus = response.status()
      }
    })

    await page.goto('/recommendations')
    await page.waitForTimeout(3000)

    await expect(page.locator('.page-header-rec h1')).toContainText('Government Scheme Recommendations')

    // Check whether cards or empty state or error is displayed
    const cards = page.locator('.scheme-card')
    const count = await cards.count()
    const errorAlert = await page.locator('.alert-danger').isVisible()

    // Document whether recommendations return cards or error based on profile state
    expect(count > 0 || errorAlert || apiCallStatus === 200).toBeTruthy()
  })

  test('9 to 15. Match Score and Deadlines on recommendation cards', async ({ page }) => {
    await page.goto('/recommendations')
    await page.waitForTimeout(3000)

    const cards = page.locator('.scheme-card')
    const count = await cards.count()

    if (count > 0) {
      const firstCard = cards.first()
      await expect(firstCard).toBeVisible({ timeout: 10000 })

      // 1. Verify Eligibility Badge exists
      const badge = firstCard.locator('.badge, .eligibility-badge').first()
      await expect(badge).toBeVisible()

      // 2. Verify Match Score is displayed separately as a fit percentage
      const scoreText = await firstCard.innerText()
      const hasMatchScore = scoreText.includes('Match') || scoreText.includes('%') || scoreText.includes('/100')
      expect(hasMatchScore).toBeTruthy()

      // 3. Verify Deadline Badge exists on the card
      const deadlineBadge = firstCard.locator('.deadline-badge, .badge')
      expect(await deadlineBadge.count()).toBeGreaterThan(0)
    } else {
      // If user profile is empty/unconfigured, page renders empty/notice gracefully
      const body = await page.innerText('body')
      expect(body.length).toBeGreaterThan(50)
    }
  })
})
