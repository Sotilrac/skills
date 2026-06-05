# Publishing to the Nextcloud App Store

Three one-time setup steps, then tag-driven releases. The naive CI release fails in several non-obvious ways; the gotchas below are why the pipeline looks the way it does.

## One-time setup

1. **Certificate.** PR to `nextcloud/app-certificate-requests` with a CSR whose CN == app id. When merged, fetch the signed cert. Key + cert live in `~/.nextcloud/certificates/<appid>.{key,crt}`. Verify they match (`openssl rsa -modulus` vs `openssl x509 -modulus`).

2. **Register the app** (separate from the cert). POST the public cert + a signature of the app id:

   ```bash
   SIG=$(printf '%s' "$APPID" | openssl dgst -sha512 -sign "$KEY" | openssl base64 -A)
   curl -X POST https://apps.nextcloud.com/api/v1/apps \
     -H "Authorization: Token $TOKEN" -H 'Content-Type: application/json' \
     -d "$(jq -n --arg c "$(cat $CERT)" --arg s "$SIG" '{certificate:$c,signature:$s}')"
   ```

   Expect `201`. Skipping this gives `400 "App <id> does not exist, you need to register it first"` at publish time.

3. **CI variables.** `NC_SIGNING_KEY` (file type, the private key; PEM can't be masked). `NC_APPSTORE_TOKEN` (masked; from apps.nextcloud.com/account/token). Use **token-header auth** (`Authorization: Token …`) — GitHub-login accounts have no password for basic auth.

## Release flow

Bump `<version>` in `appinfo/info.xml`, then `git tag -a nc-vX.Y.Z && git push --tags`. The tag version must equal `info.xml`'s version.

## CI: two jobs, not one

The App Store **fetches the `download` URL to verify the signature**, so the tarball must be publicly reachable *before* the POST. GitLab's `release:` keyword runs *after* the job script — too late. Hence:

- **package job** (build stage): build, pack, sign → save tarball + `.sig` as a permanent public artifact (`expire_in: never`).
- **release job** (deploy stage, `needs:` the package): resolve the package job's artifact URL, create the GitLab Release, then POST to the App Store. By the time it runs, the artifact URL is live.

## The download URL — four gotchas

1. **`variables:` can't strip prefixes.** GitLab does `$VAR` substitution only, not `${VAR#nc-v}`. `APP_VERSION` ends up empty → `loanledger-.tar.gz`. Derive it in the shell: `APP_VERSION="${CI_COMMIT_TAG#nc-v}"`.
2. **Generic Package Registry isn't anonymous** even on public projects (404). The App Store can't fetch it.
3. **The App Store requires the URL to end in `.tar.gz` with no query string.** The `?job=` "latest artifacts" by-ref URL fails this check (and 404s unless keep-latest-artifacts is on).
4. **Use the job-id artifact URL**, resolved at runtime — it ends in `.tar.gz`, has no query, and is anonymously downloadable:

   ```bash
   PKG_JOB_ID=$(curl -sS "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs?per_page=100" \
     | jq -r '.[]|select(.name=="<package-job>").id' | head -n1)
   DOWNLOAD="$CI_PROJECT_URL/-/jobs/$PKG_JOB_ID/artifacts/raw/$OUT_DIR/$TAR_NAME"
   ```

## Release-job skeleton

```yaml
nextcloud-package:
  stage: build
  rules: [{ if: '$CI_COMMIT_TAG =~ /^nc-v\d+\.\d+\.\d+$/' }]
  image: node:24-bookworm
  variables: { OUT_DIR: dist }
  before_script:
    - apt-get update -q && apt-get install -y -q php-cli php-xml php-zip php-mbstring composer rsync libxml2-utils curl openssl
    - corepack enable && corepack prepare pnpm@<ver> --activate && pnpm install --frozen-lockfile
    # --no-scripts: post-install runs the bamarni bin plugin (dev-only, absent under --no-dev)
    - composer install --no-progress --no-dev --no-scripts --working-dir=packages/nextcloud
    - pnpm --filter <ncpkg> build
  script:
    - APP_VERSION="${CI_COMMIT_TAG#nc-v}"; TAR="loanledger-$APP_VERSION.tar.gz"
    - curl -s https://apps.nextcloud.com/schema/apps/info.xsd -o /tmp/info.xsd
    - xmllint --schema /tmp/info.xsd packages/nextcloud/appinfo/info.xml --noout
    - mkdir -p $OUT_DIR/loanledger
    - rsync -a --exclude-from=packages/nextcloud/.nextcloudignore --exclude=node_modules --exclude=tests --exclude=src packages/nextcloud/ $OUT_DIR/loanledger/
    - tar -czf "$OUT_DIR/$TAR" -C "$OUT_DIR" loanledger
    - openssl dgst -sha512 -sign "$NC_SIGNING_KEY" "$OUT_DIR/$TAR" | base64 -w0 > "$OUT_DIR/$TAR.sig"
  artifacts: { paths: ["$OUT_DIR/loanledger-*.tar.gz", "$OUT_DIR/loanledger-*.tar.gz.sig"], expire_in: never }

release:nextcloud:
  stage: deploy
  needs: ['nextcloud-package']
  rules: [{ if: '$CI_COMMIT_TAG =~ /^nc-v\d+\.\d+\.\d+$/' }]
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  variables: { OUT_DIR: dist }
  before_script: [apk add --no-cache curl jq]
  script:
    - APP_VERSION="${CI_COMMIT_TAG#nc-v}"; TAR="loanledger-$APP_VERSION.tar.gz"; SIG=$(cat "$OUT_DIR/$TAR.sig")
    - PKG_JOB_ID=$(curl -sS "$CI_API_V4_URL/projects/$CI_PROJECT_ID/pipelines/$CI_PIPELINE_ID/jobs?per_page=100" | jq -r '.[]|select(.name=="nextcloud-package").id' | head -n1)
    - DOWNLOAD="$CI_PROJECT_URL/-/jobs/$PKG_JOB_ID/artifacts/raw/$OUT_DIR/$TAR"
    # idempotent: re-tagging reruns this job
    - 'curl -sS --request DELETE --header "JOB-TOKEN: $CI_JOB_TOKEN" "$CI_API_V4_URL/projects/$CI_PROJECT_ID/releases/$CI_COMMIT_TAG" || true'
    - |
      release-cli create --name "App $CI_COMMIT_TAG" --tag-name "$CI_COMMIT_TAG" \
        --assets-link "{\"name\":\"$TAR\",\"url\":\"$DOWNLOAD\",\"link_type\":\"package\"}"
    - |
      CODE=$(curl -sS -o /tmp/r.json -w '%{http_code}' -X POST \
        -H 'Content-Type: application/json' -H "Authorization: Token $NC_APPSTORE_TOKEN" \
        https://apps.nextcloud.com/api/v1/apps/releases \
        -d "$(jq -n --arg u "$DOWNLOAD" --arg s "$SIG" '{download:$u,signature:$s,nightly:false}')")
      echo "App Store HTTP $CODE:"; cat /tmp/r.json; echo
      case "$CODE" in 200|201) ;; *) exit 1 ;; esac
```

Always echo the App Store response body — `curl -f` hides it, and the 400s are specific and actionable ("not a valid tar.gz archive", "does not exist", signature errors).

## After a green run

`201` = accepted. The **first** release sits in Nextcloud's manual review queue before it appears in the public `apps.json` / inside servers. Subsequent releases are automatic on tag. To re-run after fixing CI without re-tagging, retry just the release job (the package artifact and release already exist).
