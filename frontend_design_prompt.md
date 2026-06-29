# Master Build Prompt — Liquid Glass Design System
## Version 2.0 — Audited against live renders of Landing page (hero + phases sections)

Use this prompt to build **any new page** for this product. It contains the original creative
brief in full, plus the exact design tokens, component recipes, and anti-slop rules that were
derived from building the Landing page — so every new page is pixel- and physics-consistent with
it, not just "in the same vibe."

> **Before building anything, read §4.1 and §4.2.** §4.1 documents the canonical glass look
> (dark, restrained, smoked — not luminous frosted). §4.2 documents the single most common
> failure mode caught in production: a glass.base card with no nested children looks like a plain
> dark box, not glass. Both sections are mandatory pre-reading.

> **This document was audited against actual renders** of the Landing page hero (Image 1) and
> the phase/narrative section (Image 2). Every spec here is confirmed against those screenshots.
> Any previous version of this document that contradicts what follows is superseded.

---

## 0. ROLE & MISSION

You are acting as an Elite Creative Technologist and Lead UI/UX Architect. Your goal is to
engineer a highly professional, visually breathtaking frontend web application. You must
completely break away from standard "AI-generated slop" layout tropes (e.g., standard rounded
rectangles with neon gradient borders, generic icon grids, basic flexbox configurations, and
predictable centered hero text).

Build a production-grade, highly interactive application inspired by the design precision of
Apple, the fluid utility of Uber, and the micro-interaction delight of Stripe. Every page you add
must read as part of the same physical object as the existing Landing page — same glass material,
same spring physics, same type scale, same restraint.

---

## 1. ABSOLUTE NEGATIVE CONSTRAINTS

These are non-negotiable. They combine the original brief's rules with the specific failure modes
caught and fixed while building this system — treat the second half as **evidence**, not theory.

**From the original brief:**
- **No "AI Slop" Box Styles.** Never use generic `border border-gray-800 bg-gray-900/50` cards
  with a single subtle gradient stroke. Every layout element must have a purposeful structural
  reason to exist.
- **No Monotonous Card Grids.** Avoid throwing data into standard even grids. Mix layout
  densities — editorial bento styles, asymmetric column spans, overlapping depth layouts.
- **No Stock Icon Abuse.** Do not place generic icons inside identical small circular/rounded
  backgrounds next to headers just to fill space. Use icons sparingly, scaled intentionally, or
  replace them entirely with typographic cues or custom micro-canvas graphics.
- **No Static Dead States.** The UI must never feel frozen when the user stops interacting. Avoid
  rigid, unmoving blocks of text or background.

**Caught and fixed during this build — do not reintroduce these:**
- **The icon-in-a-badge tell.** The original Phase cards put a Lucide icon inside an identical
  small `glass.nested` rounded square next to every header. This is the single most common
  AI-template fingerprint. It was replaced with a giant, near-invisible typographic watermark
  numeral (`01` / `02` / `03`) bleeding off the card edge. **Never put a small icon in an
  identical rounded box next to a heading, anywhere in this product.**
- **The decorative-arc chart tell.** Any chart must be generated from an actual data array run
  through a real Catmull-Rom-to-Bezier interpolation function (recipe in §7), never a
  hand-authored decorative curve.
- **The hardcoded "live" marker tell.** Any live/current-value indicator must be positioned by
  computing its coordinate from the real last data point, never eyeballed into a
  plausible-looking spot.
- **Numbered markers must be earned.** `01 / 02 / 03` style devices are only legitimate when the
  content is a genuine ordered sequence. Don't add numbering as decoration.
- **No interpolated Tailwind class names.** Never build `` `text-${accent}-400` ``. Tailwind's
  JIT compiler can't discover dynamically-assembled class names. Maintain a static,
  fully-spelled-out class string per variant.
- **The single-tier glass card tell.** (NEW — confirmed in production render of phase section)
  A `glass.base` card that contains **only text and no nested glass elements** renders as a flat,
  near-opaque dark box — not as glass. This is the most common failure on non-hero pages. See
  §4.2 for the mandatory fix.
