---
name: html-deck
description: Build self-contained HTML presentation decks with the <deck-stage> web component. Handles keyboard nav, auto-scale to viewport, one-page-per-slide print to PDF, speaker notes, and localStorage resume. Use when authoring slide presentations in HTML instead of PPTX, Keynote, or Google Slides.
---

# HTML deck

Single-file decks built on a custom element (`<deck-stage>`) shipped with this skill. You author one HTML file. The element handles navigation, scaling, print, and persistence. Output is a portable folder that opens locally, deploys to any static host, and prints cleanly to PDF.

## Files shipped with this skill

- `${CLAUDE_SKILL_DIR}/deck-stage.js` — the runtime. Copy it next to every deck.
- `${CLAUDE_SKILL_DIR}/template.html` — minimal 3-slide starter. Copy and edit.
- `${CLAUDE_SKILL_DIR}/references/rollout-guard-example.html` — full-fledged example with production typography and layout patterns. Read this when you need inspiration for a serious deck.

## Inputs to ask for before authoring

This skill does not invent aesthetics. Before writing any slide, get three things from the user. If any are missing, ask. A guessed aesthetic is almost always generic.

- **Feel / register.** One sentence: technical, editorial, corporate, minimalist, playful, academic, etc.
- **Color palette.** Either explicit hex values or a description concrete enough to translate ("dark, warm, one amber accent"). One dominant color at 60–70% visual weight, one or two supporting tones, one sharp accent.
- **Typography direction.** Serif or sans, display or utilitarian. If the user has no opinion, pick one pairing and commit.

## Workflow

1. **Draft in markdown first.** One section per slide. Annotate structure and emphasis inline (e.g. `[cover]`, `[3-col]`, `[dark]`, `[pull-quote]`, `**key phrase**`). Do not write HTML yet.
2. **Review the markdown as a deck.** Spot commonalities: if five slides are "title + three columns," they share a layout. If two are "big quote + attribution," same. Note which slides deserve a contrasting background to draw attention, and keep that list short.
3. **Translate to HTML.** Build the shared chassis first (palette, type scale, chrome, common layouts as CSS classes). Then instantiate each slide against those classes. Do not author slides in isolation.
4. **Preview and iterate.** See "Preview and export" below.

## Skeleton

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>My deck</title>
  <script src="deck-stage.js"></script>
  <style>/* deck styles */</style>
</head>
<body>
  <deck-stage width="1920" height="1080">
    <section data-label="01 Cover">...</section>
    <section data-label="02 Intro">...</section>
  </deck-stage>
