from google.adk.tools import ToolContext

from wizard_agent.models import CharacterSheet

from .shared import ToolResponse
from .spells import find_spell_by_name, list_spells

CHARACTER_SHEET_KEY = "character_sheet"


def _get_sheet(tool_context: ToolContext) -> CharacterSheet:
    """Get the character sheet from session state, creating if needed."""
    sheet_data = tool_context.state.get(CHARACTER_SHEET_KEY)
    if sheet_data is None:
        return CharacterSheet()
    return CharacterSheet.model_validate(sheet_data)


def _save_sheet(tool_context: ToolContext, sheet: CharacterSheet) -> None:
    """Save the character sheet to session state."""
    tool_context.state[CHARACTER_SHEET_KEY] = sheet.model_dump()


def get_character_sheet(tool_context: ToolContext) -> ToolResponse[dict]:
    """Gets the current character sheet.

    Returns:
        The current character sheet data.
    """
    sheet = _get_sheet(tool_context)
    return {
        "status": "success",
        "result": sheet.model_dump(),
    }


def check_next_step(tool_context: ToolContext) -> ToolResponse[dict]:
    """Checks the character sheet and determines what step should be done next.

    Returns:
        A dict with:
        - next_agent: The name of the next agent to invoke, or "complete" if done
        - step_name: Human-readable name of the next step
        - reason: Why this step is next
    """
    sheet = _get_sheet(tool_context)

    # Check each step in order
    if not sheet.name or not sheet.race:
        return {
            "status": "success",
            "result": {
                "next_agent": "race_agent",
                "step_name": "Name & Race Selection",
                "reason": "Character needs a name and race",
            },
        }

    if all(
        getattr(sheet.ability_scores, ability) == 10
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    ):
        return {
            "status": "success",
            "result": {
                "next_agent": "ability_score_agent",
                "step_name": "Ability Scores",
                "reason": "Ability scores haven't been set yet",
            },
        }

    if not sheet.character_class:
        return {
            "status": "success",
            "result": {
                "next_agent": "class_agent",
                "step_name": "Class Setup",
                "reason": "Need to set up the Wizard class and choose skills",
            },
        }

    if not sheet.background:
        return {
            "status": "success",
            "result": {
                "next_agent": "background_agent",
                "step_name": "Background Selection",
                "reason": "Need to choose a background",
            },
        }

    if not sheet.spellcasting_ability:
        return {
            "status": "success",
            "result": {
                "next_agent": "spellcasting_agent",
                "step_name": "Spellcasting Setup",
                "reason": "Need to configure spellcasting stats",
            },
        }

    if len(sheet.spellbook) < 6:
        return {
            "status": "success",
            "result": {
                "next_agent": "spellbook_agent",
                "step_name": "Spellbook Selection",
                "reason": "Need to choose 6 level-1 spells for the spellbook",
            },
        }

    if len(sheet.cantrips_known) < 3:
        return {
            "status": "success",
            "result": {
                "next_agent": "cantrip_agent",
                "step_name": "Cantrip Selection",
                "reason": "Need to choose 3 cantrips",
            },
        }

    if not sheet.prepared_spells:
        return {
            "status": "success",
            "result": {
                "next_agent": "prepared_spells_agent",
                "step_name": "Prepared Spells",
                "reason": "Need to choose which spells to prepare",
            },
        }

    if sheet.armor_class is None:
        return {
            "status": "success",
            "result": {
                "next_agent": "derived_stats_agent",
                "step_name": "Final Stats Calculation",
                "reason": "Need to calculate derived stats (AC, initiative, etc.)",
            },
        }

    # All steps complete
    return {
        "status": "success",
        "result": {
            "next_agent": "validation_agent",
            "step_name": "Final Validation & Summary",
            "reason": "All steps complete, ready for final validation",
        },
    }


def set_character_name(name: str, tool_context: ToolContext) -> ToolResponse[str]:
    """Sets the character's name.

    Args:
        name: The character's name.

    Returns:
        Confirmation of the name being set.
    """
    sheet = _get_sheet(tool_context)
    sheet.name = name
    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Character name set to '{name}'",
    }


def set_race(
    race_name: str,
    size: str,
    speed: int,
    darkvision: int | None,
    racial_traits: list[str],
    tool_context: ToolContext,
) -> ToolResponse[str]:
    """Sets the character's race and racial traits.

    Args:
        race_name: The name of the race.
        size: The size category (small or medium).
        speed: Base walking speed in feet.
        darkvision: Darkvision range in feet, or None if no darkvision.
        racial_traits: List of racial trait names.

    Returns:
        Confirmation of the race being set.
    """
    sheet = _get_sheet(tool_context)
    sheet.race = race_name
    sheet.size = size
    sheet.speed = speed
    sheet.darkvision = darkvision
    sheet.racial_traits = racial_traits
    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Race set to '{race_name}' ({size}, {speed}ft speed)",
    }