- **The missing-blob glass-depth tell.** (NEW) `backdrop-filter: blur(72px)` applied to a card
  sitting over pure near-black (`#030508`) with no color variation behind it produces a near-black
  surface that reads as a plain dark card. The glass effect requires either: (a) nested glass
  tiers visible inside the card, (b) a background color source near the card, or (c) both. Phase
  cards sitting in the middle of a long page fail because morphing blobs are positioned at far
  corners and don't reach them. See §4.2 and §7.

---

## 2. TECH STACK (already in use — match it, don't introduce alternatives)

- **React** with TypeScript (`.tsx`)
- **Framer Motion** for all animation — `motion`, `AnimatePresence`, `useMotionValue`,
  `useTransform`, `useSpring`, `useScroll`. Never use CSS transitions or `animate.css` for
  anything interactive; everything physics-driven goes through Framer Motion.
- **react-router-dom** for navigation (`useNavigate`)
- **@react-three/fiber** (`Canvas`, `useFrame`) for the ambient 3D background layer
- **lucide-react** for the rare, intentional icon (used sparingly — see §1)
- **Tailwind CSS** for layout/spacing/typography utility classes, with inline `style` objects for
  the glass material system (gradients, multi-layer box-shadows, backdrop-filter — these exceed
  what arbitrary Tailwind values can cleanly express)

---

## 3. COLOR SYSTEM

| Token | Value | Usage |
|---|---|---|
| Background | `#030508` | Page background — near-black, not pure black |
| Primary accent | `#10B981` (emerald-500/400) | Primary brand accent, positive/live states, chart line end, glow |
| Secondary accent | `#0D9488` (teal-500/400) | Secondary accent, gradient partner to emerald, alternates with emerald in repeating sequences |
| Text — primary | `text-white` | Headlines, primary content |
| Text — secondary | `text-white/60`, `/55`, `/50` | Body copy, descriptions |
| Text — tertiary | `text-white/40`, `/25` | Captions, axis labels, timestamps |
| Text — watermark | `text-white/[0.045]`, `/[0.04]` | Giant decorative typographic numerals only |

**Gradient recipe (line/accent gradients):** always teal → emerald, `linear-gradient`
left-to-right (`x1="0" x2="1"`), e.g. `#0D9488` → `#10B981`. Use this exact direction and
color order everywhere a two-stop accent gradient is needed (chart strokes, CTA glows, divider
lines).

**Glow recipe:** emerald glows use `rgba(16,185,129, α)` in box-shadow/drop-shadow, generally
layered as a tight glow (`0 0 10px`) plus a softer outer wash (`0 0 30–42px`) for breathing
CTAs. Status dots use `shadow-[0_0_8px_rgba(16,185,129,0.8)]`.

---

## 4. THE GLASS MATERIAL SYSTEM (exact tokens — copy verbatim)

Three nesting tiers exist. Each tier down reduces blur intensity and opacity to preserve a real
sense of depth — never use the same glass recipe for an outer card and the panel nested inside it.

```js
const glass = {
  // Tier 1 — outer card surface (hero cards, phase/narrative cards, mobile menu panel)
  base: {
    background: 'linear-gradient(145deg, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.028) 100%)',
    backdropFilter: 'blur(72px)',
    WebkitBackdropFilter: 'blur(72px)',
    border: '1px solid rgba(255,255,255,0.13)',
    boxShadow: [
      'inset 0 1.5px 0 rgba(255,255,255,0.26)',   // top specular highlight
      'inset 1.5px 0 0 rgba(255,255,255,0.09)',    // left specular highlight
      'inset -1px 0 0 rgba(0,0,0,0.08)',           // right edge shadow
      'inset 0 -1.5px 0 rgba(0,0,0,0.10)',         // bottom edge shadow
      '0 40px 100px rgba(0,0,0,0.52)',             // ambient drop shadow, far
      '0 8px 20px rgba(0,0,0,0.28)',               // contact shadow, near
    ].join(', '),
  },

  // Tier 2 — nested panel sitting on top of a base surface (chart panels, score badges, verdict box)
  // NO backdrop-filter — sits within the already-blurred base surface
  nested: {
    background: 'linear-gradient(145deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.01) 100%)',
    border: '1px solid rgba(255,255,255,0.085)',
    boxShadow: [
      'inset 0 1px 0 rgba(255,255,255,0.20)',
      'inset 1px 0 0 rgba(255,255,255,0.06)',
      '0 8px 32px rgba(0,0,0,0.22)',
    ].join(', '),
  },

  // Tier 3 — tight pill/badge surfaces (nav badges, status badges, secondary buttons)
  // NO backdrop-filter
  pill: {
    background: 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)',
    border: '1px solid rgba(255,255,255,0.10)',
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.20), 0 4px 12px rgba(0,0,0,0.15)',
  },
};
```

