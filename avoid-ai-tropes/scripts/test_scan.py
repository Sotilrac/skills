#!/usr/bin/env python3
"""What scan.py must keep doing. Every case here is a bug it once had.

    python3 test_scan.py
"""
import os
import subprocess
import sys
import tempfile

SCAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan.py")


def run(name, text, *args):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, name)
        with open(path, "w") as f:
            f.write(text)
        p = subprocess.run([sys.executable, SCAN, path, *args],
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        return p.stdout


def rate(summary):
    """The vocabulary rate out of a --summary-only line."""
    return float(summary.split(":")[-1].split()[0])


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def markdown_skips_fenced_blocks():
    out = run("a.md", "ordinary text here\n```\nplainly quietly nobody\n```\n")
    assert "plainly" not in out, out


@case
def markdown_skips_inline_code():
    out = run("a.md", "the flag `plainly` is not prose but genuinely is\n")
    assert "genuinely" in out and "plainly" not in out, out


@case
def markdown_reads_ordinary_prose():
    out = run("a.md", "the unit plainly refuses to start\n")
    assert "plainly" in out and "refuses" in out, out


@case
def slash_comment_survives_a_url_on_the_same_line():
    # `//` appears in every `http://`, so the marker search used to find it inside the
    # string, count one quote before it, and drop the whole comment
    out = run("a.ts", 'const u = "http://x/y"; // quietly a comment\n')
    assert "quietly" in out, out


@case
def code_is_not_prose():
    out = run("a.ts", "function nobody() { return plainly(); }\n")
    assert "nobody" not in out and "plainly" not in out, out


@case
def hash_comment_inside_a_string_is_not_a_comment():
    out = run("a.sh", "PRINT='#nobody'\necho \"plainly\"\n")
    assert "nobody" not in out and "plainly" not in out, out


@case
def block_comments_are_read_past_their_opener():
    out = run("a.c", "int x;\n/* a comment that genuinely\n   carries the thing */\n")
    assert "genuinely" in out and "carries" in out, out


@case
def python_docstrings_are_prose():
    out = run("a.py", '"""Plainly the premise."""\nx = "quietly"\n')
    assert "plainly" in out.lower() and "premise" in out, out
    assert '"quietly"' not in out, out


@case
def hyphenated_compounds_survive_whole():
    # the study's tokeniser keeps `load-bearing` as one word, so splitting on
    # punctuation first would look up `bearing`, which is not in the list
    out = run("a.md", "the load-bearing context of it\n")
    assert "load-bearing" in out, out


@case
def urls_are_not_prose():
    out = run("a.md", "see https://example.com/plainly/quietly for more\n")
    assert "plainly" not in out, out


@case
def em_dashes_are_counted():
    out = run("a.md", "one thing — another thing\n")
    assert "em dash" in out, out


@case
def top_limits_the_list():
    # `tall` is rank 1000; `plainly` is rank 1
    text = "tall plainly\n"
    assert "tall" in run("a.md", text, "--top", "1000")
    assert "tall" not in run("a.md", text, "--top", "10")


@case
def human_prose_scores_low_and_this_register_scores_high():
    plain = ("The unit starts after the network is up. If the key server cannot be "
             "reached the pool stays locked and Samba does not start. Run "
             "systemctl restart to try again after fixing the network.")
    register = ("The unit plainly refuses to start: the pool stays locked, and starting "
                "against it is worse than an outage, because an empty directory is "
                "indistinguishable from a first install. Not starting is loud instead, "
                "which is genuinely what nobody deliberately wants.")
    lo = rate(run("a.md", plain, "--summary-only"))
    hi = rate(run("a.md", register, "--summary-only"))
    assert lo < 3 <= 8 < hi, (lo, hi)


@case
def max_rate_fails_loudly():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "a.md")
        with open(path, "w") as f:
            f.write("plainly quietly nobody genuinely\n")
        p = subprocess.run([sys.executable, SCAN, path, "--max-rate", "5"],
                           capture_output=True, text=True)
        assert p.returncode == 1, p.stdout


