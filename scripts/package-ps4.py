#!/usr/bin/env python3
"""Package the external-data alpha and prepare its separate local data folder."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', choices=['tfe', 'tse'], default='tfe')
args = parser.parse_args()
game = args.game
label = game.upper()
sdk = Path(os.environ.get('OO_PS4_TOOLCHAIN', '/opt/openorbis/OpenOrbis/PS4Toolchain'))
stack = Path(os.environ.get('SS_NATIVE_STACK', '/home/nichlas/Doom3-Ps4/build/native'))
runtime = root/f'build/runtime-{game}'
stage = root/f'build/package-{game}-external'
dist = root/'dist'
out = root/f'artifacts/package-{game}-external'
for directory in [stage/'sce_sys', dist, out]:
    directory.mkdir(parents=True, exist_ok=True)
tool = sdk/'bin/linux/PkgTool.Core'
# Isolate the SDK's self-extracting .NET runtime from stale shared /tmp caches.
os.environ.setdefault('DOTNET_BUNDLE_EXTRACT_BASE_DIR', str(root/'build/pkgtool-dotnet'))
title_id = 'SSAM00001' if game == 'tfe' else 'SSAM00002'
content_id = f'IV0000-{title_id}_00-SERIOUSSAM{label}001'
version = '00.04' if game == 'tfe' else '00.02'
release = '0.04' if game == 'tfe' else '0.02'
assert re.fullmatch(r'[A-Z]{2}[0-9]{4}-'+title_id+r'_[0-9]{2}-[A-Z0-9]{16}', content_id)
elf = root/f'build/ps4-{game}/SeriousSam'
imports = set(re.findall(r'\(NEEDED\).*?\[(.*?)\]', subprocess.check_output(['readelf', '-d', str(elf)], text=True)))
allowed = {'libkernel.so', 'libSceGnmDriver.so', 'libScePad.so', 'libSceVideoOut.so',
           'libSceUserService.so', 'libSceAudioOut.so', 'libSceNet.so'}
if not imports or imports - allowed:
    raise SystemExit(f'Unexpected runtime imports: {imports-allowed}')
def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
files = set()
def copy(source, name):
    target = stage/name
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['cp', '--reflink=auto', '--', str(source), str(target)], check=True)
    files.add(name)
copy(runtime/'eboot.bin', 'eboot.bin')
subprocess.run(['python3', str(root/'scripts/stage-external-data.py'), '--game', game], check=True)
# Required loader stubs and shell attribution from the open SDK, matching the
# layout used by the physically tested Doom 3 package. Static linking alone
# does not remove the console's package requirements.
support_modules = ('sce_module/libc.prx', 'sce_module/libSceFios2.prx',
                   'sce_sys/about/right.sprx')
for name in support_modules:
    copy(sdk/'samples/SDL2'/name, name)
for source, name in [(root/'engine-vk/LICENSE', 'SeriousEngine-LICENSE'),
                     (stack/'opengnm/LICENSE', 'OpenGNM-LICENSE'),
                     (stack/'opengnm-psbc/LICENSE', 'PSBC-LICENSE'),
                     (stack/'vulkan-ps4/LICENSE', 'Vulkan-PS4-LICENSE'),
                     (root/'.tools/SDL-PS4/COPYING.txt', 'SDL-LICENSE'),
                     (root/'engine-vk/SamTFE/Sources/External/libvorbis/COPYING', 'Vorbis-LICENSE'),
                     (root/'engine-vk/SamTFE/Sources/External/libogg/COPYING', 'Ogg-LICENSE')]:
    copy(source, 'notices/'+name)
info = {'candidate': f'Serious Sam {label} PS4 Alpha {release}', 'eboot_sha256': digest(runtime/'eboot.bin'),
        'game': game, 'engine_elf_sha256': digest(elf), 'contains_owned_retail_data': False,
        'external_data_folder': 'serioussam-game' if game == 'tfe' else 'serioussamse-game',
        'search_order': ['HDD /data', 'USB slots 0-7'],
        'physical_ps4_tested': False,
        'extra_runtime_modules': {name:digest(stage/name) for name in support_modules}}
(out/'build-info.json').write_text(json.dumps(info, indent=2)+'\n')
copy(out/'build-info.json', 'build-info.json')
copy(root/f'assets/icon0-{game}.png', 'sce_sys/icon0.png')
icon = (stage/'sce_sys/icon0.png').read_bytes()
if (icon[:8] != b'\x89PNG\r\n\x1a\n' or icon[24:26] != bytes([8, 2]) or
    tuple(int.from_bytes(icon[i:i+4], 'big') for i in (16, 20)) != (512, 512)):
    raise SystemExit('Icon must be a 512x512 opaque 8-bit RGB PNG')
sfo = stage/'sce_sys/param.sfo'
sfo.unlink(missing_ok=True)
with (out/'sfo.log').open('w') as log:
    def pkgtool(*args):
        subprocess.run([str(tool), *map(str, args)], check=True, stdout=log, stderr=subprocess.STDOUT)
    pkgtool('sfo_new', sfo)
    for key, value in {'APP_TYPE':1, 'ATTRIBUTE':0, 'DOWNLOAD_DATA_SIZE':0, 'SYSTEM_VER':0}.items():
        pkgtool('sfo_setentry', sfo, key, '--type', 'Integer', '--maxsize', 4, '--value', value)
    for key, size, value in [('APP_VER',8,version), ('VERSION',8,version), ('CATEGORY',4,'gd'),
                             ('CONTENT_ID',48,content_id), ('TITLE_ID',12,title_id),
                             ('TITLE',128,f'Serious Sam {label} - PS4 Alpha {release}')]:
        pkgtool('sfo_setentry', sfo, key, '--type', 'Utf8', '--maxsize', size, '--value', value)
files.add('sce_sys/param.sfo')
subprocess.run([str(sdk/'bin/linux/create-gp4'), '-out', 'pkg.gp4', '--content-id='+content_id,
                '--files', 'eboot.bin sce_sys/param.sfo sce_sys/icon0.png'], cwd=stage, check=True)
project = stage/'pkg.gp4'
tree = ET.parse(project)
entries = tree.getroot().find('files')
entries.clear()
entries.set('img_no', '0')
directories = tree.getroot().find('rootdir')
directories.clear()
for name in sorted(files):
    ET.SubElement(entries, 'file', targ_path=name, orig_path=name)
    node = directories
    for part in PurePosixPath(name).parts[:-1]:
        child = next((item for item in node if item.get('targ_name') == part), None)
        if child is None:
            child = ET.SubElement(node, 'dir', targ_name=part)
        node = child
ET.indent(tree)
tree.write(project, encoding='utf-8', xml_declaration=True)
with (out/'build.log').open('w') as log:
    subprocess.run([str(tool), 'pkg_build', 'pkg.gp4', '.'], cwd=stage,
                   stdout=log, stderr=subprocess.STDOUT, check=True)
package = dist/f'SeriousSam-{label}-PS4-Alpha-{release}-external.pkg'
partial = package.with_suffix('.pkg.partial')
subprocess.run(['cp', '--reflink=auto', '--', str(stage/(content_id+'.pkg')), str(partial)], check=True)
with (out/'validate.log').open('w') as log:
    subprocess.run([str(tool), 'pkg_validate', '--verbose', str(partial)],
                   stdout=log, stderr=subprocess.STDOUT, check=True)
validation = (out/'validate.log').read_text()
if '[OK]' not in validation or re.search(r'\b(FAIL|FAILED|ERROR)\b', validation, re.I):
    raise SystemExit('Package validation failed; inspect artifacts/package/validate.log')
partial.replace(package)
info.update(package=str(package), sha256=digest(package), bytes=package.stat().st_size,
            title_id=title_id, version=version, files={name:digest(stage/name) for name in sorted(files)})
(out/'manifest.json').write_text(json.dumps(info, indent=2)+'\n')
package.with_suffix('.pkg.sha256').write_text(f'{info["sha256"]}  {package.name}\n')
print(f'Local package: {package}\nSHA-256: {info["sha256"]}')
