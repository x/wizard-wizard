import json
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, get_args

from .shared import ToolResponse, fuzzy_match

School = Literal[
    "abjuration",
    "conjuration",
    "divination",
    "enchantment",
    "evocation",
    "illusion",
    "necromancy",
    "transmutation",
]

Class = Literal[
    "bard",
    "cleric",
    "druid",
    "paladin",
    "ranger",
    "sorcerer",
    "warlock",
    "wizard",
]


class Spell(TypedDict):
    name: str
    level: int
    school: School
    classes: list[Class]
    actionType: str
    concentration: bool
    ritual: bool
    range: str
    components: list[str]
    material: NotRequired[str]
    duration: str
    description: str
    cantripUpgrade: NotRequired[str]


_SPELLS_CACHE: list[Spell] | None = None
"""Cache for json-loaded spells."""


def _load_spells() -> list[Spell]:
    global _SPELLS_CACHE
    if _SPELLS_CACHE is None:
        spells_file = Path(__file__).parent.parent / "data" / "spells.json"
        with open(spells_file) as f:
            _SPELLS_CACHE = json.load(f)
    return _SPELLS_CACHE


def find_spell_by_name(spell_name: str) -> ToolResponse[Spell]:
    """Finds a spell by a specific name.

    Args:
        spell_name: The spell we're searching for by name.

    Returns:
        The matching spell.
    """
    spells = _load_spells()
    all_spell_names = [spell["name"] for spell in spells]
    match_spell_name = fuzzy_match(spell_name, all_spell_names)
    if match_spell_name is None:
        return {
            "status": "failure",
            "message": f"No spell matches {spell_name}",
        }
    for spell in spells:
        if spell["name"] == match_spell_name:
            return {
                "status": "success",
                "result": spell,
            }
    raise RuntimeError(f"Unexpected, no spell name matched {match_spell_name}")


def list_schools() -> ToolResponse[list[str]]:
    """Lists all of the supported schools of spells."""
    return {
        "status": "success",
        "result": list({spell["school"] for spell in _load_spells()}),
    }


def list_classes() -> ToolResponse[list[str]]:
    """Lists all of the classes which spells list as potentially supported classes."""
    classes = set()
    for spell in _load_spells():
        classes.update(spell["classes"])
    return {"status": "success", "result": list(classes)}


def list_spells(
    _class: Class | None = None,
    school: School | None = None,
    max_level: int | None = None,
    is_ritual: bool | None = None,
) -> ToolResponse[list[Spell]]:
    """Lists all spells given some set of filters.

    Args:
        _class (optional): If passed, filter the spells by class that supports the spell.
        school (optional): If passed, filter the spells by school.
        max_level (optional): If passed, filter the spells by max_level.
        is_ritual (optional): If passed, filter the spells by being a ritual or not.

    Returns
        A list of spells matching the filters or all spells if no filters as passed.
    """
    # Validate parameters using reflection on the Literal types
    if school is not None and school not in get_args(School):
        return {
            "status": "failure",
            "message": f"Invalid school '{school}'. Must be one of: {', '.join(get_args(School))}",
        }

    if _class is not None and _class not in get_args(Class):
        return {
            "status": "failure",
            "message": f"Invalid class '{_class}'. Must be one of: {', '.join(get_args(Class))}",
        }

    # Filter spells based on criteria
    spells = _load_spells()
    filtered_spells = []

    for spell in spells:
        if _class is not None and _class not in spell["classes"]:
            continue
        if school is not None and spell["school"] != school:
            continue
        if max_level is not None and spell["level"] > max_level:
            continue
        if is_ritual is not None and spell["ritual"] != is_ritual:
            continue
        filtered_spells.append(spell)

    return {
        "status": "success",
        "result": filtered_spells,
    }
