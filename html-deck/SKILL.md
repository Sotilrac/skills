---
name: html-deck
description: Build slide decks as single-file Bento presentations (.bento.html, https://bento.page). The deck is plain JSON inside the file, so you author the document, splice it in with the bundled script, and the file includes its own viewer, editor, presenter, PDF export and speaker notes. Use whenever the user wants a presentation, slides, a deck, a talk, a pitch, a keynote, or a slideshow in HTML instead of PPTX, Keynote or Google Slides, or asks to edit an existing .bento.html. Ships a CLI (fetch, extract, splice, fonts, check with real-browser validation and per-slide screenshots), a generator template, and the bento format guide.
---

# HTML deck (Bento)

A deck is one `.bento.html` file. The Bento app (viewer, editor, presenter, PDF export) is the file; the presentation is a JSON document in a single block near the top:

```html
<script type="application/bento+json" id="bento-doc">{ "format": "bento/slides", ... }</script>
```

You author that JSON and splice it in. Everything else in the file stays as downloaded. The result opens locally, deploys to any static host, and the recipient needs nothing installed.

## Files shipped with this skill

- `${CLAUDE_SKILL_DIR}/scripts/bento.mjs`: the CLI. `fetch` downloads the app, `extract` pulls the JSON out of a deck, `splice` writes it back with the right escaping and an offline lint, `fonts` embeds Google Fonts as woff2 assets, `check` opens the deck in headless Chromium, runs the runtime validator and screenshots every slide.
- `${CLAUDE_SKILL_DIR}/template/build.mjs`: a generator starter. Presets for type and color, layout helpers with the column arithmetic done, three slides. Copy it into the deck folder and edit.
- `${CLAUDE_SKILL_DIR}/references/bento-agents.md`: the bento/slides format guide (element types, fx, morph, charts, tables, states, layout arithmetic, gotchas). Read it once before authoring; refer back for exact field names. The live copy is https://bento.page/agents.md.

## Inputs to ask for before authoring

This skill does not invent aesthetics. A guessed aesthetic reads as generic, so get three things from the user first (ask if any are missing):

- **Feel / register.** One sentence: technical, editorial, corporate, minimalist, playful, academic.
- **Color palette.** Explicit hex values or a description concrete enough to translate ("dark, warm, one amber accent"). One dominant color at 60–70% visual weight, one or two supporting tones, one sharp accent.
- **Typography direction.** Serif or sans, display or utilitarian. If the user has no opinion, pick one pairing and commit.

Also check the source material for anything that is a number series, a comparison grid, a process, or a photo. Each of those maps to a specific bento feature (see "Map material to features").

## Workflow

1. **Draft in markdown first.** One section per slide. Annotate structure and emphasis inline (`[cover]`, `[3-col]`, `[dark]`, `[chart: revenue by year]`, `[table]`, `[morph from prev]`, `**key phrase**`). No JSON yet.
2. **Review the markdown as a deck.** Spot commonalities: five "title + three columns" slides share a layout; two "big quote + attribution" slides do too. Note which slides deserve a contrasting background, and keep that list short. Note where consecutive slides show the same thing changing: those are morph candidates.
3. **Set up the folder.**
   ```bash
   mkdir my-deck && cd my-deck
   node ${CLAUDE_SKILL_DIR}/scripts/bento.mjs fetch "My Deck.bento.html"
   cp ${CLAUDE_SKILL_DIR}/template/build.mjs .
   node ${CLAUDE_SKILL_DIR}/scripts/bento.mjs fonts "Instrument Serif:400,400i" "IBM Plex Sans:400,600" > fonts.json   # only if not using system stacks
   ```
4. **Write the generator, not the JSON.** A fresh document omits `docId` and `collab`; the app mints both on first open. Edit `build.mjs`: define the palette, the type presets and the layout helpers first (the chassis), then instantiate each slide against them. Hand-writing element JSON for a dozen slides means a thousand lines of repeated fields and drifting styles; a generator keeps every `h2` identical and every id deterministic. For a two-slide edit to an existing deck, editing the extracted JSON directly is fine.
5. **Build, splice, check.**
   ```bash
   node build.mjs > doc.json
   node ${CLAUDE_SKILL_DIR}/scripts/bento.mjs splice "My Deck.bento.html" doc.json
   node ${CLAUDE_SKILL_DIR}/scripts/bento.mjs check "My Deck.bento.html" --shots shots/
   ```
   `splice` lints offline (required fields, ids, links, asset refs, margins). `check` runs the real `window.bento.validate()` (text overflow, unknown keys, unrenderable chart options, fonts not embedded) and writes one PNG per slide. Look at every screenshot. Overflowing text, a title that wrapped to three lines, two elements crowding each other: none of it shows in JSON, all of it shows on screen. Fix and repeat until the deck is clean.
6. **Hand over.** The user opens the file in a browser (`xdg-open`, `open`, `start`): it boots into the editor with the deck loaded. `#present` on the URL starts the show. PDF export and speaker view are in the app. For an audience copy that opens straight into the show with no editor, make a player file: `bento.mjs player deck.bento.html handout.bento.html` sets `readonly: true` and strips any collab keys. `template: true` is the other file mode: every open mints a fresh deck, for a distributable starter rather than a personal deck.

## Editing an existing deck

```bash
node ${CLAUDE_SKILL_DIR}/scripts/bento.mjs extract deck.bento.html > doc.json
# edit doc.json (or regenerate it), then
node ${CLAUDE_SKILL_DIR}/scripts/bento.mjs splice deck.bento.html doc.json
```

Without a shell (a chat session), the round trip goes through the app: the user copies the JSON out with Save, Copy document JSON, you return a full replacement document, and they paste it back with Save, Replace from JSON (undoable). In the browser console `window.bento.doc` reads and `window.bento.loadDoc(json)` writes.

- **Look at `collab` before reading further.** If the document has a `collab` key with `ownerPriv`, `writerPriv` or `invite`, the file contains live-session credentials, and anyone who gets the file or its JSON can join and write. Tell the user before continuing; they may not know the deck is shared. A read-only copy (Save menu, Save read-only copy) has no keys in it. `extract` prints a warning when it sees them.
- **Never regenerate `docId`.** It is the document's identity. Fresh decks omit it and the app mints one.
- Read `doc.size` and `doc.theme` and reuse existing element ids where the content is the same, so edits morph instead of popping.

## Canvas and type scale

Canonical canvas is 1280×720 with 96px side margins, so the content band is x 96–1184 (1088 wide). The arithmetic is done:

| Split | Width | x positions | Gutter |
|---|---|---|---|
| 2 columns | 528 | 96, 656 | 32 |
| 3 columns | 340 | 96, 470, 844 | 34 |
| 4 columns | 254 | 96, 374, 652, 930 | 24 |
| 60 / 40 | 624 / 432 | 96, 752 | 32 |

Title band `y:72 h:84`, content from `y:208`, bottom margin 96 leaves 416px of content height.

Safe type scale at 1280×720: 18–22px body, 40–56px section titles, 76–140px display and cover. Positions are absolute pixels; the height of a text box is not knowable from the JSON, so size generously and let `check` report overflow, or call `window.bento.measure({html, w, fontSize, lineHeight})` in the open deck's console for the exact height.

## Map material to features

The format's value is that content types have dedicated elements. Bullets on every slide waste it.

| Material | Use |
|---|---|
| Numbers to compare (trend, magnitude, share) | `chart` element: bar, line, pie, scatter. Bar and line series data are plain numbers; color by series; template formatters only. |
| Comparison, spec, pricing, feature grid | `table` element with column weights and one `style` object. Not for trends. |
| Consecutive slides where the same thing changes | Morph: same element `id` (or `morphId`) on both slides, `transition: "morph"` on the later one. Position, size and color tween. |
| A detail to drill into on request | State slide: `stateOf: "<parent-id>"` plus an element `link`. Arrow keys skip it; ← returns to the parent. |
| Appendix or backup material | `hidden: true`. Skipped in the show and PDF, reachable by `link`. |
| A headline number | Big text plus `fx: { countUp: true }`. |
| Full-bleed photo | Image at 0,0,1280,720 with `fit: "cover"`, a scrim rect, text on top. Optional slow ken-burns. |
| Sequence, flow, timeline | Line or `path` shapes, connectors with `from`/`to`, or morph a highlight through the steps. |
| Code | `code` element (content, fontSize, fontFamily, color). |
| Slide numbers, title, date, author | Tokens in text: `{{page}}`, `{{pages}}`, `{{title}}`, `{{author}}` from `doc.meta`. Never type these facts by hand. `{{date}}` is the day the file is opened, so type a meeting date literally. |

Motion is signal, like color. Morph where the same thing carries across slides, one ambient moment on the cover, count-up on the one number that matters. When everything moves, none of it reads as emphasis.

## Consistency discipline

- **Presets, not per-element styling.** Every title, body block, eyebrow, stat and footnote comes from one helper in the generator. If two elements share a purpose they share a helper; if you have typed the same `fontSize`/`color`/`lineHeight` twice by hand, extract it.
- **Same shape, same layout helper.** Four three-column slides use one `threeCol()` call each, not four hand-laid grids. Differences live in the content.
- **Stable ids for chrome.** Deck title, section label, page number: give them the same id on every slide so they morph in place instead of blinking. Slide ids `s01`, `s02`, ... and element ids `s03-title`, `s03-body` for slide-local content; `chrome-page`, `chrome-title` for the shared furniture.
- **Variation is signal, not decoration.** A light background in a mostly-dark deck means "this slide is different and important" (section divider, key stat, call to action). If every slide has a unique background, none of them do.
- **Minimize repeated chrome.** Deck title, section name, page number: pick one, or omit. Cramming brand + section + page + date onto every slide is clutter.
- **Speaker notes on every slide.** `notes` is a required field and doubles as the talk track. Write the beat the slide lands, not a description of the slide.
- **Set `role`** (`title`, `subtitle`, `body`, `kicker`) on text elements so the editor's layouts can restyle the deck later without retyping.

## Design guardrails

Universal rules that apply to any deck, regardless of feel:

- **Colors that fit this topic.** A palette that would also work for a dentist and a crypto pitch is not chosen specifically enough. Don't default to blue.
- **One dominant color, one accent.** Never give three or more colors equal weight. `theme.accent` seeds the chart palette, so choose it with the charts in mind.
- **Left-align body text.** Center only titles and cover slides.
- **Every slide needs a visual anchor.** A stat, a chart, a framed quote, a pulled phrase, a shape carrying the accent. Text-only slides are forgettable.
- **Strong size contrast on titles.** 48px+ titles over 18–22px body. When they're close in size, the hierarchy collapses.
- **Never an accent line under a title.** It's a hallmark of generated slide filler. Use whitespace or a background shift instead.
- **Commit to one motif.** A repeated element (rule color, shape, chrome pattern) on every slide, not scattered.
- **Breathing room.** Keep the 96px margins. Don't fill every pixel.
- **Contrast.** Shapes and text must read against the slide background they sit on, including scrims over photos.

## Assets

- **Fonts are embedded in the file or fall back silently.** A `fontFamily` naming a face the document doesn't embed falls back to the next entry in the stack, with no warning, and it looks right on your machine because you have the font. Either embed (`bento.mjs fonts` produces `assets` + `fonts` entries; the template merges `fonts.json`) or name a system stack and mean it. Always write a full stack: `"'Fraunces', Georgia, serif"`. Two families max, three with a mono for code.
- **Images** as data URIs in `doc.assets`, referenced `"asset:<key>"`. The file must stay self-contained. Keep photos under a few hundred KB each (resize before embedding).
- **Icons: FontAwesome, inlined as SVG.** Paste the icon's raw SVG into a `svg` element's `markup`, or put recurring icons in `doc.assets` and reference them with `asset`. Set `fill` explicitly in the markup. One FontAwesome variant per deck (solid, regular, light); mixing weights reads as sloppy. Size the element to the local type scale.
- **Glyph coverage.** Google Fonts latin subsets omit arrows and many symbols, so "→" in an embedded face falls back to a system font mid-line. Write the word, or draw the arrow as a `line` shape with `lineEnd: "arrow"`.
- **Video and audio** as `media` elements. Embed only short clips as data URIs; link big files by URL with a poster. Autoplay runs only in present mode and needs `muted: true`.

## Checks before handing over

- [ ] Every screenshot from `check` looked at, no overflow or crowding, `validate()` clean above `info`.
- [ ] Numbers that should be a chart are a chart; grids that should be a table are a table.
- [ ] Consecutive slides about one subject share ids and `transition: "morph"`.
- [ ] One accent, two typefaces, 96px margins, right-most x ≤ 1184.
- [ ] Fonts embedded or a system stack named on purpose.
- [ ] Speaker notes on every slide.
- [ ] No `collab` keys in a file that is about to be sent around.
