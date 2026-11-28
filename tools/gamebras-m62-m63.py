#!/usr/bin/env python3
"""M6.2 portable context and M6.3 generic flow runtime foundation."""
import pathlib as P, argparse, importlib.util, json, subprocess, tempfile, base64, hashlib, re
JS=r'''
const GBModuleRuntime=(()=>{
 const own=(o,k)=>Object.hasOwn(o,k), safe=k=>typeof k==='string'&&/^[A-Za-z][\w.-]{0,99}$/.test(k)&&!['constructor','prototype','__proto__'].includes(k);
 const ops={lt:(a,b)=>a<b,lte:(a,b)=>a<=b,gt:(a,b)=>a>b,gte:(a,b)=>a>=b,eq:(a,b)=>a===b,ne:(a,b)=>a!==b};
 function run(flow,state,actions,limit=500){
  if(!Array.isArray(flow.nodes)||flow.nodes.length>500||!Number.isInteger(limit)||limit<1||limit>500)throw Error('Fluxo inválido');
  const nodes=new Map(), next=structuredClone(state), trace=[];
  for(const n of flow.nodes){if(!safe(n.id)||nodes.has(n.id))throw Error('ID inválido');nodes.set(n.id,n);}
  for(const n of nodes.values()){
   if(n.type==='action'){if(!safe(n.action)||!own(actions,n.action)||!nodes.has(n.next))throw Error('Ação inválida');}
   else if(n.type==='condition'){if(!safe(n.field)||!own(next,n.field)||!own(ops,n.op)||!nodes.has(n.yes)||!nodes.has(n.no))throw Error('Condição inválida');}
   else if(n.type!=='end')throw Error('Tipo inválido');
  }
  let id=flow.start;
  for(let i=0;i<limit;i++){const n=nodes.get(id);if(!n)throw Error('Nó inexistente');trace.push(id);
   if(n.type==='end')return {state:next,trace};
   if(n.type==='condition'){id=ops[n.op](next[n.field],n.value)?n.yes:n.no;continue;}
   for(const effect of actions[n.action]){const k=effect.field;if(!safe(k)||!own(next,k))throw Error('Campo inválido');if(effect.op==='set')next[k]=effect.value;else if(effect.op==='add'&&Number.isFinite(next[k])&&Number.isFinite(effect.value)){next[k]+=effect.value;if(!Number.isFinite(next[k]))throw Error('Overflow');}else throw Error('Efeito inválido');}id=n.next;
  }throw Error('Limite de transições');
 }return {run};
})();
'''
UI=r'''
<script id="gb-portable-context">
(()=>{function init(){const tools=document.getElementById('rf-tools');if(!tools)return;const b=document.createElement('button');b.textContent='Contexto';tools.append(b);b.onclick=()=>{const m=JSON.parse(document.getElementById('gb-lineage').textContent),d=document.createElement('dialog');d.style.cssText='margin:auto;width:min(94vw,800px);max-height:85vh;overflow:auto;background:#172033;color:white;padding:16px';const h=document.createElement('h3');h.textContent='Contexto de desenvolvimento';d.append(h);const p=document.createElement('pre');p.style.whiteSpace='pre-wrap';p.textContent=JSON.stringify({...m,files:Object.keys(m.files)},null,2);d.append(p);function download(name,data){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data]));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}for(const [name,f] of Object.entries(m.files)){const x=document.createElement('button');x.textContent=name;x.style.display='block';x.onclick=()=>download(name.split('/').pop(),Uint8Array.from(atob(f.data),c=>c.charCodeAt(0)));d.append(x);}const x=document.createElement('button');x.textContent='Exportar manifesto completo';x.onclick=()=>download('gamebras-context.json',JSON.stringify(m,null,2));d.append(x);const c=document.createElement('button');c.textContent='Fechar';c.onclick=()=>{d.close();d.remove()};d.append(c);document.body.append(d);d.showModal();};}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();})();
</script>
'''
TEST=r'''
const assert=require('node:assert/strict');
const f={start:'a',nodes:[{id:'a',type:'condition',field:'level',op:'lt',value:5,yes:'b',no:'z'},{id:'b',type:'action',action:'raise',next:'z'},{id:'z',type:'end'}]};
const s={level:2};assert.equal(GBModuleRuntime.run(f,s,{raise:[{field:'level',op:'add',value:4}]}).state.level,6);assert.equal(s.level,2);assert.equal(GBModuleRuntime.run(f,{level:8},{raise:[]}).state.level,8);assert.throws(()=>GBModuleRuntime.run(f,s,{}));console.log('PASS: executor genérico, ramificação, isolamento, validação');
'''
def main():
 a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');a=a.parse_args();root=P.Path.cwd(); tool=root/'tools/gamebras-m61.py';spec=importlib.util.spec_from_file_location('lineage',tool);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 subprocess.run(['node','-e',JS+TEST],check=True)
 paths=[root/'gamebras-base.html',root/'index.html'];out={};doc=root/'AGENTS.md';text=doc.read_text();rule='\n## M6.2–M6.3 (incremento experimental)\nContexto portátil: manifesto e arquivos exportáveis pela interface. Executor declarativo genérico isolado: condições, efeitos e limite de transições. Ainda não conectado aos fluxos clínicos; M6.4 pendente. Downloads Android: localizar pelo SHA-256, não pelo nome.\n';text=text if rule in text else text+rule
 for p in paths:
  b=p.read_bytes();assert m.verify(b),f'M6.1 inválida: {p}';raw,old=m.unpack(b)
  if b'const GBModuleRuntime=' in raw:out[p]=b;continue
  assert raw.count(b'    const GBClinical=')==1 and raw.count(b'</body>')==1
  raw=raw.replace(b'    const GBClinical=',JS.encode()+b'\n    const GBClinical=',1).replace(b'</body>',UI.encode()+b'</body>',1)
  files=dict(old['files']);sources={'AGENTS.md':text.encode(),'tools/gamebras-m62-m63.py':P.Path(__file__).read_bytes(),'tests/gb-module-runtime.test.cjs':(JS+TEST).encode()}
  for k,v in sources.items():files[k]={'hash':m.digest(v),'data':base64.b64encode(v).decode()}
  meta={k:v for k,v in old.items() if k not in ['schema','project_id','content_hash','parents','files','version_id','milestone']};meta['milestone']='M6.3-foundation';out[p]=m.seal(raw,files,[old['version_id']],meta);assert m.verify(out[p])
 if a.apply:
  backup=P.Path(tempfile.mkdtemp(prefix='gamebras-m63-',dir=str(P.Path.home())))
  for p in [*paths,doc]:(backup/p.name).write_bytes(p.read_bytes())
  for p,b in out.items():p.write_bytes(b)
  doc.write_text(text);(root/'tools/gamebras-m62-m63.py').write_bytes(P.Path(__file__).read_bytes());(root/'tests').mkdir(exist_ok=True);(root/'tests/gb-module-runtime.test.cjs').write_text(JS+TEST);print('Backup:',backup)
if __name__=='__main__':main()
