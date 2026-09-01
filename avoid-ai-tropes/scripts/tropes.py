"""The tropes a regex can find, from `tropes.md`.

Most of the 48 tropes in the catalogue need a reader: negative parallelism used once
for effect and used ten times are the same regex, and premise stacking is a property
of a paragraph's argument. What is here is the subset a machine can find without
guessing, so a scan is a worklist and the catalogue is still the thing to read.

Each entry is (trope, pattern, what to do). The trope name matches a heading in
`tropes.md` so a hit can be looked up.
"""

import re

# ------------------------------------------------------------------ phrases

# (trope, regex, advice). Case-insensitive unless the pattern says otherwise: some
# of these are only tells when capitalised, because that is where a sentence starts.
PHRASES = [
    ("negative parallelism",
     # "X isn't A. It's B", "The question isn't A, the question is B"
     r"\b(?:is|was|are|were|does|do|did)n[’']?t\s+[^.;!?]{3,70}[.;,]\s+"
     r"(?:it|this|that|the\s+\w+)(?:[’']s|\s+(?:is|was|are|were))\b",
     "say what the thing is, without the setup"),
    ("negative parallelism",
     r"\bnot\s+(?:just|only|merely|simply)\s+[^.;!?]{3,50}[.;,]\s*(?:but|it[’']s)\b",
     "say what the thing is, without the setup"),
    ("Not X. Not Y. Just Z.",
     r"\bNot\s+[^.!?]{2,40}\.\s+Not\s+[^.!?]{2,40}\.\s+(?:Just|Simply|Only)\b",
     "one sentence, positively stated"),
    ("It's worth noting",
     r"\bit(?:[’']s|\s+is)\s+worth\s+(?:noting|mentioning|remembering|pointing\s+out|"
     r"considering|highlighting)\b",
     "delete the frame and state the fact"),
    ("Delve and friends",
     r"\b(?:delve[sd]?|delving|myriad|plethora|multifaceted|intricacies|"
     r"in\s+the\s+realm\s+of|navigat(?:e|ing)\s+the\s+(?:complex|landscape)|"
     r"testament\s+to|a\s+(?:crucial|vital|pivotal|key)\s+role)\b",
     "use the ordinary word"),
    ("Tapestry and Landscape",
     r"\b(?:rich\s+tapestry|tapestry\s+of|"
     r"(?:evolving|shifting|changing|digital|technological|competitive|modern)\s+landscape|"
     r"ever-(?:evolving|changing))\b",
     "name the actual subject"),
    ("Let's break this down",
     r"\blet(?:[’']s|\s+us)\s+(?:break\s+(?:this|it)\s+down|dive\s+i?n|unpack|explore|"
     r"take\s+a\s+(?:look|closer\s+look))\b",
     "just do it"),
    ("Here's the kicker",
     r"\bhere(?:[’']s|\s+is)\s+(?:the|where)\s+(?:kicker|thing|catch|rub|twist|"
     r"it\s+gets)\b",
     "state the point"),
    ("Think of it as",
     r"\b(?:think\s+of\s+it\s+as|imagine\s+(?:a\s+world|if\s+you|for\s+a\s+moment)|"
     r"picture\s+this)\b",
     "describe the thing, not an analogy for it"),
    ("The Serves As dodge",
     r"\b(?:serves?|serving|served)\s+as\b",
     "use is, or the verb that is true"),
    ("Signposted conclusion",
     r"(?:^|[.!?]\s+)(?:In\s+conclusion|Ultimately|At\s+the\s+end\s+of\s+the\s+day|"
     r"In\s+summary|To\s+sum\s+up|All\s+in\s+all|The\s+bottom\s+line|In\s+essence|"
     r"That\s+said)\b",
     "stop when the point has landed"),
    ("Despite its challenges",
     r"\b[Dd]espite\s+(?:its|these|the|their)\s+"
     r"(?:challenges|limitations|drawbacks|shortcomings|complexity)\b",
     "cut the concession, or make it specific"),
    ("Grandiose stakes inflation",
     r"\b(?:game-?chang(?:er|ing)|revolutionis|revolutioniz|paradigm\s+shift|"
     r"seismic\s+shift|sea\s+change|watershed|fundamentally\s+(?:alters?|changes?)|"
     r"the\s+stakes\s+(?:are|could\s+not\s+be))\w*",
     "say the size of the effect"),
    ("Promotional language",
     r"\b(?:seamless(?:ly)?|robust|cutting-edge|state-of-the-art|best-in-class|"
     r"world-class|unparalleled|comprehensive|enterprise-grade|production-ready|"
     r"battle-tested|blazing(?:ly)?\s+fast|first-class\s+support)\b",
     "a claim a reader can check, or nothing"),
    ("Vague attributions",
     r"\b(?:many|some|most|several)\s+(?:experts|studies|researchers|developers|"
     r"critics|observers|people)\s+(?:say|said|believe|argue|suggest|show|indicate|"
     r"agree|note)\b"
     r"|\bit(?:[’']s|\s+is)\s+(?:often|widely|generally|commonly)\s+"
     r"(?:said|believed|thought|considered|known|accepted)\b"
     r"|\b(?:studies|research)\s+(?:show|shows|suggest|suggests|indicate)\b",
     "name the source or drop the claim"),
    ("Compulsive counting",
     r"(?:^|[.!?]\s+|^#{1,6}\s+)(?:There\s+are\s+)?"
     r"(?:Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|"
     r"Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)\s+"
     r"(?:\w+\s+){0,2}(?:reasons?|things?|ways?|constraints?|factors?|steps?|"
     r"principles?|sections?|parts?|actions?|apps?|options?|rules?|checks?|"
     r"tests?|files?|are|shape|matter)\b",
     "a count goes stale on the next commit; use each or every"),
    ("Collaborative communication",
     r"\b(?:great\s+question|you(?:[’']re|\s+are)\s+absolutely\s+right|"
     r"I\s+hope\s+this\s+helps|let\s+me\s+know\s+if|happy\s+to\s+help|"
     r"excellent\s+point)\b",
     "cut it"),
    ("False ranges",
     r"\b(?:everything\s+from\s+\w+\s+to\s+\w+|"
     r"whether\s+(?:you(?:[’']re|\s+are)|it(?:[’']s|\s+is))\s+[^,]{2,30}\s+or\s+\w+)\b",
     "give the real span or one real example"),
    ("Quietly and other magic adverbs",
     # the vocabulary half has the full list; these are the ones the catalogue names
     r"\b(?:quietly|deeply|fundamentally|profoundly|inherently|precisely|genuinely|"
     r"plainly|deliberately|meaningfully|materially|crucially)\b",
     "delete it"),
]

