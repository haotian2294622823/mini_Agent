"""使用假工具验证 Executor，不访问文件或执行系统命令。"""

import pytest

from mini_agent import registry
from mini_agent.data_models import ToolResult
from mini_agent.executor import execute_tool

@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    monkeypatch.setattr(registry, "_tools", {})
    monkeypatch.setattr(registry, "_schemas", {})

def test_execute_correct_tool():
    def echo(text: str) -> str:
        return f"收到：{text}"

    def other(text: str) -> str:
        return "不应该执行这个工具"

    registry.register("echo", echo)
    registry.register("other", other)

    result = execute_tool("echo", {"text": "你好"})

    assert result.success is True
    assert result.output == "收到：你好"
    assert result.error_code is None

def test_unknown_tool():
    result = execute_tool("missing", {})

    assert result.success is False
    assert result.error_code == "TOOL_NOT_FOUND"

@pytest.mark.parametrize("name", ["", None, []])
def test_invalid_tool_name(name):
    result = execute_tool(name, {})

    assert result.success is False
    assert result.error_code == "INVALID_ARGUMENTS"

@pytest.mark.parametrize(
    "arguments",
    [
        None,
        [],
        {},
        {"wrong_name": "你好"},
        {"text": "你好", "extra": 123},
        {1: "你好"},
    ],
)
def test_invalid_arguments_do_not_execute_tool(arguments):
    calls = []

    def echo(text: str) -> str:
        calls.append(text)
        return text

    registry.register("echo", echo)

    result = execute_tool("echo", arguments)

    assert result.success is False
    assert result.error_code == "INVALID_ARGUMENTS"
    assert calls == []

def test_optional_argument_uses_default():
    def greet(name: str = "访客") -> str:
        return f"你好，{name}"

    registry.register("greet", greet)

    result = execute_tool("greet", {})

    assert result.success is True
    assert result.output == "你好，访客"

@pytest.mark.parametrize("exception_type", [RuntimeError, TypeError])
def test_tool_exception_becomes_failure(exception_type):
    def broken() -> str:
        raise exception_type("模拟工具内部错误")

    registry.register("broken", broken)

    result = execute_tool("broken", {})

    assert result.success is False
    assert result.error_code == "TOOL_ERROR"
    assert "模拟工具内部错误" in result.error_message

@pytest.mark.parametrize("success", [True, False])
def test_preserves_existing_tool_result(success):
    expected = (
        ToolResult(success=True, output="完成")
        if success
        else ToolResult(
            success=False,
            error_code="FILE_NOT_FOUND",
            error_message="文件不存在",
        )
    )

    def structured_tool() -> ToolResult:
        return expected

    registry.register("structured", structured_tool)

    result = execute_tool("structured", {})

    assert result is expected

def test_invalid_return_type():
    def bad_tool():
        return 123

    registry.register("bad", bad_tool)

    result = execute_tool("bad", {})

    assert result.success is False
    assert result.error_code == "INVALID_TOOL_RESULT"


def test_tool_without_schema_skips_type_check():
    def loose(text) -> str:
        return f"收到：{text}"

    registry.register("loose", loose)

    result = execute_tool("loose", {"text": 123})

    assert result.success is True


TYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "count": {"type": "integer", "minimum": 1, "maximum": 10},
        "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    },
    "required": ["text"],
    "additionalProperties": False,
}


def _register_typed_tool():
    calls = []

    def typed(text: str, count: int = 1, tags: list | None = None) -> str:
        calls.append((text, count, tags))
        return "完成"

    registry.register("typed", typed, schema=TYPE_SCHEMA)
    return calls


def test_schema_valid_arguments_execute_tool():
    calls = _register_typed_tool()

    result = execute_tool("typed", {"text": "你好", "count": 5, "tags": ["a"]})

    assert result.success is True
    assert calls == [("你好", 5, ["a"])]


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"text": 123},
        {"text": "你好", "count": "5"},
        {"text": "你好", "count": 0},
        {"text": "你好", "count": 11},
        {"text": "你好", "tags": []},
        {"text": "你好", "tags": [1]},
        {"text": "你好", "unknown": 1},
        {"text": "你好", "count": True},
    ],
)
def test_schema_invalid_arguments_do_not_execute_tool(arguments):
    calls = _register_typed_tool()

    result = execute_tool("typed", arguments)

    assert result.success is False
    assert result.error_code == "INVALID_ARGUMENTS"
    assert calls == []


def test_tool_without_schema_skips_type_check():
    calls = _register_typed_tool.__wrapped__ if hasattr(_register_typed_tool, "__wrapped__") else None

    def loose(text) -> str:
        return f"收到：{text}"

    registry.register("loose", loose)

    result = execute_tool("loose", {"text": 123})

    assert result.success is True
    assert result.output == "收到：123"


def test_success_result_has_duration():
    def quick() -> str:
        return "完成"

    registry.register("quick", quick)

    result = execute_tool("quick", {})

    assert result.duration_ms is not None
    assert result.duration_ms >= 0


def test_failure_result_has_duration():
    def broken() -> str:
        raise RuntimeError("坏了")

    registry.register("broken", broken)

    result = execute_tool("broken", {})

    assert result.success is False
    assert result.duration_ms is not None
    assert result.duration_ms >= 0