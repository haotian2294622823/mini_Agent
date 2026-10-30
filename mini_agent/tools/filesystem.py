from pathlib import Path
from .path_guard import resolve_workspace_path, PathOutOfBoundsError


def read_file(workspace: str | Path, file_path: str | Path) -> str:
    "读取指定文件夹内容，仅支持UTF-8编码的文本文件"
    try:
        safe_path = resolve_workspace_path(workspace, file_path)

        if not safe_path.exists():
            return f"读取失败：找不到路径 '{file_path}'"

        if safe_path.is_dir():
            return f"读取失败：'{file_path}' 是一个目录，不能当做文本读取"

        if not safe_path.is_file():
            return f"读取失败：'{file_path}' 是一种特殊文件（如管道、设备或套接字），无法读取"

        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()

    except PathOutOfBoundsError as e:
        # 捕获 resolve_workspace_path 抛出的越界异常
        return str(e)
    except UnicodeDecodeError:
        # 捕获由于强行用 utf-8 读取二进制文件（如图片、PDF）引发的乱码崩溃
        return (
            f"读取失败：'{file_path}' 包含无法解析的二进制数据，当前仅支持 UTF-8 文本。"
        )
    except Exception as e:
        # 终极兜底：处理其他所有意料之外的错误（比如操作系统的权限不足）
        return f"读取时发生未知错误: {str(e)}"


def list_files(workspace: str | Path, dir_path: str | Path) -> str:
    try:
        safe_path = resolve_workspace_path(workspace, dir_path)

        # 2. 安检门：确认它确实是个目录
        if not safe_path.exists():
            return f"列出失败：找不到目录 '{dir_path}'"
        if not safe_path.is_dir():
            return f"列出失败：'{dir_path}' 是一个文件，不是目录"

        # 3. 列出目录内容
        items = list(safe_path.iterdir())
        if not items:
            return f"目录 '{dir_path}' 是空的"

        folders = [f"{item.name}/" for item in items if item.is_dir()]
        files = [item.name for item in items if item.is_file()]
        folders.sort()
        files.sort()

        # 结构化文本返回
        output_lines = []
        if folders:
            output_lines.append("[文件夹]")
            output_lines.extend(folders)
        if files:
            output_lines.append("[文件]")
            output_lines.extend(f"  {f}" for f in files)
        return "\n".join(output_lines)

    except PathOutOfBoundsError as e:
        return str(e)
    except Exception as e:
        return f"列出目录时发生未知错误: {str(e)}"

def grep(workspace: str | Path, pattern: str, path: str | Path) -> str:
    "指定文件或目录下搜索关键字，返回匹配的文件名、行号、内容"
    if not pattern:
        return "搜索失败：关键字不能为空"
    
    try:
        safe_path = resolve_workspace_path(workspace, path)
        base_dir = Path(workspace).resolve()

        if not safe_path.exists():
            return f"搜索失败：找不到路径 '{path}'"

        if safe_path.is_file():
            target_files = [safe_path]
        elif safe_path.is_dir():
            target_files = sorted(p for p in safe_path.rglob("*") if p.is_file())
        else:
            return f"搜索失败：'{path}' 不是普通文件，无法搜索"

        results = []
        for file in target_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for line_number, line in enumerate(f, start=1):
                        if pattern in line:
                            relative_path = file.relative_to(base_dir)
                            results.append(f"{relative_path}:{line_number}:{line.strip()}")
            except UnicodeDecodeError:
                # 跳过无法解码的文件
                continue

        if not results:
            return f"搜索完成：在 '{path}' 下未找到匹配 '{pattern}' 的内容"
        return "\n".join(results)
    except PathOutOfBoundsError as e:
        return str(e)
    except Exception as e:
        return f"搜索时发生未知错误: {str(e)}"