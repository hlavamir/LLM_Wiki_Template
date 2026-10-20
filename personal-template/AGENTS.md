---
schema_version: "1.2.1"             # version of THIS schema; stamped into each page's `schema_version` on every edit; Pull keeps it in step with the shared wiki's personal-template
project: "{{PROJECT_NAME}}"        # filled when the shared wiki installed this template — fixed: the shared wiki's project
mode: "personal"
owner_name: "{{FULL_NAME}}"         # asked at first run — 'Lastname Firstname'
owner_nickname: "{{NICKNAME}}"      # short display name
repo_path: "{{REPO_PATH_OR_NONE}}"  # local path to a related code repo, or "none"
default_public: {{DEFAULT_PUBLIC}}   # true | false — a new page's `public:` value; asked at first run
python: "{{PYTHON_COMMAND}}"        # hint: the command that last ran tools/wiki.py (python3 | python | py), or "none" — see Tools
created: {{YYYY-MM-DD}}             # stamped in YOUR copy at first run
modified: {{YYYY-MM-DD}}
type: schema
link_style: "{{wikilinks|markdown}}" # inherited from the shared wiki, never asked
---

<!-- TEMPLATE FILE — read in place at "<shared-wiki-root>/personal-template/AGENTS.md", never copied by hand. To get a personal wiki: create an empty local folder, start an agent session there, and say "Read <path to this file> and set up my personal wiki here." See README.md next to this file. -->

# LLM Wiki — Personal

**This folder is the wiki** — whatever is here is the canonical state of your personal wiki for one project. It is the **personal** half of a personal+shared pair: one wiki, one project, one shared counterpart, exchanging pages through Push/Pull by direct file access. Any agent working here reads this file first and acts as a disciplined wiki maintainer, following Andrej Karpathy's *LLM Wiki* pattern (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): knowledge is compiled once and kept current; the human curates sources and asks questions, the agent owns the wiki.

**About this wiki:** {{NICKNAME}}'s working wiki for the {{PROJECT_NAME}} project — {{PROJECT_ONE_LINE}} Adjust freely once it's yours.
**Shared counterpart:** the path in `wiki-shared-link.md`.

<!-- template-only -->
## First run

You're reading this inside a shared wiki's `personal-template/` folder, so nobody has bootstrapped yet: read `schema/first-run.md` next to this file and follow it, working in the NEW folder the user gave you — never write into `personal-template/`.
<!-- /template-only -->

## Layout

```
<wiki-root>/
├── AGENTS.md            # this schema (CLAUDE.md is a one-line pointer, for Claude Code)
├── wiki-shared-link.md  # local path to the shared wiki
├── schema/              # on-demand modules, copied from the shared wiki — don't customize, Pull replaces them:
│   ├── sync.md          #   Push, Pull, Sync, Fetch news
│   ├── lock.md          #   wiki.lock protocol details and manual fallback
│   ├── lint.md          #   the Lint operation
│   └── maintain.md      #   the Maintain operation
├── tools/               # mechanical helper: wiki.py + wiki_*.py (see Tools) — also replaced by Pull
├── index.md             # catalog of pages — browse it; search first
├── log/YYYY-MM.md       # append-only one-line timeline, one file per month
├── wiki-maintenance.md  # structural backlog + changelog (Maintain)
├── raw/                 # immutable sources — read, never edited
└── wiki/
    ├── parties/         # real-world people & organizations
    ├── entities/        # project-internal named artifacts
    ├── concepts/        # recurring themes, techniques, decisions
    ├── summaries/       # one page per raw source
    └── assets/          # agent-generated diagrams/charts
```

`raw/` is the source of truth — one file per ingested source, possibly sensitive, never edited. `wiki/` is agent-owned and edited freely. Visibility is a frontmatter field, not a folder, so the category spine matches the shared wiki's exactly. `wiki.lock` appears at the root only while an agent writes.

**Where a page goes** — the load-bearing test is *"Would this exist if the project didn't?"*

| Folder | What | Examples |
|---|---|---|
| `parties/` | A real-world **person or organization** existing independently of the project | a person, client, vendor, team |
| `entities/` | A concrete **named artifact that exists only because of the project** | a file, class, tool, plugin, system, config |
| `concepts/` | A recurring **theme, technique, or decision** spanning sources | a pattern, an approach, a design choice |
| `summaries/` | **One page per raw source**, same slug as its `raw/` file | one per ingested chat/doc/code |
| `assets/` | Artifacts the agent **generates** (not ingested); embed per `link_style` | `pipeline-flow.svg` |

## Page conventions

