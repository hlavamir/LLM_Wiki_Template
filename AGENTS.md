---
schema_version: "1.2.2"             # version of THIS schema (see Notes); stamped into each page's `schema_version` on every edit
project: "{{PROJECT_NAME}}"        # set at first run
mode: "{{solo|shared}}"             # set at first run — 'solo' (one person) or 'shared' (synced wiki for several people)
owner_name: "{{FULL_NAME}}"         # solo mode only — 'Lastname Firstname'
owner_nickname: "{{NICKNAME}}"      # solo mode only — short display name
repo_path: "{{REPO_PATH_OR_NONE}}"  # solo mode only — local path to a related code repo, or "none"
python: "{{PYTHON_COMMAND}}"        # hint: the command that last ran tools/wiki.py (python3 | python | py), or "none" — see Tools
type: schema
created: {{YYYY-MM-DD}}
modified: {{YYYY-MM-DD}}
link_style: "{{wikilinks|markdown}}"
---

<!-- TEMPLATE FILE. Copy this repo's files (all but README.md, LICENSE, .git) into an empty folder and start an agent session there — or paste this repo's GitHub link into a session in an empty folder (see 'Bootstrapping from a link'). The first run fills the placeholders above, scaffolds the wiki, and prunes everything template-only from this file, including this comment. -->

# LLM Wiki — Schema

This folder is an **LLM-maintained knowledge wiki** following Andrej Karpathy's *LLM Wiki* pattern (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Any agent working here reads this file first and acts as a disciplined wiki maintainer, not a generic chatbot. Knowledge is **compiled once and kept current**, not re-derived on every query: the human curates sources and asks questions; the agent owns the wiki.

<!-- shared-only -->This is the **shared** half of a shared+personal pair: the team's synced wiki. Each person also keeps a **personal** wiki on their own machine, bootstrapped from `personal-template/`, that pushes to and pulls from this one — read `schema/shared.md` before handling contributor pages, onboarding someone, or changing the schema.<!-- /shared-only -->

**About this wiki:** {{PROJECT_ONE_LINE}}

<!-- template-only -->
## Bootstrapping from a link (no local files yet)

If the user pasted a GitHub URL to this template, or asked you to set up a wiki from it, in an empty folder (no `AGENTS.md` on disk — you fetched this file), they want a new wiki here. If you need their go-ahead to download, ask once in one plain sentence ("Shall I set up a new LLM wiki in this folder?"); then:

1. **Get the files.** Preferred: `git clone --depth 1 <url> <temporary folder>` (add `--branch <branch>` for a `…/tree/<branch>` URL), copy everything except `README.md`, `LICENSE` and `.git` into this folder, delete the temporary clone. Without git: work out `owner`/`repo`/`branch` (no branch in the URL → `default_branch` from `https://api.github.com/repos/<o>/<r>`, falling back to `main`, then `master`) and download each file below from `https://raw.githubusercontent.com/<o>/<r>/<branch>/<path>` with a download command (`curl -fsSL -o <path> <url>`, `Invoke-WebRequest -OutFile`) — never by re-typing content:
   `AGENTS.md`, `CLAUDE.md`, `schema/first-run.md`, `schema/lock.md`, `schema/lint.md`, `schema/maintain.md`, `schema/shared.md`, `tools/wiki.py`, `tools/wiki_settings.py`, `tools/wiki_common.py`, `tools/wiki_maintain.py`, `tools/wiki_lint.py`, `tools/wiki_log.py`, `tools/wiki_sync.py`, `tools/wiki_ingest.py`, `tools/wiki_lock.py`, `personal-template/AGENTS.md`, `personal-template/README.md`, `personal-template/schema/first-run.md`, `personal-template/schema/sync.md`
2. **Start the wizard now, in this session.** Read `schema/first-run.md` and begin it — the user should not have to ask again or start a new session. Don't report the download beyond half a sentence ("Got the template — let's set up your wiki."). The wiki is a fresh instance, not a fork: no `.git`, `README.md` or `LICENSE`.

## First run

No scaffold yet (no `index.md` or `wiki/` next to this file)? Read `schema/first-run.md` and follow it. It deletes this section and the one above when done.
<!-- /template-only -->

## Layout

