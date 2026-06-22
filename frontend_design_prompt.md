# Master Build Prompt — Liquid Glass Design System

Use this prompt to build **any new page** for this product. It contains the original creative
brief in full, plus the exact design tokens, component recipes, and anti-slop rules that were
derived from building the Landing page — so every new page is pixel- and physics-consistent with
it, not just "in the same vibe."

> **Before building anything, read §4.1.** It contains a real reference screenshot of the glass
> material and the exact rules for reproducing it — the look it documents is dark and restrained
> by design, not the brighter "frosted" glass the term might suggest elsewhere.

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
we caught and fixed while building this system — treat the second half of this list as
**evidence**, not theory.

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
- **The icon-in-a-badge tell.** The original Phase cards put a Lucide icon (Search, Fingerprint,
  Target) inside an identical small `glass.nested` rounded square next to every header. This is
  the single most common AI-template fingerprint. It was replaced with a giant, near-invisible
  typographic watermark numeral (`01` / `02` / `03`) bleeding off the card edge. **Never put a
  small icon in an identical rounded box next to a heading, anywhere in this product.**
- **The decorative-arc chart tell.** The original price chart was a hand-typed 4-command Bezier
  (`M0,80 Q50,70 100,85 T200,50 T300,30 T400,20`) — a single smooth swoop that goes perfectly
  up-and-to-the-right with zero volatility. Any chart in this product must be generated from an
  actual data array run through a real interpolation function (Catmull-Rom-to-Bezier — recipe in
  §7), never a hand-authored decorative curve.
- **The hardcoded "live" marker tell.** The original chart's pulsing "live" dot sat at a
  hardcoded `top-[12%]` position that didn't even align with where the curve actually ended. Any
  live/current-value indicator must be positioned by computing its coordinate from the real
  last-data-point, never eyeballed into a plausible-looking spot.
- **Numbered markers must be earned.** `01 / 02 / 03` style devices are only legitimate when the
  content is a genuine ordered sequence (a real process, a real timeline) where order carries
  information the reader needs. Don't add numbering as decoration to content that isn't actually
  sequential.
- **No interpolated Tailwind class names.** Never build a class string like
  `` `text-${accent}-400` ``. Tailwind's JIT compiler can't discover dynamically-assembled class
  names and will silently drop the styling. Maintain a static, fully-spelled-out class string per
  variant (see the `phases` array pattern in §8) instead.
- **Numbered/sequential content only where real**, per above — applies to any future timeline,
  pricing-tier, or step-based UI too.

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

**Gradient recipe (line/accent gradients):** always teal → emerald, `linear-gradient` left-to-right
(`x1="0" x2="1"`), e.g. `#0D9488` → `#10B981`. Use this exact direction and color order everywhere
a two-stop accent gradient is needed (chart strokes, CTA glows, divider lines).

**Glow recipe:** emerald glows use `rgba(16,185,129, α)` in box-shadow/drop-shadow, generally
layered as a tight glow (`0 0 10px`) plus a softer outer wash (`0 0 30–42px`) for breathing CTAs.

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
  // NO backdrop-filter — crystal clear transparent glass, no blur
  nested: {
    background: 'linear-gradient(145deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.01) 100%)',
    border: '1px solid rgba(255,255,255,0.085)',
    boxShadow: [
      'inset 0 1px 0 rgba(255,255,255,0.20)',
      'inset 1px 0 0 rgba(255,255,255,0.06)',
      '0 8px 32px rgba(0,0,0,0.22)',
    ].join(', '),
  },

  // Tier 3 — tight pill/badge surfaces (nav group, status badges, secondary buttons)
  // NO backdrop-filter — crystal clear transparent glass, no blur
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
panels, `rounded-[1.25rem]` to `rounded-[0.875rem]` for pills/buttons/nav items, `rounded-full` for
status dots and circular badges only.

---

## 4.1 CANONICAL REFERENCE — lock this exact look

This is a real render of the hero card (`glass.base` containing `glass.pill` and `glass.nested`
children) using the tokens in §4 exactly as written. **This image is the ground truth.** Any new
card on any new page should be checked against it — if a new card looks more "frosted/luminous" or
more "flat/invisible" than this, the tokens were tuned wrong.

![Canonical liquid glass card reference](./reference-hero-card.png)

**Read carefully — this is intentionally a *dark, restrained, smoked* glass, not a bright,
luminous, "frosted white" glass.** If you've seen visionOS/iOS Liquid Glass and expected something
closer to that — brighter, more obviously translucent, clear color bleeding through — that is
**not** the target here. This system trades that luminosity for an editorial, almost charcoal,
quietness, and that restraint is itself the anti-slop choice: a too-bright frosted panel is closer
to the generic "AI slop glass card" look this whole system exists to avoid.