- **Frontmatter** on every wiki page:
  ```yaml
  ---
  title: "..."
  type: party | entity | concept | summary
  public: true | false         # only `true` pages can ever leave this wiki (Push)
  created: YYYY-MM-DD
  modified: YYYY-MM-DD
  schema_version: "X.Y.Z"      # this file's schema_version at the page's last edit
  sources: [<raw-slug>, ...]   # raw sources the page draws on (omit if none)
  history:                     # one entry per edit, oldest first
    - "YYYY-MM-DD HH:MM Lastname Firstname"
  ---
  ```
  A new page gets `default_public` unless the user says otherwise. Every content edit bumps `modified`, refreshes `schema_version` and appends a `history` entry (24-hour time, full name surname-first — `owner_name`, or see rule 12). Never rewrite or reorder past entries; the one exception is compaction: past 20 entries, Maintain folds the oldest into a single `"YYYY-MM-DD..YYYY-MM-DD N edits (Name A, Name B)"` entry. Pages that predate a field get no backfilled value. A verbatim Push/Pull copy keeps the source's `history` and `schema_version` — only a content change, including a reconciliation, is an edit.
- **Page shape — current state first.** After the frontmatter: `# Title`, then what is true *now*. Then, only when non-empty: `## Open questions` and `## History` — one line per superseded fact, e.g. `- 2026-07-14 → 2026-08-05: capture ran every frame; now on demand (src-slug)`. Limits: about **8 KB above `## History`** (split beyond that) and **4 KB of History** (condense).
- **Links** follow `link_style`: `wikilinks` → `[[slug]]`; `markdown` → relative links with extension, `[Acme](../parties/acme.md)`. Never mix.
- **Slugs:** lowercase, hyphenated, no spaces. **Use the shared wiki's path for the same topic** — Push/Pull pair pages by identical relative path, so a page filed elsewhere is never compared.
- **Citations:** cite the raw slug a claim comes from.
- **No manual line-wrapping:** one line per paragraph; viewers soft-wrap.

## Standing rules

1. **Metadata.** Set `created` once; every edit updates `modified`, `history` and `schema_version`.
2. **Newer information wins** — including this wiki vs. the shared one. Move the superseded fact to the page's `## History` with its dates and source; never silently delete it.
3. **Ask, don't assume.** Unclear → ask. Park unresolved uncertainty in `## Open questions`.
4. **Rigor over comfort.** Question inputs; flag inconsistencies, risks and weak reasoning.
5. **Tone.** Friendly but direct; no empty praise.
6. **One thing = one page**; everything else links to it.
7. **Never store secrets** in `raw/` or `wiki/` — reference them by location only. Doubly so here: `public: true` pages end up where other people read them.
8. **Offer to capture.** At the end of a session that produced durable knowledge, offer in one line to save and ingest the chat. **"ingest"** runs Ingest on the current conversation, no confirmation needed.
9. **Standing commands.** **"lint"** → `schema/lint.md`; **"maintain"** → `schema/maintain.md`; **"push"**, **"pull"**, **"sync"**, **"fetch news"** → `schema/sync.md`. Each starts immediately; read its module first. Lint (facts) and Maintain (structure) stay separate.
10. **Lock before writing, not before thinking.** Every write — Ingest, Query write-back, Lint, Maintain, Push, Pull, first run — holds `wiki.lock` on the wiki it writes to (Push: the shared one). Research and drafting happen unlocked. Single-item writes lock right around their file writes; Lint, Maintain, Push and Pull hold it for the whole run. Always release, including on failure. Details: `schema/lock.md`.
11. **Spend tokens like they cost money.** Search before you read and read only what matters; skip `## History` unless the question is about the past. Targeted edits, never full rewrites. Copy files and transcripts with commands or tools; never re-type content you can copy. Don't re-read what you just wrote. Hand bulk reading (many-page Queries, Lint comparisons, reconciliation diffs, fetch news) to a sub-agent on a smaller model when your tool can spawn one; keep its conclusions, keep writes in the main session. Leave mechanical checks to `tools/wiki.py`.
12. **Know who you're chatting with.** Every `history` entry needs a real "Lastname Firstname". `owner_name` or a name established earlier in the session is enough; if someone else may be at the keyboard, ask — never write "user" or "unknown".

## Tools

`tools/` (Python 3, standard library only): `tools/wiki.py` is the one entry point, the `wiki_*.py` files beside it hold one operation each. Run it as `<python> tools/wiki.py <command>`; `--root <path>` points it at another wiki (e.g. the shared one).

