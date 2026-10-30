"""只测试注册与查询，不访问真实文件或执行系统命令。"""

import pytest

from mini_agent import registry

@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    # 每个测试使用独立字典；测试结束后自动恢复原注册表。
    monkeypatch.setattr(registry, "_tools", {})

def fake_tool(text: str) -> str:
    return f"收到：{text}"

def test_register_and_get():
    registry.register("echo", fake_tool)

    # is 验证查到的就是原来的函数对象。
    assert registry.get("echo") is fake_tool

def test_register_does_not_execute_tool():
    calls = []

    def tracked_tool() -> str:
        calls.append("called")
        return "完成"

    registry.register("tracked", tracked_tool)

    assert calls == []

def test_retrieved_tool_can_be_called():
    registry.register("echo", fake_tool)
    function = registry.get("echo")

    assert function is not None
    assert function(text="你好") == "收到：你好"

def test_duplicate_name_does_not_replace_original():
    registry.register("echo", fake_tool)

    def another_tool(text: str) -> str:
        return "另一个工具"

    with pytest.raises(ValueError, match="工具已注册"):
        registry.register("echo", another_tool)

    assert registry.get("echo") is fake_tool

def test_unknown_tool_returns_none():
    assert registry.get("missing") is None

def test_empty_registry_lists_no_tools():
    assert registry.list_tools() == []

def test_list_tools_returns_registered_names():
    registry.register("first", fake_tool)
    registry.register("second", fake_tool)

    assert registry.list_tools() == ["first", "second"]

def test_modifying_name_list_does_not_change_registry():
    registry.register("echo", fake_tool)

    names = registry.list_tools()
    names.clear()

    assert registry.list_tools() == ["echo"]

@pytest.mark.parametrize("name", ["", " ", "\t"])
def test_blank_name_is_rejected(name):
    with pytest.raises(ValueError, match="工具名称不能为空"):
        registry.register(name, fake_tool)

    assert registry.list_tools() == []

@pytest.mark.parametrize("name", [None, 123])
def test_non_string_name_is_rejected(name):
    with pytest.raises(TypeError, match="工具名称必须是字符串"):
        registry.register(name, fake_tool)

    assert registry.list_tools() == []

@pytest.mark.parametrize("function", [None, 123, "not a function"])
def test_non_callable_is_rejected(function):
    with pytest.raises(TypeError, match="工具必须是可调用对象"):
        registry.register("invalid", function)

    assert registry.list_tools() == []