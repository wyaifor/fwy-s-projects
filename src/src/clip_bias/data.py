from pathlib import Path

import pandas as pd


ADULT_AGE_GROUPS = ["20-29", "30-39", "40-49", "50-59"]


def resolve_dataset_path(project_root: str | Path, dataset_name: str) -> Path:
    """Resolve a dataset folder from either data/<name> or <name> under the project root."""
    project_root = Path(project_root)
    preferred = project_root / "data" / dataset_name
    fallback = project_root / dataset_name

    if preferred.exists():
        return preferred
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        f"Could not find the {dataset_name!r} dataset. Expected one of:\n"
        f"  - {preferred}\n"
        f"  - {fallback}\n"
        "In Colab, unzip the data archive into the project root or into the project's data/ folder."
    )


def resolve_fairface_root(project_root: str | Path) -> Path:
    """Resolve FairFace from supported Colab/local layouts."""
    root = resolve_dataset_path(project_root, "fairface")
    required = ["fairface_label_train.csv", "fairface_label_val.csv", "train", "val"]
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"FairFace directory was found at {root}, but it is missing: {missing}.\n"
            "Required layout:\n"
            "  data/fairface/fairface_label_train.csv or fairface/fairface_label_train.csv\n"
            "  data/fairface/fairface_label_val.csv or fairface/fairface_label_val.csv\n"
            "  data/fairface/train/ or fairface/train/\n"
            "  data/fairface/val/ or fairface/val/"
        )
    return root


def load_fairface_labels(root: str | Path, split: str = "both") -> pd.DataFrame:
    root = Path(root)
    split_files = {
        "train": root / "fairface_label_train.csv",
        "val": root / "fairface_label_val.csv",
    }
    if split == "both":
        frames = [_load_one_label_file(path, root) for path in split_files.values()]
        labels = pd.concat(frames, ignore_index=True)
    elif split in split_files:
        labels = _load_one_label_file(split_files[split], root)
    else:
        raise ValueError("split must be one of: train, val, both")

    required = {"file", "age", "gender", "race"}
    missing = required.difference(labels.columns)
    if missing:
        raise ValueError(f"FairFace labels missing columns: {sorted(missing)}")

    labels["image_path"] = labels["file"].apply(lambda p: str(root / p))
    labels["group"] = labels["race"].astype(str) + " | " + labels["gender"].astype(str)
    return labels


def _load_one_label_file(path: Path, root: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Could not find FairFace label file: {path}")
    df = pd.read_csv(path)
    df["source_label_file"] = str(path.relative_to(root))
    return df


def filter_adults(labels: pd.DataFrame, age_groups: list[str] | None = None) -> pd.DataFrame:
    age_groups = age_groups or ADULT_AGE_GROUPS
    return labels[labels["age"].isin(age_groups)].copy()


def balanced_sample(
    labels: pd.DataFrame,
    samples_per_group: int | None = 300,
    group_col: str = "group",
    random_state: int = 42,
) -> pd.DataFrame:
    counts = labels[group_col].value_counts()
    if counts.empty:
        raise ValueError("No rows available for balanced sampling.")

    n = counts.min() if samples_per_group is None else min(samples_per_group, counts.min())
    sampled = (
        labels.groupby(group_col, group_keys=False)
        .sample(n=n, random_state=random_state)
        .reset_index(drop=True)
    )
    return sampled