**Rule:** every new surface on a new page must map to one of these three tiers. Don't invent a
fourth glass recipe without a structural reason (i.e., a genuinely new nesting depth).

**Corner radii convention:** `rounded-[2.5rem]` for outer cards, `rounded-[1.5rem]` for nested
panels, `rounded-[1.25rem]` to `rounded-[0.875rem]` for pills/buttons/nav items, `rounded-full`
for status dots and circular badges only.

---

## 4.1 CANONICAL REFERENCE — lock this exact look

The hero card in Image 1 (the "RELIANCE" stock dashboard card) is the ground truth. **This
image is the canonical reference.** Any new card on any new page should be checked against it —
if a new card looks more "frosted/luminous" or more "flat/invisible" than this, the tokens or
nesting structure were implemented wrong.

**Read carefully — this is intentionally a *dark, restrained, smoked* glass, not a bright,
luminous, "frosted white" glass.** If you've seen visionOS/iOS Liquid Glass and expected
something closer to that — brighter, more obviously translucent, clear color bleeding through —
that is **not** the target here. This system trades that luminosity for an editorial, almost
charcoal, quietness.

**Why it looks exactly like this — three things must be true together, every time:**

1. **The page background must be near-black where the card sits.** `#030508` behind it, with
   only the sparse Three.js starfield for texture. `backdrop-filter: blur(72px)` heavily blurs
   whatever is behind the glass — point it at near-black and you get the smoked-charcoal result.
   **Do not** use `saturate()` or `brightness()` in the backdrop-filter — these amplify the
   emerald/teal background blobs and create a muddy green tint. **Do not** assume a card looks
   "broken" because it isn't glowing or showing obvious color refraction — that's correct.

2. **The alpha values in §4 are final, not a starting point.** The background gradient
   (`0.09 → 0.028`), the border (`0.13`), and the specular highlight (`0.26` top inset) are
   tuned precisely. **Never increase these values "to make the glass pop."** If a card isn't
   reading as glass, the fix is adding nested-tier children (§4.2), not higher opacity.

3. **Content sits at full opacity directly on the glass, with no extra scrim.** Headlines are
   pure `text-white`, captions/labels use the white-opacity ladder from §3 — never add a
   darkening overlay behind text "for legibility." Legibility comes from the glass already being
   dark enough relative to white text.

**What you should see in the reference hero card, and must check for on every new card:**
- A continuous, very thin (1px) lighter-gray border tracing the full rounded outline.
- A faint brightened line specifically along the *top* inner edge only (not all four edges
  evenly) — that asymmetry reads as "light source from above."
- **Three visibly distinct surface depths at once** — outer card (glass.base), nested panels
  inside it (glass.nested), and pills/badges inside those (glass.pill). Each is very slightly
  lighter than what it sits on. This multi-tier depth IS the glass effect.
- No visible blur-smear of color from behind the card — that's expected here, not missing.

---

## 4.2 THE SINGLE-TIER GLASS PROBLEM — mandatory pre-read for all non-hero cards

> **This is the root cause of the phase card flat-appearance issue confirmed in production
> renders (Image 2). Every new page built from this document must comply with the rule below.**

**The problem in plain language:**

When a `glass.base` card contains *only text* and no `glass.nested` or `glass.pill` children,
the card renders as a near-opaque dark box — indistinguishable from a generic `bg-gray-900`
card. The "glass" visual effect is not produced by `backdrop-filter: blur(72px)` alone.
`blur(72px)` applied over pure near-black (`#030508`) simply produces a near-black surface.

