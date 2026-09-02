# Releases, signatures and reproducible builds

## Two ways your app can be signed

**F-Droid signs it.** The default. F-Droid builds from source and signs with its own key. Simple, and the cost is that an APK you distribute yourself and the F-Droid one are different apps to Android: switching between them means uninstalling and losing app data.

**Reproducible build.** F-Droid builds from source, compares its output against a signed APK you publish, and on a bit-for-bit match ships *your* binary with *your* signature. Users move between your download page and F-Droid freely. This is worth the setup for any app people already installed from your own releases.

To opt in:

```yaml
Binaries: https://gitlab.com/api/v4/projects/82820309/packages/generic/foggy-maps/v%v/foggy-maps-v%v.apk
AllowedAPKSigningKeys: cd3714b78453756591ccf6ed26b691e7931ff8166f2159486551d42699307197
```

`%v` expands to `versionName` and `%c` to `versionCode`, so one URL template serves every release. It must resolve for every version in `Builds:`, forever, which rules out anything you might garbage-collect. A package registry or release asset works; a personal web server you might reorganise does not.

`AllowedAPKSigningKeys` is the SHA-256 of the **signing certificate**, not of the APK:

```bash
apksigner verify --print-certs app-release.apk | grep -i 'SHA-256 digest'
```

## Making the build reproducible

The comparison is byte-level, so anything varying between your machine and the build farm breaks it:

- `dependenciesInfo { includeInApk = false; includeInBundle = false }`. AGP otherwise embeds a signed dependency blob.
- Pin the toolchain: `compileSdk`, `targetSdk`, the AGP and Kotlin versions in a lockfile or version catalogue, and the Gradle wrapper. The farm honours these; drifting versions produce different bytecode.
- Nothing in the APK may carry a timestamp, hostname, build path or git description. `BuildConfig` fields holding the version string are fine; ones holding the build time are not.
- Export generated schemas (Room, for example) into the tree so annotation processing is deterministic.

**The mistake that breaks it most often** is not in the build at all: pinning `commit:` to the commit *before* the tag. AGP stamps the checked-out revision into the APK, so the farm's build differs from the one you signed at the tag. Pin the tag's own commit, resolved with `git rev-list -n 1 v1.2.3`.

## Version discipline

`versionCode` and `versionName` in the module's `build.gradle.kts` are the single source of truth, as plain literals. Everything else derives from them: the tag, the changelog filename, the recipe, the `Binaries` URL. Bump both in one commit when cutting a release, and have CI assert that the tag matches the `versionName` literal so a mis-tagged commit fails loudly instead of publishing a mislabelled APK.

Batch the whole release locally, then push `main` and the tag together in one go. Pushing mid-release runs a pipeline on work that is not finished, and if the tag pipeline is what publishes the APK, a second push usually cancels the first.

## A tag-driven signed pipeline (GitLab)

Fire pipelines on tags only, so a release is one pipeline and branch work is gated by local hooks instead:

```yaml
workflow:
  rules:
    - if: '$CI_COMMIT_TAG'
      when: always
    - when: never
```

Then three stages: `verify` (lint, tests), `package` (signed release APK, uploaded to the generic package registry at the URL `Binaries:` expects), `release` (a GitLab Release linking the artifact).

Inside `package`, in this order:

1. Refuse to run if `$CI_COMMIT_REF_PROTECTED != true`. The signing variables are protected, so this turns a silently unsigned build into a loud failure.
2. Assert `${CI_COMMIT_TAG#v}` equals the `versionName` literal in the Gradle file.
3. Materialise the keystore: `echo "$KEYSTORE_BASE64" | base64 -d > release.jks` (store it as `base64 -w0 release.jks` in a masked, protected variable), and export its path.
4. Assemble the release variant, copy the APK to a versioned name, `curl --upload-file` it to `${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/generic/<name>/${CI_COMMIT_TAG}/<file>.apk`.

Gradle maps `ORG_GRADLE_PROJECT_FOO` environment variables onto the `FOO` project properties your build script reads, which is the clean way to get passwords in without a properties file.

Protect the tag pattern (`v*`) in repository settings and mark every signing variable masked and protected, so the keystore is only ever exposed to a tag pipeline on a protected ref.

**Keep signing conditional.** Read the credentials as optional Gradle properties and create the signing config only when they are present, leaving the release unsigned otherwise. F-Droid builds your source without your secrets, and a build script that requires a keystore fails on the farm.

## After inclusion

With `UpdateCheckMode: Tags` and `AutoUpdateMode: Version` in place, `checkupdates` sees each new tag and proposes the recipe change on its own. Your release process is then: bump the literals, write `changelogs/<versionCode>.txt`, tag, push. Nothing to do in fdroiddata.

You go back to fdroiddata by hand only when something structural changes: a new flavor or `subdir`, a new dependency the scanner objects to, a signing key rotation, or a listing change large enough to want the maintainers to see it. Anything that alters `Builds:` in a way a regex cannot derive is a fresh MR against the same file.
