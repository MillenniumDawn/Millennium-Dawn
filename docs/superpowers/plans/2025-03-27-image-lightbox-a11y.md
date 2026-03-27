# Image lightbox accessibility & site-wide coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the docs site image lightbox in line with WAI-ARIA modal dialog practices (option B): `role="dialog"`, `aria-modal`, focus containment, stack-safe `inert` on `#main-content`, `prefers-reduced-motion` respect, and bind eligible images across the whole page (not only `#main-content`) while excluding chrome and decorative assets.

**Architecture:** Keep a single overlay instance appended to `document.body` (current pattern). Extend eligibility rules and collection scope so content images outside `<main>` (e.g. hero or sidebar slots that are not in header/footer) still bind. Add a document-level `focusin` trap while open (with `keydown` Tab fallback on the overlay if needed — some AT/browser pairs handle `focusin` + `preventDefault` inconsistently). Apply `inert` to **`#main-content` by element id** (not the `.main-content` class — TOC content targeting uses the class; drawer `inert` uses the id per `TOC_DRAWER.inertSelectors` in `docs/src/features/toc/lib/config.ts`). Use a **stack-safe restore** on close: only remove `inert` from `#main-content` when the lightbox had added it **and** the TOC mobile drawer is not using body lock (`toc-lock` on `body` from `TOC_DRAWER.bodyLockClass` — same config file). If that class is present on close, leave `inert` on `main` so an open drawer stays correct. **Known follow-up:** If the user closes the TOC drawer while the lightbox stays open, the drawer may clear `inert` on `main`; the document-level focus trap still blocks Tab to background — document for QA; fixing fully would require shared inert ownership (out of scope unless regressions appear). Optional title node for `aria-labelledby` updated on each `open()`.

**Z-index:** Overlay already uses `z-[4000]` (`LIGHTBOX_OVERLAY_CLASS`); site header uses `z-header` (token, below overlay). If stacking issues appear with TOC drawer/backdrop, compare their z-index tokens in `tailwind.ts` and adjust in a dedicated micro-task.

**Tech stack:** TypeScript, Astro client script (`docs/src/scripts/site.ts`), Tailwind class strings in `docs/src/shared/ui/tailwind.ts`, Bun for `check`/`build`, no existing unit-test runner in package (add minimal `bun test` + `happy-dom` only if you implement Task 7b).

**Informal spec:** Brainstorming session 2025-03-27 — modal pattern B + explicit request to cover all site images with sensible exclusions.

---

## File map

| File | Responsibility |
|------|------------------|
| `docs/src/features/image-lightbox/model/index.ts` | Overlay DOM, open/close, zoom, keyboard, focus trap, inert snapshot/restore, ARIA updates |
| `docs/src/features/image-lightbox/lib/eligibility.ts` (new) | Shared `LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR` + `isEligibleLightboxImage()` for tests and init |
| `docs/src/shared/ui/tailwind.ts` | Overlay `data-*` hook / reduced-motion-friendly classes if needed |
| `docs/src/styles/app.css` or `docs/src/styles/tailwind.css` | `@media (prefers-reduced-motion: reduce)` overrides for lightbox transition durations |
| `docs/package.json` | Optional `"test"` script if Task 7b is chosen |
| `docs/src/features/image-lightbox/lib/eligibility.test.ts` (new, optional) | Unit tests for eligibility |

---

### Task 1: Extract eligibility helper

**Files:**

- Create: `docs/src/features/image-lightbox/lib/eligibility.ts`
- Modify: `docs/src/features/image-lightbox/model/index.ts` (import helper, remove inlined duplicate logic)

**Behavior:** Centralize exclusion `closest()` selector. Must include existing cases **plus**:

- `.site-header` and `.site-footer` (matches `TOC_SELECTORS` in `docs/src/features/toc/lib/config.ts` — logo and any footer images must not open lightbox or steal link clicks).
- `picture[aria-hidden="true"]` (decorative `ResponsiveImage` in `docs/src/shared/ui/ResponsiveImage.astro`).

