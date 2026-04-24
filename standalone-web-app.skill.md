---
name: standalone-web-app
description: Build and ship a local-first standalone web app: monorepo, stack picks, component discipline, theming, analytics, CI, deploy. Use to bootstrap a new data-centric tool that runs entirely in the browser.
---

# Standalone web app

Playbook for building a local-first browser app that uses local data
(e.g., YAML, JSON, TOML, Markdown, csv), computes and renders something from it,
and deploys as a static bundle. The app never talks to a backend; all parsing,
math, and persistence happen in the browser.

## When to use this skill

- Tool reads user-owned data, computes something, shows a dashboard.
- No accounts, sync service, or per-user database.
- Deployable as a single static bundle to any CDN.
- You want the same core to serve future targets (Tauri desktop,
  Nextcloud, Obsidian plugin).

## Complexity budget

Spend complexity only where it shows up in the product:

1. **Style guide / design tokens.** One careful palette + typography
   pass early pays for itself across every screen.
2. **Data processing.** Parsing, schema validation, file I/O.
3. **Computations.** The domain engine (amortization, forecasting,
   whatever the app actually does).
4. **Rendering.** Chart math, layout logic, interaction details.

Everything else, use off-the-shelf and keep it boring: pnpm + Vite +
Vitest + ESLint + Prettier + Stylelint. Don't invent bespoke bundlers,
custom CSS-in-JS runtimes, or your own state container. The wheel is
round.

## Stack choices

### Framework: pick based on how interactive the app is

- **Heavily interactive / dashboard / tool app** (charts, live edits,
  client-side compute, multiple linked views): **React 19 + TypeScript**.
  Largest ecosystem, unceremonious TS story via plain `tsc`, function
  components + hooks keep things short. Split a `.tsx` file when it
  crosses ~300 lines.
- **Content-first site with sprinkles of interactivity** (marketing
  page, docs site, blog, portfolio): **Astro**. Server-rendered by
  default, ships near-zero JS, lets you drop in React / Solid / Svelte
  "islands" for the interactive bits.
- **Purely static content with Markdown as the source of truth**
  (documentation, essays, simple personal sites): **Eleventy (11ty)**.
  Tiny, no JS runtime, templates in Nunjucks / Liquid / JSX / whatever
  you like.

**Consider Vue 3** only when the codebase is already Vue, or the team
strongly prefers SFCs. It's fine, just not the default.

For state in React, default to **Zustand** (≈1 KB) for any shared state
that more than one component reads or writes. It's boring and repeatedly
useful: one store per domain (tasks, sync, UI), the hook doubles as a
selector, and the raw `getState` / `setState` make tests trivial.
`useState` / `useReducer` still cover local state; `useContext` covers
narrow read-mostly injection. Only reach for Jotai, TanStack Store, or
Redux Toolkit when Zustand's bundle or ergonomics actually get in the
way.

Always search for the latest LTS versions when starting a greenfield
project. This applies to frameworks, CI/CD component versions, and
dependencies.

### Everything else

- **Build**: Vite + `@vitejs/plugin-react`. Target `es2023`, `base: './'`
  so the bundle works at any subpath.
- **TypeScript**: strict. Turn on `noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes`, `verbatimModuleSyntax`.
- **Testing**: Vitest + `@testing-library/react` + `@testing-library/user-event`.
  `jsdom` environment for component tests, plain Node for core tests.
- **State**: Zustand for shared state (one store per domain).
  `useState` / `useReducer` for local, `useContext` for narrow
  read-mostly injection.
- **Validation**: Zod. Pairs with TypeScript so your parsed data is
  typed end-to-end; works for both request/response schemas and
  domain-model validation. Reach for Ajv + JSON Schema only when the
  schema has to round-trip as JSON (e.g., for external consumers).
- **Date handling**: `date-fns` for formatting and math. Don't
  hand-roll `new Date()` arithmetic; timezone bugs will find you.
