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

如果某个工作区希望把 PRD、TRD、执行计划等过程结果沉淀为可管理的文档资产，agent-brain 管理的项目应在 `.agent/config.toml` 中添加：

```text
.agent/config.toml
```

独立使用 dev-skills、没有 agent-brain attach surface 的工作区，仍可使用
`.dev-skills/config.toml` 作为兼容入口。若 `.agent/config.toml` 存在，则只
读取其中的 `[document_artifacts]`；只有 `.agent/config.toml` 不存在时，才回退
读取 `.dev-skills/config.toml`。

最小配置：

```toml
[document_artifacts]
enabled = true
```

This is a workspace-local behavior switch rather than a shared skill source
file, so `.agent/` and standalone `.dev-skills/` configuration should normally
remain gitignored. If a team wants to standardize artifact mode, it can
explicitly force-add the config or copy the same setting into its own project
convention.

开启后，支持该模式的 skill 必须把主要产物写入工作区文件，并在回复中给出文件路径和简短摘要。缺失配置文件、缺失 `document_artifacts.enabled`，或值不是 `true` 时，都按关闭处理。

默认目录约定：

```text
docs/research/
docs/estimates/
docs/prd/
docs/trd/
docs/plans/
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
execution_plan = "docs/plans"
task_draft = "tasks/draft"
task_ready = "tasks/ready"
task_in_progress = "tasks/in-progress"
task_blocked = "tasks/blocked"
task_done = "tasks/done"
decision = "decisions"
```

## 运行反馈与仓库校验

仓库不自动收集原始 prompt 或业务内容。为了让 skill 复盘有实际证据，可以在重要任务结束后记录一条本地运行事件：

```bash
python3 scripts/record_skill_run.py \
  --skill codebase-analysis \
  --status completed \
  --validation pass \
  --task-type orientation \
  --next-handoff write-trd
```

默认记录到 `~/.codex/dev-skills-runs.jsonl`，也可以通过 `DEV_SKILLS_RUN_LOG` 或 `--path` 改为其他本地文件。记录只包含结果元数据、简短 friction tag 和可选短反馈，不应写入原始 prompt、源码、密钥或业务数据。使用以下命令生成近期开工情况摘要：

```bash
python3 scripts/summarize_skill_runs.py \
  --path ~/.codex/dev-skills-runs.jsonl \
  --since-days 30
```

提交前或 CI 中运行仓库级契约检查：

```bash
python3 scripts/check_skill_contracts.py
```

该检查会校验 skill 元数据、Agent 配置、内部引用和 README 覆盖情况；各 skill 的结构校验仍由 `quick_validate.py` 负责。

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

建议按照研发流程从上到下选择 skill。专项场景可以按需插入，例如遇到 bug 先走 `bug-reproduction`，做重构先走 `refactor-plan`，涉及影响面不清楚时插入 `codebase-analysis`（impact 模式）。

