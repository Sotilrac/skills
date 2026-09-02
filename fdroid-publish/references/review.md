# Passing the inclusion review

A person installs your published APK on a real device, runs a packet capture, reads the source, and fills in a checklist. Their template is public (https://gitlab.com/fdroid/wiki/-/wikis/Internal/Reviewing-new-apps), so you can pass it before they ever open the MR. Unticked boxes are not necessarily rejections, but each one is a round trip, and the queue between round trips is months.

## The checklist, and what leaves each box empty

**Basic function**
- *The app can start and work normally.*
- *The functions in the description are implemented.* This is the box that fails on apps that work fine, because the reviewer could not exercise the core loop. See "Make it testable" below.
- *The app has a unique icon.*

**Policy compliance**
- *Features don't violate the Inclusion Policy.*
- *The Categories field is set properly.* Match F-Droid's official category descriptions, not the words' plain meaning.
- *Doesn't require accepting terms other than the FOSS licence.*

**Permissions**
- *The app can be used without granting optional runtime permissions.* Requesting anything on first launch fails this. Background location, notifications and the battery-optimisation exemption all count, and prompting them before the user has touched anything fails it three times over. Open to a usable screen with nothing granted, and request each permission at the moment its feature is switched on. A "start tracking" call to action that triggers the request is the shape they are looking for.
- *No unnecessary `MANAGE_EXTERNAL_STORAGE`.* Use SAF.

**Network connections**
- *Connections described clearly in the description.* They compare a capture against your listing text. Any host they see that you did not mention becomes an anti-feature conversation.
- *No automatic update check, no tracking domains, no unnecessary connections* (online fonts, icons, connectivity checks), *no in-app webview* for what belongs in a browser.

**Language support**: English, or declare otherwise in the description.

**Security scan**: VirusTotal or similar on the published APK.

## Anti-features, and how to avoid earning one

A network connection at launch invites `NonFreeNet` (depends on a proprietary service) and `TetheredNet` (useless without a specific server). You avoid both by being genuinely optional and provable:

- Make the online layer a setting, and make the app fully functional with it off. "Fully functional" means the core loop, not a degraded shell.
- Let the user point at their own instance of each service. A hardcoded host is what `TetheredNet` describes; a configurable endpoint is not tied to anyone.
- Answer with a measurement, not an assertion: a capture filtered to the package showing zero bytes over 90 seconds of real use, with the setting off.

`Tracking` needs no telemetry, no crash reporting, no update check. `NonFreeAssets` needs every bundled font, icon set and data pack to carry a free licence and attribution.

## Attribution and provenance

Reviewers grep the checkout for licence text and find nothing surprisingly often. Before submitting:

- Attribute the data your app renders, in the app and in the listing. For OSM: "© OpenStreetMap contributors", ODbL, on the map surface itself and not only in a settings screen.
- Ship the licence texts of bundled assets (OFL for a font, CC0 for an art pack) and a `THIRD_PARTY.md` mapping each shipped file to its licence and upstream source. A font's licence often lives only in its `name` table, where nobody will look.
- Give bundled content packs a `source` and `license` field, and assert their presence in a test so a new pack cannot land without provenance.
- Add an About screen listing the app version, its licence, and one line per dependency and data source. Reviewers ask for this by name.

## Make it testable

The most common way for a working app to stall: the reviewer tests indoors, gets no GPS fix, injects locations with `adb`, sees nothing happen, and leaves *"the functions in the description are implemented"* empty with a note saying so.

Fix the code first, then document it:

- Subscribe to provider callbacks (`onProviderEnabled`/`onProviderDisabled`), not just a snapshot of `isProviderEnabled` taken at registration. A test provider added after your app started otherwise never gets subscribed to, and neither does a real user toggling GPS off and on.
- Know your own filters and write them down: a minimum-distance filter drops a repeatedly-pushed static point before it reaches your code; an accuracy threshold discards fixes whose accuracy is not set; a stillness watchdog that parks the receiver keeps a phone on a desk dormant.
- Ship `docs/testing-locations.md` with the exact `adb` sequence, which provider to inject into, how far apart successive points must be, what accuracy to set, and how to keep the receiver awake. Link it from the MR.

The same reasoning applies to anything else the reviewer cannot reach: a server integration needs a test instance or a described path to skip it.

## Keeping the listing honest

The listing is reviewed as a claim about the app, so stale text is a finding:

- No "early v0.1 release" once it is not.
- Nothing shipped listed under "Planned", and nothing planned listed as shipped.
- No "offline" next to a feature that queries a server.
- Mention the backup, sync or export paths that touch the network.
- Rewrite old changelogs that advertise properties you no longer have ("no network permission").

## Answering a review

- Reply per point, in the reviewer's order, saying what changed and where. They are volunteers reading many MRs.
- Bring evidence: a capture, a hash, a pipeline link, a commit.
- Fix the non-blocking remarks too. They are cheap now and another round trip later.
- Ship the fixes as a new release and update the same MR: push to the same branch, bump `Builds`/`CurrentVersion`, then comment saying it is updated. Do not open a second MR.
- When a maintainer states a rule (one build entry, full commit hashes), comply rather than explaining why your way is defensible. They apply the same rule across thousands of apps.