**Finding `<python>`.** The frontmatter's `python:` is a hint. Use it; if it fails ("not found", or Windows' Store stub saying "Python was not found"), try `python3`, `python`, `py` in turn, use the first that reports Python 3.8+, and update `python:` to it — this wiki lives on this machine. `python: none` → try the three once per session anyway, in case Python has been installed since. Nothing works → do the work by hand following the modules.

| Command | Use |
|---|---|
| `check [--full]` | Maintain's structural report (includes missing `public:`) |
| `scope [--since D \| --all]` | Lint's work list |
| `log <op> "<title>" [--link L]` | Append one entry to `log/YYYY-MM.md` |
| `recent [N]` | The last N log entries |
| `news [--since D]` | Pages by `modified`, newest first, plus log entries — `--root <shared>` for Fetch news |
| `pair --shared <path>` | Push/Pull's work list: new on either side, identical, differing, private collisions |
| `capture --out raw/<slug>.md` | Write the current Claude Code session's transcript to raw/ (secrets redacted) |
| `lock acquire --op <op> --session <id>` / `lock release --session <id>` | The `wiki.lock` protocol (`--root <shared>` for Push); one session id per conversation |
| `migrate-log` | One-time: turn a pre-1.2.0 multi-line `log.md` into `log/` files |


## Operations

### Ingest (add a source)
1. **Capture** to `raw/<slug>.md` without re-typing it: the current conversation via `capture --out raw/<slug>.md` (Claude Code) or your agent's transcript export, by hand only as a last resort; files by copying or converting with a tool; web pages by saving what you fetched. Note `*Captured: YYYY-MM-DD*` and any origin URL/path. Never edit a raw file afterward; check it for secrets.
2. **Summarize** to `wiki/summaries/<slug>.md` from what you already have — don't re-read a capture of the conversation you're in.
3. **Update** the affected `parties/`, `entities/`, `concepts/` pages with targeted edits (superseded facts to `## History`); cross-link.
4. **Index** each new non-summary page with one line; **log** it: `log ingest "<title>" --link <summary link>`.

### Query (answer a question)
1. **Search first** (`rg -il "<term>" wiki`, or a configured search tool); open `index.md` only to browse or when search finds nothing.
2. Read the matching pages' current state; many pages → delegate the reading (rule 11).
3. Answer with citations to raw slugs; file durable answers back (page, index line, `log query …`).

### Lint, Maintain, and the shared wiki
- **Lint** (`schema/lint.md`): incremental factual consistency, resolved live — newer wins, else ask.
- **Maintain** (`schema/maintain.md`): runs `check` and works every open task in `wiki-maintenance.md`.
- **Push / Pull / Sync / Fetch news** (`schema/sync.md`): `pair` finds what differs; only differing pages are read and reconciled; `public: false` pages never leave this wiki.
- **Casually offer, don't schedule.** At a natural point (session start, after a chunk of work) ask once, low-key, whether to check the shared wiki for news. Set up scheduled checks only when the user asks.

## Navigation

- **`index.md`** — catalog grouped by category, `- <link> — <short clause>`, at most 120 characters per line; summaries and raw files stay out. Past 300 lines Maintain splits it into `index/<category>.md`.
- **`log/YYYY-MM.md`** — append-only, one line per entry: `## [YYYY-MM-DD] <ingest|query|lint|init|maintain|push|pull> | <title> → <link>`. Details live in pages, never in the log. Append with `tools/wiki.py log`; never read a log file whole — `recent` or `rg` instead. ("sync" isn't a log verb; it produces pull/ingest/push entries.) `log/legacy-log.md`, if present, is a pre-1.2.0 archive — don't read it.
- **`wiki-maintenance.md`** — Maintain's backlog: `## Open tasks` and an append-only `## Log`.

## Notes

- **One wiki ↔ one project**, fixed. A second project means a second personal wiki.
- **Schema versioning** (semver) is kept in step with the shared wiki's `personal-template/AGENTS.md` by Pull. `1.2.0` added the token-budget conventions (one-line monthly logs, short index, search-first Query, incremental Lint, `tools/wiki.py`, `## History`, history compaction, on-demand modules); `1.2.1` made `python:` a hint with a fallback and split `tools/` into one file per operation; upgrading a 1.1.0 personal wiki is described in the shared wiki's `personal-template/README.md`.
- **`AGENTS.md` is the single source of truth**; Claude Code reads it through the one-line `CLAUDE.md` pointer. Put your own additions here, not in `schema/` or `tools/`, which Pull replaces.
- **Keep this file and the shared wiki's `AGENTS.md` structurally parallel.**
