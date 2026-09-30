#!/usr/bin/env python3
"""Run the local PS4 client in an isolated shadPS4 profile and capture its window."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=int, default=25)
parser.add_argument('--display-ready', action='store_true')
args = parser.parse_args()
if args.seconds < 1:
    parser.error('--seconds must be positive')
if not args.display_ready:
    raise SystemExit(subprocess.call(['xvfb-run', '-a', '-s', '-screen 0 1280x720x24',
                                     sys.executable, __file__, '--display-ready', '--seconds', str(args.seconds)]))
emulator = os.environ.get('SHADPS4', '/home/nichlas/ScummVM-PS4/.tools/shadps4/Shadps4-sdl.AppImage')
eboot = root/'build/runtime-tfe/eboot.bin'
if not eboot.is_file():
    raise SystemExit('Build the PS4 client first')
eboot_hash = hashlib.sha256(eboot.read_bytes()).hexdigest()
out = root/'artifacts/ps4'
out.mkdir(parents=True, exist_ok=True)
(out/'emulator.png').unlink(missing_ok=True)
started = time.monotonic()
timed_stop = False
captured = False
profile = root/'build/emulator-profile'
(profile/'shadPS4/data').mkdir(parents=True, exist_ok=True)
env = dict(os.environ, XDG_DATA_HOME=str(profile), SDL_VIDEODRIVER='x11')
with (out/'emulator.log').open('w') as log:
    process = subprocess.Popen([emulator, '--fullscreen', 'false', str(eboot)], env=env,
                               stdout=log, stderr=log, start_new_session=True)
    try:
        deadline = time.monotonic() + args.seconds
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.5)
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
    'note': 'Process survival and capture are not proof of correct gameplay.'
}, indent=2) + '\n')
if not timed_stop:
    raise SystemExit('Emulator exited before the requested capture time; inspect emulator.log')
