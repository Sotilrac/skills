# Skills

A collection of [Claude Code skills](https://code.claude.com/docs/en/skills). Each skill is a short, focused playbook that Claude loads only when relevant, so having many installed costs almost nothing until one triggers.

The repo layout mirrors `~/.claude/skills/` exactly: one folder per skill, each containing a `SKILL.md`. Installation is a straight copy.

## Included

| Skill | When it triggers |
| :--- | :--- |
| [avoid-ai-tropes](avoid-ai-tropes/SKILL.md) | Writing or editing prose, docs, commit bodies, PR descriptions or comments. Two catalogues of what marks text as AI-written, sentence patterns and vocabulary, plus a scanner that scores a file against hand-written prose. |
| [d2-diagrams](d2-diagrams/SKILL.md) | Writing, debugging, or explaining [D2](https://d2lang.com) diagrams. Auto-loads on `**/*.d2`. |
| [html-deck](html-deck/SKILL.md) | Authoring single-file HTML presentation decks (keyboard nav, auto-scale, print-to-PDF, speaker notes). Ships with a runtime, a template, and a worked example. |
| [nextcloud-web-app](nextcloud-web-app/SKILL.md) | Adding a Nextcloud app target to a local-first web app and publishing it to the Nextcloud App Store. Pairs with standalone-web-app. |
| [standalone-web-app](standalone-web-app/SKILL.md) | Bootstrapping a local-first, single-bundle browser app (pnpm + Vite + React + TS). |
| [ticket](ticket/SKILL.md) | Working a Jira ticket end-to-end via Atlassian MCP: plan, branch, implement, commit, PR. Invoke as `/ticket ABC-123`. |
| [translate](translate/SKILL.md) | Translating documents. Researches native target-language material in the same domain and register first, builds a style guide and lexicon, confirms region and dialect strength. |

## Install

```bash
./install.sh              # install every skill
./install.sh d2-diagrams html-deck # install specific skills
./install.sh --list       # list available skills and which are currently installed
./install.sh --project    # install into ./.claude/skills (this repo only) instead of ~/.claude/skills
./install.sh --link       # symlink instead of copy, so edits here are live
```

Changes take effect in the current Claude Code session without a restart. To uninstall: `rm -rf ~/.claude/skills/<name>`.

## Authoring new skills

A skill is a folder with a `SKILL.md` inside. The simplest form:

```yaml
---
name: my-skill
description: One sentence saying what the skill does AND when to use it. Front-load trigger keywords, Claude matches on this.
---

# My skill

Instructions Claude follows when the skill is active.
```

### Layout

- **Minimal:** just `<name>/SKILL.md`.
- **With supporting files** (scripts, templates, examples): add siblings next to `SKILL.md` and reference them from the body so Claude knows when to read them. Use `${CLAUDE_SKILL_DIR}` in `SKILL.md` to point at bundled files regardless of the current working directory.

### Guidelines

- **Be terse.** Once loaded, every token in `SKILL.md` competes with the conversation. Only include context Claude doesn't already have. Keep under 500 lines. Move long reference material into sibling files and link to them.
- **Write the description for discovery.** Claude picks skills by matching the `description` against the user's request. Lead with the trigger keywords, then the use case. `description` + optional `when_to_use` are truncated at 1,536 characters.
- **Scope with `paths`** when the skill is file-type specific (`paths: "**/*.d2"`). Claude auto-loads it only when matching files are in play.
- **Set `disable-model-invocation: true`** for workflows with side effects (deploys, commits, sends) so Claude can't trigger them on its own. The user has to type `/name`.
- **Pick one content shape per skill:** *reference* (conventions, patterns, gotchas applied inline) or *task* (numbered steps for a specific action). Mixing dilutes the trigger.

### Frontmatter cheatsheet

| Field | Use |
| :--- | :--- |
| `name` | Becomes the `/slash-command`. Lowercase, hyphens, max 64 chars. |
| `description` | Required for discovery. What + when, keywords first. |
| `paths` | Glob(s) that scope auto-activation to matching files. |
| `disable-model-invocation` | `true` to require manual `/name` invocation. |
| `allowed-tools` | Tools pre-approved while the skill is active (e.g. `Bash(git *)`). |
| `argument-hint` | Shown during `/name` autocomplete. |

Full field reference: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).

## Contributing

Drop a new `<name>/SKILL.md` at the repo root, add a row to the table above, and open a PR.

## License

[MPL-2.0](LICENSE).
