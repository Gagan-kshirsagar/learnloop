# Frontend Performance (the WHY an experienced dev must know)

Every technique here is *why it exists*, *how it helps*, and *the interview
answer*. Follow AGENTS.md §7; this document explains it.


---

## 1. Core Web Vitals — the scoreboard

Google's user-centric metrics. They matter because they correlate with real UX,
affect SEO ranking, and are what interviewers name-drop.

| Metric | Measures | Good | Main levers |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | Time to render the largest visible element | < 2.5s | optimize hero image, preload critical assets, cut render-blocking JS/CSS, SSR/streaming |
| **INP** (Interaction to Next Paint) | Responsiveness across *all* interactions to next paint | < 200ms | break long tasks, defer non-urgent work, `useTransition`, less main-thread JS |
| **CLS** (Cumulative Layout Shift) | Unexpected layout movement | < 0.1 | explicit image/video dimensions, reserve space, skeletons that match, `next/font` |

> **INP replaced FID in 2024.** Knowing that is a cheap currency signal. INP is
> stricter — it measures *every* interaction end-to-end, so long main-thread
> tasks now hurt you far more.

**Interview:** *"What are Core Web Vitals and how do you improve them?"* → name
the three, what each measures, and one concrete lever for each (above).

---

## 2. Server Components vs Client Components (the biggest lever in Next.js)

**Concept:** In the App Router, components are **Server Components by default** —
they render on the server, ship **zero JavaScript** to the browser, and can fetch
data directly. A component only becomes a **Client Component** (`"use client"`)
when it needs interactivity (state, effects, event handlers, browser APIs).

**Why it matters:** every Client Component ships its JS to the browser, which the
browser must download, parse, and execute — the main cost of a slow page. Server
Components move work off the client entirely.

**The rule:** *push the `"use client"` boundary as deep as possible.* Keep pages,
layouts, and static content as Server Components; make only the small interactive
leaves (a button, a form, the tutor chat input) client components.

**The mistake:** slapping `"use client"` at the top of a page/layout — it drags
the entire subtree into the client bundle.

**Interview:** *"Server vs Client Components — when each?"* → "Server by default:
zero JS, direct data access, better LCP. Client only for interactivity, kept as a
small leaf so I don't ship the whole tree to the browser."

---

## 3. Code splitting & lazy loading

**Concept:** Don't ship all JavaScript up front. Split the bundle so code loads
**when needed**. `next/dynamic` (or `React.lazy`) loads a component on demand.

**Why:** a smaller initial bundle = faster load and interactivity (better LCP +
INP). A heavy dependency the user may never see shouldn't block first paint.

**Where we use it in LearnLoop:**
- **Monaco code editor** — large; load it only on the exercise page, dynamically,
  with a skeleton fallback.
- **Charts / analytics** — below the fold or admin-only.
- **The tutor panel** — load when opened.
- **Modals/dialogs** — load on trigger.

```tsx
const CodeEditor = dynamic(() => import("@/components/CodeEditor"), {
  loading: () => <EditorSkeleton />,
  ssr: false, // editor needs the browser
});
```

**Interview:** *"How do you keep the bundle small?"* → "Server Components ship no
JS; I code-split heavy/rare client components with `next/dynamic`, lazy-load
below-the-fold, and keep a bundle budget in CI."

---

## 4. Suspense & streaming

**Concept:** `<Suspense fallback={...}>` lets you render a fallback (skeleton)
while an async child (data fetch, lazy component) resolves. In the App Router,
the server can **stream** HTML — send the shell instantly, then stream in slower
sections as they're ready.

**Why:** the user sees meaningful content immediately (good LCP + perceived
speed) instead of a blank screen while the slowest query finishes. It also lets
independent sections load in parallel rather than blocking on the slowest one.

```tsx
<Suspense fallback={<LessonSkeleton />}>
  <LessonContent id={id} />   {/* async Server Component */}
</Suspense>
```

**Pair with an Error Boundary** so a failing section shows an error, not a crash.

**Interview:** *"What does Suspense give you?"* → "Declarative loading states and
server streaming — the shell paints immediately and slow parts stream in, so one
slow query doesn't block the whole page."

---

## 5. React 18/19 concurrency: `useTransition` / `useDeferredValue`

**Concept:** mark some state updates as **non-urgent** so React keeps the UI
responsive. `useTransition` wraps an update ("this can be interrupted");
`useDeferredValue` gives a lagging copy of a fast-changing value.

**Why (INP):** typing in a search box while filtering a big list — the keystroke
must feel instant (urgent), the filtering can lag a frame (non-urgent). Without
this, heavy renders block input and INP suffers.

```tsx
const [isPending, startTransition] = useTransition();
onChange={(e) => {
  setQuery(e.target.value);                 // urgent: input stays snappy
  startTransition(() => setResults(filter(e.target.value))); // interruptible
}}
```

> These make **rendering** interruptible; they do **not** reduce network calls —
> that's what debouncing is for. Strong answer uses both: debounce the fetch,
> transition the render.

