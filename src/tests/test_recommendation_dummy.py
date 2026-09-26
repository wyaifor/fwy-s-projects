import numpy as np
import pandas as pd
import pytest

from clip_bias.recommendation import (
    aggregate_topk_distribution,
    bootstrap_recommendation_disparity,
    compute_recommendation_disparity,
    recommend_occupations_for_users,
    simulate_synthetic_users,
)
from clip_bias.realworld import load_occupation_mapping


def _dummy_inputs():
    rng = np.random.default_rng(42)
    image_embeddings = rng.normal(size=(24, 8))
    text_embeddings = rng.normal(size=(4, 8))
    occupation_names = ["doctor", "teacher", "engineer", "artist"]
    metadata = pd.DataFrame(
        {
            "race": ["GroupA"] * 12 + ["GroupB"] * 12,
            "gender": ["Female"] * 6 + ["Male"] * 6 + ["Female"] * 6 + ["Male"] * 6,
        }
    )
    metadata["race_gender"] = metadata["race"] + "_" + metadata["gender"]
    return image_embeddings, metadata, text_embeddings, occupation_names


def test_recommendation_pipeline_with_dummy_data():
    image_embeddings, metadata, text_embeddings, occupation_names = _dummy_inputs()

    user_meta, user_embeddings = simulate_synthetic_users(
        image_embeddings=image_embeddings,
        metadata=metadata,
        group_col="race_gender",
        n_users_per_group=3,
        history_size=4,
        random_state=42,
    )

    assert len(user_meta) == 12
    assert user_embeddings.shape == (12, 8)

    recommendations = recommend_occupations_for_users(
        user_embeddings=user_embeddings,
        user_metadata=user_meta,
        text_embeddings=text_embeddings,
        occupation_names=occupation_names,
        top_k=2,
    )

    expected_recommendation_cols = {
        "synthetic_user_id",
        "group",
        "race",
        "gender",
        "rank",
        "occupation",
        "score",
    }
    assert expected_recommendation_cols.issubset(recommendations.columns)
    assert len(recommendations) == 24

    topk_distribution = aggregate_topk_distribution(
        recommendations,
        group_col="group",
        all_occupations=occupation_names,
    )
    expected_distribution_cols = {"group", "occupation", "topk_count", "n_users", "topk_rate"}
    assert expected_distribution_cols.issubset(topk_distribution.columns)

    disparity = compute_recommendation_disparity(topk_distribution)
    expected_disparity_cols = {
        "occupation",
        "max_topk_rate",
        "min_topk_rate",
        "disparity_gap",
        "max_group",
        "min_group",
    }
    assert expected_disparity_cols.issubset(disparity.columns)


def test_all_occupations_are_included_when_not_recommended():
    recommendations = pd.DataFrame(
        {
            "synthetic_user_id": ["u1", "u2", "u3", "u4"],
            "group": ["A", "A", "B", "B"],
            "occupation": ["doctor", "doctor", "teacher", "teacher"],
            "rank": [1, 1, 1, 1],
            "score": [1.0, 0.9, 0.8, 0.7],
        }
    )

    topk_distribution = aggregate_topk_distribution(
        recommendations,
        group_col="group",
        all_occupations=["doctor", "teacher", "engineer"],
    )

    assert set(topk_distribution["occupation"]) == {"doctor", "teacher", "engineer"}
    never_recommended = topk_distribution[topk_distribution["occupation"] == "engineer"]
    assert never_recommended["topk_count"].sum() == 0
    assert never_recommended["topk_rate"].sum() == 0


def test_synthetic_user_sampling_is_reproducible():
    image_embeddings, metadata, _, _ = _dummy_inputs()

    first_meta, first_embeddings = simulate_synthetic_users(
        image_embeddings=image_embeddings,
        metadata=metadata,
        group_col="race_gender",
        n_users_per_group=2,
        history_size=4,
        random_state=7,
    )
    second_meta, second_embeddings = simulate_synthetic_users(
        image_embeddings=image_embeddings,
        metadata=metadata,
        group_col="race_gender",
        n_users_per_group=2,
        history_size=4,
        random_state=7,
    )

    pd.testing.assert_frame_equal(first_meta, second_meta)
    np.testing.assert_allclose(first_embeddings, second_embeddings)


def test_metadata_embedding_length_mismatch_raises_error():
    image_embeddings, metadata, _, _ = _dummy_inputs()

    with pytest.raises(ValueError, match="align row-by-row"):
        simulate_synthetic_users(
            image_embeddings=image_embeddings[:-1],
            metadata=metadata,
            group_col="race_gender",
        )


def test_bootstrap_output_columns_and_ci_ordering():
    image_embeddings, metadata, text_embeddings, occupation_names = _dummy_inputs()
    user_meta, user_embeddings = simulate_synthetic_users(
        image_embeddings=image_embeddings,
        metadata=metadata,
        group_col="race_gender",
        n_users_per_group=4,
        history_size=4,
        random_state=42,
    )
    recommendations = recommend_occupations_for_users(
        user_embeddings=user_embeddings,
        user_metadata=user_meta,
        text_embeddings=text_embeddings,
        occupation_names=occupation_names,
        top_k=2,
    )

    bootstrap = bootstrap_recommendation_disparity(
        recommendations,
        group_col="group",
        all_occupations=occupation_names,
        n_bootstrap=20,
        random_state=42,
    )

    expected_cols = {"occupation", "disparity_gap", "ci_low", "ci_high", "max_group", "min_group"}
    assert expected_cols.issubset(bootstrap.columns)
    assert (bootstrap["ci_low"] <= bootstrap["ci_high"]).all()
    assert (bootstrap["disparity_gap"] >= 0).all()


def test_realworld_mapping_reports_unmapped_clip_occupations(tmp_path):
    mapping_path = tmp_path / "mapping.csv"
    mapping_path.write_text(
        "occupation,bls_occupation,mapping_note\n"
        "doctor,Physicians,direct match\n",
        encoding="utf-8",
    )

    mapping = load_occupation_mapping(mapping_path, clip_occupations=["doctor", "engineer"])

    assert mapping.loc[0, "in_clip_outputs"]
    assert mapping.attrs["unmapped_clip_occupations"] == ["engineer"]


def test_realworld_mapping_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing occupation mapping file"):
        load_occupation_mapping(tmp_path / "missing_mapping.csv")
