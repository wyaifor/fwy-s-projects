from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_occupation_mapping(path: str | Path, clip_occupations: list[str] | None = None) -> pd.DataFrame:
    """Load the manual occupation mapping used for labour-statistics comparison."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing occupation mapping file: {path}")

    mapping = pd.read_csv(path)
    required = {"occupation", "bls_occupation"}
    missing = required.difference(mapping.columns)
    if missing:
        raise ValueError(f"Mapping file missing columns: {sorted(missing)}")

    mapping = mapping.copy()
    mapping["occupation"] = mapping["occupation"].astype(str).str.strip()
    mapping["bls_occupation"] = mapping["bls_occupation"].astype(str).str.strip()
    mapping = mapping.drop_duplicates(subset=["occupation", "bls_occupation"])

    if clip_occupations is not None:
        clip_set = set(clip_occupations)
        mapping["in_clip_outputs"] = mapping["occupation"].isin(clip_set)
        unmapped = sorted(clip_set.difference(mapping["occupation"]))
        mapping.attrs["unmapped_clip_occupations"] = unmapped

    return mapping


def load_bls_gender_distribution(path: str | Path, sheet_name: str = "cpsaat11") -> pd.DataFrame:
    """Load BLS detailed occupation percent-women values from CPS table 11."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing BLS workbook: {path}")

    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    bls = raw.iloc[:, [0, 2]].copy()
    bls.columns = ["bls_occupation", "bls_percent_women"]
    bls = bls.dropna(subset=["bls_occupation"]).copy()
    bls["bls_occupation"] = bls["bls_occupation"].astype(str).str.strip()
    bls["bls_percent_women"] = pd.to_numeric(bls["bls_percent_women"], errors="coerce")
    bls = bls.dropna(subset=["bls_percent_women"])
    return bls.drop_duplicates(subset=["bls_occupation"])


def build_bls_gender_comparison(
    clip_gender_gap: pd.DataFrame,
    mapping: pd.DataFrame,
    bls_gender: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Join CLIP gender-gap outputs to mapped BLS gender distributions."""
    required_clip = {"occupation", "male_minus_female", "abs_gender_gap"}
    missing_clip = required_clip.difference(clip_gender_gap.columns)
    if missing_clip:
        raise ValueError(f"CLIP gender gap table missing columns: {sorted(missing_clip)}")

    mapping_used = (
        mapping.merge(
            clip_gender_gap[["occupation", "male_minus_female", "abs_gender_gap"]],
            on="occupation",
            how="left",
        )
        .merge(bls_gender, on="bls_occupation", how="left")
    )
    mapping_used["has_clip_gap"] = mapping_used["male_minus_female"].notna()
    mapping_used["has_bls_gender"] = mapping_used["bls_percent_women"].notna()
    mapping_used["usable_for_bls_gender"] = mapping_used["has_clip_gap"] & mapping_used["has_bls_gender"]

    comparison = mapping_used[mapping_used["usable_for_bls_gender"]].copy()
    comparison["bls_male_minus_female_percent"] = 100 - 2 * comparison["bls_percent_women"]
    comparison["abs_bls_gender_gap_percent"] = comparison["bls_male_minus_female_percent"].abs()
    comparison["same_gap_direction"] = (
        np.sign(comparison["male_minus_female"])
        == np.sign(comparison["bls_male_minus_female_percent"])
    )
    comparison["clip_abs_gap_rank"] = comparison["abs_gender_gap"].rank(method="min", ascending=False)
    comparison["bls_abs_gap_rank"] = comparison["abs_bls_gender_gap_percent"].rank(method="min", ascending=False)
    comparison["rank_difference_clip_minus_bls"] = comparison["clip_abs_gap_rank"] - comparison["bls_abs_gap_rank"]

    return comparison.sort_values("abs_gender_gap", ascending=False), mapping_used


def write_todo_note(path: str | Path, title: str, reason: str, next_steps: list[str]) -> None:
    """Write a small markdown diagnostic note when an optional analysis cannot run."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    steps = "\n".join(f"- {step}" for step in next_steps)
    text = f"""# {title}

This optional analysis was not completed.

Reason:

```text
{reason}
```

Next steps:

{steps}
"""
    path.write_text(text, encoding="utf-8")


def plot_clip_vs_bls_gender_gap(comparison: pd.DataFrame, output_path: str | Path) -> None:
    """Plot CLIP gender association gap against BLS occupation gender distribution."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=comparison,
        x="bls_male_minus_female_percent",
        y="male_minus_female",
        hue="same_gap_direction",
    )
    plt.axhline(0, color="black", linewidth=1)
    plt.axvline(0, color="black", linewidth=1)
    plt.title("CLIP gender association gap vs BLS occupation gender distribution")
    plt.xlabel("BLS male % - female %")
    plt.ylabel("CLIP male mean similarity - female mean similarity")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_realworld_gap_rank_difference(comparison: pd.DataFrame, output_path: str | Path, top_n: int = 20) -> None:
    """Plot occupations with the largest CLIP-vs-BLS absolute gap rank differences."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plot_df = comparison.reindex(
        comparison["rank_difference_clip_minus_bls"].abs().sort_values(ascending=False).index
    ).head(top_n)

    plt.figure(figsize=(10, max(6, 0.35 * len(plot_df))))
    sns.barplot(data=plot_df, y="occupation", x="rank_difference_clip_minus_bls", color="#4C78A8")
    plt.axvline(0, color="black", linewidth=1)
    plt.title("Mapped occupations with largest CLIP-vs-BLS gender-gap rank differences")
    plt.xlabel("CLIP absolute gap rank - BLS absolute gap rank")
    plt.ylabel("Occupation")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
