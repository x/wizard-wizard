from wizard_agent.tools.backgrounds import (
    find_background_by_name,
    list_all_feats,
    list_all_skills,
    list_backgrounds,
    list_backgrounds_by_feat,
)


def test_find_background_by_name():
    result = find_background_by_name("Acolyte")
    assert result["status"] == "success"
    assert result["result"]["name"] == "Acolyte"
    assert "Intelligence" in result["result"]["abilityScores"]


def test_find_background_by_name_fuzzy():
    result = find_background_by_name("acolyt")  # Partial match
    assert result["status"] == "success"
    assert result["result"]["name"] == "Acolyte"


def test_find_background_by_name_not_found():
    result = find_background_by_name("NonexistentBackground123")
    assert result["status"] == "failure"
    assert "message" in result


def test_list_backgrounds_no_filters():
    result = list_backgrounds()
    assert result["status"] == "success"
    assert len(result["result"]) > 0


def test_list_backgrounds_filter_by_ability():
    result = list_backgrounds(ability="Charisma")
    assert result["status"] == "success"
    for background in result["result"]:
        assert "Charisma" in background["abilityScores"]


def test_list_backgrounds_filter_by_skill():
    result = list_backgrounds(skill="Stealth")
    assert result["status"] == "success"
    for background in result["result"]:
        skills_lower = [s.lower() for s in background["skillProficiencies"]]
        assert "stealth" in skills_lower


def test_list_backgrounds_by_feat():
    result = list_backgrounds_by_feat("Alert")
    assert result["status"] == "success"
    assert len(result["result"]) > 0


def test_list_backgrounds_by_feat_not_found():
    result = list_backgrounds_by_feat("NonexistentFeat123")
    assert result["status"] == "failure"
    assert "message" in result


def test_list_all_skills():
    result = list_all_skills()
    assert result["status"] == "success"
    assert "Stealth" in result["result"]
    assert "Perception" in result["result"]


def test_list_all_feats():
    result = list_all_feats()
    assert result["status"] == "success"
    assert len(result["result"]) > 0
