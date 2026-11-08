"""Tests for the move explanations in backend/logic/explainer.py."""

from backend.logic.explainer import build_structured_steps, explain_solution
from backend.logic.models import GameState

from .conftest import t, tile_set


def step_types(steps):
    return [step["type"] for step in steps]


def test_unchanged_set_is_marked_keep():
    run = tile_set(t(5, "red"), t(6, "red"), t(7, "red"))
    state = GameState(rack=[], board=[run])
    result = {"new_board": [run], "remaining_rack": []}

    assert step_types(build_structured_steps(state, result)) == ["keep_set"]


def test_adding_to_a_board_set_is_marked_extend():
    old_run = tile_set(t(5, "red"), t(6, "red"), t(7, "red"))
    new_run = tile_set(t(5, "red"), t(6, "red"), t(7, "red"), t(8, "red"))
    state = GameState(rack=[t(8, "red")], board=[old_run])
    result = {"new_board": [new_run], "remaining_rack": []}

    steps = build_structured_steps(state, result)

    assert step_types(steps) == ["extend_set"]
    assert steps[0]["take_from_rack"] == [{"value": 8, "color": "red", "is_joker": False}]


def test_new_set_from_rack_is_marked_create_from_rack():
    run = tile_set(t(1, "blue"), t(2, "blue"), t(3, "blue"))
    state = GameState(rack=[t(1, "blue"), t(2, "blue"), t(3, "blue"), t(9, "yellow")], board=[])
    result = {"new_board": [run], "remaining_rack": [t(9, "yellow")]}

    assert step_types(build_structured_steps(state, result)) == ["create_from_rack"]


def test_text_explanation_lists_tiles_left_in_rack():
    run = tile_set(t(1, "blue"), t(2, "blue"), t(3, "blue"))
    state = GameState(rack=[t(1, "blue"), t(2, "blue"), t(3, "blue"), t(9, "yellow")], board=[])
    result = {"new_board": [run], "remaining_rack": [t(9, "yellow")]}

    steps = explain_solution(state, result)

    assert steps[-1] == "Tiles left in your rack: 9 yellow"


def test_text_explanation_when_rack_is_emptied():
    run = tile_set(t(1, "blue"), t(2, "blue"), t(3, "blue"))
    state = GameState(rack=[t(1, "blue"), t(2, "blue"), t(3, "blue")], board=[])
    result = {"new_board": [run], "remaining_rack": []}

    steps = explain_solution(state, result)

    assert steps[-1] == "No tiles remain in your rack."
