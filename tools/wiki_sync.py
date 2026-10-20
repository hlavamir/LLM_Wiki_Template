"""
Working with a second wiki: the shared half of a shared+personal pair (schema/sync.md).

    pair   Push/Pull's work list. Compares this wiki's pages with the shared wiki's,
           path by path, so only pages that really differ are ever read in full.
    news   Fetch news. Lists pages by their `modified` date, newest first, plus the log
           entries since a date. Point it at the shared wiki with --root.

Usage:  wiki.py pair --shared <path> [--full]
        wiki.py [--root <shared>] news [--since YYYY-MM-DD] [--limit N]
"""

import datetime as dt
import re

from wiki_common import Wiki, plural
from wiki_settings import DATE_RE, LIST_LIMIT


# =============================================================================
# Command-line registration
# =============================================================================

def register(subcommands):
    parser = subcommands.add_parser(
        "pair", help="Push/Pull: classify page pairs between this wiki and the shared one")
    parser.add_argument("--shared", required=True, help="the shared wiki's root (from wiki-shared-link.md)")
    parser.add_argument("--full", action="store_true", help="list every page, not just the first few")
    parser.set_defaults(run=run_pair)

    parser = subcommands.add_parser("news", help="pages by modified date, newest first")
    parser.add_argument("--since", help="YYYY-MM-DD: only pages and log entries from this date on")
    parser.add_argument("--limit", type=int, default=40, help="how many pages and entries to show")
    parser.set_defaults(run=run_news)


# =============================================================================
# pair
# =============================================================================

# What each group means, printed next to it so the agent knows what to do with it.
PAIR_GROUPS = {
    "push-new": "public here, missing on shared — Push creates them verbatim",
    "pull-new": "on shared, missing here — Pull copies them in (public: true)",
    "differ": "on both, content differs — read both and reconcile (rule 2/3)",
    "private-collision": "public: false here but a shared page has the same path — never push; "
                         "Pull files a maintenance task",
}


def run_pair(args):
    local, shared = Wiki(args.root), Wiki(args.shared)
    groups = {name: [] for name in PAIR_GROUPS}
    identical = private = 0

    for rel, page in sorted(local.by_rel.items()):
        shared_page = shared.by_rel.get(rel)

        if shared_page is None:
            # Only here. Public pages are Push's to create; private ones stay put.
            if page.is_public:
                groups["push-new"].append(rel)
            else:
                private += 1
        elif not page.is_public:
            # A private page sharing a path with a shared one: a naming clash to sort out by hand.
            groups["private-collision"].append(rel)
        elif _comparable(page) == _comparable(shared_page):
            identical += 1
        else:
            local_date = str(page.fm.get("modified", "?"))
            shared_date = str(shared_page.fm.get("modified", "?"))
            if local_date > shared_date:
                newer = "local"
            elif shared_date > local_date:
                newer = "shared"
            else:
                newer = "same date"
            groups["differ"].append(f"{rel}  (local {local_date}, shared {shared_date}: {newer} newer)")

    groups["pull-new"] = [rel for rel in sorted(shared.by_rel) if rel not in local.by_rel]

    print(f"pair  local={local.root}  shared={shared.root}")
    print(f"identical: {identical}   private (never pushed): {private}")
    limit = LIST_LIMIT * 2
    for name, items in groups.items():
        if not items:
            continue
        print(f"\n[{name}] {len(items)} — {PAIR_GROUPS[name]}")
        for item in (items if args.full else items[:limit]):
            print(f"  {item}")
        if not args.full and len(items) > limit:
            print(f"  … +{len(items) - limit} more (--full)")
    return 0


def _comparable(page):
    """A page's text, normalized so cosmetic differences don't count as changes.

    Ignored: Windows vs Unix line endings, trailing spaces, leading/trailing blank lines,
    and the `public:` line (a pulled page gains one; a pushed page may carry one).
    """
    text = page.text.replace("\r\n", "\n")
    text = re.sub(r"(?m)^public:.*\n", "", text, count=1)
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


# =============================================================================
# news
# =============================================================================

def run_news(args):
    wiki = Wiki(args.root)

    # One row per page: (date, path, title). A page without a valid `modified` falls back to
    # its file's modification time, marked with '*' so the agent knows it's less reliable.
    rows = []
    for page in wiki.pages:
        date = str(page.fm.get("modified", ""))
        if not DATE_RE.match(date):
            date = dt.date.fromtimestamp(page.path.stat().st_mtime).isoformat() + "*"
        if not args.since or date >= args.since:
            rows.append((date, page.rel, page.fm.get("title", page.slug)))
    rows.sort(reverse=True)  # newest first

    since_text = f" since {args.since}" if args.since else ""
    print(f"{len(rows)} page(s) modified{since_text} in {wiki.root}  (* = file mtime, no `modified`)")
    for date, rel, title in rows[:args.limit]:
        print(f"{date}  {rel}  — {title}")
    if len(rows) > args.limit:
        print(f"… +{len(rows) - args.limit} more (--limit)")

    entries = [line for date, _verb, line in wiki.log_entries()
               if not args.since or date >= args.since]
    if entries:
        print(f"\nlog ({plural(len(entries), 'entry', 'entries')}):")
        for line in entries[-args.limit:]:
            print(line)
    return 0
