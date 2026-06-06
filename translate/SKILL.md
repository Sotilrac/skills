---
name: translate
description: Translate documents with research-backed style. Before translating, gather reference material in the target language for the same domain and register, build a style guide and lexicon, and confirm the target region and dialect strength with the user. Use whenever asked to translate content beyond a trivial phrase.
---

# translate

Translate source material into a target language by first researching how native speakers actually write in that domain today, then translating against that evidence. Never translate cold from training knowledge alone: word choice, tone, and conventions drift, and direct translation reads as foreign.

## Step 1: Scope the job

Establish before any research:

- **Source and target languages.** If the target is unstated, ask.
- **Domain.** Recipes, legal contracts, marketing copy, API docs, fiction, etc.
- **Register.** Formal, casual, technical, literary, promotional. Infer from the source, confirm if ambiguous.
- **Target region and dialect strength.** Always ask, in one question, two things:
  1. Which region? (e.g. Spanish: Spain, Mexico, Rioplatense, neutral Latin American; Portuguese: Brazil vs Portugal; French: France vs Quebec)
  2. How strongly to lean into the regional dialect? Offer a scale: neutral/international (widely understood, region-correct grammar only), moderate (regional vocabulary where natural), or strong (idioms, colloquialisms, local flavor).
- **Audience and purpose.** Who reads this and why. A recipe blog and a culinary textbook translate the same dish differently.

Use AskUserQuestion for region and dialect strength. Do not guess these.

## Step 2: Research the target language domain

Before reading the source in depth, gather reference material written natively in the target language, in the same domain and register. This is the core of the skill: the goal is to write like a native author in that space, not to transpose the source.

Search the web (and any reference material the user provides) for:

1. **Domain texts in the target language.** E.g. translating recipes to Spanish: find popular Spanish-language recipe sites, note how they phrase instructions (infinitive vs imperative vs impersonal se), measurement units, ingredient names by region (e.g. "papa" vs "patata").
2. **Register-matched samples.** Material at the same formality level as the source. A casual blog post needs casual-blog references, not encyclopedia entries.
3. **Current usage.** Recent material, not just canonical references. Check how contemporary writers handle loanwords, anglicisms, and new terminology in the domain. Note what is borrowed untranslated vs localized.
4. **Regional conventions.** If a specific region was chosen, prefer sources from that region. Note region-specific vocabulary, second-person forms (tú/usted/vos/vosotros), date and number formats, currency.

Fetch and read 3-6 representative sources. More for long or specialized material, fewer for short casual pieces.

## Step 3: Build the style guide and lexicon

Distill the research into a working document before translating. Write it out (as a file for long jobs, inline for short ones) so it is checkable:

- **Tone notes.** How native domain authors address the reader, sentence rhythm, level of directness, humor conventions.
- **Grammar conventions.** Verb forms for instructions, person and formality, passive vs active norms in this domain.
- **Lexicon.** A table of domain terms: source term, chosen target term, rejected alternatives and why (wrong region, dated, wrong register). Include terms that stay untranslated.
- **Formatting conventions.** Units, numbers, dates, quotation marks, capitalization rules of the target language (e.g. Spanish does not capitalize months or title-case headings).
- **Regional dial.** Restate the chosen region and dialect strength so every word choice is checked against it.

For recurring clients or domains, suggest saving the style guide so future translations reuse it.

## Step 4: Read the source, then translate

Only now read the full source material closely. Translate informed by the style guide:

- Match the **tone** of native domain writing, not the surface structure of the source. Reorder, split, or merge sentences where the target language demands it.
- Apply the lexicon consistently. If a new term appears mid-translation, resolve it against the research (search again if needed) and add it to the lexicon.
- Localize real-world referents (prices, sizes, cultural anchors) to target-market equivalents, not just converted units. A "$80/month gym membership" becomes what a gym actually costs in the target market, not a literal currency swap. Flag substantive substitutions like price points to the user.
- Keep proper nouns, brand names, and code untranslated unless convention says otherwise.
- Preserve the source's document structure (headings, lists, links) unless target-language convention differs.

## Step 5: Review pass

Reread the translation as a standalone target-language text:

- Does it read like it was written by a native author in this domain and region, at this dialect strength?
- Any calques (literal phrasings that mirror source syntax)? Rewrite them.
- Lexicon and formality consistent throughout?
- Spot-check 2-3 tricky terms against the research.

Deliver the translation. On request, also deliver the style guide and lexicon.

## Operating notes

- Research is not optional. Skipping straight to translation is the failure mode this skill exists to prevent. Only for trivial single phrases may research be skipped.
- When the source contains errors or ambiguity, flag them to the user rather than silently fixing or guessing.
- For very long documents, translate in sections and keep the lexicon updated between sections.
