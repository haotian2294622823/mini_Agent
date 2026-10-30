"""工具注册表：保存工具名称与执行函数的对应关系。"""

from collections.abc import Callable

from mini_agent.data_models import ToolResult


# 保存函数对象，而不是函数执行后的结果。
_tools: dict[str, Callable[..., str | ToolResult]] = {}

# 保存工具参数说明书（简化版 JSON Schema），供 Executor 校验参数时使用。
_schemas: dict[str, dict[str, object]] = {}


def register(
    name: str,
    function: Callable[..., str | ToolResult],
    schema: dict[str, object] | None = None,
) -> None:
    """注册工具；无效名称、不可调用对象和重复名称都会报错。"""
    if not isinstance(name, str):
        raise TypeError("工具名称必须是字符串")
    if not name.strip():
        raise ValueError("工具名称不能为空")
    if not callable(function):
        raise TypeError("工具必须是可调用对象")
    if name in _tools:
        raise ValueError(f"工具已注册：{name}")

    _tools[name] = function
    if schema is not None:
        _schemas[name] = schema


def get(name: str) -> Callable[..., str | ToolResult] | None:
    """返回工具函数；未注册时返回 None。"""
    return _tools.get(name)


def get_schema(name: str) -> dict[str, object] | None:
    """返回工具的参数说明书；未登记时返回 None。"""
    return _schemas.get(name)


def list_tools() -> list[str]:
    """返回工具名称的新列表，避免调用者直接修改注册表。"""
    return list(_tools)
