"""
`lock` — the wiki.lock protocol (schema/lock.md), so two agents never write at once.

wiki.lock is a small text file at the wiki root:

    created: 2026-10-20T09:15:00+02:00
    host: my-laptop
    session: 3f2a…            (one random id per conversation, reused for every lock call)
    operation: ingest

    acquire   create the file — but only if it doesn't exist yet. If another session
              holds it, wait and retry; if it's over an hour old, take it over (and log
              that). Gives up after --retries and says who holds it.
    release   delete the file — only when it carries your session id (or with --force).
    status    say who holds it, if anyone.

Exit codes: 0 = done, 1 = (status) locked, 2 = blocked or bad usage, 3 = not your lock.

Usage:  wiki.py lock acquire --op <verb> --session <id> [--retries 6] [--wait 10]
        wiki.py lock release --session <id> [--force]
        wiki.py lock status
"""

import datetime as dt
import os
import socket
import time
from pathlib import Path

from wiki_common import die, parse_frontmatter, read_text
from wiki_log import append_log
from wiki_settings import LOCK_STALE_AFTER

LOCK_FILE_NAME = "wiki.lock"


# =============================================================================
# Command-line registration
# =============================================================================

def register(subcommands):
    parser = subcommands.add_parser("lock", help="wiki.lock protocol")
    parser.add_argument("action", choices=["acquire", "release", "status"])
    parser.add_argument("--op", help="ingest|query|lint|maintain|init|push|pull")
    parser.add_argument("--session", help="one random id per conversation, reused for every lock call")
    parser.add_argument("--retries", type=int, default=6, help="how often to retry a held lock")
    parser.add_argument("--wait", type=float, default=10, help="seconds between retries")
    parser.add_argument("--force", action="store_true", help="release a lock that isn't yours")
    parser.set_defaults(run=run_lock)


# =============================================================================
# The command
# =============================================================================

def run_lock(args):
    root = Path(args.root).resolve()
    lock_path = root / LOCK_FILE_NAME

    if args.action == "status":
        return _status(lock_path)
    if not args.session:
        die("--session is required (generate one id per conversation and reuse it)")
    if args.action == "release":
        return _release(lock_path, args.session, args.force)
    if not args.op:
        die("--op is required for acquire")
    return _acquire(root, lock_path, args.session, args.op, args.retries, args.wait)


def _status(lock_path):
    lock = _read_lock(lock_path)
    if not lock:
        print("unlocked")
        return 0
    stale = " (STALE)" if _is_stale(lock) else ""
    print(f"locked by host={lock.get('host')} session={lock.get('session')} "
          f"op={lock.get('operation')} since {lock.get('created')}{stale}")
    return 1


def _release(lock_path, session, force):
    lock = _read_lock(lock_path)
    if not lock:
        print("not locked")
        return 0
    if lock.get("session") != session and not force:
        die(f"lock belongs to session {lock.get('session')} (host {lock.get('host')}) — "
            f"not yours; --force to remove", exit_code=3)
    lock_path.unlink()
    print("released")
    return 0


def _acquire(root, lock_path, session, operation, retries, wait_seconds):
    contents = (f"created: {dt.datetime.now().astimezone().isoformat(timespec='seconds')}\n"
                f"host: {socket.gethostname()}\n"
                f"session: {session}\n"
                f"operation: {operation}\n")

    for attempt in range(retries + 1):
        # O_CREAT | O_EXCL: "create, but fail if it already exists" in one step. Checking
        # first and creating second would leave a gap where two agents both succeed.
        try:
            handle = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            pass
        else:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as lock_file:
                lock_file.write(contents)
            print(f"acquired (session {session}, op {operation})")
            return 0

        # Someone holds it. Is it us, an abandoned lock, or a live one?
        lock = _read_lock(lock_path) or {}
        if lock.get("session") == session:
            print(f"already held by this session (op {lock.get('operation')})")
            return 0

        if _is_stale(lock):
            lock_path.write_text(contents, encoding="utf-8", newline="\n")
            note = (f"stale wiki.lock force-cleared (was host {lock.get('host')}, "
                    f"session {lock.get('session')}, op {lock.get('operation')})")
            append_log(root, "maintain", note)
            print(f"acquired — {note}; logged")
            return 0

        if attempt < retries:
            time.sleep(wait_seconds)

    print(f"BLOCKED: wiki.lock held by host={lock.get('host')} session={lock.get('session')} "
          f"op={lock.get('operation')} since {lock.get('created')} — ask the user whether to "
          f"keep waiting or clear it")
    return 2


# =============================================================================
# Helpers
# =============================================================================

def _read_lock(lock_path):
    """The lock file's fields as a dict, or None when there is no lock."""
    try:
        return parse_frontmatter(read_text(lock_path))
    except FileNotFoundError:
        return None


def _is_stale(lock):
    """True when the lock's `created` time is more than LOCK_STALE_AFTER ago.

    A lock with an unreadable timestamp is treated as live, not stale — safer to wait.
    """
    try:
        created = dt.datetime.fromisoformat(str(lock.get("created")))
    except ValueError:
        return False
    if created.tzinfo is None:
        created = created.astimezone()  # assume the local timezone
    return dt.datetime.now(dt.timezone.utc) - created > LOCK_STALE_AFTER
