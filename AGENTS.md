---
schema_version: "1.1.0"             # version of THIS schema file (see 'Notes' — bump on every schema change); stamped into each page's own `schema_version` on every edit
project: "{{PROJECT_NAME}}"        # set at first run
mode: "{{solo|shared}}"             # set at first run — 'solo' (one person) or 'shared' (synced wiki for several people); see 'First run' below
owner_name: "{{FULL_NAME}}"         # solo mode only — asked at first run, written 'Lastname Firstname'
owner_nickname: "{{NICKNAME}}"      # solo mode only — short display name
repo_path: "{{REPO_PATH_OR_NONE}}"  # solo mode only — local path to a related code repo on this machine, or "none"
type: schema
created: {{YYYY-MM-DD}}             # stamped at first run
modified: {{YYYY-MM-DD}}
link_style: "{{wikilinks|markdown}}" # set at first run — see 'First run' below
---

<!-- TEMPLATE FILE. This is the full schema, read natively by most coding agents (Codex CLI, Gemini CLI, Aider, Zed, Devin, and others) via the AGENTS.md convention. Claude Code reads CLAUDE.md instead of AGENTS.md, so a one-line pointer file ships alongside this one for that purpose — see the Notes section below if you need a similar pointer for another tool (Cursor, Windsurf, Copilot, …). Copy this AGENTS.md and CLAUDE.md into a dedicated, empty folder, then start an agent session there and ask it to read this schema — or, in that empty folder, just paste this repo's GitHub link into the chat (see 'Bootstrapping from a link' below) and the agent will fetch the two files itself. On first run the agent asks the setup questions (who you are, project name, solo vs. shared, link style), fills the placeholders above, scaffolds the wiki, and then prunes the mode-specific parts of this file: spans fenced by HTML-comment markers named shared-only or solo-only (closed by /shared-only or /solo-only) are kept or removed depending on the chosen mode — see 'First run', step 7. -->

# LLM Wiki — Schema

This folder is an **LLM-maintained knowledge wiki**. Any agent working here **reads this file first** and acts as a disciplined wiki maintainer — not a generic chatbot. It follows Andrej Karpathy's *LLM Wiki* pattern (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

The wiki is a persistent, compounding knowledge base: knowledge is **compiled once and kept current**, not re-derived on every query. The human curates sources and asks questions; the agent owns and maintains the wiki.

<!-- shared-only -->This is the **shared** half of a shared+personal pair: this folder is the team's synced wiki, and each person working on the project also keeps their own **personal** wiki (a separate folder on their own machine, bootstrapped from `personal-template/` — see 'Shared-wiki notes' below).<!-- /shared-only -->

**About this wiki:** {{PROJECT_ONE_LINE}}   <!-- one-line purpose, set at first run -->

---

## Bootstrapping from a link (no local files yet)

You may be reading this file because a user pasted a bare GitHub URL to this template as their entire first message, in an empty working directory that has **no `AGENTS.md`/`CLAUDE.md` on disk yet** — you got here by fetching that URL, not by reading a local file. If that's the situation, do this before anything else:

1. **Normalize the URL** to `owner`, `repo`, and `branch`:
   - `https://github.com/<owner>/<repo>` → no branch given, use the repo's default branch.
   - `https://github.com/<owner>/<repo>/tree/<branch>` → branch given explicitly.
   - `https://github.com/<owner>/<repo>.git` → no branch given, use the repo's default branch.
   - When no branch is given, fetch `https://api.github.com/repos/<owner>/<repo>` and read `default_branch` (fall back to `main`, then `master`, if that call fails).
2. **Fetch and write two files**, verbatim and unmodified, into the current directory:
   - `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/AGENTS.md` → `./AGENTS.md`
   - `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/CLAUDE.md` → `./CLAUDE.md`

   Remember `owner`/`repo`/`branch` — if the user later picks **shared** mode, `personal-template/` is fetched from the same place (see First run, step 8).
3. Tell the user in one line what you fetched and from where, then continue immediately into **First run — bootstrap & setup** below — you now have a local `AGENTS.md`, so proceed exactly as if you'd read it from disk.

