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
- Separate prototype decisions from implementation commitments; re-check
  platform constraints (for example WeChat mini-program storage or canvas
  limits) in the TRD.
- The UI spec is the primary handoff artifact; the prototype is evidence that
  the flows work.

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
3. Build the prototype.
   - Write `docs/prototype/index.html` (single file preferred) with the repo's
     tokens/components when present; otherwise a small inline token set and
     demo data.
   - Cover key flows end to end, including at least one empty and one error
     state where the PRD implies them.
4. Verify interactions in a browser.
   - Open the prototype in a real browser (playwright/browser tooling) and
     click through every promised flow; fix broken navigation or states.
   - Record what was verified and what remains a wireframe.
5. Write the UI spec.
   - Read `references/ui-spec-template.md` and produce
     `docs/prototype/ui-spec.md` (or the repository's document-artifacts
     convention).
6. Report.
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

## Handoff Rules

- Hand the UI spec to `write-trd` as the UI input.
- If the PRD is missing or unsettled, hand off to `write-prd` first.
- If a visual direction is needed, hand off to `frontend-design`; do not
  duplicate it here.

## Boundaries

- No design-system governance, token management, or brand work.
- No Figma/Penpot/v0 integration in v1; adapters are a later decision.
- No production code generation; the prototype is throwaway by default.
