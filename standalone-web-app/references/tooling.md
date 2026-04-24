# Stack and tooling details

Referenced from `SKILL.md`. Read when setting up the stack, writing lint configs, or authoring hooks.

## Stack picks beyond the framework

- **Build**: Vite + `@vitejs/plugin-react`. Target `es2023`, `base: './'` so the bundle works at any subpath.
- **TypeScript**: strict. Turn on `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`.
- **Testing**: Vitest + `@testing-library/react` + `@testing-library/user-event`. `jsdom` environment for component tests, plain Node for core tests.
- **State**: Zustand for shared state (one store per domain). `useState` / `useReducer` for local, `useContext` for narrow read-mostly injection.
- **Validation**: Zod. Pairs with TypeScript so your parsed data is typed end-to-end; works for request/response schemas and domain-model validation. Reach for Ajv + JSON Schema only when the schema has to round-trip as JSON (e.g. for external consumers).
- **Date handling**: `date-fns` for formatting and math. Don't hand-roll `new Date()` arithmetic; timezone bugs will find you.
- **Forms**: plain controlled inputs are fine for <10 fields. Add `react-hook-form` + Zod when forms get larger or need complex validation.
- **Styling**: two idioms work; pick one and stick with it.
  - **Hand-written CSS**: one global stylesheet (`styles/app.css`) with tokens, typography, buttons, banners. Reach for a component-local `Component.module.css` only when a rule is genuinely one-off and class-name collisions would annoy.
  - **Tailwind v4**: utility-first, also effectively "one global stylesheet". Pairs well with a `components/ui/` kit in the shadcn style (unstyled Radix primitives + Tailwind classes committed into the repo). Good when the team prefers writing classes to writing CSS.

  Avoid CSS-in-JS runtime libraries either way; they balloon the bundle for no gain in a small app.
- **Package manager**: pnpm with workspaces. `packageManager` pinned in root `package.json` for Corepack.
- **Icons**: FontAwesome, inlined as SVG. Copy the raw SVG for each icon you need from fontawesome.com into a small `src/icons.tsx` module that exports each as a named React component (e.g. `<IconCheck />`, `<IconAlert />`). This ships only the icons the app uses; no tree-shake gymnastics, no runtime icon lookup. Pick one FontAwesome variant (solid, regular, light, duotone, sharp) and stay in it across the app. If you specifically need a kit with more custom weights, `@phosphor-icons/react` or `lucide-react` are reasonable alternatives, but stick to named imports only.
- **Component kits**: for React, **shadcn/ui** is the default worth trying. It's not a package, it's a copy-in-your-repo set of Radix-based primitives styled with Tailwind; you own the code and can customize freely. If you're hand-writing CSS, skip it and build your own small primitives as you need them.
- **Charts**: use off-the-shelf charts as much as practical. Hand-rolled SVG is fine for small single-chart dashboards (write scale + tick helpers in a `scale.ts` util, and keep the path math out of the component).

## Makefile

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

```json
"test": "pnpm -r test",
"build": "pnpm -r build",
"typecheck": "pnpm -r typecheck",
"lint": "pnpm -r lint && pnpm run lint:prettier && pnpm run lint:stylelint",
"lint:prettier": "prettier --check .",
"lint:stylelint": "stylelint \"packages/**/*.css\" --allow-empty-input"
```

## Prettier, ESLint, Stylelint

- Prettier as the formatter of record.
- ESLint with `@typescript-eslint`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, and `eslint-config-prettier` (disables rules that conflict with Prettier). Turn on `react-hooks/exhaustive-deps` as an error.
- Stylelint with `stylelint-config-standard`. CSS Modules don't require additional plugins. For SCSS, add `stylelint-config-standard-scss`.
- `.prettierignore`: `**/dist`, `**/node_modules`, `**/coverage`, `**/.pnpm-store`, `**/.vite`, `pnpm-lock.yaml`, `LICENSE`. The `.pnpm-store` entry matters; CI puts the store inside the project dir for caching, and Prettier will try to format its binary files.
- `.gitignore`: add `.pnpm-store/` alongside `node_modules/` so nobody accidentally commits it.

## Hooks with Lefthook

One YAML file, parallel by default, no shell scripts. Runs Prettier + ESLint + Stylelint on staged files at commit, and typecheck + tests on push.

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    prettier:
      glob: '*.{ts,tsx,js,jsx,css,json,yaml,yml,md}'
      run: 'pnpm exec prettier --check {staged_files}'
    eslint:
      glob: '*.{ts,tsx,js,jsx}'
      run: 'pnpm exec eslint {staged_files}'
    stylelint:
      glob: '*.css'
      run: 'pnpm exec stylelint {staged_files}'
    editorconfig:
      run: 'pnpm exec editorconfig-checker'

pre-push:
  commands:
    typecheck: { run: 'pnpm typecheck' }
    test:      { run: 'pnpm test' }
```

Install once per clone with `make install-hooks`. Never use `--no-verify`; fix the thing.
