# Serious Sam PS4

PS4 port workspace for the classic Serious Sam games. The upstream [Serious Engine 1.10](https://github.com/Croteam-official/Serious-Engine) source is pinned as a Git submodule in `engine/`.

Clone with `git clone --recurse-submodules https://github.com/NichlasEk/SeriousSamPS4.git`, or run `git submodule update --init` after a regular clone.

The upstream repository includes the `SE1_10.gro` resource archive for running the engine without the original game data. Original First Encounter and Second Encounter game resources are separate. Put locally supplied game data under `media/`; that directory is ignored by Git.

The PS4 port has not been built or tested yet. The existing Doom 3 PS4 project is a reference for the OpenOrbis graphics and packaging work.