The glass effect is produced by **three-tier depth contrast visible inside the card at the same
time**. The hero card (Image 1) looks like glass because you can see all three tiers at a glance:
the outer shell, the chart/verdict nested panels, and the Live Analysis pill. Remove those inner
tiers and the outer shell immediately reads as a flat dark card.

**The mandatory rule:**

> **Every `glass.base` card must contain at least one `glass.nested` panel or `glass.pill`
> element visible inside it.** There are no exceptions.

For content-heavy cards like phase/narrative cards (which are primarily text), the required
nested element can be:

- **A glass.nested bottom strip** — a small `rounded-[1.5rem]` panel anchored to the card's
  bottom-left or bottom-right containing a phase-relevant micro-stat, accent metric, or label:

  ```jsx
  <div
    className="mt-8 inline-flex items-center gap-2 px-4 py-2 rounded-[1.25rem]"
    style={glass.nested}
  >
    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.8)]" />
    <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-emerald-400">
      Phase Complete
    </span>
  </div>
  ```

- **A glass.pill accent tag** — a small pill badge at the eyebrow level showing the phase
  number or step label:

  ```jsx
  <span
    className="inline-flex items-center px-3 py-1 rounded-full mb-4 text-[10px] font-bold tracking-[0.12em] uppercase text-emerald-400"
    style={glass.pill}
  >
    01 / 03
  </span>
  ```

- **A gradient top-edge divider line inside a `glass.nested` micro-panel** — even a thin
  decorative strip at the card top creates enough visible tier separation to register as glass.

**The background blob coverage problem:**

The two morphing blobs (§7) are anchored at the top-right and bottom-left corners, sized
600–800px. On a full Landing page, the phase/narrative section sits in the middle scroll zone
where neither blob reaches. This means the backdrop-filter of the phase cards is blurring pure
`#030508` — confirming that nested-tier children are the non-negotiable fix, not relying on
background color variation.

**For pages taller than ~200vh:** add a third, smaller morphing blob anchored to the page
center (approximately `top: 50%, left: 50%`, 400–500px, `bg-emerald-500/5 blur-[120px]`,
drifting on a 20s loop) to ensure the backdrop-filter has at least minimal color variation to
work with throughout the full page height.

**Summary — the two mandatory conditions for glass to read as glass:**
1. The card must have at least one `glass.nested` or `glass.pill` child visible inside it.
2. The background behind the card must not be a perfectly uniform flat `#030508` surface —
   either the Three.js particle field provides enough micro-texture, or a background blob is
   nearby, or both.

---

## 5. TYPOGRAPHY SYSTEM

- **Family:** system sans stack (`font-sans`) — premium system font, no decorative serif
  anywhere across the product.
- **Tracking:** `tracking-tighter` is the default everywhere — headlines **and** body copy.
  This is a deliberate, distinctive choice; don't relax it to normal tracking on body text.
- **Weight:** `font-bold` is the default for nearly all text in this system, including paragraph
  body copy — not just headings. Regular weight is reserved for rare cases only.
- **Display scale:**
  - Hero h1: `text-5xl md:text-[5.5rem]`, `leading-[1.02]` (extremely tight for massive type)
  - Section h2: `text-5xl md:text-7xl`, `leading-[1.05]`
  - Card h3: `text-3xl`
  - Subheading / body: `text-lg md:text-xl`, `leading-relaxed`, `text-white/60`
- **Micro-caption / eyebrow pattern:** `text-[9px]` to `text-[12px]`, `uppercase`,
  `tracking-[0.1em]` to `tracking-[0.18em]` (wide letter-spacing). Used for labels, phase
  eyebrows, axis ticks, and badge captions. The wide-tracked micro-caption paired against the
  ultra-tight-tracked display type is the core typographic contrast device — always pair them,
  never use a "medium" tracking value in between.
- **Numerals:** always `tabular-nums` for any price, score, percentage, or date.
- **Selective two-tone headlines:** secondary clause of a headline drops to `text-white/40`
  against a full-white first clause (e.g. `"Precision engineering."` white, `"Zero speculation."`
  at `/40`) — creates internal emphasis without changing size or weight.
