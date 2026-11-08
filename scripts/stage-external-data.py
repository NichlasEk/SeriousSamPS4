#!/usr/bin/env python3
"""Copy and hash-check a complete external data folder; owned assets stay local."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', choices=['tfe', 'tse'], required=True)
game = parser.parse_args().game
folder = 'serioussam-game' if game == 'tfe' else 'serioussamse-game'
source = root/f'build/runtime-{game}'
target = root/'dist/external-data'/folder
target.mkdir(parents=True, exist_ok=True)
names = ['Controls', 'Data', 'Demos', 'Help', 'Players', 'Scripts', 'SE1_10b.gro', 'ModEXT.txt']
names += (['1_00.gro', '1_00_music.gro', 'Levels'] if game == 'tfe' else
          ['SE1_00.gro', 'SE1_00_Extra.gro', 'SE1_00_Levels.gro', 'SE1_00_Music.gro'])

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

files = {}
for name in names:
    item = source/name
    entries = sorted(item.rglob('*')) if item.is_dir() else [item]
    for entry in entries:
        if not entry.is_file():
            continue
        relative = entry.relative_to(source)
        dest = target/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '--reflink=auto', '--', str(entry), str(dest)], check=True)
        digest = sha(entry)
        if sha(dest) != digest:
            raise SystemExit(f'Copy mismatch: {relative}')
        files[str(relative)] = digest
# The engine uses a virtual executable path below this directory.
(target/'Bin').mkdir(exist_ok=True)
actual = {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}
if actual != set(files):
    raise SystemExit('Unexpected files in external data folder; review before delivery')
manifest = dict(game=game, folder=folder, files=files,
                bytes=sum((target/name).stat().st_size for name in files),
                source_and_destination_hashes_verified=True)
(root/f'dist/external-data/{folder}.manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Verified external data: {target} ({len(files)} files)')
