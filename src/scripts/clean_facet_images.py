from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clean local FACET images in two documented stages: "
            "single-person image filtering, then visible-face quality filtering."
        )
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--delete", action="store_true", help="Actually delete excluded images.")
    parser.add_argument("--min-person-count", type=int, default=1)
    parser.add_argument("--require-visible-face", action="store_true", default=True)
    parser.add_argument("--allow-visible-minimal", action="store_true")
    parser.add_argument("--allow-mask", action="store_true")
    return parser.parse_args()


def safe_relative(path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if not str(resolved_path).startswith(str(resolved_root)):
        raise RuntimeError(f"Unsafe path outside FACET root: {resolved_path}")
    return str(resolved_path.relative_to(root.resolve()))


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    facet_root = project_root / "data" / "facet"
    annotation_path = facet_root / "annotations" / "annotations.csv"
    image_dir = facet_root / "images"
    output_dir = project_root / "outputs" / "facet_cleanup"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not annotation_path.exists():
        raise FileNotFoundError(annotation_path)
    if not image_dir.exists():
        raise FileNotFoundError(image_dir)

    annotations = pd.read_csv(annotation_path)
    person_counts = annotations.groupby("filename").size().rename("person_count")
    annotations = annotations.merge(person_counts, on="filename", how="left")

    image_files = [path for path in image_dir.glob("*") if path.is_file()]
    image_rows = []
    for path in image_files:
        image_rows.append(
            {
                "filename": path.name,
                "path": safe_relative(path, facet_root),
                "bytes": path.stat().st_size,
            }
        )
    images = pd.DataFrame(image_rows)

    image_annotations = annotations.merge(images, on="filename", how="inner")

    single_person_mask = image_annotations["person_count"].eq(args.min_person_count)
    quality_mask = single_person_mask.copy()
    if args.require_visible_face:
        quality_mask &= image_annotations["visible_face"].eq(1)
    if not args.allow_visible_minimal:
        quality_mask &= image_annotations["visible_minimal"].eq(0)
    if not args.allow_mask:
        quality_mask &= image_annotations["has_mask"].eq(0)

    keep = image_annotations[quality_mask].copy()
    keep_names = set(keep["filename"])

    manifest = images.copy()
    manifest["keep_single_person"] = manifest["filename"].isin(
        set(image_annotations.loc[single_person_mask, "filename"])
    )
    manifest["keep_visible_face_subset"] = manifest["filename"].isin(keep_names)
    manifest["delete"] = ~manifest["keep_visible_face_subset"]
    manifest = manifest.sort_values(["delete", "filename"])

    delete_manifest = manifest[manifest["delete"]].copy()
    keep_manifest = manifest[~manifest["delete"]].copy()

    keep_annotation = keep.drop(columns=["path", "bytes"]).sort_values("filename")

    mode = "delete" if args.delete else "dry_run"
    manifest.to_csv(output_dir / f"facet_visible_face_cleanup_manifest_{mode}.csv", index=False)
    keep_manifest.to_csv(output_dir / f"facet_visible_face_keep_manifest_{mode}.csv", index=False)
    delete_manifest.to_csv(output_dir / f"facet_visible_face_delete_manifest_{mode}.csv", index=False)
    keep_annotation.to_csv(facet_root / "annotations" / "annotations_single_person_visible_face.csv", index=False)

    summary = pd.DataFrame(
        [
            {"metric": "mode", "value": mode},
            {"metric": "input_image_files", "value": len(images)},
            {"metric": "single_person_images_on_disk", "value": int(manifest["keep_single_person"].sum())},
            {"metric": "kept_visible_face_images", "value": len(keep_manifest)},
            {"metric": "deleted_or_to_delete_images", "value": len(delete_manifest)},
            {"metric": "kept_classes", "value": keep_annotation["class1"].nunique()},
            {"metric": "kept_gb", "value": round(keep_manifest["bytes"].sum() / 1024**3, 3)},
            {"metric": "deleted_or_to_delete_gb", "value": round(delete_manifest["bytes"].sum() / 1024**3, 3)},
        ]
    )
    summary.to_csv(output_dir / f"facet_visible_face_cleanup_summary_{mode}.csv", index=False)

    if args.delete:
        for rel_path in delete_manifest["path"]:
            path = (facet_root / rel_path).resolve()
            if not str(path).startswith(str(facet_root.resolve())):
                raise RuntimeError(f"Unsafe delete path outside FACET root: {path}")
            if path.exists():
                path.unlink()

    print(summary.to_string(index=False))
    print(f"Wrote manifests to {output_dir}")
    print("Wrote filtered annotation to data/facet/annotations/annotations_single_person_visible_face.csv")


if __name__ == "__main__":
    main()
