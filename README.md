# Serious Sam PS4

PS4 port workspace for the classic Serious Sam games. Croteam's original [Serious Engine 1.10](https://github.com/Croteam-official/Serious-Engine) source is pinned in `engine/`. The Linux/SDL2/[Vulkan fork](https://github.com/tx00100xt/SeriousSamClassic-VK) used for port work is pinned in `engine-vk/`. Both are Git submodules.

Clone with `git clone --recurse-submodules https://github.com/NichlasEk/SeriousSamPS4.git`, or run `git submodule update --init` after a regular clone.

The upstream repository includes the `SE1_10.gro` resource archive for running the engine without the original game data. Original First Encounter and Second Encounter game resources are separate. Put locally supplied game data under `media/`; that directory is ignored by Git.

For MODE2/2352 BIN/CUE images named `Serious Sam - The First Encounter (USA)` and `Serious Sam - The Second Encounter (USA)`, run `python3 scripts/extract_discs.py`. It leaves the original files intact, converts them to `media/iso/{tfe,tse}.iso`, and extracts them under `media/game/{tfe,tse}/`.

The original game archives are in `media/game/tfe/Install/*.gro` and `media/game/tse/Install/*.gro`. The port will stage the needed archives for each game separately. All disc images, converted ISOs, and extracted files stay local.

The first **First Encounter PS4 client** builds with OpenOrbis and boots in shadPS4 using the source-built native Vulkan/OpenGNM stack from the Doom 3 port. Startup logos and the textured 3D intro are visibly rendered from the retail data. Controller play, audio and a physical PS4 are not yet verified. Second Encounter currently has only the desktop baseline.

## Build and run the initial PS4 client

With the local OpenOrbis SDK and the Doom 3 native graphics archives available:

```sh
bash scripts/build-ps4.sh
python3 scripts/run-ps4.py --seconds 180
```

The build produces `build/runtime-tfe/eboot.bin`. The runner uses an isolated shadPS4 profile, captures `artifacts/ps4/emulator.png`, records logs and stops after the requested duration. It does not create an installable PKG.

See [port status](docs/PORT_STATUS.md) for dependencies, current evidence and remaining work.
