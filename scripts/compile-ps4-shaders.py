#!/usr/bin/env python3
"""Compile the PS4 descriptor layout into the engine's embedded SPIR-V."""
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]) / 'Engine/Graphics/Vulkan/Shaders'
for filename, name in [('Textured.frag', 'TexturedFrag'), ('TexturedAlpha.frag', 'TexturedAlphaFrag')]:
    binary = source/'CompiledSpirv'/(name+'.spv')
    subprocess.run(['glslc', '--target-env=vulkan1.1', str(source/filename), '-o', str(binary)], check=True)
    subprocess.run(['spirv-val', '--target-env', 'vulkan1.1', str(binary)], check=True)
    data = binary.read_bytes()
    header = f'alignas(4) unsigned char {name}_Spirv[] = {{' + ','.join(map(str, data)) + '};\n'
    header += f'unsigned int {name}_Size = {len(data)};\n'
    (source/'Compiled'/(name+'Spv.h')).write_text(header)
