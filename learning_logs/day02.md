# Day 02 学习日志：Data Model、Tool Schema 与 JSON

- 日期：2026-08-16
- 项目：Mini SWE Agent
- 今日主题：统一数据结构、工具说明书与 JSON 序列化
- 今日目标：理解 Agent 如何描述消息、工具调用和工具执行结果

---

## 一、今天完成的事情

- [x] 理解 `models.py` 中的 Model 是 Data Model，不是大语言模型
- [x] 理解 `LLMClient` 与 Data Model 的职责区别
- [x] 使用 `@dataclass` 定义 `Message`
- [x] 使用 `@dataclass` 定义 `ToolCall`
- [x] 使用 `@dataclass` 定义 `ToolResult`
- [x] 理解 `ToolCall.name` 与 `ToolCall.arguments` 的作用
- [x] 理解不同工具可以共用同一个 `ToolCall` 类
- [x] 为 5 个基础工具定义 Tool Schema
- [x] 理解 Tool Schema 只描述工具，不执行工具
- [x] 使用 `json.dumps()` 将工具 Schema 转换成 JSON 字符串
- [x] 区分 Data Model 测试与 Tool Schema 测试
- [x] 理解 pytest 的基本成功和失败输出

---

## 二、今天建立的整体概念

```text
Message
→ 保存一条对话消息

Tool Schema
→ 告诉 LLM 有什么工具、工具需要什么参数

ToolCall
→ 保存 LLM 选择的工具和本次实际参数

Tool Function
→ 真正执行文件或命令操作

ToolResult
→ 使用统一格式保存成功结果或失败信息
```

完整流程：

```text
用户任务
→ 转换成 Message
→ Message + Tool Schema 发送给 LLM
→ LLM 返回 ToolCall
→ Executor 根据 ToolCall 找到本地工具函数
→ 工具函数执行
→ 返回 ToolResult
→ ToolResult 转换成 Observation
→ Observation 再发送给 LLM
```

---

## 三、`@dataclass` 的作用和使用方式

### 1. 为什么需要 Data Model

Data Model 的作用不是保存日志，也不是创建大语言模型，而是规定模块之间传递的数据必须使用什么格式。

如果没有统一格式，不同工具可能返回完全不同的数据：

```text
read_file   → 字符串
write_file  → True / False
list_files  → 列表
run_command → 元组
失败        → None、错误字符串或异常
```

Agent 和 Executor 就必须针对每种情况写不同判断。

统一使用 `ToolResult` 后：

```text
ToolResult
├── success
├── output
├── error_code
└── error_message
```

Agent 只需要使用一套处理逻辑：

```text
检查 success
├── True  → 读取 output
└── False → 读取 error_code 和 error_message
```

### 2. `@dataclass` 是什么

`@dataclass` 是 Python 的装饰器，适合定义“主要用于保存数据”的类。

它会根据字段自动生成常用代码，例如：

```text
__init__  → 初始化对象
__repr__  → 以易读格式打印对象
__eq__    → 比较两个对象的数据是否相同
```

因此不需要反复手写：

```text
self.success = success
self.output = output
self.error_code = error_code
```

### 3. 当前三个 Data Model

#### Message

```text
Message
├── role
└── content
```

职责：保存一条对话消息。

#### ToolCall

```text
ToolCall
├── name
└── arguments
```

职责：保存 LLM 请求调用的工具名称和实际参数。

同一个 `ToolCall` 类可以创建很多不同对象：

```text
ToolCall 1
├── name = read_file
└── arguments = {path: README.md}

ToolCall 2
├── name = grep
└── arguments = {pattern: LLMClient, path: mini_agent}

ToolCall 3
├── name = run_command
└── arguments = {command: [pytest, -q]}
```

工具增加时，不需要为每个工具重新定义一个 `ToolCall` 类。变化的是 `name` 和 `arguments` 中的实际数据。

#### ToolResult

```text
ToolResult
├── success
├── output
├── error_code
└── error_message
```

职责：统一表示所有工具的成功或失败结果。

### 4. 类型注解的意义

```text
name: str
arguments: dict[str, object]
```

表示：

```text
name
→ 应该是字符串

arguments
→ 应该是字典
→ Key 应该是字符串
→ Value 可以是字符串、数字、布尔值、列表或其他对象
```

