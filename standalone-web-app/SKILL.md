---
name: standalone-web-app
description: Build and ship a local-first standalone web app: monorepo, stack picks, component discipline, theming, analytics, CI, deploy. Use to bootstrap a new data-centric tool that runs entirely in the browser.
---

# Standalone web app

Playbook for building a local-first browser app that uses local data (YAML, JSON, TOML, Markdown, CSV), computes and renders something from it, and deploys as a static bundle. The app never talks to a backend; all parsing, math, and persistence happen in the browser.

## Reference files shipped with this skill

Load on demand when you reach the matching step.

- `${CLAUDE_SKILL_DIR}/references/tooling.md` — detailed stack picks, Prettier/ESLint/Stylelint, Lefthook, Makefile, root scripts.
- `${CLAUDE_SKILL_DIR}/references/ci.md` — GitLab CI and GitHub Actions skeletons, split between web and desktop.
- `${CLAUDE_SKILL_DIR}/references/deploy.md` — Cloudflare Pages, Cloudflare Workers, analytics, privacy files.
- `${CLAUDE_SKILL_DIR}/references/desktop-tauri.md` — Tauri wrapper for desktop builds.

## When to use this skill

- Tool reads user-owned data, computes something, shows a dashboard.
- No accounts, sync service, or per-user database.
- Deployable as a single static bundle to any CDN.
- You want the same core to serve future targets (Tauri desktop, Nextcloud, Obsidian plugin).

## Complexity budget

Spend complexity only where it shows up in the product:

1. **Style guide / design tokens.** One careful palette and typography pass early pays for itself across every screen.
2. **Data processing.** Parsing, schema validation, file I/O.
3. **Computations.** The domain engine (amortization, forecasting, whatever the app actually does).
4. **Rendering.** Chart math, layout logic, interaction details.

Everything else, use off-the-shelf and keep it boring: pnpm + Vite + Vitest + ESLint + Prettier + Stylelint. Don't reinvent bundlers, custom CSS-in-JS runtimes, or state containers.

## Framework pick

- **Heavily interactive / dashboard / tool app** (charts, live edits, client-side compute, multiple linked views): **React 19 + TypeScript**. Largest ecosystem, function components + hooks keep things short. Split a `.tsx` file when it crosses ~300 lines.
- **Content-first site with sprinkles of interactivity** (marketing, docs, blog, portfolio): **Astro**. Server-rendered, ships near-zero JS, drop-in React / Solid / Svelte "islands" for the interactive bits.
- **Purely static content with Markdown as source of truth** (documentation, essays, simple personal sites): **Eleventy (11ty)**. Tiny, no JS runtime.

Consider Vue 3 only when the codebase is already Vue. Always search for the latest LTS versions when starting greenfield (frameworks, CI component versions, dependencies).

For React state, default to **Zustand** (~1 KB) for any shared state that more than one component reads or writes. One store per domain (tasks, sync, UI); the hook doubles as a selector; raw `getState` / `setState` make tests trivial. `useState` / `useReducer` cover local state; `useContext` covers narrow read-mostly injection. Only reach for Jotai, TanStack Store, or Redux Toolkit when Zustand's bundle or ergonomics actually get in the way.

See `references/tooling.md` for the full stack list (build, TS config, validation, dates, forms, styling, icons, charts, component kits).

## Repo shape

```
project/
  pnpm-workspace.yaml
  package.json          # root scripts, dev deps, format/lint config
  Makefile              # developer commands
  .gitlab-ci.yml        # or .github/workflows/
  tsconfig.base.json
  .editorconfig
  .prettierrc / eslint.config.js / .stylelintrc.cjs
  lefthook.yml          # pre-commit + pre-push hooks
  README.md
  packages/
    core/               # pure TS: types, schemas, engine, parsing. No DOM.
    web/                # React app (the shipping target)
    desktop/            # optional: Tauri wrapper (src-tauri + deps)
    <target>/           # other future targets (Nextcloud, Obsidian, ...)
```

## The `core` package is sacred

- No DOM references. Grep `window\.|document\.|localStorage|navigator\.` in `packages/core/src` and it must return nothing.
- `types: []` in its tsconfig; don't force Node types onto every consumer. Split a `tsconfig.test.json` with `types: ["node"]` for Node-using tests.
- Exports the data model, validation (JSON Schema + Ajv), parse/serialize (YAML, CSV), the compute engine(s), and framework-neutral interfaces (e.g. `DataSource`).
- 100% line coverage on pure compute code. Hand-verified fixtures as snapshots.

## Source abstraction: the key to a second target

The hardest thing to port is storage. Define an interface in core early:

```ts
// packages/core/src/source/types.ts
export interface DataSource {
  readonly kind: string; // 'demo' | 'fsa' | 'ocs' | ...
  readonly name: string; // UI label
  readonly canWrite: boolean;
  read(): Promise<string>; // returns serialized text
  write(text: string): Promise<void>;
}
```

Implement `DemoSource`, `FsaSource` (File System Access API), and `FallbackSource` (download-only) in the web package. The store holds a `source` ref and calls `source.read()` / `source.write()`. When you add a Nextcloud, Obsidian, or native target, you write one more `Source` class.

## Component discipline

Keep `.tsx` files under ~300 lines. When a component grows past 300 it almost always has a natural extraction point (a modal, a form section, an editor row). React's lack of a built-in template block makes JSX components feel longer than Vue SFCs at the same complexity, so the ceiling is tighter.

Common split patterns that pay off: `<DataTable>` vs `<RowEditor>`, `<Form>` vs `<FormSection*>`, `<Chart>` vs `<ChartTooltip>` vs pure `*.ts` path builders, custom hooks (`useThing.ts`) for any stateful logic reused more than once or that has its own test surface.