def set_ability_scores(
    strength: int,
    dexterity: int,
    constitution: int,
    intelligence: int,
    wisdom: int,
    charisma: int,
    tool_context: ToolContext,
) -> ToolResponse[str]:
    """Sets the base ability scores for the character.

    Args:
        strength: Strength score (typically 8-15 for standard array).
        dexterity: Dexterity score.
        constitution: Constitution score.
        intelligence: Intelligence score.
        wisdom: Wisdom score.
        charisma: Charisma score.

    Returns:
        Confirmation of scores being set.
    """
    sheet = _get_sheet(tool_context)
    sheet.ability_scores.strength = strength
    sheet.ability_scores.dexterity = dexterity
    sheet.ability_scores.constitution = constitution
    sheet.ability_scores.intelligence = intelligence
    sheet.ability_scores.wisdom = wisdom
    sheet.ability_scores.charisma = charisma
    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": (
            f"Ability scores set: STR {strength}, DEX {dexterity}, "
            f"CON {constitution}, INT {intelligence}, WIS {wisdom}, CHA {charisma}"
        ),
    }


def set_class_wizard(
    skill_proficiencies: list[str],
    tool_context: ToolContext,
) -> ToolResponse[str]:
    """Sets the character's class to Wizard with all class features.

    Args:
        skill_proficiencies: Two skills chosen from the wizard skill list.

    Returns:
        Confirmation of class being set.
    """
    valid_wizard_skills = [
        "Arcana",
        "History",
        "Insight",
        "Investigation",
        "Medicine",
        "Religion",
    ]

    for skill in skill_proficiencies:
        if skill not in valid_wizard_skills:
            return {
                "status": "failure",
                "message": f"'{skill}' is not a valid wizard skill. Choose from: {', '.join(valid_wizard_skills)}",
            }

    if len(skill_proficiencies) != 2:
        return {
            "status": "failure",
            "message": "Wizard must choose exactly 2 skill proficiencies",
        }

    sheet = _get_sheet(tool_context)
    sheet.character_class = "Wizard"
    sheet.level = 1
    sheet.hit_die = "d6"
    sheet.saving_throw_proficiencies = ["Intelligence", "Wisdom"]
    sheet.weapon_proficiencies = [
        "Daggers",
        "Darts",
        "Slings",
        "Quarterstaffs",
        "Light crossbows",
    ]
    sheet.armor_proficiencies = []
    sheet.skill_proficiencies = list(
        set(sheet.skill_proficiencies + skill_proficiencies)
    )

    # Calculate HP: 6 + CON modifier
    con_mod = sheet.get_total_modifier("constitution")
    sheet.max_hp = max(1, 6 + con_mod)

    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Class set to Wizard. HP: {sheet.max_hp}, Skills: {', '.join(skill_proficiencies)}",
    }


def set_background(
    background_name: str,
    skill_proficiencies: list[str],
    tool_proficiency: str,
    origin_feat: str,
    ability_bonuses: dict[str, int],
    tool_context: ToolContext,
) -> ToolResponse[str]:
    """Sets the character's background and associated features.

    Args:
        background_name: The name of the background.
        skill_proficiencies: Skills granted by the background.
        tool_proficiency: Tool proficiency granted.
        origin_feat: The origin feat from the background.
        ability_bonuses: Ability score bonuses from the background.

    Returns:
        Confirmation of background being set.
    """
    sheet = _get_sheet(tool_context)
    sheet.background = background_name
    sheet.origin_feat = origin_feat
    sheet.background_ability_bonuses = ability_bonuses

    # Add skill proficiencies (avoiding duplicates)
    sheet.skill_proficiencies = list(
        set(sheet.skill_proficiencies + skill_proficiencies)
    )

    # Add tool proficiency
    if tool_proficiency and tool_proficiency not in sheet.tool_proficiencies:
        sheet.tool_proficiencies.append(tool_proficiency)

    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Background set to '{background_name}' with feat '{origin_feat}'",
    }


