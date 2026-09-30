#!/usr/bin/env python3
"""Stage a local runtime for shadPS4; retail assets remain outside Git."""
from pathlib import Path
import argparse
import shutil

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', choices=['tfe', 'tse'], default='tfe')
args = parser.parse_args()
stage = root/f'build/runtime-{args.game}'
stage.mkdir(parents=True, exist_ok=True)
source = root/'engine-vk'/('SamTFE' if args.game == 'tfe' else 'SamTSE')
for name in ['Controls', 'Data', 'Demos', 'Help', 'Players', 'Scripts', 'SE1_10b.gro', 'ModEXT.txt']:
    item, target = source/name, stage/name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)
retail = root/f'media/game/{args.game}/Install'
names = (['1_00.gro', '1_00_music.gro', '1_00_ExtraTools.gro', 'Levels'] if args.game == 'tfe'
         else ['SE1_00.gro', 'SE1_00_Extra.gro', 'SE1_00_Levels.gro', 'SE1_00_Music.gro'])
for name in names:
    item, target = retail/name, stage/name
    if not item.exists():
        raise SystemExit(f'Missing retail data: {item}; run scripts/extract_discs.py')
    if target.exists() or target.is_symlink():
        if not target.is_symlink() or target.resolve() != item.resolve():
            raise SystemExit(f'Existing staging path differs: {target}')
    else:
        target.symlink_to(item)
(stage/'Bin').mkdir(exist_ok=True)
print(stage)
