"""
The wiki's timeline: log/YYYY-MM.md, one file per month, one line per entry.

    log          append an entry (used by every operation that writes)
    recent       print the latest entries, so nobody has to read a log file whole
    migrate-log  one-time: turn a pre-1.2.0 log.md (multi-line entries) into monthly files

An entry looks like this, and never runs over more than one line:

    ## [2026-10-20] ingest | Phase 3 scoping call → [[phase3-scoping-call]]

Details belong in the linked page, not in the log. Keeping entries to one line is what
lets an agent scan a month of activity for a few hundred tokens.

Usage:  wiki.py log <verb> "<title>" [--link LINK] [--date YYYY-MM-DD]
        wiki.py recent [N] [--since YYYY-MM-DD] [--op VERB]
        wiki.py migrate-log [--dry-run]
"""

import re
import sys
from pathlib import Path

from wiki_common import Wiki, die, plural, read_text, relative, today
from wiki_settings import DATE_RE, LOG_ENTRY_RE, LOG_LINE_MAX, LOG_OPS


# =============================================================================
# Command-line registration
# =============================================================================

def register(subcommands):
    parser = subcommands.add_parser("log", help="append a one-line log entry")
    parser.add_argument("op", help="|".join(sorted(LOG_OPS)))
    parser.add_argument("title")
    parser.add_argument("--link", help="link to the page holding the details, e.g. [[my-summary]]")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today)")
    parser.set_defaults(run=run_log)

    parser = subcommands.add_parser("recent", help="last N log entries")
    parser.add_argument("n", nargs="?", type=int, default=10)
    parser.add_argument("--since", help="every entry on or after YYYY-MM-DD (ignores N)")
    parser.add_argument("--op", help="only entries with this verb")
    parser.set_defaults(run=run_recent)

    parser = subcommands.add_parser("migrate-log", help="legacy log.md -> one-line log/YYYY-MM.md")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    parser.set_defaults(run=run_migrate_log)


# =============================================================================
# Appending — also used by wiki_lock.py to record a stale lock being cleared
# =============================================================================

def append_log(root, verb, title, link=None, date=None):
    """Append one entry to log/<YYYY-MM>.md, creating the file when a month starts.

    Returns (path of the log file, the line written).
    """
    verb = verb.lower()
    if verb not in LOG_OPS:
        die(f"log op must be one of {sorted(LOG_OPS)}")
    date = date or today()
    if not DATE_RE.match(date):
        die("date must be YYYY-MM-DD")

    title = " ".join(title.split())  # newlines and runs of spaces become single spaces
    line = f"## [{date}] {verb} | {title}"
    if link:
        line += f" → {link}"
    if len(line) > LOG_LINE_MAX:
        print(f"warning: entry is {len(line)} chars (max {LOG_LINE_MAX}); shorten the title",
              file=sys.stderr)

    log_dir = Path(root) / "log"
    log_dir.mkdir(exist_ok=True)
    month_file = log_dir / f"{date[:7]}.md"
    is_new_month = not month_file.exists()

    # Opened for appending: the existing entries are never read, however long the log gets.
    with open(month_file, "a", encoding="utf-8", newline="\n") as handle:
        if is_new_month:
            handle.write(f"# Log — {date[:7]}\n\n")
        handle.write(line + "\n")
    return month_file, line


# =============================================================================
# The commands
# =============================================================================

def run_log(args):
    root = Path(args.root).resolve()
    month_file, line = append_log(root, args.op, args.title, args.link, args.date)
    print(f"{relative(root, month_file.resolve())}: {line}")
    return 0


def run_recent(args):
    wiki = Wiki(args.root)
    entries = [(date, verb, line) for date, verb, line in wiki.log_entries()
               if (not args.since or date >= args.since) and (not args.op or verb == args.op)]

    # With --since, everything from that date on; otherwise the last N.
    shown = entries if args.since else entries[-args.n:]
    for _date, _verb, line in shown:
        print(line)
    if not entries:
        print("(no log entries)")
    return 0


