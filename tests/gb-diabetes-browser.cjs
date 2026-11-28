'use strict';
// Manual integration gate. Run with Playwright and a Chromium binary supporting WebGL.
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.GAMEBRAS_PLAYWRIGHT || 'playwright');

const html = process.argv[2] || 'index.html';
const moduleZip = process.argv[3];
const screenshots = process.env.GAMEBRAS_SCREENSHOTS;
const screen = [
  ['retrato', { width: 390, height: 844 }, true],
  ['paisagem', { width: 844, height: 390 }, true],
  ['desktop', { width: 1280, height: 800 }, false],
];

async function smoke(browser, [label, viewport, mobile]) {
  const context = await browser.newContext({ viewport, offline: true, isMobile: mobile, hasTouch: mobile, deviceScaleFactor: 1, acceptDownloads: true });
  const page = await context.newPage();
  const errors = [], remote = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (/^https?:/i.test(r.url())) remote.push(r.url()); });
  await page.goto(pathToFileURL(path.resolve(html)).href);
  const entry = page.locator('#gb-encounter-open');
  const dialog = page.locator('#gb-encounter');
  const button = (name) => dialog.getByRole('button', { name, exact: true });
  await entry.waitFor({ state: 'visible', timeout: 20000 });
  await page.getByRole('button', { name: 'Plantão', exact: true }).click();
  const cards = dialog.locator('.gb-enc-roster button');
  assert.equal(await cards.count(), 8);
  await dialog.locator('.gb-enc-cover').evaluate(img => img.decode());
  const dim = await dialog.evaluate(el => ({ sw: el.scrollWidth, cw: el.clientWidth, h: el.getBoundingClientRect().height }));
  assert.ok(dim.sw <= dim.cw + 1 && dim.h <= viewport.height, JSON.stringify(dim));
  if (screenshots && label !== 'paisagem') await page.screenshot({ path: path.join(screenshots, label + '-plantao.png') });

  await button('Anatomofisiopatologia do diabetes').click();
  await button('Diabetes tipo 1').click();
  const diagram = dialog.locator('.gb-enc-diagram');
  await diagram.evaluate(img => img.decode());
  await button('Compensação da acidose metabólica').click();
  assert.match(await dialog.locator('[role=status]').innerText(), /ventilação/);
  await button('Gestação').click();
  assert.match(await dialog.locator('article h3').innerText(), /demanda/);
  await button('Casos').click();
  await button('Receber kit de simulação').click();

  await cards.filter({ hasText: 'Paulo' }).click();
  await button('Caderno PBL').click();
  await dialog.getByRole('combobox', { name: 'Etapa PBL' }).selectOption('2');
  await dialog.locator('textarea').fill('Investigar diferença entre sintomas e glicemia.');
  await button('Pedir pista 1').click();
  await button('Pedir pista 2').click();
  assert.match(await dialog.locator('.gb-enc-content').innerText(), /via aérea/);
  await button('Atendimento').click();
  await button('Medir glicemia capilar').click();
  await button('Oferecer glicose por via oral').click();
  await button('Aguardar 15 min e reavaliar').click();
  await button('Medir glicemia capilar').click();
  await button('Prontuário').click();
  assert.match(await dialog.locator('.gb-enc-evidence').innerText(), /mg\/dL/);
  assert.equal(await dialog.locator('.gb-enc-chart svg circle').count(), 2);
  if (screenshots && label !== 'paisagem') await page.screenshot({ path: path.join(screenshots, label + '-prontuario.png') });
  await button('Caderno PBL').click();
  assert.equal(await dialog.locator('textarea').inputValue(), 'Investigar diferença entre sintomas e glicemia.');
  await button('Atendimento').click();
  await button('Encerrar com plano ambulatorial').click();
  assert.match(await dialog.locator('.gb-enc-content').innerText(), /Encerramento adequado/);
  await dialog.getByText('Síntese clínica', { exact: true }).waitFor();
  await dialog.getByRole('heading', { name: 'Hipoglicemia em pessoas com diabetes', exact: true }).waitFor();

  await button('Casos').click();
  await cards.filter({ hasText: 'Marina' }).click();
  assert.match(await dialog.locator('.gb-enc-meta').last().innerText(), /^\d{2} min/);
  await button('Solicitar eletrólitos e glicose plasmática').click();
  await button('Aplicar insulina de correção sem protocolo').click();
  assert.match(await dialog.locator('[role=status]').innerText(), /potássio abaixo/);
  await button('Providenciar transferência urgente').click();
  assert.match(await dialog.locator('.gb-enc-content').innerText(), /Erros 1/);
  await button('Fechar').click();

  if (label === 'desktop') {
    // Approach a character via the normal Action controller.
    const map = await page.evaluate(() => {
      const e = window.retroForge;
      const patient = e.npcs.find(n => n.name === 'Dona Rosa');
      const open = e.npcs.filter(n => n.def.asset?.startsWith('npc_')).every(n => {
        const { x, y, z } = n.container.position;
        return Number.isFinite(y) && [-1, 1].some(direction => e.isWalkable(x + direction * 1.1, z, .62, .56, y));
      });
      const at = patient.container.position;
      e.hero.container.position.set(at.x + 1.1, at.y, at.z);
      e.interactWithNearestNPC();
      return { open, rendered: e.renderer.info.render.calls > 0 };
    });
    assert.deepEqual(map, { open: true, rendered: true });
    await dialog.getByRole('heading', { name: 'Dona Rosa', exact: true }).waitFor();
    await button('Caderno PBL').click();
    await button('Ver fluxograma').click();
    const graph = page.locator('#gb-pbl');
    await graph.locator('#gbm53-graph svg').waitFor();
    await graph.getByRole('button', { name: 'Fechar', exact: true }).click();
    await button('Fechar').click();
    if (screenshots) await page.screenshot({ path: path.join(screenshots, 'desktop-cenario.png') });
  }

  if (label === 'desktop' && moduleZip) {
    // Running a preserved non-clinical phase must hide the optional encounter entry.
    await page.locator('#rf-mode').click();
    const phases = page.locator('#gb-resource-phase');
    await phases.selectOption('nordeste');
    await page.evaluate(() => {
      const button = [...document.querySelectorAll('#rf-work button')].find(b => b.textContent.includes('Testar fase selecionada'));
      if (!button) throw Error('Controle de fase ausente');
      button.click();
    });
    await entry.waitFor({ state: 'hidden' });
    await page.locator('#rf-zip-open').setInputFiles(moduleZip);
    await entry.waitFor({ state: 'visible', timeout: 12000 });
    await entry.click({ force: true });
    await dialog.waitFor({ state: 'visible' });
    assert.equal(await cards.count(), 8);
    assert.match(await dialog.locator('.gb-enc-meta').innerText(), /0 min/);
  }
  assert.deepEqual(remote, [], 'requisições externas');
  assert.deepEqual(errors, [], 'erros JavaScript');
  await context.close();
  console.log('PASS Chromium offline · ' + label + ' · ' + viewport.width + '×' + viewport.height);
}

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.GAMEBRAS_CHROMIUM || undefined,
    headless: true,
    args: ['--no-sandbox', '--no-zygote', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  try { for (const config of screen) await smoke(browser, config); }
  finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