类型注解主要用于代码阅读、编辑器提示和静态检查。普通 dataclass 默认不会在运行时严格验证每个值的类型。

### 5. Data Model 与日志的区别

```text
Data Model
→ 定义记录格式

Data
→ 根据格式创建的一份具体数据

Log / Trace
→ 把运行时产生的数据按时间保存下来
```

`ToolResult` 本身不是日志，但以后可以被 Trace 保存，成为日志的一部分。

---

## 四、Schema 层（`tool_schemas.py`）

### 核心职责

> **Schema 层只负责定规矩、向 AI 索要参数，不负责执行工具。**

Schema 告诉 LLM：

```text
工具叫什么
工具有什么用途
工具接受哪些参数
每个参数是什么类型
哪些参数必须提供
是否允许额外参数
```

例如 `read_file` Schema 表达：

```text
工具名称：read_file
用途：读取工作区内的 UTF-8 文本文件
参数：path
path 类型：string
path 是否必填：是
```

### Schema 不会做什么

Schema 不会：

```text
打开文件
读取文件内容
写入文件
搜索代码
运行命令
返回真实工具结果
```

它只是一份可以发送给 LLM 的工具说明书。

### 只有 Schema 时会发生什么

```text
程序把 Schema 发送给 LLM
→ LLM 知道可以使用 read_file
→ LLM 返回 ToolCall(name=read_file, arguments={path: ...})
→ 文件仍然没有被打开
```

还需要后续模块：

```text
Tool Function
→ 真正执行操作

Registry
→ 保存工具名称与函数的对应关系

Executor
→ 根据 ToolCall 找到并调用函数
```

完整关系：

```text
Tool Schema
→ 工具菜单

ToolCall
→ LLM 点单

Registry / Executor
→ 根据订单找到执行函数

Tool Function
→ 真正执行操作

ToolResult
→ 返回结果或失败原因
```

### 当前 5 个 Tool Schema

```text
read_file
→ 参数：path

write_file
→ 参数：path、content

list_files
→ 参数：path

grep
→ 参数：pattern、path

run_command
→ 参数：command
→ 可选参数：timeout_seconds
```

### 为什么使用字典表示 Schema

Tool Schema 本身是层层嵌套的 JSON 结构：

```text
工具
├── type
└── function
    ├── name
    ├── description
    └── parameters
        ├── type
        ├── properties
        ├── required
        └── additionalProperties
```

Python 字典和列表与 JSON 的对象和数组结构非常接近，因此第一版直接使用 `dict` 和 `list` 更容易理解。

---

## 五、`json.dumps()` 的作用和使用方式

### 1. 它解决什么问题

Python 中的 Tool Schema 使用：

```text
dict
list
str
int
bool
None
```

API 和文件传输常用 JSON 字符串。

`json.dumps()` 的作用是：

```text
Python 对象
→ JSON 字符串
```

这个过程叫做：

```text
序列化 Serialization
```

### 2. 当前使用方式

```python
json.dumps(
    TOOLS,
    ensure_ascii=False,
    indent=2,
)
```

参数含义：

```text
TOOLS
→ 要转换的 Python 列表

ensure_ascii=False
→ 中文保持可读，不转换成 \uXXXX

indent=2
→ 使用两个空格缩进，方便人工检查层级
```

### 3. `dumps` 名称的记忆方法

```text
dump
→ 把 Python 数据写成 JSON

dumps
→ dump string，返回 JSON 字符串
```

相反方向是：

```text
json.loads()
→ JSON 字符串转换回 Python 对象
```

对应关系：

```text
Python 对象
→ json.dumps()
→ JSON 字符串

JSON 字符串
→ json.loads()
→ Python 对象
```

### 4. 为什么 Day 2 要转换一次 JSON

今天使用 `json.dumps()` 不是为了执行工具，也不是为了调用 AI，而是为了检查：

```text
Schema 是否只包含可以序列化的数据
字典和列表层级是否正确
中文描述是否能正常显示
未来是否可以发送给 API
```

如果 Schema 中放入不能直接转换的对象，`json.dumps()` 会抛出错误，帮助提前发现数据格式问题。

### 5. dataclass 如何转换成 JSON

dataclass 对象通常先使用 `asdict()` 转成字典，再使用 `json.dumps()`：

```text
Message / ToolCall / ToolResult 对象
→ dataclasses.asdict()
→ Python 字典
→ json.dumps()
→ JSON 字符串
```

