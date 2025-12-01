from wizard_agent.tools.races import (
    find_race_by_name,
    list_races,
    list_sizes,
)


def test_find_race_by_name():
    result = find_race_by_name("Elf")
    assert result["status"] == "success"
    assert result["result"]["name"] == "Elf"
    assert result["result"]["size"] == "medium"


def test_find_race_by_name_fuzzy():
    result = find_race_by_name("elv")  # Partial match
    assert result["status"] == "success"
    assert result["result"]["name"] == "Elf"


def test_find_race_by_name_not_found():
    result = find_race_by_name("NonexistentRace123")
    assert result["status"] == "failure"
    assert "message" in result


def test_list_races_no_filters():
    result = list_races()
    assert result["status"] == "success"
    assert len(result["result"]) > 0


def test_list_races_filter_by_size():
    result = list_races(size="small")
    assert result["status"] == "success"
    for race in result["result"]:
        assert race["size"] == "small"


def test_list_races_filter_by_darkvision():
    result = list_races(has_darkvision=True)
    assert result["status"] == "success"
    for race in result["result"]:
        assert race["darkvision"] is not None


def test_list_races_invalid_size():
    result = list_races(size="huge")  # type: ignore[arg-type]
    assert result["status"] == "failure"
    assert "message" in result


def test_list_sizes():
    result = list_sizes()
    assert result["status"] == "success"
    assert "small" in result["result"]
    assert "medium" in result["result"]
