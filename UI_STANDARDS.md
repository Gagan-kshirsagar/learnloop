# UI_STANDARDS.md — Next-Gen UI, Motion & Design System

The look-and-feel bar for LearnLoop: modern, confident, and animated *with
purpose*. Includes the WHY and the interview angle — polished UI + tasteful motion
is a real differentiator, but done wrong it screams junior.


---

## 1. The design direction

Target aesthetic: **Linear / Vercel / Framer-grade** — clean, spacious,
high-contrast, confident. Not flashy, not glassmorphism-everywhere.

- **One accent** (a confident brand hue — violet→blue gradient for hero moments).
- **Cool near-black dark mode**, true-white-adjacent light mode; both from tokens.
- **Elevation** via subtle 1px borders + soft shadows, generous radius (12px).
- **Typography:** Inter, `tracking-tight` on headings, clear size scale, muted
  secondary text.
- **Whitespace is a feature** — crowded UIs read as amateur.

**Rule:** semantic design tokens only (`bg-surface`, `text-muted`, `bg-accent`).
Never raw hex/default Tailwind colours. One system → light+dark for free, and a
rebrand is a one-file change.

---

## 2. Motion — the philosophy

**Purposeful motion, never decorative.** Animation should *communicate*: where
something came from, that an action registered, that content is loading, that
state changed. Gratuitous motion is distracting and dates instantly.

Use **Framer Motion** (`motion`) for React animation.

### The categories we use
| Purpose | Motion | Why |
|---|---|---|
| **Entrance** | fade + short slide-up on mount/route | orients the eye; feels alive |
| **Layout** | `layout` / shared-layout transitions | changes feel continuous, not jarring |
| **Feedback** | button `active:scale-[.98]`, hover lift | confirms the interaction |
| **Loading** | skeleton shimmer, streaming caret | communicates "working" |
| **State change** | list add/remove, tab underline slide | makes change legible |
| **Attention** | subtle pulse on a new item / toast | draws the eye, briefly |

### The rules (this is what keeps it senior, not gaudy)
- **Fast + subtle:** ~150–300ms, small distances/scales. Long/big = amateur.
- **Ease, don't bounce** (mostly): `easeOut` / a gentle spring; reserve bounce for
  playful accents only.
- **Respect `prefers-reduced-motion`** — disable/reduce for users who ask. This is
  both an accessibility requirement and an interview point.
- **Animate cheap properties** — `transform` and `opacity` (GPU-composited),
  **not** `width`/`top`/`left` (trigger layout/paint → jank).
- **Don't animate everything** — motion budget; if it all moves, nothing stands out.
- **No motion that blocks interaction** or delays content meaningfully.

```tsx
// Entrance, reduced-motion-aware, cheap properties only
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.25, ease: "easeOut" }}
/>
```

**Interview:** *"How do you use animation without hurting UX/perf?"* →
"Purposefully and sparingly: animate `transform`/`opacity` only (GPU), keep it
fast (~200ms), and honour `prefers-reduced-motion`. Motion communicates state; it
isn't decoration."

---

## 3. Next-gen touches (tasteful, not gimmicky)

Pick a few; don't pile them on:
- **Micro-interactions** — hover/press feedback on every interactive element.
- **Optimistic + animated list changes** — items slide in/out on add/remove.
- **Streaming/typing affordance** — the tutor's tokens appear with a soft caret.
- **Skeleton → content crossfade** — no hard pop when data lands.
- **Command palette (⌘K)** — modern, keyboard-first navigation.
- **Animated route transitions** — subtle shared-layout or fade between pages.
- **Tasteful gradients/mesh** — reserved for hero/marketing, not data-dense views.
- **Empty states with small illustrations/animation** — a new tenant feels alive.
- **Toasts** — slide-in, auto-dismiss, `aria-live` for a11y.

**Guardrail:** on **data-dense views** (tables, editor, tutor), motion is minimal
and functional — readability wins. Save the flourish for hero/landing/empty states.

---

## 4. Accessibility is part of the design (not optional)
- Semantic HTML; real `<button>`/`<a>`/`<input>`; one `<h1>`, ordered headings.
- Every input has a label; errors via `aria-describedby` + `role="alert"`.
- **Visible focus** always (never remove the outline without replacing it).
- **Keyboard-operable** everything; modals trap focus, `Esc` closes, restore focus.
- **Contrast AA** (4.5:1 body). Colour never the only signal.
- Dynamic content (tutor stream, toasts) via `aria-live="polite"`.
- **Motion respects `prefers-reduced-motion`.**

**Interview:** *"How do you approach accessibility?"* → "Semantic-first so it's
accessible by default; `getByRole` in tests doubles as an a11y check; manage
focus in modals; and honour reduced-motion. Accessible UIs are also better SEO
and UX."

---

## 5. Responsive & mobile
- **Mobile-first**; verify at 375px and desktop. Learners study on phones.
- Sidebar collapses; the editor + tutor degrade gracefully (stacked, not broken).
- Touch targets ≥ 44px; no hover-only affordances.
- Test both orientations; no horizontal scroll on data views (overflow handled).

---

## 6. The component system
- Build on **shadcn/ui** primitives; extend, don't fight them. One `Button`, one
  `Card`, one `Input`, etc. — consistency over variety.
- Compose feature components from primitives; a new screen is assembly, not new CSS.
- Loading = skeletons **sized to the real content** (protects CLS + no pop).
- Consistent spacing scale, aligned grids — misalignment reads as junior.

---

## 7. Performance-aware UI (ties to PERFORMANCE.md)
- Heavy animated/interactive components (editor, charts, tutor) are **client
  leaves, code-split** — motion libs don't bloat the initial bundle.
- Prefer **CSS transitions** for simple hovers/toggles (cheapest); Framer Motion
  for orchestration/layout/gestures.
- Never animate layout-triggering properties on large/data-dense DOM.
- Skeletons match dimensions → no layout shift when content/motion resolves.

---

## 8. The senior differentiator to state out loud
Most portfolios are *either* functional-but-plain *or* flashy-but-janky/inaccessible.
The senior move is **both**: a polished, animated, modern UI that is *also* fast,
accessible, and motion-reduced-friendly. Being able to say *"I made it feel
premium AND kept CLS < 0.1, animated only transform/opacity, and honoured
reduced-motion"* is the thing that separates a 4-YOE front-ender from a 2-YOE one.
