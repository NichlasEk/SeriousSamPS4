#!/usr/bin/env python3
"""Extract a package, restore its metadata entries and verify staged file hashes."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', choices=['tfe', 'tse'], default='tfe')
parser.add_argument('--existing-extraction',action='store_true')
args=parser.parse_args()
out=root/f'artifacts/package-{args.game}-external'
manifest=json.loads((out/'manifest.json').read_text())
package=Path(manifest['package'])
stage=root/f'build/package-{args.game}-external'
output=root/f'build/package-{args.game}-external-extracted'
app=output/'uroot'
tool=Path(os.environ.get('OO_PS4_TOOLCHAIN','/opt/openorbis/OpenOrbis/PS4Toolchain'))/'bin/linux/PkgTool.Core'
# Isolate the SDK's self-extracting .NET runtime from stale shared /tmp caches.
os.environ.setdefault('DOTNET_BUNDLE_EXTRACT_BASE_DIR', str(root/'build/pkgtool-dotnet'))
def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
if sha(package)!=manifest['sha256']:
    raise SystemExit('Package checksum mismatch')
if not args.existing_extraction:
    subprocess.run([str(tool),'pkg_extract',str(package),str(output)],check=True)
    entries=subprocess.check_output([str(tool),'pkg_listentries',str(package)],text=True)
    for key,name in [('ICON0_PNG','icon0.png'),('PARAM_SFO','param.sfo')]:
        row=next(line.split() for line in entries.splitlines() if line.split()[-1:]==[key])
        subprocess.run([str(tool),'pkg_extractentry',str(package),row[3],str(app/'sce_sys'/name)],check=True)

def sfo(path):
    data=path.read_bytes()
    magic,version,keys,values,count=struct.unpack_from('<4sIIII',data)
    if magic!=b'\x00PSF': raise ValueError('Invalid SFO magic')
    result={}
    for i in range(count):
        key,fmt,length,capacity,value=struct.unpack_from('<HHIII',data,20+i*16)
        name=data[keys+key:].split(b'\x00',1)[0].decode()
        result[name]=(fmt,data[values+value:values+value+length])
    return result

for name,expected in manifest['files'].items():
    if name=='sce_sys/param.sfo':
        # PkgTool adds PUBTOOLINFO/PUBTOOLVER during packing; retain all input fields.
        original=sfo(stage/name)
        packed=sfo(app/name)
        if any(packed.get(key)!=value for key,value in original.items()):
            raise SystemExit('Packaged SFO changed an application field')
        if set(packed)-set(original)-{'PUBTOOLINFO','PUBTOOLVER'}:
            raise SystemExit('Unexpected generated SFO fields')
    elif sha(app/name)!=expected:
        raise SystemExit('Extracted file mismatch: '+name)
# Independently pinned SDK support files from the working Doom 3 0.06 package.
# Emulator boot and DT_NEEDED inspection do not validate this console contract.
support_modules = {
    'sce_module/libc.prx': '39ad53672bb0b14895f8465eb1619478ab935f5afe5dbf69c15f02cfc0a75ce6',
    'sce_module/libSceFios2.prx': '3f8236c5996cf8e9917b8d27706d9743f6603d89de3b9859eacbb9f466b19c01',
    'sce_sys/about/right.sprx': 'e3416f9c6152276b494982baf7b65ebcd8052274ffc42f95a776318022842b64',
}
if list(app.rglob('*.gro')) or (app/'Levels').exists():
    raise SystemExit('External package unexpectedly contains retail game data')
actual_modules = {path.relative_to(app).as_posix()
                  for pattern in ('*.prx', '*.sprx') for path in app.rglob(pattern)}
if actual_modules != set(support_modules):
    raise SystemExit('Missing or unexpected SDK support modules: '+repr(actual_modules))
for name, expected in support_modules.items():
    if sha(app/name) != expected:
        raise SystemExit('Unreviewed SDK support module: '+name)
packed=sfo(app/'sce_sys/param.sfo')
def field(key): return packed[key][1].rstrip(b'\0').decode()
title_id=field('TITLE_ID')
if title_id != ('SSAM00001' if args.game == 'tfe' else 'SSAM00002'):
    raise SystemExit('Wrong title identity for selected encounter')
if not re.fullmatch(r'[A-Z]{4}[0-9]{5}',title_id):
    raise SystemExit('Invalid title ID format')
if field('CONTENT_ID') != 'IV0000-'+title_id+f'_00-SERIOUSSAM{args.game.upper()}001':
    raise SystemExit('Content/title identity mismatch')
if title_id!=manifest['title_id'] or field('APP_VER')!=manifest['version']:
    raise SystemExit('Manifest/SFO identity mismatch')
result=dict(passed=True,checked_files=len(manifest['files']),package_sha256=manifest['sha256'],
            sdk_support_modules=support_modules,
            sfo_check='All application fields preserved; generated PUBTOOL fields allowed')
(out/'extraction-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
