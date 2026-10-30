const { chromium } = require('playwright'); const path=require('path');
(async () => {
  const b = await chromium.launch(); const page = await b.newPage({viewport:{width:1300,height:900}, deviceScaleFactor:2});
  await page.goto('file://' + path.resolve('sitio/aditiva.html'));
  await page.locator('.diagrama svg').first().screenshot({path:'figuras/07_diagrama_aditiva.png'});
  await page.screenshot({path:'render/pagina_aditiva.png', fullPage:true});
  await page.goto('file://' + path.resolve('sitio/fm.html'));
  const s = page.locator('.diagrama svg');
  await s.nth(0).screenshot({path:'figuras/08_diagrama_fm.png'});
  await s.nth(1).screenshot({path:'figuras/09_diagrama_cadena_de_escucha.png'});
  await b.close();
})();
