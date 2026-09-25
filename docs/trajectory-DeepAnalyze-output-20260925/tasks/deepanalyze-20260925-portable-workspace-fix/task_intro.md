# 候选任务介绍

## 基本信息
- 安全任务 ID：deepanalyze-20260925-portable-workspace-fix
- 脱敏标题：修复工作目录硬编码并确保 cwd 恢复
- 会话 ID 和安全定位符：01a0d7d1-7324-77a1-98dd-8bfd4d186313；sessions/2026/09/25/rollout-2026-09-25T17-07-03-01a0d7d1-7324-77a1-98dd-8bfd4d186313.jsonl#L136-L324; turn_id=01a0d7e9-5006-7d50-b3f2-651167d49e6d; ordinal=135-323
- 技术领域和任务类型：非 GPU 通用软件工程 / Bug 修复 / 跨平台兼容
- 最终状态：成功

## 任务定义
- 既有工程背景：前序诊断确认崩溃来自模块级 Linux 绝对路径，用户明确要求直接修改并运行 python run.py 验证。
- 初始问题：修复 run.py 的 Linux 硬编码工作目录，并让 generate() 安全解析、验证和恢复工作目录。
- 最终目标和约束：将工作目录改为跨平台可配置路径，支持环境变量覆盖，并在 generate() 中验证路径且始终恢复原 cwd。

## 人机协作
- 用户新增信息（如有；不要求多轮补充）：用户给出运行上下文、明确问题边界和验收动作。
- Agent 关键观察、行动和调整：在 run.py 引入项目根目录、默认示例目录、环境变量清洗和目录验证；在 deepanalyze.py 使用 PathLike 规范化、目录检查和 finally 恢复 cwd。

## 验收条件
| 核心要求 | 可观察结果 | 验证证据 | 当前状态 |
| --- | --- | --- | --- |
| 修复原始 FileNotFoundError | python run.py 退出码 0 | 会话中的实际终端结果 | 已满足 |
| 提供跨平台默认目录 | 默认工作目录由项目根目录拼接，支持 DEEPANALYZE_WORKSPACE 覆盖 | run.py 修改后源码与 git diff | 已满足 |
| 验证目录存在性 | 不存在或非目录时提前抛出清晰 FileNotFoundError | run.py 与 deepanalyze.py 修改后源码 | 已满足 |
| 恢复进程 cwd | generate() 在 finally 中恢复 original_cwd | deepanalyze.py 修改后源码与 diff | 已满足 |
| 清除环境特定路径 | 旧 workspace 与 model 绝对路径不再出现在两个运行文件 | 专题 rg 检索结果 | 已满足 |

## 支撑材料
| 材料 | 用途 | 完备状态 | 安全定位符 |
| --- | --- | --- | --- |
| 原生会话 JSONL | 保存修改命令、diff、运行结果和失败诊断 | 完整 | sessions/2026/09/25/rollout-2026-09-25T17-07-03-01a0d7d1-7324-77a1-98dd-8bfd4d186313.jsonl#L136-L324 |
| workspace/run.py | 工作目录和模型配置入口 | 最终版本存在；基线由 Git commit 007389c 提供 | workspace/run.py |
| workspace/deepanalyze.py | 工作目录验证与 cwd 恢复 | 最终版本存在；基线由 Git commit 007389c 提供 | workspace/deepanalyze.py |
| workspace/example/analysis_on_student_loan/data | 默认示例工作目录 | 存在且含 21 个文件 | workspace/example/analysis_on_student_loan/data |

## 评价
- Workspace 完备性：基本完整
- 复杂度：中
- 七个价值方向：
- 工程价值：强
- 专业挑战：中
- Agentic 深度：强
- 专家贡献：中
- 任务闭环：强
- 环境质量：中
- 验证价值：中
- 候选层级：强候选

## 结论
- 分类：推荐提交
- 缺口和风险：
- vLLM 服务未启动，因此本次只验证路径修复和进程行为；API 可用性验证由后续 Mock 任务覆盖。
- 修改尚未形成独立 commit。
- 提交前动作：
  - 由专家确认材料使用权和提交许可。
  - 确认导出的脱敏 ZIP 未包含新的个人路径或凭据。
  - 如需固定版本，提交前将相关变更整理为可定位 commit。