- **Phase eyebrow color convention:** Phase 01 and Phase 03 cards use `text-emerald-400`
  eyebrows; Phase 02 uses `text-teal-400`. This alternating pattern is subtle by design — don't
  increase contrast or add extra visual weight to distinguish them further.

---

## 6. MOTION SYSTEM

### 6.1 Shared physics vocabulary

Define these once per page (or import from a shared module) and reuse everywhere — never write
an ad hoc spring config inline:

```js
const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 }; // hover/tap on buttons, nav, icons
const springSoft   = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 }; // layout/panel mount, nav active-pill
```

The hero 3D-tilt card uses softer springs on raw motion values:
`useSpring(value, { stiffness: 150, damping: 20 })`, then mapped to `rotateX`/`rotateY` via
`useTransform` (±10deg range). Reuse this exact recipe for any other mouse-tilt card.

### 6.2 Idle ambient motion (mandatory — at least one per section)

Nothing should ever sit completely still. Patterns in use:
- A headline word floats gently: `animate={{ y: [0, -5, 0] }}`, `duration: 7, repeat: Infinity,
  ease: 'easeInOut'`. Applied to "Intelligence" in the hero headline.
- A CTA button's glow breathes: animate `boxShadow` between tight and wide values on a 3s
  infinite loop, layered with `springPress` hover/tap transition.
- A status dot pulses: `animate-pulse` + `shadow-[0_0_8px_rgba(16,185,129,0.8)]` glow wherever
  something is "live."
- Background blobs continuously drift and morph (see §7).

### 6.3 Scroll-driven interactions

- **Page-level:** `useScroll()` with no target. Used to fade in the nav surface (`opacity` 0→1
  over the first 4% of scroll) and to gently compress the hero (`scale` 1→0.97, `opacity`
  1→0.55, `y` 0→-24px over the first 10% of scroll). Reuse this for any page's hero.
- **Section-scoped:** `useScroll({ target: ref, offset: ["start center", "end center"] })`
  drives a glowing orb traveling down a vertical guide line as the user scrolls through a
  narrative section. Reuse for any step-by-step or timeline section.
- **Reveal-on-scroll:** stacked content blocks use
  `initial={{ opacity: 0, y: 50 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-100px" }}`.
  This is the default reveal for any card/section entering the viewport — don't invent a
  different reveal curve on the same page.

### 6.4 Layout orchestration (AnimatePresence + layoutId)

- **Active-state indicator:** use a shared `layoutId="nav-active-pill"` background that slides
  between active items, transitioned with `springSoft`. Use this for any tab bar, segmented
  control, or filter chip group.
- **Mount/unmount:** the mobile menu and its trigger icon (Menu ↔ X) are wrapped in
  `AnimatePresence` with `initial`/`animate`/`exit` and `springPress`/`springSoft`. Any
  dropdown, modal, toast, or popover should follow this same enter/exit-with-spring pattern.

---

## 7. THE FLUID BACKGROUND CANVAS (exact recipe)

Every page keeps the same three-layer fixed background stack, in this order (z-0, behind all
content at z-10+):

1. **Static grid texture** — `bg-grid` utility class, `opacity-50`, `pointer-events-none`. This
   class must be defined in the global stylesheet as a subtle dot/line grid pattern. If the
   `bg-grid` class is not yet defined, define it in `globals.css`:
   ```css
   .bg-grid {
     background-image:
       linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
       linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
     background-size: 40px 40px;
   }
   ```

2. **Three.js ambient point field** — a `Canvas` containing a `points` mesh of ~2500 particles
   scattered in a `35 × 20 × 20` volume, `pointsMaterial` sized `0.045`, colored `#10B981`,
   `opacity 0.8`. Rotate continuously in `useFrame`:
   `rotation.y = elapsedTime * 0.06`, `rotation.z = sin(elapsedTime * 0.1) * 0.15`.
   Composited with `mix-blend-screen` over the page.