---

## 六、测试文件的职责

### `tests/test_models.py`

测试：

```text
Message 是否正确保存 role 和 content
ToolCall 是否正确保存 name 和 arguments
ToolResult 是否能表示成功
ToolResult 是否能表示失败
dataclass 是否能转换成字典
```

它不调用 AI，也不执行工具。

### `tests/test_tool_schemas.py`

测试：

```text
TOOLS 是否为列表
计划中的 5 个工具是否存在
工具名称是否重复
每个工具是否有名称、描述和参数
必填参数是否定义在 properties 中
整个 TOOLS 是否能转换成 JSON
```

它也不调用 AI。

### pytest 成功标准

```text
每个点 . 代表一个测试通过
[100%] 代表所有测试执行完毕
最后显示 passed
没有 failed 或 error
退出码为 0
```

---

## 七、今天提出的疑问

1. `models.py` 不是已经实例化大语言模型了吗，为什么还要存在？
2. Data Model 能不能理解成日志？
3. Data Model 存在的真正意义是什么？
4. Data Model 是不是用来记录工具调用返回值？
5. `Message`、`ToolCall` 和 `ToolResult` 是否都可以使用 `@dataclass`？
6. 为什么调用工具需要传入参数？
7. `arguments: dict[str, object]` 应该怎样理解？
8. 工具越来越多时，是否每个工具都需要一个新的 `ToolCall` 类？
9. 同一个 `ToolCall` 如何表示参数完全不同的工具？
10. 某个工具的参数发生变化时，是否需要修改 `ToolCall` 类？
11. 谁负责检查 `arguments` 是否符合某个工具的要求？
12. 光有 Tool Schema，AI 能不能真的打开文件？
13. 是否需要把工具脚本直接交给 AI？
14. Tool Schema、Tool Function、Executor 和 ToolResult 分别负责什么？
15. 为什么 Day 2 只写 Schema，不立即实现文件工具？
16. `json.dumps()` 会不会执行工具或调用 AI？
17. `tests/test_models.py` 测试的是 AI 根据 Schema 返回的内容吗？
18. 为什么 `test_models.py` 和 `test_tool_schemas.py` 要分开？
19. 哪个测试是 Day 2 必做，哪个属于额外增强？
20. pytest 如何同时测试两个文件？
21. pytest 返回什么结果才算成功？

---

## 八、今日阶段性结论

今天设计的是 Agent 的“数据语言”和“工具菜单”，还没有实现真实工具。

```text
Data Model
→ 规定 Agent 内部如何传递数据

Tool Schema
→ 规定 LLM 如何请求工具

JSON
→ 让这些结构能够被 API 或文件传输
```

当前系统具备：

```text
✓ 知道消息应该长什么样
✓ 知道工具调用应该长什么样
✓ 知道工具结果应该长什么样
✓ 知道 5 个工具各自需要哪些参数
✓ Schema 可以转换成 JSON
```

当前系统还不具备：

```text
✗ 真实读取文件
✗ 真实写入文件
✗ 真实搜索代码
✗ 真实运行命令
✗ 根据 ToolCall 自动找到工具函数
```

这些能力将在后续的 Tool Function、Registry 和 Executor 中实现。

---

## 九、Day 2 验收清单

- [ ] 能解释 Data Model 与 LLM Model 的区别
- [ ] 能解释 `@dataclass` 为什么适合 Message、ToolCall 和 ToolResult
- [ ] 能解释 ToolCall 为什么只需要一个通用类
- [ ] 能解释 Tool Schema 为什么不能直接执行工具
- [ ] 能解释 Tool Schema 与 Tool Function 的区别
- [ ] 能解释 `json.dumps()` 的输入和输出
- [ ] 能解释 `ensure_ascii=False` 和 `indent=2`
- [ ] 能解释 `test_models.py` 与 `test_tool_schemas.py` 的职责
- [ ] 能识别 pytest 的成功输出
- [ ] 能说明 Day 3 为什么要开始实现真正的文件工具

---

## 十、今日一句话总结

> 今天完成了 Mini SWE Agent 的数据契约和工具菜单设计：`@dataclass` 统一 Agent 内部数据格式，Tool Schema 只负责向 LLM 描述规则和索要参数，`json.dumps()` 负责把 Python 数据序列化成可传输、可检查的 JSON 字符串。
