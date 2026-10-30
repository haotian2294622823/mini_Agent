"""统一工具执行入口。"""

import time
from inspect import signature

from mini_agent import registry
from mini_agent.data_models import ToolResult


_TYPE_CHECKS: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def _validate_against_schema(
    schema: dict[str, object], arguments: dict[str, object]
) -> str | None:
    """按简化版 JSON Schema 校验参数；通过返回 None，否则返回错误说明。"""
    if not isinstance(schema, dict):
        return None

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        properties = {}

    required = schema.get("required")
    if isinstance(required, list):
        for field in required:
            if field not in arguments:
                return f"缺少必填参数：{field}"

    if schema.get("additionalProperties") is False:
        for field in arguments:
            if field not in properties:
                return f"不认识的参数：{field}"

    for field, value in arguments.items():
        rule = properties.get(field)
        if not isinstance(rule, dict):
            continue

        expected = rule.get("type")
        if isinstance(expected, str):
            allowed = _TYPE_CHECKS.get(expected)
            if allowed is not None:
                # bool 是 int 的子类，但不应算作 integer/number。
                is_bool_mismatch = isinstance(value, bool) and expected in (
                    "integer",
                    "number",
                )
                if is_bool_mismatch or not isinstance(value, allowed):
                    return f"参数 {field} 类型错误：应为 {expected}"

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = rule.get("minimum")
            if isinstance(minimum, (int, float)) and value < minimum:
                return f"参数 {field} 过小：最小为 {minimum}"
            maximum = rule.get("maximum")
            if isinstance(maximum, (int, float)) and value > maximum:
                return f"参数 {field} 过大：最大为 {maximum}"

        items = rule.get("items")
        if expected == "array" and isinstance(items, dict) and isinstance(value, list):
            item_type = items.get("type")
            allowed = _TYPE_CHECKS.get(item_type) if isinstance(item_type, str) else None
            if allowed is not None:
                for item in value:
                    if not isinstance(item, allowed):
                        return f"参数 {field} 元素类型错误：应为 {item_type}"

        min_items = rule.get("minItems")
        if expected == "array" and isinstance(min_items, int) and isinstance(value, list):
            if len(value) < min_items:
                return f"参数 {field} 元素过少：至少 {min_items} 个"

    return None


def _to_tool_result(value: object) -> ToolResult:
    """把工具的返回值统一转换为 ToolResult。"""
    if isinstance(value, ToolResult):
        return value
    if isinstance(value, str):
        return ToolResult(success=True, output=value)
    return ToolResult(
        success=False,
        error_code="INVALID_TOOL_RESULT",
        error_message=f"工具必须返回 str 或 ToolResult，实际返回 {type(value).__name__}",
    )

def execute_tool(name: str, arguments: dict[str, object]) -> ToolResult:
    """按名称执行工具，将调用结果与异常统一转换为 ToolResult。"""
    if not isinstance(name, str) or not name.strip():
        return ToolResult(
            success=False,
            error_code="INVALID_ARGUMENTS",
            error_message="工具名称必须是非空字符串",
        )

    # 1. 查找函数，此时还没有执行工具。
    function = registry.get(name)
    if function is None:
        return ToolResult(
            success=False,
            error_code="TOOL_NOT_FOUND",
            error_message=f"工具不存在：{name}",
        )

    # 2. 检查参数容器。
    if not isinstance(arguments, dict):
        return ToolResult(
            success=False,
            error_code="INVALID_ARGUMENTS",
            error_message="arguments 必须是字典",
        )

    # 3. 获取函数签名；无法检查的工具不允许继续执行。
    try:
        tool_signature = signature(function)
    except (TypeError, ValueError) as exc:
        return ToolResult(
            success=False,
            error_code="TOOL_ERROR",
            error_message=f"无法检查工具签名：{exc}",
        )

    # 4. 检查是否缺少参数、多传参数，或者参数名不正确。
    try:
        tool_signature.bind(**arguments)
    except TypeError as exc:
        return ToolResult(
            success=False,
            error_code="INVALID_ARGUMENTS",
            error_message=str(exc),
        )

    # 5. 按 Schema 校验参数类型与范围；没有登记 Schema 的工具跳过这一步。
    schema = registry.get_schema(name)
    if schema is not None:
        schema_error = _validate_against_schema(schema, arguments)
        if schema_error is not None:
            return ToolResult(
                success=False,
                error_code="INVALID_ARGUMENTS",
                error_message=schema_error,
            )

    # 6. 真正执行并计时；工具内部异常与参数绑定错误分开处理。
    start = time.perf_counter()
    try:
        value = function(**arguments)
        result = _to_tool_result(value)
    except Exception as exc:
        result = ToolResult(
            success=False,
            error_code="TOOL_ERROR",
            error_message=f"{type(exc).__name__}: {exc}",
        )
    finally:
        duration_ms = (time.perf_counter() - start) * 1000

    # 7. 耗时由 Executor 统一填写；工具自己已填的则保留。
    if result.duration_ms is None:
        result.duration_ms = duration_ms
    return result