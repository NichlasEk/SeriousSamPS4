#!/usr/bin/env bash
set -euo pipefail
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
export OO_PS4_TOOLCHAIN=${OO_PS4_TOOLCHAIN:-/opt/openorbis/OpenOrbis/PS4Toolchain}
stack=${SS_NATIVE_STACK:-/home/nichlas/Doom3-Ps4/build/native}
converter=${CREATE_FSELF:-/home/nichlas/ut99-orbis/build/create-fself-current}
game=${1:-tfe}
case "$game" in
  tfe) tree=SamTFE; patch_name=001-openorbis-tfe.patch; target=SeriousSam; ecc=ecc; logdir=ps4; hostdir=host-tools ;;
  tse) tree=SamTSE; patch_name=002-openorbis-tse.patch; target=SeriousSamMP; ecc=ecc-se; logdir=ps4-tse; hostdir=host-tools-tse ;;
  *) echo 'Usage: build-ps4.sh [tfe|tse]' >&2; exit 1 ;;
esac
revision=510d36f901cbe883c56b155b53717e4efdeb6522
source="$root/build/ps4-source"
host_source="$root/build/$hostdir-source"
mkdir -p "$root/build" "$root/artifacts/$logdir" "$root/build/runtime-$game"
[[ -f "$stack/vulkan-ps4/libvulkan_ps4.a" && -f "$stack/libpsbc-private.a" && -f "$stack/opengnm/libopengnm.a" && -f "$stack/Vulkan-Headers/include/vulkan/vulkan.h" ]] || {
  echo 'Build the Doom3 native stack first, or set SS_NATIVE_STACK to an equivalent source-built stack.' >&2; exit 1;
}
[[ -x "$converter" ]] || { echo 'Set CREATE_FSELF to the OpenOrbis converter.' >&2; exit 1; }
sha256sum "$root/patches/$patch_name" \
  "$root/platform/ps4/"*.cpp "$root/platform/ps4/"*.c \
  "$root/cmake/"*.cmake "$root/scripts/build-ps4-sdl.py" \
  "$stack/vulkan-ps4/libvulkan_ps4.a" "$stack/opengnm/libopengnm.a" \
  "$stack/libpsbc-private.a" "$OO_PS4_TOOLCHAIN/lib/libSDL2.a" "$converter" \
  > "$root/artifacts/$logdir/build-inputs.sha256"
for checkout in "$source" "$host_source"; do
  if [[ ! -d "$checkout/.git" ]]; then git clone --shared "$root/engine-vk" "$checkout"; fi
  [[ $(git -C "$checkout" rev-parse HEAD) == "$revision" ]] || { echo "Unexpected source revision: $checkout" >&2; exit 1; }
done
patch="$root/patches/$patch_name"
if ! git -C "$source" apply --reverse --check "$patch" 2>/dev/null; then
  git -C "$source" diff --quiet -- "$tree" || { echo 'Preserve and review existing PS4 source edits before applying the patch.' >&2; exit 1; }
  git -C "$source" apply --check "$patch"
  git -C "$source" apply "$patch"
fi
cmake -S "$host_source/$tree/Sources" -B "$root/build/$hostdir" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DUSE_ASM=OFF -DUSE_SYSTEM_VULKAN=OFF \
  > "$root/artifacts/$logdir/host-configure.log" 2>&1
cmake --build "$root/build/$hostdir" --target "$ecc" -j"${BUILD_JOBS:-8}" \
  > "$root/artifacts/$logdir/host-build.log" 2>&1
python3 "$root/scripts/build-ps4-sdl.py" > "$root/artifacts/$logdir/sdl-build.log" 2>&1
python3 "$root/scripts/compile-ps4-shaders.py" "$source/$tree/Sources"
cmake -S "$source/$tree/Sources" -B "$root/build/ps4-$game" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$root/cmake/openorbis.cmake" -DSS_PS4_ROOT="$root" \
  -DSS_NATIVE_STACK="$stack" -DECC="$root/build/$hostdir/$ecc" -DECC-SE="$root/build/$hostdir/$ecc" \
  -DUSE_ASM=OFF -DUSE_SINGLE_THREAD=ON -DUSE_SYSTEM_ZLIB=OFF \
  -DVulkan_INCLUDE_DIR="$stack/Vulkan-Headers/include" \
  -DVulkan_LIBRARY="$stack/vulkan-ps4/libvulkan_ps4.a" -DCMAKE_BUILD_TYPE=Release \
  > "$root/artifacts/$logdir/configure.log" 2>&1
cmake --build "$root/build/ps4-$game" --target "$target" -j"${BUILD_JOBS:-8}" \
  > "$root/artifacts/$logdir/build.log" 2>&1
"$converter" -in="$root/build/ps4-$game/SeriousSam" -out="$root/build/runtime-$game/serioussam.oelf" \
  --eboot "$root/build/runtime-$game/eboot.bin" --paid 0x3800000000000011 \
  > "$root/artifacts/$logdir/fself.log" 2>&1
python3 "$root/scripts/stage-ps4-data.py" --game "$game"
sha256sum "$root/build/runtime-$game/eboot.bin" > "$root/artifacts/$logdir/eboot.sha256"
echo "Built PS4 $game client; run python3 scripts/run-ps4.py --game $game to test it."
