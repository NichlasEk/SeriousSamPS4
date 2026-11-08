# Serious Sam PS4 port status

2026-11-08: external-data TFE 0.04 / TSE 0.02 candidates now use HDD-first,
USB-fallback discovery. See [installation and checks](EXTERNAL-DATA.md).
The older results below describe previous builds; physical acceptance of the
external-data candidates remains pending.

Updated 2026-09-30. First Encounter 0.02 is confirmed running on physical PS4 with smooth gameplay and slower cinematics. First Encounter 0.03 adds controller functions; Second Encounter 0.01 now builds and runs in shadPS4. Hardware validation of the new builds is pending.

## Source and game data

- `engine/` pins Croteam's original Serious Engine 1.10. Its published build instructions use Visual Studio.
- `engine-vk/` pins the Linux/SDL2/Vulkan fork used for the desktop baseline. It builds separate First Encounter and Second Encounter executables. Changes for PS4 should remain traceable against this upstream.
- The two supplied discs are MODE2/2352 BIN/CUE pairs, despite being described as ISOs. `scripts/extract_discs.py` converts and extracts them without changing the originals. All images and game files are under ignored `media/`.
- First Encounter has `Install/1_00.gro` plus loose `Install/Levels/*.wld`. Second Encounter has `Install/SE1_00*.gro`, including `SE1_00_Levels.gro`. All 11 `.gro` files from the two discs passed `7z t`.

## Desktop baseline

The pinned Vulkan fork compiled on the Linux host with CMake/Ninja, `USE_ASM=OFF`, and system SDL2, zlib and Vulkan. Both executables started inside `xvfb-run` with the retail archives staged locally and `SDL_AUDIODRIVER=dummy`.

The First Encounter log reports a Vulkan context on the host RTX 4090 and a started `Levels/Intro.wld` session after staging the loose `Install/Levels` directory. The Second Encounter log likewise reports a Vulkan context and a started `Levels/LevelsMP/Intro.wld` session. Each process was stopped by a 15-second timeout. This verifies startup and intro-level loading on Linux; it does not establish visible gameplay, correct rendering, audio, or PS4 behavior.

## PS4 implementation

`patches/001-openorbis-tfe.patch` applies to `engine-vk` revision `510d36f901cbe883c56b155b53717e4efdeb6522`. The build applies it to an ignored working copy; the source submodules stay pristine. `002-openorbis-tse.patch` carries the corresponding changes for SamTSE at the same pin, with its own `/data/serioussamse` directory. Both patches are PS4-specific.

- Cross-compiles Engine, Game, Entities and Shaders as static archives using OpenOrbis, then links a single client. A generated symbol table replaces the desktop DLL loader.
- Uses the existing source-built Vulkan/OpenGNM driver and shader compiler from Doom3-Ps4. The fixed VideoOut mode is 1280x720 with D32/S8 depth and single-sample rendering.
- Packs four texture bindings into descriptor set 1; the uniform buffer uses set 0. Fragment shaders are rebuilt with `glslc` and validated with `spirv-val`.
- Adds upstream SDL's dummy video backend to a private copy of the SDK SDL archive. This leaves VideoOut owned by the native Vulkan driver. Desktop relative-mouse capture is disabled.
- Uses the engine's single-thread timer mode. Game content is read from `/app0`; user data and diagnostics use `/data/serioussam` (TFE) or `/data/serioussamse` (TSE).
- Native ScePad events feed the existing engine controls. Left-stick movement currently uses digital thresholds; right-stick aiming uses a deadzone and elapsed-time scaling. Disconnects release held keys. Menu/game context selects the appropriate button bindings.
- SDL uses a private PS4 kernel semaphore adapter for thread startup; SDK POSIX semaphore stubs and the generic SDL condition-variable workaround were unsuitable. The SDK installation is unchanged.
- Bundled Ogg/Vorbis and amp11lib decoders are linked statically and exposed through the module resolver. The engine mixes 44.1 kHz stereo and SDL resamples to the PS4 AudioOut device at 48 kHz.

### Build prerequisites

Host tools: Git, CMake, Ninja, Clang/LLD, LLVM archive tools, Python 3, Flex, Bison, `glslc`, `spirv-val`, and desktop SDL2 development files for configuring the host entity compiler. The emulator runner additionally needs `Xvfb` and ImageMagick `import`.

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
| Touchpad click | Quick save (gameplay only) |
| Hold L3 | Walk |
| D-pad up/down in TSE gameplay | Sniper zoom in/out |
| R3 in TSE gameplay | Serious Bomb |

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

- Output: `dist/SeriousSam-TFE-PS4-Alpha-0.03-local.pkg`, title ID `SSAM00001`.
- The package includes the locally supplied retail data. Keep this artifact local; the public repository contains source, patches and scripts only.
- Alpha 0.02 includes the open SDK support files `sce_module/libc.prx`, `sce_module/libSceFios2.prx`, and `sce_sys/about/right.sprx`, byte-matched to the Doom 3 0.06 package. The executable imports the system kernel, GNM, Pad, UserService, AudioOut, VideoOut and Net libraries.
- Package structure/signature validation and extracted file/SFO verification are separate from launching the extracted executable and from physical PS4 testing.
- Saves and logs use `/data/serioussam`. This alpha bundles its assets under `/app0`; no USB game-data path is implemented.

