#!/usr/bin/env python3
"""Flag words from the arriving cluster of the load-bearing study.

    scan.py docs/*.md scripts/nas-status        # prose, comments and docstrings
    scan.py --top 100 README.md                 # only the strongest tells
    echo "text" | scan.py -                     # a draft on the way past

The list is `words.tsv` beside this script: the thousand most characteristic words
of the vocabulary cluster that went from 0.7% of GitHub pull requests in 2025 to
39% by mid-2026. `lift` is how much more often the word appears inside that cluster
than outside it, so a high-lift hit is a tell and a low-lift hit is close to
ordinary English. Nothing here is a banned word: the finding is about density, and
one `carries` in a page of prose is not the thing the study measured.

Only prose is read. Fenced blocks, inline code and URLs come out of markdown; in
source files only comments and docstrings are looked at, because `zfs holds` and
`obj.settles()` are not register.
"""

import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tropes import structural  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = os.path.join(HERE, os.pardir, "words.tsv")

# the study's own tokeniser: a run of letters, digits, slashes, hyphens and
# underscores containing at least one letter, so `load-bearing` and `snake_case`
# survive whole. Matching it matters -- splitting on punctuation first would look
# up `bearing`, which is not in the list, instead of `load-bearing`, which is top
# of it.
WORD_RE = re.compile(r"[a-z0-9_/-]*[a-z][a-z0-9_/-]*")
URL_RE = re.compile(r"https?://[^\s<>\"'`)\]}]+")

ADVICE = {
    "cut": "delete it; the sentence means the same without it",
    "agency": "an object given a person's verb: name what it actually does",
    "figure": "a physical metaphor for an abstraction: say the plain thing",
    "rhetoric": "argument furniture: state the fact, drop the framing",
    "coinage": "an invented compound: use words that existed before the sentence",
    "impersonal": "an invented third party: name who, or use the passive",
    "tally": "a counted-out total: give the number or drop the count",
    "": "high-lift word from the cluster",
}


def load(top):
    """(word -> (rank, lift, category)), limited to the first `top` by lift."""
    out = {}
    with open(WORDS) as f:
        for line in f:
            if line.startswith("#"):
                continue
            rank, lift, cat, word = line.rstrip("\n").split("\t")
            if int(rank) >= top:
                break
            out[word] = (int(rank), float(lift), cat)
    return out


# ------------------------------------------------------------------ what is prose

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"`[^`]*`")

HASH = ("#", ("sh", "bash", "py", "yaml", "yml", "toml", "conf", "cfg", "ini", "mk", "rb", "pl"))
SLASH = ("//", ("ts", "tsx", "js", "jsx", "c", "h", "cpp", "hpp", "go", "rs", "java", "swift", "kt"))
PROSE_EXT = ("md", "markdown", "txt", "rst", "adoc")

SHEBANG = {"python": "py", "sh": "sh", "bash": "sh", "zsh": "sh", "perl": "pl",
           "ruby": "rb", "node": "js"}


def kind(path, text):
    """The extension to treat this file as.

    A repository of executables has no extensions on them: `scripts/nas-status`
    and `scripts/test-nas-app` are Python, and reading their extension gives "".
    That used to fall through to the prose branch, so every line of code in them
    was scanned as English and their scores were inflated by roughly a factor of
    two. The shebang is the answer the file already carries.
    """
    base = os.path.basename(path)
    if "." in base:
        return base.rsplit(".", 1)[-1].lower()
    if path == "-":
        return "md"
    first = text.split("\n", 1)[0]
    if first.startswith("#!"):
        for name, ext in SHEBANG.items():
            if name in first:
                return ext
        return "sh"                      # a shebang naming something else is still a script
    return ""                            # no extension and no shebang: read it as prose


def prose_lines(path, text):
    """(lineno, text) for every line whose content is prose rather than code.

    A generator over lines rather than one blob, so a hit can be reported at the
    line it is on: an edit pass wants somewhere to go, not a count.
    """
    ext = kind(path, text)
    lines = text.split("\n")

    if ext in PROSE_EXT or ext == "":
        fenced = False
        for i, line in enumerate(lines, 1):
            if FENCE.match(line):
                fenced = not fenced
                continue
            if not fenced:
                yield i, line
        return

    for mark, exts in (HASH, SLASH):
        if ext in exts:
            for i, line in enumerate(lines, 1):
                # a comment marker inside a string is not a comment, and telling the
                # two apart needs a parser. An odd number of quotes before the marker
                # is the cheap version of that test: it skips `printf "#"` and keeps
                # the comments people write.
                #
                # URLs go first, and not as a nicety: `//` appears in every `http://`,
                # so `const u = "http://x"; // a real comment` found its marker inside
                # the string, counted one quote before it, and dropped the comment.
                probe = URL_RE.sub(lambda m: " " * len(m.group(0)), line)
                at = probe.find(mark)
                if at < 0:
                    continue
                before = probe[:at]
                if before.count('"') % 2 or before.count("'") % 2:
                    continue
                yield i, line[at + len(mark):]
            if ext in SLASH[1]:
                yield from block_comments(lines)
            return

    # unknown extension: read the whole thing as prose rather than skipping it,
    # which fails towards noise instead of towards silence
    for i, line in enumerate(lines, 1):
        yield i, line


