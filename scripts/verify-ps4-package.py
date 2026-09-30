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
parser.add_argument('--existing-extraction',action='store_true')
args=parser.parse_args()
manifest=json.loads((root/'artifacts/package/manifest.json').read_text())
package=Path(manifest['package'])
stage=root/'build/package-tfe'
output=root/'build/package-tfe-extracted'
app=output/'uroot'
tool=Path(os.environ.get('OO_PS4_TOOLCHAIN','/opt/openorbis/OpenOrbis/PS4Toolchain'))/'bin/linux/PkgTool.Core'
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
if list(app.rglob('*.prx')) or list(app.rglob('*.sprx')):
    raise SystemExit('Unexpected additional runtime module')
packed=sfo(app/'sce_sys/param.sfo')
def field(key): return packed[key][1].rstrip(b'\0').decode()
title_id=field('TITLE_ID')
if not re.fullmatch(r'[A-Z]{4}[0-9]{5}',title_id):
    raise SystemExit('Invalid title ID format')
if field('CONTENT_ID') != 'IV0000-'+title_id+'_00-SERIOUSSAMTFE001':
    raise SystemExit('Content/title identity mismatch')
if title_id!=manifest['title_id'] or field('APP_VER')!=manifest['version']:
    raise SystemExit('Manifest/SFO identity mismatch')
result=dict(passed=True,checked_files=len(manifest['files']),package_sha256=manifest['sha256'],
            sfo_check='All application fields preserved; generated PUBTOOL fields allowed')
(root/'artifacts/package/extraction-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
