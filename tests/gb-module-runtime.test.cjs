
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

const assert=require('node:assert/strict');
const f={start:'a',nodes:[{id:'a',type:'condition',field:'level',op:'lt',value:5,yes:'b',no:'z'},{id:'b',type:'action',action:'raise',next:'z'},{id:'z',type:'end'}]};
const s={level:2};assert.equal(GBModuleRuntime.run(f,s,{raise:[{field:'level',op:'add',value:4}]}).state.level,6);assert.equal(s.level,2);assert.equal(GBModuleRuntime.run(f,{level:8},{raise:[]}).state.level,8);assert.throws(()=>GBModuleRuntime.run(f,s,{}));console.log('PASS: executor genérico, ramificação, isolamento, validação');