```
<wiki-root>/
├── AGENTS.md            # this schema (CLAUDE.md is a one-line pointer to it, for Claude Code)
├── schema/              # on-demand modules — read only when the operation needs them:
│   ├── lock.md          #   wiki.lock protocol details and manual fallback
│   ├── lint.md          #   the Lint operation
│   ├── maintain.md      #   the Maintain operation
│   └── shared.md        #   shared mode only — notes for the shared half of a shared+personal pair
├── tools/               # mechanical helper: wiki.py (entry point) + one wiki_*.py per operation (see Tools)
├── index.md             # catalog of pages — browse it; search first
├── log/YYYY-MM.md       # append-only one-line timeline, one file per month
├── wiki-maintenance.md  # structural backlog + changelog (Maintain)
├── raw/                 # immutable sources — read, never edited
├── personal-template/   # shared mode only — bootstrap for each person's personal wiki
└── wiki/
    ├── parties/         # real-world people & organizations
    ├── entities/        # project-internal named artifacts
    ├── concepts/        # recurring themes, techniques, decisions
    ├── summaries/       # one page per raw source
    └── assets/          # agent-generated diagrams/charts
```

`raw/` is the source of truth — one file per ingested source, possibly sensitive, never edited. `wiki/` is agent-owned and edited freely. This file holds conventions and workflows; co-evolve it with the user. `wiki.lock` appears at the root only while an agent writes.

**Where a page goes** — the load-bearing test is *"Would this exist if the project didn't?"*

| Folder | What | Examples |
|---|---|---|
| `parties/` | A real-world **person or organization** existing independently of the project | a person, client, vendor, team |
| `entities/` | A concrete **named artifact that exists only because of the project** | a file, class, tool, plugin, system, config |
| `concepts/` | A recurring **theme, technique, or decision** spanning sources | a pattern, an approach, a design choice |
| `summaries/` | **One page per raw source**, same slug as its `raw/` file | one per ingested chat/doc/code |
| `assets/` | Artifacts the agent **generates** (not ingested); embed per `link_style` | `pipeline-flow.svg` |

Regroup `wiki/` by another axis (time, module, client) only when the domain clearly needs it.

## Page conventions

- **Frontmatter** on every wiki page:
  ```yaml
  ---
  title: "..."
  type: party | entity | concept | summary
  created: YYYY-MM-DD
  modified: YYYY-MM-DD
  schema_version: "X.Y.Z"      # this file's schema_version at the page's last edit
  sources: [<raw-slug>, ...]   # raw sources the page draws on (omit if none)
  history:                     # one entry per edit, oldest first
    - "YYYY-MM-DD HH:MM Lastname Firstname"
  ---
  ```
  Every content edit bumps `modified`, refreshes `schema_version` and appends a `history` entry (24-hour time, the editor's full name surname-first<!-- solo-only --> — always `owner_name` here; keeping it means the wiki can go shared later untouched<!-- /solo-only --><!-- shared-only --> — whoever's session writes, see rule 12<!-- /shared-only -->). Never rewrite or reorder past entries; the one exception is compaction: past 20 entries, Maintain folds the oldest into a single `"YYYY-MM-DD..YYYY-MM-DD N edits (Name A, Name B)"` entry. Pages that predate a field get no backfilled value — the next real edit adds it. If it's unclear how to split someone's name, ask.<!-- shared-only --> A page copied here verbatim by a Push keeps its `history` and `schema_version`; only a content change, including a reconciliation, is an edit.<!-- /shared-only -->
- **Page shape — current state first.** After the frontmatter: `# Title`, then what is true *now* (what a query reads). Then, only when non-empty: `## Open questions` (remove items once answered) and `## History` — one line per superseded fact, e.g. `- 2026-07-14 → 2026-08-05: capture ran every frame; now on demand (src-slug)`. raw/ keeps the full old text, so History stays terse. Limits: about **8 KB above `## History`** (beyond that, split into linked sub-pages) and **4 KB of History** (beyond that, condense).
- **Links** follow `link_style`: `wikilinks` → `[[slug]]` (Obsidian only); `markdown` → relative links with extension, `[Acme](../parties/acme.md)` (GitHub and Obsidian). Never mix; a style change is a Maintain task.
- **Slugs:** lowercase, hyphenated, no spaces.<!-- shared-only --> Keep the same path for the same topic here and in every personal wiki — Push/Pull pair pages by identical relative path.<!-- /shared-only -->
- **Citations:** cite the raw slug a claim comes from.<!-- shared-only --> A page synthesized from contributors' pages cites `synthesized_from:` (owner + page) in frontmatter instead of linking to their personal wikis.<!-- /shared-only -->
- **No manual line-wrapping** in any markdown file here: one line per paragraph; viewers soft-wrap.

## Standing rules

