"""Tests for the Rummikub rules in backend/logic/logic.py."""

import pytest

from backend.logic.logic import validate_board, validate_game_state, validate_set
from backend.logic.models import GameState

from .conftest import joker, t, tile_set


# ---------------------------------------------------------------------------
# Groups: same value, different colors, 3-4 tiles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tiles",
    [
        [t(7, "red"), t(7, "blue"), t(7, "yellow")],
        [t(7, "red"), t(7, "blue"), t(7, "yellow"), t(7, "black")],
        [t(7, "red"), t(7, "blue"), joker()],
    ],
    ids=["three-colors", "four-colors", "with-joker"],
)
def test_valid_groups(tiles):
    is_valid, _ = validate_set(tiles)
    assert is_valid


@pytest.mark.parametrize(
    "tiles",
    [
        [t(7, "red"), t(7, "red"), t(7, "blue")],
        [t(7, "red"), t(8, "blue"), t(7, "yellow")],
        [t(7, "red"), t(7, "blue"), t(7, "yellow"), t(7, "black"), joker()],
    ],
    ids=["duplicate-color", "different-values", "five-tiles"],
)
def test_invalid_groups(tiles):
    is_valid, _ = validate_set(tiles)
    assert not is_valid


# ---------------------------------------------------------------------------
# Runs: same color, consecutive values, within 1-13
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tiles",
    [
        [t(5, "red"), t(6, "red"), t(7, "red")],
        [t(7, "red"), t(5, "red"), t(6, "red")],
        [t(5, "red"), joker(), t(7, "red")],
        [t(12, "black"), t(13, "black"), joker()],
        [t(1, "blue"), t(2, "blue"), joker(), joker()],
    ],
    ids=["simple", "unordered", "joker-fills-gap", "joker-extends-left", "two-jokers"],
)
def test_valid_runs(tiles):
    is_valid, _ = validate_set(tiles)
    assert is_valid


@pytest.mark.parametrize(
    "tiles",
    [
        [t(5, "red"), t(6, "blue"), t(7, "red")],
        [t(5, "red"), t(6, "red"), t(6, "red")],
        [t(5, "red"), t(7, "red"), t(8, "red")],
        [t(5, "red"), joker(), t(9, "red")],
    ],
    ids=["mixed-colors", "duplicate-value", "gap-without-joker", "gap-too-big"],
)
def test_invalid_runs(tiles):
    is_valid, _ = validate_set(tiles)
    assert not is_valid


def test_run_cannot_be_extended_past_13():
    # A full 1-13 run has no room left for a joker on either side.
    tiles = [t(value, "red") for value in range(1, 14)] + [joker()]

    is_valid, _ = validate_set(tiles)
    assert not is_valid


def test_set_needs_at_least_three_tiles():
    is_valid, reason = validate_set([t(5, "red"), t(6, "red")])

    assert not is_valid
    assert "at least 3" in reason


def test_all_joker_set_is_valid():
    is_valid, _ = validate_set([joker(), joker(), joker()])
    assert is_valid


# ---------------------------------------------------------------------------
# Whole board / whole game state
# ---------------------------------------------------------------------------

def test_validate_board_reports_index_of_invalid_set():
    board = [
        tile_set(t(5, "red"), t(6, "red"), t(7, "red")),
        tile_set(t(1, "blue"), t(9, "yellow"), t(4, "black")),
    ]

    is_valid, invalid_sets = validate_board(board)

    assert not is_valid
    assert [item.index for item in invalid_sets] == [1]


def test_validate_board_accepts_valid_board():
    board = [
        tile_set(t(5, "red"), t(6, "red"), t(7, "red")),
        tile_set(t(9, "red"), t(9, "blue"), t(9, "black")),
    ]

    is_valid, invalid_sets = validate_board(board)

    assert is_valid
    assert invalid_sets == []


def test_game_state_allows_two_copies_of_a_tile():
    state = GameState(
        rack=[t(5, "red")],
        board=[tile_set(t(5, "red"), t(6, "red"), t(7, "red"))],
    )

    is_valid, _ = validate_game_state(state)
    assert is_valid


def test_game_state_rejects_three_copies_of_a_tile():
    state = GameState(rack=[t(5, "red"), t(5, "red"), t(5, "red")], board=[])

    is_valid, invalid_sets = validate_game_state(state)

    assert not is_valid
    assert any("Too many copies" in item.reason for item in invalid_sets)


def test_game_state_rejects_more_than_two_jokers():
    state = GameState(rack=[joker(), joker(), joker()], board=[])

    is_valid, invalid_sets = validate_game_state(state)

    assert not is_valid
    assert any("Too many jokers" in item.reason for item in invalid_sets)
