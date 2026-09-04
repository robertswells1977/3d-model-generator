import { test, expect } from '@playwright/test';

test('app loads without console errors and shows login screen', async ({ page }) => {
  const errors: string[] = [];
  
  page.on('pageerror', error => {
    console.log("PAGE ERROR:", error);
    errors.push(`PageError: ${error.message}`);
  });

  page.on('console', msg => {
    console.log(`CONSOLE [${msg.type()}]: ${msg.text()}`);
    if (msg.type() === 'error') {
      errors.push(`ConsoleError: ${msg.text()}`);
    }
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');

  console.log("DOM content:", await page.content());

  const heading = page.locator('h1', { hasText: '3D Model Generator' });
  await expect(heading).toBeVisible();

  if (errors.length > 0) {
    throw new Error(`Frontend errors detected:\n${errors.join('\n')}`);
  }
});
