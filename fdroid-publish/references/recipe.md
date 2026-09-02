# The fdroiddata recipe

One file, `metadata/<applicationId>.yml`, in a fork of https://gitlab.com/fdroid/fdroiddata. Branch name is the applicationId. Full field reference: https://f-droid.org/docs/Build_Metadata_Reference/

## A complete recipe

This is a real one, for an app that publishes its own signed APKs and wants F-Droid to reuse that signature:

```yaml
Categories:
  - Navigation
  - Sports & Health
License: AGPL-3.0-or-later
AuthorName: Carlos Asmat
AuthorWebSite: https://asmat.ca
SourceCode: https://gitlab.com/sotilrac/foggy-maps
IssueTracker: https://gitlab.com/sotilrac/foggy-maps/-/issues

AutoName: Foggy Maps

RepoType: git
Repo: https://gitlab.com/sotilrac/foggy-maps.git
Binaries: 
  https://gitlab.com/api/v4/projects/82820309/packages/generic/foggy-maps/v%v/foggy-maps-v%v.apk

Builds:
  - versionName: 1.7.0
    versionCode: 18
    commit: 9de0d0d48d5518bc48bb80c2b87f8e12d74ac90c
    subdir: app
    gradle:
      - foss

AllowedAPKSigningKeys: cd3714b78453756591ccf6ed26b691e7931ff8166f2159486551d42699307197

AutoUpdateMode: Version
UpdateCheckMode: Tags ^v\d+\.\d+\.\d+$
CurrentVersion: 1.7.0
CurrentVersionCode: 18
```

No listing text, icon or screenshots appear here. F-Droid reads those from `fastlane/metadata/` in your own repo at build time.

## Fields that need explaining

**`Categories`** must match F-Droid's own category descriptions, not your reading of the words. `Science & Education` means "learning, studying, reference, and educational apps"; a fitness tracker with a map is `Sports & Health` and `Navigation`. A wrong category is one of the checklist boxes and gets caught every time.

**`AutoName`** has to be committed even though it looks redundant: `checkupdates` regenerates it from the manifest and the CI job fails on any diff it produces. Dropping it guarantees a red pipeline. (Reviewers sometimes suggest dropping it. The CI is the authority.)

**`Builds`** is a list, but a new-app MR carries exactly one entry, the current release. Maintainer instruction, verbatim: "Remove old versions."

**`commit`** is the full 40-character hash. Never a tag name, never a branch: those are mutable, so they do not pin anything, and maintainers ask for the hash on sight. Resolve it from the tag rather than from your local HEAD:

```bash
git rev-list -n 1 v1.7.0                   # local
git ls-remote origin 'refs/tags/v1.7.0^{}' # what the world sees, for annotated tags
```

Take it from the tag itself and not from the commit before or after. AGP stamps the checked-out revision into the APK, so a hash one commit off produces a different binary and fails the reproducible-build comparison.

**`subdir`** is the Gradle module holding the application, usually `app`. **`gradle:`** names the product flavors to assemble (`- yes` when there are none).

**`Binaries`** plus **`AllowedAPKSigningKeys`** enable reproducible builds. See `releases.md`.

**`UpdateCheckMode: Tags <regex>`** with **`AutoUpdateMode: Version`** makes `checkupdates` propose every later release on its own, which is the whole point of keeping the version literals parseable. `CurrentVersion`/`CurrentVersionCode` track the newest release F-Droid should offer.

## Verify locally before pushing

```bash
fdroid lint com.example.app
fdroid rewritemeta com.example.app     # rewrites in place; commit whatever it produces
fdroid build com.example.app:18        # full build, slow, catches what lint cannot
```

`fdroid build` wants the Android SDK and a lot of patience. Run it at least once before the first submission.

### Match the fdroidserver that CI runs

fdroiddata's pipeline installs fdroidserver from a **master tarball**, not from a release, and `rewritemeta`'s formatting differs between them. A released 2.4.5 inlines a long `Binaries:` value; master folds it onto the next line after a bare `Binaries:` with a trailing space. Format with the wrong one and the `fdroid rewritemeta` job fails on the diff, while your local run says everything is fine.

```bash
git clone --depth 1 https://gitlab.com/fdroid/fdroidserver.git /tmp/fdroidserver
PATH=/tmp/fdroidserver:$PATH PYTHONPATH=/tmp/fdroidserver \
  fdroid rewritemeta com.example.app
```

Or push and read the diff the failing job prints. Either way, the tools decide the formatting; do not hand-tune it.

## What the MR pipeline runs

Nine jobs, all of which must be green:

| Job | What it means when it fails |
| :--- | :--- |
| `fdroid lint` | Field or char-limit violation. |
| `fdroid rewritemeta` | Your formatting differs from master's canonical output. |
| `checkupdates` | The version literals or `UpdateCheckMode` regex cannot be parsed. |
| `schema validation` | Unknown or misspelled field. |
| `fdroid build` | The farm cannot build your source. The real gate. |
| `check apk` | Scanner findings in the built APK, or a signature mismatch against `AllowedAPKSigningKeys`. |
| `check source code` | Scanner findings in the checkout, usually a tracked binary. |
| `git redirect` | `Repo`/`SourceCode` URL redirects; use the final URL. |
| `tools check scripts` | Unrelated to your app; a rerun usually clears it. |

## Keeping the in-repo copy

Keep a copy of the recipe in your own repo (`fdroid/<applicationId>.yml`) with the reasoning in comments, and check that its `CurrentVersion`/`CurrentVersionCode` still match the Gradle literals (`scripts/check_repo.py --recipe` does this). It drifts a release behind the moment you stop checking, and then someone copies the stale one into fdroiddata.
