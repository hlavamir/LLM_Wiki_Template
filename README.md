# LLM Wiki Template

A ready-to-use scaffold for the **LLM Wiki** pattern: an agent-maintained, persistent knowledge base where you curate sources and ask questions, and the agent compiles and keeps a markdown wiki current — instead of re-deriving answers from raw documents on every query.

> **Note for AI agents:** a user who pastes this repository's link into a session in an empty folder, or asks you to set up a wiki from it, wants a new LLM wiki in that folder. Download the template — `git clone --depth 1` it into a temporary folder and copy everything except `README.md`, `LICENSE` and `.git` into the user's folder (no git: download the files listed under "Bootstrapping from a link" in `AGENTS.md`). Then, **in this same session, without asking the user to restart**, read `schema/first-run.md` and start its setup wizard. If you need the user's go-ahead before downloading, ask once, in one short plain-language question, and go straight on to the wizard when they agree.

## Quick Start Guide

Pick **one** of the two options below — both land in the same first-run wizard.

### Option A: ask your agent

Create an empty folder, start an agent session there (Claude Code, Codex CLI, etc.), and send:

```
Set up a new LLM wiki in this folder from https://github.com/hlavamir/LLM_Wiki_Template
```

The agent downloads the template into the folder and starts the setup wizard right away. Pasting just the link works too, but then most agents first ask whether you want it set up.

### Option B: copy the files

Copy everything in this repo except `README.md`, `LICENSE` and `.git` — [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md) (a one-line pointer for Claude Code), [`schema/`](schema/), [`tools/`](tools/) and [`personal-template/`](personal-template/) — into an empty folder, start an agent session there, and say `set up the wiki`. (A solo wiki deletes `personal-template/` at first run.)

**Python 3** (3.8+, standard library only) is recommended: `tools/wiki.py` takes over the mechanical work — structural checks, log appends, lint scoping, transcript capture, locking — so the agent doesn't spend tokens on it. Without Python everything still works by hand, just more expensively.

### What the wizard asks

Whichever option you pick, the agent opens with a two-line explanation of what the wiki does, then asks a few questions one at a time — in Claude Code as clickable choices, with its own proposals already filled in: **your name** (for marking your edits) and **what to call you**, **what the wiki is about**, **just you, or your team**, **how you'll read it** (Obsidian, GitHub/browser, or both), and — solo only — **whether it's about a code project** on your computer that it may read. It ends with a short "here's what to try first", without technical detail.

- **Just me** → one local wiki, nothing more to set up.
- **Several people** → the folder you're in becomes a **shared wiki**, so it must sit on storage everyone can reach and that syncs (Google Shared Drive, OneDrive, Dropbox, …). The wizard also installs [`personal-template/`](personal-template/) into it. Each person — you included — then creates their own **personal wiki** in a separate local folder by pointing an agent at `personal-template/AGENTS.md` (steps in [`personal-template/README.md`](personal-template/README.md)). Personal wikis exchange knowledge with the shared one through `push`, `pull` and `sync`, so people work privately and publish what's ready.

## Commands

Once a wiki is set up you mostly just talk to the agent. A few words are **standing commands** — say them and the agent runs that workflow straight away, with no "are you sure?" — and everything else is ordinary conversation. All of them are specified in `AGENTS.md`; the last four exist only where there's a shared wiki to talk to (see [Where each command works](#where-each-command-works)).

| Say… | What happens |
|---|---|
| **`ingest`** | Captures the current conversation to `raw/` as a markdown file, writes its summary page, creates or updates the relevant party / entity / concept pages, and updates `index.md` and the log. To ingest something other than the chat — a document, transcript, web article, source file — just hand it over and ask. |
| **`lint`** | Checks the **facts**: compares the pages changed since the last lint with the pages they share a new source with or link to, looking for genuine contradictions (not different wording, not mere staleness). Each one is resolved on the spot — the newer source wins if the dates make that unambiguous, otherwise the agent stops and asks you, one conflict at a time. The losing fact moves to the page's `## History`, never deleted. A run is logged even when it finds nothing. Say **`lint all`** for a full sweep. |
| **`maintain`** | Checks the **structure**: runs `tools/wiki.py check` (folder layout, frontmatter, link format and broken links, naming, orphan pages, index and log shape, oversized pages, secrets), then works through *every* open item in `wiki-maintenance.md` — things it found itself and plain-language instructions you wrote there (e.g. "convert all `[[wikilinks]]` to markdown links") — closes each into that file's log, and asks about anything ambiguous. |
| **`sync`** | Shared setups: **pull**, then **ingest** anything durable from the session, then **push**, as one run. If the two sides genuinely disagree it stops at that page, explains the conflict, asks you, and then asks whether to continue from where it stopped. |
| **`pull`** | Shared setups: brings the shared wiki's pages into your personal wiki, reconciling pages that differ, and picks up any new schema rules from the shared wiki's `personal-template/`. |
| **`push`** | Shared setups: sends your `public: true` pages to the shared wiki (new pages are created, differing ones reconciled — newer wins, or it asks), and adds them to the shared `index.md` and log. `public: false` pages never leave your wiki. |
| **`fetch news`** | Shared setups: read-only. Summarizes what changed in the shared wiki — optionally "since" a date you give — calling out what's actually notable rather than dumping a file list. |

