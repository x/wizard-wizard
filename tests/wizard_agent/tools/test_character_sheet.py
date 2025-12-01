from unittest.mock import MagicMock

import pytest

from wizard_agent.models import CharacterSheet
from wizard_agent.tools.character_sheet import (
    CHARACTER_SHEET_KEY,
    add_cantrip,
    add_spellbook_spell,
    compute_derived_stats,
    configure_spellcasting,
    get_character_sheet,
    list_wizard_cantrips,
    list_wizard_level1_spells,
    prepare_spell,
    set_ability_scores,
    set_background,
    set_character_name,
    set_class_wizard,
    set_race,
    validate_character_sheet,
)


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext with state dictionary."""
    context = MagicMock()
    context.state = {}
    return context


@pytest.fixture
def populated_context(mock_tool_context):
    """Create a context with a partially filled character sheet."""
    sheet = CharacterSheet(
        name="Test Wizard",
        race="Gnome",
        size="small",
        speed=25,
        darkvision=60,
        character_class="Wizard",
        level=1,
        hit_die="d6",
        max_hp=7,
    )
    sheet.ability_scores.intelligence = 15
    sheet.ability_scores.constitution = 14
    mock_tool_context.state[CHARACTER_SHEET_KEY] = sheet.model_dump()
    return mock_tool_context


class TestGetCharacterSheet:
    def test_returns_empty_sheet_when_not_initialized(self, mock_tool_context):
        result = get_character_sheet(mock_tool_context)
        assert result["status"] == "success"
        assert result["result"]["name"] is None
        assert result["result"]["race"] is None

    def test_returns_existing_sheet(self, populated_context):
        result = get_character_sheet(populated_context)
        assert result["status"] == "success"
        assert result["result"]["name"] == "Test Wizard"
        assert result["result"]["race"] == "Gnome"


class TestSetCharacterName:
    def test_sets_name(self, mock_tool_context):
        result = set_character_name("Fizban", mock_tool_context)
        assert result["status"] == "success"
        assert "Fizban" in result["result"]

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["name"] == "Fizban"


class TestSetRace:
    def test_sets_race_with_darkvision(self, mock_tool_context):
        result = set_race(
            "Gnome", "small", 25, 60, ["Gnome Cunning"], mock_tool_context
        )
        assert result["status"] == "success"

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["race"] == "Gnome"
        assert sheet_data["size"] == "small"
        assert sheet_data["speed"] == 25
        assert sheet_data["darkvision"] == 60
        assert "Gnome Cunning" in sheet_data["racial_traits"]

    def test_sets_race_without_darkvision(self, mock_tool_context):
        result = set_race("Human", "medium", 30, None, ["Versatile"], mock_tool_context)
        assert result["status"] == "success"

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["race"] == "Human"
        assert sheet_data["darkvision"] is None


class TestSetAbilityScores:
    def test_sets_standard_array(self, mock_tool_context):
        result = set_ability_scores(8, 14, 13, 15, 12, 10, mock_tool_context)
        assert result["status"] == "success"

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["ability_scores"]["strength"] == 8
        assert sheet_data["ability_scores"]["dexterity"] == 14
        assert sheet_data["ability_scores"]["constitution"] == 13
        assert sheet_data["ability_scores"]["intelligence"] == 15
        assert sheet_data["ability_scores"]["wisdom"] == 12
        assert sheet_data["ability_scores"]["charisma"] == 10


class TestSetClassWizard:
    def test_sets_wizard_class(self, mock_tool_context):
        # First set ability scores for HP calculation
        set_ability_scores(8, 14, 13, 15, 12, 10, mock_tool_context)

        result = set_class_wizard(["Arcana", "History"], mock_tool_context)
        assert result["status"] == "success"

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["character_class"] == "Wizard"
        assert sheet_data["level"] == 1
        assert sheet_data["hit_die"] == "d6"
        assert "Intelligence" in sheet_data["saving_throw_proficiencies"]
        assert "Wisdom" in sheet_data["saving_throw_proficiencies"]
        assert "Arcana" in sheet_data["skill_proficiencies"]
        assert "History" in sheet_data["skill_proficiencies"]
        assert sheet_data["max_hp"] == 7  # 6 + 1 (CON mod from 13)

    def test_rejects_invalid_skill(self, mock_tool_context):
        result = set_class_wizard(["Arcana", "Athletics"], mock_tool_context)
        assert result["status"] == "failure"
        assert "Athletics" in result["message"]

    def test_rejects_wrong_number_of_skills(self, mock_tool_context):
        result = set_class_wizard(["Arcana"], mock_tool_context)
        assert result["status"] == "failure"
        assert "exactly 2" in result["message"]


class TestSetBackground:
    def test_sets_background(self, mock_tool_context):
        result = set_background(
            "Sage",
            ["Arcana", "History"],
            "Calligrapher's Supplies",
            "Magic Initiate (Wizard)",
            {"intelligence": 2, "constitution": 1},
            mock_tool_context,
        )
        assert result["status"] == "success"

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["background"] == "Sage"
        assert sheet_data["origin_feat"] == "Magic Initiate (Wizard)"
        assert "Calligrapher's Supplies" in sheet_data["tool_proficiencies"]


class TestConfigureSpellcasting:
    def test_configures_wizard_spellcasting(self, mock_tool_context):
        # Setup: Set class first
        set_ability_scores(8, 14, 13, 15, 12, 10, mock_tool_context)
        set_class_wizard(["Arcana", "History"], mock_tool_context)

        result = configure_spellcasting(mock_tool_context)
        assert result["status"] == "success"

        sheet_data = mock_tool_context.state[CHARACTER_SHEET_KEY]
        assert sheet_data["spellcasting_ability"] == "Intelligence"
        assert sheet_data["spell_slots"][1] == 2
        assert sheet_data["spell_save_dc"] == 12  # 8 + 2 (prof) + 2 (INT mod)
        assert sheet_data["spell_attack_bonus"] == 4  # 2 + 2
        assert sheet_data["max_prepared_spells"] == 3  # 2 (INT mod) + 1 (level)

    def test_fails_without_wizard_class(self, mock_tool_context):
        result = configure_spellcasting(mock_tool_context)
        assert result["status"] == "failure"


class TestAddCantrip:
    def test_adds_valid_cantrip(self, populated_context):
        result = add_cantrip("Fire Bolt", populated_context)
        assert result["status"] == "success"

        sheet_data = populated_context.state[CHARACTER_SHEET_KEY]
        assert "Fire Bolt" in sheet_data["cantrips_known"]

    def test_rejects_non_cantrip(self, populated_context):
        result = add_cantrip("Magic Missile", populated_context)
        assert result["status"] == "failure"
        assert "not a cantrip" in result["message"]

    def test_rejects_non_wizard_cantrip(self, populated_context):
        result = add_cantrip("Sacred Flame", populated_context)
        assert result["status"] == "failure"
        assert "not a wizard spell" in result["message"]

    def test_limits_to_three_cantrips(self, populated_context):
        add_cantrip("Fire Bolt", populated_context)
        add_cantrip("Light", populated_context)
        add_cantrip("Mage Hand", populated_context)

        result = add_cantrip("Prestidigitation", populated_context)
        assert result["status"] == "failure"
        assert "more than 3" in result["message"]


class TestAddSpellbookSpell:
    def test_adds_valid_spell(self, populated_context):
        result = add_spellbook_spell("Magic Missile", populated_context)
        assert result["status"] == "success"

        sheet_data = populated_context.state[CHARACTER_SHEET_KEY]
        assert "Magic Missile" in sheet_data["spellbook"]

    def test_rejects_cantrip(self, populated_context):
        result = add_spellbook_spell("Fire Bolt", populated_context)
        assert result["status"] == "failure"
        assert "level 0" in result["message"]

    def test_rejects_higher_level_spell(self, populated_context):
        result = add_spellbook_spell("Fireball", populated_context)
        assert result["status"] == "failure"
        assert "level 3" in result["message"]

    def test_limits_to_six_spells(self, populated_context):
        spells = [
            "Magic Missile",
            "Shield",
            "Sleep",
            "Detect Magic",
            "Mage Armor",
            "Find Familiar",
        ]
        for spell in spells:
            add_spellbook_spell(spell, populated_context)

        result = add_spellbook_spell("Chromatic Orb", populated_context)
        assert result["status"] == "failure"
        assert "more than 6" in result["message"]


class TestPrepareSpell:
    def test_prepares_spell_from_spellbook(self, populated_context):
        # Setup spellcasting
        configure_spellcasting(populated_context)
        add_spellbook_spell("Magic Missile", populated_context)

        result = prepare_spell("Magic Missile", populated_context)
        assert result["status"] == "success"

        sheet_data = populated_context.state[CHARACTER_SHEET_KEY]
        assert "Magic Missile" in sheet_data["prepared_spells"]

    def test_rejects_spell_not_in_spellbook(self, populated_context):
        configure_spellcasting(populated_context)

        result = prepare_spell("Shield", populated_context)
        assert result["status"] == "failure"
        assert "not in your spellbook" in result["message"]


class TestComputeDerivedStats:
    def test_computes_stats(self, mock_tool_context):
        set_ability_scores(8, 14, 13, 15, 12, 10, mock_tool_context)
        set_class_wizard(["Arcana", "History"], mock_tool_context)

        result = compute_derived_stats(mock_tool_context)
        assert result["status"] == "success"
        assert result["result"]["armor_class"] == 12  # 10 + 2 (DEX mod)
        assert result["result"]["initiative"] == 2  # DEX mod
        assert result["result"]["passive_perception"] == 11  # 10 + 1 (WIS mod)


class TestValidateCharacterSheet:
    def test_valid_complete_sheet(self, mock_tool_context):
        # Build a complete character (2024 rules: no racial ability bonuses)
        set_character_name("Test Wizard", mock_tool_context)
        set_race("Gnome", "small", 25, 60, ["Gnome Cunning"], mock_tool_context)
        set_ability_scores(8, 14, 13, 15, 12, 10, mock_tool_context)
        set_class_wizard(["Arcana", "History"], mock_tool_context)
        set_background(
            "Sage",
            ["Arcana", "History"],
            "Calligrapher's Supplies",
            "Magic Initiate",
            {"intelligence": 2, "constitution": 1},
            mock_tool_context,
        )
        configure_spellcasting(mock_tool_context)

        # Add cantrips
        add_cantrip("Fire Bolt", mock_tool_context)
        add_cantrip("Light", mock_tool_context)
        add_cantrip("Mage Hand", mock_tool_context)

        # Add spellbook spells
        spells = [
            "Magic Missile",
            "Shield",
            "Sleep",
            "Detect Magic",
            "Mage Armor",
            "Find Familiar",
        ]
        for spell in spells:
            add_spellbook_spell(spell, mock_tool_context)

        compute_derived_stats(mock_tool_context)

        result = validate_character_sheet(mock_tool_context)
        assert result["status"] == "success"
        assert result["result"]["valid"] is True

    def test_invalid_incomplete_sheet(self, mock_tool_context):
        # Empty sheet should fail validation
        result = validate_character_sheet(mock_tool_context)
        assert result["status"] == "failure"
        assert result["result"]["valid"] is False
        assert len(result["result"]["errors"]) > 0


class TestListSpellHelpers:
    def test_list_wizard_cantrips(self):
        result = list_wizard_cantrips()
        assert result["status"] == "success"
        assert "Fire Bolt" in result["result"]
        assert "Light" in result["result"]

    def test_list_wizard_level1_spells(self):
        result = list_wizard_level1_spells()
        assert result["status"] == "success"
        assert "Magic Missile" in result["result"]
        assert "Shield" in result["result"]
        # Should not include cantrips
        assert "Fire Bolt" not in result["result"]
