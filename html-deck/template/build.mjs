#!/usr/bin/env node
// Deck generator starter. Edit the CHASSIS (palette, type presets, layout
// helpers) first, then the SLIDES. Emits the bento/slides document to stdout:
//   node build.mjs > doc.json && node <skill>/scripts/bento.mjs splice deck.bento.html doc.json
// Styling lives in the presets so every title, body and eyebrow renders the
// same; ids are deterministic so chrome morphs in place across slides.
import { readFileSync, existsSync } from 'node:fs'

// ---------- CHASSIS ----------
const W = 1280, H = 720, M = 96            // canvas + side margin
const BAND = W - 2 * M                      // 1088 content width
const RIGHT = W - M                         // 1184

const palette = {
  bg: '#141310',       // dominant, 60–70% of every slide
  ink: '#F2EFE6',
  muted: '#A8A399',
  accent: '#E8442E',   // one sharp accent
  paper: '#F2EFE6',    // the contrasting background, used on few slides
  paperInk: '#141310',
}

// Full stacks always. Embed the faces with `bento.mjs fonts` (fonts.json) or
// name a system stack on purpose; a missing face falls back silently.
const fontsJson = existsSync('fonts.json') ? JSON.parse(readFileSync('fonts.json', 'utf8')) : { assets: {}, fonts: [] }
const DISPLAY = "'Instrument Serif', Georgia, serif"
const BODY = "'IBM Plex Sans', system-ui, sans-serif"

const base = (id, x, y, w, h) => ({ id, x, y, w, h, rotation: 0, opacity: 1 })
const text = (id, frame, html, t) => ({
  ...base(id, ...frame), type: 'text', html,
  fontSize: t.size, fontFamily: t.font, fontWeight: t.weight, color: t.color,
  align: t.align ?? 'left', valign: t.valign ?? 'top', lineHeight: t.lh, letterSpacing: t.ls ?? 0,
  ...(t.role ? { role: t.role } : {}), ...(t.fx ? { fx: t.fx } : {}),
})
const rect = (id, frame, fill, extra = {}) => ({ ...base(id, ...frame), type: 'shape', shape: 'rect', fill, stroke: 'none', strokeWidth: 0, radius: 0, ...extra })

// Type presets at 1280x720. Same purpose, same preset.
const T = {
  display: { size: 120, font: DISPLAY, weight: 400, color: palette.ink, lh: 0.95, ls: -2, role: 'title' },
  h1: { size: 52, font: DISPLAY, weight: 400, color: palette.ink, lh: 1.05, ls: -1, role: 'title' },
  eyebrow: { size: 15, font: BODY, weight: 600, color: palette.accent, lh: 1.2, ls: 2, role: 'kicker' },
  body: { size: 20, font: BODY, weight: 400, color: palette.ink, lh: 1.4, role: 'body' },
  muted: { size: 18, font: BODY, weight: 400, color: palette.muted, lh: 1.4, role: 'body' },
  stat: { size: 96, font: DISPLAY, weight: 400, color: palette.ink, lh: 1, ls: -3 },
  chrome: { size: 13, font: BODY, weight: 500, color: palette.muted, lh: 1.2, ls: 1 },
}

// Column arithmetic for the 1088px band, gutters included.
const cols = (n) => {
  const gutter = { 2: 32, 3: 34, 4: 24 }[n]
  const w = Math.floor((BAND - gutter * (n - 1)) / n)
  return Array.from({ length: n }, (_, i) => [M + i * (w + gutter), w])
}

// Shared furniture: same ids on every slide so it morphs in place. Keep it
// to one fact ({{page}}); the deck title on every slide is clutter.
const chrome = (dark = true) => [
  text('chrome-page', [RIGHT - 240, H - 60, 240, 20], '{{page}} / {{pages}}', { ...T.chrome, align: 'right', color: dark ? palette.muted : palette.paperInk }),
]

// Layouts. Add one per recurring slide shape found in the markdown draft.
const slide = (id, { bg = palette.bg, transition = 'morph', notes, elements, ...rest }) => ({
  id, background: bg, transition, notes, elements, ...rest,
})

const titled = (id, eyebrow, title, elements, notes, opts = {}) => slide(id, {
  ...opts, notes,
  elements: [
    text(`${id}-eyebrow`, [M, 72, BAND, 24], eyebrow, T.eyebrow),
    text(`${id}-title`, [M, 104, BAND, 84], title, T.h1),
    ...elements,
    ...chrome(),
  ],
})

const threeCol = (id, eyebrow, title, items, notes) => titled(id, eyebrow, title,
  cols(3).flatMap(([x, w], i) => [
    rect(`${id}-mark-${i}`, [x, 216, 28, 4], palette.accent),
    text(`${id}-head-${i}`, [x, 240, w, 32], items[i].head, { ...T.body, weight: 600 }),
    text(`${id}-copy-${i}`, [x, 280, w, 200], items[i].copy, T.muted),
  ]), notes)

// ---------- SLIDES ----------
const slides = [
  slide('s01', {
    transition: 'none',
    notes: 'Open with the frame: one sentence on why this matters now.',
    elements: [
      text('s01-eyebrow', [M, 210, BAND, 24], 'WORKING TITLE', T.eyebrow),
      text('s01-title', [M, 250, 900, 260], 'A deck that fits<br>in a file.', T.display),
      text('s01-sub', [M, 540, 560, 60], 'Subtitle or one-line thesis. {{date}}', T.muted),
      ...chrome(),
    ],
  }),
  threeCol('s02', 'THE SHAPE', 'Three things to say', [
    { head: 'First', copy: 'One or two sentences. Left-aligned, generous line height, no more than a paragraph per column.' },
    { head: 'Second', copy: 'Differences between columns live in the content, not the structure.' },
    { head: 'Third', copy: 'If a column needs more than a paragraph, split the slide in two.' },
  ], 'Land the three beats in order; the third one is the setup for the next slide.'),
  slide('s03', {
    bg: palette.paper,   // the contrasting background, used sparingly
    notes: 'The one number. Pause on it.',
    elements: [
      text('s03-eyebrow', [M, 72, BAND, 24], 'THE NUMBER', { ...T.eyebrow }),
      text('s03-stat', [M, 240, BAND, 110], '3.7×', { ...T.stat, color: palette.paperInk, fx: { countUp: true } }),
      text('s03-copy', [M, 370, 620, 90], 'What the number means in one sentence, in plain words the audience already uses.', { ...T.body, color: palette.paperInk }),
      ...chrome(false),
    ],
  }),
]

// ---------- DOCUMENT ----------
const doc = {
  format: 'bento/slides', version: 1,
  title: 'Working title',
  meta: { author: '', company: '', subject: '', event: '' },
  size: { width: W, height: H },
  theme: { background: palette.bg, color: palette.ink, accent: palette.accent, fontFamily: BODY },
  present: { slideNumber: false, controls: false, progress: false },
  assets: { ...fontsJson.assets },
  fonts: fontsJson.fonts,
  slides,
  modified: new Date().toISOString(),
}

process.stdout.write(JSON.stringify(doc, null, 2) + '\n')
