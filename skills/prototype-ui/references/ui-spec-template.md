# UI Specification Template

Produce the UI spec that hands off to `write-trd`. Keep it decision-focused;
every row should be checkable during implementation.

## 1. Context

- Product / repo:
- Source PRD:
- Platform and audience constraints:
- Design tokens / components reused (or "none, plain prototype"):

## 2. Screen Map

| Screen | Purpose | Entry / Exit | Key States | Must Be Clickable |
| --- | --- | --- | --- | --- |
| ... | ... | ... | empty / loading / error / success | yes / no |

## 3. Key Flows

For each flow: trigger -> steps -> outcome.

- Flow 1:
- Flow 2:

## 4. States and Edge Cases

- Empty states: where they appear and what they show.
- Error states: validation failures, save failures, export failures.
- Loading states: long operations (for example export or batch layout).

## 5. UI Decisions Fixed by the Prototype

- Decisions the prototype confirms (layout, naming, defaults, mode switch).
- Open questions still needing PRD or TRD confirmation.

## 6. Platform Constraints for the TRD

Constraints observed in the prototype (for example storage, canvas, export
size, input limits) that the TRD must re-verify against the real platform.

## 7. Acceptance Points

Checkable acceptance points the TRD should inherit, one per screen / flow /
state.

Keep this document under two pages. If it grows, split per screen.
