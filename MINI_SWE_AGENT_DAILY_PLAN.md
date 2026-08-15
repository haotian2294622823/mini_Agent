# Mini SWE Agent：28 天从零实现「可靠性优先」代码 Agent

> 目标：不使用 LangChain、LangGraph、CrewAI、Strands 等 Agent 框架，使用 Python 从零实现一个最小、可验证、可恢复的代码 Agent。
>
> 项目定位不是再做一个通用 Agent Framework，而是做一个 **Verification-first、Reliability-first Coding Agent**。
>
> 建议投入：工作日每天 1～1.5 小时，周末每天 2～3 小时。学习与写代码的时间比例约为 **3:7**。

---

## 一、项目要回答的四个问题

1. Agent 说“完成”时，任务真的完成了吗？
2. LLM、工具或测试失败后，系统能否恢复，而不是直接崩溃？
3. 每次修改和执行是否可追踪、可审计？
4. 一个失败任务能否通过历史 Trace 定位到具体失败步骤？

整个项目围绕四个关键词展开：

```text
Verification
Recovery
Trace
Evaluation
```

项目最终定位：

> **A verification-first coding agent built from scratch, with explicit completion checks, failure recovery, execution traces and reproducible evaluation.**

---

## 二、最终要做成什么

完成后，`mini-swe-agent` 应该能够：

```text
接收代码任务
→ 调用 LLM 分析任务
→ 选择并调用工具
→ 读取或搜索项目文件
→ 修改代码
→ 运行 pytest
→ Verifier 检查结果
→ 验证失败时根据证据重新规划
→ 验证通过后输出任务总结
```

至少实现以下 5 个工具：

- `read_file`：读取文件
- `write_file`：创建或修改文件
- `list_files`：列出目录中的文件
- `grep`：搜索代码内容
- `run_command`：运行经过限制的命令

项目重点不是代码量，而是理解以下问题：

1. Agent Loop 为什么需要循环？
2. LLM 如何决定调用哪个工具？
3. 工具执行结果如何进入下一轮 Context？
4. 谁来判断任务是否真正完成？
5. 工具报错、测试失败或循环失控时怎么办？

### 普通 Agent Demo 与本项目的区别

普通 Demo 可能这样结束：

```text
LLM 说“已经完成”
→ Finish
```

本项目要求：

```text
Agent 修改代码
→ 执行测试
→ Verifier 检查测试完整性和执行结果
→ PASS 后才允许 SUCCESS
```

如果验证失败：

```text
VERIFICATION_FAILED
→ 保存失败证据
→ Re-plan
→ 再次修改
→ 再次验证
→ 超出限制后明确结束为 FAILED
```

---

## 三、范围与优先级

为了保证 28 天能够完成，把功能分为两个优先级。

### P0：必须完成

- Agent Loop
- 5 个基础工具
- 工作区路径边界
- 安全的命令执行
- Task Contract
- Task Status
- Verifier 与测试防篡改
- Failure Type 与 Recovery Policy
- 有限 Retry、最大步数和 Timeout
- Execution Trace 与持久化
- 5 个固定评测任务
- README、架构图和稳定 Demo

### P1：完成 P0 后再做

- Snapshot / Rollback
- Risk-based Human Approval
- Trace 查看命令
- 8～12 个评测任务
- Baseline 对比实验
- 真正的确定性 Replay

> 如果某天没有完成，不要通过跳过测试来追赶进度。顺延当天任务，并优先保证 P0 主线完整。

---

## 四、关键设计约定

这些约定会在后面的每日任务中逐步实现。

### 1. Task Contract

Agent 开始执行前，必须知道任务范围和成功条件。

```text
TaskSpec
├── task_id
├── task_type
├── instruction
├── workspace
├── allowed_paths
├── allowed_commands
├── protected_paths
├── success_checks
├── max_steps
└── timeout_seconds
```

任务结束时，统一返回：

```text
TaskResult
├── task_id
├── status
├── reason
├── changed_files
├── verification_result
├── total_steps
└── trace_id
```

第一版可以使用 `dataclass` 或 `TypedDict`，不需要设计复杂的类继承体系。

### 2. Task Status

至少支持：

```text
PENDING
RUNNING
WAITING_APPROVAL
VERIFYING
SUCCESS
FAILED
CANCELLED
```

关键规则：

> LLM 返回最终回答只代表“模型想结束”，不代表任务已经成功。

### 3. Tool Result

所有工具返回统一的结构化结果：

```text
ToolResult
├── success
├── output
├── error_code
├── error_message
├── metadata
└── duration_ms
```

其中 `metadata` 可以保存退出码、输出是否被截断、修改的文件等信息。

### 4. Verifier

Coding Task 的第一版验证规则：

```text
pytest exit_code == 0
AND tests_collected > 0
AND protected test files 未被修改
AND 没有越过 workspace 边界
AND TaskSpec.success_checks 全部通过
```

仅检查 `pytest exit_code == 0` 不够，因为 Agent 可能删除测试、修改断言或让 pytest 没有收集到测试。

### 5. 安全命令执行

不要把任意字符串直接交给 Shell。第一版使用参数列表：

```python
subprocess.run(
    ["pytest", "-q"],
    shell=False,
    cwd=workspace,
    timeout=60,
    capture_output=True,
    text=True,
)
```

第一版只允许少量命令，例如：

```text
pytest
python
ruff（可选）
mypy（可选）
```

---

## 五、每日固定流程

每天按照下面的节奏执行，避免只看教程、不写代码：

1. **10～20 分钟：学习**当天涉及的 Python 或 Agent 概念。
2. **40～90 分钟：编码**，只完成当天的核心任务。
3. **10～20 分钟：测试**正常情况和至少一个异常情况。
4. **5 分钟：记录**今天完成了什么、遇到什么问题、明天做什么。

每天结束前，在开发日志中写下：

```markdown
## YYYY-MM-DD

- 今天完成：
- 我理解了：
- 遇到的问题：
- 明天第一步：
```

---

# 第 1 周：跑通最小 Agent 闭环

## Day 1：搭建项目并跑通 LLM Client

### 学习

- Python 虚拟环境与依赖安装
- 环境变量的作用
- HTTP API 的请求与响应
- 为什么 API Key 不能写入代码或提交到 Git

### 动手

- [ ] 创建基础目录结构
- [ ] 创建虚拟环境并安装依赖
- [ ] 添加 `.gitignore` 和 `.env.example`
- [ ] 编写最小 LLM Client
- [ ] 向模型发送 `Hello` 并打印响应

### 新手执行顺序

1. 在 PowerShell 中确认 Python 已安装：

   ```powershell
   python --version
   ```

   建议使用 Python 3.11 或 3.12。只要命令能输出版本号，就先继续，不用纠结小版本。

2. 创建并激活虚拟环境：

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. 创建 `mini_agent/`、`tests/`、`evals/` 和 `examples/`。在 `mini_agent/` 中添加空的 `__init__.py`。
4. 创建 `.env.example`，只写变量名，例如 `LLM_API_KEY=`、`LLM_MODEL=`，不要写真实 Key。
5. 在 `mini_agent/llm_client.py` 中先只实现一个职责：接收消息并返回模型文本。不要在这里加入 Agent Loop。
6. 创建一个临时入口文件，调用 Client 并打印结果。
7. 成功后再故意删除或写错 API Key，观察错误是否清楚。

### 当天产物

- `mini_agent/__init__.py`
- `mini_agent/llm_client.py`
- `.env.example`
- `.gitignore`
- `pyproject.toml`
- 一次成功的模型响应截图或开发日志

### 卡住时先检查

- `python` 是否来自刚创建的 `.venv`。
- 真实 `.env` 是否被 `.gitignore` 忽略。
- Key、模型名称和 Base URL 是否与所选模型服务一致。
- 先只打印响应类型，不要猜测 SDK 返回对象的字段。

建议目录：