Next physical test: install the local PKG through the console's existing homebrew package installer, launch **Serious Sam TFE - PS4 Alpha 0.03**, press Options to leave the attract intro, then choose Single Player → New Game → Normal with Cross. R2 skips the opening cameras; Options closes NETRICSA. Check movement, aiming, firing, pause/resume and sound. Record any crash screen and retain `/data/serioussam/SeriousSam.log` and `vulkan.log` if accessible. Alpha 0.02 subsequently passed the user's physical launch/gameplay test. Repeat with 0.03 to check its added controls.

Next gates: physical PS4 launch and controls/audio, longer gameplay with saves and level changes, performance and render-correctness review, and complete campaign progression. Second Encounter is now cross-built; see the later checkpoint below. The native graphics stack still depends on the documented Doom3 checkout.

## Alpha 0.02 package correction

The user reports that 0.01 installs but the PS4 reports corrupt data afterward.
The user confirms the message only mentioned corrupt files, without a numerical error code. The exact point of failure relative to any game image remains unconfirmed. Previous
PkgTool validation and emulator gameplay did not establish console launch.

The 0.01 recipe incorrectly excluded all PRX/SPRX support files based on static
linking and the executable import list. OpenOrbis explicitly documents its
[`libc` and `libSceFios2` stub modules as needed in packages](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/blob/master/src/README.md).
The working Doom 3 0.06 package also includes these two files plus the OpenOrbis
`right.sprx` shell attribution module. All three local SDK copies match the
extracted Doom 3 0.06 files byte for byte.

0.02 restores these files and increments the displayed version, keeping the
application identity, executable and game resources. The verifier now requires
exactly these three support modules and checks independently pinned SHA-256
values. This fixes a documented packaging omission. The subsequent user report below confirms physical launch and gameplay with 0.02.

The 0.01 package is retained in `dist/`, with its package evidence archived in
`artifacts/package-001/`. No save data needs to be deleted for this test.

Local checks for 0.02 passed: PkgTool structure/signature validation and all 206
extracted-file/SFO checks, including the three pinned SDK modules. Executable
and game-asset hashes match 0.01; version/build metadata and the regenerated
icon differ. The icon remains a 512x512 opaque 8-bit RGB PNG. No new emulator
gameplay result is claimed for this packaging correction.

Package: `dist/SeriousSam-TFE-PS4-Alpha-0.02-local.pkg` (396,230,656 bytes).
SHA-256: `077accc0e22edc01927c40aaf78a20075208f1ce398ff6eb760e9178328f6835`.

## Physical PS4 result — Alpha 0.02

The user confirms 0.02 launches and the game runs smoothly on a physical PS4.
Video/cinematic sequences are slower; the user accepts that for now. This
confirms the corrected package can launch on that console. It does not yet
establish a complete campaign playthrough, save/reload or all weapons/levels.
The current work extends single-player validation and ports Second Encounter,
with a separate title ID and `/data/serioussamse` profile.

## First Encounter 0.03 / Second Encounter 0.01

Both builds use the same `ps4-targets.cmake`, pad adapter, SDL adapter and native
Vulkan stack. Build with `bash scripts/build-ps4.sh tfe` or `tse`; the default
remains TFE. TSE uses its own host `ecc-se` compiler and the engine's MP-named
static targets. The output executable in either build directory is `SeriousSam`.
The source submodules remain pinned and unmodified.

TSE identity is `SSAM00002`, content ID `IV0000-SSAM00002_00-SERIOUSSAMTSE001`,
with saves/logs in `/data/serioussamse`. TFE retains `SSAM00001` and
`/data/serioussam`. Both packages include the three SDK support files from the
working physical-console recipe. Their identities and pinned module hashes
are checked by `verify-ps4-package.py --game tfe|tse`.

New controls: touchpad click quick-saves during gameplay; holding L3 walks.
TSE adds D-pad up/down for sniper zoom and R3 for Serious Bomb; L2 remains
use/NETRICSA/scope. Quick load is available through Options → Quick Load.
The TSE-specific controls do not replace TFE's D-pad movement. Multiplayer
input and multiplayer sessions are not validated by this single-player port.

Package inventory confirms 15 numbered TFE campaign worlds and 13 numbered
TSE worlds (including its recap/prologue). Resources come from the supplied
local media; no retail assets or generated packages belong in Git. Inventory
evidence: `artifacts/campaign-inventory.json`.

### Validation

- First Encounter: 155-second controller run saved `QuickSave000007.sav`,
  changed view, then loaded the same file through the pause menu. Log and
  before/after screenshots under `artifacts/ps4/` show restored play.
- A separate 65-second launch of the extracted TFE package loaded that same
  save after restart (`artifacts/tfe-cold-reload/`).
- Second Encounter: 155-second run of the extracted package reached the
  opening jungle level, moved, aimed, fired, saved `QuickSave000002.sav`,
  and loaded it back through the pause menu. Evidence is under
  `artifacts/tse-package-gameplay-retry/`. Its isolated audio capture reports
  8,147,087 nonzero samples, peak 26,073, RMS 2,349 over approximately 155 seconds.
