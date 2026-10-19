---
schema_version: "1.1.0"             # version of THIS schema file — stamped into each page's own `schema_version` on every edit; Pull's schema propagation raises it to the shared wiki's template version
project: "{{PROJECT_NAME}}"        # filled in when the shared wiki installed this template — fixed, it's the shared wiki's project
mode: "personal"
owner_name: "{{FULL_NAME}}"         # asked at first run — written 'Lastname Firstname'
owner_nickname: "{{NICKNAME}}"      # short display name — used in casual reference and log attributions
repo_path: "{{REPO_PATH_OR_NONE}}"  # local path to a related code repo on this machine, or "none"
default_public: {{DEFAULT_PUBLIC}}   # true | false — what a new page's `public:` field defaults to; asked at first run
created: {{YYYY-MM-DD}}             # stamped in YOUR copy at first run — not in this template file
modified: {{YYYY-MM-DD}}
type: schema
link_style: "{{wikilinks|markdown}}" # filled in when the shared wiki installed this template — inherited from the shared wiki, never asked
---

<!--
TEMPLATE FILE — read in place, not copied by hand. This file lives at
"<shared-wiki-root>/personal-template/AGENTS.md". To bootstrap a personal wiki on your own machine:

  1. Create a new, empty local folder wherever you want your personal wiki to live.
  2. Start an agent session (Claude Code, Codex CLI, …) with that new folder as the working directory.
  3. Tell it something like: "Read <path-to-this-file> and set up my personal wiki here."
     (Use the actual path to THIS file as seen on your machine — e.g. a Shared Drive mounted as
     H:\Shared drives\<project>\personal-template\AGENTS.md.)
  4. The agent follows "First run — bootstrap & setup" below, which:
     - works out where the shared wiki lives from the path you gave it (no registry, no question
       about location — the path already answers that),
     - asks a few quick questions about you,
     - scaffolds a full personal-wiki vault in your new folder, with its own independent copy of this schema,
     - writes a `wiki-shared-link.md` there pointing at the shared wiki,
     - and pulls everything currently in the shared wiki into your new vault.

From then on your copy behaves exactly like the "scaffold already exists" path below — Ingest, Query,
Lint, Maintain, Push, Pull, Sync and Fetch news, all documented here.

Needs nothing beyond a coding agent that can read, write and edit files — no plugins, no sign-in.
-->

# LLM Wiki — Personal

**Your folder IS the wiki.** There is no separate "local wiki folder" this syncs from — whatever's in this folder, right now, is the current, canonical state of your personal wiki for this one project. (If you keep this folder inside a synced location for backup, that's your own OS-level choice; nothing here syncs personal content through any service — Push/Pull below work by direct file access instead.)

This is the **personal** half of a personal+shared pair: **one wiki, one project, one shared counterpart.** Any agent working here **reads this file first** and acts as a disciplined wiki maintainer — not a generic chatbot. It follows Andrej Karpathy's *LLM Wiki* pattern (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), adapted for one person's own wiki with a path to a shared, team-wide counterpart.

**About this wiki:** {{NICKNAME}}'s working wiki for the {{PROJECT_NAME}} project — {{PROJECT_ONE_LINE}} Adjust freely once it's yours.
**Shared counterpart:** see `wiki-shared-link.md` in this folder's root, written at first run.

---

## First run — bootstrap & setup

