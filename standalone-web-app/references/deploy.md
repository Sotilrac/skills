# Deploy, analytics, and privacy

Referenced from `SKILL.md`. Read when setting up deploys or getting ready to ship.

## Cloudflare Pages via wrangler

1. Add `wrangler` to root devDeps: `pnpm add -Dw wrangler`.
2. Create the Pages project interactively: `pnpm exec wrangler login`, then `pnpm exec wrangler pages project create <name> --production-branch=main`.
3. Add a script to root `package.json`:

   ```json
   "deploy:pages": "wrangler pages deploy packages/web/dist --project-name=<name> --branch=main --commit-dirty=true"
   ```

4. Add a `deploy` Makefile target: depends on `build`, then runs `deploy:pages`.
5. In CI, a `deploy:cloudflare` job on the default branch runs `pnpm run deploy:pages`. The job reads `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` from masked CI variables; don't commit them.
   - **Creating the token**: Cloudflare dashboard → My Profile → API Tokens → Create Token. Start from the "Edit Cloudflare Workers" template, then add the `Cloudflare Pages: Edit` permission. That single token covers both Pages and Workers deploys.
   - **Account ID**: visible in the right sidebar of any domain page, or Workers & Pages → Overview.
6. For a custom domain, add the subdomain in the Cloudflare dashboard and either let Cloudflare manage the DNS or add a CNAME pointing at `<project>.pages.dev`.

## Cloudflare Workers (when the app needs a whisker of backend)

Sometimes "local-first" still needs a whisker of backend: a CORS proxy to a user's WebDAV or Nextcloud, a tiny auth step that encrypts and stashes credentials, or a rate-limited outbound call to an API that can't be called from the browser. In those cases, a **Cloudflare Worker** is the right shape:

- Deployed with the same `wrangler` CLI already in the repo.
- Use `itty-router` for request routing; keep the worker under ~300 lines total.
- Use **Workers KV** for anything you need to persist between requests (encrypted session tokens, rate-limit counters). Encrypt secrets with AES-GCM before writing; the key is a `wrangler secret`.
- Local dev secrets live in `worker/.dev.vars` (git-ignored); production secrets go through `wrangler secret put`.
- Separate workspace: `packages/worker/` with its own `package.json`, `wrangler.toml`, and small test suite. The worker's routes are request/response functions, easy to unit-test with `Request` / `Response` constructors, no mock server needed.

When you don't need a backend, don't build one. Most apps in this skill's scope don't.

## Analytics

Umami (cookieless, GDPR-friendly) is the default. Add the script to `index.html`, disable auto-track, prefix the URL path when multiple sites share one Umami site:

```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="WEBSITE_ID"></script>
```

If the app has real SPA routes, also hook `popstate` to re-fire the tracker with the new path.

## Privacy files (robots.txt and llms.txt)

Drop both under `packages/web/public/`. Vite copies them to `dist/` verbatim.

- `robots.txt`: start from the sample at `${CLAUDE_SKILL_DIR}/references/robots.txt` (allows search indexing, blocks AI-training bots). Refresh the bot list when you use it.
- `llms.txt`: a short markdown file per llmstxt.org. Title, one-line blurb, then sections for what it is, privacy, data model, stack, and a "training not permitted, see /robots.txt" line.