- **Forms**: plain controlled inputs are fine for <10 fields. Add
  `react-hook-form` + Zod when forms get larger or need complex validation.
- **Styling**: two idioms work; pick one and stick with it.
  - **Hand-written CSS**: one global stylesheet (`styles/app.css`) with
    tokens, typography, buttons, banners. Reach for a component-local
    `Component.module.css` only when a rule is genuinely one-off and
    class-name collisions would annoy.
  - **Tailwind v4**: utility-first, also effectively "one global
    stylesheet". Pairs well with a `components/ui/` kit in the shadcn
    style (unstyled Radix primitives + Tailwind classes committed into
    the repo). Good when the team prefers writing classes to writing
    CSS.

  Avoid CSS-in-JS runtime libraries either way; they balloon the
  bundle for no gain in a small app.

- **Package manager**: pnpm with workspaces. `packageManager` pinned in
  root `package.json` for Corepack.
- **Icons**: `@phosphor-icons/react`, `lucide-react`, or Heroicons.
  Lucide pairs naturally with shadcn/ui; Phosphor has more stylistic
  weights. Whichever you pick, use tree-shakeable imports (no default
  pack imports).
- **Component kits**: for React, **shadcn/ui** is the default worth
  trying. It's not a package, it's a copy-in-your-repo set of Radix-
  based primitives styled with Tailwind; you own the code and can
  customize freely. If you're hand-writing CSS, skip it and build your
  own small primitives as you need them.
- **Charts**: Use off the shelf charts as much as practical. Hand-rolled SVG
  ok for small single-chart dashboards (write scale + tick helpers in a
  `scale.ts` util, and keep the path math out of the component).

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

### The `core` package is sacred

- Zero DOM references: grep `window\.|document\.|localStorage|navigator\.`
  in `packages/core/src` and it must return nothing.
- `types: []` in its tsconfig; don't force Node types onto every consumer.
  Split a `tsconfig.test.json` with `types: ["node"]` for Node-using tests.
- Exports the data model, validation (JSON Schema + Ajv), parse/serialize
  (YAML / CSV), the compute engine(s), and any framework-neutral
  interfaces (e.g., `DataSource`).
- 100% line coverage on pure compute code. Hand-verified fixtures as
  snapshots.

### Source abstraction — the key to a second target

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

Implement `DemoSource`, `FsaSource` (File System Access API), and
`FallbackSource` (download-only) in the web package. The store holds a
`source` ref and calls `source.read()` / `source.write()`. When you add a
Nextcloud / Obsidian / native target, you write one more `Source` class.

## Component discipline

### Keep .tsx files under ~300 lines

When a component grows past 300, it almost always has a natural extraction
point (a modal, a form section, an editor row). Pull it out. React's lack
of a built-in template block makes JSX components feel longer than Vue
SFCs at the same complexity, so the ceiling is tighter.

Common split patterns that pay off in practice:

- `<DataTable>` vs `<RowEditor>`: inline editors always belong in their
  own component.
- `<Form>` vs `<FormSection*>`: one component per logical field group.
- `<Chart>` vs `<ChartTooltip>` vs pure `*.ts` path builders.
- Custom hooks (`useThing.ts`) for any stateful logic a component uses
  more than once, or that has its own test surface.

### Styling: start global, split only when it hurts

If you're writing CSS, default to a single global stylesheet
(`styles/app.css`, imported once in `main.tsx`) that holds design tokens,
typography, buttons, banners, form fields, and layout helpers. This
keeps the style surface small, easy to grep, and easy to evolve.

Add a component-local CSS Module (`Component.module.css`) only when:

- The component has a one-off layout that won't recur anywhere else, and
- Its class names are specific enough that a collision with the global
  sheet would be annoying (e.g., `.row`, `.header`, `.actions`).

When two modules start needing the same rule, promote it to the global
sheet instead of copying. The heuristic: if a grep for a class across
`src/` would be confusing, scope it; if it would be useful, globalize it.

