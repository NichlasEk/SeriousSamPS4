# Serious Sam PS4 alpha — installation

This release contains First Encounter 0.04 and Second Encounter 0.02 as separate
PS4 packages. Both can be installed together. A homebrew-enabled PS4 with the
compatible kernel service used by libjbc is required for USB sandbox mapping.
No particular firmware version is certified by this release.

1. Install the PKG for the encounter you want.
2. Extract `SeriousSam-PS4-support-data.zip` on your computer. It contains
   `serioussam-game/` and `serioussamse-game/`, with engine support resources.
3. Add the following files from your own **classic original game**, not HD or
   Fusion. Preserve spelling and case; do not add another `Install` subfolder.

| Folder | Add your own game files |
| --- | --- |
| `serioussam-game/` | `1_00.gro`, `1_00_music.gro`, and the complete original `Levels/` directory |
| `serioussamse-game/` | `SE1_00.gro`, `SE1_00_Extra.gro`, `SE1_00_Levels.gro`, `SE1_00_Music.gro` |

These layouts were tested with the original disc data. Other releases of the
classic games may have different file layouts and have not been verified.
The archive `SE1_10b.gro` and support directories come from the pinned upstream
engine repository; the commercial campaign archives are not included.

4. Copy the complete folder to the PS4's internal `/data/` directory, or directly
   to the root of a PS4-readable USB drive:

```text
HDD: /data/serioussam-game/       USB: /serioussam-game/
HDD: /data/serioussamse-game/     USB: /serioussamse-game/
```

Internal HDD data takes priority. If required files are missing or unreadable,
the port searches USB slots 0–7. Install the PKG separately; merely placing a
PKG beside the folder does not install it. Settings, saves and logs always use
`/data/serioussam/` or `/data/serioussamse/` on the internal drive.

## Validation and feedback

Both packages passed build, package extraction and file-integrity checks.
Their first campaign levels loaded and created quicksaves in shadPS4. These
exact external-data builds, including USB fallback, still need physical PS4
validation. An earlier TFE build ran on physical PS4; that is not a hardware
certification of these versions. This is an experimental alpha.

When reporting an issue, include encounter/version, PS4 firmware, HDD or USB,
and the symptoms. The engine log is `SeriousSam.log` in the save/log directory.
Please do not attach commercial game files or account/private information.
