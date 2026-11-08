#!/usr/bin/env python3
"""Relink one release ELF using an installed SDK; never replace the release PKG."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--game',choices=['tfe','tse'],required=True)
p.add_argument('--verify',action='store_true')
a=p.parse_args(); root=Path(__file__).resolve().parent
sdk=os.environ.get('OO_PS4_TOOLCHAIN','/opt/openorbis/OpenOrbis/PS4Toolchain')
args=[s.replace('@SDK@',sdk) for s in json.loads((root/f'link/{a.game}/arguments.json').read_text())]
subprocess.run(args,cwd=root,check=True)
output=root/f'{a.game}-relinked.elf'
actual=hashlib.sha256(output.read_bytes()).hexdigest()
if a.verify and actual!=json.loads((root/'BUILD.json').read_text())['builds'][a.game]['elf_sha256']:
    raise SystemExit('ELF hash mismatch: '+actual)
print(a.game+': '+actual)
