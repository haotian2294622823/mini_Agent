"""工具 Schema 的结构与 JSON 序列化测试。"""

import json

from mini_agent.tool_schemas import TOOLS


EXPECTED_REQUIRED_PARAMETERS = {
    "read_file": {"path"},
    "write_file": {"path", "content"},
    "list_files": {"path"},
    "grep": {"pattern", "path"},
    "run_command": {"command"},
}


def get_tool_schema(name: str) -> dict[str, object]:
    """按名称查找工具，避免测试依赖 TOOLS 的排列顺序。"""

    return next(tool for tool in TOOLS if tool["function"]["name"] == name)


def test_tools_is_a_list_with_expected_names():
    assert isinstance(TOOLS, list)

    actual_names = [tool["function"]["name"] for tool in TOOLS]

    # 比较集合可以发现缺失或计划外工具；比较长度可以发现重复名称。
    assert set(actual_names) == set(EXPECTED_REQUIRED_PARAMETERS)
    assert len(actual_names) == len(set(actual_names))


def test_every_tool_has_basic_function_schema():
    for tool in TOOLS:
        assert tool.get("type") == "function"
        assert "function" in tool

        function_info = tool["function"]
        assert isinstance(function_info.get("name"), str)
        assert function_info["name"]
        assert isinstance(function_info.get("description"), str)
        assert function_info["description"]
        assert "parameters" in function_info

        parameters = function_info["parameters"]
        assert parameters.get("type") == "object"
        assert isinstance(parameters.get("properties"), dict)
        assert isinstance(parameters.get("required"), list)
        assert parameters.get("additionalProperties") is False


def test_required_parameters_are_declared_in_properties():
    for tool_name, expected_required in EXPECTED_REQUIRED_PARAMETERS.items():
        tool = get_tool_schema(tool_name)
        parameters = tool["function"]["parameters"]
        properties = parameters["properties"]
        required = set(parameters["required"])

        assert required == expected_required
        assert required <= set(properties)


def test_read_file_path_is_a_required_string():
    read_file_schema = get_tool_schema("read_file")
    parameters = read_file_schema["function"]["parameters"]

    assert parameters["properties"]["path"]["type"] == "string"
    assert "path" in parameters["required"]


def test_tools_can_convert_to_json():
    json_text = json.dumps(TOOLS, ensure_ascii=False, indent=2)

    assert isinstance(json_text, str)
    assert "读取工作区" in json_text
