import random
import re

from .shared import ToolResponse


def roll_dice(dice_notation: str) -> ToolResponse[int]:
    """Rolls dice using standard dice notation.

    Supports notation like "2d6+3" (roll 2 six-sided dice, add 3),
    "d20" (roll 1 twenty-sided die), or "3d8-2" (roll 3 eight-sided dice, subtract 2).

    Args:
        dice_notation: Dice notation string (e.g., "2d6+3", "d20", "3d8-2").

    Returns:
        The total result of the dice roll.
    """
    # Parse dice notation: NdX+M or NdX-M or NdX
    match = re.match(r"^(\d*)d(\d+)([+-]\d+)?$", dice_notation.strip().lower())

    if not match:
        return {
            "status": "failure",
            "message": f"Invalid dice notation '{dice_notation}'. Use format like '2d6+3', 'd20', or '3d8-2'.",
        }

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if num_dice < 1 or die_sides < 1:
        return {
            "status": "failure",
            "message": "Number of dice and die sides must be at least 1.",
        }

    rolls = [random.randint(1, die_sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier

    return {
        "status": "success",
        "result": total,
    }
