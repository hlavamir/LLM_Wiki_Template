"""
`check` — the structural report behind the Maintain operation (schema/maintain.md).

The agent runs this instead of reading every page itself. It looks at the wiki's
structure only, never at whether facts agree (that is Lint's job), and prints a short
list of findings grouped by category:

    lock          a wiki.lock is present (an active write, or an abandoned one)
    layout        required folders or files are missing
    frontmatter   missing fields, wrong `type:` for the folder, bad dates, missing `public:`
    naming        file names that aren't lowercase-hyphenated slugs
    sources       `sources:` naming raw files that don't exist; summaries without a raw file
    broken-links  links that point nowhere
    link-style    [[wikilinks]] in a markdown-link wiki, or the other way round
    orphans       pages nothing links to (summaries: nothing cites them either)
    index         long catalog lines, summaries or raw files listed, pages missing
    log           a legacy log.md, multi-line or overlong log entries
    size          pages above the size limits
    superseded    'superseded' wording above '## History' (a hint, to be reviewed)
    history       frontmatter `history:` lists past the cap
    secrets       lines that look like credentials (the value is never printed)
    raw-only      raw files without a summary page (often fine; ask once)

Usage:  wiki.py check [--full] [--strict]
"""

import re

from wiki_common import Page, Wiki, find_secret, parse_frontmatter, plural, read_text
from wiki_settings import (
    CATEGORY_TYPES,
    DATE_RE,
    HISTORY_CAP,
    INDEX_LINE_MAX,
    INDEX_SPLIT_LINES,
    JUNK_FILES,
    LIST_LIMIT,
    LOG_ENTRY_RE,
    LOG_LINE_MAX,
    PAGE_CURRENT_MAX,
    PAGE_HISTORY_MAX,
    SLUG_RE,
)

# The order categories are printed in: blocking problems first, judgment calls last.
CATEGORY_ORDER = [
    "lock", "layout", "frontmatter", "naming", "sources", "broken-links", "link-style",
    "orphans", "index", "log", "size", "superseded", "history", "secrets", "raw-only",
]

REQUIRED_FOLDERS = ["raw", "wiki/parties", "wiki/entities", "wiki/concepts",
                    "wiki/summaries", "wiki/assets", "log"]
REQUIRED_FILES = ["index.md", "wiki-maintenance.md"]


# =============================================================================
# Command-line registration
# =============================================================================

def register(subcommands):
    parser = subcommands.add_parser("check", help="structural report for Maintain")
    parser.add_argument("--full", action="store_true",
                        help="list every finding, not just the first few per category")
    parser.add_argument("--strict", action="store_true",
                        help="exit with code 1 when there are findings (for CI)")
    parser.set_defaults(run=run_check)


# =============================================================================
# The command
# =============================================================================

class Findings:
    """Findings collected per category, in the order they were found."""

    def __init__(self):
        self.by_category = {}

    def add(self, category, message):
        self.by_category.setdefault(category, []).append(message)

    def total(self):
        return sum(len(messages) for messages in self.by_category.values())


def run_check(args):
    wiki = Wiki(args.root)
    findings = Findings()
    raw_slugs = _raw_slugs(wiki)

    _check_layout(wiki, findings)
    _check_pages(wiki, findings, raw_slugs)
    outgoing = _check_links(wiki, findings)
    _check_orphans(wiki, findings, outgoing)
    _check_index(wiki, findings, outgoing)
    _check_log(wiki, findings)
    _check_secrets(wiki, findings)

    _print_report(wiki, findings, show_all=args.full)
    return 1 if (args.strict and findings.total()) else 0


# =============================================================================
# The individual checks
# =============================================================================

def _raw_slugs(wiki):
    """The slugs of everything in raw/ (file names without extension), junk files excluded."""
    raw_dir = wiki.root / "raw"
    if not raw_dir.is_dir():
        return set()
    return {path.stem for path in raw_dir.rglob("*")
            if path.is_file() and path.name.lower() not in JUNK_FILES}


def _check_layout(wiki, findings):
    """Required folders and files, the personal wiki's shared link, and a lingering lock."""
    root, mode = wiki.root, wiki.config.get("mode", "")
    for folder in REQUIRED_FOLDERS:
        if not (root / folder).is_dir():
            findings.add("layout", f"missing folder {folder}/")
    for name in REQUIRED_FILES:
        if not (root / name).exists():
            findings.add("layout", f"missing {name}")
    if mode == "personal" and not (root / "wiki-shared-link.md").exists():
        findings.add("layout", "missing wiki-shared-link.md")

    lock_file = root / "wiki.lock"
    if lock_file.exists():
        lock = parse_frontmatter(read_text(lock_file))
        findings.add("lock", f"wiki.lock present (host={lock.get('host')}, op={lock.get('operation')}, "
                             f"created={lock.get('created')}) — active write or abandoned")


