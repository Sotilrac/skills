---
name: nextcloud-web-app
description: Add a Nextcloud app target to a local-first web app and publish it to the Nextcloud App Store. Covers the app package layout, reusing the shared Source interface over an OCS API, PHP tooling, and the signed CI release pipeline (with the non-obvious gotchas). Use after standalone-web-app when the same shared engine should ship inside Nextcloud.
---

# Nextcloud web app target

Companion to `standalone-web-app`. That skill builds a local-first browser app whose `shared` package holds types, schema, engine, and a framework-neutral `DataSource` interface. This skill adds a **Nextcloud app** that reuses all of `shared`, persists data as files in the user's Nextcloud, and publishes to the App Store.

This is where the source abstraction pays off: the only new code is one OCS-backed `DataSource`, a thin PHP file-I/O layer, and a mount inside Nextcloud chrome. `shared` ships unchanged.

## Reference files (load on demand)

- `${CLAUDE_SKILL_DIR}/references/app-anatomy.md` — package layout, `info.xml`, OCS routes/controllers, the OCS `DataSource`, mounting, PHP tooling and its gotchas.
- `${CLAUDE_SKILL_DIR}/references/publishing.md` — full App Store flow: cert, one-time registration, signed two-job CI release. **Read before writing release CI; the obvious approach fails four ways.**

## When to use

- You have a local-first app with a `DataSource` interface in `shared`.
- A household/team shares the data via normal Nextcloud file sharing — no separate account or DB.
- You want tag-driven App Store releases.

## Layout

```
packages/
  shared/      # unchanged: types, schema, engine, DataSource interface
  web/         # standalone target (FsaSource, FallbackSource, DemoSource)
  nextcloud/   # NEW: PHP app + Vue/React mount + OcsSource
```

## The four pieces

1. **`appinfo/info.xml`** — app id, version (= release tag source of truth), NC/PHP version ranges, navigation, screenshots. Validate against the live `info.xsd`.
2. **PHP layer (`lib/`)** — controllers expose an OCS API (routes via `#[ApiRoute]` attributes; `routes.php` returns `[]`); services scan a configured folder and read/write files. Thin: file I/O only, no engine.
3. **OCS `DataSource` (`src/source/`)** — the same `shared` interface over `fetch`. Carry mtime from `read()`, send as `If-Match` on `write()`, map `412` to a conflict the UI surfaces. This is the whole concurrency story for shared files.
4. **Mount (`src/main.ts`)** — mount onto the NC page node; match native chrome (e.g. native `title` tooltips, not a themed floater).

## Data and sharing model

- Files in a user-chosen folder (configurable; first folder = primary for new files).
- Cross-file metadata (mappings, settings) goes **in the folder as a dotfile** (e.g. `.mappings.yaml`), not per-user NC config, so collaborators see the same state.

## PHP tooling gotchas (each cost a CI run)

- **psalm**: scope `projectFiles` to `lib` only — test files use PHPUnit mocks psalm can't type without the psalm-phpunit plugin (`composer test` gates them).
- **psalm stubs**: OCP interfaces reference private `OC\` symbols `nextcloud/ocp` doesn't ship (`IRootFolder` -> `OC\Hooks\Emitter`). Add `tests/stubs/psalm.phpstub` with *unconditional* declarations via `<stubs>`.
- **composer `--no-dev`**: add `--no-scripts` (post-install runs the bamarni bin plugin, a dev dep). Use `--working-dir=…`, not `cd … && cd -`.
- **editorconfig**: tabs for `php`/`xml`; add `phpstub` to that glob.

## Publishing in one paragraph

One-time: (1) cert via PR to `nextcloud/app-certificate-requests` (CN = app id); (2) **register the app** — a separate step — POST the public cert + a signature of the app id to `/api/v1/apps`; (3) set CI vars. Then: bump `info.xml` `<version>`, push `nc-vX.Y.Z`, CI builds/signs/submits. First release waits in manual review. Pipeline shape and gotchas in `references/publishing.md`.

## Anti-patterns

- Duplicating the engine into PHP (PHP does file I/O only).
- Shared metadata in per-user NC config (breaks sharing) — use a folder dotfile.
- Skipping the mtime/`If-Match` dance — silent clobbering on shared files.
- Signing key anywhere public. Only the public cert and app-id signatures leave the machine.
