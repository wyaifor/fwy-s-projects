from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a zip archive and split it into fixed-size parts.")
    parser.add_argument("source", type=Path, help="Directory to archive.")
    parser.add_argument("output_prefix", type=Path, help="Output prefix, for example archives/facet_visible_face.zip.")
    parser.add_argument("--part-mb", type=int, default=900, help="Part size in MiB.")
    parser.add_argument("--compression", choices=["stored", "deflated"], default="stored")
    return parser.parse_args()


def zip_directory(source: Path, zip_path: Path, compression: int) -> None:
    source = source.resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=compression, allowZip64=True) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(source.parent)
                zf.write(path, arcname)


def split_file(path: Path, part_size: int) -> list[Path]:
    parts: list[Path] = []
    with path.open("rb") as src:
        index = 1
        while True:
            chunk = src.read(part_size)
            if not chunk:
                break
            part_path = path.with_name(f"{path.name}.part{index:03d}")
            with part_path.open("wb") as dst:
                dst.write(chunk)
            parts.append(part_path)
            index += 1
    return parts


def main() -> None:
    args = parse_args()
    compression = zipfile.ZIP_STORED if args.compression == "stored" else zipfile.ZIP_DEFLATED
    zip_path = args.output_prefix
    part_size = args.part_mb * 1024 * 1024

    print(f"Creating zip: {zip_path}")
    zip_directory(args.source, zip_path, compression)
    print(f"Zip size: {zip_path.stat().st_size / 1024**3:.2f} GB")

    print(f"Splitting into {args.part_mb} MiB parts")
    parts = split_file(zip_path, part_size)
    for part in parts:
        print(f"{part.name}: {part.stat().st_size / 1024**2:.1f} MiB")
    print(f"Created {len(parts)} parts")
    print(f"Original zip kept at: {zip_path}")


if __name__ == "__main__":
    main()
