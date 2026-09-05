# Worked Example — codex-rs Deep Dive

> 浓缩版案例：codex-rs（OpenAI Codex CLI 官方 Rust 实现）的深度解读如何走完整个 workflow，以及产出物长什么样。
> 完整文档见 `~/Developer/learn/notes/codex-cli-deep-dive.md` 与 `codex-core-loop-harness.md`。
> 关键教学点：**先定位项目的心脏（core loop），其余部分保持摘要深度**。

## 项目背景

- 118 个 Rust workspace crates（`codex-rs/` 下），Bazel + Cargo 双构建，144 个 core 集成测试套件、754 个 TUI snapshot。
- 定位：终端 AI 编码代理 + 桌面/IDE 后端，与 ChatGPT 云端联动的完整链路。

## Stage 1 — 快速侦察关键招

- `ls -d */` 顶层 + README 前 80 行 → 判断这是 Codex CLI（不是玩具项目）。
- `Cargo.toml` 的 workspace members 数（118）→ **workspace 数量本身是设计事实**（细粒度 crate 拆分的纪律）。
- 入口侦察：`cli/src/main.rs` 的 `arg0_dispatch_or_else` + 子命令枚举 → 确认"一个二进制当瑞士军刀"（codex / exec / review / app-server / mcp-server 全在 main 分派）。

## Stage 2 — 架构梳理关键招

- `codegraph explore "How does the agent thread work...?"` → 返回 `CodexThread`（129 callers）→ **高 caller 数的符号 = 心脏**。
- crate 分组确认分层：`protocol/`、`app-server-protocol/`、`exec-server-protocol/` 各自独立 → 边界契约由类型强约束。
- `compile_data` 事实：`#[ts(export_to = "v2/")]` 生成 TypeScript 类型 → wire 格式 Rust/TS 永久对齐。

## Stage 3 — 核心 loop 深读（主要时间花在这）

用三层循环模板定位并逐行读：

1. **L1 事件循环**：`session/handlers.rs:524` `submission_loop` — 单消费者 mpsc，~30 种 `Op` 串行分派。结论：Actor 模型，并发坍缩为串行化，锁只剩 `active_turn` 等少数字段。
2. **L2 Task 循环**：`tasks/regular.rs` — 一次"任务"可含多次 `run_turn`，用"input_queue 是否还有未消费输入"做继续条件。
3. **L3 采样循环**：`session/turn.rs` 2821 行 — `loop { stream.next() }` 流式事件状态机；`FuturesOrdered` 交错工具执行与继续消费流；`RwLock<()>` 当信号量控制并行/串行工具；`terminal_outcome_reached: Arc<AtomicBool>` 协作式取消协议。

散点收获（摘要级记录）：rollout JSONL 后台 writer + 反向扫描、`ContextManager` 写时复制历史、世界状态 diff 做 JSON patch 持久化。

## Stage 4 — 设计思想提炼（每条配证据）

实际产出的 7 条原则示例：

- Actor + 串行化 → `submission_loop` 单消费者设计。
- 快照而非查询 → `StepContext` 冻结每次请求的全部配置，模型所见即所得。
- 流式流水线 → `FuturesOrdered` 不阻塞交错。
- 一切皆事件 → `Op` 进 / `Event` 出，UI 纯消费者。
- 硬约束编码进类型 → Plan 模式保护、root turn 归属、上下文 ≤10K tokens。
- 可观测性一等公民 → 每个 span 预埋 token 字段、工具三段计时、W3C trace。
- 弹性韧性 → compaction 远程/本地多级 fallback、取消协作协议、rollout 写失败降级 Warning。

## 产出物

- `codex-cli-deep-dive.md`：横向架构地图（分层图 + 模块表 + 功能板块 + 亮点 + 阅读路径）。
- `codex-core-loop-harness.md`：纵向执行链路（三层循环逐层 + 文件速查表）。
- 两者互为"姊妹篇"，头尾互链。

## 教训

- 一次 deep dive 分两篇更易读：横向地图 + 纵向核心链路；后续可按子系统再出第三篇（协议/沙箱/MCP）。
- 深读 must 引用行号；`codegraph explore` 的返回自带行号源码，直接引用即可，但改动过的文件要重新 `sync` 后以磁盘为准。