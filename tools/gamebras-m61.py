#!/usr/bin/env python3
"""Portable lineage and development snapshot. No network or Git mutations."""
import argparse, base64, hashlib, json, re, subprocess, pathlib, tempfile, os
P=pathlib.Path
TAG=re.compile(rb'<script id="gb-lineage" type="application/json">(.*?)</script>\n',re.S)
def digest(b): return 'sha256:'+hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def identity(m): return digest(canonical({k:v for k,v in m.items() if k!='version_id'}))
def unpack(b):
 m=TAG.search(b)
 return (TAG.sub(b'',b),json.loads(m[1])) if m else (b,None)
def verify(b):
 raw,m=unpack(b)
 return bool(m and m['content_hash']==digest(raw) and m['version_id']==identity(m) and all(digest(base64.b64decode(v['data']))==v['hash'] for v in m['files'].values()))
def seal(raw,files,parents,meta):
 m=dict(schema='gamebras.lineage/1',project_id='gamebras',content_hash=digest(raw),parents=sorted(set(parents)),files=files,**meta)
 m['version_id']=identity(m)
 tag=b'<script id="gb-lineage" type="application/json">'+canonical(m)+b'</script>\n'
 # Insert immediately before closing head; stripping restores exact bytes.
 assert raw.count(b'</head>')==1
 return raw.replace(b'</head>',tag+b'</head>',1)
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
def selftest():
 r=b'<html><head></head></html>'; a=seal(r,{},[],{}); assert verify(a); p=unpack(a)[1]['version_id']; b=seal(r,{},[p],{'branch':'a'}); c=seal(r,{},[p],{'branch':'b'}); assert verify(b) and verify(c) and b!=c; d=seal(r,{},[unpack(b)[1]['version_id'],unpack(c)[1]['version_id']],{}); assert verify(d); assert not verify(d.replace(b'<html>',b'<HTML>')); print('PASS: integridade, forks, convergência')
RULE='''\n## Identidade e continuidade portátil (M6)\nCada distribuição deve incorporar manifesto gamebras.lineage/1, SHA-256 do HTML sem o manifesto, hashes dos arquivos de desenvolvimento e identificador SHA-256 do manifesto canônico sem version_id. Pais são IDs completos; merges registram todos os pais. Branch e Git HEAD são metadados, não identidade. O HEAD registrado é a base de trabalho, não o commit futuro do próprio HTML. Preserve snapshots ancestrais para reconstruir o DAG. Não inclua segredos. Execute o verificador antes de distribuir. M6.1: selagem e verificação; M6.2: interface de exportação; M6.3–M6.7: executor, migração diabetes, editor, segundo módulo e continuidade independente. Não declare essas etapas concluídas antes dos testes.\n'''
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); ap.add_argument('--verify',type=P); ap.add_argument('--parent',action='append',default=[]); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args(); selftest()
 if a.self_test:return
 if a.verify: print('OK' if verify(a.verify.read_bytes()) else 'FALHA'); raise SystemExit(0 if verify(a.verify.read_bytes()) else 1)
 root=P(git('rev-parse','--show-toplevel')); os.chdir(root); assert 'gamebras' in git('remote','get-url','origin').lower(); doc=P('AGENTS.md'); text=doc.read_text(); assert 'Gamebras' in text and 'Colaboração assistida no SpatialSeed' not in text
 if '## Identidade e continuidade portátil (M6)' not in text:text+=RULE
 paths=[P('gamebras-base.html'),P('index.html')]; inputs={p:p.read_bytes() for p in paths}; files={}
 sources={'AGENTS.md':text.encode(), 'tools/gamebras-m61.py':P(__file__).read_bytes()}
 for p in [P('README.md'),*P('tests').glob('*.test.cjs')]:
  if p.is_file():sources[str(p)]=p.read_bytes()
 for k,v in sources.items():files[k]={'hash':digest(v),'data':base64.b64encode(v).decode()}
 outputs={}
 for p,b in inputs.items():
  raw,old=unpack(b); parents=list(a.parent)
  if old:
   if not verify(b): raise SystemExit(f'Manifesto inválido: {p}')
   if old['files']==files and not parents: outputs[p]=b;continue
   parents.append(old['version_id'])
  outputs[p]=seal(raw,files,parents,{'git_base':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'milestone':'M6.1','status':'experimental','artifact':str(p)})
  assert verify(outputs[p]); print(p,unpack(outputs[p])[1]['version_id'])
 if not a.apply:return
 backup=P(tempfile.mkdtemp(prefix='gamebras-m61-',dir=str(P.home())))
 for p,b in inputs.items():(backup/p.name).write_bytes(b)
 (backup/'AGENTS.md').write_bytes(doc.read_bytes()); print('Backup:',backup)
 for p,b in outputs.items():p.write_bytes(b)
 doc.write_text(text); P('tools').mkdir(exist_ok=True); P('tools/gamebras-m61.py').write_bytes(sources['tools/gamebras-m61.py'])
if __name__=='__main__':main()
