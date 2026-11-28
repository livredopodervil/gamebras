#!/usr/bin/env python3
"""Rebuild the v6.4.1 diabetes expansion without network access."""
import argparse
import base64
import io
import json
import re
import runpy
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "diabetes"
BASE = "854a2d926315948dd8b0e746b87c72a64914567d"
BRANCH = "feat/diabetes-pbl-v6.4.1"
CAMPAIGN = "aventura_diabetes.json"
LINEAGE = runpy.run_path(str(ROOT / "tools" / "gamebras-m641.py"))
RUNTIME = re.compile(
    rb'^[ 	]*<script (?:src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"'
    rb'|id="gb-(?:three|mp3)-runtime")>.*?</script>', re.S | re.M
)
ARTIFACTS = ("gamebras-base.html", "index.html")


def git_show(name):
    return subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=ROOT)


def module_files():
    files = {p.relative_to(MODULE).as_posix(): p.read_bytes() for p in sorted(MODULE.rglob("*")) if p.is_file()}
    campaign = json.loads(files[CAMPAIGN])
    clinical = campaign["clinicalModule"]
    for name, doc in clinical["docs"].items():
        if name not in files or files[name].decode() != doc:
            raise ValueError(f"Documento divergente no JSON: {name}")

    def check_assets(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key == "imageUrl" and value.removeprefix("./") not in files:
                    raise ValueError(f"Imagem ausente no módulo: {value}")
                check_assets(value)
        elif isinstance(item, list):
            for child in item:
                check_assets(child)

    check_assets(campaign)
    if campaign.get("phases"):
        raise ValueError("O módulo isolado não deve duplicar campanhas da distribuição.")
    return files, campaign


def zip_bytes(files):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            entry = ZipInfo(name, date_time=(2026, 11, 27, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compresslevel=9)
    return buffer.getvalue()


def with_runtime(source, parent_raw):
    snippets = RUNTIME.findall(parent_raw)
    if len(snippets) != 2 or len(RUNTIME.findall(source)) != 2:
        raise ValueError("Âncoras dos runtimes não correspondem à base.")
    replacements = iter(snippets)
    return RUNTIME.sub(lambda _: next(replacements), source)


def seal(raw, previous, name, files, dev_entries):
    manifest = dict(previous)
    manifest.update(
        artifact=name,
        branch=BRANCH,
        content_hash=LINEAGE["digest"](raw),
        files={**previous["files"], **dev_entries},
        git_base=BASE,
        milestone="M6.4.1-diabetes-pbl",
        parent_urls=[f'{previous["repository"]}/blob/{BASE}/{name}'],
        parents=[previous["version_id"]],
    )
    for path, content in files.items():
        manifest["files"]["modules/diabetes/" + path] = {
            "hash": LINEAGE["digest"](content), "bundle": path
        }
    manifest["version_id"] = LINEAGE["identity"](manifest)
    tag = b'<script id="gb-lineage" type="application/json">' + LINEAGE["canonical"](manifest) + b"</script>\n"
    if raw.count(b"</head>") != 1:
        raise ValueError("Não foi possível localizar o cabeçalho único.")
    data = raw.replace(b"</head>", tag + b"</head>", 1)
    if not LINEAGE["verify"](data):
        raise ValueError(f"Falha na verificação de {name}.")
    return data


def build():
    source, _ = LINEAGE["unpack"]((ROOT / ARTIFACTS[0]).read_bytes())
    files, campaign = module_files()
    filenames = ["AGENTS.md", "README.md", "tools/build-diabetes.py", "tests/gb-diabetes-pbl.test.cjs"]
    display_test = ROOT / "tests" / "gb-diabetes-browser.cjs"
    if display_test.is_file():
        filenames.append("tests/gb-diabetes-browser.cjs")
    dev_entries = {}
    for name in filenames:
        data = (ROOT / name).read_bytes()
        dev_entries[name] = {"hash": LINEAGE["digest"](data), "data": base64.b64encode(data).decode()}

    output = {}
    bundle_pattern = LINEAGE["BUNDLE"]
    for name in ARTIFACTS:
        parent = git_show(name)
        if not LINEAGE["verify"](parent):
            raise ValueError(f"Manifesto ancestral inválido: {name}")
        parent_raw, previous = LINEAGE["unpack"](parent)
        bundle = LINEAGE["bundle"](parent_raw)
        legacy = json.loads(bundle[CAMPAIGN])
        bundle.update(files)
        combined = {**legacy, **campaign}
        bundle[CAMPAIGN] = (json.dumps(combined, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        # The manifest points to the standalone JSON, while root JSON retains legacy phases.
        source_name = "_module_sources/diabetes/aventura_diabetes.json.txt"
        bundle[source_name] = files[CAMPAIGN]
        runtime_html = with_runtime(source, parent_raw)
        payload = base64.b64encode(zip_bytes(bundle))
        raw, count = bundle_pattern.subn(lambda match: match[1] + payload + match[3], runtime_html)
        if count != 1:
            raise ValueError("Âncora única do ZIP incorporado não encontrada.")
        dev = {**dev_entries, "modules/diabetes/" + CAMPAIGN: {
            "hash": LINEAGE["digest"](files[CAMPAIGN]), "bundle": source_name
        }}
        output[name] = seal(raw, previous, name, {p: b for p, b in files.items() if p != CAMPAIGN}, dev)
    output["gamebras-diabetes-modulo.zip"] = zip_bytes(files)
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output-dir", type=Path, help="Diretório para os dois HTMLs e o ZIP do módulo")
    mode.add_argument("--check", action="store_true", help="Verificar correspondência com os HTMLs versionados")
    args = ap.parse_args()
    for name, data in build().items():
        if args.check:
            if name in ARTIFACTS and (ROOT / name).read_bytes() != data:
                raise SystemExit(f"{name}: regenere a distribuição a partir do módulo.")
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            (args.output_dir / name).write_bytes(data)
        print(f"{name} · {len(data):,} bytes · {LINEAGE['digest'](data)}")


if __name__ == "__main__":
    main()