**Interview:** *"How do you keep a UI responsive under heavy render work?"* →
"Mark non-urgent updates with `useTransition`/`useDeferredValue` so urgent input
isn't blocked — it improves INP. Debounce the network separately."

---

## 6. Memoization — with judgement

**Concept:** `React.memo` (skip re-render if props are shallow-equal),
`useMemo` (cache a computed value), `useCallback` (stable function reference).

**Why + the catch:** they prevent wasted re-renders, BUT each has a cost (the
comparison, the retained reference, readability). Wrapping `a + b` in `useMemo`
is slower than recomputing it.

**Use them for exactly three reasons:** (1) a genuinely expensive computation,
(2) a value used as another hook's dependency (a new reference would loop),
(3) a prop to a memoized child (a new reference defeats the memo).

> **React 19's compiler** auto-memoizes, removing much manual work. Say: "I
> memoize where profiling shows a need; with the React Compiler I'd write far
> less by hand."

**Interview:** *"When do you use useMemo/useCallback?"* → the three reasons, plus
"never reflexively — measure first."

---

## 7. Images & fonts (cheap CLS + LCP wins)

- **`next/image`:** automatic modern formats (WebP/AVIF), responsive sizing, lazy
  loading below the fold, and **required width/height** → reserves space →
  prevents CLS. Preload the LCP hero image.
- **`next/font`:** self-hosts fonts, eliminates render-blocking font requests, and
  reserves space to avoid the font-swap layout shift.

**Interview:** *"How do you avoid layout shift?"* → "Explicit media dimensions,
`next/image`, `next/font`, and skeletons sized to the real content."

---

## 8. Data fetching & caching (TanStack Query)

- **Server state is a cache, not app state.** Query gives caching, dedup,
  background refetch, retries, and loading/error for free.
- **`staleTime`** — how long data is "fresh" before a background refetch (cuts
  redundant network calls).
- **`placeholderData: keepPreviousData`** — on pagination/filtering, keep showing
  the old page while the new one loads → no flash/layout jump.
- **Prefetch** on hover/route intent for instant navigation.
- **Query keys** encode all inputs → correct cache + automatic stale-response
  safety (newest key wins).

**Interview:** *"Why TanStack Query over useEffect fetching?"* → "It's a caching
layer: dedup, background revalidation, retries, and race-safe by query key —
hand-rolling that in useEffect is buggy and reinvents a cache."

---

## 9. List performance

- **Stable keys** (id, never index) so React reuses DOM + component state
  correctly on reorder/filter.
- **Virtualization** (react-window / TanStack Virtual) beyond a few hundred rows —
  render only the visible window, not 10k DOM nodes.
- **Debounce/throttle** scroll/resize/search handlers.

**Interview:** *"How do you render a 10,000-row list?"* → "Virtualize — render the
visible window + overscan; keep server-side pagination so the client never holds
everything."

---

## 10. The main thread & long tasks

**Concept:** the browser has one main thread for JS, layout, paint. A JS task >
~50ms is a **long task** that blocks input → bad INP.

**Levers:** break work into chunks, defer non-critical work (idle callbacks /
transitions), move heavy pure computation to a **Web Worker**, ship less JS
(Server Components + code splitting).

**Interview:** *"What's a long task and why care?"* → ">50ms main-thread task that
blocks interaction; I reduce them by shipping less JS, splitting work, and
offloading heavy compute to a worker."

---

## 11. Other things an experienced dev should name

- **Bundle analysis** (`@next/bundle-analyzer`) + a size budget in CI so
  regressions fail the build, not the user.
- **Tree-shaking / subpath imports** — import `lodash/debounce`, not all of lodash.
- **Preload / prefetch / preconnect** for critical assets and origins.
- **CDN + caching headers**; static assets immutable + far-future cached.
- **Debounced/optimistic UX** where correctness allows (and why sometimes it
  doesn't — server-side sorted lists).
- **Accessibility = performance-adjacent**: `getByRole` in tests, semantic HTML,
  and it also improves SEO/UX.
- **Measure, don't guess**: Lighthouse, the Performance panel, `web-vitals` lib in
  prod (real-user monitoring), React Profiler.

**Interview one-liner:** *"I optimize by measurement — Lighthouse + RUM +
Profiler — then apply the right lever: ship less JS (Server Components, code
splitting), stream with Suspense, keep interactions off the critical path
(transitions/workers), and protect CLS with sized media and fonts."*

---

## How this shows up in LearnLoop (concrete)
- Lesson pages = Server Components streaming content via Suspense.
- Monaco editor + tutor panel = dynamically imported client leaves.
- Course/learner tables = TanStack Query (`keepPreviousData`) + virtualization at
  scale + server-side pagination.
- Tutor streaming = SSE tokens with `aria-live`; input stays snappy via a
  transition on any heavy render.
- Images/fonts via `next/image`/`next/font`; bundle budget + Lighthouse in CI.
