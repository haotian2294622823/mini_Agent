from pathlib import Path
import os

class PathOutOfBoundsError(Exception):
    """自定义异常：当尝试访问工作区以外的路径时抛出"""
    pass

def resolve_workspace_path(workspace: str | Path, user_path: str | Path) -> Path:
    """安全地解析用户路径，确保最终路径位于工作区内。"""

    base_dir = Path(workspace).resolve()

    # 2. 剥离 user_path 开头的根目录符号 (防止直接传入绝对路径覆盖 base_dir)
    # 例如：把 '/etc/passwd' 变成 'etc/passwd'
    safe_user_path = str(user_path).lstrip(os.sep)
    # 如果在 Windows 上，最好同时处理正反斜杠
    safe_user_path = safe_user_path.lstrip('/').lstrip('\\')

    # 3. 路径拼接并解析成绝对路径
    target_path = base_dir / safe_user_path
    final_path = target_path.resolve()

    if not final_path.is_relative_to(base_dir):
        raise PathOutOfBoundsError(f"越界访问：目标位于工作区以外: {final_path}")

    return final_path