```text
mini-swe-agent/
├── mini_agent/
│   ├── __init__.py
│   └── llm_client.py
├── tests/
├── evals/
├── examples/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

### 完成标准

- 程序能成功获得一次模型响应。
- API Key 只从环境变量读取。
- API 请求失败时能显示清晰错误，而不是直接崩溃。

---

## Day 2：设计消息、Tool Schema 和 ToolResult

### 学习

- Python `dict`、`list` 和类型注解
- JSON 序列化与反序列化
- Structured Output 与 Tool Calling 的基本原理

### 动手

- [ ] 定义消息结构：`role`、`content`
- [ ] 定义工具的名称、用途和参数 Schema
- [ ] 为 5 个工具写出 Tool Schema
- [ ] 定义统一的 `ToolResult`
- [ ] 验证这些结构可以转换为 JSON

### 新手执行顺序

1. 创建 `mini_agent/models.py`，先定义 `ToolResult`。第一版可以用 `dataclass`，字段只保留当天真正需要的内容。
2. 创建 `mini_agent/tool_schemas.py`，先写 `read_file` 的 Schema，再模仿它写其他 4 个。
3. 为每个工具写一句明确描述，例如 `read_file` 是“读取工作区内的 UTF-8 文本文件”，不要只写“读取文件”。
4. 把所有 Schema 放进一个列表，使用 `json.dumps(..., ensure_ascii=False, indent=2)` 打印检查。
5. 创建 `tests/test_models.py`，验证 `ToolResult` 能表达成功和失败两种情况。
6. 给一个工具故意删掉必填参数，确认你的参数检查能够发现问题。

### 当天产物

- `mini_agent/models.py`
- `mini_agent/tool_schemas.py`
- `tests/test_models.py`

### 验收命令

```powershell
python -m pytest tests/test_models.py -q
```

如果测试失败，先打印实际对象和预期对象，逐个比较字段，不要立刻重写整个数据结构。

### 完成标准

- 每个工具的名称、描述、必填参数都清楚。
- 非法参数可以被识别，不会直接传给执行函数。
- 能解释“工具定义”“工具执行函数”和“工具结果”的区别。

---

## Day 3：实现工作区边界、`read_file` 和 `list_files`

### 学习

- `pathlib.Path`
- 文件编码与 UTF-8
- 相对路径、绝对路径和规范化路径
- `../` 路径穿越与符号链接风险

### 动手

- [ ] 实现统一的工作区路径检查函数
- [ ] 实现 `read_file(path)`
- [ ] 实现 `list_files(path)`
- [ ] 处理文件不存在、路径错误和读取目录等异常
- [ ] 限制工具只能访问指定工作区

### 新手执行顺序

1. 创建 `mini_agent/tools/__init__.py`、`mini_agent/tools/path_guard.py` 和 `mini_agent/tools/filesystem.py`。
2. 先在 `path_guard.py` 中实现 `resolve_workspace_path(workspace, user_path)`：
   - 把工作区和用户路径转换成绝对路径；
   - 解析 `..`；
   - 检查最终路径仍在工作区内；
   - 越界时抛出你能识别的异常。
3. 在 `filesystem.py` 中实现 `read_file`，只读取 UTF-8 文本；暂时不要支持二进制文件。
4. 再实现 `list_files`，第一版只列一层目录，避免一次返回几千个文件。
5. 在 `tests/` 中使用 pytest 的 `tmp_path` 创建临时工作区，不要拿自己的真实文件做破坏性测试。
6. 按顺序测试：正常文件、中文文件、不存在文件、把目录当文件、`../outside.txt`。

### 当天产物

- `mini_agent/tools/path_guard.py`
- `mini_agent/tools/filesystem.py`
- `tests/test_filesystem.py`

### 验收命令

```powershell
python -m pytest tests/test_filesystem.py -q
```

如果越界检查一直写不对，先只处理普通路径；符号链接测试可以记入 TODO，但 `..` 越界必须当天拦住。

### 完成标准

- 能读取工作区中的 Python 文件。
- 能列出指定目录内容。
- 尝试访问工作区外的文件时会被拒绝。
- 至少覆盖正常读取、文件不存在、目录误读和越界路径测试。

---

## Day 4：实现 `grep` 和安全的 `run_command`

### 学习

- `subprocess.run`
- 标准输出、标准错误和退出码
- `shell=False` 的意义
- 命令超时和命令注入风险

### 动手

- [ ] 实现 `grep(pattern, path)`
- [ ] 让 `run_command` 接收参数列表，而不是任意 Shell 字符串
- [ ] 设置允许的可执行命令和工作目录
- [ ] 返回 `stdout`、`stderr`、`exit_code` 和 `duration_ms`
- [ ] 增加 Timeout 和输出长度限制

### 新手执行顺序

1. 在 `filesystem.py` 中先实现纯 Python 版 `grep`：遍历允许的文本文件，逐行判断是否包含关键字，并返回文件名与行号。
2. 创建 `mini_agent/tools/shell.py`。
3. 把命令输入定义成列表，例如 `["pytest", "-q"]`，不要接收 `"pytest -q"` 这种整段字符串。
4. 写一个允许列表，第一版只接受 `python` 和 `pytest`。
5. 调用 `subprocess.run` 时设置 `shell=False`、`cwd`、`timeout`、`capture_output=True` 和 `text=True`。
6. 把 `stdout`、`stderr`、退出码和耗时装进 `ToolResult`。
7. 如果输出过长，只保留开头和结尾，并在中间写明已截断。
8. 分别测试成功命令、失败命令、非白名单命令和超时命令。

### 当天产物

- 更新后的 `mini_agent/tools/filesystem.py`
- `mini_agent/tools/shell.py`
- `tests/test_grep.py`
- `tests/test_shell.py`

### 验收命令

```powershell
python -m pytest tests/test_grep.py tests/test_shell.py -q
```

如果 `subprocess` 让你困惑，先只实现专用的 `run_tests()`，固定执行 `["pytest", "-q"]`；理解后再抽象成 `run_command()`。

### 完成标准

- 能搜索项目中的函数名或关键字。
- 能运行 `python --version` 和 `pytest`。
- 命令不存在、超时或退出码非 0 时主程序不会崩溃。
- 非白名单命令会被拒绝。

---

## Day 5：实现 Tool Registry 和 Executor

### 学习

- Python 函数也是对象
- 字典映射和函数分发
- 参数校验与异常处理

### 动手

- [ ] 用字典注册工具名称和执行函数
- [ ] 实现统一入口 `execute_tool(name, arguments)`
- [ ] 检查工具是否存在
- [ ] 检查参数是否合法
- [ ] 捕获工具异常并转换为 `ToolResult`

### 新手执行顺序

1. 创建 `mini_agent/registry.py`，先用一个普通字典保存 `{工具名: 函数}`。
2. 实现 `register(name, function)`，重复名称要报错。
3. 实现 `get(name)` 和 `list_tools()`。
4. 创建 `mini_agent/executor.py`，实现 `execute_tool(name, arguments)`。
5. Executor 的固定顺序是：查找工具 → 校验参数 → 调用工具 → 计时 → 捕获错误 → 返回 `ToolResult`。
6. 不要让工具自己打印最终结果；统一由调用者处理返回值。
7. 使用一个假的工具函数测试 Registry，不需要每个测试都碰真实文件或命令。

### 当天产物

- `mini_agent/registry.py`
- `mini_agent/executor.py`
- `tests/test_registry.py`
- `tests/test_executor.py`

### 验收命令

```powershell
python -m pytest tests/test_registry.py tests/test_executor.py -q
```

当天结束前，尝试口头解释：为什么 Agent 只依赖 Executor，而不应该直接导入每一个工具函数？

### 完成标准

- Executor 能按名称调用正确工具。
- 未知工具、错误参数和工具异常都有结构化结果。
- 新增工具时不需要修改 Agent Loop。

---

## Day 6：实现第一版 Agent Loop

### 学习

- `while` 循环和退出条件
- Reason → Act → Observe 循环
- Observation 为什么必须进入下一轮 Context

### 动手

- [ ] 接收用户任务并加入消息列表
- [ ] 调用 LLM
- [ ] 解析普通回复或工具调用
- [ ] 调用 Executor
- [ ] 把 ToolResult 作为 Observation 放回消息列表
- [ ] 设置最大循环次数，例如 10 次

### 新手执行顺序

1. 创建 `mini_agent/agent.py`，先画伪代码，不急着写完整 Python：

   ```text
   保存用户任务
   while step < max_steps:
       请求模型
       如果模型要调用工具：执行并保存结果
       否则：保存最终回答并退出
   超出步数：失败退出
   ```

2. 把循环需要的依赖通过参数传入，例如 LLM Client 和 Executor，避免在函数内部创建全局对象。
3. 第一次只支持一轮一个 Tool Call；并行工具调用留到以后。
4. 把 `ToolResult` 转换成模型能理解的 Observation 消息。
5. 每轮打印简单信息：当前 Step、模型动作、工具结果状态。
6. 创建一个 Fake LLM：第一次固定返回 `list_files`，第二次固定返回最终答案。先用它验证循环，再接真实模型。
7. 测试达到最大步数时能退出。

### 当天产物

- `mini_agent/agent.py`
- `tests/test_agent_loop.py`
- 一个不依赖真实 API 的 Fake LLM 测试

### 验收命令

```powershell
python -m pytest tests/test_agent_loop.py -q
```

如果真实模型不按预期调用工具，先确认 Fake LLM 测试通过。这样可以判断问题在 Agent Loop，还是在 Prompt/模型输出。

### 完成标准

- Agent 能根据任务主动调用一个只读工具。
- 工具结果能影响下一轮模型决策。
- 达到最大步数时会停止，不会无限循环。
- 暂时允许模型请求结束，但还不能把它当作可靠的 `SUCCESS`。

---

## Day 7：第一周复盘与只读演示

### 动手

- [ ] 运行全部测试并修复失败项
- [ ] 用一个示例项目测试完整只读流程
- [ ] 画出当前 Agent Loop 架构图
- [ ] 更新 README 的安装和运行方法
- [ ] 记录本周最大的 3 个问题

### 新手执行顺序

1. 先运行整个测试套件，不要边看边猜：

   ```powershell
   python -m pytest -q
   ```

2. 按“最早出现的失败”逐个修复。前一个错误可能导致后面很多连锁失败。
3. 在 `examples/read_only_demo/` 创建 2～3 个简单 Python 文件。
4. 用 Fake LLM 跑一次完整演示，再用真实模型跑三次。
5. 在 README 中写出安装、配置、运行和测试四组命令。
6. 用 Mermaid 或纯文本画出 `User → LLM → Executor → Tool → Observation → LLM`。
7. 在 `DEVLOG.md` 写本周三个问题，并分别标记“已解决”或“下周处理”。

### 当天产物

- `examples/read_only_demo/`
- 初版 `README.md`
- `DEVLOG.md`
- 第一版架构图

### 本周不要继续加功能

如果只读 Demo 还不稳定，不要提前实现 `write_file`。先保证已有链路可以重复运行并且错误可定位。

### 演示任务

```text
请列出项目中的 Python 文件，读取其中一个文件，
然后告诉我这个文件的主要作用。不要修改文件。
```

### 完成标准

- 按照 README 可以启动项目。
- 演示任务至少连续成功运行 3 次。
- 能不用看代码讲清楚 Agent Loop 的运行过程。

---

# 第 2 周：安全修改、Task Contract 与 Verifier

## Day 8：实现安全、原子的 `write_file`

### 学习

- 文件覆盖风险
- 原子写入的基本思想
- 工作区边界和受保护文件

### 动手

- [ ] 实现 `write_file(path, content)`
- [ ] 写入临时文件成功后再替换目标文件
- [ ] 拒绝写入工作区之外
- [ ] 拒绝写入 `.env` 等敏感文件
- [ ] 返回修改路径、字符数和修改状态
- [ ] 为新建、覆盖、失败写入和非法路径编写测试

### 新手执行顺序

1. 在 `filesystem.py` 中复用 Day 3 的路径检查函数，不要为写文件重新写一套边界逻辑。
2. 先实现“新建文件”，确认父目录不存在时是拒绝还是主动创建，并把规则写进测试。
3. 再实现“覆盖文件”：先把新内容写到同目录临时文件，写入成功后再替换目标文件。
4. 建立 `protected_paths`，至少保护 `.env`、`.git/` 和评测测试目录。
5. 写入成功后返回 `changed=True`；新旧内容相同时返回 `changed=False`，避免无意义修改。
6. 使用 `tmp_path` 测试新建、覆盖、内容不变、编码错误、越界路径和受保护路径。

### 当天产物

- 更新后的 `mini_agent/tools/filesystem.py`
- `tests/test_write_file.py`

### 验收命令

```powershell
python -m pytest tests/test_write_file.py -q
```

今天先让写入行为“安全且可预测”。展示 Diff 和自动备份放在后面，不要一次把所有功能塞进 `write_file`。

### 完成标准

- Agent 可以创建和修改测试文件。
- `../` 等越界路径会被拒绝。
- 写入中途失败时不会留下半个文件或破坏原文件。

---

## Day 9：定义 TaskSpec 和 TaskResult

### 学习

- `dataclass` 或 `TypedDict`
- 输入约束和输出契约
- 为什么可靠验证需要预先定义成功条件

### 动手

- [ ] 定义 `TaskSpec`
- [ ] 定义 `TaskResult`
- [ ] 区分只读任务与代码修改任务
- [ ] 为代码任务配置工作区、保护路径和验证命令
- [ ] 为任务设置最大步数和总 Timeout

### 新手执行顺序

1. 在 `models.py` 中先定义 `TaskStatus` 枚举，但当天不必实现完整状态转换。
2. 使用 `dataclass` 定义 `TaskSpec`，为 `max_steps` 和 `timeout_seconds` 提供默认值。
3. 定义 `TaskResult`，其中 `status` 和 `reason` 必填，其他字段可以有默认值。
4. 创建一个只读 TaskSpec，成功条件是“产生最终说明”。
5. 创建一个代码修改 TaskSpec，成功条件是“受保护测试通过”。
6. 对非法配置做校验，例如 `max_steps <= 0`、工作区不存在、保护路径在工作区外。
7. 写测试确认对象可以转换为字典或 JSON，以便以后保存 Trace。

### 当天产物

- 更新后的 `mini_agent/models.py`
- `tests/test_task_models.py`
- `examples/task_specs.py` 或两个 JSON 示例

### 验收命令

```powershell
python -m pytest tests/test_task_models.py -q
```

如果字段设计拿不准，先问自己：“Verifier 判断成功时真的会用到这个字段吗？”暂时用不到的字段先不加。

### 完成标准

- Agent 执行前可以打印任务范围和成功条件。
- 不同任务可以使用不同的 `success_checks`。
- 任务结束时总能返回结构一致的 `TaskResult`。

---

## Day 10：改进 Prompt、工具选择和解析器

### 学习

- System Prompt 的职责
- 工具描述对工具选择的影响
- 模型输出不完整或格式错误的常见情况
- 防御式编程

### 动手

- [ ] 编写简短的 System Prompt
- [ ] 要求 Agent 先查看相关代码，再修改文件
- [ ] 要求代码修改后必须请求验证
- [ ] 检查工具名、参数类型和必填参数
- [ ] 处理空参数、未知字段和损坏的 JSON
- [ ] 准备 5 个任务观察工具选择是否合理

### 新手执行顺序

1. 创建 `mini_agent/prompts.py`，把 System Prompt 从 `agent.py` 移出来。
2. Prompt 第一版只写 5 条规则：先调查、按需调用工具、遵守工作区、修改后验证、无法完成时明确失败。
3. 创建 `mini_agent/parser.py`，把模型响应统一解析成 `ToolAction` 或 `FinalAnswer`。
4. 为 Parser 准备固定输入，不要每个解析测试都请求真实模型。
5. 依次测试：合法 Tool Call、普通最终回答、未知工具、缺少必填参数、损坏 JSON。
6. 准备 5 个选择题式任务观察模型行为，例如“只解释文件”“查找函数”“修复 Bug”“运行测试”“读取工作区外文件”。
7. 把每次选择是否正确记录在 `DEVLOG.md`，先不要急着反复修改 Prompt。

### 当天产物

- `mini_agent/prompts.py`
- `mini_agent/parser.py`
- `tests/test_parser.py`
- 一张 5 个任务的工具选择记录表

### 验收命令

```powershell
python -m pytest tests/test_parser.py -q
```

如果模型选错工具，先检查工具描述是否含糊，再检查 Prompt。不要立刻在 Agent Loop 里写大量 `if` 强行纠正模型。

### 完成标准

- 只读任务不会调用 `write_file`。
- 修改任务会先读取相关代码。
- 错误模型输出不会导致程序崩溃。
- 每条 Prompt 规则都有明确目的。

---

## Day 11：准备隔离、可重复的评测项目

### 学习

- 测试夹具（fixture）的基本概念
- 为什么每次评测前必须恢复相同初始状态
- Agent 自身测试与被修复项目测试的区别

### 动手

- [ ] 创建一个很小的 Python 示例项目
- [ ] 故意放入 3 个简单 Bug
- [ ] 为每个 Bug 编写会失败的 pytest
- [ ] 把评测测试设为受保护路径
- [ ] 为每个评测任务准备干净副本或初始化脚本
- [ ] 记录任务预期修改和成功条件

### 新手执行顺序

1. 在 `evals/fixtures/` 下创建三个独立小项目：`calculator_bug`、`average_bug`、`text_bug`。
2. 每个项目只保留一个源文件和一个测试文件，控制在几十行内。
3. 先写正确测试，再故意改坏源代码；不要让 Agent 面对含糊需求。
4. 手动运行每个项目的 pytest，确认修改前确实失败。
5. 手动修复一次并确认测试通过，然后恢复成 Bug 初始状态。
6. 把测试目录加入 `protected_paths`。
7. 创建 `evals/tasks/`，为每个任务记录：用户指令、工作区、允许修改路径、保护路径和验证命令。
8. 先用复制目录的方式生成每次运行的工作副本；暂时不用 Docker 或复杂 Git 操作。

### 当天产物

- `evals/fixtures/calculator_bug/`
- `evals/fixtures/average_bug/`
- `evals/fixtures/text_bug/`
- `evals/tasks/` 中的 3 个任务定义

### 验收命令

在每个 fixture 目录中运行：

```powershell
python -m pytest -q
```

初始状态应该稳定失败。如果偶尔成功，说明评测任务本身不可靠，应先修任务，不要继续开发 Agent。

### 完成标准

- 修改前测试稳定失败，正确修复后稳定通过。
- 每次评测都从相同初始状态开始。
- Agent 无法修改评测测试文件。

---

## Day 12：让 Agent 自动运行 pytest

### 学习

- pytest 输出结构
- 测试通过、断言失败、收集失败和无测试的区别

### 动手

- [ ] 引导 Agent 在修改后运行 pytest
- [ ] 返回退出码、测试收集数量和精简后的输出
- [ ] 保留错误输出开头、结尾和截断标记
- [ ] 测试失败时把证据送回 Agent

### 新手执行顺序

1. 先让 `run_command(["pytest", "-q"], ...)` 能在一个 fixture 工作副本中运行。
2. 在 `ToolResult.metadata` 中加入 `exit_code`、`timed_out` 和 `output_truncated`。
3. 从 pytest 输出中提取测试收集数量。第一版可以采用简单、可测试的解析规则，不需要支持所有 pytest 插件格式。
4. 把失败测试名、断言信息和 traceback 尾部保留下来。
5. 修改 Prompt：代码发生变化后，Agent 必须调用 pytest；没有验证时不允许声明成功。
6. 使用 Fake LLM 构造“写文件 → 运行 pytest → 输出结束”的固定流程。
7. 再使用真实模型尝试一个最简单 Bug。

### 当天产物

- 更新后的 `mini_agent/tools/shell.py`
- 更新后的 `mini_agent/agent.py`
- `tests/test_pytest_result.py`

### 验收命令

```powershell
python -m pytest tests/test_pytest_result.py -q
```

今天的目标只是让测试证据进入 Agent Loop，还没有实现最终成功判定；不要看到 pytest 通过就直接在 Shell 工具中设置任务成功。

### 完成标准

- Agent 能完成“修改简单 Bug → 运行 pytest”。
- Agent 不会只说“已修复”而不请求测试。
- `0 tests collected` 不会被当作验证成功。

---

## Day 13：实现 Task Status 和 Verifier

### 学习

- 状态机基本概念
- Generator 与 Verifier 分离
- 为什么能用程序验证的事情不要交给 LLM 猜

### 动手

- [ ] 定义任务状态及合法转换
- [ ] 实现结构化 `VerificationResult`
- [ ] 检查 pytest 是否通过且确实收集到测试
- [ ] 检查受保护测试是否被修改
- [ ] 检查工作区边界和 `success_checks`
- [ ] 只有 Verifier PASS 才允许代码任务进入 `SUCCESS`

### 新手执行顺序

1. 在 `models.py` 中定义 `VerificationResult`，至少包含 `passed`、`checks` 和 `reason`。
2. 创建 `mini_agent/verifier.py`，先实现最小的 `verify(task_spec, execution_evidence)`。
3. 按固定顺序检查：测试是否执行 → 是否收集到测试 → 退出码是否为 0 → 保护文件是否完整 → 自定义检查是否通过。
4. 在任务开始前计算受保护测试文件的哈希值，验证时重新计算并比较。
5. 在 `agent.py` 中添加 Completion Gate：模型请求结束时，如果是代码任务，先进入 `VERIFYING`。
6. Verifier PASS 后转成 `SUCCESS`；FAIL 时把证据加入 Context，暂时返回 `RUNNING` 或 `FAILED`，为明天 Re-plan 做准备。
7. 测试三个作弊场景：删除测试、修改断言、让 pytest 收集 0 个测试。

### 当天产物

- `mini_agent/verifier.py`
- 更新后的 `mini_agent/models.py`
- `tests/test_verifier.py`

### 验收命令

```powershell
python -m pytest tests/test_verifier.py -q
```

如果哈希校验暂时太难，先只允许 Agent 修改 `src/` 或指定源文件，并从权限层完全禁止写入 `tests/`；之后再补哈希作为第二层保护。

### 完成标准

- LLM 仅仅输出“完成”不能让任务成功。
- Agent 删除测试或修改测试断言后无法通过验证。
- 每次任务结束都有明确的 `status` 和 `reason`。

---

## Day 14：打通端到端验证闭环

### 动手

- [ ] 运行所有单元测试
- [ ] 完成 3 个固定 Bug 修复任务
- [ ] 打通修改、pytest、Verifier、成功或失败状态
- [ ] 记录每个任务的步数和工具调用
- [ ] 更新架构图和 README

### 新手执行顺序

1. 创建 `tests/test_coding_flow.py`，先使用 Fake LLM 固定返回以下动作：读取文件 → 写入修复 → 运行测试 → 请求完成。
2. 验证成功路径最终状态为 `SUCCESS`。
3. 把 Fake LLM 的写入内容改错，验证最终不能成为 `SUCCESS`。
4. 让 Agent 尝试修改受保护测试，验证 Executor 拒绝且 Verifier 不通过。
5. 为三个 fixture 分别创建干净副本，再使用真实模型运行。
6. 在表格中记录：任务、最终状态、步数、修改文件、pytest 结果和失败原因。
7. 只修复阻塞完整闭环的问题，不在复盘日增加新模块。

### 当天产物

- `tests/test_coding_flow.py`
- 第一张端到端运行结果表
- 更新后的 README 与架构图

### 验收命令

```powershell
python -m pytest -q
```

如果真实模型成功率低，但 Fake LLM 端到端测试稳定通过，说明系统骨架基本正确，下一周重点应放在失败证据、Prompt 和 Recovery，而不是推翻重写。

### 完成标准

- 至少 2/3 个固定任务能独立完成。
- 每次文件修改都有对应验证结果。
- 测试失败时状态不是 `SUCCESS`。
- 失败时可以看到明确证据，而不是只有最终报错。

---

# 第 3 周：Failure Recovery、Trace 与安全控制

## Day 15：定义 Failure Type 和 Recovery Policy

### 学习

- 失败分类为什么比一个模糊的 `Exception` 更有用
- 哪些错误可以 Retry，哪些错误需要 Re-plan 或停止

### 动手

- [ ] 定义以下 Failure Type
- [ ] 为每种失败定义处理策略
- [ ] 让失败类型进入 `ToolResult`、`VerificationResult` 或 `TaskResult`

### 新手执行顺序

1. 创建 `mini_agent/errors.py`，先定义 `FailureType` 枚举，不急着创建很多异常类。
2. 创建 `mini_agent/policy.py`，实现 `decide_recovery(failure_type, attempt_count)`。
3. 让 Policy 返回有限的几个动作：`RETRY`、`REPLAN`、`ASK_APPROVAL`、`STOP`。
4. 把已有错误逐一映射到 FailureType，例如命令超时映射到 `TIMEOUT`，越界路径映射到 `PERMISSION_DENIED`。
5. 为策略写参数化测试：输入 FailureType 和尝试次数，检查输出动作。
6. 检查代码中宽泛的 `except Exception`：可以在系统边界捕获，但必须记录原异常，并转换成明确类型。

### 当天产物

- `mini_agent/errors.py`
- `mini_agent/policy.py`
- `tests/test_policy.py`

### 验收命令

```powershell
python -m pytest tests/test_policy.py -q
```

不要今天就把所有异常重构完。先覆盖最常见的 6～8 种失败，未知异常统一标记为 `INTERNAL_ERROR` 也比静默吞掉更好。

```text
LLM_ERROR
PARSE_ERROR
TOOL_ERROR
EXECUTION_ERROR
VERIFICATION_FAILED
MAX_STEPS
TIMEOUT
PERMISSION_DENIED
```

建议策略：

| 失败类型 | 默认策略 |
|---|---|
| 临时网络错误 | 有限 Retry |
| 解析错误 | 返回格式错误证据，最多修正一次 |
| 工具参数错误 | 不重复相同调用，交给 Agent Re-plan |
| 验证失败 | 将测试证据加入 Context 后 Re-plan |
| 权限拒绝 | 请求批准或停止 |
| 最大步数 / 总超时 | 明确结束为 FAILED |

### 完成标准

- 失败原因可以被程序识别。
- 不同错误不会全部使用同一种盲目重试策略。

---

## Day 16：实现有限 Retry、Re-plan 和总 Timeout

### 学习

- Retry 与 Re-plan 的区别
- 退避策略
- 为什么重复同一个错误动作通常没有意义

### 动手

- [ ] 为临时 LLM 错误增加有限 Retry
- [ ] 为 Agent 设置最大步数
- [ ] 为整个任务设置总 Timeout
- [ ] 验证失败时把失败证据加入 Context
- [ ] 阻止 Agent 使用完全相同参数重复失败调用

### 新手执行顺序

1. 在 Agent Loop 中分别记录 `step_count`、`retry_count` 和任务开始时间，不要混成一个计数器。
2. LLM 临时网络错误发生时，最多重试 2 次，并使用短暂递增等待。
3. Tool 参数错误时，不直接再次执行相同参数；把错误信息作为 Observation 交还模型。
4. Verifier FAIL 时生成一条清晰消息，包含失败检查、pytest 错误摘要和剩余步数。
5. 保存最近一次失败 Tool Call 的工具名与参数摘要；完全相同时阻止无限重复。
6. 在每轮开始前检查总 Timeout，在调用耗时操作前也检查剩余时间。
7. 使用 Fake LLM 编写“第一次写错、第二次修对”的测试。

### 当天产物

- 更新后的 `mini_agent/agent.py`
- 更新后的 `mini_agent/policy.py`
- `tests/test_recovery.py`

### 验收命令

```powershell
python -m pytest tests/test_recovery.py -q
```

如果异步 Timeout 太难，第一版可以保持同步：LLM Client 和 subprocess 各自设置 Timeout，再由 Agent Loop 检查总耗时。先不要为了 Timeout 强行引入 `asyncio`。

### 完成标准

- 至少一个任务经历“验证失败 → Re-plan → 再修改 → 验证成功”。
- 超过步数、重试次数或时间限制后明确结束为 `FAILED`。

---

## Day 17：实现 Execution Trace

### 学习

- 日志级别
- 可观察性为什么是调试 Agent 的核心
- Trace 与普通文本日志的区别

### 动手

- [ ] 为每个 Agent Step 分配序号
- [ ] 记录模型动作、工具名称和参数摘要
- [ ] 记录 Observation、耗时、状态和失败类型
- [ ] 记录 VerificationResult
- [ ] 对 API Key、敏感路径和过长内容进行隐藏或截断

### 新手执行顺序

1. 在 `models.py` 中定义 `TraceStep`，先记录计划中列出的核心字段。
2. 创建 `mini_agent/trace.py`，实现内存中的 `TraceRecorder`。
3. 为每次模型响应和工具调用生成递增 `step_id`。
4. 在调用前记录开始时间，调用后计算 `duration_ms`。
5. 只保存工具参数摘要：文件路径可以保存，完整文件内容不要重复写入 Trace。
6. 写 `sanitize_trace_value()`，把疑似 API Key、超长文本和敏感字段替换成 `[REDACTED]` 或截断摘要。
7. 在任务结束时打印一张简短时间线。
8. 使用 Fake LLM 运行一次成功和一次失败任务，人工检查 Trace 是否能解释全过程。

### 当天产物

- `mini_agent/trace.py`
- 更新后的 `mini_agent/models.py`
- `tests/test_trace.py`

### 验收命令

```powershell
python -m pytest tests/test_trace.py -q
```

今天只在内存中记录，不急着写入磁盘。先把 Trace 内容设计正确，Day 22 再持久化。

每一步至少记录：

```text
step_id
timestamp
model_action
tool_name
arguments_summary
observation_summary
duration_ms
status
failure_type
verification_result
```

### 完成标准

- 只看 Trace 就能还原 Agent 做过哪些动作。
- 能定位哪一步最慢、哪一步失败。
- Trace 中没有 API Key 等敏感信息。

---

## Day 18：控制 Context 和工具输出大小

### 学习

- Context Window 与 Token 的基本概念
- 工具输出过长会造成什么问题
- 截断、摘要和滑动窗口的区别

### 动手

- [ ] 限制单次文件读取长度
- [ ] 限制命令输出长度
- [ ] 保留输出开头、结尾和“已截断”提示
- [ ] 设置最大消息数量或近似字符预算
- [ ] 确保 pytest 的关键错误位置不会被截掉

### 新手执行顺序

1. 创建 `mini_agent/context.py`，先实现两个独立函数：`truncate_text()` 和 `build_context()`。
2. `truncate_text()` 保留开头和结尾，在中间插入明确的省略标记和原始长度。
3. 文件读取结果按字符限制；pytest 输出优先保留失败测试名、断言和 traceback 尾部。
4. 为消息列表设置一个简单字符预算。预算不足时优先保留 System Prompt、用户任务、最近几步和最新失败证据。
5. 不要在第一个月精确计算每家模型的 Token；字符预算已经足够帮助理解问题。
6. 准备 1 万字符文件和超长测试输出，确认裁剪结果仍有开头、结尾及标记。
7. 把裁剪后的长度和是否截断写进 ToolResult metadata。

### 当天产物

- `mini_agent/context.py`
- `tests/test_context.py`

### 验收命令

```powershell
python -m pytest tests/test_context.py -q
```

如果摘要功能需要再次调用 LLM，先不做摘要，只做确定性的截断和滑动窗口。这样更容易测试，也更符合第一个月范围。

### 完成标准

- 大文件和超长测试输出不会塞满 Context。
- 截断后仍保留解决问题需要的关键错误证据。

---

## Day 19：实现 Risk-based Human Approval

> 这是 P1 功能。如果 P0 进度落后，先完成静态权限拒绝，审批交互可以顺延。

### 学习

- Human-in-the-loop
- 最小权限原则
- 只读、写入和执行操作的风险差异

### 动手

- [ ] 给 Tool 定义风险等级
- [ ] 低风险工具自动执行
- [ ] 中风险工具支持配置是否审批
- [ ] 高风险工具默认拒绝或必须审批
- [ ] 把审批决定记录进 Trace

### 新手执行顺序

1. 在 `models.py` 中定义 `RiskLevel` 和 `ApprovalDecision`。
2. 在 Registry 注册工具时附带风险等级，而不是在 Agent Loop 里按工具名写很多 `if`。
3. 在 `policy.py` 中实现 `requires_approval(tool, arguments)`。
4. 第一版 CLI 审批只需要显示工具、参数摘要和风险，然后接受 `y/n`。
5. 自动化测试中注入 Fake Approval Provider，分别固定返回批准和拒绝，避免测试卡在 `input()`。
6. 用户拒绝后返回 `PERMISSION_DENIED` Observation，同时禁止相同请求反复弹窗。
7. 把请求、决定、时间和对应 `step_id` 写入 Trace。

### 当天产物

- 更新后的 `mini_agent/models.py`
- 更新后的 `mini_agent/policy.py`
- 可选的 `mini_agent/approval.py`
- `tests/test_approval.py`

### 验收命令

```powershell
python -m pytest tests/test_approval.py -q
```

如果 P0 仍未稳定，只实现“LOW 自动执行、其他全部拒绝”的静态策略。交互审批属于加分项，可以顺延。

```text
LOW
- read_file
- list_files
- grep

