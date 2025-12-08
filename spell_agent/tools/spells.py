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
    """Finds a spell by name and returns its full details.

    Use this when someone asks about a specific spell like "tell me about Fireball"
    or "what does Magic Missile do?"

    Args:
        spell_name: The name of the spell to look up (fuzzy matching supported).

    Returns:
        The spell's complete information including description, level, school, etc.
    """
    spells = _load_spells()
    all_spell_names = [spell["name"] for spell in spells]
    match_spell_name = fuzzy_match(spell_name, all_spell_names)
    if match_spell_name is None:
        return {
            "status": "failure",
            "message": f"No spell found matching '{spell_name}'. Try a different spelling or check the spell list.",
        }
    for spell in spells:
        if spell["name"] == match_spell_name:
            return {
                "status": "success",
                "result": spell,
            }
    raise RuntimeError(f"Unexpected: no spell name matched {match_spell_name}")


def list_schools() -> ToolResponse[list[str]]:
    """Lists all schools of magic.

    Use this when someone asks "what are the schools of magic?" or wants to browse
    spells by school.

    Returns:
        List of all magic schools (abjuration, conjuration, divination, etc.)
    """
    return {
        "status": "success",
        "result": list(get_args(School)),
    }


def list_classes() -> ToolResponse[list[str]]:
    """Lists all spellcasting classes.

    Use this when someone asks which classes can cast spells or wants to know
    their options.

    Returns:
        List of all classes that have spell lists.
    """
    return {
        "status": "success",
        "result": list(get_args(Class)),
    }


def list_spells(
    _class: Class | None = None,
    school: School | None = None,
    level: int | None = None,
    max_level: int | None = None,
    is_ritual: bool | None = None,
    is_concentration: bool | None = None,
) -> ToolResponse[list[Spell]]:
    """Lists spells matching the given filters.

    Use this to search for spells by various criteria like class, school, or level.
    All filters are optional - omit them to get all spells.

    Examples:
    - "What wizard spells are there?" -> _class="wizard"
    - "Show me evocation spells" -> school="evocation"
    - "What are the level 3 spells?" -> level=3
    - "What rituals can a cleric cast?" -> _class="cleric", is_ritual=True

    Args:
        _class: Filter by class that can cast the spell (wizard, cleric, etc.)
        school: Filter by school of magic (evocation, necromancy, etc.)
        level: Filter by exact spell level (0 for cantrips, 1-9 for leveled spells)
        max_level: Filter by maximum spell level (e.g., 3 = cantrips through 3rd level)
        is_ritual: Filter to only ritual spells (True) or non-rituals (False)
        is_concentration: Filter to concentration spells (True) or non-concentration (False)

    Returns:
        List of spells matching all provided filters.
    """
    # Validate parameters
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

    # Filter spells
    spells = _load_spells()
    filtered_spells = []

    for spell in spells:
        if _class is not None and _class not in spell["classes"]:
            continue
        if school is not None and spell["school"] != school:
            continue
        if level is not None and spell["level"] != level:
            continue
        if max_level is not None and spell["level"] > max_level:
            continue
        if is_ritual is not None and spell["ritual"] != is_ritual:
            continue
        if is_concentration is not None and spell["concentration"] != is_concentration:
            continue
        filtered_spells.append(spell)

    return {
        "status": "success",
        "result": filtered_spells,
    }


def compare_spells(spell_name_1: str, spell_name_2: str) -> ToolResponse[dict]:
    """Compares two spells side by side.

    Use this when someone asks to compare spells like "what's the difference between
    Fireball and Lightning Bolt?"

    Args:
        spell_name_1: First spell to compare.
        spell_name_2: Second spell to compare.

    Returns:
        Both spells' details for easy comparison.
    """
    result1 = find_spell_by_name(spell_name_1)
    if result1["status"] == "failure":
        return result1

    result2 = find_spell_by_name(spell_name_2)
    if result2["status"] == "failure":
        return result2

    return {
        "status": "success",
        "result": {
            "spell_1": result1["result"],
            "spell_2": result2["result"],
        },
    }
