# Codebase Deep Dive (deep-dive mode)

Mode reference for the `$codebase-analysis` skill. Read this file only after the router selects `deep-dive`: a study-grade walkthrough of how a project actually works (core loops, execution harness, module design) and why it is designed that way, ending in a durable markdown note. Where `orientation` builds a quick map with chat output, this mode produces the guided tour and the artifact.

## Core Principles

- **Depth is selective, not exhaustive.** Read every layer at summary level, but read only the *core paths* line by line. Identify the one or two loops/mechanisms that make the project tick and spend most effort there.
- **Verify with live files.** CodeGraph (`.codegraph/` index) is the retrieval backend and gives verbatim line-numbered source, but stale indexes lie. Cross-check graph leads against the on-disk file before claiming anything. Read `AGENTS.md`, README, and manifests directly for run/test commands and conventions.
- **Design ideas come from evidence, not vibes.** Every "design principle" you claim must map to a concrete mechanism you read (a type, a lock, a loop, an invariant enforced by code or comments).
- **Do not guess APIs or flows.** If a surface is unread, mark it as unexplored/open question.
- **Produce the artifact.** Unless the user says chat-only, write the deep-dive to a durable note file so the effort compounds.
- **Stay in the user's language** unless they request otherwise.

## Workflow

### Stage 0 — Scoping and index readiness

1. Confirm the target repo root and what the user wants depth on (whole project, or a specific subsystem like "core loop / harness / protocol / sandbox"). **This user's convention: projects live under `~/Developer/learn/project/`** (e.g. `project/codex`, `project/pi`); notes go to `~/Developer/learn/notes/`. Start from those paths when the repo was moved unless the user says otherwise.
2. Check retrieval backend state:
   ```bash
   codegraph --version
   codegraph status --json <repo-root>
   ```
   - Inspect `initialized`, `pendingChanges`, `index.state`, `index.pendingRefs`, `index.reindexRecommended`.
   - Not initialized → report it, then initialize when indexing is in scope (user asked for a deep dive, so it usually is): `cd <repo-root> && codegraph init .`
   - Pending changes → `codegraph sync <repo-root> --quiet` before retrieval; `reindexRecommended` → `codegraph index <repo-root> --quiet`.
   - Stale lock → `codegraph unlock <repo-root>`. CLI unavailable → say so and fall back to live-file reading; do not claim graph-backed coverage. In pi, the CLI is the only path (no MCP client).
3. Decide the notes destination early (see Stage 4).

### Stage 1 — Fast recon (live files)

