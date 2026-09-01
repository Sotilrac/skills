---
name: avoid-ai-tropes
description: Use when writing or editing any prose the user will read or publish - blog posts, essays, READMEs, docs, code comments, docstrings, commit bodies, PR and MR descriptions, app store listings, replies. Catalogues the two things that mark text as AI-written: the sentence, tone and formatting patterns (negative parallelism "it's not X, it's Y", em dashes as pauses, punchy fragments, bold-first bullets, title case headings, signposted conclusions, "it's worth noting", "serves as", promotional adjectives) and the vocabulary (plainly, quietly, genuinely, nobody, deliberately, indistinguishable, load-bearing, asymmetry, premise, and objects given human verbs - X carries Y, X buys Y, X asserts Y, X refuses to). Ships a scanner. Use it whenever the user asks to clean up, tighten, de-slop or de-AI writing, and before drafting documentation, a commit message or a PR description.
---

# Avoid AI writing tells

Two catalogues and one scanner. They cover different things and both are needed: a
paragraph can have perfect sentence shapes built entirely from tell words, or plain
vocabulary arranged in the shape of a LinkedIn post.

| File | Contents | Source |
| --- | --- | --- |
| `tropes.md` | 48 sentence, tone and formatting patterns | [tropes.fyi](https://tropes.fyi) by [ossama.is](https://ossama.is) |
| `words.tsv` | 1,000 words with their lift, and a category | [the load-bearing study](https://louisabraham.github.io/load-bearing/) |

Where the vocabulary comes from, since the number is the argument. Louis Abraham
sampled 1,000 GitHub pull request descriptions a day
for 602 days (467,387 descriptions, 52 million words) and clustered them by word
choice using KL-divergence k-means, with no time variable in the model. One of the
ten clusters went from 0.7% of descriptions in early 2025 to 39% by mid-2026, so the
rise is in what people wrote. `lift` is how much more often a word appears inside
that cluster than outside it: `plainly` 34x, `quietly` 30x, `nobody` 29x, `carries`
22x, `load-bearing` 20x.

## Run the scanner, then read the catalogue

```sh
scripts/scan.py draft.md                     # both halves
scripts/scan.py --tropes --words docs/*.md   # one half or the other
scripts/scan.py --summary-only docs/*.md     # one line per file
git diff | scripts/scan.py -                 # a change on the way past
scripts/scan.py --top 1000 draft.md          # the whole word list, not just the tells
```

It reads prose only: fenced blocks and URLs come out of markdown, and in source
files it reads comments and docstrings, because `zfs holds` and `obj.settles()` are
not register. Both scores are hits per 1,000 words, against these:

| Text | words/1k | tropes/1k |
| --- | --- | --- |
| `man bash`, `git-rebase`, `rsync`, `systemd.unit`, Python docstrings | 0.0 - 1.4 | 0.0 - 1.5 |
| the repository that prompted this skill | 9.7 - 31.1 | 0.0 - 16.0 |

Under 3 words/1k is ordinary. Over 8 is the cluster. There is no stemming, so `buy`
is absent where `buys` is present: the count is a floor. Read the file, not just the
number.

`scripts/refresh.py` rebuilds `words.tsv` from the study, which republishes daily.
`scripts/test_scan.py` is the scanner's suite; every case in it is a bug it once had.

## The tropes that show up most

Full entries and examples are in `tropes.md`. Read it before drafting anything longer
than a couple of sentences, and re-read the entry for any pattern you catch yourself
reaching for.

- Negative parallelism: "It's not X, it's Y." Say what the thing is.
- Em dashes as dramatic pauses. Commas, periods, parentheses.
- Short punchy fragments as standalone paragraphs.
- Preamble that announces the answer instead of giving it, and counting the items
  before listing them.
- Reasoning leak: narrating what the text is about to do.
- Tie-backs and signposted conclusions. Stop when the point has landed.
- Bold-first bullets, title case headings, unicode arrows and smart quotes.
- Invented compound labels (the "supervision paradox"), magic adverbs, and the
  "serves as" dodge in place of "is".
- Synonym cycling for one referent. Pick a word, keep it.

## The seven vocabulary habits

`words.tsv` has a `category` column for each of these. Most of the work is deletion.

**Delete the adverb.** `plainly`, `quietly`, `genuinely`, `deliberately`,
`precisely`, `merely`, `outright`, `legitimately`, `honestly`, `structurally`,
`empirically`, `demonstrably`, `provably`, `vacuously`, `identically`, `loudly`, and
the matching adjectives `genuine`, `deliberate`, `honest`, `faithful`, `vacuous`.
These are the top of the list because they are free to add.

> Not starting is loud instead.
> -> Not starting is visible: the dashboard reports every application missing.

**Give the verb back to a person.** An object given a human verb: `carries`, `buys`,
`earns`, `owes`, `pays`, `asserts`, `argues`, `admits`, `refuses`, `declines`,
`agrees`, `disagrees`, `decides`, `judges`, `governs`, `settles`, `holds`, `knows`,
`wants`, `owns`, `says`. Name what the thing does.

> that absence is the claim that unattended-upgrades has it
> -> nothing is drawn for anything apt installs, because unattended-upgrades updates it

**Drop the physical metaphor.** Abstractions given a body or a place: `sits`,
`stands`, `rests`, `rides`, `lands`, `travels`, `folds`, `wedged`, `stranded`, and
the nouns `floor`, `ceiling`, `rung`, `ladder`, `seam`, `hole`, `lever`,
`chokepoint`, `backstop`. Some are ordinary (`the file sits in /etc`). Rewrite where
the metaphor is doing the explaining.

**Cut the argument furniture.** `premise`, `asymmetry`, `load-bearing`,
`indistinguishable`, `opposite`, `worse`, `defect`, `symptom`, `remedy`,
`precedent`, `consequence`, `latent`, `inert`, `blind`, `worth`, `halves`. These
frame a claim instead of making one.

> starting against it is worse than an outage
> -> starting against it writes container state to the boot disk

> an empty config directory is indistinguishable from a first install
> -> an empty config directory looks like a first install

**Name the person.** `nobody`, `somebody`, `anyone`, `whoever`, `whichever`,
`nowhere`, `nothing`, `stranger`, `neighbour`, `caller`. A made-up third party is a
way of not naming the real one.

> a container being down is somebody's evening interrupted
> -> a container being down stops playback

**Use words that existed before the sentence.** `re-derived`, `re-measured`,
`re-verified`, `re-checked`, `mutation-checked`, `byte-identical`, `bit-identical`,
`unit-testable`, `root-caused`, `carve-out`, `pre-fix`. Hyphenating two words is not
a term of art.

**Stop counting.** `eleven`, `twelve`, `fourteen`, `sixteen`, `hundred`, and
`Seven sections`, `Eighteen actions`, `Six apps`. A tally goes stale on the next
commit. Give the figure because the reader needs it, or say `each` and `every`.

## How to use both

Draft, then reread against the catalogue and cut. Any one pattern once is fine; the
tell is several together, or one repeated. Vary sentence length, be specific, name
sources.

Three failure modes to avoid:

**Swapping one tell for another.** `carries` to `holds`, `plainly` to `clearly`,
an em dash to a colon in the same dramatic position. Rewrite the sentence, or delete
the word.

**Editing towards the score.** A file at 1.0 per 1,000 that no longer means what it
meant has been edited into nonsense. The scanner finds candidates; whether each one
goes is a judgement about that sentence.

**Trusting the scanner on what it cannot see.** It finds 19 of the 48 tropes. Stacked
premises, reasoning leak, one-point dilution, superficial analysis, synonym cycling
and fractal summaries are properties of an argument across paragraphs, and no regex
reaches them. A clean scan is not a clean draft.

## What the list is not

It measures **register, not authorship**. The study's own README scores 20.2
words/1k and 16.6 tropes/1k, higher than every file in the repository that prompted
this skill. A person who writes like this is not an AI, and text that scans clean
was not necessarily written by one.

`scan.py SKILL.md` reports about 21 words/1k. Every hit is either the frontmatter
naming the words this skill is about or a `>` example quoting prose that needs
fixing. The scanner reads register and cannot tell a citation from a use, so a
document about the words will always score like one written with them.