### Not commands, but worth knowing

- **Questions are queries.** Ask anything; the agent searches the wiki for the key terms (browsing `index.md` only when search comes up empty), reads the relevant pages, answers with citations to the raw sources, and files a durable answer back into the wiki as a new page.
- **The agent offers to capture.** At the end of a session that produced something worth keeping, it offers — in one line — to save and ingest the chat. Saying `ingest` is the shortcut.
- **Writes take a lock.** Every command that writes holds `wiki.lock` while it does, so two agents can't write at once; `lint`, `maintain`, `push` and `pull` hold it for the whole run. On synced storage the lock is advisory (sync lag), as `AGENTS.md` explains.
- **No scheduled checks.** The agent may casually ask at a natural point whether you'd like it to `fetch news`, but it won't set up automatic polling unless you ask.

### Where each command works

| Wiki | `ingest` `lint` `maintain` | `sync` `pull` `push` `fetch news` |
|---|---|---|
| Solo wiki | ✓ | — |
| Shared wiki (the synced folder) | ✓ | — (contributors push to it from their personal wikis) |
| Personal wiki (bootstrapped from `personal-template/`) | ✓ | ✓ |

## Upgrading a wiki from 1.1.0

1. Replace the wiki's `AGENTS.md` with the new template, keeping its frontmatter values (project, mode, owner fields, `link_style`, dates) and any sections you added; delete the template-only sections the way the first run would, and add a `python:` line to the frontmatter. Copy in `schema/` (without `first-run.md`, and without `shared.md` for a solo wiki) and `tools/`. An agent can do all of this if you point it at the template and this section.
2. Say **`maintain`**. `check` reports what's out of date — the legacy `log.md`, long index lines, summaries in the index, oversized pages, superseded text above `## History` — and Maintain works through it, starting with `migrate-log`, which keeps the old log as `log/legacy-log.md`.
3. **Shared setups:** update `personal-template/` in the shared wiki too. A 1.1.0 personal wiki can't upgrade itself through Pull (its Pull only appends missing sections), so tell each person once to say: *"Upgrade this wiki's schema from `<shared>/personal-template/`, following step 5 of Pull in its `schema/sync.md`."* After that, Pull keeps it current.

## Credits

This is an implementation of Andrej Karpathy's **LLM Wiki** pattern, described in his gist: [gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The core idea, the three-layer split, and the guiding philosophy below are his — this repo turns that description into a concrete, reusable schema file plus a few operational additions covered below.

> "The human's job is to curate sources, direct the analysis, ask good questions... The LLM's job is everything else."

## What's carried over from the original

- **Three layers**: immutable raw sources → an LLM-owned wiki of markdown pages → a schema document that governs how the LLM behaves as maintainer.
- **`index.md`** — a content-oriented catalog of every page.
- **`log.md`** — an append-only chronological record of activity (here: one line per entry, in monthly `log/YYYY-MM.md` files).
- **Ingest** (add a source, update the wiki in one pass), **Query** (answer with citations, file durable answers back), and **Lint** (periodic health check for contradictions, staleness, orphans, gaps) as the core operations.
- The human/LLM division of labor as the guiding philosophy.

## What this template adds

The gist describes the pattern; this repo is a distributable schema built on top of it, with the following additions:

