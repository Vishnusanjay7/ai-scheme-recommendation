import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen } from '../fixtures/test-data'
import { loginUser } from '../utils/helpers'

test.describe('User Profile E2E Tests', () => {
  let citizen

  test.beforeEach(async ({ page }) => {
    citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
  })

  test('1 to 11. Profile form fields entry and state/district dynamic cascade', async ({ page }) => {
    await page.goto('/profile')
    await expect(page.locator('h2')).toContainText('Citizen Demographic Profile')

    // Fill demographic inputs
    await page.fill('#age', citizen.age)
    await page.selectOption('#gender', citizen.gender)
    await page.fill('#annualIncome', citizen.annualIncome)
    await page.selectOption('#occupation', citizen.occupation)
    await page.selectOption('#education', citizen.education)
    await page.selectOption('#category', citizen.category)

    // Verify disability toggle
    const disabilityCheckbox = page.locator('#disabilityStatus')
    await expect(disabilityCheckbox).toBeVisible()
    await disabilityCheckbox.check()
    expect(await disabilityCheckbox.isChecked()).toBe(true)

    // Test State Selection -> Dynamic District cascade
    const stateSelect = page.locator('#stateId')
    await expect(stateSelect).toBeVisible()
    await stateSelect.selectOption('23') // Tamil Nadu

    // Wait for districts to populate
    const districtSelect = page.locator('#districtId')
    await expect(districtSelect).toBeEnabled({ timeout: 10000 })
    const districtOptions = await districtSelect.locator('option').allInnerTexts()
    expect(districtOptions.some((opt) => opt.includes('Chennai'))).toBeTruthy()

    // Select District
    await districtSelect.selectOption({ label: 'Chennai' })
  })

  test('12, 13 & 14. Profile saves successfully, survives refresh, and allows editing', async ({ page }) => {
    await page.goto('/profile')

    // Fill and submit profile
    await page.fill('#age', '21')
    await page.selectOption('#gender', 'FEMALE')
    await page.selectOption('#stateId', '23')
    await page.waitForTimeout(1000)
    await page.selectOption('#districtId', { label: 'Chennai' })
    await page.fill('#annualIncome', '150000')
    await page.selectOption('#occupation', 'Student')
    await page.selectOption('#education', 'Higher Secondary (12th)')
    await page.selectOption('#category', 'General')

    await page.click('button[type="submit"]')
    const alertSuccess = page.locator('.alert-success')
    await expect(alertSuccess).toBeVisible({ timeout: 10000 })
    await expect(alertSuccess).toContainText('saved successfully')

    // Survives page refresh
    await page.reload()
    await expect(page.locator('#age')).toHaveValue('21')
    await expect(page.locator('#gender')).toHaveValue('FEMALE')
    await expect(page.locator('#annualIncome')).toHaveValue('150000')
    await expect(page.locator('#occupation')).toHaveValue('Student')

    // Edit profile
    await page.fill('#age', '22')
    await page.click('button[type="submit"]')
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 10000 })

    await page.reload()
    await expect(page.locator('#age')).toHaveValue('22')
  })
})