# ------------------------------------------------------------------ tropes


@case
def negative_parallelism_is_found():
    out = run("a.md", "This isn't a performance problem. It's a design problem.\n")
    assert "negative parallelism" in out, out


@case
def negative_parallelism_does_not_fire_on_an_ordinary_negation():
    out = run("a.md", "The unit isn't started at boot, so the pool stays locked.\n")
    assert "negative parallelism" not in out, out


@case
def title_case_headings_are_found_and_sentence_case_is_not():
    out = run("a.md", "## How It Fits Together\n\n## Rebooting the NAS\n\n## Time Machine\n")
    assert "How It Fits Together" in out, out
    assert "Rebooting" not in out and "Machine" not in out, out


@case
def bold_first_bullets_are_found():
    out = run("a.md", "- **Status:** eight chips, each with a value.\n")
    assert "Bold-first bullets" in out, out


@case
def a_bullets_continuation_line_is_not_a_punchy_fragment():
    # a three-line bullet had lines two and three read as new paragraphs, and the
    # tail of the item came back as a fragment
    out = run("a.md", "- **The pool** scrubs from its capacity card, and offers\n"
                      "  CLEAR ERRORS only when there are errors to clear.\n")
    assert "Short punchy fragments" not in out, out


@case
def inline_code_at_the_start_of_a_line_does_not_split_a_paragraph():
    out = run("a.md", "`make deploy` ships it and proves it owns the channel;\n"
                      "`make test` is the suite, which needs neither the NAS nor root.\n")
    assert "Short punchy fragments" not in out, out


@case
def a_real_punchy_fragment_is_found():
    out = run("a.md", "A long enough opening paragraph to be ordinary prose, with\n"
                      "several clauses in it.\n\nTwo containers, one namespace.\n")
    assert "Short punchy fragments" in out, out


@case
def worth_noting_and_friends_are_found():
    out = run("a.md", "It's worth noting that the tapestry of options here serves as\n"
                      "a comprehensive, enterprise-grade solution.\n")
    for want in ("It's worth noting", "Tapestry", "Serves As", "Promotional"):
        assert want in out, (want, out)


@case
def counting_is_found_only_where_it_counts():
    hit = run("a.md", "Two constraints shape the design of the whole thing here.\n")
    miss = run("a.md", "Two of the six drives were replaced in March of last year.\n")
    assert "Compulsive counting" in hit, hit
    assert "Compulsive counting" not in miss, miss


@case
def unicode_decoration_is_found():
    out = run("a.md", "the version reads latest, or → 2.0.0 when it is not\n")
    assert "Unicode decoration" in out, out


@case
def code_is_not_read_for_tropes_either():
    out = run("a.ts", 'const label = "It\'s worth noting";\n')
    assert "worth noting" not in out, out


@case
def the_two_halves_can_be_asked_for_separately():
    text = "This isn't plainly a problem. It's genuinely a design.\n"
    only_words = run("a.md", text, "--words")
    only_tropes = run("a.md", text, "--tropes")
    assert "lift" in only_words and "negative parallelism" not in only_words, only_words
    assert "negative parallelism" in only_tropes and "lift " not in only_tropes, only_tropes


@case
def an_extensionless_script_is_read_by_its_shebang():
    # a repository of executables has no extensions on them, and reading these as
    # prose scanned every line of code as English and roughly doubled their scores
    py = run("collector", '#!/usr/bin/env python3\n"""Plainly the premise."""\n'
                          'nobody = compute(plainly)\n')
    assert "premise" in py, py
    assert "nobody" not in py, py
    sh = run("deploy", "#!/bin/bash\n# quietly, a comment\necho \"plainly\"\n")
    assert "quietly" in sh, sh
    assert "plainly" not in sh, sh


@case
def a_file_with_no_extension_and_no_shebang_is_still_read_as_prose():
    out = run("NOTES", "the unit plainly refuses to start\n")
    assert "plainly" in out, out


def main():
    bad = 0
    for fn in CASES:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            bad += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(CASES) - bad}/{len(CASES)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