If you're using Tailwind, the same "write it inline, promote when it
repeats" rule still applies. A rule that shows up on five buttons
becomes a `@apply` utility or a component with the classes baked in.

Avoid CSS-in-JS (`styled-components`, Emotion) unless you have a concrete
reason. Boring CSS (or Tailwind) + tokens handles everything this kind
of app needs.

## Style guide (design tokens)

Create a color palette with named colours (e.g, merigold).

Keep a single `tokens.css` as the source of truth. For instance:

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

Typography: one serif face for headings/numbers with character, one sans
for UI, one mono for code/paths. Use `font-feature-settings: 'tnum' 1` for
money/amounts so digits align in columns.

## Analytics

Umami (cookieless, GDPR-friendly) is the default. Add the script to
`index.html`, disable auto-track, prefix the URL path when multiple sites
share one Umami site:

```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="WEBSITE_ID"></script>
```

If the app has real SPA routes, also hook `popstate` to re-fire the
tracker with the new path.

## Privacy files (`robots.txt` + `llms.txt`)

Drop both under `packages/web/public/`. Vite copies them to `dist/`
verbatim.

- `robots.txt`: `User-agent: *` → `Allow: /` (so search indexing still
  works), plus explicit `Disallow: /` blocks for AI-training bots
  (GPTBot, ClaudeBot, CCBot, Google-Extended, PerplexityBot, Bytespider,
  etc.). Maintain the list; new bots appear every quarter.
- `llms.txt`: a short markdown file per llmstxt.org. Title, one-line
  blurb, then sections for what it is, privacy, data model, stack, and a
  "training not permitted, see /robots.txt" line.

## Deploy: Cloudflare Pages via wrangler

1. Add `wrangler` to root devDeps: `pnpm add -Dw wrangler`.
2. Create the Pages project interactively:
   `pnpm exec wrangler login` then
   `pnpm exec wrangler pages project create <name> --production-branch=main`.
3. Add a script to root `package.json`:
   ```
   "deploy:pages": "wrangler pages deploy packages/web/dist --project-name=<name> --branch=main --commit-dirty=true"
   ```
4. Add a `deploy` Makefile target: depends on `build`, then runs
   `deploy:pages`.
5. In CI, a `deploy:cloudflare` job on the default branch runs
   `pnpm run deploy:pages`. The job reads `CLOUDFLARE_API_TOKEN` and
   `CLOUDFLARE_ACCOUNT_ID` from masked CI variables; don't commit them.
   - **Creating the token**: Cloudflare dashboard → My Profile → API
     Tokens → Create Token. Start from the "Edit Cloudflare Workers"
     template, then add the `Cloudflare Pages: Edit` permission. That
     single token covers both Pages and Workers deploys.
   - **Account ID**: visible in the right sidebar of any domain page, or
     Workers & Pages → Overview.
6. For custom domain, add the subdomain in the Cloudflare dashboard and
   either let Cloudflare manage the DNS or add a CNAME pointing at
   `<project>.pages.dev`.

## Lightweight backend: Cloudflare Workers (when the app needs one)

Sometimes "local-first" still needs a whisker of backend: a CORS proxy
to a user's WebDAV / Nextcloud, a tiny auth step that encrypts and
stashes credentials, or a rate-limited outbound call to an API that
can't be called from the browser. In those cases, a **Cloudflare
Worker** is the right shape:

- Deployed with the same `wrangler` CLI already in the repo.
- Use `itty-router` for request routing; keep the worker under ~300
  lines total.
- Use **Workers KV** for anything you need to persist between requests
  (encrypted session tokens, rate-limit counters). Encrypt secrets with
  AES-GCM before writing; the key is a `wrangler secret`.
- Local dev secrets live in `worker/.dev.vars` (git-ignored); production
  secrets go through `wrangler secret put`.
- Separate workspace: `packages/worker/` with its own `package.json`,
  `wrangler.toml`, and small test suite. The worker's routes are
  request/response functions: easy to unit-test with `Request` / `Response`
  constructors, no mock server needed.

