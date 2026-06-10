# dev-skills

将研发流程中可复用的单点能力沉淀为 skills，尽量保持轻量高效。每个 skill 只解决一个明确问题，提供必要的流程约束、检查维度和输出格式，避免做成过重的知识库或泛化文档。

## Design Principles

- 单点能力：一个 skill 聚焦一个研发动作，例如调研、重构规划、提交前检查。
- 轻量优先：优先使用精简的 `SKILL.md`，只有确实需要时才增加 scripts、references 或 assets。
- 流程约束：把容易遗漏的步骤、风险点和验证方式固化下来。
- 可执行输出：skill 的产物应能直接进入下一步研发流程，而不是停留在泛泛建议。
- 可组合：skills 之间能串成研发流程，而不是互相重叠。

## Workspace Configuration

默认情况下，skills 只在对话中输出结构化结果，不强制创建或更新文件。

如果某个工作区希望把 PRD、TRD、执行计划等过程结果沉淀为可管理的文档资产，可以在当前工作目录内添加：

```text
.dev-skills/config.toml
```

最小配置：

```toml
[document_artifacts]
enabled = true
```

开启后，支持该模式的 skill 必须把主要产物写入工作区文件，并在回复中给出文件路径和简短摘要。缺失配置文件、缺失 `document_artifacts.enabled`，或值不是 `true` 时，都按关闭处理。

默认目录约定：

```text
docs/prd/
docs/trd/
plans/
tasks/draft/
tasks/ready/
tasks/in-progress/
tasks/blocked/
tasks/done/
decisions/
```

可选覆盖：

```toml
[document_artifacts.paths]
prd = "docs/prd"
trd = "docs/trd"
execution_plan = "plans"
task_draft = "tasks/draft"
task_ready = "tasks/ready"
task_in_progress = "tasks/in-progress"
task_blocked = "tasks/blocked"
task_done = "tasks/done"
decision = "decisions"
```

文档资产模式下的文件应尽量使用稳定文件名，并包含可追踪元数据，例如：

```yaml
---
id: prd-user-auth
type: prd
status: draft
created_at: 2026-06-06
updated_at: 2026-06-06
sources: []
related: {}
---
```

## Skills

建议按照研发流程从上到下选择 skill。专项场景可以按需插入，例如遇到 bug 先走 `bug-reproduction`，做重构先走 `refactor-plan`，涉及影响面不清楚时插入 `change-impact-analysis`。

| 场景 | Skill | 时机 | 主要产物 |
| --- | --- | --- | --- |
| 想法调研 | `research-brief` | 只有原始想法、技术方向或业界实践不清楚时，用于补充背景、替代方案、盲点和决策输入。 | 调研简报、可选方向、风险盲点、后续 PRD/TRD 输入。 |
| PRD 沉淀 | `write-prd` | 需求内容已经讨论清楚或基本成型，需要沉淀为产品需求文档时。 | 目标、范围、用户场景、功能需求、非功能需求、验收标准和后续设计输入。 |
| 代码库导向 | `codebase-orientation` | 在既有仓库里做设计、计划、调试或实现前，需要先理解系统现状时。 | 技术栈、运行验证命令、模块职责、入口路径、数据流、依赖集成、测试方式和风险边界。 |
| 影响面分析 | `change-impact-analysis` | 某个改动、接口、数据结构、配置、依赖或重构的影响范围不清楚时。 | 受影响模块、接口契约、数据/配置影响、兼容风险、测试范围和后续 skill handoff。 |
| TRD 沉淀 | `write-trd` | 已有 PRD、明确产品需求或确定 feature scope，需要转成技术方案时。 | 架构边界、接口契约、数据模型、状态流转、安全、可观测性、兼容迁移、测试策略和执行计划输入。 |
| 执行计划 | `write-execution-plan` | 技术方案已经明确，需要拆成可执行步骤、依赖顺序和并发方案时。 | 实施 DAG、关键路径、风险优先级、验证节点、subagent 并发判断和子计划。 |
| 远端交接 | `prepare-remote` | 执行计划已经批准或某个 DAG 节点需要委派给另一台机器、远端 Codex、GitHub Issue 或任务文件时。 | 远端任务包、来源文档引用、依赖关系、并行边界、写入所有权、验收标准和反馈格式。 |
| 计划实现 | `implement-plan` | 已有执行计划，需要按节点实现、验证、合并 subagent 产物并推进闭环时。 | 节点级实现记录、TDD/回归/特征/手工验证选择、阶段验证结果和进度更新。 |
| Bug 修复 | `bug-reproduction` | 用户报告 broken behavior、失败命令、失败页面、失败 API、CI 失败或回归问题时。 | 预期与实际行为、真实入口、最小复现、日志/网络/数据/状态证据、已确认事实和修复方向。 |
| 重构 | `refactor-plan` | 需要重组代码、简化结构、解耦、抽取模块、减少重复或清理技术债时。 | 重构目标、行为保护、风险点、执行步骤、验证方式、回滚点和完成标准。 |
| 提交准备 | `prepare-commit` | 需要 review pending changes、整理提交、stage 相关文件、生成提交信息或完成 commit 时。 | Diff review 结论、验证结果、暂存范围、commit message、最终工作区状态。 |
| 技能复盘 | `skill-retrospective` | 真实任务暴露出 skill 触发、流程、handoff、输出、验证或命名问题，需要轻量迭代时。 | 反馈归纳、最小修订、结构校验结果和后续观察点。 |

## Installation

仓库根目录提供了幂等的安装/卸载脚本，会把 `skills/` 下每个子目录软链到 `~/.codex/skills/`（可用 `CODEX_HOME` 覆盖目标 Codex 目录）。安装时会检测 `graphify` 是否可用，缺失时通过 `uv tool install --upgrade graphifyy` 或 `python3 -m pip install graphifyy` 安装。

```bash
cd /path/to/dev-skills
./install.sh              # 安装（已存在则跳过，重复运行安全）
./install.sh --dry-run    # 仅打印计划，不改磁盘
./install.sh --uninstall  # 卸载（只移除 dev-skills 自己的软链）
```

新机器一键安装：

```bash
git clone git@github.com:shawnxie94/dev-skills.git ~/dev-skills
~/dev-skills/install.sh
```

软链方式意味着后续在仓库内编辑 `SKILL.md` 或新增 skill 都会热生效，无需手动同步。
