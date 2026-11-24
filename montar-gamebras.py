#!/usr/bin/env python3
"""Gamebras Alfa: montagem auditável de HTML único. Não publica nem altera repositórios."""
from html.parser import HTMLParser
import argparse, base64, hashlib, io, json, pathlib, re, subprocess, tarfile, tempfile, urllib.request, zipfile, sys
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('html',type=pathlib.Path)
P.add_argument('--pixelbras',type=pathlib.Path,help='Clone local limpo do PixelBras, opcional')
P.add_argument('--compact-only',action='store_true',help='Usa somente o editor compacto interno; não incorpora o código original')
P.add_argument('--three-package',type=pathlib.Path,help='Tarball npm three-0.128.0.tgz local')
P.add_argument('--mp3-package',type=pathlib.Path,help='Tarball npm lamejs-1.2.1.tgz local')
P.add_argument('--tailwind',type=pathlib.Path,help='Build browser Tailwind 3.4.17 local')
P.add_argument('-o','--output',type=pathlib.Path)
P.add_argument('--stage',type=pathlib.Path,help='Cria diretório novo de publicação local, sem git push')
a=P.parse_args();src=a.html.resolve();out=(a.output or src.with_name('gamebras-alfa-offline.html')).resolve()
if out==src or out.exists():sys.exit('A saída já existe ou coincide com a entrada; escolha -o. Nada alterado.')
if a.stage and a.stage.exists():sys.exit('Diretório de preparação já existe; escolha outro. Nada alterado.')
log=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def get(url,limit):
 print('Obtendo',url,flush=True)
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Gamebras-build/1'}),timeout=30) as r:b=r.read(limit+1)
 if not 0<len(b)<=limit:raise ValueError('Tamanho inesperado: '+url)
 return b
def package(name,version,local):
 if local:b=local.read_bytes();where=str(local)
 else:
  meta=json.loads(get('https://registry.npmjs.org/'+name+'/'+version,2_000_000));dist=meta['dist'];where=dist['tarball']
  if not where.startswith('https://registry.npmjs.org/'):raise ValueError('Origem npm inesperada: '+where)
  b=get(where,32_000_000);algo,digest=dist['integrity'].split('-',1)
  if algo!='sha512' or base64.b64encode(hashlib.sha512(b).digest()).decode()!=digest:raise ValueError('Integridade npm inválida: '+name)
 t=tarfile.open(fileobj=io.BytesIO(b),mode='r:gz');meta=json.loads(t.extractfile('package/package.json').read())
 if meta['name']!=name or meta['version']!=version:raise ValueError('Versão de pacote incompatível: '+name)
 log.append(f'{name}@{version} SHA256 {sha(b)} origem {where}')
 return t,b
def member(t,*names):
 for n in names:
  try:
   m=t.getmember('package/'+n)
   if m.isfile() and m.size<=4_000_000:return t.extractfile(m).read()
  except KeyError:pass
 raise ValueError('Arquivo ausente no pacote: '+str(names))
