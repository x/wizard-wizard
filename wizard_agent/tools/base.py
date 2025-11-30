from typing import Literal, NotRequired, TypedDict


class ToolResponse[T](TypedDict):
    status: Literal["success", "failure"]
    message: NotRequired[str]
    response: NotRequired[T]
