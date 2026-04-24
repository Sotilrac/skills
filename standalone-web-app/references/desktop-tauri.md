# Tauri desktop builds

Referenced from `SKILL.md`. Read when adding a desktop target.

For a standalone desktop build, wrap the web bundle in **Tauri**. It's smaller than Electron (uses the system webview instead of bundling Chromium), Rust-backed, and plays nicely with Vite.

Start with `pnpm create tauri-app` (or `pnpm add -D @tauri-apps/cli` in an existing repo, then `tauri init`). The default config points Tauri at the Vite dev server in development and at `dist/` for production. Stash the Rust side under `packages/desktop/src-tauri/` so the web package stays target-agnostic.

Use Tauri's filesystem and dialog APIs instead of the File System Access API in the desktop build. This is exactly the `DataSource` abstraction paying off: write a `TauriSource` alongside `FsaSource` and the rest of the app is unchanged.

Bundle targets: `.msi` / `.exe` (Windows), `.dmg` / `.app` (macOS), and `.AppImage` / `.deb` / `.rpm` (Linux). Code-signing is optional but recommended for production; without it, Windows shows SmartScreen warnings and macOS Gatekeeper refuses to run unsigned downloads.

For the CI side, see `ci.md` → "GitHub Actions skeleton for Tauri desktop builds".