</body>
</html>
```

- **Design size** is set once via `width`/`height` on `<deck-stage>`. Every slide renders at those exact pixel dimensions and scales to fit the window, letterboxed.
- **Each `<section>` is a slide.** Siblings stack at `inset: 0`; the active slide gets `data-deck-active`. Don't wrap slides in extra containers.
- **`data-label="NN Title"`** names the slide for speaker notes and comment flow. Use a two-digit prefix so ordering matches numbering.

## Authoring rules (runtime mechanics)

- **Position is absolute inside the canvas.** The component sets `position: absolute; inset: 0` on every `<section>`. Your slide layout uses normal flow inside that fixed-size box.
- **Use absolute pixel values** matching the design size (e.g. `padding: 96px 120px`, `font-size: 72px` at 1920×1080). Don't use viewport units; the canvas is scaled, not responsive.
- **Safe type scale at 1920×1080:** 26–30px body, 56–72px section titles, 112–220px display/cover.
- **Non-active slides stay in the DOM.** State (videos, iframes, inputs, React trees) is preserved across navigation.
- **Set `text-wrap: balance`** on titles so line breaks look intentional.

## Consistency discipline

- **Shared styling in global CSS, not inline.** Every `<em>`, `<strong>`, `<h2>`, `.eyebrow`, `.stat`, `.footnote` should render identically across slides. Use class names. If you've pasted the same `style="..."` twice, extract it. Inline styles reserved for genuine one-offs.
- **Variation is signal, not decoration.** A light background in a mostly-dark deck means "this slide is different and important" (section divider, key stat, call to action). If every slide has a unique background, none of them do.
- **Don't hardcode the same fact twice.** Hardcoding a slide number (`03/12`) per slide is fine — the work happens once, at authoring time. What's not fine is duplicating that number elsewhere (top chrome *and* footer, page title *and* slide title, etc.). A fact that appears in two places has to be changed in two places when the deck shifts.
- **Minimize repeated chrome.** Deck title, section name, page number: pick one and apply it through a shared class, or omit it. Cramming brand + section + page + date onto every slide is clutter. Prefer clean; the runtime already handles counting.
- **Same shape → same layout class.** Four three-column slides should use one layout class, not four hand-laid grids. Differences between them live in the content, not the structure.

## Design guardrails

Universal rules that apply to any deck, regardless of feel:

- **Colors that fit this topic.** A palette that would also work for a dentist and a crypto pitch means you haven't chosen specifically enough.
- **One dominant color, one accent.** Never give three or more colors equal weight.
- **Left-align body text.** Center only titles and cover slides.
- **Every slide needs a visual anchor.** Text-only slides are forgettable. A stat, an icon, a chart, a framed quote, a pulled phrase — something.
- **Strong size contrast on titles.** 72px+ titles over 26–32px body. When they're close in size, the hierarchy collapses.
- **Never an accent line under a title.** It's a hallmark of AI-generated slide filler. Use whitespace or a background shift instead.
- **Don't default to blue.** Pick colors that fit the topic.
- **Commit to one motif.** A repeated element (rule color, shape, chrome pattern) carried across every slide, not scattered.
- **Breathing room.** 96–120px side margins at 1920×1080. Don't fill every pixel.

## Assets

- **Fonts: Google Fonts.** Link from `fonts.googleapis.com` in the `<head>`. Limit to 2–3 families total (display, body, mono). The example deck pairs Instrument Serif + IBM Plex Sans + JetBrains Mono.
- **Icons: FontAwesome, inlined as SVG.** Do not link the full FontAwesome CSS or JS bundle; it ships icons you won't use and adds a network dependency for the exported HTML. Grab the raw SVG for each icon you need from the FontAwesome site and inline it, either pasted at the use site or (preferred when the same icon recurs) as a `<symbol>` in a hidden sprite at the top of `<body>`:

  ```html
  <svg style="display:none" aria-hidden="true">
    <symbol id="i-check" viewBox="0 0 512 512"><path d="..."/></symbol>
    <symbol id="i-alert" viewBox="0 0 512 512"><path d="..."/></symbol>
  </svg>
  <!-- elsewhere -->
  <svg class="icon"><use href="#i-check"/></svg>
  ```

- **One icon style per deck.** Pick one FontAwesome variant (solid, regular, light, thin, duotone) and stay in it. Mixing weights reads as sloppy.
- **Size icons to the local type scale.** An icon next to 30px body text sits around 30px; an icon in a 22px eyebrow sits around 22px. Use a shared `.icon` class with `width: 1em; height: 1em; fill: currentColor` and let surrounding font-size set the size.

## Speaker notes

Optional. Include a JSON script with one entry per slide:

```html
<script type="application/json" id="speaker-notes">
[
  { "title": "Cover", "notes": "Open with the frame." },
  { "title": "Intro", "notes": "Land the why-now beat first." }
]
</script>
```

The component dispatches a `slidechange` event and posts `{slideIndexChanged: N}` to the parent window, so any notes renderer can wire into either.

## Controls (built-in)

- ← / → / PgUp / PgDn / Space — prev / next
- Home / End — first / last
- 1–9 — jump to slide N (0 → slide 10)
- R — reset to first slide
- Mobile: tap the left third to go back, right third to go forward

## Preview and export

```bash
# Preview (any static server works)
python3 -m http.server 8000
# or: npx serve .

# Export to PDF
# Open the deck in browser, File → Print → Save as PDF.
# The component injects @page rules sized to your design dimensions,
# so output is one slide per page with no margins.
```

For PPTX export, capture each slide with Playwright at authored size and set the `noscale` attribute on `<deck-stage>` so the captured DOM is unscaled.

Bootstrap a new deck by making a folder, copying `${CLAUDE_SKILL_DIR}/deck-stage.js` and `${CLAUDE_SKILL_DIR}/template.html` into it, then editing the template.

## Programmatic API

```js
const deck = document.querySelector('deck-stage');
deck.goTo(3); deck.next(); deck.prev(); deck.reset();
deck.index;   // current 0-based index
deck.length;  // total slide count

deck.addEventListener('slidechange', (e) => {
  // e.detail.index, previousIndex, total, slide, previousSlide, reason
});
```

Full component documentation is in the header comment of `deck-stage.js`.
