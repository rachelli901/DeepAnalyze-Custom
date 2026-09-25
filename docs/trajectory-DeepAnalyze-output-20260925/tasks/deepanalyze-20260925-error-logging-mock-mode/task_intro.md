# 候选任务介绍

## 基本信息
- 安全任务 ID：deepanalyze-20260925-error-logging-mock-mode
- 脱敏标题：增加 API 错误日志与无 GPU Mock 模式
- 会话 ID 和安全定位符：01a0d7d1-7324-77a1-98dd-8bfd4d186313；sessions/2026/09/25/rollout-2026-09-25T17-07-03-01a0d7d1-7324-77a1-98dd-8bfd4d186313.jsonl#L326-L448; turn_id=01a0d7f0-36a3-7b62-98a6-34636d770ef6; ordinal=325-447
- 技术领域和任务类型：非 GPU 通用软件工程 / 可靠性 / 可测试性 / 可观测性
- 最终状态：成功

## 任务定义
- 既有工程背景：路径修复后脚本退出码为 0 但只输出空行，因为 vLLM 连接异常被 generate() 的裸 except 静默吞掉。
- 初始问题：消除 API 异常静默捕获，增加分类日志、错误返回字段和无 GPU Mock 测试流程。
- 最终目标和约束：让连接失败、HTTP 错误、响应结构错误和未知异常可诊断，并提供无需 GPU 即可运行的正常路径 Mock 模式。

## 人机协作
- 用户新增信息（如有；不要求多轮补充）：用户给出运行上下文、明确问题边界和验收动作。
- Agent 关键观察、行动和调整：在 deepanalyze.py 分类捕获 requests 与响应结构异常、增加 request_timeout、返回 error 字段并实现 mock_responses；run.py 配置日志并在 error 时以退出码 1 结束。

## 验收条件
| 核心要求 | 可观察结果 | 验证证据 | 当前状态 |
| --- | --- | --- | --- |
| 取消静默失败 | 连接和 HTTP 异常输出 ERROR 与 traceback | 502 模拟运行输出 | 已满足 |
| 提供可机读错误状态 | generate() 返回 error 字段 | deepanalyze.py 修改后源码与 diff | 已满足 |
| 支持无 GPU 验证 | Mock 模式跳过网络请求并执行两轮本地响应 | Mock 运行日志与退出码 0 | 已满足 |
| 非零退出通知调用方 | run.py 在 answer.error 存在时 SystemExit(1) | run.py 修改后源码及 502 运行结果 | 已满足 |
| 配置 API 请求超时 | request_timeout 默认 300 秒并传给 requests.post | deepanalyze.py 修改后源码 | 已满足 |

## 支撑材料
| 材料 | 用途 | 完备状态 | 安全定位符 |
| --- | --- | --- | --- |
| 原生会话 JSONL | 保存修改、diff、Mock 成功和 502 失败证据 | 完整 | sessions/2026/09/25/rollout-2026-09-25T17-07-03-01a0d7d1-7324-77a1-98dd-8bfd4d186313.jsonl#L326-L448 |
| workspace/deepanalyze.py | 异常分类、日志、超时和 Mock 实现 | 最终版本存在；基线由 Git commit 007389c 提供 | workspace/deepanalyze.py |
| workspace/run.py | 日志初始化、Mock 开关和错误退出 | 最终版本存在；基线由 Git commit 007389c 提供 | workspace/run.py |

## 评价
- Workspace 完备性：基本完整
- 复杂度：中
- 七个价值方向：
- 工程价值：强
- 专业挑战：中
- Agentic 深度：强
- 专家贡献：中
- 任务闭环：强
- 环境质量：强
- 验证价值：强
- 候选层级：强候选

## 结论
- 分类：推荐提交
- 缺口和风险：
- 尚未形成自动化单元测试文件；验证来自实际 Mock 运行和模拟失败运行。
- 修改尚未形成独立 commit。
- 提交前动作：
  - 由专家确认材料使用权和提交许可。
  - 确认导出的脱敏 ZIP 未包含新的个人路径或凭据。
  - 如需固定版本，提交前将相关变更整理为可定位 commit。