def configure_spellcasting(tool_context: ToolContext) -> ToolResponse[str]:
    """Configures wizard spellcasting attributes.

    Returns:
        Confirmation of spellcasting being configured.
    """
    sheet = _get_sheet(tool_context)

    if sheet.character_class != "Wizard":
        return {
            "status": "failure",
            "message": "Character must be a Wizard to configure spellcasting",
        }

    sheet.spellcasting_ability = "Intelligence"

    # Level 1 wizard spell slots
    sheet.spell_slots = {1: 2}

    # Calculate spell save DC and attack bonus
    int_mod = sheet.get_total_modifier("intelligence")
    sheet.spell_save_dc = 8 + sheet.proficiency_bonus + int_mod
    sheet.spell_attack_bonus = sheet.proficiency_bonus + int_mod

    # Max prepared spells = INT mod + level (minimum 1)
    sheet.max_prepared_spells = max(1, int_mod + sheet.level)

    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": (
            f"Spellcasting configured: DC {sheet.spell_save_dc}, "
            f"Attack +{sheet.spell_attack_bonus}, "
            f"Max prepared: {sheet.max_prepared_spells}"
        ),
    }


def add_cantrip(spell_name: str, tool_context: ToolContext) -> ToolResponse[str]:
    """Adds a cantrip to the character's known cantrips.

    Args:
        spell_name: The name of the cantrip to add.

    Returns:
        Confirmation or error message.
    """
    # Verify spell exists and is a wizard cantrip
    spell_result = find_spell_by_name(spell_name)
    if spell_result["status"] == "failure":
        return spell_result

    spell = spell_result["result"]
    if spell["level"] != 0:
        return {
            "status": "failure",
            "message": f"'{spell['name']}' is not a cantrip (level {spell['level']})",
        }
    if "wizard" not in spell["classes"]:
        return {
            "status": "failure",
            "message": f"'{spell['name']}' is not a wizard spell",
        }

    sheet = _get_sheet(tool_context)

    if len(sheet.cantrips_known) >= 3:
        return {
            "status": "failure",
            "message": "Cannot add more than 3 cantrips at level 1",
        }

    if spell["name"] in sheet.cantrips_known:
        return {
            "status": "failure",
            "message": f"'{spell['name']}' is already known",
        }

    sheet.cantrips_known.append(spell["name"])
    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Added cantrip '{spell['name']}' ({len(sheet.cantrips_known)}/3)",
    }


def add_spellbook_spell(
    spell_name: str,
    tool_context: ToolContext,
) -> ToolResponse[str]:
    """Adds a 1st-level spell to the wizard's spellbook.

    Args:
        spell_name: The name of the spell to add.

    Returns:
        Confirmation or error message.
    """
    # Verify spell exists and is a level 1 wizard spell
    spell_result = find_spell_by_name(spell_name)
    if spell_result["status"] == "failure":
        return spell_result

    spell = spell_result["result"]
    if spell["level"] != 1:
        return {
            "status": "failure",
            "message": f"'{spell['name']}' is level {spell['level']}, must be level 1",
        }
    if "wizard" not in spell["classes"]:
        return {
            "status": "failure",
            "message": f"'{spell['name']}' is not a wizard spell",
        }

    sheet = _get_sheet(tool_context)

    if len(sheet.spellbook) >= 6:
        return {
            "status": "failure",
            "message": "Cannot add more than 6 spells to spellbook at level 1",
        }

    if spell["name"] in sheet.spellbook:
        return {
            "status": "failure",
            "message": f"'{spell['name']}' is already in spellbook",
        }

    sheet.spellbook.append(spell["name"])
    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Added '{spell['name']}' to spellbook ({len(sheet.spellbook)}/6)",
    }


def prepare_spell(spell_name: str, tool_context: ToolContext) -> ToolResponse[str]:
    """Prepares a spell from the spellbook.

    Args:
        spell_name: The name of the spell to prepare.

    Returns:
        Confirmation or error message.
    """
    sheet = _get_sheet(tool_context)

    if spell_name not in sheet.spellbook:
        return {
            "status": "failure",
            "message": f"'{spell_name}' is not in your spellbook",
        }

    if sheet.max_prepared_spells is None:
        return {
            "status": "failure",
            "message": "Spellcasting has not been configured yet",
        }

    if len(sheet.prepared_spells) >= sheet.max_prepared_spells:
        return {
            "status": "failure",
            "message": f"Cannot prepare more than {sheet.max_prepared_spells} spells",
        }

    if spell_name in sheet.prepared_spells:
        return {
            "status": "failure",
            "message": f"'{spell_name}' is already prepared",
        }

    sheet.prepared_spells.append(spell_name)
    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": f"Prepared '{spell_name}' ({len(sheet.prepared_spells)}/{sheet.max_prepared_spells})",
    }


