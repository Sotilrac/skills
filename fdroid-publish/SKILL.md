---
name: fdroid-publish
description: Get an Android app into F-Droid and keep it there. Covers the fdroiddata metadata recipe (Builds entries, full commit hashes, AutoName, rewritemeta formatting), fastlane listing at the repo root, reproducible builds via Binaries + AllowedAPKSigningKeys, a tag-driven signed release pipeline, and the inclusion review checklist that actually decides the outcome. Use whenever F-Droid, fdroiddata, an inclusion request or RFP, a metadata .yml recipe, checkupdates, fdroid lint/rewritemeta/build, or an F-Droid reviewer's comment comes up, and whenever someone wants their Android app published somewhere other than a proprietary store.
---

# Publishing to F-Droid

Two repositories are in play and confusing them wastes weeks:

- **your app repo**, which carries the listing text (`fastlane/`), the version literals, and the release pipeline;
- **[fdroiddata](https://gitlab.com/fdroid/fdroiddata)**, whose `metadata/<applicationId>.yml` recipe tells F-Droid's build farm how to build you. You submit a merge request against it and a human reviews the app on a device.

Inclusion is decided by that human, not by CI. CI only stops you from wasting their time.

## Reference files (load on demand)

- `${CLAUDE_SKILL_DIR}/references/recipe.md` — every recipe field that matters, the rules maintainers enforce by hand, the fdroiddata CI jobs, and how to reproduce them locally. **Read before writing or editing a recipe.**
- `${CLAUDE_SKILL_DIR}/references/review.md` — the reviewer's checklist, what fails it, and how to answer review comments. **Read before submitting, and again when a review lands.**
- `${CLAUDE_SKILL_DIR}/references/releases.md` — tag-driven signed builds, reproducible builds, and shipping later versions once you are in.

## Order of work

1. **Prepare the app repo** (below), then run `scripts/check_repo.py`. Everything it catches is something a reviewer or the build farm would have caught later, more slowly.
2. **Cut a tag** and publish a signed APK, if you want reproducible builds and your own signature. See `references/releases.md`. Do this before writing the recipe: the recipe pins the tag's commit.
3. **Write the recipe** and verify it locally with `fdroid lint`, `fdroid rewritemeta`, `fdroid build`. See `references/recipe.md`.
4. **Open the MR** against fdroiddata from a branch named exactly the applicationId, then wait. The queue is long, months rather than days.
5. **Answer the review.** See `references/review.md`.

## Preparing the app repo

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_repo.py          # run from the repo root
python3 ${CLAUDE_SKILL_DIR}/scripts/check_repo.py --recipe fdroid/com.example.app.yml
```

Wire it into the project's own `make` target or pre-push hook, so the contract is enforced by the repo rather than remembered.

What it checks and why each one bites:

- **`fastlane/metadata/android/<locale>/` sits at the checkout root.** fdroidserver scans the root for `fastlane/`, not the Gradle module directory. Put it under `app/` and your listing is silently empty.
- **`versionCode` and `versionName` are plain literals** in the module's `build.gradle.kts`. `checkupdates` regex-parses that file to propose each new release and discards anything computed, so a version read from `gradle.properties` or derived from git means every future release is a manual MR.
- **A changelog per release**, `changelogs/<versionCode>.txt`. Named by code, not by name.
- **Character limits**, enforced by `fdroid lint`: name 50, summary 80, description 4000, changelog 500.
- **No archives or binaries anywhere in the tracked tree.** The scanner walks the whole checkout, not just what ships: `.jar` (except `gradle/wrapper/gradle-wrapper.jar`), `.zip`, `.aar`, `.apk`, `.so`, `.dex`, `.swf`, `.ai`, plus `Thumbs.db` and `.DS_Store`. Vendored design sources and editor cruft are the usual offenders. Delete them rather than arguing for a `scanignore:`, which reviewers read as a smell.

Also, not mechanically checkable:

- **Build unsigned when no keystore is present.** F-Droid builds your source without your secrets, so make the signing config conditional on the credentials existing. A release build that fails without a keystore fails on the build farm.
- **Keep a FOSS product flavor** if any variant pulls proprietary dependencies, and point the recipe at it with `gradle: [foss]`. No Google Play Services, no Firebase, no proprietary maps SDK in the built variant.
- **Say what the app does over the network, in the listing.** The reviewer runs a packet capture. Anything they see that the description does not mention becomes an anti-feature discussion.

## The five mistakes that cost the most

1. **Pinning `commit:` to a tag name or to HEAD.** It must be the full 40-character hash, and it must be the commit the tag points at. Tags are mutable, so maintainers reject them outright; and AGP stamps the checked-out revision into the APK, so a hash one commit off breaks reproducibility. `git rev-list -n 1 v1.2.3`.
2. **Shipping a recipe with a `Builds:` history.** A new-app MR builds one version, the current one. Old entries mean the farm builds and publishes releases nobody asked for.
3. **Formatting the recipe with your installed fdroidserver.** fdroiddata's CI installs fdroidserver from **master**, and its `rewritemeta` disagrees with released versions about things like line folding. Reproduce CI's version locally (`references/recipe.md`) or just read the failing job's diff.
4. **Prompting for runtime permissions at startup.** The checklist has a box for "usable without granting optional runtime permissions". Ask when the feature is switched on, never on first launch.
5. **An app the reviewer cannot exercise.** They test indoors, on one device, in about an hour. If your core loop needs GPS, a camera, or a server, ship the instructions that let them drive it and make sure injected/mock input actually works.

## Anti-patterns

- Opening a second MR for a new release. Push to the same branch; the MR updates in place.
- Answering a review comment with a claim instead of evidence. "It works offline" loses; "capture with the setting off shows zero bytes over 90 seconds" wins.
- Treating non-blocking review remarks as optional. They are the difference between a merge this month and another round trip.
- Hand-editing formatting that `rewritemeta` owns, or hand-setting fields (`AutoName`) that `checkupdates` regenerates, in either direction. Match what the tools produce.
- Adding `scanignore:`/`scandelete:` to get a dirty tree past the scanner.
