#!/usr/bin/env python3
"""Run a PS4 test with a private PulseAudio sink and save only its audio."""
from array import array
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import wave

root = Path(__file__).resolve().parents[1]
out = root/'artifacts/ps4'
out.mkdir(parents=True, exist_ok=True)
sink = f'serioussam_test_{os.getpid()}'
module = subprocess.check_output(['pactl', 'load-module', 'module-null-sink',
                                 f'sink_name={sink}', 'rate=48000', 'channels=2'], text=True).strip()
recorder = None
test = None
(out/'emulator.pid').unlink(missing_ok=True)
try:
    with (out/'audio.pcm').open('wb') as stream:
        recorder = subprocess.Popen(['parec', '--raw', '--format=s16le', '--rate=48000',
                                     '--channels=2', '--device='+sink+'.monitor'], stdout=stream)
        try:
            test = subprocess.Popen([sys.executable, str(root/'scripts/run-ps4.py'), *sys.argv[1:]],
                                    env=dict(os.environ, PULSE_SINK=sink, SDL_AUDIODRIVER='pulseaudio'))
            routed = set()
            while test.poll() is None:
                pidfile = out/'emulator.pid'
                if pidfile.exists():
                    pid = pidfile.read_text().strip()
                    streams = json.loads(subprocess.check_output(
                        ['pactl', '--format=json', 'list', 'sink-inputs'], stderr=subprocess.PIPE))
                    for item in streams:
                        if str(item.get('properties', {}).get('application.process.id')) == pid and item['index'] not in routed:
                            subprocess.run(['pactl', 'move-sink-input', str(item['index']), sink], check=True)
                            routed.add(item['index'])
                time.sleep(.5)
        finally:
            if test is not None and test.poll() is None:
                test.terminate()
                test.wait(timeout=15)
            recorder.terminate()
            recorder.wait(timeout=5)
finally:
    subprocess.run(['pactl', 'unload-module', module], check=True)
pcm = (out/'audio.pcm').read_bytes()
with wave.open(str(out/'audio.wav'), 'wb') as output:
    output.setnchannels(2)
    output.setsampwidth(2)
    output.setframerate(48000)
    output.writeframes(pcm)
samples = array('h', pcm)
if sys.byteorder != 'little':
    samples.byteswap()
stats = {'seconds': len(samples)/96000, 'nonzero_samples': sum(s != 0 for s in samples),
         'peak': max((abs(s) for s in samples), default=0),
         'rms': math.sqrt(sum(s*s for s in samples)/max(1, len(samples))),
         'note': 'Signal capture does not prove perceptual quality or physical PS4 output.'}
(out/'audio.json').write_text(json.dumps(stats, indent=2)+'\n')
print(stats)
raise SystemExit(test.returncode)
