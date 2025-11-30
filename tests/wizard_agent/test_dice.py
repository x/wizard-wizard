from math import floor

from wizard_agent.tools.dice import roll_dice


def middleint(a, b):
    """Always return the mid_low number."""
    return floor(a + (b - a) / 2)


def test_roll_dice(mocker):
    mocker.patch("random.randint", side_effect=middleint)
    assert roll_dice("2d6+1") == {"status": "success", "result": 7}
