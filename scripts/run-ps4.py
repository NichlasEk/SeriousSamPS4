#!/usr/bin/env python3
"""Run the local PS4 client in an isolated shadPS4 profile and capture its window."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--game', choices=['tfe', 'tse'], default='tfe')
parser.add_argument('--seconds', type=int, default=25)
parser.add_argument('--display-ready', action='store_true')
parser.add_argument('--actions', type=Path, help='JSON list of timed X11 key transitions and captures')
parser.add_argument('--eboot', type=Path)
parser.add_argument('--profile', type=Path, help='Separate emulator data/profile directory')
parser.add_argument('--output', type=Path, help='Separate evidence directory')
args = parser.parse_args()
if args.eboot is None:
    args.eboot = root/f'build/runtime-{args.game}/eboot.bin'
if args.seconds < 1:
    parser.error('--seconds must be positive')
if not args.display_ready:
    # Let Xvfb reserve its own free display atomically. Concurrent xvfb-run -a
    # instances can race and attach to the same display before its lock exists.
    read_fd, write_fd = os.pipe()
    server = subprocess.Popen(['Xvfb', '-displayfd', str(write_fd), '-screen', '0',
                               '1280x720x24', '-nolisten', 'tcp'], pass_fds=(write_fd,),
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(write_fd)
    try:
        if not select.select([read_fd], [], [], 15)[0]:
            raise SystemExit('Timed out starting private X display')
        display = os.read(read_fd, 64).decode().strip()
        if not display.isdigit():
            raise SystemExit('Xvfb did not allocate a display')
        command = [sys.executable, __file__, '--game', args.game, '--display-ready',
                   '--seconds', str(args.seconds), '--eboot', str(args.eboot.resolve()),
                   *(['--profile', str(args.profile.resolve())] if args.profile else []),
                   *(['--output', str(args.output.resolve())] if args.output else []),
                   *(['--actions', str(args.actions.resolve())] if args.actions else [])]
        raise SystemExit(subprocess.call(command, env=dict(os.environ, DISPLAY=':'+display)))
    finally:
        os.close(read_fd)
        server.terminate()
        server.wait(timeout=5)
actions = json.loads(args.actions.read_text()) if args.actions else []
for action in actions:
    if action['type'] not in ('keydown', 'keyup', 'capture') or not 0 <= action['at'] < args.seconds:
        raise SystemExit('Invalid action type or time')
actions.sort(key=lambda action: action['at'])
emulator = os.environ.get('SHADPS4', '/home/nichlas/ScummVM-PS4/.tools/shadps4/Shadps4-sdl.AppImage')
eboot = args.eboot.resolve()
if not eboot.is_file():
    raise SystemExit('Build the PS4 client first')
eboot_hash = hashlib.sha256(eboot.read_bytes()).hexdigest()
out = args.output or root/('artifacts/ps4' if args.game == 'tfe' else 'artifacts/ps4-tse')
out.mkdir(parents=True, exist_ok=True)
(out/'emulator.png').unlink(missing_ok=True)
(out/'run.json').unlink(missing_ok=True)
for action in actions:
    if action['type'] == 'capture':
        name = Path(action['name']).name
        if not name.endswith('.png'):
            raise SystemExit('Capture names must end in .png')
        (out/name).unlink(missing_ok=True)
started = time.monotonic()
timed_stop = False
captured = False
profile = args.profile or root/('build/emulator-profile' if args.game == 'tfe' else 'build/emulator-profile-tse')
(profile/'shadPS4/data').mkdir(parents=True, exist_ok=True)
# Current shadPS4 asks about legacy save migration when creating user 1000,
# even for an empty profile. Prepare only our isolated users' empty directories.
for user in range(1000, 1004):
    for directory in ('savedata', 'trophy', 'inputs'):
        (profile/f'shadPS4/home/{user}'/directory).mkdir(parents=True, exist_ok=True)
env = dict(os.environ, XDG_DATA_HOME=str(profile), SDL_VIDEODRIVER='x11')
def stop_on_signal(signum, frame):
    raise KeyboardInterrupt
signal.signal(signal.SIGTERM, stop_on_signal)
with (out/'emulator.log').open('w') as log:
    process = subprocess.Popen([emulator, '--fullscreen', 'false', str(eboot)], env=env,
                               stdout=log, stderr=log, start_new_session=True)
    (out/'emulator.pid').write_text(str(process.pid)+'\n')
    try:
        deadline = time.monotonic() + args.seconds
        action_start = time.monotonic()
        executed = []
        while process.poll() is None and time.monotonic() < deadline:
            while actions and time.monotonic() - action_start >= actions[0]['at']:
                action = actions.pop(0)
                if action['type'] == 'capture':
                    name = Path(action['name']).name
                    subprocess.run(['import', '-window', 'root', str(out/name)], check=True, timeout=10)
                else:
                    subprocess.run([sys.executable, str(root/'scripts/x11-input.py'), action['type'], action['key']], check=True)
                executed.append(action)
            time.sleep(0.05)
        if process.poll() is None:
            subprocess.run(['import', '-window', 'root', str(out/'emulator.png')], check=True, timeout=10)
            captured = True
            timed_stop = True
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
print(f'Emulator ended with status {process.returncode}; inspect {out}')
(out/'run.json').write_text(json.dumps({
    'eboot_sha256': eboot_hash,
    'duration_seconds': round(time.monotonic() - started, 2),
    'requested_seconds': args.seconds,
    'stopped_by_runner': timed_stop,
    'screenshot_captured': captured,
    'emulator_exit_status': process.returncode,
    'actions_executed': executed,
    'note': 'Process survival and capture are not proof of correct gameplay.'
}, indent=2) + '\n')
if not timed_stop:
    raise SystemExit('Emulator exited before the requested capture time; inspect emulator.log')
