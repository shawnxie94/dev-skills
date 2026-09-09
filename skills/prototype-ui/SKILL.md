---
name: prototype-ui
description: Turn a settled PRD or product scope into a design-stage handoff — visual direction, clickable HTML prototype, and UI spec before the TRD. Use when layout, flow, states, or visual direction are still unverified（原型、线框、wireframe、mockup、UI 设计）.
---

# Prototype UI

Own the design-stage workflow from a settled PRD to a reviewed prototype and UI
specification before the TRD. The workflow includes information architecture,
interaction and state design, visual direction, prototype verification, and
handoff. The result is design evidence and implementation constraints, not
production UI or a governed design system.

## Core Principles

- Prototype flows, states, and visual intent. Visual direction is part of this
  skill's workflow; do not require or invoke a separate visual-design skill.
- Reuse the repository's existing UI stack, components, and design tokens when
  present. When no system exists or visual exploration is explicitly requested,
  define a temporary prototype token set and record it as such; do not imply
  production design-system governance.
- Keep the prototype single-file or a small static set; no build tooling.
- Keep the UI specification and the repository-materialized prototype as the
  source of truth. A design workspace or visual generator is an optional
  provider, not a replacement for the UI handoff contract.
- Separate prototype decisions from implementation commitments; re-check
  platform constraints (for example WeChat mini-program storage or canvas
  limits) in the TRD.
- The UI spec is the primary handoff artifact; the prototype is evidence that
  the flows work.

## Design Workflow

Run the following design activities inside this skill. Do not hand off the
visual-design stage to another skill merely because the result needs a stronger
visual point of view.

1. Extract the product subject, audience, and the primary job of each screen.
2. Define the screen map, key flows, and required states before styling.
3. Write a compact visual brief:
   - 4–6 named colors and their semantic roles;
   - display, body, and utility typography roles when needed;
   - layout, density, spacing, radius, and surface principles;
   - one memorable signature element appropriate to the product;
   - motion, responsive, keyboard-focus, and reduced-motion rules.
4. Review the direction against the brief before building. Remove choices that
   look like generic AI defaults unless the product genuinely calls for them.
5. Use content as interface material: labels describe user actions, copy stays
   specific and conversational, and empty/error states explain the next step.
6. After building, critique the result for hierarchy, consistency, task clarity,
   responsive behavior, accessibility basics, and unnecessary decoration.

Visual exploration must serve the product subject and user task. A distinctive
direction is useful only when it remains legible, coherent, and implementable.

## Prototype Provider

`local-static` is the built-in implementation path and fallback. When an
external provider is useful, choose exactly one of the following per run unless
the user explicitly requests a comparison or two-stage workflow:

- `huashu-design`: use for visual-direction exploration, high-fidelity HTML,
  animation, infographics, or multiple visual variants. It is a visual delivery
  provider, not a replacement for the local UI-spec handoff or production
  application architecture.
- `opendesign`: use the connected OpenDesign MCP when project context, a
  coordinated design workspace, design-system exploration, or responsive
  multi-screen treatment is the material advantage.
- `figma`: use a connected Figma app or integration when editability, shared
  components, manual refinement, or ongoing design-asset maintenance is the
  material advantage. If Figma is unavailable, report that limitation and use
  `local-static` or another explicitly selected provider.

Provider selection does not change the design contract: the screen map, flows,
states, visual brief, acceptance points, and local UI spec remain owned by this
skill.

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
2. Read only the Huashu references relevant to the requested output. Select
   Huashu only when visual exploration or high-fidelity visual delivery is a
   material need. Once selected, follow Huashu's provider contract, including
   its mandatory three-direction gate, unless the user explicitly asks to skip
   that gate; use `local-static` for an ordinary settled flow/state prototype.
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

When `figma` is selected:

1. Confirm that the Figma file or connected integration is accessible before
   treating it as a provider input.
2. Use Figma for editable visual assets, components, and manual refinement; do
   not assume that a Figma file alone proves the product flow works.
3. Record the relevant file, page, frame, component, and variable decisions in
   the local UI spec without making the repository depend on an unreachable
   Figma URL.
4. Materialize the review evidence needed for implementation under the
   repository when possible (screenshots, exports, or a local prototype), and
   run browser verification for promised interactions.

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
3. Establish the visual direction.
   - Reuse existing tokens and components when they exist.
   - Otherwise create the compact visual brief defined above.
   - Record which visual choices are fixed and which remain exploratory.
4. Select the prototype provider.
   - Use `local-static` for ordinary flow/state validation or when no external
     provider is available.
   - Select one external provider only when its specific advantage is material.
   - Preserve the screen map, visual brief, and acceptance points as local
     constraints for the provider output.
5. Build or materialize the prototype.
   - Write `docs/prototype/index.html` (single file preferred) with the repo's
     tokens/components when present; otherwise a small inline token set and
     demo data.
   - When using OpenDesign, pull the selected artifact into this repository
     before treating it as the prototype under review.
   - Cover key flows end to end, including at least one empty and one error
     state where the PRD implies them.
6. Verify interactions in a browser.
   - Open the prototype in a real browser (playwright/browser tooling) and
     click through every promised flow; fix broken navigation or states.
   - Record what was verified and what remains a wireframe.
7. Write the UI spec.
   - Read `references/ui-spec-template.md` and produce
     `docs/prototype/ui-spec.md` (or the repository's document-artifacts
     convention).
8. Report.
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
- If OpenDesign was used, hand off the materialized repository artifact and the
  local UI spec together; OpenDesign remains an optional production provider,
  not a replacement for `prototype-ui` or `write-trd`.
- If Huashu was used, hand off the materialized HTML/evidence and the local UI
  spec together; keep the Huashu skill's optional export and cloud capabilities
  out of the required product handoff unless the user explicitly requests them.
- If Figma was used, hand off the local UI spec and any materialized review
  evidence together; keep the required handoff usable when the Figma file is
  unavailable.

## Boundaries

- No production design-system governance, long-term token ownership, or brand
  program management. Prototype-level visual direction and temporary tokens are
  in scope.
- No mandatory external design-provider dependency. Supported external provider
  routes are Huashu, OpenDesign, and Figma; provider availability must be
  checked at runtime and must not block a local handoff.
- No production code generation; the prototype is throwaway by default.