| 场景 | Skill | 时机 | 主要产物 |
| --- | --- | --- | --- |
| 调研（brief/deep） | `research` | 想法或需求需要调研输入时。`brief` 模式用于原始想法、技术方向、业界实践、盲点和低成本决策；`deep` 模式用于跨业务流程、系统边界、合规或需要冻结正式输入的深度调研。 | brief：调研简报、可选方向、风险盲点；deep：Requirement Research Packet、证据矩阵、冻结估时工作项。 |
| 交付估时（review/synthesis） | `delivery-estimation` | `review` 模式：Reviewer 基于完全相同的冻结输入和标准独立产出密封估时，并将模型作为主要变量交叉验证；`synthesis` 模式：Research Lead 汇总三份或更多密封估时、定位离散项并形成可信规划区间。 | review：逐工作项人月 O/M/P 与 PERT 估时、复用策略、P50/P80、机器可校验 JSON；synthesis：可比性校验、中位数/范围/离散度、复核项与共识报告。 |
| PRD 沉淀 | `write-prd` | 需求内容已经讨论清楚或基本成型，需要沉淀为产品需求文档时。 | 目标、范围、用户场景、功能需求、非功能需求、验收标准和后续设计输入。 |
| 交付就绪评估 | `delivery-readiness` | 正式跨阶段交接（PRD→TRD→计划→实现→验证→发布）、plan-linked/batch-linked 交付、高风险发布或迁移前的阶段门禁，循环评估直到 ready 或 blocked；非正式小改动不触发。 | 阶段门禁、需求/设计/计划追踪、稳定问题 ID、源文件哈希、修复循环和可追溯 readiness report。 |
| 原型/UI 规格 | `prototype-ui` | PRD 已定型但布局、流程、状态、视觉方向或交互仍是未验证假设，需要在 TRD 前完成设计收口时；内置视觉方向流程，默认本地静态原型，可选 Huashu Design、OpenDesign 或 Figma 作为外部 provider。 | 仓库内可点击 HTML 原型、视觉方向、页面/流程/状态清单、UI 验收点和 TRD 输入。 |
| 代码库分析（orientation/deep-dive/impact） | `codebase-analysis` | `orientation` 模式：在既有仓库里做设计、计划、调试或实现前需要先理解系统现状（技术栈、运行命令、模块、入口、数据流、风险边界，有索引时由 CodeGraph 支撑）；`deep-dive` 模式：需要研究级深读——核心 loop、执行 harness、模块设计、设计思想——并沉淀为持久学习笔记时；`impact` 模式：某个改动、接口、数据结构、配置、依赖或重构的影响范围不清楚时。三个模式默认互斥，只在陌生仓库需要时先 orientation 再 deep-dive/impact 分步组合。 | orientation map、深度解读笔记（写入用户学习笔记目录，如 `~/Developer/learn/notes/`，并登记其 INDEX）或 impact report（受影响模块、契约、数据/配置影响、兼容风险、测试范围）。 |
| TRD 沉淀 | `write-trd` | 已有 PRD、明确产品需求或确定 feature scope，需要转成技术方案时。 | 架构边界、接口契约、数据模型、状态流转、安全、可观测性、兼容迁移、测试策略和执行计划输入。 |
| 执行交付（plan/delegate） | `execution-delivery` | `plan` 模式：先评估并行收益并由用户选择 `batch` 或 `parallel_dag`，再生成对应计划；`delegate` 模式：计划批准后由用户选择当前会话或子智能体执行。 | plan：整体执行计划或并行 DAG（写入边界、验收、plan hash）；delegate：当前会话路由或有界子智能体任务包（来源引用、依赖、并行边界、验收和反馈格式）。 |
| 计划实现 | `implement-plan` | 已有整体执行计划、并行 DAG 节点或委派任务，需要按已确定的执行策略实现和验证时。 | `batch`：完整 goal 的实现与内部验证；`parallel_dag`：节点级实现和验收证据；不自行改变执行策略。 |
| 发布交付 | `release-delivery` | 已有通过 Quality Gate 的候选版本，需要确定性发现项目 runbook、校验合并/环境审批和备份/回滚证据、部署或回滚时。 | 只读发布计划、候选与证据绑定、runbook 执行约束、smoke/观察记录和 Release Result。 |
| Bug 修复 | `bug-reproduction` | 用户报告 broken behavior、失败命令、失败页面、失败 API、CI 失败或回归问题时。 | 预期与实际行为、真实入口、最小复现、日志/网络/数据/状态证据、已确认事实和修复方向。 |
| 重构 | `refactor-plan` | 需要重组代码、简化结构、解耦、抽取模块、减少重复或清理技术债时。 | 重构目标、行为保护、风险点、执行步骤、验证方式、回滚点和完成标准。 |
| 提交准备 | `prepare-commit` | 需要 review pending changes、整理提交、stage 相关文件、生成提交信息或完成 commit 时。 | Diff review 结论、验证结果、暂存范围、commit message、最终工作区状态。 |
| 技能复盘 | `skill-retrospective` | 真实任务暴露出 skill 触发、流程、handoff、输出、验证或命名问题，需要轻量迭代时。 | 反馈归纳、最小修订、结构校验结果和后续观察点。 |

