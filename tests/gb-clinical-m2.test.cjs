const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const s=fs.readFileSync('gamebras-base.html','utf8');const start=s.indexOf('    // GBClinical M2'),end=s.indexOf('    const GBSimulation',start);const C=vm.runInNewContext(s.slice(start,end)+'\nGBClinical');
test('decisions alter trajectory',()=>{const a=new C.Patient('hypo'),b=new C.Patient('hypo');a.act('carbs');a.advance(15);b.advance(15);assert(a.g>b.g);});
test('urgent referral and unsafe discharge differ',()=>{const a=new C.Patient('dka'),b=new C.Patient('dka');a.act('refer');b.act('plan');assert(a.score>b.score);assert(a.finished&&b.finished);});
test('measurement is timestamped',()=>{const a=new C.Patient('dm2');a.act('measure');a.advance(10);assert.equal(a.observed.g.at,0);assert.equal(a.elapsed,10);});
