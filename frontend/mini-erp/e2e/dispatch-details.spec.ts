import { test, expect } from '@playwright/test';

test('verify dispatch details and form expansion', async ({ page }) => {
  await page.goto('http://localhost:3000/inventory/dispatch');
  
  // 1. Verify Detail Dialog
  // Open the first row
  await page.locator('[data-testid="dispatch-table"] tbody tr').first().click();
  
  const detailDialog = page.locator('role=dialog');
  await expect(detailDialog).toBeVisible();
  
  // Check if it's wide (5xl) - check bounding box
  const box = await detailDialog.boundingBox();
  expect(box?.width).toBeGreaterThan(800);
  
  // Check for picking list title
  await expect(page.getByText('Picking List', { exact: false })).toBeVisible();
  
  // Close dialog
  await page.keyboard.press('Escape');
  
  // 2. Verify Form Expansion
  // Click "Tạo phiếu xuất"
  await page.getByText('Tạo phiếu xuất').click();
  
  const formDialog = page.locator('role=dialog');
  await expect(formDialog).toBeVisible();
  
  // Check if it's very wide (7xl)
  const formBox = await formDialog.boundingBox();
  expect(formBox?.width).toBeGreaterThan(1200);
  
  // Check for Table headers in form
  await expect(page.getByText('Sản phẩm xuất', { exact: true })).toBeVisible();
  await expect(page.getByText('Vị trí (Kệ)', { exact: true })).toBeVisible();
});
