# Lint — factual consistency

Triggered by **"lint"** (incremental) or **"lint all"** (full sweep). Scope: do the facts the pages state agree? Not structure, links or formatting — that's Maintain. A real contradiction is a factual disagreement about the same thing — not different wording, not staleness alone.

1. **Scope** (unlocked): `<python> tools/wiki.py scope` — pages changed since the last `lint` log entry (no lint yet, or "lint all" → `scope --all`). For each changed page it lists:
   - `same-source` — pages drawing on a source ingested since the last lint: read in full and compare;
   - `links-to` — pages it links to: check what the changed page's linking lines claim against that page's current state;
   - `mentioned-by` — pages linking to it: check only their mentioning lines (`scope --excerpts` prints them).
   Without Python: changed = pages whose `modified` is on or after the last lint date; neighbours = pages they link to, pages linking to them, pages sharing a new source.
2. **Compare.** Read current-state sections only; skip `## History`, it is superseded by definition. Many pairs → split them across sub-agents on a smaller model, each returning only suspected contradictions as `page A ↔ page B: claim vs claim (dates, sources)`; verify each one yourself before acting.
3. **Resolve each contradiction live**, before the next. Rule 2 when the dates make it unambiguous (newer wins); otherwise stop and ask the user which side is right, one conflict at a time. Never file a contradiction in `wiki-maintenance.md`.
4. **Write the resolution** (under `wiki.lock`, op `lint`, held from the first fix to the end of the run): on the losing page move the superseded fact to `## History` (dates + source), fix the current state, and bump `modified`/`history`/`schema_version`.
5. **Log, release:** `log lint "<n> pages scanned, <k> conflicts resolved (since <date> | all)"` — clean runs too, since the next lint starts from this entry's date. Release the lock if you took it.