def _check_pages(wiki, findings, raw_slugs):
    """Everything that can be judged one page at a time, then raw files without a summary."""
    is_personal = wiki.config.get("mode", "") == "personal"

    for page in wiki.pages:
        fm = page.fm

        # --- file name -----------------------------------------------------------------
        if not SLUG_RE.match(page.slug):
            findings.add("naming", f"{page.rel}: filename is not a lowercase-hyphenated slug")

        # --- frontmatter ---------------------------------------------------------------
        if not page.has_frontmatter:
            findings.add("frontmatter", f"{page.rel}: no frontmatter")
            continue

        missing = [key for key in ("title", "type", "created", "modified") if not fm.get(key)]
        if missing:
            findings.add("frontmatter", f"{page.rel}: missing {', '.join(missing)}")

        expected_type = CATEGORY_TYPES.get(page.category)
        if expected_type and fm.get("type") and fm.get("type") != expected_type:
            findings.add("frontmatter", f"{page.rel}: type '{fm.get('type')}' "
                                        f"but folder implies '{expected_type}'")

        for key in ("created", "modified"):
            value = fm.get(key)
            if value and not DATE_RE.match(str(value)):
                findings.add("frontmatter", f"{page.rel}: {key} '{value}' is not YYYY-MM-DD")

        created, modified = str(fm.get("created", "")), str(fm.get("modified", ""))
        if DATE_RE.match(created) and DATE_RE.match(modified) and modified < created:
            findings.add("frontmatter", f"{page.rel}: modified is before created")

        if is_personal and str(fm.get("public", "")).lower() not in ("true", "false"):
            findings.add("frontmatter", f"{page.rel}: `public:` missing or not true/false "
                                        f"(set it to default_public)")

        history = fm.get("history")
        if isinstance(history, list) and len(history) > HISTORY_CAP:
            findings.add("history", f"{page.rel}: {len(history)} history entries "
                                    f"(cap {HISTORY_CAP}) — compact the oldest")

        # --- sources -------------------------------------------------------------------
        for source in page.sources:
            if raw_slugs and source not in raw_slugs:
                findings.add("sources", f"{page.rel}: sources lists '{source}' "
                                        f"but raw/ has no such file")

        # --- size ----------------------------------------------------------------------
        current_bytes = len(page.current.encode("utf-8"))
        history_bytes = len(page.history_section.encode("utf-8"))
        if current_bytes > PAGE_CURRENT_MAX:
            findings.add("size", f"{page.rel}: {current_bytes // 1024} KB above '## History' "
                                 f"(max {PAGE_CURRENT_MAX // 1024}) — split or condense")
        if history_bytes > PAGE_HISTORY_MAX:
            findings.add("size", f"{page.rel}: '## History' is {history_bytes // 1024} KB "
                                 f"(max {PAGE_HISTORY_MAX // 1024}) — condense to one line "
                                 f"per superseded fact")

        # --- superseded wording in the current-state part -------------------------------
        # Only a hint: "supersedes" can be a legitimate fact. Maintain reviews each one.
        mentions = [line for line in page.current.split("\n")
                    if re.search(r"supersed", line, re.IGNORECASE)]
        if mentions:
            findings.add("superseded", f"{page.rel}: {len(mentions)} 'superseded' mention(s) "
                                       f"above '## History' — move old facts down (review)")

        # --- a summary needs its raw file ---------------------------------------------
        if page.category == "summaries" and raw_slugs and page.slug not in raw_slugs:
            findings.add("sources", f"{page.rel}: summary without a raw/{page.slug}.* source")

    # Raw files nobody summarized. Often deliberate ("keep it raw-only"), so Maintain asks once.
    summary_slugs = {page.slug for page in wiki.pages if page.category == "summaries"}
    for slug in sorted(raw_slugs - summary_slugs):
        findings.add("raw-only", f"raw/{slug}: no summary page (fine if raw-only was intended)")


def _check_links(wiki, findings):
    """Broken links, and links written in the style the wiki doesn't use.

    Returns the outgoing-link map, which the orphan and index checks reuse.
    """
    style = wiki.config.get("link_style", "")
    outgoing, records = wiki.link_graph()

    wrong_style_counts = {}  # file -> how many links in the wrong style
    for source, kind, target, line_number, resolved in records:
        if resolved is None:
            findings.add("broken-links", f"{source}:{line_number}: {target}")

        links_to_a_page = target.split("#")[0].lower().endswith(".md")
        if style == "wikilinks" and kind == "md" and links_to_a_page:
            wrong_style_counts[source] = wrong_style_counts.get(source, 0) + 1
        elif style == "markdown" and kind == "wiki":
            wrong_style_counts[source] = wrong_style_counts.get(source, 0) + 1

    other_style = "markdown links" if style == "wikilinks" else "[[wikilinks]]"
    for source, count in sorted(wrong_style_counts.items()):
        findings.add("link-style", f"{source}: {count} {other_style} (link_style is {style})")

    return outgoing


