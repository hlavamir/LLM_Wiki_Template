# Maintain — structural health

Triggered by **"maintain"**. Scope: folder structure, frontmatter, naming, link format and broken links, orphans, missing cross-references, index and log shape, page size — never factual contradictions (that's Lint). `wiki-maintenance.md` holds both the issues Maintain finds and plain-language structural instructions the owner writes there (e.g. "convert all `[[wikilinks]]` to markdown links").

1. **Lock** (op `maintain`) and hold it for the whole run.
2. **Scan:** `<python> tools/wiki.py check` (`--full` when a category is truncated). Add each finding not already listed to **Open tasks** — group many alike into one task ("trim 187 index lines"), don't copy 187 lines. No Python → check the same things by hand, but sample rather than read every page.
3. **Work every open task**, owner instructions included, one at a time. For each: fix it with targeted edits, then move it to `## Log` as `- YYYY-MM-DD <one-line result>`. Ambiguous, or needs a decision or approval → ask, leave it open, move on to the next. Add new tasks as you find them. Recipes:
   - **Superseded material above `## History`** (`superseded`): move superseded facts into `## History`, one line each with dates and source; keep the current state accurate. Judgment call — when unsure whether something is superseded, leave it.
   - **Oversized page** (`size`): split coherent sub-topics into their own pages (one thing = one page) and link them; condense an oversized `## History` to one line per fact — the full text is in raw/.
   - **History compaction** (`history`): fold the oldest entries into one `"YYYY-MM-DD..YYYY-MM-DD N edits (Name A, Name B)"`, keeping the newest 10.
   - **Index** (`index`): trim each line to one clause of at most 120 chars; remove summary and raw lines; add missing pages; past 300 lines split into `index/<category>.md` linked from `index.md`.
   - **Log** (`log`): a legacy `log.md` → run `migrate-log` (one line per entry, monthly files, old file kept as `log/legacy-log.md`); multi-line entries in `log/` → move any detail missing from the linked page into that page, then cut the entry to one line.
   - **Orphans / missing pages:** link the page from where it belongs, or ask whether it should go; a concept mentioned on several pages without its own page → create it.
   - **Secrets** (`secrets`): show the user where (never the value) and ask; in `wiki/` replace the value with its location. raw/ is immutable, so a secret there means asking the user to remove or redact the raw file themselves.
   - **Personal wikis only:** a page without `public:` simply gets `default_public` (no task, no question); a public page whose path the shared wiki would file differently → rename it to match, since Push/Pull pair pages by path.
   - **Raw without summary** (`raw-only`): ask whether to ingest it or leave it raw-only on purpose; record the answer so it isn't asked again.
4. **Wiki wants grouping** by some axis (time, module, client)? File it as a task for the owner.
5. **Finish:** `log maintain "<k> closed, <a> added, <w> waiting"`, release the lock, and report what was closed, what was added, and what waits on the user.

## Upgrading from 1.1.0

After `AGENTS.md`, `schema/` and `tools/` are replaced with the 1.2.0 template (keeping this wiki's frontmatter values and its own additions to `AGENTS.md`), the first Maintain does the migration: `migrate-log`, then the index, superseded and size tasks above. Spread big wikis over several runs — closing the cheap tasks first (log, index) gets most of the savings.
