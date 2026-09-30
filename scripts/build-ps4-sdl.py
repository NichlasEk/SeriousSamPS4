#!/usr/bin/env python3
"""Enable SDL's dummy video backend; the native Vulkan driver owns VideoOut."""
from pathlib import Path
import os
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
sdk = Path(os.environ.get('OO_PS4_TOOLCHAIN', '/opt/openorbis/OpenOrbis/PS4Toolchain'))
source = root / '.tools/SDL-PS4'
revision = '7774cf3e7d04448c44d569c50d1f9a4532a2efe7'
if not source.exists():
    subprocess.run(['git', 'clone', 'https://github.com/OpenOrbis/SDL-PS4.git', str(source)], check=True)
build = root / 'build/ps4-sdl'
tree = build / 'source'
tree.mkdir(parents=True, exist_ok=True)
archive = subprocess.check_output(['git', '-C', str(source), 'archive', revision])
subprocess.run(['tar', '-x', '-C', str(tree)], input=archive, check=True)
objects = []
for relative in ['src/video/SDL_video.c', 'src/video/dummy/SDL_nullvideo.c',
                 'src/video/dummy/SDL_nullevents.c', 'src/video/dummy/SDL_nullframebuffer.c']:
    obj = build / (Path(relative).name + '.o')
    subprocess.run(['clang', '--target=x86_64-pc-freebsd12-elf', '-fPIC', '-O2',
                    '-D__PS4__', '-D__ORBIS__', '-DSDL_VIDEO_DRIVER_DUMMY=1',
                    '-isysroot', str(sdk), '-isystem', str(sdk/'include'),
                    '-I'+str(tree/'include'), '-I'+str(tree/'src'),
                    '-c', str(tree/relative), '-o', str(obj)], check=True)
    objects.append(str(obj))
lib = build/'libSDL2.a'
shutil.copyfile(sdk/'lib/libSDL2.a', lib)
subprocess.run(['llvm-ar', 'r', str(lib), *objects], check=True)
print(lib)