def compute_derived_stats(tool_context: ToolContext) -> ToolResponse[dict]:
    """Computes all derived combat stats for the character.

    Returns:
        Dictionary of computed stats.
    """
    sheet = _get_sheet(tool_context)

    # AC (unarmored) = 10 + DEX mod
    dex_mod = sheet.get_total_modifier("dexterity")
    sheet.armor_class = 10 + dex_mod

    # Initiative = DEX mod
    sheet.initiative = dex_mod

    # Passive Perception = 10 + Perception modifier
    wis_mod = sheet.get_total_modifier("wisdom")
    perception_bonus = wis_mod
    if "Perception" in sheet.skill_proficiencies:
        perception_bonus += sheet.proficiency_bonus
    sheet.passive_perception = 10 + perception_bonus

    # Recalculate HP if CON changed
    if sheet.character_class == "Wizard":
        con_mod = sheet.get_total_modifier("constitution")
        sheet.max_hp = max(1, 6 + con_mod)

    _save_sheet(tool_context, sheet)
    return {
        "status": "success",
        "result": {
            "armor_class": sheet.armor_class,
            "initiative": sheet.initiative,
            "passive_perception": sheet.passive_perception,
            "max_hp": sheet.max_hp,
        },
    }


def validate_character_sheet(tool_context: ToolContext) -> ToolResponse[dict]:
    """Validates the character sheet for completeness and correctness.

    Returns:
        Validation result with any errors found.
    """
    sheet = _get_sheet(tool_context)
    errors = []

    # Check required fields
    if not sheet.race:
        errors.append({"field": "race", "message": "Race not set"})

    if not sheet.character_class:
        errors.append({"field": "character_class", "message": "Class not set"})

    if not sheet.background:
        errors.append({"field": "background", "message": "Background not set"})

    # Check ability scores are valid
    for ability in [
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    ]:
        total = sheet.total_ability_scores.get(ability, 0)
        if total < 1 or total > 30:
            errors.append(
                {
                    "field": f"ability_scores.{ability}",
                    "message": f"{ability.capitalize()} score {total} is out of range (1-30)",
                }
            )

    # Check cantrips
    if len(sheet.cantrips_known) != 3:
        errors.append(
            {
                "field": "cantrips_known",
                "message": f"Expected 3 cantrips, found {len(sheet.cantrips_known)}",
            }
        )

    # Check spellbook
    if len(sheet.spellbook) != 6:
        errors.append(
            {
                "field": "spellbook",
                "message": f"Expected 6 spells in spellbook, found {len(sheet.spellbook)}",
            }
        )

    # Check prepared spells
    if sheet.max_prepared_spells is not None:
        if len(sheet.prepared_spells) > sheet.max_prepared_spells:
            errors.append(
                {
                    "field": "prepared_spells",
                    "message": f"Too many prepared spells ({len(sheet.prepared_spells)}/{sheet.max_prepared_spells})",
                }
            )

    # Check derived stats computed
    if sheet.armor_class is None:
        errors.append({"field": "armor_class", "message": "AC not computed"})
    if sheet.max_hp is None:
        errors.append({"field": "max_hp", "message": "HP not computed"})

    if errors:
        return {
            "status": "failure",
            "message": f"Validation failed with {len(errors)} error(s)",
            "result": {"errors": errors, "valid": False},
        }

    return {
        "status": "success",
        "result": {
            "valid": True,
            "summary": {
                "name": sheet.name or "Unnamed Wizard",
                "race": sheet.race,
                "class": f"{sheet.character_class} {sheet.level}",
                "background": sheet.background,
                "hp": sheet.max_hp,
                "ac": sheet.armor_class,
                "abilities": sheet.total_ability_scores,
                "cantrips": sheet.cantrips_known,
                "spellbook": sheet.spellbook,
                "prepared_spells": sheet.prepared_spells,
            },
        },
    }


def list_wizard_cantrips() -> ToolResponse[list[str]]:
    """Lists all available wizard cantrips.

    Returns:
        List of wizard cantrip names.
    """
    result = list_spells(_class="wizard", max_level=0)
    if result["status"] == "failure":
        return result

    cantrip_names = [spell["name"] for spell in result["result"]]
    return {
        "status": "success",
        "result": cantrip_names,
    }


def list_wizard_level1_spells() -> ToolResponse[list[str]]:
    """Lists all available level 1 wizard spells.

    Returns:
        List of level 1 wizard spell names.
    """
    result = list_spells(_class="wizard", max_level=1)
    if result["status"] == "failure":
        return result

    # Filter to only level 1 (exclude cantrips)
    spell_names = [spell["name"] for spell in result["result"] if spell["level"] == 1]
    return {
        "status": "success",
        "result": spell_names,
    }
