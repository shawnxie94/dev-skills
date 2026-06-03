# dev-skills

将研发流程中可复用的单点能力沉淀为 skills，尽量保持轻量高效。每个 skill 只解决一个明确问题，提供必要的流程约束、检查维度和输出格式，避免做成过重的知识库或泛化文档。

## Design Principles

- 单点能力：一个 skill 聚焦一个研发动作，例如调研、重构规划、提交前检查。
- 轻量优先：优先使用精简的 `SKILL.md`，只有确实需要时才增加 scripts、references 或 assets。
- 流程约束：把容易遗漏的步骤、风险点和验证方式固化下来。
- 可执行输出：skill 的产物应能直接进入下一步研发流程，而不是停留在泛泛建议。
- 可组合：skills 之间能串成研发流程，而不是互相重叠。

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
| 计划实现 | `implement-plan` | 已有执行计划，需要按节点实现、验证、合并 subagent 产物并推进闭环时。 | 节点级实现记录、TDD/回归/特征/手工验证选择、阶段验证结果和进度更新。 |
| Bug 修复 | `bug-reproduction` | 用户报告 broken behavior、失败命令、失败页面、失败 API、CI 失败或回归问题时。 | 预期与实际行为、真实入口、最小复现、日志/网络/数据/状态证据、已确认事实和修复方向。 |
| 重构 | `refactor-plan` | 需要重组代码、简化结构、解耦、抽取模块、减少重复或清理技术债时。 | 重构目标、行为保护、风险点、执行步骤、验证方式、回滚点和完成标准。 |
| 提交准备 | `prepare-commit` | 需要 review pending changes、整理提交、stage 相关文件、生成提交信息或完成 commit 时。 | Diff review 结论、验证结果、暂存范围、commit message、最终工作区状态。 |
| 技能复盘 | `skill-retrospective` | 真实任务暴露出 skill 触发、流程、handoff、输出、验证或命名问题，需要轻量迭代时。 | 反馈归纳、最小修订、结构校验结果和后续观察点。 |

## Installation

本仓库中的 skill 可以通过软链安装到 Codex：

```bash
ln -sfn /path/to/dev-skills/skills/<skill-name> ~/.codex/skills/<skill-name>
```

安装或更新后，重启 Codex 以重新加载 skills。