def _check_orphans(wiki, findings, outgoing):
    """Pages nothing links to. A summary also counts as reached when a page cites its slug."""
    inbound = {}
    for source, targets in outgoing.items():
        for target in targets:
            inbound.setdefault(target, set()).add(source)

    cited = {source for page in wiki.pages for source in page.sources}
    for page in wiki.pages:
        if page.category == "summaries":
            if page.slug not in cited and not inbound.get(page.rel):
                findings.add("orphans", f"{page.rel}: no page cites it in `sources:` or links to it")
        elif not inbound.get(page.rel):
            findings.add("orphans", f"{page.rel}: no inbound links")


def _check_index(wiki, findings, outgoing):
    """index.md: short lines, no summaries or raw files, every other page listed."""
    index_file = wiki.root / "index.md"
    if not index_file.exists():
        return
    lines = read_text(index_file).split("\n")
    listed = outgoing.get("index.md", set())

    long_lines = [(number, len(line)) for number, line in enumerate(lines, start=1)
                  if len(line) > INDEX_LINE_MAX and line.lstrip().startswith(("-", "*"))]
    if long_lines:
        worst_line, worst_length = max(long_lines, key=lambda item: item[1])
        findings.add("index", f"index.md: {len(long_lines)} catalog line(s) over {INDEX_LINE_MAX} "
                              f"chars (longest: line {worst_line}, {worst_length} chars) — trim to "
                              f"one short clause")

    listed_summaries = [rel for rel in listed if rel.startswith("wiki/summaries/")]
    if listed_summaries:
        findings.add("index", f"index.md lists {len(listed_summaries)} summary page(s) — summaries "
                              f"stay out of the index (reached via `sources:` and log/)")

    listed_raw = [rel for rel in listed if rel.startswith("raw/")]
    if listed_raw:
        findings.add("index", f"index.md lists {len(listed_raw)} raw file(s) — raw/ stays out of "
                              f"the index (each summary links its source)")

    for page in wiki.pages:
        if page.category != "summaries" and page.rel not in listed:
            findings.add("index", f"{page.rel}: not in index.md")

    if len(lines) > INDEX_SPLIT_LINES:
        findings.add("index", f"index.md has {len(lines)} lines — consider splitting into "
                              f"index/<category>.md")


def _check_log(wiki, findings):
    """The log is one line per entry, in monthly files."""
    if (wiki.root / "log.md").exists():
        findings.add("log", "legacy log.md present — run `wiki.py migrate-log`")

    for log_file in wiki.log_files():
        content_lines = [line for line in read_text(log_file).split("\n")
                         if line.strip() and not line.startswith("# ")]
        not_entries = [line for line in content_lines if not LOG_ENTRY_RE.match(line)]
        too_long = [line for line in content_lines
                    if LOG_ENTRY_RE.match(line) and len(line) > LOG_LINE_MAX]
        if not_entries:
            findings.add("log", f"log/{log_file.name}: {len(not_entries)} non-entry line(s) — "
                                f"entries are one line each, details belong in pages")
        if too_long:
            findings.add("log", f"log/{log_file.name}: {len(too_long)} entr(y/ies) over "
                                f"{LOG_LINE_MAX} chars")


def _check_secrets(wiki, findings):
    """Credential-looking lines in wiki/ and raw/ (markdown files). Never prints the value."""
    files = list(wiki.pages)
    raw_dir = wiki.root / "raw"
    if raw_dir.is_dir():
        files += [Page(wiki.root, path) for path in raw_dir.rglob("*.md")]

    for page in files:
        for line_number, line in enumerate(page.text.split("\n"), start=1):
            kind = find_secret(line)
            if kind:
                findings.add("secrets", f"{page.rel}:{line_number}: looks like a {kind} "
                                        f"(value not shown)")


# =============================================================================
# Output
# =============================================================================

def _print_report(wiki, findings, show_all):
    config = wiki.config
    print(f"wiki check  root={wiki.root}  pages={len(wiki.pages)}  "
          f"schema={config.get('schema_version', '?')}  "
          f"link_style={config.get('link_style', '') or '?'}  mode={config.get('mode', '') or '?'}")

    if not findings.by_category:
        print("clean — no issues")
        return

    def print_position(category):
        return CATEGORY_ORDER.index(category) if category in CATEGORY_ORDER else len(CATEGORY_ORDER)

    for category in sorted(findings.by_category, key=print_position):
        messages = findings.by_category[category]
        print(f"\n[{category}] {len(messages)}")
        shown = messages if show_all else messages[:LIST_LIMIT]
        for message in shown:
            print(f"  {message}")
        if len(messages) > len(shown):
            print(f"  … +{len(messages) - len(shown)} more (--full)")

    count = len(findings.by_category)
    print(f"\n{findings.total()} issue(s) in {plural(count, 'category', 'categories')}")
