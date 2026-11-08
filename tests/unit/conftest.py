"""Shared helpers for building tiles in the unit tests."""

from backend.logic.models import Tile, TileSet


def t(value: int, color: str) -> Tile:
    """A regular tile, e.g. t(5, "red")."""
    return Tile(value=value, color=color)


def joker() -> Tile:
    return Tile(is_joker=True)


def tile_set(*tiles: Tile) -> TileSet:
    return TileSet(tiles=list(tiles))
