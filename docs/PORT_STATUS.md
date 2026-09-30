# Serious Sam PS4 port status

Updated 2026-09-30. The PS4 client has not been built or run.

## Source and game data

- `engine/` pins Croteam's original Serious Engine 1.10. Its published build instructions use Visual Studio.
- `engine-vk/` pins the Linux/SDL2/Vulkan fork used for the desktop baseline. It builds separate First Encounter and Second Encounter executables. Changes for PS4 should remain traceable against this upstream.
- The two supplied discs are MODE2/2352 BIN/CUE pairs, despite being described as ISOs. `scripts/extract_discs.py` converts and extracts them without changing the originals. All images and game files are under ignored `media/`.
- First Encounter has `Install/1_00.gro` plus loose `Install/Levels/*.wld`. Second Encounter has `Install/SE1_00*.gro`, including `SE1_00_Levels.gro`. All 11 `.gro` files from the two discs passed `7z t`.

## Desktop baseline

The pinned Vulkan fork compiled on the Linux host with CMake/Ninja, `USE_ASM=OFF`, and system SDL2, zlib and Vulkan. Both executables started inside `xvfb-run` with the retail archives staged locally and `SDL_AUDIODRIVER=dummy`.

The First Encounter log reports a Vulkan context on the host RTX 4090 and a started `Levels/Intro.wld` session after staging the loose `Install/Levels` directory. The Second Encounter log likewise reports a Vulkan context and a started `Levels/LevelsMP/Intro.wld` session. Each process was stopped by a 15-second timeout. This verifies startup and intro-level loading on Linux; it does not establish visible gameplay, correct rendering, audio, or PS4 behavior.

## Next port steps

The OpenOrbis SDL2 archive exports `SDL_Vulkan_CreateSurface`, `SDL_Vulkan_GetInstanceExtensions`, and `SDL_Vulkan_GetDrawableSize`; export presence alone does not prove that its PS4 backend can create the surface this renderer needs. The installed SDK has SDL2 but no ready-to-link Vulkan or zlib archive. The Doom 3 PS4 checkout has source-built native Vulkan/OpenGNM archives that can be assessed for reuse.

1. Audit the fork's SDL2, Vulkan, dynamic-library, filesystem and audio calls against the OpenOrbis SDK and the working Doom 3 PS4 stack.
2. Build a first OpenOrbis client with the game's data staged under `/app0`, keeping the retail files ignored and local.
3. Validate compile, link, shadPS4 launch, visible rendering and physical-console play as separate gates.
