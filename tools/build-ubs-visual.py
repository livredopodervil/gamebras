import runpy, json, base64, subprocess, io, zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]; L=runpy.run_path(str(R/'tools/gamebras-m641.py')); BASE='82299540e8617ef0380c4a339fe08c9a5965bb3c'; BRANCH='feat/diabetes-visual-ubs'; M=R/'modules/diabetes'
def build(parent):
 campaign=json.loads((M/'aventura_diabetes.json').read_bytes()); files={p.relative_to(M).as_posix():p.read_bytes() for p in M.rglob('*') if p.is_file()}; out={}
 for name in ['index.html','gamebras-base.html']:
  old=parent(name); assert L['verify'](old); raw,m=L['unpack'](old); b=L['bundle'](raw); orig=json.loads(b['aventura_diabetes.json']); assert orig['clinicalModule']==campaign['clinicalModule']; b.update(files); b['aventura_diabetes.json']=json.dumps({**orig,**campaign},ensure_ascii=False,separators=(',',':')).encode(); src='_module_sources/diabetes/aventura_diabetes.json.txt'; b[src]=files['aventura_diabetes.json']; z=io.BytesIO()
  with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
   for p,v in sorted(b.items()):
    i=zipfile.ZipInfo(p,(2026,11,27,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;f.writestr(i,v,compresslevel=9)
  new=L['BUNDLE'].sub(lambda x:x[1]+base64.b64encode(z.getvalue())+x[3],raw,count=1); assert L['BUNDLE'].sub(b'',new)==L['BUNDLE'].sub(b'',raw)
  prev=m['version_id']; m.update(content_hash=L['digest'](new),parents=[prev],parent_urls=[f'{m["repository"]}/blob/{BASE}/{name}'],git_base=BASE,branch=BRANCH,milestone='M6.4.1-ubs-visual')
  for p,v in files.items():m['files']['modules/diabetes/'+p]={'hash':L['digest'](v),'bundle':src if p=='aventura_diabetes.json' else p}
  for p in ['AGENTS.md','tools/build-ubs-visual.py']:
   v=(R/p).read_bytes();m['files'][p]={'hash':L['digest'](v),'data':base64.b64encode(v).decode()}
  m['version_id']=L['identity'](m); result=new.replace(b'</head>',b'<script id="gb-lineage" type="application/json">'+L['canonical'](m)+b'</script>\n</head>',1);assert L['verify'](result);out[name]=result
 return out
if __name__=='__main__':
 for n,v in build(lambda n:subprocess.check_output(['git','show',f'{BASE}:{n}'],cwd=R)).items():(R/n).write_bytes(v)