MEDIUM
- write_file

HIGH
- 非白名单命令
- 破坏性操作
```

### 完成标准

- 用户拒绝后 Agent 不会绕过限制。
- 高风险命令不会因为模型反复请求而自动执行。

---

## Day 20：实现最小 Snapshot / Rollback

> 这是 P1 功能。没有完成时，不影响本月 P0 验收。

### 学习

- 为什么修改前需要恢复点
- 单文件快照和任务级工作副本的区别
- 最小事务思想

### 动手

- [ ] 修改前保存原始内容、文件路径、时间和 `step_id`
- [ ] 实现单步文件恢复
- [ ] 把 Rollback 行为记录进 Trace
- [ ] 不使用 Rollback 恢复工作区外文件或受保护文件

### 新手执行顺序

1. 先确认 P0 测试全部通过；否则跳过今天的 P1 功能，回去修复主线。
2. 创建 `mini_agent/snapshot.py`，定义 `FileSnapshot(path, original_content, existed, step_id)`。
3. 在 `write_file` 真正修改前创建快照；快照失败时不要继续写入。
4. 实现 `rollback(step_id)`：原文件存在则恢复原内容，原文件原本不存在则删除本次新建文件。
5. Rollback 仍必须调用工作区和保护路径检查。
6. 测试覆盖文件恢复、新文件撤销、未知 step、越界路径和重复 rollback。
7. 演示一次错误修改 → pytest 更差 → 用户或策略触发恢复。

### 当天产物

- `mini_agent/snapshot.py`
- `tests/test_snapshot.py`

### 验收命令

```powershell
python -m pytest tests/test_snapshot.py -q
```

第一版只支持单步、单文件恢复即可。多文件事务、Git 分支和完整工作区快照放到后续版本。

### 完成标准

- 能演示一次错误修改后的恢复。
- 恢复后原文件内容和测试状态符合预期。

---

## Day 21：第三周故障演练

### 动手

- [ ] 模拟 LLM 超时
- [ ] 模拟 Tool 参数错误
- [ ] 模拟文件不存在
- [ ] 模拟 pytest 超时
- [ ] 模拟 Verification Failure
- [ ] 模拟用户拒绝执行
- [ ] 模拟 Agent 达到最大步数
- [ ] 为发现的问题补测试

### 新手执行顺序

1. 创建 `tests/test_failure_scenarios.py`，每种故障写成独立测试，不要写一个包含全部情况的巨型测试。
2. 用 Fake LLM 抛出 Timeout，检查策略是否有限 Retry 后失败。
3. 用 Fake Tool 返回参数错误，检查 Agent 是否把证据交给模型而不是崩溃。
4. 让命令睡眠超过 Timeout，检查子进程是否结束。
5. 让 Fake LLM 永远返回相同 Tool Call，检查最大步数和重复调用保护。
6. 尝试写入受保护测试，检查权限错误、最终状态和 Trace。
7. 如果实现审批，模拟拒绝并确认相同高风险请求不会重复弹出。
8. 运行全量测试，将每个发现的问题记录为“复现步骤 → 原因 → 修复 → 防回归测试”。

### 当天产物

- `tests/test_failure_scenarios.py`
- `DEVLOG.md` 中的故障演练记录
- 修复对应的回归测试

### 验收命令

```powershell
python -m pytest -q
```

如果一次出现很多失败，只处理最早的失败。修复后重新跑相关单测，再跑全量测试，避免同时改动多个模块后找不到原因。

### 完成标准

- P0 场景都能安全结束或按策略恢复。
- 错误信息能说明“发生了什么”和“系统如何处理”。
- 只看 Trace 可以指出任务失败在哪一层。

---

# 第 4 周：Trace 持久化、Evaluation 与最终交付

## Day 22：实现 Trace Persistence

### 学习

- 为什么 Agent 调试需要持久化执行轨迹
- JSONL 与 SQLite 的取舍

### 动手

- [ ] 使用 JSONL 保存 Task 和 Step
- [ ] 保存任务输入、工具调用、验证结果和最终状态
- [ ] 程序启动后可以读取历史任务
- [ ] 对敏感字段做脱敏，对过长字段做截断

### 新手执行顺序

1. 在项目根目录约定 `.mini-agent/traces/` 为本地 Trace 目录，并把它加入 `.gitignore`。
2. 先选择 JSONL：每行一个 JSON 对象，结构简单，便于手工查看。
3. 在 `trace.py` 中实现 `save_task_trace()`，使用 UTF-8 和 `ensure_ascii=False`。
4. 保存前统一调用 Day 17 的脱敏函数，禁止直接把原始对象随手写盘。
5. 实现 `load_task_trace(task_id)`，找不到时返回明确错误。
6. 先保存一个 Fake LLM 任务，关闭程序后再读取并打印。
7. 人工打开 JSONL，确认没有 API Key、完整文件内容或无限长 pytest 输出。
8. 写入中途失败时不要破坏已有 Trace；第一版可采用临时文件后替换。

### 当天产物

- 支持持久化的 `mini_agent/trace.py`
- `.mini-agent/traces/` 本地目录约定
- `tests/test_trace_persistence.py`

### 验收命令

```powershell
python -m pytest tests/test_trace_persistence.py -q
```

JSONL 已足够完成本月目标。只有在确实需要复杂查询时才考虑 SQLite，不要为了“像生产系统”提前增加数据库。

至少保存：

```text
task_id
input
steps
tool_calls
observation_summaries
verification
final_status
latency
```

### 完成标准

- 程序关闭后仍能查看历史任务。
- 每条记录可以通过 `task_id` 找到。
- 敏感信息不会直接落盘。

---

## Day 23：实现 Trace Inspect

> 本月先实现历史轨迹查看，不把它错误地称为真正 Replay。

### 学习

- Trace Inspect 与 Replay 的区别
- 为什么模型随机性会影响真正的任务复现

### 动手

- [ ] 支持按照 `task_id` 查看历史执行轨迹
- [ ] 显示每一步状态、工具、耗时和验证结果
- [ ] 默认不重新执行工具或危险动作
- [ ] 为不存在的 `task_id` 返回清晰错误

### 新手执行顺序

1. 创建 `mini_agent/cli.py` 和 `mini_agent/__main__.py`。
2. 先支持 `python -m mini_agent inspect task_001`，不急着引入第三方 CLI 框架。
3. CLI 调用 `load_task_trace()`，按 `step_id` 排序。
4. 每一步只显示动作摘要、状态、耗时和失败类型；增加 `--verbose` 后才显示详细 Observation。
5. 最后一行显示 Final Status、Reason、总步数和总耗时。
6. 确认 `inspect` 路径中没有 Executor 调用，避免查看历史时重新写文件或运行命令。
7. 测试成功任务、失败任务、空 Trace 和不存在的 task_id。

### 当天产物

- `mini_agent/cli.py`
- `mini_agent/__main__.py`
- `tests/test_cli_inspect.py`

### 验收命令

```powershell
python -m pytest tests/test_cli_inspect.py -q
python -m mini_agent inspect task_001
```

如果 CLI 参数解析卡住，可以先让 `inspect_task(task_id)` 作为普通 Python 函数工作，再添加命令行入口。

示例：

```bash
python -m mini_agent inspect task_001
```

```text
Step 1: read_file      SUCCESS
Step 2: write_file     SUCCESS
Step 3: pytest         FAILED
Step 4: write_file     SUCCESS
Step 5: pytest         PASSED
Final: SUCCESS
```

### 完成标准

- 能快速定位历史任务失败在哪一步。
- 查看历史不会重新执行写文件或命令操作。

真正 Replay 留到后续版本。它至少需要保存：

- 初始工作区快照
- Prompt 和模型配置
- 每轮模型输入与输出
- 工具输入与输出
- 代码与依赖版本

---

## Day 24：建立固定 Agent Eval Set

### 学习

- Agent 评测为什么不能只看一次成功 Demo
- 成功率、验证通过率、步数、耗时和工具错误次数

### 动手

- [ ] 先准备 5 个 P0 固定任务
- [ ] 时间充足时扩充到 8～12 个任务
- [ ] 为每个任务定义明确的 `success_checks`
- [ ] 每次运行前恢复干净的评测项目
- [ ] 记录评测结果

### 新手执行顺序

1. 在 `evals/tasks/` 中为每个任务创建一个 JSON 文件，字段与 `TaskSpec` 对齐。
2. 先选择 5 个 P0 任务，不要一开始写 12 个：
   - 一个只读理解任务；
   - 一个单文件简单 Bug；
   - 一个必须二次修复的 Bug；
   - 一个工具失败后应恢复的任务；
   - 一个应因权限或条件不足而失败的任务。
3. 创建 `evals/runner.py`：读取任务 → 复制 fixture 到临时目录 → 执行 Agent → 保存 TaskResult → 清理工作副本。
4. 为每个任务写机器可判断的 success checks，不要写“回答看起来不错”。
5. 创建 `EvalResult`，记录计划中的指标和失败分类。
6. 先用 Fake LLM 跑通 Runner，再用真实模型跑一个任务。
7. 确认前一次评测修改不会污染下一次运行。

### 当天产物

- 5 个 `evals/tasks/*.json`
- `evals/runner.py`
- `tests/test_eval_runner.py`

### 验收命令

```powershell
python -m pytest tests/test_eval_runner.py -q
```

今天先保证评测基础设施可重复。真实模型是否全部成功不是当天验收条件。

任务至少覆盖：

- 只读代码理解
- 单文件简单 Bug
- 测试失败后需要二次修复
- Tool 错误后的恢复
- 一个应当明确失败的任务

指标至少包括：

```text
task_success
verification_pass
steps
tool_errors
retries
latency
```

### 完成标准

- 5 个 P0 任务可以重复运行。
- 成功与失败由 Verifier 或规则判断，不由人工感觉决定。

---

## Day 25：运行评测并分析失败模式

### 动手

- [ ] 每个 P0 任务至少运行一次
- [ ] 成本允许时，每个任务重复运行 3 次
- [ ] 统计 Verified Success Rate
- [ ] 把失败任务分类
- [ ] 选择影响最大的一个失败原因做针对性修复
- [ ] 修复后重新运行相关评测

### 新手执行顺序

1. 先运行 5 个任务各一次，把原始结果保存下来，不要看到失败就中途手改数据。
2. 创建 `evals/results/YYYY-MM-DD.json` 保存机器可读结果。
3. 创建同名 Markdown，总结任务状态、验证状态、步数、耗时、重试和失败类型。
4. 计算：`Verified Success Rate = Verifier PASS 的任务数 / 总任务数`。
5. 选择出现次数最多、影响最大的一个失败类型。
6. 根据证据定位层级：如果工具没被选中，检查 Prompt/Schema；如果工具执行错，检查 Executor；如果测试明明失败却成功，检查 Verifier。
7. 只修改一个主要因素，然后重新运行受影响任务。
8. 在报告中同时保留修改前后结果，即使改动没有提升也如实记录。

### 当天产物

- `evals/results/YYYY-MM-DD.json`
- `evals/results/YYYY-MM-DD.md`
- 一次有证据的针对性改进

### 结果表模板

| Task | Status | Verified | Steps | Retries | Tool errors | Latency |
|---|---|:---:|---:|---:|---:|---:|
| task_001 |  |  |  |  |  |  |

如果 API 成本有限，每个任务先跑一次。重复三次是加分项，不要因为预算不足而伪造稳定性数据。

失败分类：

```text
Reasoning
Tool Selection
Parsing
Execution
Verification
Permission
Loop Control
```

### 完成标准

- 得到一张真实评测表。
- 能指出系统最常失败在哪一层。
- 能用评测结果说明一次改动是否有效。

### 可选 Baseline

时间充足时比较：

```text
Baseline
普通 Agent Loop

vs

Reliability Version
Verifier + Recovery + Trace
```

不要为了完成表格而伪造或手工美化数据。

---

## Day 26：完善 README 和架构说明

### 动手

- [ ] 写清项目解决什么问题
- [ ] 写清为什么不是另一个通用 Agent Framework
- [ ] 解释为什么 LLM 的“完成”不等于任务成功
- [ ] 解释 Verifier、Recovery、权限和 Trace
- [ ] 写清安装、配置、运行和测试方法
- [ ] 加入真实评测结果
- [ ] 添加架构图和执行流程图
- [ ] 说明当前限制和后续计划

### 新手执行顺序

1. 先写 README 目录，再逐节填内容，避免从第一句话开始反复修改。
2. 第一屏依次放：项目一句话定位、核心能力、一个最短运行示例、当前 Verified Success Rate。
3. 在“工作原理”中画两张小图：系统模块图和 `Act → Observe → Verify → Recover` 流程图。
4. 从空目录按照 README 安装一次，记录遗漏的依赖或环境变量。
5. 复制所有命令逐条执行，确保路径和参数没有写错。
6. 把 Day 25 的真实结果表放入 README，并链接详细评测报告。
7. 写出至少 3 个当前限制，例如只支持小型 Python 项目、命令白名单有限、没有真正 Sandbox。
8. 检查仓库状态，确认 `.env`、本地 Trace 和临时评测副本没有被纳入版本控制。

### 当天产物

- 完整 `README.md`
- 架构图
- 可复现的安装、运行、测试和评测命令

### 文档验收

找一个全新的临时目录，完全按照 README 操作。如果需要依靠自己记忆补步骤，就说明 README 还不完整。

README 第一屏建议使用：

> **A verification-first coding agent built from scratch.**
>
> It focuses on explicit completion checks, recoverable execution, risk-aware tool use, trace inspection and reproducible evaluation.

README 至少回答：

1. 这个项目解决什么问题？
2. 为什么不用现成 Agent 框架？
3. 为什么 LLM 的“完成”不代表真正完成？
4. Verifier 如何决定 `SUCCESS`？
5. 如何防止 Agent 修改测试来骗过验证？
6. 工具失败后如何 Recovery？
7. Trace 如何帮助定位失败任务？
8. Evaluation 如何衡量可靠性？
9. 当前有哪些限制？

### 完成标准

- 没看过代码的人可以按照 README 启动项目。
- 面试官看 README 第一屏就能理解项目的技术主张。
- README 没有暴露 API Key 或个人敏感信息。

---

## Day 27：准备两个最终 Demo

### Demo A：经历失败后成功

```text
读取代码
→ 修改
→ pytest FAILED
→ Verifier FAIL
→ Agent 读取失败证据
→ Re-plan
→ 再修改
→ pytest PASSED
→ Verifier PASS
→ SUCCESS
```

### Demo B：无法安全完成

```text
任务要求越过工作区或执行危险命令
→ Risk / Permission Check
→ 系统拒绝
→ Agent 不绕过权限
→ FAILED 或 CANCELLED
```

### 动手

- [ ] 准备干净、可重复的 Demo 初始状态
- [ ] 展示 Tool Call、Observation、Verification 和 Trace
- [ ] 两个 Demo 各连续运行 3 次
- [ ] 编写 3～5 分钟演示讲稿

### 新手执行顺序

1. 在 `examples/demo_success/` 固定成功 Demo 的初始代码与测试。
2. 选择一个模型第一次容易犯错、但错误信息足够清晰的任务；不要为了演示故意设计随机谜题。
3. 在 `examples/demo_rejected/` 固定越界访问或危险命令任务。
4. 写 `scripts/reset_demo.ps1` 的需求清单；如果还不会写脚本，就在 README 明确列出手工重置步骤，不要用不熟悉的删除命令。
5. 分别运行两个 Demo 三次，记录成功次数和失败原因。
6. 演示讲稿只讲：问题、普通 Agent 风险、你的完成门、失败恢复、证据和结果。
7. 提前准备 API 不可用时的备用材料：保存的 Trace、终端输出和架构图。
8. 录制一次完整演示，回看是否能清楚看到任务状态和验证结果。

### 当天产物

- `examples/demo_success/`
- `examples/demo_rejected/`
- Demo 重置说明
- `docs/demo-script.md`
- 一次完整演示录像（可选）

### 卡住时先检查

- Demo 初始状态是否每次相同。
- 模型、Prompt 和 TaskSpec 是否固定。
- 测试文件是否受保护。
- 失败究竟来自模型随机性，还是系统代码错误。

### 完成标准

- 两个 Demo 都能稳定复现。
- 成功 Demo 展示 Recovery，而不只是一次成功。
- 失败 Demo 展示系统能够安全拒绝任务。

---

## Day 28：最终验收与项目复盘

### P0 最终验收清单

- [ ] 5 个基础工具全部可用
- [ ] Agent Loop 能稳定运行并安全退出
- [ ] 有明确的 TaskSpec、TaskResult 和 Task Status
- [ ] 代码修改必须经过 Verifier
- [ ] Verifier 能发现未收集测试和测试文件被修改
- [ ] 测试失败后 Agent 能 Re-plan
- [ ] 有有限 Retry、最大步数和总 Timeout
- [ ] 有 Failure Type 和 Recovery Policy
- [ ] 有工作区边界和安全命令控制
- [ ] 有 Execution Trace 和持久化
- [ ] 有 Trace Inspect
- [ ] 有至少 5 个固定评测任务
- [ ] README 包含真实评测结果
- [ ] 两个最终 Demo 可以稳定复现

### 新手执行顺序

1. 从干净状态运行全量测试：

   ```powershell
   python -m pytest -q
   ```

2. 运行 5 个 P0 Eval，保存最终结果，不再临时调整成功标准。
3. 运行成功 Demo 和安全拒绝 Demo。
4. 逐项勾选 P0 清单；没有完成的项目如实写进 README 的限制，不要假装完成。
5. 清理临时调试输出、废弃文件和注释掉的大段代码，但不要在最后一天大规模重构。
6. 检查 `.gitignore`，确保 API Key、Trace、本地虚拟环境和临时工作副本不会被提交。
7. 在 `docs/retrospective.md` 回答复盘问题。
8. 创建一个版本标签计划，例如 `v0.1.0`；只有测试、Eval 和文档都完成后才视为本月结束。

### 当天产物

- 最终测试结果
- 最终 Eval 报告
- `docs/retrospective.md`
- 可发布的 `v0.1.0` 项目状态

### 最后一天的原则

最后一天只做验收、修复和记录，不再添加新功能。一个诚实、稳定、边界清楚的 v0.1，比功能很多但无法解释的项目更有价值。

### P1 加分项清单

- [ ] 有 Snapshot / Rollback
- [ ] 有 Risk-based Human Approval
- [ ] Eval Set 扩展到 8～12 个任务
- [ ] 完成 Baseline 对比实验
- [ ] 实现真正可控的 Replay

### 最终复盘问题

1. 为什么“LLM 说完成”不能代表任务真的完成？
2. `pytest` 返回 0 为什么仍可能是假成功？
3. Generator 和 Verifier 为什么应该分开？
4. 哪些错误应该 Retry，哪些应该 Re-plan 或直接停止？
5. Agent 最常失败在 Reasoning、Tool、Execution 还是 Verification？
6. Human Approval 应该放在哪些动作前？
7. Trace Inspect 与真正 Replay 有什么区别？
8. 当前项目的 Verified Success Rate 是多少？
9. 如果继续开发一个月，最值得改进什么？

### 最终成功标准

最终项目应该展示：

```text
TaskSpec
→ Reason
→ Act
→ Observe
→ Verify
→ FAIL?
    ↓ Yes
  Recover / Re-plan
    ↓
→ Verify Again
→ PASS
→ SUCCESS
```

而不是：

```text
Task
→ LLM
→ “Done”
```

---

## 六、建议代码结构

不要求第一天就创建全部文件，随着每日任务逐步拆分：

```text
mini-swe-agent/
├── mini_agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── llm_client.py
│   ├── models.py
│   ├── parser.py
│   ├── registry.py
│   ├── executor.py
│   ├── verifier.py
│   ├── policy.py
│   ├── trace.py
│   └── tools/
│       ├── __init__.py
│       ├── filesystem.py
│       └── shell.py
├── tests/
├── evals/
│   ├── fixtures/
│   └── tasks/
├── examples/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

为什么这样拆分：

- `agent.py`：只负责 Agent Loop，不直接实现工具。
- `registry.py`：负责工具注册和查找。
- `executor.py`：负责参数校验与工具执行。
- `verifier.py`：独立判断任务是否真正完成。
- `policy.py`：集中管理失败恢复和权限策略。
- `trace.py`：记录并持久化执行轨迹。

这是为了降低模块耦合，并不是为了追求复杂的面向对象设计。

---

## 七、本阶段暂时不要做

为了真正理解最小 Agent，本阶段先不加入：

- LangChain、LangGraph、CrewAI、Strands 等 Agent 框架
- Web UI
- Multi-Agent
- RAG 或向量数据库
- MCP
- 长期 Memory 系统
- SQLite 任务恢复系统
- Docker Sandbox
- TypeScript、Go 或 Rust 重写
- 为模仿其他 Agent 项目而加入大量通用功能
- 复杂的自动代码审查或大型项目支持

这些能力可以以后增加。当前目标是：

> **用尽量少的代码，亲手实现一个能够修改代码、执行验证、根据失败证据继续行动，并且不会把“模型说完成”当成真正完成的 Agent Loop。**

---

## 八、每周里程碑

| 时间 | 里程碑 | 验收结果 |
|---|---|---|
| 第 1 周 | 最小只读 Agent | 能自主读取文件并回答项目问题 |
| 第 2 周 | 可验证代码修改闭环 | 能修改简单 Bug，且只有 Verifier PASS 才能成功 |
| 第 3 周 | Recovery 与安全控制 | 有失败分类、Re-plan、Timeout、Trace 和权限边界 |
| 第 4 周 | 可评测交付 | 有 Trace 历史、固定评测集、真实指标、README 和 Demo |

---

## 九、每日打卡表

| Day | 日期 | 是否完成 | 实际用时 | 一句话收获 |
|---:|---|:---:|---:|---|
| 1 |  | [ ] |  |  |
| 2 |  | [ ] |  |  |
| 3 |  | [ ] |  |  |
| 4 |  | [ ] |  |  |
| 5 |  | [ ] |  |  |
| 6 |  | [ ] |  |  |
| 7 |  | [ ] |  |  |
| 8 |  | [ ] |  |  |
| 9 |  | [ ] |  |  |
| 10 |  | [ ] |  |  |
| 11 |  | [ ] |  |  |
| 12 |  | [ ] |  |  |
| 13 |  | [ ] |  |  |
| 14 |  | [ ] |  |  |
| 15 |  | [ ] |  |  |
| 16 |  | [ ] |  |  |
| 17 |  | [ ] |  |  |
| 18 |  | [ ] |  |  |
| 19 |  | [ ] |  |  |
| 20 |  | [ ] |  |  |
| 21 |  | [ ] |  |  |
| 22 |  | [ ] |  |  |
| 23 |  | [ ] |  |  |
| 24 |  | [ ] |  |  |
| 25 |  | [ ] |  |  |
| 26 |  | [ ] |  |  |
| 27 |  | [ ] |  |  |
| 28 |  | [ ] |  |  |

---

## 十、完成 28 天后的下一步

先不要立刻把它扩成一个通用 Agent 平台。优先总结并复用这些可靠性组件：

```text
Task Contract
Verifier
Failure Policy
Permission / Approval
Trace
Rollback
Evaluation
```

随后可以把它们应用到更真实的 Agent 场景中。但在进入下一阶段前，先确保自己能够独立解释并演示：

> **Agent 为什么可以被信任，以及它在无法安全完成任务时为什么能够明确失败。**