Keep: `[data-lightbox-ignore]`, `dialog`, `button`, empty `src` check.

```typescript
// eligibility.ts
export const LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR =
  "[data-lightbox-ignore], dialog, button, .site-header, .site-footer, picture[aria-hidden='true']";

export function isEligibleLightboxImage(image: HTMLImageElement): boolean {
  if (image.closest(LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR)) return false;
  const src = image.currentSrc ?? image.getAttribute("src") ?? "";
  return Boolean(src.trim());
}
```

- [ ] **Step 1:** Add `eligibility.ts` with the constant and function above.

- [ ] **Step 2:** Replace `isEligibleImage` in `model/index.ts` with imports from `eligibility.ts`; run typecheck.

Run: `cd docs && bun run check`  
Expected: no TypeScript errors.

- [ ] **Step 3:** Commit

```bash
git add docs/src/features/image-lightbox/lib/eligibility.ts docs/src/features/image-lightbox/model/index.ts
git commit -m "refactor(lightbox): centralize image eligibility rules"
```

---

### Task 2: Collect images site-wide

**Files:**

- Modify: `docs/src/features/image-lightbox/model/index.ts`

**Behavior:**

- Remove dependency on `#main-content` for **discovery**: use `document.querySelectorAll<HTMLImageElement>("img")` (or `document.images` filtered by type) instead of `root.querySelectorAll`.
- Remove unused `ROOT_SELECTOR` constant (or keep only if needed for inert target — `#main-content` remains the **inert** target, not the query root).
- `initImageLightbox` early exit: if `document.querySelector("#main-content")` is missing, return `NOOP` (layouts without main should not init; keeps redirect-only pages safe).
- Keep `astro:page-load` re-init behavior unchanged via existing `site.ts`.

- [ ] **Step 1:** Change collection to global `img` list filtered by `isEligibleLightboxImage`.

- [ ] **Step 2:** Verify header logo still navigates home (click should **not** trigger lightbox — excluded by `.site-header`).

Run: `cd docs && bun run build && bun run preview` (manual click test on a built page).

- [ ] **Step 3:** Commit

```bash
git add docs/src/features/image-lightbox/model/index.ts
git commit -m "fix(lightbox): bind eligible images outside main content"
```

---

### Task 3: Modal semantics and accessible name

**Files:**

- Modify: `docs/src/features/image-lightbox/model/index.ts`

**Behavior:**

- On the overlay root element, set `role="dialog"`, `aria-modal="true"`.
- Add a visually hidden heading (or element with `id`) for `aria-labelledby`, e.g. `id="image-lightbox-title"`. Reuse existing screen-reader utility class if the project has `sr-only` / equivalent in Tailwind; otherwise add `class="sr-only"` if defined in `tailwind.css`, or inline minimal CSS in a shared pattern used elsewhere.
- On each `open()`, set the title element’s **text content** to a sensible string: prefer the image `alt` when non-empty; otherwise `"Image"` (English matches current `aria-label` strings).
- Remove redundant `aria-hidden="false"` when open if redundant with `role="dialog"`; keep `hidden` attribute sync with visibility as today.

- [ ] **Step 1:** Update `innerHTML` / attributes on overlay creation and `open()` to wire ARIA.

- [ ] **Step 2:** Run `cd docs && bun run check`.

- [ ] **Step 3:** Commit

```bash
git add docs/src/features/image-lightbox/model/index.ts
git commit -m "feat(lightbox): dialog role and labelled title for screen readers"
```

---

### Task 4: Focus trap (document-level)

**Files:**

- Modify: `docs/src/features/image-lightbox/model/index.ts`

**Behavior:**

