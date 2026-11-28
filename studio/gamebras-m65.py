#!/usr/bin/env python3
"""Experimental distribution builder. Never changes source or publishes."""
import argparse, base64, io, json, re, runpy, zipfile, hashlib, html
from pathlib import Path

def build(source, output, profile, parent_url, keep_pixel=False, keep_context=False):
    L=runpy.run_path(str(source.parent/'tools/gamebras-m641.py'))
    original=source.read_bytes()
    if not L['verify'](original): raise ValueError('Manifesto original inválido')
    raw,old=L['unpack'](original); assets=L['bundle'](raw); before=dict(assets)
    if profile=='dev': keep_pixel=keep_context=True
    if not keep_pixel:
        assets={k:v for k,v in assets.items() if not k.startswith('_tools/pixelbras/')}
        anchor=b'function openPixelEditor(){'
        assert raw.count(anchor)==1
        raw=raw.replace(anchor,anchor+"status('PixelBras não incluído nesta distribuição.');return;".encode(),1)
    if not keep_context:
        raw,n=re.subn(rb'<script id="gb-portable-context">.*?</script>\s*',b'',raw,flags=re.S); assert n==1
    if profile=='user':
        css=b'<style id="gb-distribution-ui">#rf-open-work,#rf-mode,#gb-open-audio{display:none!important}</style>\n'
        raw=raw.replace(b'</head>',css+b'</head>',1)
    if assets!=before:
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            for k,v in sorted(assets.items()):z.writestr(zipfile.ZipInfo(k,(1980,1,1,0,0,0)),v,compress_type=zipfile.ZIP_DEFLATED)
        raw=L['BUNDLE'].sub(lambda m:m[1]+base64.b64encode(buf.getvalue())+m[3],raw,count=1)
    files={k:v for k,v in old.get('files',{}).items() if keep_context and ('bundle' not in v or v['bundle'] in assets)}
    # Retain credits/license entries even in lean profiles.
    for k,v in old.get('files',{}).items():
        if any(x in k.lower() for x in ('licen','credit','source.txt')) and ('bundle' not in v or v['bundle'] in assets):files[k]=v
    m={k:v for k,v in old.items() if k not in ('version_id','content_hash','parents','parent_urls','files','milestone','git_base','branch')}
    m.update(artifact=output.name,milestone='M6.5-preview',parents=[old['version_id']],parent_urls=[parent_url],files=files,content_hash=L['digest'](raw),distribution={'profile':profile,'pixelbras_payload':keep_pixel,'portable_context':keep_context,'legacy_editor_code_retained':True})
    m['version_id']=L['identity'](m)
    new=raw.replace(b'</head>',b'<script id="gb-lineage" type="application/json">'+L['canonical'](m)+b'</script>\n</head>',1)
    assert L['verify'](new)
    assert all(assets[k]==v for k,v in before.items() if not k.startswith('_tools/pixelbras/'))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(new)
    print(output,len(original),'->',len(new),m['version_id'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--profile',choices=['dev','user','custom'],default='user');p.add_argument('--parent-url',required=True);p.add_argument('--pixelbras',action='store_true');p.add_argument('--context',action='store_true');a=p.parse_args()
    if a.source.resolve()==a.output.resolve():p.error('Não sobrescreva a fonte')
    build(a.source,a.output,a.profile,a.parent_url,a.pixelbras,a.context)
