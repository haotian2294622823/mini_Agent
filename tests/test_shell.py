"""shell.run_command 的单元测试。"""

import sys

from mini_agent.tools.shell import run_command

def test_success_command(tmp_path):
    """成功命令：python 能正常执行，退出码应为 0。"""
    result = run_command(tmp_path, [sys.executable, "-c", "print('hello')"])

    assert result.success is True
    assert "hello" in result.output
    assert "退出码: 0" in result.output

# 注意：白名单是 {"python", "pytest"}，而 sys.executable 可能是 python.exe，
# 若在 Windows 上白名单比对失败，把 ALLOWED_COMMANDS 改成用 stem 比对即可。

def test_failing_command(tmp_path):
    """失败命令：脚本以退出码 2 结束，success 应为 False。"""
    result = run_command(tmp_path, [sys.executable, "-c", "import sys; sys.exit(2)"])

    assert result.success is False
    assert result.error_code == "NON_ZERO_EXIT"
    assert "退出码: 2" in result.output

def test_command_not_allowed(tmp_path):
    """非白名单命令：应被拦截，不执行。"""
    result = run_command(tmp_path, ["rm", "-rf", "."])

    assert result.success is False
    assert result.error_code == "COMMAND_NOT_ALLOWED"

def test_timeout_command(tmp_path):
    """超时命令：应触发 TIMEOUT。"""
    result = run_command(
        tmp_path,
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout_seconds=1,
    )

    assert result.success is False
    assert result.error_code == "TIMEOUT"

def test_empty_command(tmp_path):
    """空命令：应被输入校验拦截。"""
    result = run_command(tmp_path, [])

    assert result.success is False
    assert result.error_code == "INVALID_COMMAND"