**Why it looks exactly like this — three things have to be true together, every time:**

1. **The page background must be near-black and mostly empty where the card sits.** `#030508`
   behind it, with only the sparse Three.js starfield (§7) for texture. `backdrop-filter: blur(72px)`
   heavily blurs whatever is behind the glass — point it at near-black and you get the exact
   smoked-charcoal result. **Do not** use `saturate()` or `brightness()` in the backdrop-filter —
   these amplify whatever color sits behind the glass (the emerald/teal background blobs) and create
   a muddy green tint instead of clean glass. **Do not** assume a card looks "broken" or
   "unfinished" because it isn't glowing or showing obvious color refraction — that's correct,
   not a bug. A glass card does **not** need one of the morphing color blobs (§7) positioned
   directly behind it to look right; this reference card has none nearby and is correct as-is.
2. **The alpha values in §4 are final, not a starting point.** The background gradient
   (`0.09 → 0.028`), the border (`0.13`), and the specular highlight (`0.26` top inset) are tuned
   precisely to produce: a barely-there lightening of the surface versus the page background, a
   thin but visible edge outline, and a faint brightened hairline at the top of the card (look
   closely at the top edge in the reference — that's the entire "specular highlight," it is meant
   to be subtle, not a visible shine). **Never increase these values "to make the glass pop" or
   "make it read more clearly as glass."** If a card isn't reading as glass, the fix is contrast
   against its neighbors (tier 1 vs. tier 2 vs. tier 3, per §4's three-tier rule) and correct
   corner-radius/shadow layering — not higher opacity.
3. **Content sits at full opacity directly on the glass, with no extra scrim.** Headlines are pure
   `text-white`, captions/labels use the white-opacity ladder from §3 — never add a darkening
   overlay behind text "for legibility." Legibility comes from the glass already being dark enough
   relative to white text; an extra scrim flattens the depth and is what makes a card start to look
   like a generic dark card-with-border instead of an actual material.

**What you should be able to see in the reference, and should check for on every new card:**
- A continuous, very thin (1px) lighter-gray border tracing the full rounded outline.
- A faint brightened line specifically along the *top* inner edge only (not all four edges evenly)
  — that asymmetry is what reads as "light source from above" rather than a flat stroke.
- Three visibly distinct surface depths at once (outer card, the chart/verdict panels nested
  inside it, the small pills/badges nested inside those) — each very slightly lighter than the one
  it sits on, never the same flatness twice.
- No visible blur-smear of color from behind the card — that's expected here, not missing.

---

## 5. TYPOGRAPHY SYSTEM

- **Family:** system sans stack (`font-sans`) — premium system font, no decorative serif anywhere.
- **Tracking:** `tracking-tighter` is the default everywhere — headlines **and** body copy. This
  is a deliberate, distinctive choice; don't relax it to normal tracking on body text.
- **Weight:** `font-bold` is the default for nearly all text in this system, including paragraph
  body copy — not just headings. Regular weight is reserved for rare cases only.
- **Display scale:** hero headlines run `text-5xl md:text-[5.5rem]` with `leading-[1.02]`
  (extremely tight line-height for massive type). Section headlines run `text-5xl md:text-7xl`
  with `leading-[1.05]`. Card headlines run `text-3xl`.
- **Micro-caption / eyebrow pattern:** `text-[9px]` to `text-[12px]`, `uppercase`,
  `tracking-[0.1em]` to `tracking-[0.18em]` (wide letter-spacing), used for labels, phase
  eyebrows, axis ticks, and badge captions. This wide-tracked micro-caption paired against the
  ultra-tight-tracked display type is the core typographic contrast device of the system — always
  pair them, never use a "medium" tracking value in between.
- **Numerals:** always `tabular-nums` for any price, score, percentage, or date.
- **Selective two-tone headlines:** secondary clause of a headline often drops to `text-white/40`
  against a full-white first clause (e.g. "Precision engineering. / Zero speculation." with the
  second line muted) — use this to create internal emphasis without changing size or weight.

---

## 6. MOTION SYSTEM

### 6.1 Shared physics vocabulary
Define these once per page (or import from a shared module) and reuse everywhere — never write an
ad hoc spring config inline. Consistency of physics across components is what makes the whole UI
feel like one material.

```js
const springPress = { type: 'spring', stiffness: 420, damping: 26, mass: 0.6 }; // hover/tap on buttons, nav, icons
const springSoft   = { type: 'spring', stiffness: 220, damping: 28, mass: 0.9 }; // layout/panel mount, nav active-pill
```

The hero 3D-tilt card uses its own softer spring on the raw motion values:
`useSpring(value, { stiffness: 150, damping: 20 })`, then maps to `rotateX`/`rotateY` via
`useTransform` (±10deg range). Reuse this exact recipe for any other mouse-tilt card.

### 6.2 Idle ambient motion (mandatory — at least one per section)
Nothing should ever sit completely still. Patterns already in use:
- A headline word floats gently: `animate={{ y: [0, -5, 0] }}`, `duration: 7, repeat: Infinity, ease: 'easeInOut'`.
- A CTA button's glow breathes: animate `boxShadow` between a tight and wide value on a 3s
  infinite loop, layered with its `springPress` hover/tap transition.
- A status dot pulses (`animate-pulse` + matching `shadow-[0_0_8px_...]` glow) wherever something
  is "live."
- Background blobs continuously drift and morph (see §7).

### 6.3 Scroll-driven interactions
- **Page-level:** `useScroll()` with no target tracks whole-document progress. Used to fade in the
  nav surface (`opacity` 0→1 over the first 4% of scroll) and to gently compress the hero
  (`scale` 1→0.97, `opacity` 1→0.55, `y` 0→-24px over the first 10% of scroll). Reuse this exact
  "first 10%" compression recipe for any other page's hero.
- **Section-scoped:** `useScroll({ target: ref, offset: ["start center", "end center"] })` drives
  a glowing orb traveling down a vertical guide line as the user scrolls through a narrative/story
  section (`top` and `scale` mapped via `useTransform`). Reuse for any future step-by-step or
  timeline section.
- **Reveal-on-scroll:** stacked content blocks use
  `initial={{ opacity: 0, y: 50 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-100px" }}`.
  This is the default reveal for any card/section entering the viewport — don't invent a different
  reveal curve elsewhere on the same page.

### 6.4 Layout orchestration (`AnimatePresence` + `layoutId`)
- **Active-state indicator:** nav items use a shared `layoutId="nav-active-pill"` background that
  slides between whichever item is active, transitioned with `springSoft`. Use this exact pattern
  for any tab bar, segmented control, or filter chip group elsewhere in the product.
- **Mount/unmount:** the mobile menu and its trigger icon (Menu ↔ X) are wrapped in
  `AnimatePresence` with `initial`/`animate`/`exit` and `springPress`/`springSoft`. Any
  dropdown, modal, toast, or popover in the product should follow this same
  enter/exit-with-spring pattern rather than a plain CSS fade.

---

## 7. THE FLUID BACKGROUND CANVAS (exact recipe)

Every page keeps the same three-layer fixed background stack, in this order (z-0, behind all
content at z-10+):

1. **Static grid texture** — `bg-grid` utility class, low opacity (`opacity-50`), `pointer-events-none`.
2. **Three.js ambient point field** — a `Canvas` containing a `points` mesh of ~2500 particles
   scattered in a `35 × 20 × 20` volume, `pointsMaterial` sized `0.045`, colored `#10B981`,
   `opacity 0.8`. Rotate it continuously and very slowly in `useFrame`:
   `rotation.y = elapsedTime * 0.06`, `rotation.z = sin(elapsedTime * 0.1) * 0.15`. Composited
   with `mix-blend-screen` over the page.
3. **Morphing organic blobs** — two large (`600–800px`) blurred (`blur-[150px]`) color washes
   (one emerald, one teal) positioned off-canvas at opposing corners. Each is a `motion.div`
   animating **simultaneously**: `x`/`y` drift (±20–40px), `scale` breathing (0.9–1.15), and a
   literal organic `borderRadius` morph between asymmetric percentage values (e.g.
   `'42% 58% 60% 40% / 50% 45% 55% 50%'`) — this is what makes them read as fluid/organic rather
   than static glowing circles. Loop duration 22–28s, `ease: 'easeInOut'`, `repeat: Infinity`,
   offset the second blob's loop with a `delay` so they never sync.

This three-layer stack is the literal implementation of the brief's "Fluid Background Canvas"
requirement — reuse it unchanged on every new page rather than re-deriving it.

### Data visualization recipe (charts)
Never hand-author a decorative path. Any chart needs:
1. A real data array (or fetched data).
2. A coordinate-mapping function (min/max normalize into the SVG viewBox).
3. A **Catmull-Rom-to-Bezier** smoothing pass over the mapped points (not a raw polyline, not a
   hand-typed `Q`/`T` arc) so the line is fluid but still reflects genuine data shape/volatility:

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
4. An optional area fill (`linearGradient`, top stop ~`stopOpacity 0.20`, bottom `0`) and 2–3
   ultra-faint (`rgba(255,255,255,0.05)`) horizontal reference lines — never a heavy data-grid.
5. Any "live"/current marker positioned by reading the **actual last point's coordinates**
   (`x / viewBoxWidth * 100%`, `y / viewBoxHeight * 100%`), never a hardcoded percentage.
6. Animate the stroke in with `pathLength` 0→1 (`duration: 2, ease: 'easeInOut'`), area fade in
   slightly after, live marker pop in last with a continuous pulse (`scale [1, 2.5, 1]`,
   `opacity [0.8, 0, 0.8]`, 2s infinite).

---

## 8. LAYOUT PATTERNS

- **Fixed-layer compositing:** all ambient backgrounds (`fixed inset-0`) sit at `z-0`; all real
  content sits at `z-10` or above; the nav sits at `z-50` with its own fading glass scrim at `z-40`.
- **Nav, not three even columns:** logo on the left, nav links grouped inside a single `glass.pill`
  container in the center (not spread across the bar), CTA/login button on the right. Active link
  state is the `layoutId` sliding-pill (§6.4), not an underline or color-only change. Provide a
  hamburger trigger + `AnimatePresence` dropdown panel (`glass.base`) below `md` breakpoint — never
  ship a page without a working mobile nav.
- **Hero: asymmetric split, never centered.** Copy block left-aligned in one column (headline →
  subhead → CTA row → status line), an interactive/visual element (tilt card, chart, demo) in the
  other column. Never default to a centered headline + centered subtext + centered button stack.
- **Narrative/process sections: alternating offset, not a grid.** Sequential content blocks
  alternate `self-start`/`self-end` at `md:w-[85%]` width (not 100%, not an even grid), each with a
  short connecting line (`w-24 h-[1px]`) bleeding off the card toward the section's vertical guide
  line. A scroll-linked glow orb (§6.3) travels the guide line as the reader scrolls.
- **Eyebrow → headline → body** is the standard content block order wherever a section needs
  introducing: a wide-tracked micro-caption eyebrow (§5), then a large tight-tracked headline,
  then body copy at `text-white/55` to `/60`.
- **Static class lookups for per-item variants:** when mapping over an array to render visually
  distinct cards/items (e.g., alternating accent colors), store the **complete** Tailwind class
  string per item in the data object (`edgeClass`, `eyebrowClass`, etc.) rather than interpolating
  a color name into a template string (§1).

---

## 9. COMPONENT RECIPE LIBRARY (reusable across pages)

- **Glass button** — `glass.pill` background, `springPress` on `whileHover`(scale 1.03)/`whileTap`
  (scale 0.96–0.97).
- **Primary CTA** — solid white fill, black text, `springPress`, animated breathing `boxShadow`
  glow (3s loop), `ArrowRight` icon trailing.
- **Status/live badge** — `glass.pill`, small pulsing dot (`animate-pulse` + glow shadow) +
  uppercase micro-caption, e.g. "Live Analysis."
- **Score/metric badge** — `glass.nested`, large `tabular-nums` number stacked over a tiny
  uppercase emerald label — no icon.
- **Narrative/process card** — `glass.base`, giant low-opacity typographic numeral watermark
  bleeding off the top-left corner, eyebrow → headline → body inside, alternating left/right
  offset position (§8). Use only for genuinely sequential content.
- **Data chart panel** — `glass.nested` wrapper, chart built per the §7 recipe, axis tick labels
  beneath at `text-[9px] text-white/25 uppercase tracking-[0.1em]`.
- **Verdict/insight panel** — `glass.nested`, thin gradient top divider
  (`bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent`), uppercase emerald
  eyebrow, then body text — use for any "system says X" summary box.

---

## 10. CHECKLIST FOR BUILDING A NEW PAGE

When asked to build another page in this product, work through this list before writing JSX:

1. Start from the same three-layer fixed background stack (§7) and the same fading nav scrim —
   don't rebuild these per page.
2. Identify this page's **one signature element** — the thing this page will be remembered by
   (per the design skill: spend your boldness in one place, keep the rest disciplined). Don't
   make every section equally loud.
3. Map every surface to one of the three glass tiers (§4) — never invent a fourth.
4. Use the shared `springPress`/`springSoft` constants for all interaction — never an inline
   one-off spring.
5. Give every section at least one idle-motion element (§6.2) — nothing static.
6. If the page has sequential content, use the alternating-offset narrative pattern (§8) with
   earned numbering; if it's not truly sequential, don't number it.
7. If the page has any icon, ask: is it sparse, intentional, and unboxed? If it's a small icon in
   a circle next to a header, stop and replace it with a typographic or numeral device instead.
8. If the page has a chart or live value, build it from real data through the smoothing function
   in §7 — never a decorative hand-typed path, never a hardcoded marker position.
9. Check for any interpolated Tailwind class names and replace with static per-variant strings.
10. Confirm mobile: nav collapses to the `AnimatePresence` hamburger pattern, hero stacks to a
    single column, narrative cards drop their `md:w-[85%]` offset to full width.