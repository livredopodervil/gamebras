'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('gamebras-base.html', 'utf8');
const clinical = html.slice(html.indexOf('const GBModuleRuntime='), html.indexOf('    const GBM4='));
const simulation = html.slice(html.indexOf('    const GBSimulation ='), html.indexOf('    // === End GB Simulation M1A ==='));
const mockDocument = { getElementById: () => null };
const { GBClinical, GBWard, GBSimulation } = vm.runInNewContext(
  clinical + simulation + '\n({GBClinical, GBWard, GBSimulation})',
  { structuredClone, document: mockDocument },
);
const campaign = JSON.parse(fs.readFileSync('modules/diabetes/aventura_diabetes.json'));
const moduleData = campaign.clinicalModule;
const patient = id => new GBClinical.Patient(id, moduleData);
const play = (p, ...ids) => {
  for (const id of ids) p.advance(p.act(id));
  return p;
};

const routes = {
  dm2: ['history', 'exam', 'measure', 'a1c', 'renal', 'social', 'dx_dm2', 'renalPlan', 'shared', 'close_dm2'],
  hypo: ['history', 'exam', 'measure', 'dx_hypo', 'carbs', 'wait', 'measure', 'meal', 'plan'],
  dka: ['exam', 'history', 'support', 'measure', 'ketones', 'gas', 'electro', 'dx_dka', 'refer'],
  edka: ['exam', 'history', 'measure', 'ketones', 'gas', 'dx_edka', 'hold_sglt2', 'support', 'refer'],
  hhs: ['exam', 'history', 'support', 'electro', 'osm', 'ketones', 'gas', 'trigger', 'dx_hhs', 'refer'],
  recurrent: ['measure', 'parenteral', 'meal_note', 'refer'],
  gest: ['history', 'exam', 'preg_test', 'dx_gest', 'nutrition', 'preg_monitor', 'insulinPlan', 'close_gest'],
  foot: ['history', 'exam', 'dx_foot', 'protect_foot', 'refer'],
};

for (const [id, route] of Object.entries(routes)) {
  test('rota segura ' + id, () => {
    const p = play(patient(id), ...route);
    assert.equal(p.outcome, 'appropriate', JSON.stringify(p.log));
    assert.equal(p.errors.length, 0);
    assert.ok(p.score >= 7);
    assert.ok(p.log.every(record => record.trace.length >= 3));
    const dx = route.find(x => x.startsWith('dx_'));
    if (dx) assert.equal(p.log.find(r => r.action === dx).points, 3);
  });
}

test('CAD: glicose isolada, potássio baixo e insulina não monitorada', () => {
  const p = play(patient('dka'), 'measure', 'dx_dka');
  assert.equal(p.log.at(-1).points, 0);
  play(p, 'electro');
  assert.ok(p.observed.electro.potassium < 3.5);
  const before = { g: p.state.g, k: p.state.potassium, acid: p.state.bicarbonate };
  play(p, 'insulin');
  assert.equal(p.errors.at(-1).action, 'insulin');
  assert.ok(p.state.potassium < before.k);
  assert.ok(p.state.g < before.g);
  assert.ok(p.state.bicarbonate < before.acid);
  assert.equal(p.finished, false);
});

test('Joana: atraso com glicemia abaixo de 200, progressão da cetose e acidose', () => {
  const p = play(patient('edka'), 'measure', 'ketones', 'gas');
  const readings = structuredClone(p.observed);
  const t = p.elapsed;
  play(p, 'wait', 'measure', 'ketones', 'gas');
  assert.ok(p.errors.some(r => r.action === 'wait'));
  assert.ok(p.observed.g.value < 200);
  assert.ok(p.observed.k.value > readings.k.value);
  assert.ok(p.observed.gas.bicarbonate < readings.gas.bicarbonate);
  assert.ok(p.observed.g.at > t);
  assert.equal(play(p, 'refer').outcome, 'appropriate');
});

test('Augusto: hiperosmolalidade calculada com dados da mesma coleta', () => {
  const p = play(patient('hhs'), 'osm');
  assert.equal(p.observed.osm, undefined);
  play(p, 'electro');
  const sample = p.observed.electro;
  const plasma = p.state.g;
  p.advance(90);
  play(p, 'osm');
  assert.ok(p.state.g > plasma);
  assert.equal(p.observed.osm.value, Math.round(2 * sample.sodium + sample.plasma / 18));
  assert.ok(p.observed.osm.value > 300);
});