Don't clone the whole repo, and don't carry over its `.git`, `README.md`, or `LICENSE` — this wiki is a fresh instance of the schema, not a fork of the template repo.

If `AGENTS.md`/`CLAUDE.md` are already on disk in this folder, skip this section entirely.

---

## First run — bootstrap & setup

If there is **no scaffold yet** in this folder (no sibling `index.md` / `wiki/`), this is a first run. Do the following, in order. Hold `wiki.lock` (operation `init`, see **Concurrency lock**) around the writes, per standing rule 10.

1. **Scaffold** these siblings of this file:
   - `index.md`, `log.md`, `wiki-maintenance.md`
   - `raw/`
   - `wiki/parties/`, `wiki/entities/`, `wiki/concepts/`, `wiki/summaries/`, `wiki/assets/`
   (Create the folders with a `.gitkeep` if empty. Seed `index.md` and `log.md` with a heading, and `wiki-maintenance.md` with its two sections: `## Open tasks` and `## Log`.)
2. **Setup question 1 — who am I talking with?** Ask for three things: (a) your **full name** — written `Lastname Firstname` wherever the schema attributes an edit to you; if it's ambiguous how to split it (a multi-word surname, someone going by one name), ask rather than guess — (b) a **nickname / display name** for casual reference, (c) the **local path of a related code repository** on this machine, or `none`. You may propose a draft for (a)/(b) from context (e.g. `git config user.name`), but present it as a proposal to confirm, never as a fact. The full name goes into every page's `history` entries from here on (see Page conventions), in both modes.
3. **Setup question 2 — name & description.** Scan the current context — folder name, README/manifest, git remote, top-level files — and draft a project **name** and a one-line **description**. Present:
   > **a)** use the proposed name & description   **b)** write your own
4. **Setup question 3 — just you, or several people?** Ask:
   > **a)** just me — one local wiki   **b)** shared — a synced wiki several people maintain together
   - **a) solo** → `mode: solo`. Nothing else to set up.
   - **b) shared** → `mode: shared`. This folder becomes the **shared wiki**, so it must live on storage every collaborator can reach and that syncs between machines (a Google Shared Drive, OneDrive/SharePoint, Dropbox, a network share…) — confirm that it does before continuing, and mention that `wiki.lock` is only *advisory* on sync-based storage (see **Concurrency lock**). Each person then keeps a **personal wiki** in their own folder on their own machine and exchanges knowledge with this one via Push/Pull (set up in step 8). If the user isn't sure, suggest starting solo — nothing is lost by it, but moving a solo wiki to shared later is a manual job.
5. **Setup question 4 — how will the wiki be viewed?** Ask the user:
   > **a)** Obsidian (or another `[[wikilink]]`-aware viewer) only   **b)** pushed to GitHub / viewed in a plain browser   **c)** both
   This decides the link syntax (see **Links** under Page conventions):
   - **a) Obsidian-only** → use `[[wikilinks]]` everywhere.
   - **b) GitHub/browser** → use standard markdown links `[text](../folder/file.md)` (relative, with extension) — GitHub does not render `[[wikilinks]]` outside its wiki feature.
   - **c) Both** → use markdown links `[text](../folder/file.md)` (renders correctly in both Obsidian and GitHub); avoid `[[wikilinks]]`.
   In shared mode this answer applies to the shared wiki **and** is inherited by every personal wiki — personal wikis never ask it again.