3. **Morphing organic blobs** — three `motion.div` elements with `blur-[120px]` to `blur-[150px]`:

   ```
   Blob A: top-right corner — emerald — 800×800px, bg-emerald-500/10, blur-[150px]
           Animates: x [0,40,-25,0], y [0,-30,20,0], scale [1,1.15,0.94,1]
           borderRadius: ['50%', '42% 58% 60% 40% / 50% 45% 55% 50%',
                          '58% 42% 40% 60% / 45% 55% 45% 55%', '50%']
           duration: 24s, repeat: Infinity, ease: 'easeInOut'

   Blob B: bottom-left corner — teal — 600×600px, bg-teal-500/10, blur-[150px]
           Animates: x [0,-30,30,0], y [0,25,-25,0], scale [1,0.9,1.12,1]
           borderRadius: ['50%', '60% 40% 38% 62% / 55% 45% 55% 45%',
                          '40% 60% 62% 38% / 45% 55% 45% 55%', '50%']
           duration: 28s, repeat: Infinity, ease: 'easeInOut', delay: 2

   Blob C (for pages taller than ~200vh): center — emerald — 400–500px,
           bg-emerald-500/5, blur-[120px]
           Position: top: 40–60% of page height, centered horizontally
           Animates: x [0,20,-20,0], y [0,-20,20,0], scale [1,1.1,0.95,1]
           borderRadius morph same pattern as Blob A
           duration: 20s, repeat: Infinity, ease: 'easeInOut', delay: 5
   ```

   Each blob is a `motion.div` animating **simultaneously**: `x`/`y` drift, `scale` breathing,
   and literal organic `borderRadius` morphing between asymmetric percentage values — this is
   what makes them read as fluid/organic rather than static glowing circles.

This three/four-layer stack is reused unchanged on every page.

### Data visualization recipe (charts)

Never hand-author a decorative path. Any chart needs:
1. A real data array (or fetched data).
2. A coordinate-mapping function (min/max normalize into the SVG viewBox).
3. A **Catmull-Rom-to-Bezier** smoothing pass:

```js
function buildSmoothPath(points) {
  let d = `M${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] || p2;
    const cp1x = p1.x + (p2.x - p0.x) / 6, cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6, cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
  }
  return d;
}
```

4. An area fill (`linearGradient`, top stop ~`stopOpacity 0.20`, bottom `0`) and 2–3
   ultra-faint (`rgba(255,255,255,0.05)`) horizontal reference lines — never a heavy data grid.
5. Any "live"/current marker positioned from the **actual last data point's coordinates**
   (`x / viewBoxWidth * 100%`, `y / viewBoxHeight * 100%`), never hardcoded.
6. Animate: stroke draws in with `pathLength` 0→1 (`duration: 2, ease: 'easeInOut'`), area
   fades in slightly after, live marker pops in last with a continuous pulse (`scale [1, 2.5, 1]`,
   `opacity [0.8, 0, 0.8]`, 2s infinite).

---

## 8. LAYOUT PATTERNS

- **Fixed-layer compositing:** all ambient backgrounds (`fixed inset-0`) sit at `z-0`; all real
  content at `z-10` or above; the nav at `z-50` with its own fading glass scrim at `z-40`.

- **Nav — confirmed layout (matches live renders):**
  - Logo left: `"INVR"` + `<span className="text-emerald-500">.</span>`, bold, `text-2xl`,
    `tracking-tighter`.
  - **No center navigation links** in the desktop layout — confirmed absent from both the live
    render and the code. The product currently uses a simplified nav with logo + CTA only.
    If center nav links are added in the future, they belong in a single `glass.pill` container
    with `layoutId="nav-active-pill"` sliding indicator. Until then, do not add phantom center
    links.
  - CTA/login right: `"Client Login"` button, `glass.pill` style, `springPress` on
    `whileHover`/`whileTap`, `hidden md:block`.
  - Mobile: hamburger (`Menu` icon) → `AnimatePresence` dropdown panel (`glass.base`,
    `rounded-[1.5rem]`) with text items at `text-sm font-bold tracking-tighter text-white/70`.
    Icon animates between Menu and X via `AnimatePresence mode="wait"` with spring rotation.
  - Nav scrim: `fixed top-0 inset-x-0 h-24 z-40`, `backdrop-filter: blur(20px)`,
    `background: linear-gradient(180deg, rgba(3,5,8,0.7) 0%, rgba(3,5,8,0) 100%)`,
    `opacity` driven by `useScroll` 0→1 over the first 4% of page scroll.

- **Hero: asymmetric split, never centered.** Copy block left-aligned in one column
  (headline → subhead); an interactive/visual element (tilt card, chart, demo) in the other
  column. Never default to a centered headline + centered subtext + centered button stack.
  Grid: `grid-cols-1 lg:grid-cols-2 gap-16`. Hero card is `hidden lg:flex`.

  > **Hero copy block confirmed components (Image 1):**
  > - h1 at `text-5xl md:text-[5.5rem] font-bold tracking-tighter leading-[1.02]`, pure white
  > - One word/phrase in `text-gradient-finance` CSS class (teal→emerald gradient, defined in
  >   globals: `background: linear-gradient(90deg, #0D9488, #10B981); -webkit-background-clip: text; -webkit-text-fill-color: transparent`)
  > - That gradient word also has a gentle idle float: `animate={{ y: [0, -5, 0] }}`, `duration: 7`
  > - Subheading: `text-lg md:text-xl font-bold tracking-tighter text-white/60 leading-relaxed`
  > - **No primary CTA button** in the hero section — confirmed absent from the live render.
  >   If a CTA is needed on future pages, see §9 for the recipe; do not add it to the Landing hero.

- **Narrative/process sections: alternating offset, not a grid.** Sequential content blocks
  alternate `self-start`/`self-end` at `md:w-[85%]` width, each with a connecting line
  (`w-24 h-[1px]`) bleeding off the card toward the section's vertical guide line at
  `bg-emerald-500/40` (Phase 01/03) or `bg-teal-500/40` (Phase 02) — use `/40` opacity, not
  `/20`, so the lines are actually perceptible.

- **Eyebrow → headline → body** is the standard content block order: wide-tracked micro-caption
  eyebrow, then large tight-tracked headline, then body copy at `text-white/55` to `/60`.

- **Static class lookups for per-item variants:** store complete Tailwind class strings per item
  in the data object, never interpolate a color name into a template string.

---

## 9. COMPONENT RECIPE LIBRARY (reusable across pages)

### Glass button (secondary)
`glass.pill` background, `springPress` on `whileHover`(scale 1.03)/`whileTap`(scale 0.96–0.97),
`text-sm font-bold tracking-tighter text-white`, `rounded-[1rem]`, `px-6 py-2.5`.

### Primary CTA
Solid white fill (`bg-white`), black text (`text-black`), `font-bold tracking-tighter`,
`springPress`, animated breathing `boxShadow` glow on a 3s infinite loop (tight emerald glow
expanding and contracting), `ArrowRight` icon trailing with `ml-2`.

### Status / live badge
`glass.pill`, small pulsing dot (`animate-pulse` + `shadow-[0_0_8px_rgba(16,185,129,0.8)]`
glow, `bg-emerald-500`, `w-2 h-2 rounded-full`) + uppercase micro-caption `text-[11px] font-bold
tracking-tighter text-white uppercase`. Example: "LIVE ANALYSIS".

### Score / metric badge
`glass.nested`, `rounded-[1.25rem]`, `px-5 py-3`. Large `tabular-nums` number in `text-2xl
font-bold tracking-tighter text-white leading-none`, stacked over a tiny `text-[9px] font-bold
tracking-[0.15em] text-emerald-400 uppercase mt-1` label. No icon.

### Narrative / process card (UPDATED — nesting requirement mandatory)
`glass.base`, `p-10 md:p-14`, `rounded-[2.5rem]`, `overflow-hidden`. Contains:

1. **Giant typographic numeral watermark:** `absolute -top-6 -left-3`, `text-[9rem] md:text-[11rem]`,
   `font-bold leading-none text-white/[0.045] select-none pointer-events-none tracking-tighter`,
   `aria-hidden="true"`.

2. **Eyebrow:** `text-[11px] font-bold tracking-[0.15em] uppercase` in `text-emerald-400` (odd
   phases) or `text-teal-400` (even phases), `mb-1.5`.

3. **Headline:** `text-3xl font-bold text-white tracking-tighter mb-6 max-w-md`.

4. **Body:** `text-white/55 text-lg leading-relaxed font-bold tracking-tighter max-w-xl`.

5. **⚠ MANDATORY — nested glass element:** Every phase card must end with at least one of:
   - A `glass.nested` or `glass.pill` mini-badge/strip (see examples in §4.2).
   - A `glass.nested` mini-panel containing a phase-relevant accent (small metric, keyword
     chip, step counter pill, etc.).
   - Minimum viable version: a `glass.pill` inline badge after the body text showing the phase
     step label (`"01 / 03"`, `"02 / 03"`, `"03 / 03"`) in emerald/teal micro-caption text.

   **Without this element, the card renders as a flat dark box. This is non-negotiable.**

### Data chart panel
`glass.nested` wrapper, `rounded-[1.5rem]`, `p-6`. Chart built per the §7 recipe. Axis tick
labels beneath at `text-[9px] font-bold tracking-[0.1em] text-white/25 uppercase`. Header row:
`text-[12px] font-bold tracking-tighter text-white/40 uppercase mb-4` with label on left, current
value in `text-white/70` on right.

### Verdict / insight panel
`glass.nested`, `rounded-[1.5rem]`, `p-6`, `overflow-hidden`. Thin gradient top divider:
`absolute top-0 left-8 right-8 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/40
to-transparent`. Uppercase emerald eyebrow (`text-[10px] font-bold tracking-[0.18em]
text-emerald-400 uppercase mb-2.5`), then body text in `text-sm text-white/75 font-bold
tracking-tighter leading-relaxed`.

### Hero dashboard card (3D tilt)
`glass.base`, `p-8`, `rounded-[2.5rem]`. Mouse-move tilt via `useMotionValue` → `useSpring` →
`useTransform` (±10deg). Contains three nested tiers:
- Status row: `glass.pill` badge (Live Analysis) + timestamp label
- Stock header: ticker name + percentage badge + score box (`glass.nested`)
- Chart panel: `glass.nested` wrapping the price SVG chart
- Verdict panel: `glass.nested` with gradient top divider

---

## 10. CHECKLIST FOR BUILDING A NEW PAGE

Work through this list before writing any JSX:

1. Start from the same three-layer background stack (§7) and the same fading nav scrim — don't
   rebuild these per page. Add Blob C if the page content exceeds ~200vh.

2. Identify this page's **one signature element** — spend your boldness in one place, keep the
   rest disciplined.

3. Map every surface to one of the three glass tiers (§4) — never invent a fourth.

4. **Audit every `glass.base` card: does it contain at least one `glass.nested` or `glass.pill`
   child?** If not, add one (see §4.2 and §9 narrative card recipe). A glass.base card with
   only text children is a flat dark box — this check is mandatory.

5. Use `springPress`/`springSoft` for all interactions — never an inline one-off spring.

6. Give every section at least one idle-motion element (§6.2) — nothing static.

7. If the page has sequential content, use the alternating-offset narrative pattern (§8) with
   earned numbering; if it's not truly sequential, don't number it.

8. If the page has an icon, ask: is it sparse, intentional, and unboxed? If it's a small icon
   in a circle next to a header, replace it with a typographic or numeral device instead.

9. If the page has a chart or live value, build it from real data through the smoothing function
   in §7 — never a decorative hand-typed path, never a hardcoded marker position.

10. Check for any interpolated Tailwind class names and replace with static per-variant strings.

11. Confirm mobile: nav collapses to the `AnimatePresence` hamburger pattern, hero stacks to a
    single column, narrative cards drop their `md:w-[85%]` offset to full width.

12. Check the nav layout: logo left, CTA button right. Do not add center nav links unless the
    product spec calls for them explicitly; the Landing page nav is intentionally minimal.

13. Verify connecting lines on narrative cards are at `/40` opacity, not `/20` — at `/20` they
    are invisible and the connecting-line device loses all purpose.
