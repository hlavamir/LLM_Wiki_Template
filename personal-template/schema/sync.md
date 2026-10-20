# Push, Pull, Sync, Fetch news

Read when the user says **"push"**, **"pull"**, **"sync"** or **"fetch news"**. The shared wiki is used directly as files at the path in `wiki-shared-link.md` (`<shared>`); unreachable (drive not mounted, offline, moved) → stop and tell the user, never guess another location. Only `public: true` pages are ever pushed; `public: false` pages never leave this wiki.

Push and Pull are whole-wiki sweeps: hold `wiki.lock` on the side being written — Push on the shared wiki (`--root <shared>`), Pull here — for the whole run.

## The work list — `pair`

`<python> tools/wiki.py pair --shared <shared>` classifies every page path under `wiki/` on both sides:
- `push-new` — public here, missing there; `pull-new` — there, missing here;
- `differ` — on both, content differs (ignoring the `public:` line), with both `modified` dates;
- `private-collision` — `public: false` here but the shared wiki has that path;
- counts of identical and private pages, which need nothing.

Only `differ` pages are ever read in full. Without Python: compare `modified` dates and file sizes first, and read only pages where those differ.

## Push (this wiki → shared)
1. `pair`; lock the shared wiki (op `push`).
2. `push-new` → copy each file to `<shared>/wiki/<relpath>` (create folders as needed), verbatim.
3. `differ` → read both versions and reconcile: rule 2 (newer `modified` wins) and rule 3 (ask when it isn't obvious); write the resolution to the **shared** copy, superseded facts into `## History`, never dropped. That is an edit, attributed to whoever drives this session (rule 12).
4. Still under the shared lock: add one catalog line per created page to `<shared>/index.md` (same style), and `<python> tools/wiki.py --root <shared> log push "<n> pushed, <m> created, <k> reconciled (<nickname>)"`.
5. Release the shared lock; log the same entry here: `log push "<n> pushed, <m> created, <k> reconciled"`.

## Pull (shared → this wiki)
1. `pair`; lock this wiki (op `pull`).
2. `pull-new` → copy each into `wiki/<relpath>`; make sure it has `public: true` — check first, a pushed page usually already carries it, and a second `public:` line breaks the frontmatter. Add a catalog line to this `index.md`.
3. `differ` → reconcile as in Push, in reverse, writing here.
4. `private-collision` → touch nothing; file a task in `wiki-maintenance.md` (which page, and that a private page shares a public path).
5. **Schema propagation.** Compare `<shared>/personal-template/AGENTS.md`'s `schema_version` with this file's. Equal → skip — nothing to read. Different →
   - copy `<shared>/schema/lock.md`, `lint.md`, `maintain.md`, `<shared>/personal-template/schema/sync.md` and every `.py` file in `<shared>/tools/` over the local copies (delete local `tools/*.py` files the shared wiki no longer has);
   - rebuild `AGENTS.md`: start from the template, refill its placeholders from your current frontmatter values (owner fields, `default_public`, `python`, `created`), carry over every section or rule you added that the template lacks, set `schema_version` to the template's. Show the user a short list of what changes and ask before writing it.
   - Pages keep their own `schema_version` until next edited.
6. Release the lock; `log pull "<n> pulled, <m> created, <k> reconciled[, schema → X.Y.Z]"`. (At first run, the `init` entry covers this.)

## Sync — Pull, Ingest, Push
Triggered by **"sync"**, run as one unit: **Pull** (with its schema propagation) → **Ingest** whatever durable knowledge this session produced and hasn't captured (nothing new → skip without comment) → **Push**. If Pull or Push hits a genuine conflict — the sides disagree and it isn't simply "newer wins" — **stop the sync there**: show each conflicting page one at a time, explain what's in tension, ask which side is right or how to merge. Once resolved, ask whether to continue from where it stopped — don't restart, don't silently resume. Report the sync complete only when every step ran clean.

## Fetch news (read-only, no lock)
`<python> tools/wiki.py --root <shared> news [--since <date>]` lists shared pages by `modified`, newest first, plus the shared log since that date. Read only the entries that look notable (or hand them to a sub-agent) and summarize what actually changed and why it matters — not a file list. No files are written.