- While overlay is open (not `hidden`, state not `closing`), register `document.addEventListener("focusin", handler, true)`.
- If `focusin.target` is not contained in `overlay`, call `preventDefault()`, `stopPropagation()`, and `closeButton.focus()`.
- **Fallback:** On `overlay` `keydown`, if `event.key === "Tab"` and the active target would move focus outside the overlay (e.g. only one tab stop — the close button — cycle with `event.preventDefault()` + `closeButton.focus()`), mirror APG dialog behavior so Tab cannot escape even if `focusin` handling differs by browser/AT.
- Register on open (after `hidden = false`), unregister on `finishClose` and `destroy`.
- Keep initial focus on close button after open (existing `requestAnimationFrame`).

**Acceptance — `destroy()` / view transitions:** If `destroy()` runs while the overlay is open (e.g. `astro:before-swap` → `cleanupPage()` in `docs/src/scripts/site.ts`), it must run the same teardown as a normal close: clear close timer, call `finishClose` **synchronously** (or inline equivalent: unlock body, remove trap listeners, restore `inert` per Task 5, remove overlay from DOM). Do not leave listeners, body scroll lock, or a stray `inert` on `main`.

- [ ] **Step 1:** Implement trap with capture-phase `focusin` + Tab fallback on overlay.

- [ ] **Step 2:** Manual test: open lightbox, press Tab repeatedly — focus must not land in header nav, skip link target, or footer. Optional: one screen reader smoke test.

- [ ] **Step 3:** Manual test: open lightbox, trigger an in-app navigation that fires `astro:before-swap` — no leaked listeners; page usable after navigation.

- [ ] **Step 4:** Commit

```bash
git add docs/src/features/image-lightbox/model/index.ts
git commit -m "feat(lightbox): trap focus inside dialog while open"
```

---

### Task 5: Stack-safe `inert` on `#main-content`

**Files:**

- Modify: `docs/src/features/image-lightbox/model/index.ts`

**Behavior:**

- Resolve `const main = document.querySelector("#main-content")` when opening (must be the **id** selector to match TOC drawer `inert` targets).
- Before setting `inert`, record `const wasInert = main?.hasAttribute("inert") ?? true` (if no `main`, skip).
- If `main` exists and `!wasInert`, set `main.setAttribute("inert", "")`.
- On `finishClose` and on **`destroy()`**, restore with:

  - If `main` existed and `!wasInert`, remove `inert` **only when** `document.body.classList.contains("toc-lock")` is **false** (drawer not claiming page inert). If `toc-lock` is present, another subsystem (TOC) may still require `main` to stay inert — do not remove.

- Do **not** strip `inert` from header/footer — lightbox does not own those; TOC drawer does.

- [ ] **Step 1:** Implement snapshot/restore with `toc-lock` guard as above.

- [ ] **Step 2:** Manual regression matrix:

  1. Open mobile TOC drawer → open lightbox → close lightbox (drawer still open): `main` must remain `inert`.
  2. Open lightbox → open TOC drawer → close lightbox first: `main` must remain `inert` while drawer open.
  3. Open lightbox alone → close lightbox: `main` must lose `inert` if it was added by lightbox.

- [ ] **Step 3:** Commit

```bash
git add docs/src/features/image-lightbox/model/index.ts
git commit -m "feat(lightbox): stack-safe inert on main content while open"
```

---

### Task 6: `prefers-reduced-motion`

**Files:**

- Modify: `docs/src/styles/app.css` or `docs/src/styles/tailwind.css` (whichever already hosts site-wide media queries)

**Behavior:**

- Add `data-image-lightbox-overlay` (or reuse a single stable `data-` attribute) on the overlay root in `createLightbox()` for CSS targeting.
- Under `@media (prefers-reduced-motion: reduce)`, set transition durations for that overlay subtree to `0ms` or `1ms`, and disable transform transitions that animate open/close (match selectors used by `LIGHTBOX_*` classes — inspect compiled class list in `tailwind.ts`).

Prefer **targeting only nodes that use transitions** from `LIGHTBOX_OVERLAY_CLASS`, `LIGHTBOX_CLOSE_BUTTON_CLASS`, `LIGHTBOX_CONTENT_CLASS` in `docs/src/shared/ui/tailwind.ts` (e.g. overlay root + close button + content wrapper) instead of a blanket `[data-image-lightbox-overlay] *` with `!important`, to avoid suppressing unrelated nested transitions.

