Title: [Release] Serious Sam Classic TFE & TSE for PS4 — experimental alpha

I've put together PS4 ports of Serious Sam: The First Encounter and The Second
Encounter, based on the open-source Serious Engine/Vulkan port.

Both games have separate small PKGs. Game data stays outside the package:
internal HDD is checked first, then USB. Saves and settings stay on HDD.
You'll need your own original classic game files — no commercial game data
is included. Setup instructions and source/build material are in the release.

This is an early alpha: both first levels load and create quicksaves in shadPS4,
but these exact builds and USB fallback still need testing on a real PS4.
Feedback with your firmware, game and storage setup would be appreciated!

Download: https://github.com/NichlasEk/SeriousSamPS4/releases/tag/alpha-tfe-0.04-tse-0.02

Credits to Croteam, the SeriousSamClassic-VK contributors and the OpenOrbis/native
PS4 graphics developers. Dependency credits and caveats are in THIRD-PARTY.md.