## Recommended Skill Chains

按任务复杂度选择最短可用链路，不要求每次都走完整流程：

- 轻量调研：`research`（brief）→ `write-prd` 或 `write-trd`。
- 正式需求分析：`research`（brief，可选）→ `research`（deep）→ `write-prd` → `prototype-ui`（UI 假设未验证时）→ `write-trd`。
- 多模型交叉估时：`research`（deep）→ 三个或更多 Reviewer 分别运行 `delivery-estimation`（review）→ Research Lead 运行 `delivery-estimation`（synthesis）。
- 复杂需求交付：`write-prd` → `delivery-readiness`（prd_to_trd，正式交接时）→ `write-trd` → `delivery-readiness`（trd_to_plan，正式交接时）→ `execution-delivery`（先评估并行，再生成 `batch` 或 `parallel_dag` plan）→ `delivery-readiness`（plan_to_build，进入实现前）→ `execution-delivery`（delegate，选择当前会话或子智能体；子智能体再选 `codex_subagent` 或 `zcode_mcp`）→ `implement-plan` → 整体验收/集成验收 → `prepare-commit` → `release-delivery`（获得对应审批后）。readiness 门是显式阶段门，非正式小改动不进 gate。
- 简单改动：直接使用对应专项 Skill 或 `implement-plan` 的轻量模式，完成聚焦验证后进入 `prepare-commit`，不强制创建 PRD、TRD 或多 Agent DAG。

## Multi-Agent Orchestration

在 Multica、Squad、managed-agent platform 或其他外部编排器中使用时，建议把 Skill 视为角色能力和执行协议，把任务拆分、状态推进、重试和汇总留给外部编排器：

- Research Lead：绑定 `research`（brief）和 `delivery-estimation`（synthesis），负责研究契约、Reviewer 隔离、差异复核和最终汇总。
- Requirement & Solution Analyst：绑定 `research`（deep），必要时串联 `write-prd`、`write-trd`、`codebase-analysis`（orientation/impact）。
- Estimation Reviewer：只绑定 `delivery-estimation`（review 模式）；所有 Reviewer 使用相同冻结输入、指令、Skill 版本和输出格式，首轮不读取其他估时也不读取 synthesis 逻辑，模型或 runtime 作为主要变量。
- Delivery Actor：`batch` 计划绑定一个完整 goal 的 `implement-plan`；`parallel_dag` 计划按节点绑定 `implement-plan` 及节点要求的专项 Skills。子智能体只执行收到的整体 goal 或当前节点，不自行改变计划形态、认领 sibling issue 或递归创建 Agent。
- Release Operator：只绑定 `release-delivery`；从项目 profile 的 `release.yaml` 精确定位 runbook，候选/QG/审批/备份/回滚证据不完整时停止，不自行批准合并或生产发布。

`execution-delivery`（plan 模式）先产出平台无关的并行性评估；用户选择后，`batch` 计划产出一个整体 Actor 契约，`parallel_dag` 计划的每个节点产出 Actor 契约。契约至少包含 required capabilities、required skills、write ownership、forbidden writes、verification 和 handoff readiness。

## 与 agent-brain 的任务契约衔接

当执行任务通过 agent-brain 的外循环运行时，两个仓库各自负责一层：

- `agent-brain` 的 Task Pack 是外部合同，负责目标、范围、`allowed_paths`、canonical acceptance、基线和最终 Done 门。
- `dev-skills` 是内部研发能力，负责调研、设计、计划、交接、实现和提交前检查；Skill 不另造一套 acceptance 真相。
- 默认采用短输出策略：模型先读当前节点和最小相关证据，按
  `git diff --name-only` → `git diff --stat` → 必要时完整 diff 的顺序探索；
  通过的命令只回报状态/计数，完整 stdout/stderr 留在日志中，失败才回报尾部诊断。
  Context Pack、Experience episode、handoff 和证明流程完整性的文档按需读取，
  不作为每轮默认上下文。
