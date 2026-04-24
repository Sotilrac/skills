# CI/CD skeletons

Referenced from `SKILL.md`. Read when wiring up CI for a new repo.

## GitLab vs GitHub

- **GitLab CI** is great for build / lint / test / deploy-to-web flows on Linux. Its shared runners only offer Linux; macOS runners exist only on paid tiers with limited minutes.
- **GitHub Actions** is the default when you need **cross-platform desktop builds**, because its free matrix covers `ubuntu-latest` / `macos-latest` / `windows-latest`.

Practical split for a project that ships both a web bundle and a desktop app:

- GitLab CI: install → lint → typecheck → test → build → deploy to Cloudflare Pages.
- GitHub Actions: triggered on tags (e.g. `desktop-v*`), runs a matrix of `[ubuntu-latest, macos-latest, windows-latest]` and calls `tauri build` on each, then attaches the resulting installers to a GitHub Release.

Keep both CI configs alongside each other; they're not exclusive. If you only ship the web app, stay on GitLab alone. If you only ship the desktop app, stay on GitHub alone.

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
  stage: install
  cache: { <<: *pnpm-cache, policy: pull-push }
  <<: *setup
  script: [pnpm -v, node -v]

lint:
  stage: check
  needs: [install]
  cache: { <<: *pnpm-cache, policy: pull }
  <<: *setup
  script: [pnpm lint]

typecheck:
  stage: check
  needs: [install]
  cache: { <<: *pnpm-cache, policy: pull }
  <<: *setup
  script: [pnpm typecheck]

test:
  stage: check
  needs: [install]
  cache: { <<: *pnpm-cache, policy: pull }
  <<: *setup
  script: [pnpm test]

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

On GitHub Actions the shape is identical; swap the cache mechanism for `actions/cache`.

## GitHub Actions skeleton for Tauri desktop builds

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
