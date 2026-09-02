#!/usr/bin/env node
// CLI for .bento.html decks: fetch the app, extract/splice the document JSON,
// embed Google Fonts, and check a deck in headless Chromium (validate + shots).
// No dependencies beyond Node 20+ and, for `check`, a Chromium binary.
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { homedir } from 'node:os'
import { resolve, join } from 'node:path'
import { pathToFileURL } from 'node:url'

const RELEASE_URL = 'https://bento.page/releases/slides/Bento_Slides.bento.html'
const BLOCK = /(<script type="application\/bento\+json" id="bento-doc">)([\s\S]*?)(<\/script>)/

const usage = `usage:
  bento.mjs fetch <out.bento.html>               download the latest Bento Slides app
  bento.mjs extract <deck.bento.html>            print the document JSON (stdout)
  bento.mjs splice <deck.bento.html> <doc.json>  lint doc.json and write it into the deck
  bento.mjs lint <doc.json>                      offline lint only
  bento.mjs player <deck.bento.html> <out.bento.html>
                                                 write a read-only player copy (boots into the show, collab keys stripped)
  bento.mjs fonts "Family:400,600,400i" [...]    print {assets, fonts} with embedded Google Fonts woff2
  bento.mjs check <deck.bento.html> [--shots dir] [--chrome path]
                                                 run window.bento.validate() and screenshot every slide`

const [cmd, ...args] = process.argv.slice(2)
const die = (msg) => { console.error(msg); process.exit(1) }

// ---------- document block ----------
function readBlock(file) {
  const html = readFileSync(file, 'utf8')
  const m = html.match(BLOCK)
  if (!m) die(`${file}: no #bento-doc block found (is this a .bento.html?)`)
  if (html.match(new RegExp(BLOCK.source, 'g')).length !== 1) die(`${file}: more than one #bento-doc block`)
  return { html, json: m[2].trim() }
}

function escapeForBlock(json) {
  return json.replace(/</g, '\\u003c')
}

function warnCollab(doc) {
  const c = doc.collab
  if (c && (c.ownerPriv || c.writerPriv || c.invite || c.key)) {
    console.error('WARNING: this deck carries live-collaboration keys (doc.collab). Anyone holding the file or its JSON can join the session. Tell the user before sharing it further; a read-only copy carries no keys.')
  }
}

// ---------- offline lint ----------
const BASE_FIELDS = ['id', 'type', 'x', 'y', 'w', 'h', 'rotation', 'opacity']
const TYPE_FIELDS = {
  text: ['html', 'fontSize', 'fontFamily', 'fontWeight', 'color', 'align', 'valign', 'lineHeight'],
  code: ['content', 'fontSize', 'fontFamily', 'color', 'align', 'valign', 'lineHeight'],
  shape: ['shape', 'fill', 'stroke', 'strokeWidth', 'radius'],
  image: ['src', 'fit'],
  svg: [],
  chart: ['option'],
  table: ['columns', 'rows', 'header', 'style'],
  media: ['kind', 'src'],
}

