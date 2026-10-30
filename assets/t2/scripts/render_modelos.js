const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const out = {};
  for (const [pg, jobs] of Object.entries(JSON.parse(process.argv[2]))) {
    const page = await b.newPage({ viewport: { width: 1100, height: 900 } });
    const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await page.goto('file://' + path.resolve('sitio/' + pg + '.html'));
    await page.waitForTimeout(300);
    for (const [nombre, p, cola] of jobs) {
      const b64 = await page.evaluate(([p, c]) => window.renderBase64(p, c), [p, cola ?? 0.3]);
      fs.writeFileSync('render/' + nombre + '.wav', Buffer.from(b64, 'base64'));
    }
    await page.screenshot({ path: 'render/pagina_' + pg + '.png', fullPage: true });
    console.log(pg, 'errores:', errs);
  }
  await b.close();
})();