When you don't need a backend, don't build one. Most apps in this skill's
scope don't.

## Desktop app: Tauri

For a standalone desktop build, wrap the web bundle in **Tauri**. It's
smaller than Electron (uses the system webview instead of bundling
Chromium), Rust-backed, and plays nicely with Vite.

Start with `pnpm create tauri-app` (or `pnpm add -D @tauri-apps/cli` in
an existing repo, then `tauri init`). The default config points Tauri at
the Vite dev server in development and at `dist/` for production. Stash
the Rust side under `packages/desktop/src-tauri/` so the web package
stays target-agnostic.

Use Tauri's filesystem and dialog APIs instead of the File System Access
API in the desktop build. This is exactly the `DataSource` abstraction
paying off: write a `TauriSource` alongside `FsaSource` and the rest of
the app is unchanged.

Bundle targets: `.msi` / `.exe` (Windows), `.dmg` / `.app` (macOS), and
`.AppImage` / `.deb` / `.rpm` (Linux). Code-signing is optional but
recommended for production; without it, Windows shows SmartScreen
warnings and macOS Gatekeeper refuses to run unsigned downloads.

## CI/CD choice: GitLab vs GitHub

- **GitLab CI** is great for build / lint / test / deploy-to-web flows
  on Linux. Its shared runners only offer Linux; macOS runners exist
  only on paid tiers with limited minutes.
- **GitHub Actions** is the default when you need **cross-platform
  desktop builds**, because its free matrix covers
  `ubuntu-latest` / `macos-latest` / `windows-latest`.

Practical split for a project that ships both a web bundle and a desktop
app:

- GitLab CI: install → lint → typecheck → test → build → deploy to
  Cloudflare Pages.
- GitHub Actions: triggered on tags (e.g. `desktop-v*`), runs a matrix
  of `[ubuntu-latest, macos-latest, windows-latest]` and calls
  `tauri build` on each, then attaches the resulting installers to a
  GitHub Release.

Keep both CI configs alongside each other; they're not exclusive. If you
only ship the web app, stay on GitLab alone. If you only ship the
desktop app, stay on GitHub alone.

### GitHub Actions skeleton for Tauri builds

```yaml
# .github/workflows/release-desktop.yml
name: release-desktop
on:
  push:
    tags: ['desktop-v*']

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v5
        with:
          node-version: 24
          cache: pnpm
      - uses: dtolnay/rust-toolchain@stable
      - name: Linux build deps
        if: matrix.os == 'ubuntu-latest'
        run: sudo apt-get update && sudo apt-get install -y libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
      - run: pnpm install --frozen-lockfile
      - uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Optional code-signing secrets:
          # APPLE_CERTIFICATE, APPLE_CERTIFICATE_PASSWORD, APPLE_SIGNING_IDENTITY, APPLE_ID, APPLE_PASSWORD, APPLE_TEAM_ID
          # WINDOWS_CERTIFICATE, WINDOWS_CERTIFICATE_PASSWORD
        with:
          tagName: ${{ github.ref_name }}
          releaseName: 'Desktop ${{ github.ref_name }}'
          releaseDraft: true
          prerelease: false
```

## README structure

Keep it short and complete:

1. **Title + one-line pitch.**
2. **Live URL.**
3. **Features**: bullet list using `**Label:** description` form. One
   line per feature, write what it does for the user, not the tech.
4. **Using the app**: numbered steps from "open the URL" to "save the
   file". Every button in the UI should be mentioned here.
5. **Minimal data-file example**: the smallest valid input. Link the full
   schema file under the example, don't inline it.
6. **Development**: prereqs (pinned Node / pnpm versions), clone + install
   commands, then the Makefile target list as a code block. That's
   usually enough — most devs don't want more.
7. **CI + deploy**: one paragraph naming the CI file and the secrets the
   deploy job needs. Include a short table of variable names and where
   to find them on Cloudflare / GitHub / wherever.
8. **Key dependencies**: a table listing major runtime and tooling deps
   with versions and one-line purposes. Makes audits and upgrade
   planning trivial.
