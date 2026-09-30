#!/usr/bin/env python3
"""Extract owned Serious Sam MODE2/2352 BIN/CUE discs without changing originals."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
SECTOR = 2352
USER_DATA_OFFSET = 24
USER_DATA_SIZE = 2048
DISCS = {
    "tfe": "Serious Sam - The First Encounter (USA)",
    "tse": "Serious Sam - The Second Encounter (USA)",
}


def convert_disc(name: str, stem: str) -> None:
    source = MEDIA / f"{stem}.bin"
    cue = MEDIA / f"{stem}.cue"
    iso = MEDIA / "iso" / f"{name}.iso"
    destination = MEDIA / "game" / name

    if not source.is_file() or not cue.is_file():
        raise FileNotFoundError(f"Missing BIN/CUE pair: {stem}")
    cue_text = cue.read_text(encoding="utf-8")
    if f'FILE "{source.name}" BINARY' not in cue_text or "TRACK 01 MODE2/2352" not in cue_text:
        raise ValueError(f"Unexpected CUE layout: {cue}")
    size = source.stat().st_size
    if size % SECTOR:
        raise ValueError(f"Incomplete sector in {source}")
    with source.open("rb") as raw:
        raw.seek(16 * SECTOR + USER_DATA_OFFSET)
        if raw.read(6) != b"\x01CD001":
            raise ValueError(f"No ISO 9660 primary volume descriptor in {source}")

    iso.parent.mkdir(parents=True, exist_ok=True)
    expected_iso_size = (size // SECTOR) * USER_DATA_SIZE
    if iso.exists() and iso.stat().st_size != expected_iso_size:
        raise ValueError(f"Existing ISO has unexpected size: {iso}")
    if not iso.exists():
        temporary = iso.with_suffix(".iso.partial")
        try:
            with source.open("rb") as raw, temporary.open("wb") as output:
                for _ in range(size // SECTOR):
                    sector = raw.read(SECTOR)
                    output.write(sector[USER_DATA_OFFSET:USER_DATA_OFFSET + USER_DATA_SIZE])
            temporary.replace(iso)
        finally:
            temporary.unlink(missing_ok=True)

    print(f"{name}: {iso} ({iso.stat().st_size} bytes)", flush=True)
    if destination.exists() and any(destination.iterdir()):
        print(f"{name}: keeping existing extraction at {destination}", flush=True)
        return
    if destination.exists():
        destination.rmdir()
    temporary = destination.with_name(f"{destination.name}.partial")
    if temporary.exists():
        raise ValueError(f"Incomplete extraction exists; inspect it before retrying: {temporary}")
    temporary.mkdir(parents=True)
    subprocess.run(["7z", "x", "-y", f"-o{temporary}", str(iso)], check=True)
    temporary.rename(destination)
    print(f"{name}: extracted to {destination}", flush=True)


def main() -> int:
    for name, stem in DISCS.items():
        convert_disc(name, stem)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