def script(b):return re.sub(r'</script',lambda m:r'<\/script',b.decode('utf-8'),flags=re.I)
html=src.read_text(encoding='utf-8');tag='<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>';mp3tag='<script id="gb-mp3-runtime">/* GB_MP3_RUNTIME */</script>'
if html.count(tag)!=1 or html.count(mp3tag)!=1:sys.exit('Esperava o HTML Gamebras Alfa de preparação, com os dois marcadores intactos.')
m=re.search(r'(<script id="rf-bundle" type="application/octet-stream">)([^<]+)(</script>)',html)
if not m:sys.exit('Bundle ausente.')
old=zipfile.ZipFile(io.BytesIO(base64.b64decode(m.group(2))));assert old.testzip() is None
three,three_src=package('three','0.128.0',a.three_package);threejs=member(three,'build/three.min.js');three_license=member(three,'LICENSE','LICENSE.txt');assert b'REVISION' in threejs and b'128' in threejs and len(threejs)>100000
mp3,mp3_src=package('lamejs','1.2.1',a.mp3_package);mp3js=member(mp3,'lame.min.js');mp3_license=member(mp3,'LICENSE','LICENSE.txt');assert b'Mp3Encoder' in mp3js
# Test libraries in isolated Node process if installed; verifies real encoding before incorporating.
with tempfile.TemporaryDirectory(prefix='gamebras-libs-') as temp:
 root=pathlib.Path(temp);(root/'three.cjs').write_bytes(threejs);(root/'lame.cjs').write_bytes(mp3js+b'\nmodule.exports=lamejs;\n')
 try:subprocess.run(['node','-e',"const t=require('./three.cjs');if(t.REVISION!=='128')throw Error(t.REVISION);const l=require('./lame.cjs');const e=new l.Mp3Encoder(1,44100,96);const b=e.encodeBuffer(new Int16Array(44100));const f=e.flush();if(b.length+f.length<100)throw Error('MP3 vazio');console.log('Three r128 e encoder MP3: OK')"],cwd=root,check=True)
 except FileNotFoundError:print('Node ausente: validação dinâmica das bibliotecas pendente.')
 tools={}
 if a.compact_only:
  raise ValueError('Esta revisão distribui o PixelBras original incorporado. Não use --compact-only.')
 if a.pixelbras or a.tailwind:
  raise ValueError('Esta revisão usa os fontes fixados no bundle interno. Atualizações exigem revisão do adaptador e hashes.')
 for n in old.namelist():
  if n.startswith('_tools/pixelbras/') and not n.endswith('/'):
   tools[n.removeprefix('_tools/pixelbras/')]=old.read(n)
 required=('index.html','transform-engine.js','mask-groups.js','tailwind.js','SOURCE.txt','TAILWIND-LICENSE.txt')
 if not all(n in tools for n in required):raise ValueError('PixelBras original incorporado incompleto.')
 match=re.search(r'const PB_TRUSTED=(\{[^;]+\});',html)
 if not match:raise ValueError('Hashes do PixelBras ausentes.')
 for n,digest in json.loads(match.group(1)).items():
  if n not in tools or sha(tools[n])!=digest:raise ValueError('PixelBras alterado: '+n)
 log.extend([f'Three.js runtime SHA256 {sha(threejs)}',f'LAME runtime SHA256 {sha(mp3js)}'])
 log.append('PixelBras HEAD d9445755b00d66a1c34961cff000f852a22be4dc; CSS Tailwind 4.1.10 compilado')
 log.extend(f'PixelBras/{n} SHA256 {sha(b)}' for n,b in tools.items())
 print('PixelBras incorporado e verificado (nenhum download do repositório necessário).')
 # Keep source package and licenses with every project export. Source of LGPL MP3 encoder remains available and replaceable via this builder.
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
  for f in old.infolist():
   if not f.filename.startswith(('_tools/pixelbras/','_runtime/')):z.writestr(f,old.read(f))
  for n,b in tools.items():z.writestr('_tools/pixelbras/'+n,b)
  z.writestr('_runtime/three-r128.min.js',threejs);z.writestr('_runtime/lamejs-1.2.1.min.js',mp3js);z.writestr('_runtime/three-LICENSE.txt',three_license);z.writestr('_runtime/lamejs-LICENSE.txt',mp3_license);z.writestr('_runtime/lamejs-1.2.1-source.tgz',mp3_src)
  z.writestr('_runtime/BUILD.txt','\n'.join(log)+'\n')
 assert zipfile.ZipFile(io.BytesIO(buf.getvalue())).testzip() is None
 # Replace archive before library tags to avoid offsets changing.
 html=html[:m.start(2)]+base64.b64encode(buf.getvalue()).decode()+html[m.end(2):]
 html=html.replace(tag,'<script id="gb-three-runtime">\n/* Three.js r128 — MIT\n'+three_license.decode('utf-8').replace('*/','* /')+'\n*/\n'+script(threejs)+'\n</script>',1)
 html=html.replace(mp3tag,'<script id="gb-mp3-runtime">\n/* lamejs 1.2.1 — LGPL-3.0; source in _runtime/lamejs-1.2.1-source.tgz and https://github.com/zhuker/lamejs */\n'+script(mp3js)+'\n</script>',1)
 class Check(HTMLParser):
  def __init__(self):super().__init__();self.external=[]
  def handle_starttag(self,tag,attrs):
   if tag=='script' and dict(attrs).get('src'):self.external.append(dict(attrs)['src'])
 check=Check();check.feed(html)
 if check.external:raise ValueError('Ainda existem scripts externos: '+str(check.external))
 with out.open('x',encoding='utf-8') as f:f.write(html)
 if a.stage:
  a.stage.mkdir(parents=True,exist_ok=False);(a.stage/'index.html').write_text(html,encoding='utf-8');(a.stage/'gamebras-base.html').write_bytes(src.read_bytes());(a.stage/'montar-gamebras.py').write_bytes(pathlib.Path(__file__).read_bytes());(a.stage/'.nojekyll').touch();(a.stage/'README.md').write_text('# Gamebras Alfa\n\nEngine de jogos 2.5D. Abra index.html. O projeto, recursos e dependências estão incorporados.\n\nBuild: python montar-gamebras.py gamebras-base.html.\n\nCréditos e licenças no bundle interno (_runtime/ e _tools/). Código do PixelBras sujeito à autorização dos titulares.\n\nPrévia local: python -m http.server 8796 --bind 127.0.0.1\n\nPublicação somente após validação e aprovação. Não publicar gravações privadas.\n',encoding='utf-8');(a.stage/'AGENTS.md').write_text('# Gamebras\nPreservar HTML único, autoria, créditos, compatibilidade JSON e edição mobile. Validar antes de commit/push; nunca publicar conteúdo privado. Não alterar o site principal automaticamente.\n',encoding='utf-8');(a.stage/'BUILD.txt').write_text('\n'.join(log)+'\n',encoding='utf-8')
 print('HTML:',out,'bytes:',out.stat().st_size,'SHA256:',sha(out.read_bytes()));print('Nenhuma publicação executada.')
