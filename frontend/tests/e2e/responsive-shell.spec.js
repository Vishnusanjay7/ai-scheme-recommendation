import { test, expect } from '@playwright/test'

test.describe('Responsive Application Shell & Navbar E2E Tests', () => {
  const viewports = [
    { width: 320, height: 568, name: '320px Mobile' },
    { width: 375, height: 667, name: '375px Mobile' },
    { width: 768, height: 1024, name: '768px Tablet' },
    { width: 1024, height: 768, name: '1024px Laptop' },
    { width: 1440, height: 900, name: '1440px Desktop' },
  ]

  for (const vp of viewports) {
    test(`No horizontal overflow on ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height })
      await page.goto('/login')
      await page.waitForLoadState('domcontentloaded')

      const isOverflowing = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth
      })
      expect(isOverflowing).toBe(false)
    })
  }

  test('Mobile drawer opens, closes on escape, and has proper navigation', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/login')

    const toggleBtn = page.locator('#mobile-nav-toggle')
    await expect(toggleBtn).toBeVisible()

    // Desktop nav is hidden on mobile
    await expect(page.locator('nav.nav-links')).toBeHidden()

    // Mobile menu starts closed
    await expect(page.locator('#mobile-nav-menu')).toHaveCount(0)

    // Open mobile menu
    await toggleBtn.click()
    const mobileMenu = page.locator('#mobile-nav-menu')
    await expect(mobileMenu).toBeVisible()
    await expect(mobileMenu.locator('a[href="/login"]')).toBeVisible()
    await expect(mobileMenu.locator('a[href="/register"]')).toBeVisible()

    // Press Escape to close
    await page.keyboard.press('Escape')
    await expect(page.locator('#mobile-nav-menu')).toHaveCount(0)
  })

  test('Skip to main content accessibility link is present and targets #main-content', async ({ page }) => {
    await page.goto('/login')
    const skipLink = page.locator('a[href="#main-content"]')
    await expect(skipLink).toBeAttached()
    await expect(skipLink).toHaveText('Skip to main content')

    const mainTarget = page.locator('#main-content')
    await expect(mainTarget).toBeAttached()
  })

  test('Footer displays academic prototype notice and external reference links', async ({ page }) => {
    await page.goto('/login')
    const footer = page.locator('footer.portal-footer')
    await expect(footer).toBeVisible()
    await expect(footer).toContainText('SchemeSetu')
    await expect(footer).toContainText('Academic Project Prototype')

    // Check external links have rel="noopener noreferrer"
    const externalLinks = footer.locator('a[target="_blank"]')
    const count = await externalLinks.count()
    expect(count).toBeGreaterThanOrEqual(4)
    for (let i = 0; i < count; i++) {
      const rel = await externalLinks.nth(i).getAttribute('rel')
      expect(rel).toContain('noopener')
      expect(rel).toContain('noreferrer')
    }
  })
})