function lint(doc) {
  const out = []
  const err = (m) => out.push({ severity: 'error', message: m })
  const warn = (m) => out.push({ severity: 'warn', message: m })
  const info = (m) => out.push({ severity: 'info', message: m })

  if (doc.format !== 'bento/slides') err(`format must be "bento/slides" (got ${JSON.stringify(doc.format)})`)
  if (doc.version !== 1) warn(`version is ${doc.version}; this tool knows format version 1`)
  if (!doc.title) err('title is required')
  if (!doc.size?.width || !doc.size?.height) err('size {width, height} is required')
  for (const k of ['background', 'color', 'accent', 'fontFamily']) if (!doc.theme?.[k]) err(`theme.${k} is required`)
  if (!Array.isArray(doc.slides) || !doc.slides.length) { err('slides must be a non-empty array'); return out }
  if (!doc.modified) info('modified (ISO timestamp) missing; the app sets it on save')

  const W = doc.size?.width ?? 1280, H = doc.size?.height ?? 720
  const slideIds = new Set()
  const assets = doc.assets ?? {}
  const fontFamilies = new Set((doc.fonts ?? []).map((f) => f.family.toLowerCase()))
  const missingFonts = new Set()
  const TRANSITIONS = ['none', 'fade', 'slide', 'zoom', 'morph']
  let prevKeys = new Set()

  doc.slides.forEach((s, i) => {
    const tag = `slide ${i + 1} (${s.id ?? '?'})`
    if (!s.id) err(`${tag}: missing id`)
    else if (slideIds.has(s.id)) err(`${tag}: duplicate slide id`)
    slideIds.add(s.id)
    if (!s.background) err(`${tag}: missing background`)
    if (!TRANSITIONS.includes(s.transition)) err(`${tag}: transition must be one of ${TRANSITIONS.join('|')}`)
    if (typeof s.notes !== 'string') warn(`${tag}: no speaker notes`)
    else if (!s.notes.trim()) warn(`${tag}: speaker notes are empty`)
    if (!Array.isArray(s.elements)) { err(`${tag}: elements must be an array`); return }
    if (!s.elements.length) warn(`${tag}: empty slide`)

    const keys = new Set()
    const ids = new Set()
    for (const el of s.elements) {
      const etag = `${tag} › ${el.type ?? '?'} ${el.id ?? '?'}`
      for (const f of BASE_FIELDS) if (el[f] === undefined) err(`${etag}: missing ${f}`)
      if (ids.has(el.id)) err(`${etag}: duplicate element id within slide`)
      ids.add(el.id)
      const key = el.morphId || el.id
      if (keys.has(key)) err(`${etag}: morph key "${key}" used twice on one slide`)
      keys.add(key)
      const need = TYPE_FIELDS[el.type]
      if (!need) err(`${etag}: unknown element type`)
      else for (const f of need) if (el[f] === undefined) err(`${etag}: missing ${f}`)
      if (typeof el.x === 'number' && typeof el.w === 'number') {
        if (el.x + el.w > W || el.x < 0) info(`${etag}: bleeds off the canvas horizontally`)
        else if (el.type !== 'image' && el.type !== 'shape' && (el.x < 96 || el.x + el.w > W - 96)) info(`${etag}: outside the 96px side margins (x ${el.x}–${el.x + el.w})`)
      }
      if (typeof el.y === 'number' && typeof el.h === 'number' && (el.y + el.h > H || el.y < 0)) info(`${etag}: bleeds off the canvas vertically`)
      if (el.link && !doc.slides.some((t) => t.id === el.link)) err(`${etag}: link → "${el.link}" is not a slide id`)
      for (const ref of [el.src, el.poster, el.asset]) {
        if (typeof ref === 'string' && ref.startsWith('asset:') && !(ref.slice(6) in assets)) err(`${etag}: ${ref} not in doc.assets`)
      }
      if (typeof el.src === 'string' && /^https?:/.test(el.src)) info(`${etag}: external src; the deck is no longer self-contained`)
      if (el.type === 'text' || el.type === 'code') {
        const fam = (el.fontFamily ?? '').split(',')[0].trim().replace(/^['"]|['"]$/g, '')
        if (fam && !fontFamilies.has(fam.toLowerCase()) && !/^(system-ui|sans-serif|serif|monospace|ui-|-apple|segoe|helvetica|arial|georgia|times|courier|menlo|consolas|inter$)/i.test(fam)) missingFonts.add(fam)
        if (!(el.fontFamily ?? '').includes(',')) warn(`${etag}: fontFamily has no fallback stack`)
      }
      if (el.type === 'chart') {
        for (const ser of el.option?.series ?? []) {
          if ((ser.type === 'bar' || ser.type === 'line') && (ser.data ?? []).some((d) => typeof d !== 'number')) err(`${etag}: ${ser.type} series data must be plain numbers`)
          if (ser.label) info(`${etag}: series.label is ignored on bar/line charts`)
        }
        if (JSON.stringify(el.option).includes('"formatter":"function')) err(`${etag}: formatter functions do not serialize; use {b}/{c}/{d} templates`)
      }
      if (el.fx?.loop?.type === 'dash-march' && !['dashed', 'dotted'].includes(el.strokeStyle)) warn(`${etag}: dash-march needs strokeStyle dashed|dotted`)
      if (el.fx?.loop?.type === 'motion-path' && el.fx?.enter) warn(`${etag}: motion-path loop and an entrance tween fight over the same transform`)
    }
    if (s.transition === 'morph' && i > 0 && ![...keys].some((k) => prevKeys.has(k))) warn(`${tag}: transition is morph but shares no element id with the previous slide (nothing will morph)`)
    if (s.stateOf && !doc.slides.some((t) => t.id === s.stateOf)) err(`${tag}: stateOf → "${s.stateOf}" is not a slide id`)
    prevKeys = keys
  })
  for (const f of missingFonts) warn(`font "${f}" is used but not embedded in doc.fonts; it will fall back on other machines`)
  return out
}

function printFindings(findings, label) {
  const counts = { error: 0, warn: 0, info: 0 }
  for (const f of findings) {
    counts[f.severity] = (counts[f.severity] ?? 0) + 1
    console.error(`${f.severity.padEnd(5)} ${f.message}`)
  }
  console.error(`${label}: ${counts.error} errors, ${counts.warn} warnings, ${counts.info} info`)
  return counts.error === 0
}

// ---------- fonts ----------
async function embedFonts(specs) {
  const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
  const assets = {}, fonts = []
  for (const spec of specs) {
    const [family, list = '400'] = spec.split(':')
    const variants = list.split(',').map((v) => v.trim()).map((v) => ({ weight: parseInt(v, 10) || 400, italic: /i$/.test(v) }))
    const hasItalic = variants.some((v) => v.italic)
    const axis = hasItalic
      ? 'ital,wght@' + variants.map((v) => `${v.italic ? 1 : 0},${v.weight}`).sort().join(';')
      : 'wght@' + [...new Set(variants.map((v) => v.weight))].sort((a, b) => a - b).join(';')
    const url = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family).replace(/%20/g, '+')}:${axis}&display=swap`
    const css = await (await fetch(url, { headers: { 'User-Agent': UA } })).text()
    // Blocks are "/* subset */ @font-face { ... }"; keep latin only.
    const blocks = css.split('@font-face').slice(1)
    let got = 0
    for (let i = 0; i < blocks.length; i++) {
      const prev = i === 0 ? css.split('@font-face')[0] : blocks[i - 1]
      const subset = (prev.match(/\/\*\s*([\w-]+)\s*\*\/\s*$/) ?? [])[1]
      if (subset && subset !== 'latin') continue
      const b = blocks[i]
      const weight = parseInt((b.match(/font-weight:\s*(\d+)/) ?? [])[1] ?? '400', 10)
      const style = (b.match(/font-style:\s*(\w+)/) ?? [])[1] ?? 'normal'
      const src = (b.match(/url\((https:[^)]+\.woff2)\)/) ?? [])[1]
      if (!src) continue
      const buf = Buffer.from(await (await fetch(src)).arrayBuffer())
      const key = `font-${family.toLowerCase().replace(/\s+/g, '-')}-${weight}${style === 'italic' ? 'i' : ''}`
      assets[key] = `data:font/woff2;base64,${buf.toString('base64')}`
      fonts.push({ family, asset: key, weight, style })
      got++
    }
    if (!got) die(`no latin woff2 found for "${family}" (check the family name and weights)`)
    console.error(`${family}: embedded ${got} face(s)`)
  }
  return { assets, fonts }
}

// ---------- check (CDP against a Chromium binary) ----------
function isSnapShim(path) {
  try { const head = readFileSync(path, { encoding: 'utf8', flag: 'r' }).slice(0, 400); return head.startsWith('#!') && head.includes('/snap/') } catch { return false }
}

// Snap-confined Chromium cannot read files outside $HOME (ERR_FILE_NOT_FOUND), so
// real binaries and Playwright's cached Chromium rank ahead of snap shims.
function findChrome(explicit) {
  const wanted = explicit ?? process.env.BENTO_CHROME
  if (wanted) { if (existsSync(wanted)) return wanted; die(`chrome not found at ${wanted}`) }
  const candidates = [
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium',
    'C:/Program Files/Google/Chrome/Application/chrome.exe']
  const pw = join(homedir(), '.cache', 'ms-playwright')
  if (existsSync(pw)) for (const d of readdirSync(pw).filter((n) => /^chromium-\d+$/.test(n)).sort().reverse()) {
    for (const rel of ['chrome-linux64/chrome', 'chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-win/chrome.exe']) candidates.push(join(pw, d, rel))
  }
  const found = candidates.filter((c) => existsSync(c))
  const real = found.filter((c) => !isSnapShim(c) && !c.startsWith('/snap/'))
  const pick = real[0] ?? found[0] ?? (existsSync('/snap/bin/chromium') ? '/snap/bin/chromium' : null)
  if (pick && !real.length) console.error(`warning: only a snap Chromium was found (${pick}); it cannot read files outside your home directory`)
  return pick
}

const CHROME_FLAGS = ['--headless=new', '--remote-debugging-port=0', '--no-first-run', '--no-default-browser-check', '--allow-file-access-from-files', '--hide-scrollbars', '--disable-gpu', '--disable-dev-shm-usage', '--window-size=1280,720', '--force-device-scale-factor=1', 'about:blank']

function launch(chrome, extra = []) {
  const proc = spawn(chrome, [...extra, ...CHROME_FLAGS], { stdio: ['ignore', 'ignore', 'pipe'] })
  const wsUrl = new Promise((res, rej) => {
    let buf = ''
    proc.stderr.on('data', (d) => { buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/); if (m) res(m[1]) })
    proc.on('exit', (c) => rej(Object.assign(new Error(`chromium exited (${c}) before DevTools came up:\n${buf.split('\n').slice(0, 3).join('\n')}`), { log: buf })))
    setTimeout(() => rej(new Error('timed out waiting for DevTools')), 15000)
  })
  return { proc, wsUrl }
}

async function cdp(chrome, file, fn) {
  let { proc, wsUrl: wsPromise } = launch(chrome)
  let wsUrl
  try {
    wsUrl = await wsPromise
  } catch (e) {
    if (!/No usable sandbox/.test(e.log ?? '')) throw e
    // Distros that disable unprivileged user namespaces (Ubuntu 23.10+) refuse
    // to start Chromium's sandbox. We only ever load a local file we wrote.
    console.error('chromium: no usable sandbox on this system, retrying with --no-sandbox')
    ;({ proc, wsUrl: wsPromise } = launch(chrome, ['--no-sandbox']))
    wsUrl = await wsPromise
  }
  const list = await (await fetch(wsUrl.replace(/^ws/, 'http').replace(/\/devtools\/browser\/.*/, '/json'))).json()
  const page = list.find((t) => t.type === 'page')
  const ws = new WebSocket(page.webSocketDebuggerUrl)
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
  let seq = 0
  const pending = new Map()
  ws.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result) } }
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })) })
  const evaluate = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? JSON.stringify(r.exceptionDetails))
    return r.result.value
  }
  try {
    await send('Page.enable'); await send('Runtime.enable')
    await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false })
    // Offline on purpose: a deck must render with nothing but the file, and the
    // app skips its update check so no toast lands in the screenshots.
    await send('Network.enable')
    await send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 })
    return await fn({ send, evaluate, file })
  } finally {
    ws.close(); proc.kill()
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function check(file, shotsDir, chromePath) {
  const chrome = findChrome(chromePath)
  if (!chrome) die('no Chromium found. Install chromium/google-chrome, or pass --chrome <path>, or set BENTO_CHROME.')
  const { json } = readBlock(file)
  if (!json) die(`${file}: the #bento-doc block is empty; splice a document first`)
  const doc = JSON.parse(json)
  const shown = doc.slides.filter((s) => !s.stateOf && !s.hidden)
  const url = pathToFileURL(resolve(file)).href + '#present'
  return cdp(chrome, file, async ({ send, evaluate }) => {
    await send('Page.navigate', { url })
    for (let i = 0; i < 100; i++) { if (await evaluate('typeof window.bento !== "undefined" && typeof window.bento.validate === "function"')) break; await sleep(200) }
    if (!(await evaluate('typeof window.bento?.validate === "function"'))) {
      const state = await evaluate('JSON.stringify({ href: location.href, title: document.title, ready: document.readyState, bento: typeof window.bento, body: (document.body?.innerText ?? "").slice(0, 300) })')
      die(`the deck never exposed window.bento.validate (using ${chrome}). Page state: ${state}\nIf this is a snap Chromium it cannot read files outside your home directory; pass --chrome or set BENTO_CHROME.`)
    }
    await sleep(2500) // splash + first entrance
    const v = await evaluate('JSON.stringify(window.bento.validate())')
    let { findings } = JSON.parse(v)
    // The app mints dormant collab keys in memory on boot; if the file on disk
    // has no collab block there is nothing to leak, so the finding is noise here.
    if (!doc.collab) findings = findings.filter((f) => f.code !== 'collab-secrets-present')
    const loud = findings.filter((f) => f.severity !== 'info')
    for (const f of findings) console.error(`${f.severity.padEnd(5)} ${f.code}${f.slide != null ? ` [slide ${f.slide}${f.element ? ' › ' + f.element : ''}]` : ''}: ${f.message}`)
    console.error(`validate(): ${findings.length} finding(s), ${loud.length} above info`)
    if (shotsDir) {
      mkdirSync(shotsDir, { recursive: true })
      for (let i = 0; i < shown.length; i++) {
        if (i > 0) {
          await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39 })
          await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39 })
          await sleep(1600) // let morphs and entrances settle
        }
        const shot = await send('Page.captureScreenshot', { format: 'png' })
        const name = `${String(i + 1).padStart(2, '0')}-${shown[i].id}.png`
        writeFileSync(join(shotsDir, name), Buffer.from(shot.data, 'base64'))
        console.error(`shot ${name}`)
      }
      console.error(`${shown.length} slide(s) → ${shotsDir} (state and hidden slides are not captured)`)
    }
    return loud.filter((f) => f.severity === 'error').length === 0
  })
}

