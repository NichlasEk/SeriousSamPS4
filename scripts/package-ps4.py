#!/usr/bin/env python3
"""Package the built TFE alpha with the user's local data for console testing."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
sdk = Path(os.environ.get('OO_PS4_TOOLCHAIN', '/opt/openorbis/OpenOrbis/PS4Toolchain'))
stack = Path(os.environ.get('SS_NATIVE_STACK', '/home/nichlas/Doom3-Ps4/build/native'))
runtime = root/'build/runtime-tfe'
stage = root/'build/package-tfe'
dist = root/'dist'
out = root/'artifacts/package'
for directory in [stage/'sce_sys', dist, out]:
    directory.mkdir(parents=True, exist_ok=True)
tool = sdk/'bin/linux/PkgTool.Core'
title_id = 'SSAM00001'
content_id = 'IV0000-SSAM00001_00-SERIOUSSAMTFE001'
assert re.fullmatch(r'[A-Z]{2}[0-9]{4}-'+title_id+r'_[0-9]{2}-[A-Z0-9]{16}', content_id)
elf = root/'build/ps4-tfe/SeriousSam'
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
for name in ['eboot.bin', 'Controls', 'Data', 'Demos', 'Help', 'Players', 'Scripts',
             'SE1_10b.gro', 'ModEXT.txt', '1_00.gro', '1_00_music.gro', 'Levels']:
    source = (runtime/name).resolve(strict=True)
    if source.is_dir():
        for entry in sorted(source.rglob('*')):
            if entry.is_file():
                copy(entry, str(PurePosixPath(name)/entry.relative_to(source).as_posix()))
    else:
        copy(source, name)
for source, name in [(root/'engine-vk/LICENSE', 'SeriousEngine-LICENSE'),
                     (stack/'opengnm/LICENSE', 'OpenGNM-LICENSE'),
                     (stack/'opengnm-psbc/LICENSE', 'PSBC-LICENSE'),
                     (stack/'vulkan-ps4/LICENSE', 'Vulkan-PS4-LICENSE'),
                     (root/'.tools/SDL-PS4/COPYING.txt', 'SDL-LICENSE'),
                     (root/'engine-vk/SamTFE/Sources/External/libvorbis/COPYING', 'Vorbis-LICENSE'),
                     (root/'engine-vk/SamTFE/Sources/External/libogg/COPYING', 'Ogg-LICENSE')]:
    copy(source, 'notices/'+name)
info = {'candidate': 'Serious Sam TFE PS4 Alpha 0.01', 'eboot_sha256': digest(runtime/'eboot.bin'),
        'engine_elf_sha256': digest(elf), 'contains_owned_retail_data': True,
        'physical_ps4_tested': False, 'extra_runtime_modules': []}
(out/'build-info.json').write_text(json.dumps(info, indent=2)+'\n')
copy(out/'build-info.json', 'build-info.json')
subprocess.run(['magick', '-background', '#171719', str(root/'assets/icon0.svg'),
                '-alpha', 'off', '-depth', '8', 'PNG24:'+str(stage/'sce_sys/icon0.png')], check=True)
files.add('sce_sys/icon0.png')
sfo = stage/'sce_sys/param.sfo'
sfo.unlink(missing_ok=True)
with (out/'sfo.log').open('w') as log:
    def pkgtool(*args):
        subprocess.run([str(tool), *map(str, args)], check=True, stdout=log, stderr=subprocess.STDOUT)
    pkgtool('sfo_new', sfo)
    for key, value in {'APP_TYPE':1, 'ATTRIBUTE':0, 'DOWNLOAD_DATA_SIZE':0, 'SYSTEM_VER':0}.items():
        pkgtool('sfo_setentry', sfo, key, '--type', 'Integer', '--maxsize', 4, '--value', value)
    for key, size, value in [('APP_VER',8,'00.01'), ('VERSION',8,'00.01'), ('CATEGORY',4,'gd'),
                             ('CONTENT_ID',48,content_id), ('TITLE_ID',12,title_id),
                             ('TITLE',128,'Serious Sam TFE - PS4 Alpha 0.01')]:
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
package = dist/'SeriousSam-TFE-PS4-Alpha-0.01-local.pkg'
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
            title_id=title_id, version='00.01', files={name:digest(stage/name) for name in sorted(files)})
(out/'manifest.json').write_text(json.dumps(info, indent=2)+'\n')
package.with_suffix('.pkg.sha256').write_text(f'{info["sha256"]}  {package.name}\n')
print(f'Local package: {package}\nSHA-256: {info["sha256"]}')
