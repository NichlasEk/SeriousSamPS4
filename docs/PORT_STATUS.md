# Serious Sam PS4 port status

Updated 2026-09-30. Initial First Encounter OpenOrbis client built and booted in shadPS4; this is an early graphics bring-up, not a finished console port.

## Source and game data

- `engine/` pins Croteam's original Serious Engine 1.10. Its published build instructions use Visual Studio.
- `engine-vk/` pins the Linux/SDL2/Vulkan fork used for the desktop baseline. It builds separate First Encounter and Second Encounter executables. Changes for PS4 should remain traceable against this upstream.
- The two supplied discs are MODE2/2352 BIN/CUE pairs, despite being described as ISOs. `scripts/extract_discs.py` converts and extracts them without changing the originals. All images and game files are under ignored `media/`.
- First Encounter has `Install/1_00.gro` plus loose `Install/Levels/*.wld`. Second Encounter has `Install/SE1_00*.gro`, including `SE1_00_Levels.gro`. All 11 `.gro` files from the two discs passed `7z t`.

## Desktop baseline

The pinned Vulkan fork compiled on the Linux host with CMake/Ninja, `USE_ASM=OFF`, and system SDL2, zlib and Vulkan. Both executables started inside `xvfb-run` with the retail archives staged locally and `SDL_AUDIODRIVER=dummy`.

The First Encounter log reports a Vulkan context on the host RTX 4090 and a started `Levels/Intro.wld` session after staging the loose `Install/Levels` directory. The Second Encounter log likewise reports a Vulkan context and a started `Levels/LevelsMP/Intro.wld` session. Each process was stopped by a 15-second timeout. This verifies startup and intro-level loading on Linux; it does not establish visible gameplay, correct rendering, audio, or PS4 behavior.

## PS4 implementation

`patches/001-openorbis-tfe.patch` applies to `engine-vk` revision `510d36f901cbe883c56b155b53717e4efdeb6522`. The build applies it to an ignored working copy; the source submodules stay pristine. This patch is specifically for the TFE PS4 build, not a general desktop patch.

- Cross-compiles Engine, Game, Entities and Shaders as static archives using OpenOrbis, then links a single client. A generated symbol table replaces the desktop DLL loader.
- Uses the existing source-built Vulkan/OpenGNM driver and shader compiler from Doom3-Ps4. The fixed VideoOut mode is 1280x720 with D32/S8 depth and single-sample rendering.
- Packs four texture bindings into descriptor set 1; the uniform buffer uses set 0. Fragment shaders are rebuilt with `glslc` and validated with `spirv-val`.
- Adds upstream SDL's dummy video backend to a private copy of the SDK SDL archive. This leaves VideoOut owned by the native Vulkan driver. Desktop relative-mouse capture is disabled.
- Uses the engine's single-thread timer mode. Game content is read from `/app0`; user data and diagnostics use `/data/serioussam`.
- Audio is disabled for this milestone. Dynamically loaded Vorbis/MP3 libraries are not linked yet.

### Build prerequisites

Host tools: Git, CMake, Ninja, Clang/LLD, LLVM archive tools, Python 3, Flex, Bison, `glslc`, `spirv-val`, and desktop SDL2 development files for configuring the host entity compiler. The emulator runner additionally needs `xvfb-run` and ImageMagick `import`.

Default local paths (overridable through environment variables):

| Variable | Default / requirement |
| --- | --- |
| `OO_PS4_TOOLCHAIN` | `/opt/openorbis/OpenOrbis/PS4Toolchain` |
| `SS_NATIVE_STACK` | `/home/nichlas/Doom3-Ps4/build/native` |
| `CREATE_FSELF` | `/home/nichlas/ut99-orbis/build/create-fself-current` |
| `SHADPS4` | `/home/nichlas/ScummVM-PS4/.tools/shadps4/Shadps4-sdl.AppImage` |
| `BUILD_JOBS` | `8` |

The native stack must contain `vulkan-ps4/libvulkan_ps4.a`, `opengnm/libopengnm.a`, `libpsbc-private.a` and `Vulkan-Headers/include`. Plain upstream archives are insufficient: Doom3's patches include shader push-constant lowering and private shader-compiler thread symbols. The inspected Doom3 checkout is clean at `300695a50cabe875a048ed3d11ea9e6f4a9c8a17`; its `scripts/build-native-vulkan.sh` records the source pins and builds the dependencies. Serious Sam's build reads those archives without modifying them. A standalone native-stack build inside this repository remains future work.

SDL source for the private video backend is pinned to OpenOrbis/SDL-PS4 `7774cf3e7d04448c44d569c50d1f9a4532a2efe7`.

```sh
bash scripts/build-ps4.sh
python3 scripts/run-ps4.py --seconds 180
```

Outputs:

- `build/ps4-tfe/SeriousSam`: linked OpenOrbis ELF.
- `build/runtime-tfe/eboot.bin`: converted PS4 executable with locally staged TFE resources.
- `artifacts/ps4/`: build logs, input/output SHA-256 records, emulator log, screenshot and `run.json`.
- `build/emulator-profile/shadPS4/data/serioussam/`: engine and native graphics logs.

The runtime stage uses symlinks to the local retail archives and loose `Levels` directory. It is for local emulator testing, not a portable package tree. No retail assets are committed.

## Validation and remaining work

Confirmed so far:

- OpenOrbis compilation and static link, executable conversion, and a complete scripted build from a fresh source/build directory (513 Ninja steps). The fresh build reproduced the same `eboot.bin` SHA-256: `ff1962896e1fbc2b2205e82502b5f62eb3e1b08923170ce139c113cf71750dc2`.
- shadPS4 boot into the actual game engine, native PS4 Vulkan context creation, loading the retail intro level and adding its player.
- Captured Croteam and GODGames logos rendered through the native graphics stack. The final 180-second run reached frame 8,424, remained alive until capture, and was stopped by the runner. Its inspected screenshot shows the textured 3D intro: Egyptian temple, obelisks, statue, palms, sky and particle effects. This verifies visible 3D output, not full scene correctness or controller gameplay.

The runner's successful timeout only demonstrates that the process remained alive until capture. It does not establish rendering correctness or playability. Screenshots and engine/native-driver logs must be checked together.

Next gates:

1. Validate a playable level beyond the now-visible 3D intro, including depth, textures and timing.
2. Implement and test DualShock navigation, movement and aiming; desktop mouse capture is currently disabled.
3. Restore audio and statically link the required codecs.
4. Produce a local installable PKG, then test on the physical PS4. No physical-console test has been performed.
5. Carry the working platform changes to Second Encounter, which is not yet cross-built.

Resolved bring-up failures: SDL timer-thread startup crash (single-thread engine mode), competing SDL/native VideoOut handles (dummy SDL window), unsupported D24 depth format (D32/S8), and SDL relative-mouse warp assertion (disabled desktop capture).
