"""受限制的命令执行工具。

只允许运行白名单中的可执行文件，禁止用 shell 解释器执行任意字符串。
"""
import subprocess
import time
from pathlib import Path

from .path_guard import resolve_workspace_path, PathOutOfBoundsError
from ..data_models import ToolResult, ErrorCode

ALLOWED_COMMANDS = {"python","pytest"}
DEFAULT_TIMEOUT = 30  
MAX_OUTPUT_SIZE = 10000  # 最大输出字符数限制

def _truncate(text: str, limit: int = MAX_OUTPUT_SIZE) -> str:
    """输出过长时只保留开头和结尾，中间写明已截断。"""
    if not text:
        return ""
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    omitted = len(text) - limit
    return f"{text[:head]}\n... [输出被截断，省略了 {omitted} 个字符] ...\n{text[-tail:]}"


def run_command(
    workspace_path: str | Path,
    command: list[str],
    timeout_seconds: int = DEFAULT_TIMEOUT,
) -> ToolResult:
    """在工作区内运行白名单命令，返回统一的 ToolResult 对象。"""

    # 1. 校验输入非空
    if not isinstance(command, list) or not command:
        return ToolResult(
            success=False,
            error_code=ErrorCode.INVALID_COMMAND,
            error_message="command 必须是非空字符串列表，例如 ['pytest', '-q']。",
        )
    if not all(isinstance(part, str) for part in command):
        return ToolResult(
            success=False,
            error_code=ErrorCode.INVALID_COMMAND,
            error_message="command 列表中的每个元素必须是字符串。",
        )

    # 2. 白名单检查：只比可执行文件名，防止传 "C:/evil/python.exe"
    executable = Path(command[0]).stem
    if executable not in ALLOWED_COMMANDS:
        return ToolResult(
            success=False,
            error_code=ErrorCode.COMMAND_NOT_ALLOWED,
            error_message=f"命令 '{executable}' 不在允许的白名单中。",
        )

    # 3. 解析工作区路径，防止越界访问
    try:
        working_dir = resolve_workspace_path(workspace_path, ".")
    except PathOutOfBoundsError as e:
        return ToolResult(
            success=False,
            error_code=ErrorCode.PATH_OUT_OF_BOUNDS,
            error_message=str(e),
        )
    # 4. 执行并计时
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            shell=False,  # 关键：不经 shell，杜绝命令注入
            cwd=working_dir,  # 限定工作目录
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(
            success=False,
            error_code=ErrorCode.TIMEOUT,
            error_message=f"命令超过 {timeout_seconds} 秒未结束，已强制终止。耗时 {duration_ms} ms。",
        )
    except FileNotFoundError:
        return ToolResult(
            success=False,
            error_code=ErrorCode.EXECUTABLE_NOT_FOUND,
            error_message=f"找不到可执行文件 '{command[0]}'。",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error_code=ErrorCode.UNKNOWN_ERROR,
            error_message=f"执行命令时发生未知错误: {str(e)}",
        )

    duration_ms = int((time.perf_counter() - started) * 1000)

    # 5. exit_code / duration_ms 装进 output（ToolResult 没有这两个字段）
    output = "\n".join(
        [
            f"退出码: {completed.returncode}",
            f"耗时: {duration_ms} ms",
            "--- stdout ---",
            _truncate(completed.stdout),
            "--- stderr ---",
            _truncate(completed.stderr),
        ]
    )
    return ToolResult(
        success=(completed.returncode == 0),
        output=output,
        error_code=None if completed.returncode == 0 else ErrorCode.NON_ZERO_EXIT,
        error_message=None if completed.returncode == 0 else f"命令以退出码 {completed.returncode} 结束。",
    )