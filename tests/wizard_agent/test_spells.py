from wizard_agent.tools.spells import (
    find_spell_by_name,
    list_classes,
    list_schools,
    list_spells,
)


def test_find_spell_by_name():
    result = find_spell_by_name("Fireball")
    assert result["status"] == "success"
    assert result["result"]["name"] == "Fireball"
    assert result["result"]["level"] == 3


def test_find_spell_by_name_fuzzy():
    result = find_spell_by_name("firebll")  # Typo
    assert result["status"] == "success"
    assert result["result"]["name"] == "Fireball"


def test_find_spell_by_name_not_found():
    result = find_spell_by_name("NonexistentSpell123")
    assert result["status"] == "failure"
    assert "message" in result


def test_list_schools():
    result = list_schools()
    assert result["status"] == "success"
    assert "evocation" in result["result"]
    assert "necromancy" in result["result"]


def test_list_classes():
    result = list_classes()
    assert result["status"] == "success"
    assert "wizard" in result["result"]
    assert "cleric" in result["result"]


def test_list_spells_no_filters():
    result = list_spells()
    assert result["status"] == "success"
    assert len(result["result"]) > 0


def test_list_spells_filter_by_class():
    result = list_spells(_class="wizard")
    assert result["status"] == "success"
    for spell in result["result"]:
        assert "wizard" in spell["classes"]


def test_list_spells_filter_by_level():
    result = list_spells(max_level=1)
    assert result["status"] == "success"
    for spell in result["result"]:
        assert spell["level"] <= 1


def test_list_spells_invalid_school():
    result = list_spells(school="invalid")  # type: ignore[arg-type]
    assert result["status"] == "failure"
    assert "message" in result