9. **Contributing**: Conventional Commits, scoping rules, fixture rules.
10. **License**.

## Build, test, lint

### Makefile

```makefile
.PHONY: help install dev build test lint format typecheck install-hooks clean deploy

help:
	@echo "  make install        Install all workspace dependencies"
	@echo "  make dev            Start dev server"
	@echo "  make build          Build all packages"
	@echo "  make test           Run all tests"
	@echo "  make lint           Run ESLint, Prettier, Stylelint"
	@echo "  make format         Auto-fix formatting + lint"
	@echo "  make typecheck      Typecheck all packages"
	@echo "  make install-hooks  Install pre-commit hooks"
	@echo "  make deploy         Build and deploy to Cloudflare Pages"
	@echo "  make clean          Remove build output"

install:      ; pnpm install
dev:          ; pnpm dev
build:        ; pnpm build
test:         ; pnpm test
lint:         ; pnpm lint
format:       ; pnpm format
typecheck:    ; pnpm typecheck
install-hooks:; pnpm exec lefthook install
clean:        ; pnpm -r exec rm -rf dist coverage .vite
deploy: build ; pnpm run deploy:pages
```

Root `package.json` scripts chain through to each package:

```
"test": "pnpm -r test",
"build": "pnpm -r build",
"typecheck": "pnpm -r typecheck",
"lint": "pnpm -r lint && pnpm run lint:prettier && pnpm run lint:stylelint",
"lint:prettier": "prettier --check .",
"lint:stylelint": "stylelint \"packages/**/*.css\" --allow-empty-input"
```

### Prettier / ESLint / Stylelint

- Prettier as the formatter of record.
- ESLint with `@typescript-eslint`, `eslint-plugin-react`,
  `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, and
  `eslint-config-prettier` (disables rules that conflict with Prettier).
  Turn on `react-hooks/exhaustive-deps` as an error.
- Stylelint with `stylelint-config-standard`. CSS Modules don't require
  additional plugins. If you add SCSS later, bring in
  `stylelint-config-standard-scss`.
- `.prettierignore`: `**/dist`, `**/node_modules`, `**/coverage`,
  `**/.pnpm-store`, `**/.vite`, `pnpm-lock.yaml`, `LICENSE`. The
  `.pnpm-store` entry matters; CI puts the store inside the project dir
  for caching, and Prettier will try to format its binary files.
- `.gitignore`: add `.pnpm-store/` alongside `node_modules/` so nobody
  accidentally commits it.

### Hooks with Lefthook

One YAML file, parallel by default, no shell scripts. Runs Prettier +
ESLint + Stylelint on staged files at commit and typecheck + tests on
push.

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    prettier:
      {
        glob: '*.{ts,tsx,js,jsx,css,json,yaml,yml,md}',
        run: 'pnpm exec prettier --check {staged_files}',
      }
    eslint: { glob: '*.{ts,tsx,js,jsx}', run: 'pnpm exec eslint {staged_files}' }
    stylelint: { glob: '*.css', run: 'pnpm exec stylelint {staged_files}' }
    editorconfig: { run: 'pnpm exec editorconfig-checker' }

pre-push:
  commands:
    typecheck: { run: 'pnpm typecheck' }
    test: { run: 'pnpm test' }
```

Install once per clone with `make install-hooks`. Never use `--no-verify`;
fix the thing.

## Testing philosophy

- **Core**: exhaustive unit tests. 100% line coverage target. Fixtures
  committed alongside expected outputs; a round-trip snapshot test catches
  accidental behavior drift.
- **Web**: test **Zustand stores** directly (call `useThingStore.getState()`
  and its actions; no mounting needed) and small pure helpers. Test
  custom hooks with `renderHook` from `@testing-library/react` for a
  minimal harness. Mount a full component only when you need to assert
  an interaction that's hard to describe in props (e.g., a sticky
  header rendering at the right row); use `render` + `screen` +
  `userEvent`, no shallow rendering. Don't bother with E2E or
  visual-regression unless prompted.