### Styling: start global, split only when it hurts

If you're writing CSS, default to a single global stylesheet (`styles/app.css`, imported once in `main.tsx`) that holds design tokens, typography, buttons, banners, form fields, and layout helpers. This keeps the style surface small, easy to grep, easy to evolve.

Add a component-local CSS Module (`Component.module.css`) only when the component has a one-off layout that won't recur anywhere else, and when its class names are specific enough that a collision with the global sheet would be annoying (`.row`, `.header`, `.actions`). When two modules start needing the same rule, promote it to the global sheet instead of copying. If you're using Tailwind, the same "write it inline, promote when it repeats" rule applies: a rule that shows up on five buttons becomes a `@apply` utility or a component with the classes baked in.

Avoid CSS-in-JS runtime libraries; they balloon the bundle for no gain in a small app.

## Design tokens

Keep a single `tokens.css` as the source of truth, with named colors (e.g. "marigold", "paper", "ink"):

```css
:root {
  --paper: #faf7f2;
  --paper-sunk: #f3efe8;
  --ink: #1a1915;
  --ink-muted: #7a766d;
  --accent: #1f3a5f;
  --mark: #d97e2b; /* secondary accent */
  --positive: #3f6d4e;
  --negative: #8c3a2e;
  --shadow-rgb: 0 0 0; /* flipped in dark mode */
  --font-serif: 'Source Serif 4', ..., serif;
  --font-sans: 'Inter', system-ui, ..., sans-serif;
  --font-mono: 'JetBrains Mono', ..., monospace;
}

@media (prefers-color-scheme: dark) {
  :root {
    /* remapped palette + --shadow-rgb: 255 255 255 */
  }
}
```

Typography: one serif face for headings/numbers with character, one sans for UI, one mono for code/paths. Use `font-feature-settings: 'tnum' 1` for money/amounts so digits align in columns. Load from Google Fonts via a `<link>` in `index.html` above the bundle script, and cap the total at 2–3 families to keep the payload small.

## Testing philosophy

- **Core**: exhaustive unit tests. 100% line coverage target. Fixtures committed alongside expected outputs; a round-trip snapshot test catches accidental behavior drift.
- **Web**: test **Zustand stores** directly (`useThingStore.getState()` and its actions, no mounting needed) and small pure helpers. Test custom hooks with `renderHook` from `@testing-library/react` for a minimal harness. Mount a full component only when you need to assert an interaction that's hard to describe in props (e.g. a sticky header rendering at the right row); use `render` + `screen` + `userEvent`, no shallow rendering. Don't bother with E2E or visual-regression unless prompted.
- **One smoke test per component file** catches import breaks and basic render failures cheaply.
- When a bug is fixed, add the failing test first so it can't regress.

## README structure

Keep it short and complete.

1. **Title and one-line pitch.**
2. **Live URL.**
3. **Features**: bullet list using `**Label:** description` form. One line per feature, write what it does for the user, not the tech.
4. **Using the app**: numbered steps from "open the URL" to "save the file". Every button in the UI should be mentioned here.
5. **Minimal data-file example**: the smallest valid input. Link the full schema file under the example, don't inline it.
6. **Development**: prereqs (pinned Node and pnpm versions), clone + install commands, then the Makefile target list as a code block. Usually enough; most devs don't want more.
7. **CI and deploy**: one paragraph naming the CI file and the secrets the deploy job needs. Include a short table of variable names and where to find them on Cloudflare, GitHub, etc.
8. **Key dependencies**: a table listing major runtime and tooling deps with versions and one-line purposes. Makes audits and upgrade planning trivial.
9. **Contributing**: Conventional Commits, scoping rules, fixture rules.
10. **License.**

## Checklist for a new repo

1. `pnpm init` root + `pnpm-workspace.yaml`. Pin `packageManager`.
2. `tsconfig.base.json` with strict options.
3. Root `.editorconfig`, `.prettierrc`, `eslint.config.js`, `.stylelintrc.cjs`, `.prettierignore` (with `.pnpm-store`). See `references/tooling.md`.
4. `packages/core` with types, schemas, engine, tests. No DOM.
5. `packages/web` with Vite + React + Zustand, one global `styles/app.css` (tokens + base) or Tailwind, `main.tsx`, `App.tsx`, one component, one Zustand store, one test.
6. `Makefile` + root scripts. See `references/tooling.md`.
7. `lefthook.yml` + `make install-hooks`. See `references/tooling.md`.
8. `README.md` (features + use + minimal example + dev + license).
9. `.gitlab-ci.yml` with install/check/build/deploy stages. See `references/ci.md`.
10. `robots.txt` and `llms.txt` in `packages/web/public/`. See `references/deploy.md`.
11. `wrangler` devDep + `deploy:pages` script + `make deploy` target. See `references/deploy.md`.
12. First Cloudflare Pages deploy (once CI secrets are set).
13. Umami script in `index.html` (optional, once you want analytics). See `references/deploy.md`.
14. Optional: `packages/desktop/` with Tauri, plus `.github/workflows/release-desktop.yml` for cross-platform installers. See `references/desktop-tauri.md` and `references/ci.md`.

## Anti-patterns to avoid

- Skipping the core/target split and putting everything in one package.
- Inlining CSS in files for rules that apply elsewhere.
- Letting the store couple directly to FSA, fetch, or `localStorage`. Always go through an interface.
- Committing the pnpm store. Add `.pnpm-store` to both `.gitignore` and `.prettierignore`.