def block_comments(lines):
    """`/* ... */` runs, which the line scan above cannot see past its opener."""
    inside = False
    for i, line in enumerate(lines, 1):
        if inside:
            end = line.find("*/")
            yield i, line if end < 0 else line[:end]
            inside = end < 0
            continue
        start = line.find("/*")
        if start < 0:
            continue
        end = line.find("*/", start)
        if end < 0:
            inside = True
            yield i, line[start + 2:]
        else:
            yield i, line[start + 2:end]


def docstrings(text):
    """(lineno, text) for Python triple-quoted strings.

    Every triple-quoted string, not only the ones in a docstring position: a module
    of triple-quoted blocks used as prose reads the same to a reader either way, and
    deciding which are docstrings needs the ast for no gain here.
    """
    for m in re.finditer(r'("""|\'\'\')(.*?)\1', text, re.S):
        base = text.count("\n", 0, m.start(2)) + 1
        for k, line in enumerate(m.group(2).split("\n")):
            yield base + k, line


# ------------------------------------------------------------------ the scan


def scan(path, text, table):
    """(words counted, vocabulary hits, trope hits)."""
    hits, words = [], 0
    lines = list(prose_lines(path, text))
    if kind(path, text) == "py":
        lines += list(docstrings(text))
    tropes = structural(lines)
    for lineno, line in lines:
        # inline code comes out here rather than in `prose_lines`, because the trope
        # checks above need the line as written: stripping `make dev` from the front
        # of a line left it starting with spaces, which read as an indented
        # continuation, which split the paragraph and reported its tail as a punchy
        # fragment. The vocabulary lookup is the only half that wants code gone.
        line = URL_RE.sub(" ", INLINE.sub(" ", line).lower())
        for w in WORD_RE.findall(line):
            w = w.strip("_/").rstrip("-")
            if not w:
                continue
            words += 1
            if w in table:
                rank, lift, cat = table[w]
                hits.append((lineno, w, rank, lift, cat))
    hits.sort(key=lambda h: (h[0], h[2]))
    return words, hits, tropes


# measured, not guessed: seven man pages of hand-written technical prose (bash, git,
# rsync, ssh, tar, systemd.unit, docker) average 1.0 vocabulary hits per 1,000 words
# at --top 150, and the sixteen documents of the repository that prompted this skill
# average 18.2.
BANDS = ((3.0, "ordinary prose"), (8.0, "the register is showing"),
         (float("inf"), "this is the cluster"))


def band(rate):
    return next(name for edge, name in BANDS if rate < edge)


def report(path, words, hits, tropes, args):
    """Print one file's findings and return its vocabulary rate."""
    rate = 1000 * len(hits) / words if words else 0.0
    t_rate = 1000 * len(tropes) / words if words else 0.0
    head = (f"{path}: {rate:5.1f} words/1k, {t_rate:5.1f} tropes/1k"
            f"  ({words} words)  {band(rate)}")

    if args.summary_only or not (hits or tropes):
        print(head)
        return rate

    print(f"{path}  ({words} words)")
    if hits and not args.tropes:
        print("  vocabulary")
        shown = sorted(hits, key=lambda h: h[2])[:args.limit]
        for lineno, w, rank, lift, cat in sorted(shown, key=lambda h: (h[0], h[2])):
            print(f"    {lineno:>5}  {w:<20} lift {lift:5.1f}, rank {rank + 1:<5} "
                  f"{ADVICE[cat]}")
        if len(hits) > args.limit:
            print(f"    ... and {len(hits) - args.limit} more")

    if tropes and not args.words:
        print("  tropes")
        by_trope = Counter(t[1] for t in tropes)
        for lineno, name, detail, note in tropes[:args.limit]:
            print(f"    {lineno:>5}  {name:<32} {detail:<46} {note}")
        if len(tropes) > args.limit:
            print(f"    ... and {len(tropes) - args.limit} more")
        print("    " + ", ".join(f"{n}x {t}" for t, n in by_trope.most_common(6)))

    spread = ", ".join(f"{n} {c or 'other'}"
                       for c, n in Counter(c for *_, c in hits).most_common())
    print(f"  {rate:.1f} words/1k ({spread}), {t_rate:.1f} tropes/1k, {band(rate)}\n")
    return rate


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="+", help="files to read, or - for stdin")
    p.add_argument("--words", action="store_true", help="vocabulary only")
    p.add_argument("--tropes", action="store_true", help="tropes only")
    p.add_argument("--top", type=int, default=150, metavar="N",
                   help="how many of the highest-lift words to count (default: 150, "
                        "which separates hand-written technical prose from the cluster "
                        "by 18x; 1000 for the whole list)")
    p.add_argument("--limit", type=int, default=40, metavar="N",
                   help="most hits of each kind to print per file (default: 40)")
    p.add_argument("--summary-only", action="store_true", help="one line per file")
    p.add_argument("--max-rate", type=float, default=None, metavar="R",
                   help="exit 1 if any file exceeds R vocabulary hits per 1,000 words")
    args = p.parse_args()

    table = load(args.top)
    worst = 0.0
    for path in args.paths:
        try:
            text = sys.stdin.read() if path == "-" else open(path, errors="replace").read()
        except OSError as e:
            print(f"{path}: {e}", file=sys.stderr)
            continue
        words, hits, tropes = scan(path, text, table)
        worst = max(worst, report(path, words, hits, tropes, args))
    if args.max_rate is not None and worst > args.max_rate:
        print(f"worst file is {worst:.1f} per 1,000, over the {args.max_rate} limit",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
