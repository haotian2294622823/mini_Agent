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