If you're reading this file **from inside a shared wiki's `personal-template/` folder** (i.e. you haven't bootstrapped yet), this is a first run. Do the following, in order, in the NEW folder the user gave you as the working directory — never write into `personal-template/` itself, that's the shared wiki's template, not this person's wiki:

1. **Resolve the shared wiki's location.** You were handed a path to this file. The shared wiki's root is two path levels up from it — strip `personal-template/AGENTS.md` off the end. No lookup needed — this file's own location already says where it lives. Check that the folder is reachable and holds an `AGENTS.md` with `mode: shared`; if it isn't (a drive that isn't mounted, a wrong path), stop and tell the user rather than guessing. Read that file's frontmatter for `project` and `link_style` and its **About this wiki** line; they must match this file's — if not, trust the shared wiki.
2. **Setup question — who am I talking with?** Ask four things: (a) your **full name** — every `history` entry (see Page conventions) writes it as `"Lastname Firstname"`, so get the split right (ask if it's ambiguous rather than guessing); (b) a **nickname / display name** for the "About this wiki" line and casual reference; (c) the **local path of a related code repository** on this machine, or `none`; (d) whether new pages should default to **a)** `public: true` (shared with the team on the next Push) or **b)** `public: false` (stays in your wiki until you flip it). You may propose a draft for (a)/(b) from context (e.g. `git config user.name`), but present it as a proposal to confirm. The project and the link style are already fixed by the shared wiki — don't ask about them.
3. **Scaffold** in the NEW working directory (not here):
   - `AGENTS.md` — write the full content of THIS file into it, with the frontmatter's `created`/`modified` stamped to today, `{{FULL_NAME}}`/`{{NICKNAME}}`/`{{REPO_PATH_OR_NONE}}`/`{{DEFAULT_PUBLIC}}` replaced with the answers to step 2, the remaining `{{…}}` in the body filled from the shared wiki (project, link style, About line), the leading `TEMPLATE FILE` comment removed, and this "First run" section's content replaced with the standard "if the scaffold already exists, operate normally" short-circuit (see the bottom of this section). From that point on, this new `AGENTS.md` is a normal, independent personal-wiki schema, not a template.
   - `CLAUDE.md` — a one-line pointer for Claude Code: `# LLM Wiki` plus `Full schema and instructions: see [AGENTS.md](AGENTS.md) — read it first, before doing anything in this folder.` (Other agents read `AGENTS.md` directly.)
   - `wiki-shared-link.md` — frontmatter with `type: shared-link` and `shared_wiki_path:` set to the path resolved in step 1, plus one line noting the path is specific to this machine (update it if the drive letter or mount point ever changes).
   - `index.md`, `log.md`, `wiki-maintenance.md` (seeded as in the shared wiki: headings, and `## Open tasks` / `## Log`)
   - `raw/`
   - `wiki/parties/`, `wiki/entities/`, `wiki/concepts/`, `wiki/summaries/`, `wiki/assets/`
4. **Pull everything.** Run the **Pull** procedure documented below (shared → this new wiki) in full, right now, against the shared wiki resolved in step 1 — every page there gets copied in and tagged `public: true`. This is the "join the project already in progress" step; skip nothing.
5. **Log it.** Append to the new wiki's `log.md`: `## [YYYY-MM-DD] init | <project name> (bootstrapped from personal-template, pulled <n> pages)`.

If the scaffold already exists in your working directory (you're past first run), skip all of the above and operate normally — treat this file as the schema of your own personal wiki, including the operations below.

---

## The three layers

1. **`raw/`** — immutable source documents = the source of truth. Read, **never edited**. One file per ingested source. May contain sensitive data; treat it as a sealed archive.
2. **`wiki/`** — the agent-owned, interlinked markdown knowledge base. Created and updated freely.
3. **This `AGENTS.md`** — conventions + workflows. Co-evolve it with the user as the wiki matures.

Plus navigation/maintenance files at the root: `index.md` (catalog, read first on queries), `log.md` (append-only ingest/query/lint/push/pull timeline), and `wiki-maintenance.md` (a combined backlog + changelog for wiki-*health* work).

## Directory layout

```
<wiki-root>/                  # this IS the personal wiki — no wrapper folder
├── AGENTS.md             # this schema
├── CLAUDE.md             # one-line pointer to AGENTS.md, for Claude Code
├── wiki-shared-link.md   # local path to the shared wiki — written at first run
├── index.md              # catalog of every page (read first on a query)
├── log.md                # append-only ingest/query/lint/push/pull timeline
├── wiki-maintenance.md   # wiki-health backlog + changelog (structure/format)
├── raw/                  # immutable sources — read, never edited
└── wiki/
    ├── parties/       # real-world people & organizations
    ├── entities/      # project-internal named artifacts
    ├── concepts/      # recurring themes, techniques, decisions
    ├── summaries/     # one page per raw source
    └── assets/        # agent-generated artifacts (SVG/diagrams/charts)
```

**No `private/`/`public/` subfolders** — visibility is a **boolean frontmatter field** (`public:`, see Page conventions), so the category spine here stays identical to the shared wiki's. This is the one deliberate structural difference from the shared wiki: single tree, no visibility-based folder split.

`wiki.lock` (not shown above) may appear transiently at the wiki root while an agent is writing — see **Concurrency lock** below.

## Where a page goes

Same test as the shared wiki: **"Would this exist if the project didn't?"**

| Folder | Test | Examples |
|---|---|---|
| `parties/` | A real-world **person or organization** that exists independently of the project. | a person, client, vendor, team, account holder |
| `entities/` | A concrete **named artifact that exists only because of the project**. | a file, class, tool, plugin, system, build, config |
| `concepts/` | A recurring **theme, technique, or decision** spanning multiple sources. | a pattern, an approach, a design choice |
| `summaries/` | **One page per raw source** — problem, key facts, resolution, open questions — with a link back to its `raw/` file. | one per ingested chat/doc/code/etc. |
| `assets/` | Artifacts the agent **generates** (not ingested): flowcharts, diagrams, charts. Reference per `link_style` (`![[filename]]` for wikilinks, `![alt](../wiki/assets/filename)` for markdown). | `pipeline-flow.svg` |

## Page conventions

- **Frontmatter** on every wiki page:
  ```yaml
  ---
  title: "..."
  type: party | entity | concept | summary
  public: true | false
  created: YYYY-MM-DD
  modified: YYYY-MM-DD
  schema_version: "X.Y.Z"      # version of this AGENTS.md that was active at the page's last edit
  sources: [<raw-slug>, ...]   # raw sources this page draws on (omit if none)
  history:                     # append-only edit log — one entry per edit, oldest first, never reorder/remove
    - "YYYY-MM-DD HH:MM Lastname Firstname"   # e.g. "2026-09-14 12:01 Hlava Miroslav"
  ---
  ```
  `public` is a boolean, named `public` rather than `visibility`. A new page gets this wiki's `default_public` (see frontmatter above) unless the user says otherwise. Only `public: true` pages are ever candidates to leave this wiki (Push); a `public: false` page never does.
  `schema_version` is the `schema_version` from this file's frontmatter **at the moment of the page's last edit** — every edit that changes a page's content overwrites it with the current value, so a page always says which schema it was last written under. Pages that predate the field don't get a backfilled value — don't guess; the first real edit simply adds it. A verbatim Push/Pull copy carries the source's value as-is.
  `history` is an append-only array, one string per edit, oldest-first: `"YYYY-MM-DD HH:MM Lastname Firstname"` (24-hour time, the editor's full name in surname-first order — built from `owner_name`, or standing rule 12's "Know who you're chatting with"). If it's ever unclear how to split someone's name into "Lastname Firstname", ask rather than guess. Every edit that changes a page's content appends a new entry, bumps `modified`, and refreshes `schema_version`; past entries are never rewritten or deleted, even once the fact they recorded is superseded (rule 2 handles that with a note in the page body, not by editing history). A verbatim Push/Pull copy (content unchanged, just relocated) carries the source's `history` as-is — not itself a new edit, so no entry is added; only an actual content change — including a Push/Pull *reconciliation* — is an edit, attributed to whoever's session is writing that resolution. Pages that predate the `history` field don't get retroactive entries — don't fabricate any; the first real edit simply adds the field.
- **Links** between pages follow `link_style` (set from the shared wiki, in this file's frontmatter): `wikilinks` → `[[wikilinks]]`; `markdown` → relative markdown links with the `.md` extension, e.g. `[Acme Corp](../parties/acme-corp.md)`. Don't mix styles.
- **Slugs / filenames:** lowercase, hyphenated, no spaces. **Match the shared wiki's path for the same topic where one exists** (`wiki/entities/foo.md` here pairs with `wiki/entities/foo.md` there) — Push/Pull pair pages by identical relative path, not by title or an explicit link, so a public page filed under a different path than its shared counterpart won't be compared or reconciled at all.
- **Open questions:** end a page with an `## Open questions` section **only when** unresolved questions exist; remove items once answered.
- **Citations:** when a claim comes from a specific source, cite its raw slug.
- **No manual line-wrapping:** write each prose paragraph as a single line in the source, however long — let the viewer soft-wrap for display.

## Standing rules

1. **Date, history & schema metadata.** Every wiki page carries `created`, `modified`, `schema_version`, and a `history` array (see Page conventions) logging every edit. Set `created` once; on every edit bump `modified`, append a `history` entry, and set `schema_version` to the current value from this file's frontmatter. Never lose the original `created` date or edit past `history` entries.
2. **Newer information wins.** When two sources conflict — including this wiki vs. the shared wiki — the more recent one is authoritative. Mark the superseded fact as such (don't silently delete it — note it and its date) and record the change in `log.md`.
3. **Ask, don't assume.** If anything is unclear, ask rather than guess. Park unresolved uncertainty in the page's `## Open questions`.
4. **Rigor over comfort.** Question inputs; flag inconsistencies, risks, and weak reasoning rather than smoothing them over.
5. **Tone.** Friendly but direct. Skip empty praise — just do the work.
6. **One thing = one page.** Each party, entity, or concept gets exactly one page; everything else references it with a link (per `link_style`).
7. **Never store secrets.** API keys, tokens, passwords, credentials are never written into `raw/` *or* `wiki/`. Reference them by location only. This matters doubly here: anything `public: true` ends up in a shared wiki other people can read.
8. **Offer to capture the conversation.** At the end of any session that produced durable knowledge, proactively offer to save the chat to `raw/` and ingest it. "ingest" is a standing command to do this immediately.
9. **The word "maintain" is a command.** Maintain owns the **technical/structural** side of wiki health — folder structure, frontmatter conformance, link *format* (per `link_style`), broken/dead links, naming conventions — never factual contradictions between pages (that's rule 11, "lint"; keep the two separate). `wiki-maintenance.md` is both an auto-found backlog *and* a place you can write plain-language structural instructions for Maintain to carry out. "maintain" works through every open task there — auto-found issues and your own instructions alike — until closed or blocked on a question.
10. **Lock before writing, not before thinking.** Any write (Ingest, Maintain, Lint, First-run bootstrap, Push, Pull) holds `wiki.lock` while writing, releases when done — see **Concurrency lock**. This matters even on a single machine: two independent sessions pointed at the same wiki are two writers, not one.
11. **The word "lint" is a command.** Lint owns the **factual/information** side of wiki health — whether the facts stated across `wiki/` are internally consistent — deliberately separate from rule 9's "maintain." When you say **"lint"**, scan every page against every other page for genuinely contradicting facts (not just different wording, not staleness alone). Resolve each one found immediately, the same way a Push/Pull reconciliation works: apply rule 2 (newer wins) if unambiguous; if not, **stop and ask you directly**, one conflict at a time, rather than filing it into `wiki-maintenance.md`. Mark the superseded fact as such on the losing page and bump its `modified`/`history`/`schema_version`. Log a `## [YYYY-MM-DD] lint | <n> pages scanned, <k> conflicts found and resolved` entry either way.
12. **Know who you're chatting with.** Every `history` entry needs an attributed name ("Lastname Firstname" — see Page conventions). Confidently inferred from context (this wiki's own owner — see the frontmatter's `owner_name` — or a name already established earlier in the session) is fine; don't interrogate the user on every message. But if you're genuinely unsure who's actually driving the session (an unfamiliar machine, someone other than the wiki's usual owner at the keyboard), **ask directly** rather than guessing or defaulting to a placeholder like "user" or "unknown".

## Concurrency lock (`wiki.lock`)

`wiki.lock` is a plaintext lock file at the root of whichever wiki you're writing to (this one, or the shared one during Push), held for the duration of any write.

**Contents:**
```
created: <ISO-8601 timestamp with UTC offset>
host: <machine name>
session: <random ID, generated once per session>
operation: <ingest | query | lint | maintain | init | push | pull>
```

**Acquire:** generate a `session` ID once per conversation; try to **create** `wiki.lock` with an operation that fails if the file already exists (e.g. PowerShell `New-Item -ItemType File -Path wiki.lock -ErrorAction Stop`) — never a plain overwrite. Created → it's yours. Already exists → read it: if `created` is more than 1 hour ago it's stale — overwrite it with your own info and note the force-clear (old `host`/`session`/`operation`) in `log.md`; if it's fresh, wait 10 seconds and retry, up to 6 times, re-reading whatever you're about to touch if the lock disappears on a retry; still locked after 6 tries → stop and tell the user who holds it and since when, and ask whether to keep waiting or clear it.

**Release:** delete `wiki.lock` as the final step — including when the operation is aborted or errors partway through.

**Lock late, release early.** Do reading, research, and drafting *before* acquiring it. Single-item operations (one Ingest, one Query write-back) take it right before the first file write and drop it right after the last. Maintain, Lint, Push and Pull are whole-wiki sweeps — take the lock once at the start of the run and hold it until the run is done.

**This lock is a hard guarantee here, not merely advisory** — for *this* wiki. A personal wiki lives on a true local filesystem (even if the folder also happens to be backed up by a sync client — the lock only has to work for writers on THIS machine, and local atomic file creation does that). The **shared** wiki's lock, which Push takes, lives on sync-based storage and is only *advisory*: sync lag between machines can let two writers each create a lock before either becomes visible. It reliably catches the common case; it isn't a guarantee.

## Operations

### Ingest (add a source)
1. **Detect the genre** of the source (chat transcript, meeting transcript, document, source code, web article, email, …) and capture it faithfully to `raw/<slug>.md`, with a `*Captured: YYYY-MM-DD*` line (and the origin URL/path + access date for external sources). Never edit a `raw/` file afterward.
2. Write `wiki/summaries/<slug>.md` — problem/context, key facts, decisions, resolution, open questions.
3. Create/update the relevant `parties/`, `entities/`, and `concepts/` pages; add cross-links (per `link_style`).
4. Update `index.md`; append `## [YYYY-MM-DD] ingest | <title>` to `log.md`.

### Query (answer a question)
Read `index.md`, drill into the relevant pages, answer with citations to source slugs, and file durable answers back into the wiki as new pages (update `index.md`, log a `query` entry).

### Lint (standing command — factual/information health)
Triggered by the word **"lint"** (standing rule 11): scan every page against every other for genuinely contradicting facts; resolve each live — rule 2 if the dates make it unambiguous, otherwise ask — mark the losing fact superseded (never delete it), bump `modified`/`history`/`schema_version`, and log a `lint` entry, clean runs included.

### Maintain (standing command — technical/structural health)
Triggered by the word **"maintain"** (standing rule 9). Scope: folder structure, frontmatter conformance, link *format*, broken links, naming, orphan pages, concepts mentioned but lacking a page — never factual contradictions. Additionally checks that every page has a `public:` value (a missing one is simply set to `default_public`, no judgment call, no flagging) and that public pages' paths plausibly have, or should have, a shared-wiki counterpart to compare against. Read `AGENTS.md`, `index.md` and `wiki-maintenance.md` first, then work through **every** item in **Open tasks** — auto-found and your own instructions alike — moving each to the **Log** with today's date and a one-line result, or asking when it's ambiguous or needs a decision.

### Push / Pull (sync with the shared wiki)
Not a file copy — staged cheap-to-expensive comparison, then reasoning about anything that actually differs. Only `public: true` pages are ever candidates to push; pages with `public: false` never leave this wiki under any circumstance.

The shared wiki is used directly as files — its local path lives in `wiki-shared-link.md`. If that path isn't reachable (drive not mounted, offline, path changed), stop and tell the user — don't guess a different location.

Both Push and Pull are writes and count as whole-wiki sweeps: hold `wiki.lock` on whichever side you're writing to, for the whole run. Push writes to the **shared** wiki (lock there); Pull writes to **this wiki** (lock here).

#### Push (this wiki → shared)
1. Read `wiki-shared-link.md` for `<shared>`, the shared wiki's local path.
2. List every `.md` under this wiki's `wiki/` with `public: true` in its frontmatter. Its path relative to `wiki/` (e.g. `entities/foo.md`) is the pairing key — identical on both sides.
3. For each one, compare against `<shared>/wiki/<relpath>`:
   - **Cheap check first:** if `<shared>/wiki/<relpath>` doesn't exist, it's new — go straight to create. If it exists, compare mtimes/`modified` fields before reading full content — skip pages unchanged on both sides since you last checked.
   - **Missing on shared:** acquire `wiki.lock` there (if not already held for this run), create the file (and any missing `wiki/<category>/` folders) with this wiki's content, verbatim.
   - **Present on both, identical content:** nothing to do.
   - **Present on both, different content:** reconciliation case. Read both versions, apply standing rule 2 (newer `modified` wins) and rule 3 (ask if unclear), write the resolution to the **shared** copy, mark superseded facts rather than dropping them. Ask the user if it's genuinely not obvious which side should win.
4. Before releasing the lock, **update the shared wiki's own `index.md` and `log.md`** (still under the same lock — this is part of the push, not a separate operation): add a one-line catalog entry (same link format and style as this wiki's own `index.md`) under the right category for every page just created there, and append `## [YYYY-MM-DD] push | <n> pushed, <m> created, <k> reconciled` to the shared wiki's `log.md` — a project-wide record of who pushed what, distinct from this wiki's private timeline (standing rule 12 says whose name goes on it).
5. Release `wiki.lock` on the shared wiki.
6. Log a matching `## [YYYY-MM-DD] push | <n> pushed, <m> created, <k> reconciled` entry in **this wiki's own** `log.md` too — one push produces two log entries, one per side.

#### Pull (shared → this wiki)
1. Read `wiki-shared-link.md` for `<shared>`.
2. List every `.md` under `<shared>/wiki/` — everything there is implicitly public.
3. For each one, relative path `<relpath>` under `wiki/`:
   - **Missing locally:** acquire `wiki.lock` on **this wiki** (if not already held for this run), copy it in at `wiki/<relpath>` (creating folders as needed), and make sure `public: true` is set in its frontmatter — **check first, don't blindly insert**: a page that reached the shared wiki via a Push carries its `public` field verbatim, so it's usually already there, and adding a second `public:` line produces invalid duplicate-key frontmatter. Only add the field if it's genuinely absent. Also add a one-line catalog entry for it to **this wiki's** `index.md`, under the right category.
   - **Present locally but NOT `public: true`:** don't touch it — flag a genuine content difference in `wiki-maintenance.md`'s **Open tasks** instead of silently overwriting or skipping.
   - **Present locally and public, identical content:** nothing to do.
   - **Present locally and public, different content:** same reconciliation as Push, in reverse.
4. **Schema propagation:** after the page sync, read `<shared>/personal-template/AGENTS.md` at its current, live content (not from memory) and compare it against this wiki's own `AGENTS.md`. For any Operations subsection or standing rule present in the template but genuinely missing from yours, append it verbatim (renumbering standing rules to fit your file, nothing else) — never touch anything you've already customized (your owner fields, project-specific notes, other frontmatter), and never delete or rewrite existing sections just because the template's wording drifted. Then set your own `schema_version` to the template's — the one exception to leaving frontmatter alone, since your schema now matches it; pages you edit from here on get stamped with the new value, existing pages keep theirs until next edited. This is how a schema addition reaches every already-onboarded person without a manual edit. Note what was added, if anything, in the pull's log entry.
5. Release `wiki.lock` here.
6. Log a `## [YYYY-MM-DD] pull | <n> pulled, <m> created, <k> reconciled` entry in `log.md` (mention any schema propagation from step 4 in the same entry). (At first-run bootstrap this is the entry from step 5 of "First run" — one entry covers both.)

#### Sync — Pull, then Ingest anything new, then Push (standing shortcut)
Triggered by the word **"sync"**. Runs the three operations below, in this order, as one unit:
1. **Pull** (shared → this wiki) — full procedure above, including its own schema-propagation step.
2. **Ingest** — if this session has produced durable knowledge not yet captured (a conversation, a fix, a decision), ingest it now, exactly as the standing "ingest" command would. If there's genuinely nothing new to ingest, skip this step without comment rather than manufacturing something to write.
3. **Push** (this wiki → shared) — full procedure above.

**Conflict handling — the reason this isn't just three commands chained blindly:** if Pull or Push hits a genuine reconciliation case (standing rules 2/3 — two sides disagree and it isn't simply "newer wins") while running as part of a sync, **stop the sync at that point** rather than guessing or plowing through it. Surface each conflicting page one at a time, explain what's actually in tension between the two versions, and ask the user for their view on which side is right (or how to merge them). Once that conflict is resolved, ask whether to continue the sync from where it stopped — don't restart from the top, and don't silently resume without checking first. Only report a sync as fully complete once every step has actually run clean, including any that needed a conflict resolved along the way.

#### Fetch news (read-only — no lock needed)
1. Read `wiki-shared-link.md` for `<shared>`.
2. List every `.md` under `<shared>/wiki/`, with each page's `modified:` frontmatter date (fall back to file mtime if missing/malformed).
3. Sort newest-first. If the user gave a "since" date, only list pages modified after it; otherwise list everything.
4. Summarize what's new/changed — don't just dump the list; skim anything newly relevant and call out what's actually notable. No files are written.

#### Casually offer, don't schedule
Don't set up an automated/scheduled check for this unless the user specifically asks for one — a scheduled task can't tell whether now is a good moment. Instead, at a natural point in a session (the start, or after wrapping up a chunk of work), casually ask something like *"Want me to check if there's anything new in the shared wiki?"* Keep it low-key and skippable.

## Navigation files

- **`index.md`** — content catalog, grouped by category, one line per page: `<link> — one-line summary` (link per `link_style`).
- **`log.md`** — append-only, chronological: `## [YYYY-MM-DD] <ingest|query|lint|init|maintain|push|pull> | <title>`. ("sync" isn't its own log verb — running it just produces the normal pull/ingest/push entries in sequence.)
- **`wiki-maintenance.md`** — the **technical/structural** wiki-health backlog + changelog (folder structure, link format, broken links, frontmatter), distinct from Lint's factual-contradiction checks (resolved live, never filed here — see rule 11). Populated by Maintain's own scans and by you writing structural instructions in directly; worked via the "maintain" command.

## Notes

- **One wiki ↔ one project, fixed 1:1.** This wiki belongs to its shared wiki's project for its whole life. Working on a second project means a second, separate personal wiki — not a project switcher inside one.
- **Schema versioning.** `schema_version` follows semantic versioning (PATCH wording, MINOR additive, MAJOR breaking) and is kept in step with the shared wiki's `personal-template/AGENTS.md` by Pull's schema propagation. A page without `schema_version` was last edited before `1.1.0` — expected, not a defect.
- **`AGENTS.md` is the single source of truth** here too; Claude Code reads it through the one-line `CLAUDE.md` pointer, other agents read it directly.
- **This file and the shared wiki's own `AGENTS.md` should stay structurally parallel.** If the shared wiki's schema evolves, this template should get the same updates, and vice versa.