Example shape (adjust to match final `data-` hooks):

```css
@media (prefers-reduced-motion: reduce) {
  [data-image-lightbox-overlay],
  [data-image-lightbox-close],
  [data-image-lightbox-content] {
    transition-duration: 0.01ms !important;
  }
}
```

Add `data-image-lightbox-close` / `data-image-lightbox-content` in markup if those nodes need explicit hooks (close button already has `data-image-lightbox-close` today; content wrapper may need a new `data-` attribute).

- [ ] **Step 1:** Add overlay `data-image-lightbox-overlay` in TS; add CSS media block.

- [ ] **Step 2:** Toggle reduced motion in OS/browser devtools and confirm open/close is effectively instant.

- [ ] **Step 3:** Commit

```bash
git add docs/src/features/image-lightbox/model/index.ts docs/src/styles/app.css
git commit -m "feat(lightbox): honor prefers-reduced-motion"
```

(Adjust second path if you edited `tailwind.css` instead.)

---

### Task 7a: Verification (default — no new deps)

- [ ] **Step 1:** Run full static checks

```bash
cd docs && bun run lint && bun run check && bun run build
```

Expected: all succeed.

- [ ] **Step 2:** Manual keyboard protocol (one content page with markdown images + home hero if present)

1. Tab to an in-content image (not header); Enter opens lightbox.
2. Escape closes; focus returns to trigger.
3. With lightbox open, Tab does not escape to chrome (including skip link / header).
4. `+` / `-` / `0` still adjust zoom; Escape still closes.
5. Build preview: click header logo — navigates home, does not open lightbox.
6. Optional: linked markdown image `<a><img></a>` — click opens lightbox and does not navigate (existing `preventDefault` behavior should remain).
7. Open lightbox, navigate to another page (SPA-style Astro swap): no stuck scroll lock, no orphaned `inert`/`listeners`.

- [ ] **Step 3:** Commit only if fixing issues found; otherwise document “verified” in PR description.

---

### Task 7b (optional): Unit tests for eligibility

**Files:**

- Create: `docs/src/features/image-lightbox/lib/eligibility.test.ts`
- Modify: `docs/package.json` — add `"test": "bun test src/features/image-lightbox"`

- [ ] **Step 1:** `cd docs && bun add -d happy-dom`

- [ ] **Step 2:** Use a **per-test** (or per-describe) `happy-dom` `Window` instance; assign `globalThis.document` only inside that test and restore previous `document` after (or use a pattern Bun documents for isolated DOM) — avoid a single `beforeAll` that mutates `globalThis.document` for the entire suite.

Example shape:

```typescript
import { describe, expect, test } from "bun:test";
import { isEligibleLightboxImage } from "./eligibility";

describe("isEligibleLightboxImage", () => {
  test("excludes header images", async () => {
    const { Window } = await import("happy-dom");
    const window = new Window({ url: "https://example.com" });
    const doc = window.document;
    doc.body.innerHTML =
      '<header class="site-header"><img src="/x.png" alt="logo" /></header>';
    const img = doc.querySelector("img")!;
    expect(isEligibleLightboxImage(img as unknown as HTMLImageElement)).toBe(false);
  });
});
```

(Adjust casting if you export a small test helper that accepts `Document`.)

- [ ] **Step 3:** Run `cd docs && bun test src/features/image-lightbox`

Expected: all tests pass.

- [ ] **Step 4:** Commit

```bash
git add docs/package.json docs/bun.lock docs/src/features/image-lightbox/lib/eligibility.test.ts
git commit -m "test(lightbox): cover eligibility exclusions"
```

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2025-03-27-image-lightbox-a11y.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. REQUIRED SUB-SKILL: @superpowers:subagent-driven-development

**2. Inline Execution** — Run tasks in this session using @superpowers:executing-plans with checkpoints between tasks.

Which approach do you want?
