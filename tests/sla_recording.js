const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('http://10.153.1.189/');
  await page.getByRole('link', { name: 'Sign In' }).click();
  await page.getByRole('link', { name: 'sign in here' }).click();
  await page.getByRole('textbox', { name: 'Email' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('admin@yourdomain.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('Adm1nP@ss!');
  await page.getByRole('textbox', { name: 'Password' }).click();
  await page.getByRole('textbox', { name: 'Password' }).fill('Adm1nP@ss!');
  await page.getByRole('button', { name: ' Log In' }).click();
  await page.getByRole('link', { name: 'Admin Panel' }).click();
  await page.getByRole('link', { name: 'Manage' }).click();
  await page.getByRole('link', { name: 'Filters' }).click();
  await page.getByRole('link', { name: ' Add New Filter' }).click();
  await page.getByRole('heading', { name: 'Add New Filter' }).click();
  await page.locator('input[name="name"]').click();
  await page.locator('input[name="name"]').fill('LMT & MST New System - Minor');
  await page.locator('input[name="execorder"]').click();
  await page.locator('input[name="execorder"]').fill('99');
  await page.getByRole('radio').first().check();
  await page.locator('select[name="target"]').selectOption('Any');
  await page.getByText('Match All').click();
  await page.locator('select[name="rules[0][w]"]').selectOption('field.48');
  await page.locator('select[name="rules[1][w]"]').selectOption('field.47');
  await page.locator('select[name="rules[0][h]"]').selectOption('equal');
  await page.locator('select[name="rules[1][h]"]').selectOption('equal');
  await page.locator('input[name="rules[0][v]"]').click();
  await page.locator('input[name="rules[0][v]"]').fill('New System');
  await page.locator('input[name="rules[1][v]"]').click();
  await page.locator('input[name="rules[1][v]"]').fill('Minor');
  await page.getByRole('link', { name: ' Filter Actions' }).click();
  await page.locator('#new-action-select').selectOption('sla');
  await page.locator('select[name="fd9d3533d0745b[]"]').selectOption('5');
  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.close();

  // ---------------------
  await context.close();
  await browser.close();
})();