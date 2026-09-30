#!/usr/bin/env python3
"""Load one campaign level through the normal New Game menu in an isolated test.

Only the disposable runtime's startup script is changed. Production packages,
retail archives and the regular emulator profile are left intact.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', choices=['tfe', 'tse'], required=True)
parser.add_argument('--level', required=True, help='Engine-relative .wld path')
parser.add_argument('--seconds', type=int, default=90)
args = parser.parse_args()
if args.seconds < 81:
    parser.error('--seconds must be at least 81 for the menu sequence')
level = args.level.replace('\\', '/')
if not level.startswith('Levels/') or not level.endswith('.wld') or any(c in level for c in '\";\n\r') or '..' in level:
    parser.error('Expected a safe Levels/...wld path')
case = Path(level).stem
base = root/f'build/level-tests/{args.game}/{case}'
stage = base/'runtime'
if base.exists():
    parser.error(f'Previous evidence exists: {base}; use a new case or archive it first')
stage.mkdir(parents=True)
source = root/f'build/package-{args.game}-extracted/uroot'
for item in source.iterdir():
    if item.name == 'Scripts':
        shutil.copytree(item, stage/item.name)
    elif item.name == 'eboot.bin':
        shutil.copy2(item, stage/item.name)
    else:
        (stage/item.name).symlink_to(item, target_is_directory=item.is_dir())
# The shell parser understands doubled backslashes in string literals.
script_level = level.replace('/', '\\\\')
with (stage/'Scripts/Game_startup.ini').open('a') as f:
    f.write(f'\nsam_bAutoPlayDemos=0;\nsam_strFirstLevel="{script_level}";\n')
actions=[]
for at, key in [(25,'n'),(29,'n'),(33,'n'),(37,'n'),(65,'o'),(70,'o'),(78,'Return')]:
    actions.extend([dict(at=at,type='keydown',key=key),dict(at=at+.3,type='keyup',key=key)])
actions.append(dict(at=args.seconds-2,type='capture',name='level.png'))
action_file=base/'actions.json'
action_file.write_text(json.dumps(actions,indent=2)+'\n')
out=root/f'artifacts/levels/{args.game}/{case}'
subprocess.run([sys.executable,str(root/'scripts/run-ps4.py'),'--game',args.game,
    '--eboot',str(stage/'eboot.bin'),'--profile',str(base/'profile'),
    '--output',str(out),'--seconds',str(args.seconds),'--actions',str(action_file)],check=True)
userdir='serioussam' if args.game=='tfe' else 'serioussamse'
log=base/f'profile/shadPS4/data/{userdir}/SeriousSam.log'
text=log.read_text(errors='replace') if log.is_file() else ''
if log.is_file():
    shutil.copy2(log,out/'SeriousSam.log')
expected="Starting session: '"+level.replace('/','\\')+"'"
started=expected in text and 'Adding player:' in text[text.index(expected):]
result=dict(game=args.game,level=level,session_and_player_started=started,
            engine_log_present=log.is_file(),
            note='Level load smoke test, not a campaign playthrough or transition test.')
(out/'level-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
if not started: raise SystemExit('Requested level/player did not start')
