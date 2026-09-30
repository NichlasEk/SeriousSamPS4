#!/usr/bin/env bash
set -euo pipefail
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
export OO_PS4_TOOLCHAIN=${OO_PS4_TOOLCHAIN:-/opt/openorbis/OpenOrbis/PS4Toolchain}
stack=${SS_NATIVE_STACK:-/home/nichlas/Doom3-Ps4/build/native}
converter=${CREATE_FSELF:-/home/nichlas/ut99-orbis/build/create-fself-current}
revision=510d36f901cbe883c56b155b53717e4efdeb6522
source="$root/build/ps4-source"
host_source="$root/build/host-tools-source"
mkdir -p "$root/build" "$root/artifacts/ps4" "$root/build/runtime-tfe"
[[ -f "$stack/vulkan-ps4/libvulkan_ps4.a" && -f "$stack/libpsbc-private.a" && -f "$stack/opengnm/libopengnm.a" && -f "$stack/Vulkan-Headers/include/vulkan/vulkan.h" ]] || {
  echo 'Build the Doom3 native stack first, or set SS_NATIVE_STACK to an equivalent source-built stack.' >&2; exit 1;
}
[[ -x "$converter" ]] || { echo 'Set CREATE_FSELF to the OpenOrbis converter.' >&2; exit 1; }
sha256sum "$root/patches/001-openorbis-tfe.patch" \
  "$root/platform/ps4/"*.cpp "$root/platform/ps4/"*.c \
  "$root/cmake/"*.cmake "$root/scripts/build-ps4-sdl.py" \
  "$stack/vulkan-ps4/libvulkan_ps4.a" "$stack/opengnm/libopengnm.a" \
  "$stack/libpsbc-private.a" "$OO_PS4_TOOLCHAIN/lib/libSDL2.a" "$converter" \
  > "$root/artifacts/ps4/build-inputs.sha256"
for checkout in "$source" "$host_source"; do
  if [[ ! -d "$checkout/.git" ]]; then git clone --shared "$root/engine-vk" "$checkout"; fi
  [[ $(git -C "$checkout" rev-parse HEAD) == "$revision" ]] || { echo "Unexpected source revision: $checkout" >&2; exit 1; }
done
patch="$root/patches/001-openorbis-tfe.patch"
if ! git -C "$source" apply --reverse --check "$patch" 2>/dev/null; then
  git -C "$source" diff --quiet || { echo 'Preserve and review existing PS4 source edits before applying the patch.' >&2; exit 1; }
  git -C "$source" apply --check "$patch"
  git -C "$source" apply "$patch"
fi
cmake -S "$host_source/SamTFE/Sources" -B "$root/build/host-tools" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DUSE_ASM=OFF -DUSE_SYSTEM_VULKAN=OFF \
  > "$root/artifacts/ps4/host-configure.log" 2>&1
cmake --build "$root/build/host-tools" --target ecc -j"${BUILD_JOBS:-8}" \
  > "$root/artifacts/ps4/host-build.log" 2>&1
python3 "$root/scripts/build-ps4-sdl.py" > "$root/artifacts/ps4/sdl-build.log" 2>&1
python3 "$root/scripts/compile-ps4-shaders.py" "$source/SamTFE/Sources"
cmake -S "$source/SamTFE/Sources" -B "$root/build/ps4-tfe" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$root/cmake/openorbis.cmake" -DSS_PS4_ROOT="$root" \
  -DSS_NATIVE_STACK="$stack" -DECC="$root/build/host-tools/ecc" \
  -DUSE_ASM=OFF -DUSE_SINGLE_THREAD=ON -DUSE_SYSTEM_ZLIB=OFF \
  -DVulkan_INCLUDE_DIR="$stack/Vulkan-Headers/include" \
  -DVulkan_LIBRARY="$stack/vulkan-ps4/libvulkan_ps4.a" -DCMAKE_BUILD_TYPE=Release \
  > "$root/artifacts/ps4/configure.log" 2>&1
cmake --build "$root/build/ps4-tfe" --target SeriousSam -j"${BUILD_JOBS:-8}" \
  > "$root/artifacts/ps4/build.log" 2>&1
"$converter" -in="$root/build/ps4-tfe/SeriousSam" -out="$root/build/runtime-tfe/serioussam.oelf" \
  --eboot "$root/build/runtime-tfe/eboot.bin" --paid 0x3800000000000011 \
  > "$root/artifacts/ps4/fself.log" 2>&1
python3 "$root/scripts/stage-ps4-data.py"
sha256sum "$root/build/runtime-tfe/eboot.bin" > "$root/artifacts/ps4/eboot.sha256"
echo 'Built PS4 TFE client; run python3 scripts/run-ps4.py to test it.'
