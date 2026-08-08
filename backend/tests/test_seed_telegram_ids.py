"""Проверка: дефолтные SEED telegram_id не пересекаются."""

from __future__ import annotations

import pytest

from scripts.seed_demo import (
    DEFAULT_BORIS_TG,
    DEFAULT_IWONA_TG,
    DEFAULT_JAN_TG,
    DEFAULT_VIKTORIA_TG,
    _assert_unique_telegram_ids,
)


def test_default_seed_telegram_ids_are_unique() -> None:
    ids = [
        int(DEFAULT_VIKTORIA_TG),
        int(DEFAULT_IWONA_TG),
        int(DEFAULT_BORIS_TG),
        int(DEFAULT_JAN_TG),
    ]
    assert len(ids) == len(set(ids))
    # Jan больше не делит ID с Viktoria
    assert DEFAULT_VIKTORIA_TG != DEFAULT_JAN_TG


def test_assert_unique_telegram_ids_raises_on_collision() -> None:
    with pytest.raises(ValueError, match="Одинаковый telegram_id"):
        _assert_unique_telegram_ids(
            [
                ("Viktoria", 111),
                ("Jan", 111),
            ]
        )
