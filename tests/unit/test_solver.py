"""Tests for the ILP solver in backend/logic/solver_ilp.py."""

from collections import Counter

import pytest

from backend.logic.logic import validate_set
from backend.logic.models import GameState
from backend.logic.solver_ilp import solve_max_rack_tiles_ilp

from .conftest import joker, t, tile_set


def real_tile_counts(tiles):
    """Count non-joker tiles by (value, color)."""
    return Counter((tile.value, tile.color) for tile in tiles if not tile.is_joker)


def all_tiles(board):
    return [tile for tile_set_ in board for tile in tile_set_.tiles]


def assert_solution_is_consistent(state: GameState, result: dict):
    """
    Invariants every successful solution must satisfy:
    - every set on the new board is a legal Rummikub set
    - no tile was lost or duplicated: new board = old board + tiles played from the rack
    - tiles_used_count matches the size of the rack minus what is left in it
    """
    new_board = result["new_board"]
    remaining = result["remaining_rack"]

    for tile_set_ in new_board:
        is_valid, reason = validate_set(tile_set_.tiles)
        assert is_valid, reason

    played_from_rack = real_tile_counts(state.rack) - real_tile_counts(remaining)
    expected_board = real_tile_counts(all_tiles(state.board)) + played_from_rack
    assert real_tile_counts(all_tiles(new_board)) == expected_board

    jokers_before = sum(tile.is_joker for tile in all_tiles(state.board) + state.rack)
    jokers_after = sum(tile.is_joker for tile in all_tiles(new_board) + remaining)
    assert jokers_after == jokers_before

    assert result["tiles_used_count"] == len(state.rack) - len(remaining)


def test_plays_a_full_run_from_the_rack():
    state = GameState(rack=[t(5, "red"), t(6, "red"), t(7, "red")], board=[])

    result = solve_max_rack_tiles_ilp(state)

    assert result["status"] == "success"
    assert result["tiles_used_count"] == 3
    assert result["remaining_rack"] == []
    assert_solution_is_consistent(state, result)


def test_extends_an_existing_board_set():
    state = GameState(
        rack=[t(8, "red")],
        board=[tile_set(t(5, "red"), t(6, "red"), t(7, "red"))],
    )

    result = solve_max_rack_tiles_ilp(state)

    assert result["tiles_used_count"] == 1
    assert len(result["new_board"]) == 1
    assert_solution_is_consistent(state, result)


def test_rearranges_board_to_play_more_tiles():
    # The 5 red must be taken from the run on the board and moved into a
    # group with the rack's 5 blue and 5 yellow; the run still has 6-7-8 left.
    state = GameState(
        rack=[t(5, "blue"), t(5, "yellow")],
        board=[tile_set(t(5, "red"), t(6, "red"), t(7, "red"), t(8, "red"))],
    )

    result = solve_max_rack_tiles_ilp(state)

    assert result["tiles_used_count"] == 2
    assert len(result["new_board"]) == 2
    assert_solution_is_consistent(state, result)


def test_maximizes_number_of_rack_tiles_played():
    # One long run (5-8) would play 4 tiles, but a group of 5s plus a
    # run of 6-8 plays all 6.
    state = GameState(
        rack=[
            t(5, "red"), t(6, "red"), t(7, "red"), t(8, "red"),
            t(5, "blue"), t(5, "yellow"),
        ],
        board=[],
    )

    result = solve_max_rack_tiles_ilp(state)

    assert result["tiles_used_count"] == 6
    assert result["remaining_rack"] == []
    assert_solution_is_consistent(state, result)


def test_uses_a_joker_from_the_rack():
    state = GameState(rack=[t(5, "red"), t(6, "red"), joker()], board=[])

    result = solve_max_rack_tiles_ilp(state)

    assert result["tiles_used_count"] == 3
    assert len(result["joker_assignments"]) == 1
    assert_solution_is_consistent(state, result)


def test_board_joker_stays_on_the_board():
    state = GameState(
        rack=[],
        board=[tile_set(t(5, "red"), joker(), t(7, "red"))],
    )

    result = solve_max_rack_tiles_ilp(state)

    assert result["status"] == "success"
    assert sum(tile.is_joker for tile in all_tiles(result["new_board"])) == 1
    assert_solution_is_consistent(state, result)


@pytest.mark.parametrize(
    "board",
    [
        [],
        [tile_set(t(5, "red"), t(6, "red"), t(7, "red"))],
    ],
    ids=["empty-board", "unrelated-board"],
)
def test_no_possible_move_plays_nothing(board):
    rack = [t(1, "red"), t(10, "blue")]
    state = GameState(rack=rack, board=board)

    result = solve_max_rack_tiles_ilp(state)

    assert result["tiles_used_count"] == 0
    assert result["remaining_rack"] == rack


def test_invalid_board_returns_error():
    # Two tiles can never form a legal set, so no arrangement exists.
    state = GameState(rack=[], board=[tile_set(t(5, "red"), t(6, "red"))])

    result = solve_max_rack_tiles_ilp(state)

    assert result["status"] == "error"
    assert result["tiles_used_count"] == 0


def test_more_than_two_jokers_is_rejected():
    state = GameState(rack=[joker(), joker(), joker()], board=[])

    result = solve_max_rack_tiles_ilp(state)

    assert result["status"] == "error"
    assert "at most 2 jokers" in result["message"]