def run_migrate_log(args):
    """Convert a legacy log.md into monthly one-line files.

    Each old entry keeps its heading line (shortened if very long) plus, when its body
    linked a summary page, that link. The old file is moved to log/legacy-log.md — kept
    as an archive, never read in normal operation — so nothing is lost.
    """
    root = Path(args.root).resolve()
    legacy_file = root / "log.md"
    if not legacy_file.exists():
        print("no legacy log.md — nothing to migrate")
        return 0
    legacy_text = read_text(legacy_file)

    entries = _parse_legacy_entries(legacy_text)
    for entry in entries:
        entry["line"] = _one_line_version(entry)

    # Old logs were "append-only" but not always in date order. Sorting is stable, so entries
    # from the same day keep their original order.
    entries.sort(key=lambda entry: entry["date"])
    lines_by_month = {}
    for entry in entries:
        lines_by_month.setdefault(entry["date"][:7], []).append(entry["line"])

    size_kb = len(legacy_text) // 1024
    if args.dry_run:
        for month, lines in sorted(lines_by_month.items()):
            print(f"log/{month}.md: {plural(len(lines), 'entry', 'entries')}")
        print(f"would move log.md -> log/legacy-log.md ({size_kb} KB, kept as an archive, never read)")
        return 0

    log_dir = root / "log"
    archive = log_dir / "legacy-log.md"
    if archive.exists():
        die("log/legacy-log.md already exists — move it aside first")
    log_dir.mkdir(exist_ok=True)

    for month, lines in sorted(lines_by_month.items()):
        _merge_into_month_file(log_dir / f"{month}.md", month, lines)
        print(f"log/{month}.md: {plural(len(lines), 'entry', 'entries')}")

    legacy_file.rename(archive)
    print(f"moved log.md -> log/legacy-log.md ({size_kb} KB archive — never read it in normal operation)")
    return 0


# =============================================================================
# migrate-log helpers
# =============================================================================

def _parse_legacy_entries(text):
    """Split an old log into entries: each '## [date] …' heading plus the lines below it."""
    entries, current = [], None
    for line in text.split("\n"):
        match = LOG_ENTRY_RE.match(line)
        if match:
            current = {"date": match.group(1), "heading": line.strip(), "body": []}
            entries.append(current)
        elif current is not None:
            current["body"].append(line)
    return entries


def _one_line_version(entry):
    """The entry's heading, cut to fit, plus a link to its summary page if the body had one."""
    line = entry["heading"]

    # Very long legacy titles are cut (leaving room for a link); the full text stays in
    # log/legacy-log.md.
    room = LOG_LINE_MAX - 60
    if len(line) > room:
        parts = re.match(r"^(## \[[^\]]+\][^|]*\|)(.*)$", line)  # "## [date] verb |" + title
        if parts:
            prefix, title = parts.group(1), parts.group(2)
            line = prefix + title[:room - len(prefix)].rstrip() + "…"

    # Point the one-liner at the details: the first summary link found in the entry's body.
    if "summaries/" not in line:
        body = "\n".join(entry["body"])
        summary_link = re.search(
            r"\[\[[^\]]*summaries/[^\]]+\]\]"        # [[wiki/summaries/x]] or [[…|label]]
            r"|\[[^\]]*\]\([^)]*summaries/[^)]+\)",  # [label](../summaries/x.md)
            body)
        if summary_link and len(summary_link.group(0)) < 80:
            line = f"{line} → {summary_link.group(0)}"
    return line


def _merge_into_month_file(month_file, month, new_lines):
    """Write entries into a monthly file, keeping any entries it already has (no duplicates)."""
    if month_file.exists():
        existing = read_text(month_file).split("\n")
    else:
        existing = [f"# Log — {month}", ""]
    already_there = set(existing)

    merged = existing[:-1] if existing[-1:] == [""] else existing[:]
    merged += [line for line in new_lines if line not in already_there]
    month_file.write_text("\n".join(merged).rstrip("\n") + "\n", encoding="utf-8", newline="\n")
