---
name: prototype-ui
description: Turn a settled PRD or product scope into a clickable HTML prototype plus a UI specification that feeds the TRD and implementation. Use when product requirements are already documented but layout, flow, states, or interactions are still unverified assumptions, or when the user asks for a prototype, wireframe, mockup, 原型, 线框, or UI design before technical design. Focus on information architecture, key flows, states, and acceptance points; reuse existing UI stacks and design tokens instead of inventing a visual system.
---

# Prototype UI

Build a clickable prototype and UI specification from a settled PRD before the
TRD. The goal is to surface unverified UI assumptions cheaply, not to produce
production UI.

## Core Principles

- Prototype flows and states, not visual polish. Invoke `frontend-design` only
  when the user asks for a visual direction.
- Reuse the repository's existing UI stack, components, and design tokens when
  present; otherwise use plain HTML/CSS with demo data.
- Keep the prototype single-file or a small static set; no build tooling.
- Keep the UI specification and the repository-materialized prototype as the
  source of truth. A design workspace or visual generator is an optional
  provider, not a replacement for the UI handoff contract.
- Separate prototype decisions from implementation commitments; re-check
  platform constraints (for example WeChat mini-program storage or canvas
  limits) in the TRD.
- The UI spec is the primary handoff artifact; the prototype is evidence that
  the flows work.

## Prototype Provider

Choose the smallest provider that can validate the open UI assumptions:

- `local-static` (default): write the prototype directly in the repository.
  Use this for flow/state validation, ordinary TRD input, or when no visual
  direction is requested.
- `opendesign` (optional): use the connected OpenDesign MCP for high-fidelity
  visual exploration when the user asks for brand-grade output, a design
  system, multiple coordinated screens, responsive/animated treatment, or a
  visual artifact worth iterating on.
- `huashu-design` (optional): use the installed HTML-native design skill when
  visual direction, high-fidelity presentation, animation, infographics, or
  multiple visual variants are the main uncertainty. It is a visual delivery
  provider, not a replacement for the local UI-spec handoff or a production
  application architecture.

When `opendesign` is selected:

1. Keep the current repository as the delivery boundary. An OpenDesign project
   or preview URL is not the final handoff.
2. Prefer project/artifact/file operations to create or inspect the visual
   draft, then pull the complete artifact bundle and materialize the relevant
   files under `docs/prototype/` before browser verification.
3. Continue to produce `docs/prototype/ui-spec.md` locally. Record which visual
   decisions were confirmed by the OpenDesign artifact and which remain open.
4. Do not start a nested OpenDesign Agent run by default from inside Codex. If
   the user explicitly requests it, verify the selected runtime first so the
   Codex -> OpenDesign -> Codex loop is not created accidentally.

If OpenDesign is unavailable, fall back to `local-static` and report that the
visual-provider path was not used; do not block the UI-spec handoff.

When `huashu-design` is selected:

1. Keep the current repository as the delivery boundary. Treat generated HTML,
   screenshots, exports, and any copied assets as review evidence that must be
   materialized under the repository before handoff.
2. Read only the Huashu references relevant to the requested output. Use its
   three-direction exploration for visual-first work, but do not force three
   directions for a settled flow/state prototype unless the user asks for
   visual exploration.
3. Preserve the screen map, flows, states, and acceptance points from this
   skill. Huashu's visual output does not replace `docs/prototype/ui-spec.md`.
4. Do not select `huashu-design` and `opendesign` for the same prototype run
   unless the user explicitly requests a comparison or a two-stage workflow.
   Use Huashu for visual direction and static/high-fidelity HTML; use
   OpenDesign when its project context, artifact workspace, or connected
   design-system workflow is the material advantage.
5. Verify the resulting HTML in a browser and run the relevant interaction
   checks. Do not treat a screenshot, PPTX, or video export as proof that the
   promised product flow works.

## Inputs

- Settled PRD or product scope, platform, and audience constraints.
- Existing design system, components, or style references when available.
- User preferences that affect UI (for example names vs masked identifiers,
  layout modes).

## Workflow

1. Extract UI-relevant decisions from the PRD.
   - List screens, primary flows, and states (empty, loading, error, success).
   - Mark decisions already fixed (layout rules, export content) versus open UI
     assumptions.
2. Define the screen map.
   - One line per screen: purpose, entry/exit, key states, and which flows must
     be clickable.
3. Select the prototype provider.
   - Use `local-static` unless the scope explicitly needs visual exploration or
     the user asks for a visual provider.
   - Use `opendesign` when the connected project context, design-system
     workspace, coordinated artifacts, or responsive treatment is the main
     advantage.
   - Use `huashu-design` when visual direction, high-fidelity HTML, decks,
     animation, or infographics are the main uncertainty.
   - If using `opendesign` or `huashu-design`, preserve the screen map and
     acceptance points as the local constraints for the visual draft.
   - Select one visual provider per run unless the user explicitly requests a
     comparison or a two-stage workflow.
4. Build the prototype.
   - Write `docs/prototype/index.html` (single file preferred) with the repo's
     tokens/components when present; otherwise a small inline token set and
     demo data.
   - When using OpenDesign, pull the selected artifact into this repository
     before treating it as the prototype under review.
   - Cover key flows end to end, including at least one empty and one error
     state where the PRD implies them.
5. Verify interactions in a browser.
   - Open the prototype in a real browser (playwright/browser tooling) and
     click through every promised flow; fix broken navigation or states.
   - Record what was verified and what remains a wireframe.
6. Write the UI spec.
   - Read `references/ui-spec-template.md` and produce
     `docs/prototype/ui-spec.md` (or the repository's document-artifacts
     convention).
7. Report.
   - Summarize verified flows, open UI assumptions, and handoff to `write-trd`.

## Outputs

- `docs/prototype/index.html` — clickable prototype with demo data.
- `docs/prototype/ui-spec.md` — UI specification for the TRD.
- `docs/prototype/README.md` — how to open and run the prototype, only when the
  repository lacks one.

## Validation

- The prototype opens in a browser and every promised flow is clickable.
- Empty/loading/error states are covered where implied.
- The UI spec maps every screen and flow to a TRD-visible acceptance point.
- Demo data is labeled as such; no production integration is implied.
- When OpenDesign is used, the reviewed files exist in the repository and the
  result does not depend on an unreachable preview URL or an unrecorded
  external project state.

## Handoff Rules

- Hand the UI spec to `write-trd` as the UI input.
- If the PRD is missing or unsettled, hand off to `write-prd` first.
- If a visual direction is needed, hand off to `frontend-design`; do not
  duplicate it here.
- If OpenDesign was used, hand off the materialized repository artifact and the
  local UI spec together; OpenDesign remains an optional production provider,
  not a replacement for `prototype-ui` or `write-trd`.
- If Huashu was used, hand off the materialized HTML/evidence and the local UI
  spec together; keep the Huashu skill's optional export and cloud capabilities
  out of the required product handoff unless the user explicitly requests them.

## Boundaries

- No design-system governance, token management, or brand work.
- No mandatory external design-provider dependency; OpenDesign and Huashu are
  optional providers selected by the routing rules above.
- No Figma/Penpot/v0 integration in v1; Huashu is an optional local skill
  provider, not a design-file integration adapter. Other adapters remain later
  decisions.
- No production code generation; the prototype is throwaway by default.
