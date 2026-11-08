#!/usr/bin/env python3
"""Prepare exact external-data PKGs, upstream support data and source/relink kit."""
import hashlib, json, os, shlex, shutil, subprocess, tarfile, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('OO_PS4_TOOLCHAIN', '/opt/openorbis/OpenOrbis/PS4Toolchain'))
STACK = Path(os.environ.get('SS_NATIVE_STACK', ROOT.parent/'Doom3-Ps4/build/native'))
RELEASE = ROOT/'dist/release-alpha-tfe-0.04-tse-0.02'
EXPECTED = {'tfe':'62737b774cccae8e028cad9dc406b79f18402b0f62a14895c6f90afc433fa27b',
            'tse':'7a0efe4b4a04ed9d7cbec574df8faa3043d749f5251563ca7ec57ffcc4595dfa'}
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    RELEASE.mkdir(exist_ok=True)
    kit=Path(tempfile.mkdtemp(prefix='release-source-',dir=ROOT/'build'))
    def copy(src,dest):
        target=kit/dest; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,target); return str(dest)
    excluded={'.o','.a','.so','.dll','.exe','.pdb','.obj','.lib','.pyc','.d','.log','.gro','.pkg','.iso','.b6i','.b6t','.key','.pem'}
    def snapshot(src,dest):
        count=0
        for p in sorted(src.rglob('*')):
            rel=p.relative_to(src)
            if any(n in {'.git','build','__pycache__','.cache','node_modules'} for n in rel.parts): continue
            if not p.is_file() or p.is_symlink() or p.suffix.lower() in excluded or p.name.startswith('.env'): continue
            raw=p.read_bytes()
            # Sources, codegen inputs and shader binaries are retained, never executables.
            if raw.startswith((b'\x7fELF',b'MZ')): continue
            copy(p,Path(dest)/rel); count+=1
        return count
    sources={
      'engine/SamTFE/Sources':ROOT/'build/ps4-source/SamTFE/Sources',
      'engine/SamTSE/Sources':ROOT/'build/ps4-source/SamTSE/Sources',
      'SDL-PS4':ROOT/'build/ps4-sdl/source',
      'ps4-libjbc-adapted':ROOT/'build/ps4-usb',
      'opengnm':STACK/'opengnm','opengnm-psbc':STACK/'opengnm-psbc',
      'vulkan-ps4':STACK/'vulkan-ps4','Vulkan-Headers':STACK/'Vulkan-Headers',
      'SPIRV-Headers':STACK/'SPIRV-Headers','openorbis-modules':SDK/'src/modules'}
    counts={name:snapshot(src,'sources/'+name) for name,src in sources.items()}
    for name in ['platform','patches','cmake','scripts','docs','tests']:
        snapshot(ROOT/name,'port/'+name)
    snapshot(ROOT.parent/'Doom3-Ps4/thirdparty/ps4-native','graphics-build/thirdparty/ps4-native')
    copy(ROOT.parent/'Doom3-Ps4/scripts/build-native-vulkan.sh','graphics-build/scripts/build-native-vulkan.sh')
    for src,dest in [(ROOT/'engine-vk/LICENSE','licenses/SeriousEngine-GPLv2'),
                     (ROOT/'engine-vk/README.md','licenses/engine-upstream-README.md'),
                     (SDK/'LICENSE','licenses/OpenOrbis-LICENSE'),
                     (ROOT/'.tools/SDL-PS4/COPYING.txt','licenses/SDL-COPYING.txt'),
                     (ROOT/'docs/THIRD-PARTY.md','THIRD-PARTY.md')]: copy(src,dest)
    builds={}
    for game,tree in [('tfe','SamTFE'),('tse','SamTSE')]:
        m=json.loads((ROOT/f'artifacts/package-{game}-external/manifest.json').read_text())
        pkg=Path(m['package']); build=ROOT/f'build/ps4-{game}'
        assert sha(pkg)==EXPECTED[game]==m['sha256'] and not m['contains_owned_retail_data']
        assert sha(build/'SeriousSam')==m['engine_elf_sha256']
        shutil.copyfile(pkg,RELEASE/pkg.name)
        command=subprocess.check_output(['ninja','-C',str(build),'-t','commands','SeriousSam' if game=='tfe' else 'SeriousSamMP'],text=True).splitlines()[-1]
        args=shlex.split(command)
        assert args[:2]==[':','&&'] and args[-2:]==['&&',':']
        args=args[2:-2]; args[0]='clang++'; rewritten=[]; number=0
        for arg in args:
            p=Path(arg)
            if arg.endswith(('.o','.a')) and not str(p).startswith(str(SDK)):
                src=p if p.is_absolute() else build/p
                if arg.endswith('.o'):
                    number+=1; dest=f'link/{game}/objects/{number:04d}-{p.name}'
                else: dest=f'link/{game}/libraries/{p.name}'
                arg=copy(src,dest)
            elif arg=='SeriousSam': arg=f'{game}-relinked.elf'
            rewritten.append(arg.replace(str(SDK),'@SDK@'))
        (kit/f'link/{game}/arguments.json').write_text(json.dumps(rewritten,indent=2)+'\n')
        copy(build/'static_exports.cpp',f'generated/{game}/static_exports.cpp')
        builds[game]={'package_sha256':m['sha256'],'elf_sha256':m['engine_elf_sha256']}
    (kit/'BUILD.json').write_text(json.dumps({'builds':builds,'source_files':counts},indent=2)+'\n')
    copy(ROOT/'scripts/relink-release.py','relink.py')
    (kit/'README.md').write_text('''# Serious Sam PS4 source/relink companion

Patched engine, graphics, SDL and USB sources, port build recipes, and original
link inputs accompany the two exact release packages. No retail game data.
See port/docs/THIRD-PARTY.md for independent dependency notices.

With clang/lld and an installed OpenOrbis SDK (OO_PS4_TOOLCHAIN), run:

    python3 relink.py --game tfe --verify
    python3 relink.py --game tse --verify

These commands verify exact original ELF hashes. Sources are supplied in their
adapted build state, alongside patches and original recipes. The port recipe
expects the pinned upstream engine clone; see port/docs/EXTERNAL-DATA.md.
The graphics recipe is under graphics-build/. Full clean SDK reconstruction
has not been verified. This is not a claim that every dependency shares GPLv2.
''')
    for game in builds:
        subprocess.run(['python3',str(kit/'relink.py'),'--game',game,'--verify'],check=True)
        (kit/f'{game}-relinked.elf').unlink()
    inventory={p.relative_to(kit).as_posix():sha(p) for p in sorted(kit.rglob('*')) if p.is_file()}
    (kit/'FILES.json').write_text(json.dumps(inventory,indent=2)+'\n')
    with tarfile.open(RELEASE/'SeriousSam-PS4-source-relink.tar.gz','w:gz') as tar:
        tar.add(kit,arcname='SeriousSam-PS4-source-relink')
    with zipfile.ZipFile(RELEASE/'SeriousSam-PS4-support-data.zip','w',zipfile.ZIP_DEFLATED) as z:
        for tree,folder in [('SamTFE','serioussam-game'),('SamTSE','serioussamse-game')]:
            base=ROOT/'engine-vk'/tree
            for name in ['Controls','Data','Demos','Help','Players','Scripts','SE1_10b.gro','ModEXT.txt']:
                item=base/name
                for p in sorted(item.rglob('*')) if item.is_dir() else [item]:
                    if p.is_file(): z.write(p,folder+'/'+str(p.relative_to(base)))
            z.writestr(folder+'/Bin/','')
        z.write(ROOT/'engine-vk/LICENSE','LICENSE-engine.txt')
        z.write(ROOT/'engine-vk/README.md','README-upstream.md')
    for src,dest in [('INSTALL-ALPHA.md','INSTALL.md'),('THIRD-PARTY.md','THIRD-PARTY.md'),('RELEASE-ALPHA.md','RELEASE-NOTES.md')]:
        shutil.copyfile(ROOT/'docs'/src,RELEASE/dest)
    for name in ['tfe-0.04-shadps4.png','tse-0.02-shadps4.png']:
        shutil.copyfile(ROOT/'docs/screenshots'/name, RELEASE/name)
    (RELEASE/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(RELEASE.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
    print(json.dumps({'kit':str(kit),'release':str(RELEASE),'source_files':len(inventory)},indent=2))
if __name__=='__main__': main()
