"""Tests de la séparation train / validation / test (Phase 5)."""

from __future__ import annotations

import pandas as pd
import pytest

from ml.src import split


def _ids(parts: dict[str, pd.DataFrame]) -> list[list[int]]:
    return [parts[name]["id"].tolist() for name in ("train", "validation", "test")]


def test_split_sizes_match_shares() -> None:
    frame = pd.DataFrame({"id": range(1000)})
    parts = split.split_dataset(frame, seed=7)
    assert {name: len(part) for name, part in parts.items()} == {
        "train": 700,
        "validation": 150,
        "test": 150,
    }


def test_split_is_disjoint_and_exhaustive() -> None:
    frame = pd.DataFrame({"id": range(997)})
    parts = split.split_dataset(frame, seed=7)
    train, validation, test = _ids(parts)
    assert set(train).isdisjoint(validation)
    assert set(train).isdisjoint(test)
    assert set(validation).isdisjoint(test)
    assert sorted(train + validation + test) == list(range(997))


def test_split_absorbs_rounding_into_train() -> None:
    frame = pd.DataFrame({"id": range(97)})
    parts = split.split_dataset(frame, seed=1)
    assert sum(len(part) for part in parts.values()) == 97


def test_split_is_deterministic_for_a_seed() -> None:
    frame = pd.DataFrame({"id": range(200)})
    first = _ids(split.split_dataset(frame, seed=42))
    second = _ids(split.split_dataset(frame, seed=42))
    assert first == second


def test_split_changes_with_the_seed() -> None:
    frame = pd.DataFrame({"id": range(200)})
    first = _ids(split.split_dataset(frame, seed=1))
    second = _ids(split.split_dataset(frame, seed=2))
    assert first != second


def test_split_resets_index_and_keeps_columns() -> None:
    frame = pd.DataFrame({"id": range(50), "prix": range(1000, 1050)})
    parts = split.split_dataset(frame, seed=3)
    for part in parts.values():
        assert part.columns.tolist() == ["id", "prix"]
        assert part.index.tolist() == list(range(len(part)))


def test_split_rejects_invalid_shares() -> None:
    frame = pd.DataFrame({"id": range(10)})
    with pytest.raises(ValueError, match="sommer à 1"):
        split.split_dataset(frame, shares={"train": 0.5, "test": 0.4}, seed=1)
    with pytest.raises(ValueError, match="strictement positive"):
        split.split_dataset(
            frame, shares={"train": 0.7, "validation": 0.3, "test": 0.0}, seed=1
        )
    with pytest.raises(ValueError, match="Au moins un ensemble"):
        split.split_dataset(frame, shares={}, seed=1)


def test_split_rejects_dataset_smaller_than_splits() -> None:
    frame = pd.DataFrame({"id": range(2)})
    with pytest.raises(ValueError, match="trop petit"):
        split.split_dataset(frame, seed=1)
