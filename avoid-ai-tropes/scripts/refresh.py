#!/usr/bin/env python3
"""Rebuild words.tsv from the load-bearing study, which republishes daily.

    scripts/refresh.py                     # fetch and rebuild in place
    scripts/refresh.py analysis.js         # rebuild from a local copy

The ranking is one fit's answer -- the study runs eight seeds and publishes the
cheapest, and its own README says the seed moves the headline. So expect the order
near the top to change between refreshes and the vocabulary itself not to.

Source: https://louisabraham.github.io/load-bearing/analysis.js (generated 2026-08-31).
Component 0 is the cluster that appeared in 2026 and reached 37% of PRs attributed
to humans. `lift` is how many times more frequent the word is in that cluster than
outside it, which is the number that says a word is a tell rather than just common.

The category is my reading, not the study's: the study says which words, this says
what to do about each kind.
"""
import json
import os
import sys

CUT = """plainly quietly genuinely outright deliberately precisely merely legitimately
honestly routinely structurally empirically demonstrably provably vacuously identically
exactly loudly forever simply actually truly really clearly obviously notably fundamentally
deeply crucially critically importantly effectively essentially inherently necessarily
particularly specifically arguably notably meaningfully materially""".split()

CUT_ADJ = """genuine deliberate honest faithful vacuous legitimate""".split()

AGENCY = """carries carry carrying carried buys buy bought earns earn earned owed owes
pays pay paid priced spends spend spent drains drain gains gain gained loses lose lost
beats beat outranks outrank mints mint minted reaps reaped withheld withhold offered offer
discharged swallowed asserts assert asserted asserting argues argue argued arguing says
say said told tell telling admits admit admitted refuses refuse refused refusing declines
decline declined agrees agree agreed disagrees disagree disagreed disagreeing decides
decide decided judges judge judged rules ruled refutes refuted cites cite cited asks ask
asked answers answered guesses guessed reasons reasoned contradicts contradicted
contradicting restates restated restating honours honoured honors honored governs govern
governed settles settle settled settling holds hold held knows know wants want owns own
owned demands demand insists insist claims claim invites invite promises promise
reclaims reclaimed""".split()

FIGURE = """sits sit sitting sat stands stand standing stood rests rest resting rides ride
rode lands land landed lands walks walk walked travels travel parks park parked wedged
wedge folded folds fold folding froze freeze drifted drift swept sweep widens widen widened
widening reaches reach stranded centred centered arrives arrive arrived arriving leaves
leave stayed stay stays lives live lived died die drew draw drawn draws painted paint paints
fired fire fires drove drive drives fell fall vanished gone armed arms arm beside apart
alongside floor floored ceiling rung ladder leg legs seam band hole wedge chokepoint
backstop lever machinery straight""".split()

RHETORIC = """halves half whole premise asymmetry load-bearing worse worst indistinguishable
opposite defect defects symptom remedy precedent consequence judgement judgment grounds
shortfall hazard idiom prose tally census twin latent inert untouched unguarded ungated
blind cheap loud worth alike neither ruling refusal refusals disagreement falsified
reproduces checkable verbatim degrades outlives predates surviving survives survive survived
mattered matters""".split()

IMPERSONAL = """nobody somebody nowhere nothing whoever whichever anyone someone everyone
stranger strangers neighbour neighbours neighbor neighbors neighbouring neighboring
caller""".split()

TALLY = """one two three four five six seven eight nine ten eleven twelve thirteen fourteen
fifteen sixteen seventeen eighteen nineteen twenty hundred fourth fifth sixth seventh
eighth ninth tenth""".split()

CATS = [("cut", CUT), ("cut", CUT_ADJ), ("agency", AGENCY), ("figure", FIGURE),
        ("rhetoric", RHETORIC), ("impersonal", IMPERSONAL), ("tally", TALLY)]


def category(w):
    if w.startswith("re-") or "-" in w and any(
            w.startswith(p) for p in ("mutation-", "byte-", "bit-", "unit-", "pre-", "root-", "self-")):
        return "coinage"
    for name, words in CATS:
        if w in words:
            return name
    return ""


SRC = "https://louisabraham.github.io/load-bearing/analysis.js"


def main(src=None, out=None):
    out = out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              os.pardir, "words.tsv")
    if src:
        raw = open(src).read()
    else:
        import urllib.request
        with urllib.request.urlopen(SRC, timeout=60) as r:
            raw = r.read().decode()
    A = json.loads(raw[len("window.ANALYSIS = "):].rstrip().rstrip(";"))
    c = next(c for c in A["components"] if c["lead"])
    rows = []
    for rank, (w, lift) in enumerate(zip(c["word_list"], c["word_lift"])):
        rows.append(f"{rank}\t{lift}\t{category(w)}\t{w}")
    hdr = (f"# cluster-0 vocabulary, load-bearing study, generated {A['generated']}\n"
           f"# {A['documents']} pull requests, {A['appearances']} words, {A['days']} days\n"
           f"# https://louisabraham.github.io/load-bearing/\n"
           f"# rank\tlift\tcategory\tword\n")
    open(out, "w").write(hdr + "\n".join(rows) + "\n")
    from collections import Counter
    counts = Counter(r.split("\t")[2] or "uncategorised" for r in rows)
    print(f"{out}: {len(rows)} words, generated {A['generated']}")
    for cat, n in counts.most_common():
        print(f"  {n:4d}  {cat}")


if __name__ == "__main__":
    main(*sys.argv[1:])
