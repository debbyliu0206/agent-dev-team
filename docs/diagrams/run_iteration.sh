#!/bin/bash
# Run one full iteration: build diagram → verify → screenshot
# Usage: bash docs/diagrams/run_iteration.sh
# Requires: Excalidraw canvas server at http://127.0.0.1:3000

set -e
cd "$(dirname "$0")/../.."

echo "=== STEP 1: Build diagram ==="
python docs/diagrams/build_diagram.py

echo ""
echo "=== STEP 2: Verify elements ==="
python docs/diagrams/verify_diagram.py

echo ""
echo "=== STEP 3: Screenshot via Playwright ==="
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 2400, height: 1800 },
    deviceScaleFactor: 1
  });
  await page.goto('http://127.0.0.1:3000');
  await page.waitForTimeout(2500);

  // Deselect everything
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  // Try multiple zoom approaches
  // 1. Click empty area to focus canvas
  await page.mouse.click(1200, 900);
  await page.waitForTimeout(200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);

  // 2. Zoom to fit via keyboard (Ctrl+Shift+1)
  await page.keyboard.press('Control+Shift+Digit1');
  await page.waitForTimeout(1000);

  // 3. Fallback: manually zoom out
  for (let i = 0; i < 3; i++) {
    await page.keyboard.press('Control+Minus');
    await page.waitForTimeout(200);
  }
  await page.waitForTimeout(1000);

  await page.screenshot({ path: 'diagram-check.png', type: 'png' });
  console.log('Screenshot saved: diagram-check.png');
  await browser.close();
})();
" 2>&1

echo ""
echo "=== DONE ==="
echo "Review diagram-check.png to verify layout."