1. **Metadata.** Set `created` once; every edit updates `modified`, `history` and `schema_version` (Page conventions).
2. **Newer information wins.** When sources conflict, the more recent is authoritative. Move the superseded fact to the page's `## History` with its dates and source — never silently delete it.
3. **Ask, don't assume.** Unclear → ask. Park unresolved uncertainty in `## Open questions`.
4. **Rigor over comfort.** Question inputs; flag inconsistencies, risks and weak reasoning.
5. **Tone.** Friendly but direct; no empty praise. (Users can ask for a different tone; don't prompt for it.)
6. **One thing = one page.** Each party, entity or concept has exactly one page; everything else links to it rather than repeating its details.
7. **Never store secrets** in `raw/` or `wiki/` — API keys, tokens, passwords, credentials. Reference them by location only ("key in `api_key.txt`, gitignored").
8. **Offer to capture.** At the end of a session that produced durable knowledge (a decision, a fix, a new fact, a resolved question), offer in one line to save and ingest the chat. The word **"ingest"** runs Ingest on the current conversation, no confirmation needed.
9. **Standing commands.** **"lint"** runs Lint (factual consistency — `schema/lint.md`); **"maintain"** runs Maintain (structure — `schema/maintain.md`). Each starts immediately; read its module first. Keep the two separate: Lint never files to `wiki-maintenance.md`, Maintain never judges facts.
10. **Lock before writing, not before thinking.** Every write — Ingest, Query write-back, Lint, Maintain, first run<!-- shared-only -->, contributors' Push<!-- /shared-only --> — holds `wiki.lock` (see Tools; details in `schema/lock.md`). Research, drafting and waiting on the user happen unlocked. Single-item writes take the lock right before the first file write and release it right after the last; Lint and Maintain hold it for the whole run. Always release, including on failure.
11. **Spend tokens like they cost money.** Search before you read (`rg`/grep, or a configured search tool) and read only the pages — and the parts of pages — that matter; skip `## History` unless the question is about the past. Edit pages with targeted edits, never full rewrites. Copy files and transcripts with commands or tools; never re-type content you can copy. Don't re-read what you just wrote. Hand bulk reading (a Query spanning many pages, Lint comparisons) to a sub-agent on a smaller model when your tool can spawn one, and keep only its conclusions and page paths; writes stay with the main session. Leave mechanical checks to `tools/wiki.py`.
<!-- shared-only -->12. **Know who you're chatting with.** Every `history` entry needs a real "Lastname Firstname". A name established earlier in the session, or `synthesized_from:` provenance, is enough; if you're genuinely unsure who drives a write, ask — never write "user" or "unknown".<!-- /shared-only -->

## Tools

`tools/` (Python 3, standard library only) does the mechanical work so the agent doesn't spend tokens on it. `tools/wiki.py` is the one entry point; the `wiki_*.py` files beside it hold one operation each. Run it as `<python> tools/wiki.py <command>`. Its output is terse by design — read it, don't re-derive it.

**Finding `<python>`.** The frontmatter's `python:` is a hint — the command that worked on the machine that last set it — not a guarantee<!-- shared-only -->: a shared wiki is opened from many machines<!-- /shared-only -->. Use it; if it fails ("not found", or Windows' Store stub saying "Python was not found"), try `python3`, `python`, `py` in turn and use the first that reports Python 3.8+ for the rest of the session.<!-- solo-only --> If that differs from `python:`, update `python:`.<!-- /solo-only --><!-- shared-only --> Don't rewrite `python:` for your machine — it would only break the next person's.<!-- /shared-only --> `python: none` means none was found when it was last checked: try the three once per session anyway, in case Python has been installed since. Nothing works → do the work by hand following the modules.

| Command | Use |
|---|---|
| `check [--full]` | Maintain's structural report: frontmatter, naming, broken links, link style, orphans, index, log, page sizes, history length, secrets |
| `scope [--since D \| --all]` | Lint's work list: pages changed since the last lint and what to compare each with |
| `log <op> "<title>" [--link L]` | Append one entry to `log/YYYY-MM.md` |
| `recent [N]` | The last N log entries |
| `news [--since D]` | Pages by `modified`, newest first, plus log entries since D |
| `capture --out raw/<slug>.md` | Write the current Claude Code session's transcript to raw/ (tool output omitted, secrets redacted) |
| `lock acquire --op <op> --session <id>` / `lock release --session <id>` | The `wiki.lock` protocol; generate one random session id per conversation and reuse it |
| `migrate-log` | One-time: turn a pre-1.2.0 multi-line `log.md` into `log/` files |

Don't customize `tools/` per wiki; improve the template's copy instead.

## Operations

