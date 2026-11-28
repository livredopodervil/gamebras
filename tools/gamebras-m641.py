#!/usr/bin/env python3
import argparse,base64,hashlib,io,json,re,subprocess,zipfile,tempfile
from pathlib import Path
TAG=re.compile(rb'<script id="gb-lineage" type="application/json">(.*?)</script>\n',re.S)
BUNDLE=re.compile(rb'(<script id="rf-bundle" type="application/octet-stream">)(.*?)(</script>)',re.S)
REPO='https://github.com/livredopodervil/gamebras'
def digest(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def canonical(m):return json.dumps(m,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def identity(m):return digest(canonical({k:v for k,v in m.items() if k!='version_id'}))
def unpack(b):
 m=TAG.search(b);return (TAG.sub(b'',b),json.loads(m[1])) if m else (b,None)
def bundle(raw):
 m=BUNDLE.search(raw)
 if not m:raise ValueError('bundle ausente')
 with zipfile.ZipFile(io.BytesIO(base64.b64decode(m[2]))) as z:return {n:z.read(n) for n in z.namelist() if not n.endswith('/')}
def verify(b):
 raw,m=unpack(b)
 if not m or m['content_hash']!=digest(raw) or m['version_id']!=identity(m):return False
 fs=m.get('files',{});assets=bundle(raw) if any('bundle' in v for v in fs.values()) else {}
 return all(digest(assets[v['bundle']] if 'bundle' in v else base64.b64decode(v['data'],validate=True))==v['hash'] for v in fs.values())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--verify',type=Path);a=ap.parse_args()
 if a.verify:
  ok=verify(a.verify.read_bytes());print('OK' if ok else 'FALHA');raise SystemExit(not ok)
 assert 'gamebras' in git('remote','get-url','origin').lower()
 head=git('rev-parse','HEAD');paths=[Path('index.html'),Path('gamebras-base.html')];out={};archives={}
 doc=Path('AGENTS.md');rule='\n## M6.4.1 — distribuição enxuta\nPais imediatos e URLs de commits; tag de distribuição permanente. Não incorporar arquivos binários novamente no contexto quando disponíveis no bundle. Preservar fonte de terceiros no repositório e avisos de licença. Verificar ambos os HTMLs antes de publicar.\n';text=doc.read_text();text=text if rule in text else text+rule
 for p in paths:
  b=p.read_bytes();assert verify(b),p;raw,old=unpack(b)
  if old.get('milestone')=='M6.4.1':continue
  assert old.get('milestone','').startswith('M6.4'),old.get('milestone')
  assert subprocess.check_output(['git','show',f'HEAD:{p}'])==b,'HTML deve estar no commit pai'
  assets=bundle(raw);name='_runtime/lamejs-1.2.1-source.tgz'
  if name in assets:archives[Path('third_party/lamejs-1.2.1-source.tgz')]=assets.pop(name)
  zbuf=io.BytesIO()
  with zipfile.ZipFile(zbuf,'w',zipfile.ZIP_DEFLATED) as z:
   for n,v in assets.items():z.writestr(n,v)
  raw=BUNDLE.sub(lambda x:x[1]+base64.b64encode(zbuf.getvalue())+x[3],raw,count=1)
  # Keep license/source discovery visible offline; archive is published separately.
  notice=f'<meta name="gamebras-source" content="{REPO}/blob/experiment/pbl-m5/third_party/lamejs-1.2.1-source.tgz">\n'.encode()
  raw=raw.replace(b'</head>',notice+b'</head>',1)
  anchor=b'Uint8Array.from(atob(f.data),c=>c.charCodeAt(0))'
  assert raw.count(anchor)==1
  raw=raw.replace(b'x.onclick=()=>download(name.split(\'/\').pop(),'+anchor+b');',b'x.onclick=async()=>{try{const bytes=f.bundle?await (await JSZip.loadAsync(document.getElementById("rf-bundle").textContent.trim(),{base64:true})).file(f.bundle).async("uint8array"):'+anchor+b';download(name.split("/").pop(),bytes)}catch(e){alert(String(e))}};')
  assert b'x.onclick=async()=>{try{const bytes=f.bundle?' in raw
  lookup={digest(v):n for n,v in assets.items()};files={}
  for n,v in old['files'].items():
   files[n]={'hash':v['hash'],'bundle':lookup[v['hash']]} if v['hash'] in lookup else v
  for n,v in {'AGENTS.md':text.encode(),'tools/gamebras-m641.py':Path(__file__).read_bytes()}.items():files[n]={'hash':digest(v),'data':base64.b64encode(v).decode()}
  m={k:v for k,v in old.items() if k not in ('version_id','content_hash','parents','files','milestone','schema')};m.update(schema='gamebras.lineage/2',milestone='M6.4.1',content_hash=digest(raw),parents=[old['version_id']],parent_urls=[f'{REPO}/blob/{head}/{p}'],repository=REPO,git_base=head,files=files)
  m['version_id']=identity(m);new=raw.replace(b'</head>',b'<script id="gb-lineage" type="application/json">'+canonical(m)+b'</script>\n</head>',1);assert verify(new);assert len(new)<len(b);out[p]=new;print(p,len(b),'->',len(new),m['version_id'])
 if not out:return
 assert len(out)==2,'instalação parcial'
 for p,b in archives.items():assert not p.exists() or p.read_bytes()==b
 if not a.apply:return
 backup=Path(tempfile.mkdtemp(prefix='gamebras-m641-',dir=Path.home()));targets={**out,**archives,doc:text.encode(),Path('tools/gamebras-m641.py'):Path(__file__).read_bytes()};original={p:p.read_bytes() if p.exists() else None for p in targets}
 for p,b in original.items():
  if b is not None:q=backup/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 try:
  for p,b in targets.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  subprocess.run(['node','--test',*[str(p) for p in Path('tests').glob('*.test.cjs')]],check=True)
 except BaseException:
  for p,b in original.items():
   if b is None:p.unlink(missing_ok=True)
   else:p.write_bytes(b)
  raise
 print('Backup:',backup)
if __name__=='__main__':main()