6. **Personalize this file.** Write the chosen name into the `project:` frontmatter field, the description into **About this wiki** above, the mode into `mode:` (`solo` or `shared`), and the chosen style into the `link_style:` frontmatter field (`wikilinks` or `markdown`). Stamp `created` and `modified` with today's date. In **solo** mode also write the answers to question 1 into `owner_name:`, `owner_nickname:` and `repo_path:`; in **shared** mode delete those three frontmatter lines — a shared schema belongs to the team, not to whoever ran the wizard (the answers are used for attribution only, below).
7. **Prune the mode-specific spans.** Some of this file is fenced by pairs of HTML-comment markers: an opening comment whose text is just `shared-only` or `solo-only`, closed by one whose text is just `/shared-only` or `/solo-only` (spans may sit inline within a sentence or wrap whole blocks). Search the file for every such marker pair as it appears in the body of the schema — outside this step's own description of them. Since this wiki is **shared** or **solo**: for a span matching the chosen mode, delete only the two marker comments and keep what's between them; for a span of the other mode, delete the markers *and* everything between them. In **solo** mode also delete the `personal-template/` line from the directory-layout tree. Afterwards no marker comments should remain in the schema. Also delete the `TEMPLATE FILE` HTML comment near the top — it describes the template, not this wiki.
8. **Shared mode only — install `personal-template/`.** Create `personal-template/` and fetch two files from the template repo into it, verbatim:
   - `personal-template/AGENTS.md` and `personal-template/README.md`
   Source: if you bootstrapped from a link, the same `owner`/`repo`/`branch` (raw URL `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/personal-template/<file>`); otherwise the canonical template, `hlavamir/LLM_Wiki_Template` on `main`. If the fetch fails or there's no network, ask the user to copy the repo's `personal-template/` folder in by hand rather than inventing its content. Then personalize `personal-template/AGENTS.md`: replace `{{PROJECT_NAME}}`, `{{PROJECT_ONE_LINE}}` and `{{wikilinks|markdown}}` with this wiki's values, and leave the `{{FULL_NAME}}`/`{{NICKNAME}}`/`{{REPO_PATH_OR_NONE}}`/`{{DEFAULT_PUBLIC}}`/date placeholders alone — each person's own first run fills those. Finally tell the user how people join: send each collaborator to `personal-template/README.md` (they need access to this shared folder), and the user who just set this up needs a personal wiki too — a *separate* folder, same procedure.
9. **Log it.** Append to `log.md`: `## [YYYY-MM-DD] init | <project name>` — in shared mode add the mode and who set it up, `## [YYYY-MM-DD] init | <project name> (shared, set up by Lastname Firstname)`.

If the scaffold already exists, skip all of the above and operate normally.

---

## The three layers

1. **`raw/`** — immutable source documents = the source of truth. Read, **never edited**. One file per ingested source. May contain sensitive data; treat it as a sealed archive.
2. **`wiki/`** — the agent-owned, interlinked markdown knowledge base. Created and updated freely.
3. **This `AGENTS.md`** — conventions + workflows. Co-evolve it with the user as the wiki matures. (Claude Code reads it via the `CLAUDE.md` pointer alongside it.)

Plus navigation/maintenance files at the root: `index.md` (catalog, read first on queries), `log.md` (append-only ingest/query/lint timeline), and `wiki-maintenance.md` (a combined backlog + changelog for wiki-*health* work — merges/splits/link fixes/format conformance; read it when doing structural maintenance rather than ingesting knowledge).

## Directory layout

```
<wiki-root>/
├── AGENTS.md             # this schema — read natively by Codex, Gemini CLI, Aider, Zed, Devin, etc.
├── CLAUDE.md             # one-line pointer to AGENTS.md, for Claude Code
├── index.md              # catalog of every page (read first on a query)
├── log.md                # append-only ingest/query/lint timeline
├── wiki-maintenance.md   # wiki-health backlog + changelog (structure/format)
├── raw/                  # immutable sources — read, never edited
├── personal-template/    # shared mode only — bootstrap schema for each person's personal wiki
└── wiki/
    ├── parties/       # real-world people & organizations
    ├── entities/      # project-internal named artifacts
    ├── concepts/      # recurring themes, techniques, decisions
    ├── summaries/     # one page per raw source
    └── assets/        # agent-generated artifacts (SVG/diagrams/charts)
```

`wiki.lock` (not shown above) may appear transiently at the wiki root while an agent is writing — see **Concurrency lock** below. It should not exist between operations; if you find one, it's either an active write or an abandoned one.

## Where a page goes

The load-bearing test for `parties/` vs `entities/` is **"Would this exist if the project didn't?"**

