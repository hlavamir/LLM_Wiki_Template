# LLM Wiki Template

A ready-to-use scaffold for the **LLM Wiki** pattern: an agent-maintained, persistent knowledge base where you curate sources and ask questions, and the agent compiles and keeps a markdown wiki current — instead of re-deriving answers from raw documents on every query.

## Quick Start Guide

Pick **one** of the two options below — both land in the same first-run wizard.

### Option A: paste the link

Create an empty folder, start an agent session there (Claude Code, Codex CLI, etc.), and paste this repo's URL as your first message — e.g. `https://github.com/hlavamir/LLM_Wiki_Template` — then hit enter. The agent fetches `AGENTS.md` and `CLAUDE.md` from GitHub, writes them into the folder, and runs the first-run wizard. (This works because `AGENTS.md` itself carries the instruction — see "Bootstrapping from a link" in that file.)

### Option B: copy the files

Drop [AGENTS.md](AGENTS.md) (and [CLAUDE.md](CLAUDE.md), a one-line pointer for Claude Code) into an empty folder, start an agent session there, and it bootstraps the rest.

### What the wizard asks

Whichever option you pick, the first-run wizard asks four things: **who you are** (name, nickname, optional related code repo), **the project's name and description**, **just you, or several people**, and **how the wiki will be viewed** (Obsidian, GitHub, or both).

- **Just me** → one local wiki, nothing more to set up.
- **Several people** → the folder you're in becomes a **shared wiki**, so it must sit on storage everyone can reach and that syncs (Google Shared Drive, OneDrive, Dropbox, …). The wizard also installs [`personal-template/`](personal-template/) into it. Each person — you included — then creates their own **personal wiki** in a separate local folder by pointing an agent at `personal-template/AGENTS.md` (steps in [`personal-template/README.md`](personal-template/README.md)). Personal wikis exchange knowledge with the shared one through `push`, `pull` and `sync`, so people work privately and publish what's ready.

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
| **First-run bootstrap wizard** | Scaffolds all folders and files automatically, then asks four setup questions (who you are, project name/description, solo vs. shared, Obsidian vs GitHub vs both) before doing anything else. | Turns the pattern from "a description to implement" into a template you can copy and run. |
| **Shared mode** (`mode: shared`) + **`personal-template/`** | Optional multi-person setup: a synced shared wiki plus one personal wiki per person, bootstrapped from `personal-template/`. Personal wikis `push` / `pull` / `sync` / `fetch news` against the shared one, with page pairing by path, a `public:` flag per page, and schema updates that propagate to every personal wiki on its next pull. | Lets a team build one knowledge base on a shared drive without everyone editing the same files at once. |
| **Identity & per-page `history`** | The wizard asks who you are; every page, solo or shared, carries an append-only `history` of `"YYYY-MM-DD HH:MM Lastname Firstname"` edits (in shared mode the agent also asks rather than guesses who is driving a write). | Makes edits attributable, and means any solo wiki can later become a shared one without rewriting its pages. |
| **Schema versioning** (`schema_version`, currently `1.1.0`) | The schema file carries a semantic version; every page records the version that was active at its last edit. | Shows which pages were written under which schema, so a schema change can be rolled out to the pages that predate it. |
| **Solo/shared pruning** | The one `AGENTS.md` carries both modes; at first run the agent deletes the parts that don't apply to the chosen mode. | A solo wiki doesn't carry the multi-person rules around, yet one template serves both. |
| **Bootstrap from a link** | Paste this repo's GitHub URL into an agent session in an empty folder; the agent fetches `AGENTS.md`/`CLAUDE.md` itself and runs the same wizard — no manual file copy needed. | Gets a new wiki running in one pasted link instead of a download-and-copy step. |
| **`link_style` (wikilinks vs. markdown)** | A single frontmatter setting that switches every cross-link between Obsidian-style `[[wikilinks]]` and relative markdown links, decided once at setup. | Makes the same schema work whether the wiki is read in Obsidian, on GitHub, or both. |
| **Multi-agent write lock** (`wiki.lock`) | A plaintext lock file with atomic create, staleness takeover, and a bounded retry loop, so two agent sessions can't write at once. | The original describes a single-user system; this template is built to be safe when several agents (parallel sessions, different machines) touch the same wiki. |
| **Standing rules** | Eleven explicit rules (twelve in shared mode) covering conflict resolution ("newer information wins"), tone, secrets handling, one-page-per-thing, and more. | Encodes judgment calls once instead of re-deciding them per session. |
| **Spoken trigger commands** | Saying "ingest", "maintain" or "lint" runs that workflow immediately, no further confirmation needed (shared mode adds "sync", "push", "pull" and "fetch news"). | Removes friction for the most common actions. |
| **Cross-agent portability** | `AGENTS.md` (read natively by Codex, Gemini CLI, Aider, Zed, Devin, etc.) as the source of truth, with `CLAUDE.md` as a minimal pointer for Claude Code — plus guidance for adding similar pointers for Cursor, Windsurf, or Copilot. | The original is written as `CLAUDE.md` for a single tool; this template works the same wiki across most current coding agents. |
| **Explicit page conventions** | Required YAML frontmatter (`title`, `type`, `created`/`modified`, `sources`), slug rules, an `## Open questions` section, citation rules, and a no-manual-line-wrap rule. | Makes every page structurally consistent and diffable, rather than leaving format to the LLM's judgment each time. |
| **Lint vs. Maintain split** + **`wiki-maintenance.md`** | **Maintain** works a backlog + changelog of technical/structural health (link format, broken links, frontmatter, naming, orphans), separate from `log.md`'s knowledge timeline; you can write plain-language structural instructions into it too. **Lint** checks only whether pages state contradicting facts, and resolves each live — newer wins, or it asks you — instead of filing it away. | Keeps mechanical clean-up and factual judgment calls apart, so findings get resolved rather than piling up unread. |
| **`parties/` vs `entities/` vs `concepts/` split** | Wiki pages are sorted by a concrete test ("would this exist if the project didn't?") instead of one generic entity/concept bucket. | Keeps person/org pages (which shouldn't duplicate across projects) distinct from project-internal artifacts. |
| **Dedicated `summaries/` and `assets/` folders** | One page per raw source lives in `summaries/`; agent-generated diagrams/charts live in `assets/`, separate from ingested knowledge. | Keeps generated-from-source content and agent-authored artifacts out of the general wiki namespace. |


## License

MIT — see [LICENSE](LICENSE). The pattern itself is Karpathy's; this repo licenses the template implementation.
