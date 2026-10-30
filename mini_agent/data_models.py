"""Mini SWE Agent 各模块之间共享的数据结构。"""

from dataclasses import dataclass


@dataclass
class Message:
    """表示一条发送给模型或由模型返回的消息。"""

    role: str
    content: str


@dataclass
class ToolCall:
    """表示模型请求执行一次工具。"""

    # name 决定调用哪个工具，例如 read_file。
    name: str

    # arguments 保存该工具本次调用所需的实际参数。
    arguments: dict[str, object]


@dataclass
class ToolResult:
    """所有工具统一使用的执行结果格式。"""

    success: bool
    output: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    # 单次工具调用耗时，单位毫秒；由 Executor 统一填充。
    duration_ms: float | None = None


class ErrorCode:
    """所有工具共用的标准错误码，集中定义便于统一复用与避免拼写错误。"""

    INVALID_COMMAND = "INVALID_COMMAND"
    COMMAND_NOT_ALLOWED = "COMMAND_NOT_ALLOWED"
    PATH_OUT_OF_BOUNDS = "PATH_OUT_OF_BOUNDS"
    TIMEOUT = "TIMEOUT"
    EXECUTABLE_NOT_FOUND = "EXECUTABLE_NOT_FOUND"
    NON_ZERO_EXIT = "NON_ZERO_EXIT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
