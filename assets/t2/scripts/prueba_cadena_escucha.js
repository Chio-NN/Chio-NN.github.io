const { chromium } = require('playwright'); const path=require('path');
(async () => {
  const variantes = [['normal',8,150],['rapido',1,20],['lento',60,800]];
  for (const [n,at,lib] of variantes) {
    const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/tmp/claude-0/prueba_silbido_con_pausas.wav%noloop','--autoplay-policy=no-user-gesture-required'] });
    const ctx = await b.newContext({ acceptDownloads: true, permissions:['microphone'] });
    const page = await ctx.newPage(); const errs=[]; page.on('pageerror', e => errs.push(e.message));
    await page.goto('file://' + path.resolve('sitio/fm.html'));
    await page.evaluate(([at,lib]) => { VIVO_PARAMS[1].valor=at; VIVO_PARAMS[2].valor=lib; }, [at,lib]);
    await page.click('#vivo-on'); await page.waitForTimeout(300);
    await page.click('#grabar'); await page.waitForTimeout(7800);
    const [dl] = await Promise.all([page.waitForEvent('download'), page.click('#grabar')]);
    await dl.saveAs('render/sim_vivo_'+n+'.wav'); console.log(n, errs); await b.close();
  }
})();