- Package validation and extracted content verification passed: 206 files
  for TFE and 190 for TSE, including SFO identity/version and SDK support files.

The runner now asks Xvfb to allocate displays atomically with `-displayfd`,
so simultaneous tests do not share an X display. Fresh isolated emulator user
directories are prepared to avoid the pinned emulator's unconditional save
migration dialog. Failed early test-tool attempts are retained under
`artifacts/levels/*/*-initial` and `*-migration`; they are not successful game
checks. These changes do not touch the user's normal emulator profiles.

Reproduce a save/reload run:

```sh
python3 scripts/record-ps4-audio.py --game tse --seconds 155 \
  --eboot build/package-tse-extracted/uroot/eboot.bin \
  --actions scripts/tests/ps4-save-reload.json --output artifacts/tse-save-check
python3 scripts/run-ps4.py --game tfe --seconds 65 \
  --eboot build/package-tfe-extracted/uroot/eboot.bin \
  --actions scripts/tests/ps4-cold-reload.json --output artifacts/tfe-cold-check
```

`test-ps4-level.py --game tse --level Levels/LevelsMP/2_1_Ziggurrat.wld`
creates a disposable runtime/profile from the extracted package and changes
only its startup script to select a campaign level. It verifies the requested
world and player started; the accompanying screenshot still needs inspection.
It refuses to overwrite earlier evidence. This does not verify traversing
level exits, bosses, or a complete campaign.

TFE package `SeriousSam-TFE-PS4-Alpha-0.03-local.pkg`: 396,754,944 bytes; SHA-256 `e9a077b5c81becdc44d95de62488f1324b65375266a877509fbe315574d81966`. Executable SHA-256 `888d6b2283ee7bd0f8c7c3dba1b74a173a64cd1030870c910be655d4069fc0a0`.

TSE package `SeriousSam-TSE-PS4-Alpha-0.01-local.pkg`: 417,136,640 bytes; SHA-256 `f4f8fdd3ce11b9e53d1d82626332941d27ff260f1efd0a875c2ec9dae0eca7d4`. Executable SHA-256 `3ec25f122aa45d7f85ab6d426c31733612eac5b93d1b3285c1aaa1d095e31e88`.

### Later-level checks

The package executables also started these worlds and added a player; captured
screenshots were inspected for actual 3D output and HUD:

| Game | World | Evidence |
| --- | --- | --- |
| TFE | `07_Dunes.wld` | Desert scene, enemies and minigun in view |
| TFE | `15_TheGreatPyramid.wld` | Pyramid entrance, lighting and weapon/HUD |
| TSE | `2_1_Ziggurrat.wld` | Babylon chamber with textured walls and pistol/HUD |
| TSE | `3_3_CorridorOfDeath.wld` | Final-level courtyard, effects and minigun/HUD |

These checks live under `artifacts/levels/{tfe,tse}/`, each with
`level-check.json`, `SeriousSam.log`, `run.json` and `level.png`. They verify
load/render at the start of those worlds, not completion of battles or bosses.

Remaining: physical PS4 test of TSE 0.01 and TFE 0.03's added controls, Bomb inventory behavior, level-exit transitions, long sessions and
complete campaigns. The user's reported slower cinematics are deliberately
deferred. Online/splitscreen play is outside the verified single-player scope.

Both games passed a separate cold-load check of their existing quicksave via
the main menu; see `artifacts/tfe-cold-reload/` and `artifacts/tse-cold-reload/`.

### Generated icons

At the user's request, the built-in image generation tool produced separate
cover icons: golden Egyptian temples for TFE and a teal/green jungle pyramid
for TSE. Original generated art lives in `assets/artwork/{tfe,tse}-cover.png`.
The package consumes `assets/icon0-tfe.png` and `assets/icon0-tse.png`, each
512x512, opaque 8-bit RGB PNG. Exact prompts and the tool identity are recorded
in `assets/icon-prompts.json`. The earlier SVG placeholders are retained.

The artwork repack changes only `sce_sys/icon0.png` among the application
files. Both tested executables and every game-resource hash are unchanged.
Versions remain TFE 0.03 and TSE 0.01; the hashes above identify the artwork
repack. Earlier package manifests are in `artifacts/package-*-before-artwork/`.

Additional TSE controller check (`artifacts/tse-weapons-retry/`): R1 cycles
from the minigun to the sniper; L2 opens the scope. D-pad up changes the visible
zoom from 2.3x to 4.0x, and down reduces it again. L2 closes the scope. R3
produces the `0x2000` fire-bomb action bit, but this spawn had no collected bomb;
actual detonation remains unverified. The initial attempt was still in NETRICSA
and is retained under `artifacts/tse-weapons/`, not counted as a weapon test.

Final artwork packages were copied to the root of `SCUMMVM_PS4`, with file
and directory fsync completed, expected byte lengths, and successful safe
unmount/power-off. No full USB readback hash was performed. Delivery evidence
is in `artifacts/usb-artwork-delivery.json`.
