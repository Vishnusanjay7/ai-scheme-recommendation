/**
 * E2E Test Helper Functions
 */

export async function registerNewUser(page, user) {
  await page.goto('/register')
  await page.fill('#fullName', user.fullName)
  await page.fill('#email', user.email)
  await page.fill('#password', user.password)
  await page.fill('#confirmPassword', user.password)
  await page.click('button[type="submit"]')
}

export async function loginUser(page, email, password) {
  await page.goto('/login')
  await page.fill('#login-email', email)
  await page.fill('#login-password', password)
  await page.click('button[type="submit"]')
}

export async function logoutUser(page) {
  const logoutBtn = page.locator('button.btn-logout')
  if (await logoutBtn.isVisible()) {
    await logoutBtn.click()
    await page.waitForURL('**/login')
  }
}

export async function registerAndLogin(page, user) {
  await registerNewUser(page, user)
  // Wait for either direct navigation to dashboard or account creation success alert
  try {
    await page.waitForFunction(
      () => window.location.pathname.includes('/dashboard') || document.querySelector('.alert-success'),
      { timeout: 15000 }
    )
  } catch {
    // proceed to check url
  }

  if (!page.url().includes('/dashboard')) {
    await loginUser(page, user.email, user.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 }).catch(() => {})
  }
}

