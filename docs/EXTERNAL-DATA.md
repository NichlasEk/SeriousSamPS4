# External data packages (2026-11-08)

TFE 0.04 and TSE 0.02 contain the executable and SDK support files, with game
resources in a separate folder. These are private local test candidates.

| Game | Package in `dist/` | Data folder in `dist/external-data/` | PS4 HDD destination |
| --- | --- | --- | --- |
| First Encounter | `SeriousSam-TFE-PS4-Alpha-0.04-external.pkg` | `serioussam-game` | `/data/serioussam-game/` |
| Second Encounter | `SeriousSam-TSE-PS4-Alpha-0.02-external.pkg` | `serioussamse-game` | `/data/serioussamse-game/` |

Install the PKG and copy the corresponding **whole data folder** to `/data/`
on the internal drive, or to the root of a PS4-readable USB drive. Do not nest
it inside `external-data` on the console/USB. The `.manifest.json` files are
local verification records and need not be copied. A PKG sitting beside a
folder is not sufficient: installation and the destination above matter.

Each title checks its HDD folder first. If required files are missing or
unreadable, it searches USB slots 0–7. It selects one data root; it does not mix
incomplete HDD files with USB files. Startup checks the required archives for
ZIP signatures plus key loose support files. This detects missing/truncated
inputs, not every possible archive corruption. The preparation script performs
full source/copy SHA-256 comparison for every delivered file.

Saves, settings and logs remain in `/data/serioussam/` (TFE) and
`/data/serioussamse/` (TSE). Title IDs remain `SSAM00001` and `SSAM00002`.
The selected root is logged as `Selected external game data:`; the engine's
`SeriousSam.log` also records `Assumed engine data directory:`. Missing data
stops startup rather than falling back to packaged resources.

USB uses Doom3's read-only sandbox mapping approach with `/ssam_usbN` aliases.
It requires the compatible homebrew kernel service already used by Doom3;
this application does not install one. Credentials are restored before engine
startup and only mounts created by this process are released on normal exit.
A restoration failure stops startup. Physical USB mapping/loading still needs
verification on the PS4.

## Build and checks

```sh
bash scripts/build-ps4.sh tfe
python3 scripts/package-ps4.py --game tfe
python3 scripts/verify-ps4-package.py --game tfe
bash scripts/build-ps4.sh tse
python3 scripts/package-ps4.py --game tse
python3 scripts/verify-ps4-package.py --game tse

c++ -std=c++11 -Itests/stubs -Ibuild/ps4-usb tests/storage.cpp -o build/test-storage-tfe
build/test-storage-tfe
c++ -std=c++11 -DSS_PS4_TSE -Itests/stubs -Ibuild/ps4-usb tests/storage.cpp -o build/test-storage-tse
build/test-storage-tse
```

The supplemental `003-external-data-{tfe,tse}.patch` is applied after the
original encounter patch. `scripts/build-ps4-usb.py` builds local libjbc revision
`835fe016ff0ae5dd89b9249f39cc0fe093fd07dd`, using `SS_JBC_SOURCE` or the sibling
`ScummVM-PS4/.tools/ps4-libjbc` cache. Its source fingerprints are recorded in
`build/ps4-usb/source-sha256.txt`. The upstream dependency has no declared
license; no third-party source/archive is added to Git. This work does not
establish a public redistribution license for that dependency.

Packaging writes a new external package stage and preserves the previous
bundled TFE 0.03 / TSE 0.01 packages in `dist/` for rollback. Extracted payload
hashes, SFO identity and SDK support modules are checked. Commercial game data,
build output, manifests and packages remain ignored by Git.

## Console acceptance test

1. Copy the matching data folder to HDD and install the new PKG. Start a level
   with USB disconnected. Check the engine log points to `/data/...-game/`.
2. With both HDD and USB copies present, check HDD is still selected.
3. Temporarily rename the HDD data folder, leave the correct folder at the USB
   root, and start again. Check the selected `/ssam_usbN/...` or `/mnt/usbN/...`
   path, then load a level and verify saves still go to the internal save folder.
4. Restore the HDD folder name. Previous bundled packages remain the rollback.

Builds, host resolver tests and emulator evidence are separate from physical
PS4 installation, USB access and gameplay acceptance.

## Verified local results

- Both OpenOrbis builds and clean replay of all four patches passed.
- Host resolver tests passed for both encounters: HDD priority, incomplete and
  invalid archive rejection, USB slots 0/7, archive reopen after credential
  restoration, missing data/service, restoration/mount failure and mount ownership.
- Both PKGs passed PkgTool validation and extracted payload/SFO/module checks.
- TFE: 27,852,800-byte PKG; separate data: 192 files, 356,811,483 bytes.
- TSE: 28,704,768-byte PKG; separate data: 176 files, 376,049,779 bytes.
- Every external data file was SHA-256 compared against its source and rechecked
  after emulator startup. Data folders are complete ordinary copies, not symlinks.
- Exact extracted package executables started their intro sessions in isolated
  shadPS4 profiles, using `/data/serioussam-game/` and `/data/serioussamse-game/`.

Package hashes:

```text
62737b774cccae8e028cad9dc406b79f18402b0f62a14895c6f90afc433fa27b  SeriousSam-TFE-PS4-Alpha-0.04-external.pkg
7a0efe4b4a04ed9d7cbec574df8faa3043d749f5251563ca7ec57ffcc4595dfa  SeriousSam-TSE-PS4-Alpha-0.02-external.pkg
```

Evidence is in `artifacts/external-data-validation.json`,
`artifacts/external-patch-check.json`, `artifacts/storage-test-{tfe,tse}.txt`,
`artifacts/package-{tfe,tse}-external/`, `artifacts/external-test-tfe-fixed/`
and `artifacts/external-test-tse/`.

First-campaign-level smoke tests also passed using the exact extracted EBOOTs:
TFE `Levels/01_Hatshepsut.wld` and TSE `Levels/LevelsMP/1_1_Palenque.wld`.
Both screenshots showed the level and player HUD; both created nonempty quick
saves under their internal `/data/serioussam[se]/SaveGame/` directories.
Evidence: `artifacts/levels-external/`. These 90-second tests verify level startup
and save creation, not full gameplay, save reload or physical-console behavior.

Reproduce with:

```sh
python3 scripts/test-ps4-level.py --game tfe --level Levels/01_Hatshepsut.wld
python3 scripts/test-ps4-level.py --game tse --level Levels/LevelsMP/1_1_Palenque.wld
```

The level runner refuses to overwrite an existing case's evidence. Archive that
case before repeating it. Only the disposable external-data copy's startup
script is changed; the delivered data folder and package remain untouched.
