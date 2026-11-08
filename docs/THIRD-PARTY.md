# Third-party credits and source scope

Serious Engine and amp11lib retain GPLv2 and their authors' notices.
Credit to Croteam, sultim-t, tx00100xt and the SeriousSamClassic-VK contributors.
The engine baseline is `510d36f901cbe883c56b155b53717e4efdeb6522` of
https://github.com/tx00100xt/SeriousSamClassic-VK .

The native graphics stack includes OpenGNM, opengnm-psbc and vulkan-ps4, with
upstream licenses retained in the source companion. SDL2 uses the zlib license;
Ogg/Vorbis and other engine dependencies retain their own notices. OpenOrbis
provides the SDK runtime and loader modules. The companion includes the port,
patched engine and graphics sources, adapted SDL/libjbc sources, build recipes,
licenses and original application link inputs. It requires an installed
OpenOrbis SDK; it does not claim an independently rebuilt complete SDK.
The source companion's relink verification checks the ELF hashes of both
release builds. The original PKGs are preserved unchanged.

## USB mapping dependency

Original: https://github.com/sleirsgoevy/ps4-libjbc
Used fork: https://github.com/bucanero/ps4-libjbc
Revision: `835fe016ff0ae5dd89b9249f39cc0fe093fd07dd`.
Credit to sleirsgoevy/Sergey Lisov, LightningMods and bucanero/Damian Parrino
for their upstream contributions. Local adaptations are recorded in
`scripts/build-ps4-usb.py`.

The pinned source has no declared upstream license. It is linked into these
executables for temporary credentials and read-only USB sandbox mapping.
This notice discloses the unresolved permission status and provides credit;
it is not a license grant, and the engine's GPL does not relicense libjbc.
No upstream author was contacted by this release workflow.

## Data

No owned retail archives, disc images, saved games or credentials are included.
The support-data ZIP contains only resources already present in the pinned
upstream engine repository, with its license and README. Users supply the
commercial campaign data separately. Croteam's game names remain their owners'
property; this is an unofficial community port.
