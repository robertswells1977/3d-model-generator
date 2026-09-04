# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: app.spec.ts >> app loads without console errors and shows login screen
- Location: tests/app.spec.ts:3:1

# Error details

```
Error: Frontend errors detected:
ConsoleError: Failed to load resource: the server responded with a status of 403 ()
ConsoleError: [GSI_LOGGER]: The given origin is not allowed for the given client ID.
```

# Page snapshot

```yaml
- generic [ref=e4]:
  - heading "3D Model Generator" [level=1] [ref=e5]
  - paragraph [ref=e6]: Sign in with Google to manage your autonomous CAD agent.
  - generic [ref=e9]:
    - button "Sign in with Google. Opens in new tab" [ref=e11] [cursor=pointer]:
      - generic [ref=e13]: Sign in with Google
    - iframe
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('app loads without console errors and shows login screen', async ({ page }) => {
  4  |   const errors: string[] = [];
  5  |   
  6  |   page.on('pageerror', error => {
  7  |     console.log("PAGE ERROR:", error);
  8  |     errors.push(`PageError: ${error.message}`);
  9  |   });
  10 | 
  11 |   page.on('console', msg => {
  12 |     console.log(`CONSOLE [${msg.type()}]: ${msg.text()}`);
  13 |     if (msg.type() === 'error') {
  14 |       errors.push(`ConsoleError: ${msg.text()}`);
  15 |     }
  16 |   });
  17 | 
  18 |   await page.goto('/');
  19 |   await page.waitForLoadState('networkidle');
  20 | 
  21 |   console.log("DOM content:", await page.content());
  22 | 
  23 |   const heading = page.locator('h1', { hasText: '3D Model Generator' });
  24 |   await expect(heading).toBeVisible();
  25 | 
  26 |   if (errors.length > 0) {
> 27 |     throw new Error(`Frontend errors detected:\n${errors.join('\n')}`);
     |           ^ Error: Frontend errors detected:
  28 |   }
  29 | });
  30 | 
```