# these read as tells only where a sentence starts, so their patterns keep their case
CASE_SENSITIVE = {"Not X. Not Y. Just Z.", "Signposted conclusion",
                  "Compulsive counting", "Despite its challenges"}

PHRASE_RE = [(name, re.compile(pat, 0 if name in CASE_SENSITIVE else re.I), note)
             for name, pat, note in PHRASES]

# ------------------------------------------------------------------ structure

EM_DASH = "—"
# arrows, checkmarks, stars, emoji and smart quotes. NOT `•`, `‣` or `▪`: a rendered
# man page is full of them and they are how a list is drawn, not decoration.
DECORATION = re.compile(r"[→←↑↓⇒⇐✓✗✔✘★☆]|[\U0001F300-\U0001FAFF☀-➿]|[“”‘’]")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BULLET = re.compile(r"^\s*[-*+]\s+\*\*[^*]{2,60}\*\*\s*[:.—-]?\s+\S")
CAP_WORD = re.compile(r"^[A-Z][a-z]{2,}$")
# words a title-case check must not count: they are capitalised in a sentence-case
# heading too, and counting them called every two-word heading title case
LOWER_IN_TITLE = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "is",
                  "it", "of", "on", "or", "the", "to", "with", "not", "no", "if"}
SENTENCE_END = re.compile(r"[.!?][\"')\]]*$")