| Folder | Test | Examples |
|---|---|---|
| `parties/` | A real-world **person or organization** that exists independently of the project. | a person, client, vendor, team, account holder |
| `entities/` | A concrete **named artifact that exists only because of the project**. | a file, class, tool, plugin, system, build, config |
| `concepts/` | A recurring **theme, technique, or decision** spanning multiple sources. | a pattern, an approach, a design choice |
| `summaries/` | **One page per raw source** — problem, key facts, resolution, open questions — with a link back to its `raw/` file. | one per ingested chat/doc/code/etc. |
| `assets/` | Artifacts the agent **generates** (not ingested): flowcharts, diagrams, charts. Reference per the wiki's `link_style` (`![[filename]]` for wikilinks, `![alt](../wiki/assets/filename)` for markdown). | `pipeline-flow.svg` |

If a domain clearly needs grouping by some axis (e.g. by time, module, client), you may reorganize `wiki/` accordingly — but the flat spine above is the default; don't partition a wiki that doesn't need it.

## Page conventions

- **Frontmatter** on every wiki page:
  ```yaml
  ---
  title: "..."
  type: party | entity | concept | summary
  created: YYYY-MM-DD
  modified: YYYY-MM-DD
  schema_version: "X.Y.Z"      # version of this AGENTS.md that was active at the page's last edit
  sources: [<raw-slug>, ...]   # raw sources this page draws on (omit if none)
  history:                     # append-only edit log — one entry per edit, oldest first, never reorder/remove
    - "YYYY-MM-DD HH:MM Lastname Firstname"   # e.g. "2026-09-14 12:01 Hlava Miroslav"
  ---
  ```
  `schema_version` is the `schema_version` from this file's frontmatter **at the moment of the page's last edit** — every edit that changes a page's content overwrites it with the current value, so a page always says which schema it was last written under (handy for finding pages that predate a schema change). Pages that predate the field don't get a backfilled value — don't guess; the first real edit simply adds it.
  `history` is an append-only array, one string per edit, oldest first: `"YYYY-MM-DD HH:MM Lastname Firstname"` (24-hour time, the editor's full name in surname-first order). <!-- solo-only -->In a solo wiki the name is always `owner_name` from this file's frontmatter — it never varies, but keeping the field means the wiki can become a shared one later without touching a single page.<!-- /solo-only --><!-- shared-only -->The name comes from whoever's session is writing — see standing rule 12, 'Know who you're chatting with'.<!-- /shared-only --> If it's unclear how to split someone's name, ask rather than guess. Every edit that changes a page's content appends a new entry, bumps `modified`, and refreshes `schema_version`; past entries are never rewritten or deleted, even once the fact they recorded is superseded (rule 2 handles that with a note in the page body, not by editing history). <!-- shared-only -->A page that lands here verbatim from a contributor's personal wiki (Push) carries its `history` and `schema_version` as-is — that's not itself a new edit, so nothing is added for the act of pushing; only an actual content change — including a Push/Pull *reconciliation* — is an edit, attributed to whoever's session is writing the resolution. <!-- /shared-only -->Pages that predate the `history` field don't get retroactive entries — don't fabricate any; the first real edit simply adds the field.
- **Links** between pages follow the wiki's `link_style` (set at first run, in this file's frontmatter):
  - `wikilinks` → `[[wikilinks]]` (basename-based, so links survive moving a page between subfolders). Obsidian-only; GitHub does not render these as links.
  - `markdown` → standard relative markdown links, e.g. `[Acme Corp](../parties/acme-corp.md)`, including the `.md` extension and correct relative path. Renders on GitHub and in Obsidian.
  Don't mix styles within the wiki; if `link_style` is ever changed, note it in `log.md` and treat existing links as a maintenance task (see `wiki-maintenance.md`).
- **Slugs / filenames:** lowercase, hyphenated, no spaces.<!-- shared-only --> **Keep the same path for the same topic across the shared wiki and every personal wiki** (`wiki/entities/foo.md` here pairs with `wiki/entities/foo.md` there) — Push/Pull pair pages by identical relative path, not by title or an explicit link, so a page filed under a different path than its counterpart won't be compared or reconciled at all.<!-- /shared-only -->
- **Open questions:** end a page with an `## Open questions` section **only when** unresolved questions exist; remove items once answered.
- **Citations:** when a claim comes from a specific source, cite its raw slug.<!-- shared-only --> A page synthesized from a contributor's personal wiki cites `synthesized_from:` in frontmatter (owner + page name) rather than linking live back to their personal wiki.<!-- /shared-only -->
- **No manual line-wrapping:** write each prose paragraph as a single line in the source, however long — don't hard-wrap sentences. Let the rendering viewer (GitHub, Obsidian, etc.) soft-wrap for display. Lists, headings, code blocks, and tables are unaffected. Applies to every markdown file in the wiki (`raw/` captures at write-time, `wiki/` pages, `index.md`, `log.md`, this file).

