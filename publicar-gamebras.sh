#!/usr/bin/env bash
# Run in the extracted kit after testing the built index.html. No force push.
set -euo pipefail
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STAGE="${1:-$BASE/publicacao}"
OWNER="${GAMEBRAS_GITHUB_OWNER:-livredopodervil}"
SITE="${GAMEBRAS_SITE_REPO:-rogerioduarte.org}"
[[ "$OWNER" =~ ^[a-zA-Z0-9-]+$ && "$SITE" =~ ^[a-zA-Z0-9._-]+$ ]] || { echo 'Nome GitHub inválido'; exit 1; }
[[ -s "$STAGE/index.html" && -s "$STAGE/BUILD.txt" ]] || { echo 'Monte o HTML offline antes de publicar.'; exit 1; }
python - "$STAGE/index.html" <<'PY'
import sys,re,base64,zipfile,io,json
from html.parser import HTMLParser
from pathlib import Path
s=Path(sys.argv[1]).read_text()
class Check(HTMLParser):
 def __init__(self):super().__init__();self.bad=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script' and dict(attrs).get('src'):self.bad.append(dict(attrs)['src'])
c=Check();c.feed(s);assert not c.bad,c.bad
assert 'id="gb-three-runtime"' in s and 'GB_MP3_RUNTIME' not in s
m=re.search(r'<script id="rf-bundle" type="application/octet-stream">([^<]+)</script>',s);assert m
z=zipfile.ZipFile(io.BytesIO(base64.b64decode(m[1])));assert z.testzip() is None
for n in ('_tools/pixelbras/index.html','_tools/pixelbras/transform-engine.js','_tools/pixelbras/tailwind.js','_runtime/three-LICENSE.txt','_runtime/lamejs-LICENSE.txt'):assert n in z.namelist(),n
d=json.loads(z.read('aventura_diabetes.json'));assert {'nordeste','polo_industrial'}<=set(d['phases']);assert 'models/coqueiro.gbmodel.json' in z.namelist();print('HTML offline, campanhas e bundle: OK')
PY
command -v git >/dev/null
SITE_URL="git@github.com:$OWNER/$SITE.git"
GAME_URL="git@github.com:$OWNER/gamebras.git"
WORK="$(mktemp -d "${HOME}/gamebras-publicacao-XXXXXX")"
echo "Área de trabalho preservada: $WORK"
# First inspect the site's actual main and clone; do not touch user's current worktree.
git ls-remote --exit-code "$SITE_URL" refs/heads/main >/dev/null
git clone --quiet --branch main "$SITE_URL" "$WORK/site"
git -C "$WORK/site" status --short
git -C "$WORK/site" log -1 --format='SITE HEAD %H %s'
# Validate the homepage and generate only an additive section. No replacement of existing sections.
python - "$WORK/site" "$STAGE/index.html" <<'PY'
import sys,re,shutil
from pathlib import Path
site=Path(sys.argv[1]); src=Path(sys.argv[2]); home=site/'index.html'; dest=site/'gamebras'/'index.html'
if not home.is_file() or home.is_symlink():raise SystemExit('Homepage index.html não encontrada ou é link: inspeção manual necessária.')
s=home.read_text(encoding='utf-8');mark='<!-- GAMEBRAS-SECTION -->';end='<!-- /GAMEBRAS-SECTION -->'
section='''<!-- GAMEBRAS-SECTION -->
<section id="gamebras" aria-label="Gamebras Alfa" style="padding:1rem;margin:1rem auto;max-width:64rem;border:1px solid currentColor;border-radius:.8rem">
  <h2>Gamebras Alfa</h2>
  <p>Engine brasileira de jogos 2.5D e editor de aventuras, com PixelBras integrado.</p>
  <a href="/gamebras/">Abrir Gamebras Alfa</a>
</section>
<!-- /GAMEBRAS-SECTION -->'''
if mark in s or end in s:
 if s.count(mark)!=1 or s.count(end)!=1 or s.index(mark)>s.index(end):raise SystemExit('Marcadores Gamebras inconsistentes; nenhuma alteração publicada.')
 s=s[:s.index(mark)]+section+s[s.index(end)+len(end):]
elif re.search(r'''href\s*=\s*["'](?:https://rogerioduarte\.org)?/gamebras/?["']''',s,re.I):
 print('Link Gamebras já existe: homepage mantida.')
else:
 matches=list(re.finditer(r'</main\s*>',s,re.I)) or list(re.finditer(r'</body\s*>',s,re.I))
 if len(matches)!=1:raise SystemExit('Estrutura da homepage não reconhecida; inspeção manual necessária.')
 i=matches[0].start();s=s[:i]+section+'\n'+s[i:]
