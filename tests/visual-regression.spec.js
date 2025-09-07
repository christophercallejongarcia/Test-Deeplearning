import { test, expect } from '@playwright/test';

test.describe('NEW CHAT Button Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000/');
    await page.waitForLoadState('networkidle');
  });

  test('should match button visual baseline', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Take screenshot of just the button
    await expect(button).toHaveScreenshot('new-chat-button-baseline.png');
  });

  test('should match button hover state', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Hover over button
    await button.hover();
    
    // Take screenshot of hover state
    await expect(button).toHaveScreenshot('new-chat-button-hover.png');
  });

  test('should match button focus state', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Focus the button
    await button.focus();
    
    // Take screenshot of focus state
    await expect(button).toHaveScreenshot('new-chat-button-focus.png');
  });

  test('should match button active state', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Simulate active state by holding down mouse
    await button.hover();
    await page.mouse.down();
    
    // Take screenshot of active state
    await expect(button).toHaveScreenshot('new-chat-button-active.png');
    
    await page.mouse.up();
  });

  test('should match sidebar section with button', async ({ page }) => {
    const sidebarSection = page.locator('.sidebar-section').first();
    
    // Take screenshot of entire button section
    await expect(sidebarSection).toHaveScreenshot('new-chat-button-section.png');
  });

  test('should match button across different viewport sizes', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(button).toHaveScreenshot('new-chat-button-desktop.png');
    
    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(button).toHaveScreenshot('new-chat-button-tablet.png');
    
    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(button).toHaveScreenshot('new-chat-button-mobile.png');
  });

  test('should maintain visual consistency in dark theme context', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Take full sidebar screenshot to show button in context
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).toHaveScreenshot('sidebar-with-new-chat-button.png');
  });

  test('should handle text overflow gracefully', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Test with longer text (simulate different languages)
    await button.evaluate((el) => {
      el.textContent = '+ NEUE UNTERHALTUNG STARTEN';
    });
    
    await expect(button).toHaveScreenshot('new-chat-button-long-text.png');
    
    // Reset text
    await button.evaluate((el) => {
      el.textContent = '+ NEW CHAT';
    });
  });
});