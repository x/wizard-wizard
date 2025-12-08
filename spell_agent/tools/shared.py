from typing import Literal, NotRequired, TypedDict

import rapidfuzz


class ToolResponse[T](TypedDict):
    status: Literal["success", "failure"]
    message: NotRequired[str]
    result: NotRequired[T]


def fuzzy_match(query: str, candidates: list[str]) -> str | None:
    """Fuzzy match a query against a list of candidates.

    Args:
        query: The search query.
        candidates: List of strings to match against.

    Returns:
        The best matching candidate or None if no good match found.
    """
    result = rapidfuzz.process.extractOne(
        query,
        candidates,
        scorer=rapidfuzz.fuzz.WRatio,
        score_cutoff=65,
        processor=lambda x: x.lower(),
    )
    return result[0] if result else None