- `execution-delivery`（plan 模式）应携带 `orchestration_mode`、`plan_id`、`source_plan_sha256`、`base_commit`、`task_id`、`source_artifacts`、`source_hash`、`acceptance_ids` 和 `evidence_required`；执行目标和 backend 在交接时补齐。
- `execution-delivery`（delegate 模式）要原样传递这些字段，并明确 `execution_target`；当目标为 `subagent` 时还必须选择 `execution_backend=codex_subagent|zcode_mcp`，同时传递 `required_skills`、`write_ownership`、`forbidden_writes`、依赖和 worktree 隔离。
- 两个 subagent backend 都是执行适配器：Codex 使用 `multi_agent_v1__spawn_agent` / `multi_agent_v1__wait_agent`，ZCode 使用 `mcp__zcode_codex__zcode_dispatch` 及其状态/继续接口；运行时工具未提供时必须报告阻塞，不得假装已委派。
- 远端或多 Agent 执行时，由 Task Pack 生成 Acceptance Pack；验收证据必须包含 `acceptance.json`、scope 结果和必要的测试/手工确认。文字声称、host goal 完成或子 Agent 返回成功都不能单独构成 Done。
- 状态推进规则：`ready` 只表示依赖满足且可领取；`done` 只表示实现分支完成；只有 Acceptance Pack source hash 匹配且 evidence `overall=pass` 才能进入 `accepted`，下游任务据此 promotion。`skipped` 必须由用户拥有 residual risk，不能自动 promotion。
- 多 Agent 并发前必须检查规范化后的 `write_ownership`、mutex、branch/worktree 和 base commit；共享 contract/schema/migration/generated artifact 默认单写者。

多 Agent 的 worktree 策略不是“一任务一 worktree”：先做影响分析并标记并发模式。只读分析可共享工作区并行；可安全串行的独立写入可复用工作区；只有真正需要同时写入代码的任务才强制独立 branch/worktree。

推荐衔接：

```text
TRD / settled scope
  → execution-delivery plan (parallelism assessment → batch or DAG + contract linkage)
  → execution-delivery delegate (current session or bounded subagent packet + source hash)
  → agent-brain Task Pack (canonical acceptance + baseline)
  → implement-plan (whole-goal batch or node-scoped build/verify)
  → acceptance.json + scope evidence
  → prepare-commit
```

## Installation

仓库根目录提供了幂等的安装/卸载脚本，会把 `skills/` 下每个子目录软链到选定 runtime 的 Skill 目录：默认是 `~/.codex/skills/`，使用 `--target claude` 时是 `~/.claude/skills/`，使用 `--target zcode` 时是 `~/.zcode/skills/`（可分别用 `CODEX_HOME` / `CLAUDE_HOME` / `ZCODE_HOME` 覆盖）。安装时会检测 `codegraph` 是否可用，缺失时通过官方 macOS/Linux 安装脚本或 `npm install -g @colbymchenry/codegraph` 安装，并为选定 runtime 执行对应的 CodeGraph 配置（zcode 暂无 codegraph 集成，只检查二进制，不写 MCP 配置）。可设置 `CODEGRAPH_CONFIGURE=0` 跳过配置写入。卸载时会同时清掉仍指向本仓库 `skills/` 但已不存在的旧 skill 死链。

```bash
cd /path/to/dev-skills
./install.sh              # 安装到 Codex（已存在则跳过，重复运行安全）
./install.sh --target claude # 安装到 Claude Code
./install.sh --target zcode  # 安装到 ZCode
./install.sh --dry-run    # 仅打印计划，不改磁盘
./install.sh --uninstall  # 卸载（移除 dev-skills 软链，含旧 skill 死链）
./uninstall.sh --target claude # 卸载 Claude Code 的软链
```

新机器一键安装：

```bash
git clone git@github.com:shawnxie94/dev-skills.git ~/dev-skills
~/dev-skills/install.sh
```

软链方式意味着后续在仓库内编辑 `SKILL.md` 或新增 skill 都会热生效，无需手动同步。