def title_case_heading(text):
    """Is this heading Title Cased rather than sentence cased?

    Counting capitals alone flagged `Time Machine`, `Open WebUI` and every heading
    naming a product. The test that works is on the words the two styles disagree
    about: a sentence-case heading leaves `the`, `of` and `is` lowercase, and a
    Title Cased one does not. One lowercase function word settles it.
    """
    words = text.split()
    if len(words) < 3:
        return False
    rest = words[1:]
    if any(w.lower() in LOWER_IN_TITLE and w[:1].islower() for w in rest):
        return False
    caps = sum(1 for w in rest if w[:1].isupper())
    return caps >= 2 and caps >= 0.6 * len(rest)


LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d{1,2}[.)])\s")


def paragraphs(lines):
    """(first lineno, text) per prose paragraph, skipping lists, tables and headings.

    An indented line is a continuation and not a paragraph of its own. Without that,
    a three-line bullet had its second and third lines read as two new paragraphs,
    and the last few words of the item came back as a punchy fragment. Which is the
    trope's own failure mode: the check was finding the shape and not the writing.
    """
    buf, start = [], 0
    for lineno, line in lines + [(0, "")]:
        stripped = line.strip()
        skip = (not stripped
                or line[:1] in (" ", "\t")          # a continuation, or a code block
                or stripped[0] in "#>|"
                or LIST_ITEM.match(line))
        if skip:
            if buf:
                yield start, " ".join(buf)
                buf = []
            continue
        if not buf:
            start = lineno
        buf.append(stripped)


INLINE_CODE = re.compile(r"`[^`]*`")
URL = re.compile(r"https?://[^\s<>\"'`)\]}]+")


def structural(lines):
    """(lineno, trope, detail, advice).

    `lines` is (lineno, text) as written. The shape checks need it that way -- a
    line's indentation and its bullet marker are the signal -- while the phrase
    patterns need code and links out of the way first, or `plainly` as the name of a
    flag reads as a magic adverb and a link to `example.com/quietly` reads as prose.
    """
    out = []
    for lineno, line in lines:
        for _ in range(line.count(EM_DASH)):
            out.append((lineno, "Em-dash addiction", "em dash",
                        "comma, period or parentheses"))
        for m in DECORATION.finditer(line):
            out.append((lineno, "Unicode decoration", repr(m.group(0)),
                        "plain ascii, or a real word"))
        h = HEADING.match(line)
        if h and title_case_heading(h.group(2)):
            out.append((lineno, "Title case headings", h.group(2)[:40],
                        "sentence case"))
        if BULLET.match(line):
            out.append((lineno, "Bold-first bullets", line.strip()[:40],
                        "write the sentence, drop the label"))

    for lineno, para in paragraphs(lines):
        # inline code counts as one word however long it is, so `zfs list -t snapshot`
        # does not make a three-word paragraph look like a sentence
        words = re.sub(r"`[^`]*`", "X", para).split()
        if 3 <= len(words) <= 6 and SENTENCE_END.search(para) and len(para) >= 15:
            out.append((lineno, "Short punchy fragments", para[:44],
                        "join it to the paragraph it belongs to"))

    # blanked to the same length rather than removed, so an offset in this text is
    # still an offset in the original and the line number stays right
    blank = "\n".join(INLINE_CODE.sub(lambda m: " " * len(m.group(0)),
                                      URL.sub(lambda m: " " * len(m.group(0)), line))
                      for _, line in lines)
    first = lines[0][0] if lines else 1
    for name, rx, note in PHRASE_RE:
        for m in rx.finditer(blank):
            lineno = blank.count("\n", 0, m.start()) + first
            out.append((lineno, name, " ".join(m.group(0).split())[:44], note))

    out.sort(key=lambda h: (h[0], h[1]))
    return out
