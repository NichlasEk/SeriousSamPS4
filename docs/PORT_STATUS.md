# Serious Sam PS4 port status

Updated 2026-09-30. First Encounter alpha now includes native controller input, statically linked audio codecs, and a local console package. Physical-console validation remains outstanding.

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
- Native ScePad events feed the existing engine controls. Left-stick movement currently uses digital thresholds; right-stick aiming uses a deadzone and elapsed-time scaling. Disconnects release held keys. Menu/game context selects the appropriate button bindings.
- SDL uses a private PS4 kernel semaphore adapter for thread startup; SDK POSIX semaphore stubs and the generic SDL condition-variable workaround were unsuitable. The SDK installation is unchanged.
- Bundled Ogg/Vorbis and amp11lib decoders are linked statically and exposed through the module resolver. The engine mixes 44.1 kHz stereo and SDL resamples to the PS4 AudioOut device at 48 kHz.

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

The runtime stage uses symlinks to the local retail archives and loose `Levels` directory. It is for local emulator testing, not a portable package tree. No retail assets are committed. `scripts/package-ps4.py` copies the local data into a self-contained, ignored PKG for personal console testing.

## Validation and remaining work

Initial graphics checkpoint (`0b54cdf`):

- OpenOrbis compilation and static link, executable conversion, and a complete scripted build from a fresh source/build directory (513 Ninja steps). The fresh build reproduced the same `eboot.bin` SHA-256: `ff1962896e1fbc2b2205e82502b5f62eb3e1b08923170ce139c113cf71750dc2`.
- shadPS4 boot into the actual game engine, native PS4 Vulkan context creation, loading the retail intro level and adding its player.
- Captured Croteam and GODGames logos rendered through the native graphics stack. The final 180-second run reached frame 8,424, remained alive until capture, and was stopped by the runner. Its inspected screenshot shows the textured 3D intro: Egyptian temple, obelisks, statue, palms, sky and particle effects. This verifies visible 3D output, not full scene correctness or controller gameplay.

The runner's successful timeout only demonstrates that the process remained alive until capture. It does not establish rendering correctness or playability. Screenshots and engine/native-driver logs must be checked together.

## Alpha 0.01 checkpoint

The final 130-second shadPS4 run used `build/package-tfe-extracted/uroot/eboot.bin`, not the development staging tree. It survived until the runner stopped it and reached frame 5,354. Verified evidence:

- Navigated the menus via emulated ScePad and started `Levels/01_Hatshepsut.wld` on Normal; the engine created a quicksave.
- Closed NETRICSA and displayed the first-person pistol, crosshair and HUD. `game-before.png` shows the start platform; `game-moved.png` shows the player further up the ramp; `game-turned.png` shows a changed heading after right-stick input.
- `PS4 ACTION` records forward movement changing from `0` to `-10` and back, and the fire bit changing from `0` to `1` and back. The test then opened the pause menu (`game-paused.png`). Enemy combat, complete levels and save reloads are not yet validated.
- The isolated audio capture contains 5,867,287 nonzero 16-bit samples, peak 18,005, RMS approximately 1,302 over 134.144 seconds. This confirms actual host audio output from the emulated AudioOut path, without claiming subjective quality or console output.
- PkgTool validation passed. Extraction checked 203 files; application SFO fields were preserved. No PRX/SPRX files are present.

Artifacts are under ignored `artifacts/ps4/` and `artifacts/package/`. The exact tested executable SHA-256 is `1e3e34fc21bb7330e3f9f164e59b49ae0e65ebb6a879eae18b062fbd229a0c1b`; the local package SHA-256 is `eeae5814f6016eb539d2304e97869dab7e99b2431e19b41ee59dc67d8eb56c0c` (395,837,440 bytes). Repackaging may change the package hash because of metadata timestamps.

Resolved this step: semaphore/thread-start synchronization, right-stick motion being overwritten by desktop mouse polling, and incorrect bracket scancodes for weapon cycling. The original SDK SDL library remains untouched.

## Controls

| DualShock input | Action |
| --- | --- |
| D-pad / left stick in menus | Navigate |
| Cross in menus | Select |
| Circle in menus / Options | Back / menu / resume |
| Left stick in game | Move and strafe (digital threshold for now) |
| Right stick in game | Aim |
| Cross / Circle in game | Jump / crouch |
| R2 / L2 | Fire / use or NETRICSA |
| Square | Reload |
| L1 / R1 | Previous / next weapon |
| Triangle | Third-person view |

These bindings use the supplied default control profile. Remapping engine keyboard bindings also changes the corresponding pad actions. Menus currently navigate one item per press, with no held-direction repeat.

## Reproduce controller/audio tests

```sh
python3 scripts/record-ps4-audio.py --seconds 130 --actions scripts/tests/ps4-gameplay.json
```

The timed input script enters a Normal single-player game, skips introductory cameras with fire, moves, turns, fires and opens the pause menu. It sends XTest keyboard events to the isolated shadPS4 display, which shadPS4 translates to ScePad; it does not inject actions directly into the game. The host additionally needs X11/XTest libraries, PulseAudio-compatible `pactl`/`parec`, and an active audio server.

The recorder creates a temporary private sink, routes only the launched emulator PID's audio streams into it, and removes the sink afterward. `audio.wav` and `audio.json` report the captured signal. Signal presence does not establish perceptual quality or physical PS4 output. Timed actions are evidence only when the corresponding screenshots and `PS4 INPUT` / `PS4 ACTION` logs confirm their effects.

## Local console package

```sh
python3 scripts/package-ps4.py
python3 scripts/verify-ps4-package.py
python3 scripts/run-ps4.py --eboot build/package-tfe-extracted/uroot/eboot.bin --seconds 130 --actions scripts/tests/ps4-gameplay.json
```

- Output: `dist/SeriousSam-TFE-PS4-Alpha-0.01-local.pkg`, title ID `SSAM00001`.
- The package includes the locally supplied retail data. Keep this artifact local; the public repository contains source, patches and scripts only.
- No additional PRX/SPRX modules are bundled. The executable imports the system kernel, GNM, Pad, UserService, AudioOut, VideoOut and Net libraries.
- Package structure/signature validation and extracted file/SFO verification are separate from launching the extracted executable and from physical PS4 testing.
- Saves and logs use `/data/serioussam`. This alpha bundles its assets under `/app0`; no USB game-data path is implemented.

First physical test: install the local PKG through the console's existing homebrew package installer, launch **Serious Sam TFE - PS4 Alpha 0.01**, press Options to leave the attract intro, then choose Single Player → New Game → Normal with Cross. R2 skips the opening cameras; Options closes NETRICSA. Check movement, aiming, firing, pause/resume and sound. Record any crash screen and retain `/data/serioussam/SeriousSam.log` and `vulkan.log` if accessible. This procedure has not yet been performed on hardware.

Next gates: physical PS4 launch and controls/audio, longer gameplay with saves and level changes, performance and render-correctness review, and carrying the platform changes to Second Encounter. TSE is not yet cross-built. The native graphics stack still depends on the documented Doom3 checkout.
