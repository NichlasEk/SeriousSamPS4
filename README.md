# Serious Sam PS4

PS4 port workspace for the classic Serious Sam games. Croteam's original [Serious Engine 1.10](https://github.com/Croteam-official/Serious-Engine) source is pinned in `engine/`. The Linux/SDL2/[Vulkan fork](https://github.com/tx00100xt/SeriousSamClassic-VK) used for port work is pinned in `engine-vk/`. Both are Git submodules.

Clone with `git clone --recurse-submodules https://github.com/NichlasEk/SeriousSamPS4.git`, or run `git submodule update --init` after a regular clone.

The upstream repository includes the `SE1_10.gro` resource archive for running the engine without the original game data. Original First Encounter and Second Encounter game resources are separate. Put locally supplied game data under `media/`; that directory is ignored by Git.

For MODE2/2352 BIN/CUE images named `Serious Sam - The First Encounter (USA)` and `Serious Sam - The Second Encounter (USA)`, run `python3 scripts/extract_discs.py`. It leaves the original files intact, converts them to `media/iso/{tfe,tse}.iso`, and extracts them under `media/game/{tfe,tse}/`.

The original game archives are in `media/game/tfe/Install/*.gro` and `media/game/tse/Install/*.gro`. The port will stage the needed archives for each game separately. All disc images, converted ISOs, and extracted files stay local.

**First Encounter 0.02 is confirmed running on a physical PS4:** the user reports smooth gameplay and slower cinematics. The next First Encounter build adds touchpad quicksave and hold-L3 walking. **Second Encounter now cross-builds and runs through the same PS4 Vulkan stack in shadPS4**, with a separate title, profile and local package. Its physical PS4 test is pending.

## Build and run the initial PS4 client

With the local OpenOrbis SDK and the Doom 3 native graphics archives available:

```sh
bash scripts/build-ps4.sh tfe
python3 scripts/run-ps4.py --game tfe --seconds 180
bash scripts/build-ps4.sh tse
python3 scripts/run-ps4.py --game tse --seconds 180
```

The builds produce `build/runtime-tfe/eboot.bin` and `build/runtime-tse/eboot.bin`. The runner uses separate shadPS4 profiles and atomically allocated Xvfb displays, captures `artifacts/ps4/emulator.png` or `artifacts/ps4-tse/emulator.png`, records logs and stops after the requested duration.

To create and check a local installable package containing your supplied game data:

```sh
python3 scripts/package-ps4.py --game tfe
python3 scripts/verify-ps4-package.py --game tfe
python3 scripts/package-ps4.py --game tse
python3 scripts/verify-ps4-package.py --game tse
```

Local outputs (both contain retail assets and remain ignored by Git):

| Game | Package | Title ID | Saves/logs |
| --- | --- | --- | --- |
| First Encounter | `dist/SeriousSam-TFE-PS4-Alpha-0.03-local.pkg` | `SSAM00001` | `/data/serioussam` |
| Second Encounter | `dist/SeriousSam-TSE-PS4-Alpha-0.01-local.pkg` | `SSAM00002` | `/data/serioussamse` |

Both include the full supplied campaign data, not just the opening level. The two titles can coexist. This is still an alpha: including every campaign file does not establish a complete playthrough.

See [port status](docs/PORT_STATUS.md) for dependencies, current evidence and remaining work.

## Cover icons

Separate generated artwork is included for each encounter. Package-ready icons:
[TFE](assets/icon0-tfe.png) · [TSE](assets/icon0-tse.png). Originals are under
`assets/artwork/`; the [exact prompts](assets/icon-prompts.json) record the
built-in image generation workflow.