## Standing rules

1. **Date, history & schema metadata.** Every wiki page carries `created`, `modified`, `schema_version`, and a `history` array (see Page conventions) logging every edit. Set `created` once; on every edit bump `modified`, append a `history` entry, and set `schema_version` to the current value from this file's frontmatter. Never lose the original `created` date or edit past `history` entries.
2. **Newer information wins.** When two sources conflict, the more recent one is authoritative. Mark the superseded fact as such (don't silently delete it — note it and its date) and record the change in `log.md`.
3. **Ask, don't assume.** If anything is unclear, ask rather than guess. Park unresolved uncertainty in the page's `## Open questions`.
4. **Rigor over comfort.** Question inputs; flag inconsistencies, risks, and weak reasoning rather than smoothing them over. Fact-rigor is not optional.
5. **Tone.** Friendly but direct. Skip empty praise ("great question", "excellent decision") — just do the work. (Any user who wants a different tone can ask for it; don't prompt for tone.)
6. **One thing = one page.** Each party, entity, or concept gets exactly one page; everything else references it with a link (per `link_style`) rather than duplicating its details. A person's/org's details live only on their `parties/` page.
7. **Never store secrets.** API keys, tokens, passwords, credentials are never written into `raw/` *or* `wiki/`. Reference them by location only (e.g. "key in `api_key.txt`, gitignored").
8. **Offer to capture the conversation.** At the end of any session that produced durable knowledge (a decision, a fix, a new fact, a resolved question), proactively offer — in one line — to save the current chat to `raw/` as a markdown file and ingest it. The user can also trigger this anytime by saying **"ingest"**; treat that as a command to run the Ingest workflow on the current conversation with no further confirmation.
9. **The word "maintain" is a command.** Maintain owns the **technical/structural** side of wiki health — folder structure, frontmatter conformance, link *format* (per `link_style`), broken/dead links, naming conventions, orphan pages — tracked in `wiki-maintenance.md`, a combined backlog + changelog kept separate from `log.md`. It deliberately does **not** cover factual contradictions between pages — that's rule 11, "lint"; keep the two separate. `wiki-maintenance.md` is also where the owner can write plain-language structural instructions for Maintain to carry out (e.g. "convert all `[[wikilinks]]` to markdown links throughout `wiki/`"), not just auto-found issues. When the user says **"maintain"**, run the Maintain operation below: read that file first, then work through **every** item in its **Open tasks** — auto-found issues and owner instructions alike — one at a time, until each is closed (moved to that file's **Log** with today's date and a one-line result) or blocked on a question. Don't stop at the first item. If an item is ambiguous or needs the user's decision/approval, **ask** rather than guess, and leave it open until answered. Add new tasks to the backlog as you discover them, so it stays current.
10. **Lock before writing, not before thinking.** Any operation that writes to the wiki (Ingest, Maintain, Lint, Query's write-back step, First-run bootstrap<!-- shared-only -->, Push/reconciliation<!-- /shared-only -->) must hold `wiki.lock` while it writes, and release it when done — see **Concurrency lock** below. Research, drafting, and reasoning happen unlocked. For a single-item operation (Ingest, Query's write-back), acquire the lock right before the first actual file write and release right after the last one. For a whole-wiki sweep (Maintain, Lint), acquire the lock once at the start of the run and hold it for the entire operation, since it touches many items across one pass and shouldn't leave the wiki half-updated for another agent to see. This is what keeps two agents from writing at the same time, without one agent's minutes-long "thinking" blocking another that's ready to write.
11. **The word "lint" is a command.** Lint owns the **factual/information** side of wiki health — whether the facts stated across `wiki/` pages are internally consistent — deliberately separate from rule 9's "maintain," which owns the technical/structural side. When the user says **"lint"**, run the Lint operation below: scan every page against every other page for genuinely contradicting facts (not just different wording, not staleness alone — an actual factual disagreement about the same thing). Resolve each one found immediately: apply rule 2 (newer wins) if the dates make it unambiguous; if not, **stop and ask the user directly**, one conflict at a time, rather than filing it away in `wiki-maintenance.md` for later — Lint findings don't belong in that file, since it's scoped to Maintain's technical backlog. Mark the superseded fact as such on the losing page (never silently delete it) and bump its `modified`/`history`/`schema_version`. Log a `## [YYYY-MM-DD] lint | <n> pages scanned, <k> conflicts found and resolved` entry either way — a clean run (0 conflicts) is worth logging too.
<!-- shared-only -->12. **Know who you're chatting with.** Every `history` entry needs an attributed name ("Lastname Firstname" — see Page conventions). Confidently inferred from context (a name already established earlier in the session, or `synthesized_from:` provenance on the page itself) is fine; don't interrogate the user on every message. But if you're genuinely unsure who's actually driving a given write — more than one teammate could plausibly be behind a given push/reconciliation, or the session gives no clue at all — **ask directly** rather than guessing or defaulting to a placeholder like "user" or "unknown".<!-- /shared-only -->

## Concurrency lock (`wiki.lock`)

Multiple agents — parallel sessions, or sessions on different machines<!-- shared-only -->, including different teammates' agents<!-- /shared-only --> — may try to write to this wiki at once. `wiki.lock` is a plaintext lock file, sibling to this file, that any write operation must hold before touching `wiki/`, `index.md`, `log.md`, or `wiki-maintenance.md`.

**Lock late, release early — except for whole-wiki sweeps.** Do all reading, research, and drafting *before* acquiring the lock — none of that needs it. For a single-item operation — one Ingest of one source, or one Query write-back — acquire the lock only immediately before the first actual file write, and release it immediately after the last one for that item. Never hold the lock while composing content in your head or waiting on the user. **Maintain and Lint are the exception:** each is a single scan/pass across many items, and should complete as one atomic unit rather than interleaving with another agent's writes partway through — acquire the lock once at the start of the run (after any up-front reading needed to know what to scan) and hold it until the entire run is done, then release.

**Contents:**
```
created: <ISO-8601 timestamp with UTC offset>
host: <machine name>
session: <random ID, generated once per session>
operation: <ingest | query | lint | maintain | init>
```
<!-- shared-only -->In shared mode `operation` also includes `push`.<!-- /shared-only -->

**Acquire:**
1. Generate a `session` ID once per conversation (e.g. a GUID) the first time this session needs to write to the wiki, and reuse it for every lock check in that session.
2. Try to **create** `wiki.lock` with an operation that fails if the file already exists (e.g. PowerShell `New-Item -ItemType File -Path wiki.lock -ErrorAction Stop`) — never a plain overwrite. This closes the gap between "check" and "write" that would otherwise let two agents both create a lock at once.
3. Creation succeeds → the lock is yours; proceed with the operation.
4. Creation fails because the file exists → read it:
   - **Stale** (`created` more than 1 hour ago): presumed a crashed or abandoned session. Overwrite the lock with your own info, note in `log.md` that a stale lock (record its old `host`/`session`/`operation`) was force-cleared, and proceed.
   - **Fresh:** wait 10 seconds and retry from step 2, up to 6 times (~1 minute total).
     - If the lock is gone on a retry, **re-read whatever you're about to touch** (`index.md`, the relevant wiki pages, recent `log.md` entries) *before* creating your own lock — another agent may have just changed it, and your view may be stale.
     - Still locked after 6 retries → stop and tell the user the wiki is held by `<host>`/`<session>` since `<created>`, and ask whether to keep waiting or investigate/clear it manually.

**Release:** delete `wiki.lock` as the final step of the operation — including when the operation is aborted or errors partway through (treat this as a `finally`, not an afterthought).

**Manual override:** deleting `wiki.lock` by hand unlocks the wiki immediately. Use this if an operation crashed without cleaning up and the 1-hour staleness window hasn't elapsed yet.

**Caveat — synced-drive storage:** if this wiki folder lives on a sync-based drive (Google Drive, OneDrive, a Shared Drive, …) rather than a local or true networked filesystem, sync latency between machines means this lock is *advisory*, not a hard guarantee — two machines could each create a lock locally before either upload is visible to the other. It reliably prevents the common case (two sessions on the same or well-synced machine); it is not a cryptographic guarantee across machines with sync lag.<!-- shared-only --> A shared wiki *is* on such storage, which is why the personal-wiki-side lock is the more reliable of the two — a personal wiki lives on a true local filesystem, no sync lag involved.<!-- /shared-only -->

## Operations

### Ingest (add a source)
1. **Detect the genre** of the source (chat transcript, meeting transcript, document, source code, web article, email, …) and capture it faithfully to `raw/<slug>.md`. Include a `*Captured: YYYY-MM-DD*` line (and, for external sources, the origin URL/path + access date). Never edit a `raw/` file afterward.
2. Write `wiki/summaries/<slug>.md` — problem/context, key facts, decisions, resolution, open questions.
3. Create/update the relevant `parties/`, `entities/`, and `concepts/` pages; add cross-links (per `link_style`).
4. Update `index.md`.
5. Append to `log.md`: `## [YYYY-MM-DD] ingest | <title>`.

### Query (answer a question)
1. Read `index.md`, then drill into the relevant pages.
2. Answer with citations to source slugs.
3. File durable answers back into the wiki as new pages, update `index.md`, and log a `query` entry.

### Lint (standing command — factual/information health)
Triggered by the word **"lint"** (standing rule 11). Scope is deliberately narrow, and kept separate from Maintain below: Lint is about whether the **facts** the wiki states are internally consistent — not file structure, links, or formatting.
1. Scan every `wiki/` page against every other page for pages that state genuinely contradicting facts about the same thing (not just different wording, not staleness alone — an actual disagreement).
2. For each contradiction found: apply standing rule 2 (newer wins) if the two pages' dates make it unambiguous. If it's not obviously resolvable that way, **stop and ask the user directly** which side is right, one conflict at a time — don't file it away for later the way a structural issue would be.
3. Once resolved (by rule 2 or by the user), write the resolution to the losing/superseded page: mark the fact as superseded rather than deleting it, and bump `modified`/`history`/`schema_version`.
4. Log a `## [YYYY-MM-DD] lint | <n> pages scanned, <k> conflicts found and resolved` entry — even a completely clean run (0 conflicts) is worth logging.

### Maintain (standing command — technical/structural health)
Triggered by the word **"maintain"** (standing rule 9). Scope is the technical/structural side of wiki health — folder structure, frontmatter conformance, link *format* (per `link_style`), broken/dead links, naming conventions, orphan pages (no inbound links), concepts mentioned but lacking a page, missing cross-references — never factual contradictions (that's Lint's job, above). `wiki-maintenance.md` is both an auto-maintained backlog of technical issues Maintain finds on its own sweeps, *and* a place the owner can write plain-language structural instructions for Maintain to carry out directly. Read `AGENTS.md`, `index.md`, and `wiki-maintenance.md` first, then work through **every** item in its **Open tasks** — auto-found issues and owner instructions alike — one at a time: do the fix following the conventions above, then move the item to that file's **Log** with today's date and a one-line result. If an item is ambiguous or needs the user's decision/approval, **ask** the user and leave it open until answered (moving on to the next actionable item meanwhile). Add new tasks as you find them. Continue until every task is closed or blocked on a question, then report what was closed, what was added, and what's waiting on the user. If the wiki has grown to clearly want grouping by some axis, flag that as a task too.

## Navigation files

- **`index.md`** — content catalog. Grouped by category (parties / entities / concepts / summaries), one line per page: `<link> — one-line summary` (link per `link_style`). Read first on a query; kept current on every ingest.
- **`log.md`** — append-only, chronological, grep-parseable: `## [YYYY-MM-DD] <ingest|query|lint|init|maintain<!-- shared-only -->|push<!-- /shared-only -->> | <title>`.
- **`wiki-maintenance.md`** — combined backlog + changelog for the **technical/structural** side of wiki health (folder structure, link format, broken links, frontmatter conformance), distinct from `log.md`'s knowledge timeline and from Lint's factual-contradiction checks (resolved live in conversation, never filed here — see standing rule 11). Two zones: **Open tasks** (auto-found technical issues, plus any structural instructions the owner writes in directly) and an append-only **Log** (what's been done). Worked via the Maintain operation / the "maintain" command.

<!-- shared-only -->
## Shared-wiki notes

- **This is the shared half of a shared+personal pair.** Each person working on this project keeps their own **personal** wiki — a separate folder on their own machine, bootstrapped from `personal-template/AGENTS.md` (see `personal-template/README.md` for the steps a new person follows). Personal wikis follow the same page conventions but carry a boolean `public: true | false` frontmatter field. Only `public: true` pages are ever candidates to reach this shared wiki.
- **How pages get here:** not a file copy. Push/reconciliation (documented in each personal wiki's own `AGENTS.md`) reads a contributor's `public: true` pages, compares them against this wiki's corresponding pages by relative path, and reasons about whether a difference is a real factual conflict before writing here — auto-resolving the obvious cases (rule 2, newer wins) and asking the human when it isn't. Treat a page here that looks synthesized from several contributors accordingly; check `synthesized_from:` frontmatter for provenance before assuming single authorship.
- **This wiki's own `index.md` and `log.md` are kept current by Push, not just by this file's own Ingest operation.** A pushing contributor's session adds a catalog line to this `index.md` and a `push` entry to this `log.md` for every page it creates here, under the same `wiki.lock` as the page write itself. A `log.md` entry here that looks like it came from a contributor's session rather than a direct edit to this wiki is therefore expected.
- **Onboarding a new person:** point them at `personal-template/README.md` in this wiki (not this file). `personal-template/AGENTS.md` locates this shared wiki from its own file path — no setup question about location — and pulls everything into a fresh personal wiki on their machine.
- **Schema updates propagate to personal wikis automatically.** Each personal wiki's Pull diffs its own `AGENTS.md` against this wiki's `personal-template/AGENTS.md` and appends any Operations/standing-rule section it's missing. To roll a new personal-side command out to everyone, add it to `personal-template/AGENTS.md` here — nobody has to hand-edit their wiki. This file itself has no such mechanism: diff it against the upstream template repo's `AGENTS.md` now and then, and pull in improvements deliberately rather than letting it drift silently.
- **Keep this file and `personal-template/AGENTS.md` structurally parallel.** They share standing rules, page conventions and operations; if one evolves, update the other.
<!-- /shared-only -->

## Notes

- **Schema versioning.** This file's `schema_version` follows semantic versioning: PATCH for wording/clarifications, MINOR for additive changes (new options, commands, fields), MAJOR for changes that make existing pages or workflows non-conforming. Bump it whenever you change this file's rules or conventions — and nothing else changes automatically: pages keep the older value in their own `schema_version` until they're next edited, which is the point (it shows which pages were written under which schema). Versions so far: `1.0.0` was the original template (no `history`, no `schema_version`, no shared mode); `1.1.0` added shared mode, `history` in every mode, and `schema_version`. A wiki still on `1.0.0` has pages with neither field — expected, not a defect.
- The wiki is plain markdown — git-friendly, and Obsidian-friendly when `link_style: wikilinks`. Version it if useful.
- Keep prose tight. This is reference material, not narrative.
- Everything beyond the above (an `overview.md`/`synthesis.md`, Obsidian graph colour-tags, a `sensitive:` flag, scheduled auto-ingest, image handling, a search tool) is **optional** — add it only when the user asks.
- **`AGENTS.md` is the single source of truth.** `CLAUDE.md` is a one-line pointer to it, needed because Claude Code loads `CLAUDE.md` rather than reading `AGENTS.md` natively. Most other coding agents (Codex CLI, Gemini CLI, Aider, Zed, Devin, and others) read `AGENTS.md` directly — no pointer needed. If you use a tool that still expects its own filename instead (e.g. Cursor's `.cursor/rules/`, Windsurf's `.windsurfrules`, GitHub Copilot's `.github/copilot-instructions.md`), add a similarly minimal pointer file at that location rather than duplicating this schema's content. (If a project only ever uses Claude Code, merging `AGENTS.md` into `CLAUDE.md` and deleting the pointer is a legitimate simplification — but re-split it if another agent ever joins.)
