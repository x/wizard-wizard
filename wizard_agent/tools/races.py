import json
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, get_args

from .shared import ToolResponse, fuzzy_match

Size = Literal["small", "medium"]

Ability = Literal[
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
    "any",
]


class AbilityScore(TypedDict):
    ability: Ability
    bonus: int
    count: NotRequired[int]


class Race(TypedDict):
    name: str
    abilityScores: list[AbilityScore]
    darkvision: int | None
    size: Size
    source: str


_RACES_CACHE: list[Race] | None = None
"""Cache for json-loaded races."""


def _load_races() -> list[Race]:
    global _RACES_CACHE
    if _RACES_CACHE is None:
        races_file = Path(__file__).parent.parent / "data" / "races.json"
        with open(races_file) as f:
            _RACES_CACHE = json.load(f)
    return _RACES_CACHE


def find_race_by_name(race_name: str) -> ToolResponse[Race]:
    """Finds a race by a specific name.

    Args:
        race_name: The race we're searching for by name.

    Returns:
        The matching race.
    """
    races = _load_races()
    all_race_names = [race["name"] for race in races]
    match_race_name = fuzzy_match(race_name, all_race_names)
    if match_race_name is None:
        return {
            "status": "failure",
            "message": f"No race matches {race_name}",
        }
    for race in races:
        if race["name"] == match_race_name:
            return {
                "status": "success",
                "result": race,
            }
    raise RuntimeError(f"Unexpected, no race name matched {match_race_name}")


def list_races(
    size: Size | None = None,
    has_darkvision: bool | None = None,
    ability: Ability | None = None,
) -> ToolResponse[list[Race]]:
    """Lists all races given some set of filters.

    Args:
        size (optional): If passed, filter races by size (small or medium).
        has_darkvision (optional): If passed, filter races by darkvision presence.
        ability (optional): If passed, filter races that have a bonus to this ability.

    Returns:
        A list of races matching the filters or all races if no filters are passed.
    """
    # Validate parameters
    if size is not None and size not in get_args(Size):
        return {
            "status": "failure",
            "message": f"Invalid size '{size}'. Must be one of: {', '.join(get_args(Size))}",
        }

    if ability is not None and ability not in get_args(Ability):
        return {
            "status": "failure",
            "message": f"Invalid ability '{ability}'. Must be one of: {', '.join(get_args(Ability))}",
        }

    # Filter races based on criteria
    races = _load_races()
    filtered_races = []

    for race in races:
        if size is not None and race["size"] != size:
            continue
        if has_darkvision is not None:
            if has_darkvision and race["darkvision"] is None:
                continue
            if not has_darkvision and race["darkvision"] is not None:
                continue
        if ability is not None:
            race_abilities = [score["ability"] for score in race["abilityScores"]]
            if ability not in race_abilities:
                continue

        filtered_races.append(race)

    return {
        "status": "success",
        "result": filtered_races,
    }


def get_ability_bonuses(race_name: str) -> ToolResponse[list[AbilityScore]]:
    """Gets the ability score bonuses for a specific race.

    Args:
        race_name: The name of the race.

    Returns:
        List of ability score bonuses for the race.
    """
    race_result = find_race_by_name(race_name)
    if race_result["status"] == "failure":
        return race_result

    race = race_result["result"]
    return {
        "status": "success",
        "result": race["abilityScores"],
    }


def list_races_by_ability(ability: Ability) -> ToolResponse[list[str]]:
    """Lists all race names that grant a bonus to a specific ability.

    Args:
        ability: The ability score to filter by.

    Returns:
        List of race names that grant a bonus to the specified ability.
    """
    if ability not in get_args(Ability):
        return {
            "status": "failure",
            "message": f"Invalid ability '{ability}'. Must be one of: {', '.join(get_args(Ability))}",
        }

    races = _load_races()
    matching_races = []

    for race in races:
        race_abilities = [score["ability"] for score in race["abilityScores"]]
        if ability in race_abilities:
            matching_races.append(race["name"])

    return {
        "status": "success",
        "result": matching_races,
    }


def list_sizes() -> ToolResponse[list[str]]:
    """Lists all possible race sizes."""
    return {
        "status": "success",
        "result": list(get_args(Size)),
    }
