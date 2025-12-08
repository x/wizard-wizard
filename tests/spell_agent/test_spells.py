from spell_agent.tools.spells import (
    compare_spells,
    find_spell_by_name,
    list_classes,
    list_schools,
    list_spells,
)


class TestFindSpellByName:
    def test_finds_exact_match(self):
        result = find_spell_by_name("Fireball")
        assert result["status"] == "success"
        assert result["result"]["name"] == "Fireball"
        assert result["result"]["level"] == 3
        assert result["result"]["school"] == "evocation"

    def test_fuzzy_match(self):
        result = find_spell_by_name("firebll")  # Typo
        assert result["status"] == "success"
        assert result["result"]["name"] == "Fireball"

    def test_not_found(self):
        result = find_spell_by_name("NonexistentSpell123")
        assert result["status"] == "failure"
        assert "message" in result


class TestListSchools:
    def test_returns_all_schools(self):
        result = list_schools()
        assert result["status"] == "success"
        assert "evocation" in result["result"]
        assert "necromancy" in result["result"]
        assert "abjuration" in result["result"]


class TestListClasses:
    def test_returns_all_classes(self):
        result = list_classes()
        assert result["status"] == "success"
        assert "wizard" in result["result"]
        assert "cleric" in result["result"]
        assert "bard" in result["result"]


class TestListSpells:
    def test_no_filters(self):
        result = list_spells()
        assert result["status"] == "success"
        assert len(result["result"]) > 0

    def test_filter_by_class(self):
        result = list_spells(_class="wizard")
        assert result["status"] == "success"
        for spell in result["result"]:
            assert "wizard" in spell["classes"]

    def test_filter_by_school(self):
        result = list_spells(school="evocation")
        assert result["status"] == "success"
        for spell in result["result"]:
            assert spell["school"] == "evocation"

    def test_filter_by_level(self):
        result = list_spells(level=3)
        assert result["status"] == "success"
        for spell in result["result"]:
            assert spell["level"] == 3

    def test_filter_by_max_level(self):
        result = list_spells(max_level=1)
        assert result["status"] == "success"
        for spell in result["result"]:
            assert spell["level"] <= 1

    def test_filter_rituals(self):
        result = list_spells(is_ritual=True)
        assert result["status"] == "success"
        for spell in result["result"]:
            assert spell["ritual"] is True

    def test_filter_concentration(self):
        result = list_spells(is_concentration=True)
        assert result["status"] == "success"
        for spell in result["result"]:
            assert spell["concentration"] is True

    def test_multiple_filters(self):
        result = list_spells(_class="wizard", school="evocation", max_level=3)
        assert result["status"] == "success"
        for spell in result["result"]:
            assert "wizard" in spell["classes"]
            assert spell["school"] == "evocation"
            assert spell["level"] <= 3

    def test_invalid_school(self):
        result = list_spells(school="invalid")  # type: ignore[arg-type]
        assert result["status"] == "failure"

    def test_invalid_class(self):
        result = list_spells(_class="invalid")  # type: ignore[arg-type]
        assert result["status"] == "failure"


class TestCompareSpells:
    def test_compare_two_spells(self):
        result = compare_spells("Fireball", "Lightning Bolt")
        assert result["status"] == "success"
        assert "spell_1" in result["result"]
        assert "spell_2" in result["result"]
        assert result["result"]["spell_1"]["name"] == "Fireball"
        assert result["result"]["spell_2"]["name"] == "Lightning Bolt"

    def test_first_spell_not_found(self):
        result = compare_spells("NonexistentSpell", "Fireball")
        assert result["status"] == "failure"

    def test_second_spell_not_found(self):
        result = compare_spells("Fireball", "NonexistentSpell")
        assert result["status"] == "failure"
