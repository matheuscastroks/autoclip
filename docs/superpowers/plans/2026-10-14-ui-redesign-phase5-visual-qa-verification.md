# UI Redesign Phase 5: Visual QA, Accessibility & Final Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish permanent automated invariant guards in `visual-tokens.test.ts` for zero orange, zero pulse animations, studio header tokens, and list defaults; run the complete test suite; and produce the final verification report.

**Architecture:** Extend Vitest regression guards in `desktop/tests/visual-tokens.test.ts` to scan all `desktop/src/` files for aesthetic regressions, ensure all 110+ tests pass cleanly, and commit the complete redesign.

**Tech Stack:** Vitest, Node.js `fs` / `path`, Vue 3, TypeScript.

**Spec:** `docs/superpowers/specs/2026-10-14-ui-redesign-phase5-visual-qa-verification-design.md`

## Global Constraints

- No regressions in any test file.
- All tests must pass: `npm test -- --run`.

---

### Task 1: Expand Invariant Guards in `visual-tokens.test.ts`

**Files:**
- Modify: `desktop/tests/visual-tokens.test.ts`

- [ ] **Step 1: Add automated check for zero @keyframes pulse in `desktop/src`**
- [ ] **Step 2: Add check for header height token (`--header-height: 48px`)**
- [ ] **Step 3: Run visual tokens test**
  Run: `cd desktop; npx vitest run tests/visual-tokens.test.ts`
  Expected: PASS.
- [ ] **Step 4: Commit updated test guards**
  ```bash
  git add desktop/tests/visual-tokens.test.ts
  git commit -m "test: add permanent regression guards for zero pulse and studio header tokens"
  ```

---

### Task 2: Final Full-Suite Verification & Delivery

- [ ] **Step 1: Run full vitest suite**
  Run: `cd desktop; npm test -- --run`
  Expected: 20 test files, 110+ tests passed.
- [ ] **Step 2: Audit git status**
  Run: `git status`
  Expected: Clean working tree.
- [ ] **Step 3: Present Phase 5 and Full Redesign Completion Report to User**
