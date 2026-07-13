# dev-skills

将研发流程中可复用的单点能力沉淀为 skills，尽量保持轻量高效。每个 skill 只解决一个明确问题，提供必要的流程约束、检查维度和输出格式，避免做成过重的知识库或泛化文档。

## Design Principles

- 单点能力：一个 skill 聚焦一个研发动作，例如调研、重构规划、提交前检查。
- 轻量优先：优先使用精简的 `SKILL.md`，只有确实需要时才增加 scripts、references 或 assets。
- 流程约束：把容易遗漏的步骤、风险点和验证方式固化下来。
- 可执行输出：skill 的产物应能直接进入下一步研发流程，而不是停留在泛泛建议。
- 可组合：skills 之间能串成研发流程，而不是互相重叠。
- 复用优先：方案和估时优先复用成熟的内部组件、托管服务、官方库或维护良好的开源组件；只有需求明确要求自研时才单独建设。若成熟方案无法满足关键约束，先形成决策项并获得明确的自研批准，不能默认造轮子。

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
docs/research/
docs/estimates/
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
research = "docs/research"
delivery_estimates = "docs/estimates"
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
| 深度需求调研 | `requirement-deep-research` | 需求跨业务流程、系统边界、技术选项或外部证据，需要形成可追踪且可供方案与估时复用的正式输入时。 | Requirement Research Packet、证据矩阵、功能/流程/系统边界、冻结估时工作项。 |
| 独立交付估时 | `delivery-estimation-standard` | 多个 Reviewer 需要基于完全相同的冻结输入和标准独立估时，并将模型作为主要变量进行交叉验证时。 | 逐工作项人月 O/M/P 与 PERT 估时、成熟组件复用策略、角色总量、P50/P80、假设与机器可校验 JSON。 |
| 估时综合评审 | `synthesize-delivery-estimates` | Research Lead 需要汇总三份或更多独立估时、定位离散项并形成可信规划区间时。 | 可比性校验、中位数/范围/离散度、复核项、Lead 综合结论与审计链。 |
| PRD 沉淀 | `write-prd` | 需求内容已经讨论清楚或基本成型，需要沉淀为产品需求文档时。 | 目标、范围、用户场景、功能需求、非功能需求、验收标准和后续设计输入。 |
| 代码库导向 | `codebase-orientation` | 在既有仓库里做设计、计划、调试或实现前，需要先理解系统现状时。 | 技术栈、运行验证命令、模块职责、入口路径、数据流、依赖集成、测试方式和风险边界。 |
| 影响面分析 | `change-impact-analysis` | 某个改动、接口、数据结构、配置、依赖或重构的影响范围不清楚时。 | 受影响模块、接口契约、数据/配置影响、兼容风险、测试范围和后续 skill handoff。 |
| TRD 沉淀 | `write-trd` | 已有 PRD、明确产品需求或确定 feature scope，需要转成技术方案时。 | 架构边界、接口契约、数据模型、状态流转、安全、可观测性、兼容迁移、测试策略和执行计划输入。 |
| 执行计划 | `write-execution-plan` | 技术方案已经明确，需要拆成可执行步骤、依赖顺序、执行 Actor 和并发方案时。 | 实施 DAG、关键路径、风险优先级、能力/Skill 要求、写入边界、验证节点和 Actor 执行契约。 |
| 远端交接 | `prepare-remote` | 执行计划已经批准或某个 DAG 节点需要委派给另一台机器、远端 Codex、managed-agent issue、Squad child issue、GitHub Issue 或任务文件时。 | 委派任务包、来源文档引用、依赖关系、能力/Skill 要求、并行边界、写入所有权、验收标准和反馈格式。 |
| 计划实现 | `implement-plan` | 已有执行计划或具体 managed-platform 节点，需要按当前节点实现、验证并推进闭环时。 | 节点级实现记录、TDD/回归/特征/手工验证选择、阶段验证结果和进度更新。 |
| Bug 修复 | `bug-reproduction` | 用户报告 broken behavior、失败命令、失败页面、失败 API、CI 失败或回归问题时。 | 预期与实际行为、真实入口、最小复现、日志/网络/数据/状态证据、已确认事实和修复方向。 |
| 重构 | `refactor-plan` | 需要重组代码、简化结构、解耦、抽取模块、减少重复或清理技术债时。 | 重构目标、行为保护、风险点、执行步骤、验证方式、回滚点和完成标准。 |
| 提交准备 | `prepare-commit` | 需要 review pending changes、整理提交、stage 相关文件、生成提交信息或完成 commit 时。 | Diff review 结论、验证结果、暂存范围、commit message、最终工作区状态。 |
| 技能复盘 | `skill-retrospective` | 真实任务暴露出 skill 触发、流程、handoff、输出、验证或命名问题，需要轻量迭代时。 | 反馈归纳、最小修订、结构校验结果和后续观察点。 |

## Recommended Skill Chains

按任务复杂度选择最短可用链路，不要求每次都走完整流程：

- 轻量调研：`research-brief` → `write-prd` 或 `write-trd`。
- 正式需求分析：`research-brief`（可选）→ `requirement-deep-research` → `write-prd` → `write-trd`。
- 多模型交叉估时：`requirement-deep-research` → 三个或更多 Reviewer 分别运行 `delivery-estimation-standard` → Research Lead 运行 `synthesize-delivery-estimates`。
- 复杂需求交付：`write-trd` → `write-execution-plan` → `prepare-remote`（需要委派时）→ `implement-plan` → `prepare-commit`。
- 简单改动：直接使用对应专项 Skill 或 `implement-plan` 的轻量模式，完成聚焦验证后进入 `prepare-commit`，不强制创建 PRD、TRD 或多 Agent DAG。

## Multi-Agent Orchestration

在 Multica、Squad、managed-agent platform 或其他外部编排器中使用时，建议把 Skill 视为角色能力和执行协议，把任务拆分、状态推进、重试和汇总留给外部编排器：

- Research Lead：绑定 `research-brief` 和 `synthesize-delivery-estimates`，负责研究契约、Reviewer 隔离、差异复核和最终汇总。
- Requirement & Solution Analyst：绑定 `requirement-deep-research`，必要时串联 `write-prd`、`write-trd`、`codebase-orientation` 和 `change-impact-analysis`。
- Estimation Reviewer：只绑定 `delivery-estimation-standard`；所有 Reviewer 使用相同冻结输入、指令、Skill 版本和输出格式，首轮不读取其他估时，模型或 runtime 作为主要变量。
- Delivery Actor：按 DAG 节点绑定 `implement-plan` 及节点要求的专项 Skills；收到具体 child issue 后只执行当前节点，不自行认领 sibling issue，也不递归创建 Agent，除非明确拥有编排职责。

`write-execution-plan` 产出的每个节点应使用平台无关的 Actor 契约，至少包含 required capabilities、required skills、write ownership、forbidden writes、verification 和 handoff readiness。这样同一计划可以交给本地 Agent、Multica managed Agent、Squad child issue 或远端 worker，而不需要重写任务边界。

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
