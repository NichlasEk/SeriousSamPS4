# Serious Sam PS4

PS4 port workspace for the classic Serious Sam games. Croteam's original [Serious Engine 1.10](https://github.com/Croteam-official/Serious-Engine) source is pinned in `engine/`. The Linux/SDL2/[Vulkan fork](https://github.com/tx00100xt/SeriousSamClassic-VK) used for port work is pinned in `engine-vk/`. Both are Git submodules.

Clone with `git clone --recurse-submodules https://github.com/NichlasEk/SeriousSamPS4.git`, or run `git submodule update --init` after a regular clone.

The upstream repository includes the `SE1_10.gro` resource archive for running the engine without the original game data. Original First Encounter and Second Encounter game resources are separate. Put locally supplied game data under `media/`; that directory is ignored by Git.

For MODE2/2352 BIN/CUE images named `Serious Sam - The First Encounter (USA)` and `Serious Sam - The Second Encounter (USA)`, run `python3 scripts/extract_discs.py`. It leaves the original files intact, converts them to `media/iso/{tfe,tse}.iso`, and extracts them under `media/game/{tfe,tse}/`.

The original game archives are in `media/game/tfe/Install/*.gro` and `media/game/tse/Install/*.gro`. The port will stage the needed archives for each game separately. All disc images, converted ISOs, and extracted files stay local.

The PS4 port has not been built or tested yet. The existing Doom 3 PS4 project is a reference for the OpenOrbis graphics and packaging work.

See [port status](docs/PORT_STATUS.md) for the current data and desktop baseline.
