---
name: translate
description: Translate documents with research-backed style. Before translating, gather reference material in the target language for the same domain and register, build a style guide and lexicon, and confirm the target region and dialect strength with the user. Use whenever asked to translate content beyond a trivial phrase.
---

# translate

Research how native speakers write in the domain today, then translate against that evidence.

## Craft principles

- **Translate context and effect, not words.** Word-for-word produces translatorese; a translation is an interpretation.
- **Inhabit the voice.** Read the source whole before translating anything.
- **Purpose governs method.** Different audiences and uses yield different valid translations.
- **Commit to interpretations.** One deliberate choice, never hedging or in-text alternatives.
- **Draft, then chisel.** A fast complete draft plus revision passes beats sentence-by-sentence perfectionism.
- **The ear will not accept what the eye will.** Hunt unnatural rhythm by rereading as if aloud.

## Step 1: Scope

- **Source and target languages.** Ask if unstated.
- **Domain and register.** Infer from the source, confirm if ambiguous.
- **Region and dialect strength.** Always ask both (AskUserQuestion, one question): which region, and how regional: neutral/international, moderate (regional vocabulary where natural), or strong (idioms, local flavor).
- **Audience and purpose.**
- **Text type sets the strategy**: informative → clarity and complete content; expressive → preserve voice and form; operative (ads, CTAs) → transcreate the effect. If the text needs to *work*, translate; if it needs to *win someone over*, transcreate.

Read the source whole: register voice, rhythm, motifs, jokes.

## Step 2: Research the target language domain

Gather material written natively in the target language, same domain and register. Search for:

1. **Domain texts** (e.g. Spanish recipe sites: instruction verb form, units, regional ingredient names).
2. **Register-matched samples.** A casual blog needs casual-blog references, not encyclopedia entries.
3. **Current usage.** How contemporary writers handle loanwords and new terminology; what stays untranslated.
4. **Regional conventions.** Vocabulary, second-person forms, date/number/currency formats.

Read 3-6 representative sources; more for long or specialized material.

## Step 3: Style guide and lexicon

Write it out (style.md for long jobs, inline for short ones):

- **Tone notes.** How native authors address the reader, rhythm, directness, humor.
- **Grammar conventions.** Instruction verb forms, person and formality, passive vs active norms.
- **Lexicon.** Source term → chosen target term, rejected alternatives and why, do-not-translate list.
- **Formatting.** Units, numbers, dates, quotes, capitalization rules.
- **Regional dial.** Restate region and dialect strength.

## Step 4: Translate

Read the source closely, then draft the whole translation:

- Match the tone of native domain writing. Reorder, split, merge freely.
- Apply the lexicon consistently; resolve new terms against the research and add them.
- Keep recurring words and motifs consistent; an author's repetitions are structural.
- Localize real-world referents (prices, sizes, cultural anchors) to target-market equivalents. Flag substantive substitutions to the user.
- Proper nouns, brands, code stay untranslated unless convention says otherwise.
- Solve grammatical asymmetries (gender, T/V, plurality) unobtrusively.

When literal rendering fails, escalate: transposition (change word class) → modulation (shift viewpoint: "not difficult" → "easy") → idiomatic reformulation (target's own idiom, never element-by-element) → cultural substitution → borrow plus one-time gloss → compensation (recreate a lost pun or register marker nearby; preserve the laugh, not the joke).

Resist flattening: translations drift toward over-explicitness and cliché. Leave implicit what the source leaves implicit; keep idiosyncratic phrasing idiosyncratic.

## Step 5: Two review passes

Each catches what the other misses:

1. **Bilingual accuracy**, target vs source segment by segment: addition, omission, mistranslation, untranslated text; numbers/dates/units locale-formatted; lexicon and do-not-translate respected.
2. **Monolingual fluency**, translation alone, ear over eye: reads native for this domain, region, dialect strength; calques rewritten; register consistent; spot-check 2-3 tricky terms against the research.

Meaning errors outrank cosmetic ones: fix accuracy first, polish second.

Deliver the translation, style guide w/ lexicon.

## Operating notes

- Research is mandatory. Exception: trivial single phrases.
- Flag source errors or ambiguity to the user instead of silently fixing.
- For long documents, translate in sections, keeping the lexicon updated between them.
