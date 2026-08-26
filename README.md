# LLM Wiki Template

A ready-to-use scaffold for the **LLM Wiki** pattern: an agent-maintained, persistent knowledge base where you curate sources and ask questions, and the agent compiles and keeps a markdown wiki current — instead of re-deriving answers from raw documents on every query.

## Quick Start Guide

Drop [AGENTS.md](AGENTS.md) (and [CLAUDE.md](CLAUDE.md), a one-line pointer for Claude Code) into an empty folder, start an agent session there, and it bootstraps the rest.

## Credits

This is an implementation of Andrej Karpathy's **LLM Wiki** pattern, described in his gist: [gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The core idea, the three-layer split, and the guiding philosophy below are his — this repo turns that description into a concrete, reusable schema file plus a few operational additions covered below.

> "The human's job is to curate sources, direct the analysis, ask good questions... The LLM's job is everything else."

## What's carried over from the original

- **Three layers**: immutable raw sources → an LLM-owned wiki of markdown pages → a schema document that governs how the LLM behaves as maintainer.
- **`index.md`** — a content-oriented catalog of every page.
- **`log.md`** — an append-only chronological record of activity.
- **Ingest** (add a source, update the wiki in one pass), **Query** (answer with citations, file durable answers back), and **Lint** (periodic health check for contradictions, staleness, orphans, gaps) as the core operations.
- The human/LLM division of labor as the guiding philosophy.

## What this template adds

The gist describes the pattern; this repo is a distributable schema built on top of it, with the following additions:

| Addition | What it does | Why |
|---|---|---|
| **First-run bootstrap wizard** | Scaffolds all folders and files automatically, then asks two setup questions (project name/description, Obsidian vs GitHub vs both) before doing anything else. | Turns the pattern from "a description to implement" into a template you can copy and run. |
| **`link_style` (wikilinks vs. markdown)** | A single frontmatter setting that switches every cross-link between Obsidian-style `[[wikilinks]]` and relative markdown links, decided once at setup. | Makes the same schema work whether the wiki is read in Obsidian, on GitHub, or both. |
| **Multi-agent write lock** (`wiki.lock`) | A plaintext lock file with atomic create, staleness takeover, and a bounded retry loop, so two agent sessions can't write at once. | The original describes a single-user system; this template is built to be safe when several agents (parallel sessions, different machines) touch the same wiki. |
| **Standing rules** | Ten explicit rules covering conflict resolution ("newer information wins"), tone, secrets handling, one-page-per-thing, and more. | Encodes judgment calls once instead of re-deciding them per session. |
| **Spoken trigger commands** | Saying "ingest" or "maintain" runs that workflow immediately, no further confirmation needed. | Removes friction for the two most common actions. |
| **Cross-agent portability** | `AGENTS.md` (read natively by Codex, Gemini CLI, Aider, Zed, Devin, etc.) as the source of truth, with `CLAUDE.md` as a minimal pointer for Claude Code — plus guidance for adding similar pointers for Cursor, Windsurf, or Copilot. | The original is written as `CLAUDE.md` for a single tool; this template works the same wiki across most current coding agents. |
| **Explicit page conventions** | Required YAML frontmatter (`title`, `type`, `created`/`modified`, `sources`), slug rules, an `## Open questions` section, citation rules, and a no-manual-line-wrap rule. | Makes every page structurally consistent and diffable, rather than leaving format to the LLM's judgment each time. |
| **`wiki-maintenance.md`** + a **Maintain** operation | A backlog + changelog for structural wiki-health work (merges, splits, link fixes, staleness), separate from `log.md`'s knowledge timeline, worked via the spoken trigger word "maintain". | Keeps Lint's findings from just piling up unread — gives them a queue and a workflow that closes them out. |
| **`parties/` vs `entities/` vs `concepts/` split** | Wiki pages are sorted by a concrete test ("would this exist if the project didn't?") instead of one generic entity/concept bucket. | Keeps person/org pages (which shouldn't duplicate across projects) distinct from project-internal artifacts. |
| **Dedicated `summaries/` and `assets/` folders** | One page per raw source lives in `summaries/`; agent-generated diagrams/charts live in `assets/`, separate from ingested knowledge. | Keeps generated-from-source content and agent-authored artifacts out of the general wiki namespace. |


## License

MIT — see [LICENSE](LICENSE). The pattern itself is Karpathy's; this repo licenses the template implementation.
