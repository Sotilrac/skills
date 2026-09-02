#!/usr/bin/env python3
"""Check an Android repo against what F-Droid's tooling and reviewers require.

Every rule here comes from something that bit a real submission: a build that failed on archives in
the source tree, a checkupdates that could not read the version, listing metadata in a directory
fdroidserver never scans, a changelog over the limit, and an in-repo recipe that drifted a release
behind. Nothing here needs fdroidserver installed, so it is cheap enough to run from a pre-push hook.

    python3 check_repo.py                                  # from the repo root
    python3 check_repo.py --repo ~/dev/app --recipe fdroid/com.example.app.yml

Exit status is 1 if anything failed, 0 otherwise. Warnings never fail the run.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# fdroidserver's own regexes (common.py parse_androidmanifests). It reads the version straight out of
# the gradle file and takes only a plain literal; anything computed is invisible to it.
VERSION_CODE = re.compile(r"""\b[Vv]ersionCode\s*=?\s*["'(]*([0-9][0-9_]*)["')]*""")
VERSION_NAME = re.compile(r"""\b[Vv]ersionName\s*=?\s*(["'])((?:(?=(\\?))\3.)*?)\1""")
APPLICATION_ID = re.compile(r"""\bapplicationId\s*=?\s*["']([A-Za-z0-9_.]+)["']""")

# fdroid's scanner walks the whole checkout, not just what ships.
BANNED_SUFFIXES = (".zip", ".aar", ".apk", ".aab", ".dex", ".so", ".swf", ".ai", ".7z", ".rar")
BANNED_NAMES = ("Thumbs.db", ".DS_Store")
ALLOWED_JARS = ("gradle/wrapper/gradle-wrapper.jar",)

# fdroidserver common.py char_limits.
LIMITS = {"name": 50, "summary": 80, "description": 4000, "changelog": 500}

FULL_HASH = re.compile(r"^[0-9a-f]{40}$")


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def find_gradle(root: Path, files: list[str]) -> Path | None:
    """The module declaring applicationId is the one F-Droid builds."""
    candidates = [f for f in files if f.endswith(("build.gradle.kts", "build.gradle"))]
    candidates.sort(key=lambda f: (f.count("/"), f))
    for name in candidates:
        path = root / name
        try:
            if APPLICATION_ID.search(path.read_text(encoding="utf-8", errors="replace")):
                return path
        except OSError:
            continue
    return None


def check_tracked_tree(root: Path, files: list[str], report: Report) -> None:
    for path in files:
        name = path.rsplit("/", 1)[-1]
        if path.endswith(".jar") and path not in ALLOWED_JARS:
            report.fail(f"{path}: tracked jar; fdroid's scanner rejects it")
        if path.lower().endswith(BANNED_SUFFIXES):
            report.fail(f"{path}: fdroid's scanner rejects this file type in the source tree")
        if name in BANNED_NAMES:
            report.fail(f"{path}: editor or OS cruft, tracked")


def read_version(gradle: Path, report: Report) -> tuple[int | None, str | None, str | None]:
    text = gradle.read_text(encoding="utf-8", errors="replace")
    code = VERSION_CODE.search(text)
    name = VERSION_NAME.search(text)
    appid = APPLICATION_ID.search(text)
    rel = gradle.name
    if not code:
        report.fail(f"{rel}: no versionCode literal; checkupdates cannot read it")
    if not name:
        report.fail(f"{rel}: no versionName literal; checkupdates cannot read it")
    if "dependenciesInfo" not in text:
        report.warn(
            f"{rel}: no dependenciesInfo block; set includeInApk/includeInBundle = false for "
            "reproducible builds"
        )
    return (
        int(code.group(1).replace("_", "")) if code else None,
        name.group(2) if name else None,
        appid.group(1) if appid else None,
    )


def check_fastlane(root: Path, code: int | None, report: Report) -> None:
    base = root / "fastlane" / "metadata" / "android"
    if not base.is_dir():
        report.fail(
            "fastlane/metadata/android/<locale> missing at the checkout root; fdroidserver scans "
            "the root, not the gradle module directory"
        )
        return
    locales = sorted(d for d in base.iterdir() if d.is_dir())
    if not locales:
        report.fail(f"{base}: no locale directories")
        return
    if not any(d.name.startswith("en") for d in locales):
        report.warn(
            "fastlane: no en-* locale; F-Droid expects English or a declaration in the description"
        )

    for locale in locales:
        tag = f"fastlane/{locale.name}"
        for required in ("title.txt", "short_description.txt", "full_description.txt"):
            if not (locale / required).is_file():
                report.fail(f"{tag}: {required} missing")
        for filename, limit_key in (
            ("title.txt", "name"),
            ("short_description.txt", "summary"),
            ("full_description.txt", "description"),
        ):
            path = locale / filename
            if path.is_file():
                length = len(path.read_text(encoding="utf-8").strip())
                if length > LIMITS[limit_key]:
                    report.fail(
                        f"{tag}: {filename} is {length} chars, over the {LIMITS[limit_key]} limit"
                    )
        for changelog in sorted((locale / "changelogs").glob("*.txt")):
            length = len(changelog.read_text(encoding="utf-8").strip())
            if length > LIMITS["changelog"]:
                report.fail(
                    f"{tag}: changelogs/{changelog.name} is {length} chars, over the "
                    f"{LIMITS['changelog']} limit"
                )
        if code is not None and not (locale / "changelogs" / f"{code}.txt").is_file():
            report.fail(f"{tag}: changelogs/{code}.txt missing for the current versionCode")

    icons = list(base.glob("*/images/icon.png"))
    if not icons:
        report.fail("fastlane: no images/icon.png in any locale")


def check_recipe(path: Path, code: int | None, name: str | None, report: Report) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.name

    current_name = re.search(r"^CurrentVersion:\s*(\S+)", text, re.M)
    current_code = re.search(r"^CurrentVersionCode:\s*(\d+)", text, re.M)
    if current_name and name and current_name.group(1) != name:
        report.fail(f"{rel}: CurrentVersion {current_name.group(1)} does not match {name}")
    if current_code and code is not None and int(current_code.group(1)) != code:
        report.fail(f"{rel}: CurrentVersionCode {current_code.group(1)} does not match {code}")

    commits = re.findall(r"^\s*commit:\s*(\S+)", text, re.M)
    for commit in commits:
        if not FULL_HASH.match(commit):
            report.fail(
                f"{rel}: commit '{commit}' is not a full 40-character hash; maintainers reject "
                "tags and branches because they are mutable"
            )
    entries = len(re.findall(r"^\s*-\s*versionName:", text, re.M))
    if entries > 1:
        report.warn(
            f"{rel}: {entries} Builds entries; a new-app submission carries one, the current release"
        )
    if entries and code is not None and f"versionCode: {code}" not in text:
        report.fail(f"{rel}: no Builds entry for the current versionCode {code}")

    if "Binaries:" in text and "AllowedAPKSigningKeys:" not in text:
        report.fail(f"{rel}: Binaries without AllowedAPKSigningKeys; the comparison has no key")
    if "AutoName:" not in text:
        report.warn(
            f"{rel}: no AutoName; checkupdates regenerates it and fdroiddata's CI fails on the diff"
        )
    if "scanignore" in text or "scandelete" in text:
        report.warn(f"{rel}: scanignore/scandelete present; reviewers read these as a smell")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=None, help="repo root (default: git toplevel)")
    parser.add_argument("--gradle", type=Path, default=None, help="the app module's build script")
    parser.add_argument("--recipe", type=Path, default=None, help="in-repo copy of the recipe")
    args = parser.parse_args()

    root = args.repo
    if root is None:
        try:
            root = Path(
                subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            root = Path.cwd()
    root = root.resolve()

    report = Report()
    files = tracked_files(root)
    check_tracked_tree(root, files, report)

    gradle = args.gradle if args.gradle else find_gradle(root, files)
    if gradle is None:
        report.fail("no build script declaring applicationId found; pass --gradle")
        code = name = appid = None
    else:
        code, name, appid = read_version(root / gradle if not gradle.is_absolute() else gradle, report)

    check_fastlane(root, code, report)

    recipe = args.recipe
    if recipe is None and appid:
        for guess in (root / "fdroid" / f"{appid}.yml", root / "metadata" / f"{appid}.yml"):
            if guess.is_file():
                recipe = guess
                break
    if recipe is not None:
        recipe = recipe if recipe.is_absolute() else root / recipe
        if recipe.is_file():
            check_recipe(recipe, code, name, report)
        else:
            report.fail(f"{recipe}: recipe not found")

    for warning in report.warnings:
        print(f"warning: {warning}")
    if report.failures:
        print("F-Droid checks failed:")
        for failure in report.failures:
            print(f"  {failure}")
        return 1
    label = f"{name} / {code}" if name else "no version"
    print(f"F-Droid checks passed ({appid or 'unknown appid'}, {label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
