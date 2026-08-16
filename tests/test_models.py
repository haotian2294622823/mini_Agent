"""共享数据模型的单元测试。"""

from dataclasses import asdict

from mini_agent.data_models import Message, ToolCall, ToolResult


def test_message_stores_role_and_content():
    message = Message(role="user", content="请读取 README.md")

    assert message.role == "user"
    assert message.content == "请读取 README.md"


def test_tool_call_stores_name_and_arguments():
    tool_call = ToolCall(name="read_file", arguments={"path": "README.md"})

    assert tool_call.name == "read_file"
    assert tool_call.arguments == {"path": "README.md"}


def test_tool_result_can_represent_success():
    result = ToolResult(success=True, output="文件内容")

    assert result.success is True
    assert result.output == "文件内容"
    assert result.error_code is None
    assert result.error_message is None


def test_tool_result_can_represent_failure():
    result = ToolResult(
        success=False,
        error_code="FILE_NOT_FOUND",
        error_message="文件不存在",
    )

    assert result.success is False
    assert result.output is None
    assert result.error_code == "FILE_NOT_FOUND"
    assert result.error_message == "文件不存在"


def test_data_model_can_convert_to_dictionary():
    tool_call = ToolCall(name="read_file", arguments={"path": "README.md"})

    assert asdict(tool_call) == {
        "name": "read_file",
        "arguments": {"path": "README.md"},
    }
