# Concurrency lock (`wiki.lock`)

Read when you first need to write in a session and `tools/wiki.py` can't run, or when a lock gets in the way. With Python, `tools/wiki.py lock acquire|release|status` implements everything below.

Several agents — parallel sessions, other machines, teammates' agents — may write to a wiki at once. `wiki.lock`, a plaintext file at the wiki root, must be held by any operation that writes to `wiki/`, `index.md`, `log/` or `wiki-maintenance.md`.

**Contents**
```
created: <ISO-8601 timestamp with UTC offset>
host: <machine name>
session: <random id, generated once per conversation>
operation: <ingest | query | lint | maintain | init | push | pull>
```

**Lock late, release early.** Read, research and draft before acquiring; never hold the lock while composing or waiting on the user. A single-item write (one Ingest, one Query write-back) acquires right before its first file write and releases right after its last. Whole-wiki sweeps — Lint, Maintain, Push, Pull — acquire once at the start (after any up-front reading) and hold until the run ends, so no other agent sees the wiki half-updated.

**Acquire**
1. Generate the session id the first time this conversation writes; reuse it for every lock call.
2. **Create** `wiki.lock` with an operation that fails if the file exists — never a plain overwrite (PowerShell: `New-Item -ItemType File -Path wiki.lock -ErrorAction Stop`; POSIX shell: `set -C; echo … > wiki.lock`). That closes the gap between "check" and "write".
3. Created → it's yours.
4. Already exists → read it. Your own session id → you already hold it. `created` more than 1 hour ago → stale (a crashed session): overwrite it with your own contents and log `maintain | stale wiki.lock force-cleared (was host …, session …, op …)`. Fresh → wait 10 s and retry, up to 6 times; if it disappears meanwhile, re-read what you're about to touch (`index.md`, the pages, the latest log entries) before locking — another agent may just have changed them. Still locked → stop and tell the user who holds it (`host`/`session`) since when; ask whether to keep waiting or clear it.

**Release:** delete `wiki.lock` as the operation's final step — also when it aborts or errors (a `finally`, not an afterthought). Only delete a lock carrying your own session id.

**Manual override:** deleting `wiki.lock` by hand unlocks immediately — for a crash inside the 1-hour window.

**Synced storage caveat.** On a sync-based drive (Google Drive, OneDrive, a Shared Drive) the lock is *advisory*: sync lag lets two machines each create one before either sees the other's. It reliably prevents the common case — sessions on one machine or well-synced machines — but is no guarantee across machines. A personal wiki on a local disk gets a hard guarantee for writers on that machine; a shared wiki on synced storage does not.