// ---------- main ----------
;(async () => {
  switch (cmd) {
    case 'fetch': {
      const out = args[0] ?? die(usage)
      const res = await fetch(RELEASE_URL)
      if (!res.ok) die(`download failed: ${res.status}`)
      const html = await res.text()
      if (!BLOCK.test(html)) die('downloaded file has no #bento-doc block; the release format may have changed')
      writeFileSync(out, html)
      console.error(`wrote ${out} (${(html.length / 1024).toFixed(0)} KB). The document block is empty; splice your doc into it.`)
      break
    }
    case 'extract': {
      const { json } = readBlock(args[0] ?? die(usage))
      if (!json) die('the #bento-doc block is empty (fresh download); nothing to extract')
      const doc = JSON.parse(json)
      warnCollab(doc)
      process.stdout.write(JSON.stringify(doc, null, 2) + '\n')
      break
    }
    case 'lint': {
      const doc = JSON.parse(readFileSync(args[0] ?? die(usage), 'utf8'))
      process.exit(printFindings(lint(doc), 'lint') ? 0 : 1)
    }
    case 'splice': {
      const [file, docFile] = args
      if (!file || !docFile) die(usage)
      const doc = JSON.parse(readFileSync(docFile, 'utf8'))
      if (!printFindings(lint(doc), 'lint')) die('fix the errors above, then splice again')
      const { html, json } = readBlock(file)
      if (json) {
        const old = JSON.parse(json)
        if (old.docId && doc.docId && old.docId !== doc.docId) die(`docId changed (${old.docId} → ${doc.docId}); never regenerate a document's identity`)
        if (old.docId && !doc.docId) doc.docId = old.docId
      }
      if (!doc.modified) doc.modified = new Date().toISOString()
      const next = html.replace(BLOCK, (_, a, __, c) => a + escapeForBlock(JSON.stringify(doc)) + c)
      writeFileSync(file, next)
      console.error(`spliced ${docFile} into ${file} (${doc.slides.length} slides)`)
      break
    }
    case 'player': {
      const [file, out] = args
      if (!file || !out) die(usage)
      const { html, json } = readBlock(file)
      if (!json) die('the #bento-doc block is empty; splice a document first')
      const doc = JSON.parse(json)
      delete doc.collab
      doc.readonly = true
      writeFileSync(out, html.replace(BLOCK, (_, a, __, c) => a + escapeForBlock(JSON.stringify(doc)) + c))
      console.error(`wrote ${out}: readonly player, collab stripped`)
      break
    }
    case 'fonts': {
      if (!args.length) die(usage)
      process.stdout.write(JSON.stringify(await embedFonts(args), null, 2) + '\n')
      break
    }
    case 'check': {
      const file = args[0] ?? die(usage)
      const shots = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null
      const chrome = args.includes('--chrome') ? args[args.indexOf('--chrome') + 1] : null
      process.exit((await check(file, shots, chrome)) ? 0 : 1)
    }
    default:
      die(usage)
  }
})().catch((e) => die(e.stack ?? String(e)))