- **One smoke test per component file** is fine; it catches import
  breaks and basic render failures cheaply.
- When a bug is fixed, add the failing test first so it can't regress.

## GitLab CI skeleton

```yaml
default:
  image: node:24-bookworm
  interruptible: true

variables:
  PNPM_HOME: '$CI_PROJECT_DIR/.pnpm-store'
  npm_config_cache: '$CI_PROJECT_DIR/.npm'

stages: [install, check, build, deploy]

.pnpm-cache: &pnpm-cache
  key: { files: [pnpm-lock.yaml] }
  paths: [.pnpm-store/, node_modules/, packages/*/node_modules/]

.setup: &setup
  before_script:
    - corepack enable
    - corepack prepare pnpm@10.33.1 --activate
    - pnpm config set store-dir .pnpm-store
    - pnpm install --frozen-lockfile

install:
  {
    stage: install,
    cache: { <<: *pnpm-cache, policy: pull-push },
    <<: *setup,
    script: [pnpm -v, node -v],
  }
lint:
  {
    stage: check,
    needs: [install],
    cache: { <<: *pnpm-cache, policy: pull },
    <<: *setup,
    script: [pnpm lint],
  }
typecheck:
  {
    stage: check,
    needs: [install],
    cache: { <<: *pnpm-cache, policy: pull },
    <<: *setup,
    script: [pnpm typecheck],
  }
test:
  {
    stage: check,
    needs: [install],
    cache: { <<: *pnpm-cache, policy: pull },
    <<: *setup,
    script: [pnpm test],
  }
build:
  stage: build
  needs: [lint, typecheck, test]
  cache: { <<: *pnpm-cache, policy: pull }
  <<: *setup
  script: [pnpm build]
  artifacts:
    name: 'web-dist-$CI_COMMIT_SHORT_SHA'
    paths: [packages/web/dist/]
    expire_in: 14 days

deploy:cloudflare:
  stage: deploy
  needs: [build]
  rules: [{ if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH }]
  cache: { <<: *pnpm-cache, policy: pull }
  <<: *setup
  script: [pnpm run deploy:pages]
```

On GitHub Actions the shape is identical; swap the cache mechanism for
`actions/cache`.

## Checklist for a new repo

1. `pnpm init` root + `pnpm-workspace.yaml`. Pin `packageManager`.
2. `tsconfig.base.json` with strict options.
3. Root `.editorconfig`, `.prettierrc`, `eslint.config.js`,
   `.stylelintrc.cjs`, `.prettierignore` (with `.pnpm-store`).
4. `packages/core` with types, schemas, engine, tests. No DOM.
5. `packages/web` with Vite + React + Zustand, one global
   `styles/app.css` (tokens + base) or Tailwind, `main.tsx`, `App.tsx`,
   one component, one Zustand store, one test.
6. `Makefile` + root scripts.
7. `lefthook.yml` + `make install-hooks`.
8. `README.md` (features + use + minimal example + dev + license).
9. `.gitlab-ci.yml` with install/check/build/deploy stages.
10. `robots.txt` and `llms.txt` in `packages/web/public/`.
11. `wrangler` devDep + `deploy:pages` script + `make deploy` target.
12. First Cloudflare Pages deploy (once CI secrets are set).
13. Umami script in `index.html` (optional, once you want analytics).
14. Optional: `packages/desktop/` with Tauri, plus
    `.github/workflows/release-desktop.yml` for cross-platform installers.

## Anti-patterns I'll regret later

- Skipping the core/target split and putting everything in one package.
- Inlining CSS in files for rules that apply elsewhere.
- Letting the store couple directly to FSA / fetch / `localStorage`.
  Always go through an interface.
- Committing the pnpm store. Always add `.pnpm-store` to both
  `.gitignore` and `.prettierignore`.
- Listing every AI-training bot manually is unavoidable; do
  it once, refresh yearly.
