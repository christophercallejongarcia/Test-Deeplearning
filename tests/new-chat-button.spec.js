import { test, expect } from '@playwright/test';

test.describe('NEW CHAT Button Optimization Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000/');
  });

  test('should have optimized selectors and be accessible', async ({ page }) => {
    // Test 1: Robust selectors - ID is most stable
    const buttonById = page.locator('#newChatButton');
    await expect(buttonById).toBeVisible();
    
    // Test 2: Class selector as fallback
    const buttonByClass = page.locator('.new-chat-button');
    await expect(buttonByClass).toBeVisible();
    
    // Test 3: Accessible role-based selector
    const buttonByRole = page.getByRole('button', { name: '+ NEW CHAT' });
    await expect(buttonByRole).toBeVisible();
  });

  test('should have proper accessibility attributes', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Test aria-label for screen readers
    await expect(button).toHaveAttribute('aria-label', 'Start new chat conversation');
    
    // Test button is enabled and clickable
    await expect(button).toBeEnabled();
    
    // Test proper role
    await expect(button).toHaveRole('button');
  });

  test('should handle interactions properly', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Wait for button to be ready
    await button.waitFor({ state: 'visible' });
    
    // Test hover state
    await button.hover();
    
    // Test click functionality
    await button.click();
    
    // Verify chat input is focused after click (expected behavior)
    const chatInput = page.locator('#chatInput');
    await expect(chatInput).toBeFocused();
  });

  test('should maintain consistent styling', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Test computed styles match design system
    const styles = await button.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        color: computed.color,
        padding: computed.padding,
        borderRadius: computed.borderRadius,
        cursor: computed.cursor
      };
    });
    
    expect(styles.backgroundColor).toBe('rgb(30, 41, 59)'); // Dark blue
    expect(styles.color).toBe('rgb(241, 245, 249)'); // Light text
    expect(styles.padding).toBe('16px 24px');
    expect(styles.borderRadius).toBe('12px');
    expect(styles.cursor).toBe('pointer');
  });

  test('should be responsive across different screen sizes', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(button).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(button).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(button).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    const button = page.locator('#newChatButton');
    
    // Focus button with keyboard
    await page.keyboard.press('Tab');
    await expect(button).toBeFocused();
    
    // Activate with Enter key
    await page.keyboard.press('Enter');
    
    // Verify expected behavior
    const chatInput = page.locator('#chatInput');
    await expect(chatInput).toBeFocused();
    
    // Test Space key activation
    await button.focus();
    await page.keyboard.press(' ');
    await expect(chatInput).toBeFocused();
  });
});