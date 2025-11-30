import json
from pathlib import Path
from typing import TypedDict, cast

from .shared import ToolResponse, fuzzy_match


class Background(TypedDict):
    name: str
    abilityScores: list[str]
    originFeat: str
    skillProficiencies: list[str]
    toolProficiency: str
    equipment: str


_BACKGROUNDS_CACHE: dict[str, Background] | None = None
"""Cache for json-loaded backgrounds."""


def _load_backgrounds() -> dict[str, Background]:
    global _BACKGROUNDS_CACHE
    if _BACKGROUNDS_CACHE is None:
        backgrounds_file = Path(__file__).parent.parent / "data" / "backgrounds.json"
        with open(backgrounds_file) as f:
            raw_data = json.load(f)

        # Transform the data structure to include name and parse fields
        _BACKGROUNDS_CACHE = {}
        for name, data in raw_data.items():
            _BACKGROUNDS_CACHE[name] = cast(
                Background,
                {
                    "name": name,
                    "abilityScores": [
                        ability.strip() for ability in data["Ability Scores"].split(",")
                    ],
                    "originFeat": data["Origin Feat"],
                    "skillProficiencies": [
                        skill.strip()
                        for skill in data["Skill Proficiencies"].split(",")
                    ],
                    "toolProficiency": data["Tool Proficiency"],
                    "equipment": data["Equipment"],
                },
            )

    return _BACKGROUNDS_CACHE


def find_background_by_name(background_name: str) -> ToolResponse[Background]:
    """Finds a background by a specific name.

    Args:
        background_name: The background we're searching for by name.

    Returns:
        The matching background.
    """
    backgrounds = _load_backgrounds()
    all_background_names = list(backgrounds.keys())
    match_background_name = fuzzy_match(background_name, all_background_names)
    if match_background_name is None:
        return {
            "status": "failure",
            "message": f"No background matches {background_name}",
        }
    return {
        "status": "success",
        "result": backgrounds[match_background_name],
    }


def list_backgrounds(
    ability: str | None = None,
    skill: str | None = None,
) -> ToolResponse[list[Background]]:
    """Lists all backgrounds given some set of filters.

    Args:
        ability (optional): If passed, filter backgrounds that provide this ability score choice.
        skill (optional): If passed, filter backgrounds that provide this skill proficiency.

    Returns:
        A list of backgrounds matching the filters or all backgrounds if no filters are passed.
    """
    backgrounds = _load_backgrounds()
    filtered_backgrounds = []

    for background in backgrounds.values():
        if ability is not None:
            if ability not in background["abilityScores"]:
                continue
        if skill is not None:
            # Case-insensitive skill matching
            background_skills_lower = [
                s.lower() for s in background["skillProficiencies"]
            ]
            if skill.lower() not in background_skills_lower:
                continue

        filtered_backgrounds.append(background)

    return {
        "status": "success",
        "result": filtered_backgrounds,
    }


def list_backgrounds_by_feat(feat_name: str) -> ToolResponse[list[str]]:
    """Lists all background names that grant a specific origin feat.

    Args:
        feat_name: The feat name to search for (case-insensitive, partial match).

    Returns:
        List of background names that grant the specified feat.
    """
    backgrounds = _load_backgrounds()
    matching_backgrounds = []

    feat_lower = feat_name.lower()
    for background in backgrounds.values():
        if feat_lower in background["originFeat"].lower():
            matching_backgrounds.append(background["name"])

    if not matching_backgrounds:
        return {
            "status": "failure",
            "message": f"No backgrounds found with feat matching '{feat_name}'",
        }

    return {
        "status": "success",
        "result": matching_backgrounds,
    }


def list_all_skills() -> ToolResponse[list[str]]:
    """Lists all unique skill proficiencies available from backgrounds."""
    backgrounds = _load_backgrounds()
    all_skills = set()

    for background in backgrounds.values():
        all_skills.update(background["skillProficiencies"])

    return {
        "status": "success",
        "result": sorted(all_skills),
    }


def list_all_feats() -> ToolResponse[list[str]]:
    """Lists all unique origin feats available from backgrounds."""
    backgrounds = _load_backgrounds()
    all_feats = {background["originFeat"] for background in backgrounds.values()}

    return {
        "status": "success",
        "result": sorted(all_feats),
    }
