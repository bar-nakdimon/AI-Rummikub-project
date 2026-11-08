"""Tests for the Tile model validation in backend/logic/models.py."""

import pytest
from pydantic import ValidationError

from backend.logic.models import Tile, TileColor


def test_valid_regular_tile():
    tile = Tile(value=7, color="blue")

    assert tile.value == 7
    assert tile.color == TileColor.blue
    assert tile.is_joker is False


def test_joker_needs_no_value_or_color():
    tile = Tile(is_joker=True)

    assert tile.is_joker is True
    assert tile.value is None
    assert tile.color is None


@pytest.mark.parametrize("value", [0, 14, -1])
def test_tile_value_must_be_between_1_and_13(value):
    with pytest.raises(ValidationError):
        Tile(value=value, color="red")


def test_regular_tile_without_value_is_rejected():
    with pytest.raises(ValidationError):
        Tile(color="red")


def test_regular_tile_without_color_is_rejected():
    with pytest.raises(ValidationError):
        Tile(value=5)


def test_unknown_color_is_rejected():
    with pytest.raises(ValidationError):
        Tile(value=5, color="green")
