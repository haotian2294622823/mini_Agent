"""发送给 LLM 的工具说明书。

这些 Schema 只描述工具的名称、用途和参数，不会真正执行文件或命令操作。
"""

import json


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取工作区内指定的 UTF-8 文本文件并返回文件内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对于工作区根目录的文件路径，例如 'README.md'。",
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "向工作区内指定路径写入 UTF-8 文本；文件存在时覆盖原内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对于工作区根目录的文件路径。",
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的完整文本内容。",
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出工作区内指定目录的直接子文件和子目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对于工作区根目录的目录路径；根目录使用 '.'。",
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "在工作区指定路径中搜索文本，并返回匹配的文件、行号和内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "要搜索的文本或模式。",
                    },
                    "path": {
                        "type": "string",
                        "description": "相对于工作区根目录的文件或目录路径。",
                    },
                },
                "required": ["pattern", "path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "在工作区内运行允许列表中的命令，并返回退出码、标准输出和标准错误。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "命令及参数列表，例如 ['pytest', '-q']。",
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 120,
                        "description": "命令的最大执行秒数；未提供时由程序使用默认值。",
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
]


if __name__ == "__main__":
    # 直接运行本文件时，以易读格式打印工具菜单。
    print(json.dumps(TOOLS, ensure_ascii=False, indent=2))