| Addition | What it does | Why |
|---|---|---|
| **First-run bootstrap wizard** | Scaffolds all folders and files automatically, then asks four setup questions (who you are, project name/description, solo vs. shared, Obsidian vs GitHub vs both) before doing anything else. | Turns the pattern from "a description to implement" into a template you can copy and run. |
| **Shared mode** (`mode: shared`) + **`personal-template/`** | Optional multi-person setup: a synced shared wiki plus one personal wiki per person, bootstrapped from `personal-template/`. Personal wikis `push` / `pull` / `sync` / `fetch news` against the shared one, with page pairing by path, a `public:` flag per page, and schema updates that propagate to every personal wiki on its next pull. | Lets a team build one knowledge base on a shared drive without everyone editing the same files at once. |
| **Identity & per-page `history`** | The wizard asks who you are; every page, solo or shared, carries an append-only `history` of `"YYYY-MM-DD HH:MM Lastname Firstname"` edits (in shared mode the agent also asks rather than guesses who is driving a write). | Makes edits attributable, and means any solo wiki can later become a shared one without rewriting its pages. |
| **Schema versioning** (`schema_version`, currently `1.2.2`) | The schema file carries a semantic version; every page records the version that was active at its last edit. | Shows which pages were written under which schema, so a schema change can be rolled out to the pages that predate it. |
| **Solo/shared pruning** | The one `AGENTS.md` carries both modes; at first run the agent deletes the parts that don't apply to the chosen mode. | A solo wiki doesn't carry the multi-person rules around, yet one template serves both. |
| **Bootstrap from a link** | Paste this repo's GitHub URL into an agent session in an empty folder; the agent fetches `AGENTS.md`/`CLAUDE.md` itself and runs the same wizard — no manual file copy needed. | Gets a new wiki running in one pasted link instead of a download-and-copy step. |
| **`link_style` (wikilinks vs. markdown)** | A single frontmatter setting that switches every cross-link between Obsidian-style `[[wikilinks]]` and relative markdown links, decided once at setup. | Makes the same schema work whether the wiki is read in Obsidian, on GitHub, or both. |
| **Multi-agent write lock** (`wiki.lock`) | A plaintext lock file with atomic create, staleness takeover, and a bounded retry loop, so two agent sessions can't write at once. | The original describes a single-user system; this template is built to be safe when several agents (parallel sessions, different machines) touch the same wiki. |
| **Standing rules** | Eleven explicit rules (twelve in shared mode) covering conflict resolution ("newer information wins"), tone, secrets handling, one-page-per-thing, token discipline, and more. | Encodes judgment calls once instead of re-deciding them per session. |
| **Spoken trigger commands** | Saying "ingest", "maintain" or "lint" runs that workflow immediately, no further confirmation needed (shared mode adds "sync", "push", "pull" and "fetch news"). | Removes friction for the most common actions. |
| **Cross-agent portability** | `AGENTS.md` (read natively by Codex, Gemini CLI, Aider, Zed, Devin, etc.) as the source of truth, with `CLAUDE.md` as a minimal pointer for Claude Code — plus guidance for adding similar pointers for Cursor, Windsurf, or Copilot. | The original is written as `CLAUDE.md` for a single tool; this template works the same wiki across most current coding agents. |
| **Explicit page conventions** | Required YAML frontmatter (`title`, `type`, `created`/`modified`, `sources`), slug rules, a current-state-first page shape with optional `## Open questions` and `## History` sections, size limits, citation rules, and a no-manual-line-wrap rule. | Makes every page structurally consistent and diffable, rather than leaving format to the LLM's judgment each time. |
| **Lint vs. Maintain split** + **`wiki-maintenance.md`** | **Maintain** works a backlog + changelog of technical/structural health (link format, broken links, frontmatter, naming, orphans), separate from `log.md`'s knowledge timeline; you can write plain-language structural instructions into it too. **Lint** checks only whether pages state contradicting facts, and resolves each live — newer wins, or it asks you — instead of filing it away. | Keeps mechanical clean-up and factual judgment calls apart, so findings get resolved rather than piling up unread. |
| **Token budget** (`1.2.0`) | One-line log entries in monthly `log/` files; a short index without summaries; search-first queries; incremental Lint; current-state-first pages with superseded facts in a terse `## History`; `history` compaction; first-run and rarely needed rules moved to on-demand `schema/` modules; transcripts and files copied by tool rather than re-typed; bulk reading handed to cheaper sub-agents. | Keeps cost tied to what changed rather than to the wiki's size. On a 143-page wiki: one read of the log drops from ~50k tokens to ~4k, and an incremental lint reads 10 pages in full instead of all 143. |
| **`tools/`** | A standard-library Python helper the agent runs: `check` (structural report), `scope` (lint work list), `log` / `recent` / `news`, `pair` (Push/Pull work list), `capture` (Claude Code transcript → `raw/`, secrets redacted), `lock`, `migrate-log`. `wiki.py` is the entry point; each operation lives in its own commented `wiki_*.py` file, and the tunable limits sit together in `wiki_settings.py`. | Mechanical checks done by a script cost no tokens; the agent reads a few lines of findings instead of every page. |
| **`parties/` vs `entities/` vs `concepts/` split** | Wiki pages are sorted by a concrete test ("would this exist if the project didn't?") instead of one generic entity/concept bucket. | Keeps person/org pages (which shouldn't duplicate across projects) distinct from project-internal artifacts. |
| **Dedicated `summaries/` and `assets/` folders** | One page per raw source lives in `summaries/`; agent-generated diagrams/charts live in `assets/`, separate from ingested knowledge. | Keeps generated-from-source content and agent-authored artifacts out of the general wiki namespace. |


## License

MIT — see [LICENSE](LICENSE). The pattern itself is Karpathy's; this repo licenses the template implementation.