test('Paulo: sem empilhar carboidrato e sem alta com valor precoce', () => {
  const pending = play(patient('hypo'), 'measure', 'carbs');
  play(pending, 'carbs');
  assert.match(pending.feedback, /intervalo/);
  play(pending, 'measure', 'plan');
  assert.equal(pending.outcome, 'unsafe');
  const recovered = play(patient('hypo'), 'measure', 'carbs', 'wait', 'measure');
  const measures = recovered.log.filter(x => x.action === 'measure');
  assert.equal(measures[0].observed.g.value, 48);
  assert.ok(measures[1].observed.g.value >= 70);
  assert.ok(measures[1].minute > measures[0].minute);
  assert.equal(play(recovered, 'plan').outcome, 'appropriate');
});

test('Celina: via oral insegura; resgate melhora, mas hipoglicemia recorre', () => {
  const p = play(patient('recurrent'), 'carbs');
  assert.equal(p.errors.length, 1);
  assert.equal(p.state.absorption, 0);
  play(p, 'parenteral');
  assert.ok(p.state.g > 70);
  p.advance(100);
  assert.ok(p.state.g < 70);
  assert.equal(play(p, 'discharge_recurrent').outcome, 'unsafe');
  const q = play(patient('recurrent'), 'parenteral', 'discharge_recurrent');
  assert.equal(q.outcome, 'unsafe');
});

test('seguimentos incompletos e divergências de evidência', () => {
  assert.equal(play(patient('dm2'), 'exam', 'renal', 'dx_dm2', 'renalPlan', 'close_dm2').outcome, 'unsafe');
  assert.equal(play(patient('gest'), 'preg_monitor').observed.preg_monitor, undefined);
  assert.equal(play(patient('gest'), 'exam', 'preg_test', 'dx_gest', 'close_gest').outcome, 'unsafe');
  assert.equal(play(patient('foot'), 'close_foot').outcome, 'unsafe');
  assert.ok(play(patient('foot'), 'wait').state.infection > 2);
});

test('relógio da enfermaria evolui pacientes em paralelo, recursos e pontuação de idempotência', () => {
  const sim = new GBSimulation.Session();
  const ward = GBWard.start(sim, moduleData);
  const inventory = new Set();
  const game = { gbSimulation: sim, items: { inventory }, storyFlags: {} };
  assert.match(GBWard.act(game, ward.Paulo, 'measure'), /mochila/);
  assert.equal(sim.minute, 0);
  inventory.add('glicosimetro');
  GBWard.act(game, ward.Paulo, 'measure');
  GBWard.act(game, ward.Paulo, 'history');
  GBWard.act(game, ward.Paulo, 'history');
  assert.equal(ward.Paulo.score, 1);
  assert.equal(ward.Joana.elapsed, sim.minute);
  assert.ok(ward.Joana.state.k > 4.1);
  assert.ok(ward.Augusto.state.g > 677);
  assert.equal(ward.Celina.observed.g, undefined);
  assert.equal(sim.snapshot().ward.Paulo.log[0].observed.g.value, 48);
});

test('contrato, extensão opcional, referências e mapeamento dos oito NPCs', () => {
  assert.equal(GBClinical.validate(moduleData), moduleData);
  assert.equal(moduleData.lesson.chapters.length, 4);
  const npcNames = new Set(campaign.npcs.map(n => n.name));
  for (const c of moduleData.cases) {
    assert.ok(npcNames.has(c.person));
    assert.ok(moduleData.docs['docs/clinica/' + c.topic + '.md']);
    assert.match(moduleData.references[c.topic], /^https:\/\//);
    assert.ok(c.checkpoints.every(id => c.actions.includes(id)));
  }
  assert.throws(() => patient('dm2').act('parenteral'), /Ação inválida/);
  const invalid = structuredClone(moduleData);
  invalid.cases[0].actions.push('missing');
  assert.throws(() => GBClinical.validate(invalid), /Ações de caso/);
});
