import { test, expect } from '@playwright/test'
import { getConfirmedTestCitizen } from '../fixtures/test-data'
import { loginUser } from '../utils/helpers'

test.describe('Multilingual Conversational Chatbot E2E Tests', () => {
  let citizen

  test.beforeEach(async ({ page }) => {
    citizen = getConfirmedTestCitizen()
    await loginUser(page, citizen.email, citizen.password)
    await page.waitForURL('**/dashboard', { timeout: 15000 })
  })

  test('1 to 10. Chatbot loads, processes English and Tamil queries', async ({ page }) => {
    await page.goto('/chatbot')
    await expect(page.locator('h1')).toContainText('AI Scheme Assistant')

    // 1. Initial greeting exists
    await expect(page.locator('.chat-messages-container')).toContainText('Hello! I can help you find government schemes')

    // 2. Send English question
    const chatInput = page.locator('#chat-message-input')
    await chatInput.fill('What education scholarships can a college student in Tamil Nadu apply for?')
    await page.click('#chat-send-button')

    // Wait for response
    await page.waitForTimeout(4000)
    const botMessages = page.locator('.chat-msg-bot, .chat-bubble')
    await expect(botMessages.last()).toBeVisible({ timeout: 15000 })
    const replyText = await botMessages.last().innerText()
    expect(replyText.length).toBeGreaterThan(10)

    // 3. Send Tamil question using quick prompt or typing
    const tamilPromptBtn = page.locator('button.btn-prompt-chip:has-text("தமிழ்")').first()
    if (await tamilPromptBtn.isVisible()) {
      await tamilPromptBtn.click()
    } else {
      await chatInput.fill('நான் தமிழ்நாட்டில் படிக்கும் மாணவி. எனக்கு என்ன கல்வி உதவித்தொகை கிடைக்கும்?')
      await page.click('#chat-send-button')
    }

    await page.waitForTimeout(4000)
    const allBotMessages = page.locator('.chat-msg-bot, .chat-bubble')
    const finalReply = await allBotMessages.last().innerText()
    expect(finalReply.length).toBeGreaterThan(10)
  })
})
