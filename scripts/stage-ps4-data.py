#!/usr/bin/env python3
"""Stage a local TFE runtime for shadPS4; retail assets remain outside Git."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
stage = root/'build/runtime-tfe'
stage.mkdir(parents=True, exist_ok=True)
source = root/'engine-vk/SamTFE'
for name in ['Controls', 'Data', 'Demos', 'Help', 'Players', 'Scripts', 'SE1_10b.gro', 'ModEXT.txt']:
    item, target = source/name, stage/name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)
retail = root/'media/game/tfe/Install'
for name in ['1_00.gro', '1_00_music.gro', '1_00_ExtraTools.gro', 'Levels']:
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