### Ingest (add a source)
1. **Capture** to `raw/<slug>.md` without re-typing it. The current conversation: `capture --out raw/<slug>.md` in Claude Code; in other agents, their own transcript export; write it out by hand only as a last resort. A file: copy it, or convert it with a tool (pandoc, pdftotext, markitdown). A web page: save what you fetched. Note `*Captured: YYYY-MM-DD*` and, for external sources, the origin URL/path. Never edit a raw file afterward; check it for secrets (rule 7).
2. **Summarize** to `wiki/summaries/<slug>.md`: context, key facts, decisions, resolution, open questions. Write it from what you already have — don't re-read a capture of the conversation you're in.
3. **Update** the affected `parties/`, `entities/` and `concepts/` pages with targeted edits — new facts in the current-state part, superseded ones to `## History` — and cross-link per `link_style`.
4. **Index** each new non-summary page with one line (see Navigation).
5. **Log** it: `log ingest "<title>" --link <summary link>`.

### Query (answer a question)
1. **Search first:** grep the key terms across `wiki/` (`rg -il "<term>" wiki`) or use the configured search tool. Open `index.md` only to browse, or when search finds nothing.
2. Read the matching pages' current state. More than a handful of pages → delegate the reading (rule 11).
3. Answer with citations to raw slugs.<!-- solo-only --> Code in `repo_path` (when not `none`) is a source you may read for the answer, never edit.<!-- /solo-only -->
4. File durable answers back as a new or updated page (index line, `log query "<title>" --link <page>`).

### Lint and Maintain
- **Lint** — are the facts across pages consistent? Incremental by default: only pages changed since the last lint, compared with the pages they share a new source with or link to. Contradictions are resolved live (rule 2, otherwise ask the user), never filed for later. Say "lint all" for a full sweep. Steps: `schema/lint.md`.
- **Maintain** — is the structure sound? Runs `check`, files findings in `wiki-maintenance.md`'s **Open tasks** (where the owner can also write plain-language structural instructions), and works through every open task until each is closed or waiting on the user. Steps: `schema/maintain.md`.

## Navigation

- **`index.md`** — catalog grouped by category, one line per page: `- <link> — <short clause>`, at most 120 characters. Summaries and raw files stay out (pages reach summaries through `sources:`, the log links them). Past 300 lines, Maintain splits it into `index/<category>.md` files linked from `index.md`.
- **`log/YYYY-MM.md`** — append-only, one line per entry: `## [YYYY-MM-DD] <ingest|query|lint|init|maintain<!-- shared-only -->|push<!-- /shared-only -->> | <title> → <link>`. Details live in the linked page, never in the log. Append with `tools/wiki.py log` (or a UTF-8 shell append); never read a log file whole — `recent` or `rg "^## \[2026-10" log` instead. `log/legacy-log.md`, if present, is a pre-1.2.0 archive: never read it in normal operation.
- **`wiki-maintenance.md`** — Maintain's backlog: `## Open tasks` (found issues and owner instructions) and an append-only `## Log` of what was done.

## Notes

- **Schema versioning** (semver): PATCH for wording, MINOR for additive changes, MAJOR for changes that make existing pages or workflows non-conforming. Bump `schema_version` on every change to this file or `schema/`; pages keep their old value until next edited, which shows what was written under which schema. History: `1.0.0` original; `1.1.0` shared mode, `history`, `schema_version`; `1.2.0` token budget — one-line monthly logs, short index without summaries, search-first Query, incremental Lint, `tools/wiki.py`, current-state-first pages with `## History`, history compaction, on-demand `schema/` modules; `1.2.1` `python:` treated as a hint with a fallback, `tools/` split into one file per operation; `1.2.2` plain-language setup wizard asking one question at a time (clickable where the agent supports it), started in the same session as the download. A wiki upgraded from 1.1.0 has `check` findings until Maintain migrates it (`schema/maintain.md`, "Upgrading").
- Plain markdown: git-friendly, Obsidian-friendly with `link_style: wikilinks`.
- Optional extras — `overview.md`/`synthesis.md`, graph colour tags, a `sensitive:` flag, scheduled ingest, a search tool or MCP server — only when the user asks. A search tool pays for itself past ~50 pages.
- **`AGENTS.md` is the single source of truth**; most agents (Codex CLI, Gemini CLI, Aider, Zed, Devin, …) read it natively. Claude Code reads `CLAUDE.md`, a pointer whose `@AGENTS.md` import loads this file with the project instructions (no extra Read). For tools that expect another filename (`.cursor/rules/`, `.windsurfrules`, `.github/copilot-instructions.md`), add a similar pointer — never a copy.
