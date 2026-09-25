# 候选任务介绍

## 基本信息
- 安全任务 ID：deepanalyze-20260925-subprocess-timeout-safety
- 脱敏标题：以子进程、超时和 AST 拦截加固代码执行
- 会话 ID 和安全定位符：01a0d7d1-7324-77a1-98dd-8bfd4d186313；sessions/2026/09/25/rollout-2026-09-25T17-07-03-01a0d7d1-7324-77a1-98dd-8bfd4d186313.jsonl#L492-L629; turn_id=01a0d7f8-1d34-7963-902c-e95e009f1564; ordinal=491-628
- 技术领域和任务类型：非 GPU 通用软件工程 / 安全加固 / 可靠性重构
- 最终状态：成功

## 任务定义
- 既有工程背景：安全审计确认 while True 可挂死主进程，os.system 和 shutil.rmtree 可按当前用户权限执行，且现有 HTTP timeout 不覆盖代码执行。
- 初始问题：将模型生成代码从同进程 exec 改为独立子进程执行，加入硬超时、输出捕获和 AST 高危操作拦截。
- 最终目标和约束：在无 Docker 前提下落实独立子进程、默认 60 秒 code_timeout、stdout/stderr 捕获和基础危险操作拦截，并用 Mock 验证。

## 人机协作
- 用户新增信息（如有；不要求多轮补充）：用户给出运行上下文、明确问题边界和验收动作。
- Agent 关键观察、行动和调整：实现 _validate_code_safety 与 AST 名称解析，使用 subprocess.run([sys.executable, "-I", "-"], capture_output=True, timeout=code_timeout)，并保留 Mock 驱动的端到端验证。

## 验收条件
| 核心要求 | 可观察结果 | 验证证据 | 当前状态 |
| --- | --- | --- | --- |
| 替换进程内执行 | execute_code 使用独立 Python 子进程和标准输入 | 源码与替换后 diff | 已满足 |
| 硬超时中断死循环 | code_timeout=2 的 while True 在约 2 秒终止 | Mock 端到端运行日志与返回错误 | 已满足 |
| 拦截基础危险操作 | os.system 在子进程启动前被 AST 检查阻止 | Mock 拦截运行结果 | 已满足 |
| 捕获子进程输出 | stdout 和 stderr 一并进入 Execute 结果 | subprocess.run 参数与 Mock 输出 | 已满足 |
| 避免遗留旧机制 | 无 in-process exec(code_str) 残留且 diff 检查通过 | rg 与 git diff --check | 已满足 |

## 支撑材料
| 材料 | 用途 | 完备状态 | 安全定位符 |
| --- | --- | --- | --- |
| 原生会话 JSONL | 保存重构、溢出修复、Mock 测试和最终 diff | 完整 | sessions/2026/09/25/rollout-2026-09-25T17-07-03-01a0d7d1-7324-77a1-98dd-8bfd4d186313.jsonl#L492-L629 |
| workspace/deepanalyze.py | 子进程、超时和 AST 安全检查实现 | 最终版本存在；基线由 Git commit 007389c 提供 | workspace/deepanalyze.py |
| workspace/run.py | Mock 模式入口和错误退出集成 | 最终版本存在；基线由 Git commit 007389c 提供 | workspace/run.py |

## 评价
- Workspace 完备性：基本完整
- 复杂度：高
- 七个价值方向：
- 工程价值：强
- 专业挑战：强
- Agentic 深度：强
- 专家贡献：强
- 任务闭环：强
- 环境质量：中
- 验证价值：强
- 候选层级：强候选

## 结论
- 分类：推荐提交
- 缺口和风险：
- AST 检查是辅助防线，不是完整沙箱；尚无文件系统、网络、内存和进程树级隔离。
- 检查逻辑尚未形成独立自动化测试文件。
- 修改尚未形成独立 commit。
- 提交前动作：
  - 由专家确认材料使用权和提交许可。
  - 确认导出的脱敏 ZIP 未包含新的个人路径或凭据。
  - 如需固定版本，提交前将相关变更整理为可定位 commit。