- Top-level layout: `ls -d */`, root README first 80 lines.
- Language/package metadata: `Cargo.toml` (Rust), `package.json` (TS/JS), `pyproject.toml` (Python), `go.mod`, etc. Count workspace members / packages — a large workspace count is itself a design fact.
- Conventions: `AGENTS.md` / `CLAUDE.md` / contributor docs (they encode the project's own engineering rules — gold for the "design ideas" stage).
- Entry points: `main`, `src/bin/*`, `cli`, app/server entry, routes.
- Build/test/run commands from README + CI files (`.github/workflows`).

### Stage 2 — Architecture survey with CodeGraph

Use `codegraph explore "<question>" --path <root>` (CLI; where the host wires CodeGraph's MCP server, `codegraph_explore` is the equivalent) with questions, plus targeted primitives:

- "What are the main components and how do they relate?" → layering, directories
- `codegraph query <symbol>` — symbol lookup
- `codegraph node <symbol>` — one symbol's source plus caller/callee trail
- `codegraph callers/callees <symbol>` — direction of dependency/flow (use this to *prove* layering rather than assuming it from folder names)
- `codegraph impact <symbol>` — blast radius / core-ness signal (the symbol with 100+ callers is likely the heart)

From this, produce:
- **Layer diagram** (ASCII or mermaid): frontends → API/protocol → core → execution/transport → platform.
- **Boundary contracts**: where protocol types are defined (dedicated crates? generated TS? schema fixtures?), how cross-process calls are transported.
- **Module table**: path / responsibility / why it exists.
- **"Swiss-army entry" hypothesis**: check whether one binary/CLI dispatches multiple subcommands (argv[0], subcommand enum, `--server` modes).

### Stage 3 — Core loop / harness deep read (the heart)

Work top-down into the one loop that drives the system, then read it line by line. Generic template to look for (verify, don't assume):

1. **Event/actor loop** — single consumer of commands (`mpsc` channel, `while let Some(op) = rx.recv()`), one mutex point. Understand: all inputs funnel through here → concurrency collapses to serialization.
2. **Task/wrap loop** — a higher-level unit (request, turn, job) that may internally loop over steps (drain pending input → continue).
3. **Inner sampling/processing loop** — streaming consumer over an event stream; states per event; where outputs fan out (UI events, persistence, tool execution).
4. **Read these carefully and quote the source** when writing the note: the exact `loop {}` + match arms, the concurrency primitives (`RwLock` as semaphore, `CancellationToken`, `AbortOnDropHandle`, `FuturesOrdered` for overlapped streaming + tool execution), the snapshot/per-request immutable context struct, and any RAII guards (Drop-based release of limits).
5. Along the way note **invariants the code enforces by type or assert** (e.g., "rejected input leaves thread unchanged", "at most one active task", "context fragments ≤ N tokens", "parallel tool calls share read lock, serial tools take write lock").

Also cover, at summary depth: persistence/state (how is history written — JSONL? SQLite? background writer? snapshot+diff?), config layering, observability (tracing spans, W3C trace headers, pre-declared span fields), and error/resilience design (fallbacks, degradation, cancellation cooperation).

### Stage 4 — Extract design philosophy, then write the artifact

1. Turn observed mechanisms into 5–10 design principles, each paired with the concrete code evidence (include file:line references in the note).
2. **Notes destination**: default to `~/Developer/learn/notes/` (the user's learning-notes folder). Confirm it exists (`ls -d ~/Developer/learn/notes`), follow any repo/AGENTS convention for note paths if present, and allow the user to override. Filename pattern: `<project-slug>-<topic>.md` (e.g., `codex-cli-deep-dive.md`, `codex-core-loop-harness.md`). Multiple deep dives on one project append as sibling files; link to the previous note as a companion ("姊妹篇").
3. Include frontmatter-lite header: topic, date, source repo path, companion links, retrieval method (CodeGraph version + index path).
4. **Update the notes index** at `~/Developer/learn/notes/INDEX.md`: add or refresh the repo's row with paths to the new note(s) and a 2–3 line summary. This keeps future deep dives linkable to past reads (see Notes Index below).
5. Keep the final chat reply concise: file path, one-paragraph summary, and the top 3 things the reader should know. Do not duplicate the full document in chat unless asked.

## Output Document Template

Use this structure (compress for small repos):

```markdown
# <Project> 深度解读 — <Topic>

> 生成时间 / 来源（repo 路径）/ 姊妹篇链接 / 检索方式（CodeGraph 版本 + 索引）

## 0. 定位
<这个项目是什么、核心价值、规模事实（crate/package 数、测试数、快照数）>

## 1. 总体架构
<分层图 + 边界契约 + 模块表>

## 2. 核心流程（核心 loop 逐段讲解）
<流程伪代码 + 关键数据结构 + 每层职责>

## 3. 核心机制深读
<事件循环 / 工具执行 / 并发控制 / 快照 / 状态管理 等，逐个深入>

## 4. 技术设计亮点
<5–10 个设计思想，每个配证据>

## 5. 设计哲学总结
<要点式>

## 6. 推荐继续阅读
<文件路径 + 为什么>

## 附：关键文件速查
<path | 职责 | 规模>
```

## Notes Index（已解读项目联动）

The learning-notes folder keeps the registry of every project this mode has deep-read: `~/Developer/learn/notes/INDEX.md`. It maps each repository to its archived notes with short summaries. The index is a learning-domain document owned by the notes folder itself — this mode maintains it, but never stores it inside the skill. Purpose:

- **Fast linkage**: at mode start, read the index first; if the target repo already has notes, offer to refresh, link, or build on them instead of re-reading from scratch.
- **Cross-project pattern library**: after several deep dives, the index doubles as a corpus of "design ideas seen in the wild".
- **No duplication**: full documents live in the notes folder; the index only points to them. Do not copy document bodies into the index — that creates two sources of truth that drift.

Index entry format (notes are siblings of the index, so plain relative links):

```markdown
| Repo | Notes | Summary |
|---|---|---|
| `path/to/repo` (项目说明) | [`<slug>.md`](<slug>.md) · [`<slug2>.md`](<slug2>.md) | <2–3 行摘要> |
```

## Quality Gates

Before finishing, self-check:

- [ ] Every design claim has a concrete code reference (file + line or function name).
- [ ] Layer diagram is verified by callers/callees direction, not just folder names.
- [ ] Core loop was actually read line-by-line (not paraphrased from memory).
- [ ] The note answers both "how it works" and "why it's designed that way".
- [ ] Unexplored areas are explicitly marked as open questions, not silently skipped.
- [ ] Artifact written (or user explicitly declined it).
- [ ] Notes index row added/refreshed.

## Worked Example

See [`codex-case-study.md`](codex-case-study.md) for a condensed worked example: how the codex-rs deep dive mapped this workflow onto a real codebase (stages, key queries, and how the two notes were produced).
