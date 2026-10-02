// Rend les images de l’appli (icônes, écrans de lancement) à partir de pages HTML.
// Usage : node render_assets.js jobs.json   — chaque tâche : { out, width, height, scale, html, transparent }
const fs = require('fs');
const path = require('path');
const pw = (() => { for (const p of ['/opt/npm-tools/node_modules/playwright', 'playwright']) { try { return require(p); } catch (e) { /* suivant */ } } throw new Error('Playwright introuvable'); })();
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await pw.chromium.launch();
  const tmp = path.join(path.dirname(path.resolve(process.argv[2])), '_render.html');
  for (const j of jobs) {
    const ctx = await browser.newContext({ viewport: { width: j.width, height: j.height }, deviceScaleFactor: j.scale || 1 });
    const page = await ctx.newPage();
    fs.writeFileSync(tmp, j.html);
    await page.goto('file://' + tmp);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(60);
    fs.mkdirSync(path.dirname(j.out), { recursive: true });
    await page.screenshot({ path: j.out, omitBackground: !!j.transparent });
    await ctx.close();
  }
  fs.unlinkSync(tmp);
  await browser.close();
  console.log('rendu :', jobs.length, 'images');
})();
