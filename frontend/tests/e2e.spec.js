// Deprecated Playwright E2E test removed. Puppeteer test is in e2e.puppeteer.js



test('ORBIT Command Center end-to-end', async ({ page }) => {
  // Navigate to the dev server
  await page.goto('http://localhost:5175');

  // Verify branding - title contains ORBIT
  await expect(page).toHaveTitle(/ORBIT/);

  // Verify top bar exists via placeholder textarea
  const textarea = page.locator('textarea[placeholder*="e.g., Analyze this sales data"]');
  await expect(textarea).toBeVisible();

  // Verify sidebar exists (by checking for Recent Activity header)
  await expect(page.locator('text=Recent Activity')).toBeVisible();

  // Fill task composer
  await textarea.fill('Analyze the role of multi-agent AI systems in modern software development.');

  // Click Run Task
  await page.locator('button:has-text("Run Task")').click();

  // Verify state transitions appear in activity list
  const activity = page.locator('.flex.flex-col.gap-2.font-body-sm');
  await expect(activity.locator('text=Task received')).toBeVisible();
  await expect(activity.locator('text=ORCHESTRATOR planning')).toBeVisible();

  // Wait for completion indicator
  await expect(page.locator('span', { hasText: 'Completed' })).toBeVisible({ timeout: 15000 });

  // Verify result appears
  const result = page.locator('pre', { hasText: 'Mocked result data' });
  await expect(result).toBeVisible();
});