if dest.exists() and ('Gamebras' not in dest.read_text(encoding='utf-8',errors='replace') or dest.is_symlink()):raise SystemExit('Destino gamebras/index.html já existe e não foi reconhecido como Gamebras.')
if dest.parent.is_symlink():raise SystemExit('Diretório de destino é link simbólico.')
dest.parent.mkdir(exist_ok=True);shutil.copyfile(src,dest);home.write_text(s,encoding='utf-8');print('Seção preparada:',dest)
PY
# Verify repository access. Creation is authorized by the user's explicit publication request.
if ! git ls-remote "$GAME_URL" >"$WORK/game-refs" 2>"$WORK/game-error"; then
  command -v gh >/dev/null || { cat "$WORK/game-error"; echo 'Para criar o repositório, instale gh e autentique-se (gh auth login); depois execute novamente.'; exit 1; }
  LOGIN="$(gh api user --jq .login)"
  [[ "${LOGIN,,}" == "${OWNER,,}" ]] || { echo "Conta autenticada ($LOGIN) difere do proprietário ($OWNER)."; exit 1; }
  if gh api "repos/$OWNER/gamebras" >"$WORK/game-info.json" 2>"$WORK/gh-error"; then
    echo 'O repositório existe, mas SSH falhou. Corrija o acesso SSH.'; exit 1
  elif grep -q 'HTTP 404' "$WORK/gh-error"; then
    printf 'Criar repositório público %s/gamebras? Digite CRIAR: ' "$OWNER"; read -r consent; [[ "$consent" == CRIAR ]] || exit 1
    gh repo create "$OWNER/gamebras" --public --description 'Gamebras Alfa — engine 2.5D com PixelBras integrado'
  else cat "$WORK/gh-error"; exit 1; fi
  git ls-remote "$GAME_URL" >"$WORK/game-refs"
fi
if grep -q $'\trefs/heads/main$' "$WORK/game-refs"; then
 git clone --quiet --branch main "$GAME_URL" "$WORK/gamebras"
elif [[ ! -s "$WORK/game-refs" ]]; then
 git init -q -b main "$WORK/gamebras"
 git -C "$WORK/gamebras" remote add origin "$GAME_URL"
else echo 'Repositório Gamebras não vazio e sem main. Interrompido para não substituir história.'; exit 1; fi
# Keep existing repository files; update only build artifacts managed by this kit.
for name in index.html gamebras-base.html montar-gamebras.py BUILD.txt README.md AGENTS.md .nojekyll; do
 if [[ -f "$STAGE/$name" ]]; then
   if [[ "$name" == README.md || "$name" == AGENTS.md ]] && [[ -e "$WORK/gamebras/$name" ]]; then continue; fi
   cp -- "$STAGE/$name" "$WORK/gamebras/$name"
 fi
done
for name in publicar-gamebras.sh; do cp -- "$BASE/$name" "$WORK/gamebras/$name"; done
# Only tracked/intended files from fresh worktrees.
git -C "$WORK/gamebras" add -- index.html gamebras-base.html montar-gamebras.py BUILD.txt README.md AGENTS.md .nojekyll publicar-gamebras.sh
git -C "$WORK/site" add -- index.html gamebras/index.html
for repo in gamebras site; do
 git -C "$WORK/$repo" status --short
 git -C "$WORK/$repo" diff --cached --stat
 git -C "$WORK/$repo" diff --cached --check
done
git -C "$WORK/site" diff --cached -- index.html
printf '\nConfirme que testou o HTML, autorizou redistribuição do PixelBras e não há gravações privadas. Digite PUBLICAR para commit/push em main: '
read -r consent
[[ "$consent" == PUBLICAR ]] || { echo "Cancelado; clones locais preservados: $WORK"; exit 1; }
for repo in gamebras site; do
 if ! git -C "$WORK/$repo" diff --cached --quiet; then git -C "$WORK/$repo" commit -m "feat(gamebras): publish alpha with campaigns and asset calibration"; fi
done
# No force, no reset. If either remote moved, Git stops on non-fast-forward.
git -C "$WORK/gamebras" push -u origin main
git -C "$WORK/site" push origin main
for repo in gamebras site; do
 local_head="$(git -C "$WORK/$repo" rev-parse HEAD)"
 remote_head="$(git -C "$WORK/$repo" ls-remote origin refs/heads/main | cut -f1)"
 [[ "$local_head" == "$remote_head" ]] || { echo "HEAD remoto mudou: $repo"; exit 1; }
 echo "$repo MAIN CONFIRMADO: $local_head"
done
echo "Página de destino: https://rogerioduarte.org/gamebras/ (aguarde o deploy configurado no site)."
echo "Repositórios locais: $WORK"
