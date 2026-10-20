"""
`scope` — the work list behind the Lint operation (schema/lint.md).

Lint asks whether the facts across pages agree. Comparing every page with every other
page grows with the square of the wiki, so Lint is incremental: it looks only at pages
changed since the last lint, and for each one lists what it has to be compared with.

For each changed page the output has up to three lists:

    same-source   pages drawing on a source that was ingested since the last lint.
                  These state facts from the same material — read them in full and compare.
    links-to      pages the changed page links to. Check what the linking lines claim
                  against that page's current state.
    mentioned-by  pages linking to the changed page. Check only their mentioning lines
                  (--excerpts prints those lines, so the pages needn't be opened at all).

"Since the last lint" means the date of the newest `lint` entry in log/. With no lint
yet, or with --all, every page is in scope.

Usage:  wiki.py scope [--since YYYY-MM-DD | --all] [--excerpts]
"""

from wiki_common import Wiki


# =============================================================================
# Command-line registration
# =============================================================================

def register(subcommands):
    parser = subcommands.add_parser("scope", help="Lint scope: changed pages and their neighbours")
    when = parser.add_mutually_exclusive_group()
    when.add_argument("--since", help="YYYY-MM-DD (default: date of the last lint entry in log/)")
    when.add_argument("--all", action="store_true", help="every page (full sweep)")
    parser.add_argument("--excerpts", action="store_true",
                        help="print the lines that mention each changed page")
    parser.set_defaults(run=run_scope)


# =============================================================================
# The command
# =============================================================================

def run_scope(args):
    wiki = Wiki(args.root)
    since = None if args.all else (args.since or _date_of_last_lint(wiki))

    # Who links to whom, and on which line (for the mentioned-by excerpts).
    outgoing, records = wiki.link_graph(extra_files=())
    mentions = {}  # page -> [(page that links to it, line number), …]
    for source, _kind, _target, line_number, resolved in records:
        if resolved and resolved != source and resolved in wiki.by_rel:
            mentions.setdefault(resolved, []).append((source, line_number))

    # Which pages draw on each raw source.
    pages_by_source = {}
    for page in wiki.pages:
        for source in page.sources:
            pages_by_source.setdefault(source, set()).add(page.rel)

    # A page has "changed" when its `modified` date is on or after `since`.
    # (A page without `modified` sorts as '9999', i.e. always in scope.)
    changed = [page for page in wiki.pages
               if since is None or str(page.fm.get("modified", "9999")) >= since]

    # Only sources ingested since the last lint are a reason to compare whole pages: their
    # summaries changed too. Older shared sources were already linted when they arrived.
    new_sources = {page.slug for page in changed if page.category == "summaries"} if since else None

    _print_header(wiki, since, changed)

    read_in_full, spot_check = set(), set()
    for page in sorted(changed, key=lambda page: page.rel):
        same_source = set()
        for source in page.sources:
            if new_sources is None or source in new_sources:
                same_source |= pages_by_source.get(source, set())
        same_source.discard(page.rel)

        links_to = sorted(target for target in outgoing.get(page.rel, set())
                          if target in wiki.by_rel and target not in same_source
                          and target != page.rel)
        mentioned_by = sorted({source for source, _ in mentions.get(page.rel, [])
                               if source not in same_source and source not in links_to
                               and source != page.rel})

        read_in_full |= same_source | {page.rel}
        spot_check |= set(links_to) | set(mentioned_by)

        print(f"\n{_short(page.rel)}")
        if same_source:
            print(f"  same-source: {', '.join(_short(rel) for rel in sorted(same_source))}")
        if links_to:
            print(f"  links-to: {', '.join(_short(rel) for rel in links_to)}")
        if mentioned_by and args.excerpts:
            print(f"  mentioned-by {len(mentioned_by)}:")
            for source, line_number in mentions[page.rel]:
                if source in mentioned_by:
                    print(f"    {_excerpt(wiki, source, line_number)}")
        elif mentioned_by:
            print(f"  mentioned-by: {', '.join(_short(rel) for rel in mentioned_by)}")

    print(f"\n{len(read_in_full)} page(s) to read in full; "
          f"{len(spot_check - read_in_full)} more to spot-check by their linking lines")
    return 0


# =============================================================================
# Helpers
# =============================================================================

def _date_of_last_lint(wiki):
    """The date of the newest `lint` log entry, or None when there has never been one."""
    lint_dates = [date for date, verb, _line in wiki.log_entries() if verb == "lint"]
    return max(lint_dates) if lint_dates else None


def _print_header(wiki, since, changed):
    if since is None:
        print(f"lint scope: ALL {len(wiki.pages)} pages (no previous lint, or --all)")
    else:
        print(f"lint scope since {since}: {len(changed)} changed page(s)")
    print("same-source: read in full and compare | links-to: check the linking lines' claims "
          "against that page | mentioned-by: check only the mentioning lines (--excerpts prints "
          "them).  Paths are under wiki/, no .md")


def _short(rel):
    """'wiki/parties/acme.md' -> 'parties/acme' — shorter output, fewer tokens."""
    if rel.startswith("wiki/") and rel.endswith(".md"):
        return rel[len("wiki/"):-len(".md")]
    return rel


def _excerpt(wiki, source, line_number, max_chars=240):
    """'parties/acme:12: <the line, trimmed>'."""
    lines = wiki.by_rel[source].text.split("\n")
    text = lines[line_number - 1].strip() if 0 < line_number <= len(lines) else ""
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    return f"{_short(source)}:{line_number}: {text}"
