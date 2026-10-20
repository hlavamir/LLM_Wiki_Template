"""
The building blocks every wiki tool shares.

    Small helpers      die(), today(), read_text(), relative()
    Frontmatter        split_frontmatter(), parse_frontmatter(), read_schema_config()
    Pages              the Page class: one markdown file under wiki/
    Links              find_links(): every wikilink and local markdown link in a text
    The wiki           the Wiki class: all pages, link resolution, the link graph, the log
    Secrets            find_secret(), redact_secrets()

Nothing in this file writes to disk; the command modules (wiki_*.py) do that.
"""

import datetime as dt
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from wiki_settings import (
    FENCE_RE,
    INLINE_CODE_RE,
    LOG_ENTRY_RE,
    MDLINK_RE,
    SECRET_PATTERNS,
    WIKILINK_RE,
)


# =============================================================================
# Small helpers
# =============================================================================

def die(message, exit_code=2):
    """Print an error and stop. Exit code 2 = wrong usage or missing input."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def today():
    """Today's date as YYYY-MM-DD."""
    return dt.date.today().isoformat()


def read_text(path):
    """Read a file as UTF-8. A stray invalid byte becomes '�' instead of crashing."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text(encoding="utf-8", errors="replace")


def relative(root, path):
    """`path` relative to `root`, with forward slashes on every OS: 'wiki/parties/acme.md'."""
    return Path(path).relative_to(root).as_posix()


def plural(count, singular, plural_form=None):
    """'1 entry', '3 entries' — pass the plural when it isn't just singular + 's'."""
    return f"{count} {singular if count == 1 else (plural_form or singular + 's')}"


# =============================================================================
# Frontmatter
#
# Wiki pages start with a small YAML block between two '---' lines. We only need a tiny
# subset of YAML, so instead of depending on a YAML library we parse these shapes:
#
#     title: "Some title"         -> a string (quotes removed)
#     sources: [a, b, c]          -> a list
#     history:                    -> a list, one item per '- ' line below it
#       - "2026-10-20 09:00 Doe Jane"
#     link_style: "markdown"  # a comment   -> comments after ' #' are dropped
# =============================================================================

def split_frontmatter(text):
    """Split a markdown file into (frontmatter text, body).

    Returns (None, text) when the file has no frontmatter block.
    """
    if text.startswith("﻿"):  # a byte-order mark some Windows editors add
        text = text[1:]
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if lines[0].strip() != "---":  # e.g. a horizontal rule like '------'
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return None, text  # an opening '---' that is never closed is not frontmatter


def _strip_comment(value):
    """Drop a trailing ' # comment', but not a '#' inside quotes."""
    kept, open_quote = [], None
    for i, char in enumerate(value):
        if open_quote:
            if char == open_quote:
                open_quote = None
        elif char in "\"'":
            open_quote = char
        elif char == "#" and (i == 0 or value[i - 1].isspace()):
            break
        kept.append(char)
    return "".join(kept).strip()


def _scalar(value):
    """A single value: comment removed, surrounding quotes removed."""
    value = _strip_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(frontmatter_text):
    """Turn a frontmatter block into a dict (see the shapes described above)."""
    data, current_key = {}, None
    for line in frontmatter_text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        # "key: value" at the start of a line
        key_match = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if key_match and not line.startswith((" ", "\t")):
            current_key = key_match.group(1)
            value = _strip_comment(key_match.group(2))
            if value == "":
                data[current_key] = []  # a block list follows (or the value is empty)
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                data[current_key] = [_scalar(item.strip()) for item in inner.split(",")] if inner else []
            else:
                data[current_key] = _scalar(value)
            continue

        # "  - item" belonging to the last key
        item_match = re.match(r"^\s+-\s*(.*)$", line)
        if item_match and current_key is not None:
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(_scalar(item_match.group(1)))
    return data


def read_schema_config(root):
    """The wiki's settings: the frontmatter of AGENTS.md (or, in older wikis, CLAUDE.md).

    Useful keys: schema_version, mode ('solo' | 'shared' | 'personal'), link_style.
    Returns {} when neither file has a schema frontmatter.
    """
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = root / name
        if not path.exists():
            continue
        frontmatter, _ = split_frontmatter(read_text(path))
        if frontmatter:
            config = parse_frontmatter(frontmatter)
            if config.get("type") == "schema" or "schema_version" in config:
                config["_file"] = name
                return config
    return {}


# =============================================================================
# Pages
# =============================================================================

def split_history(body):
    """Split a page body into (current state, '## History' section).

    The history part is "" when the page has no '## History' heading.
    """
    match = re.search(r"(?m)^## History\s*$", body)
    if not match:
        return body, ""
    return body[:match.start()], body[match.start():]


class Page:
    """One markdown file in the wiki, read once and kept in memory.

    Attributes:
        path             absolute Path
        rel              path relative to the wiki root, e.g. 'wiki/parties/acme.md'
        slug             file name without '.md', e.g. 'acme'
        category         wiki/ sub-folder ('parties', 'entities', …), or None for wiki/x.md
        text             the whole file
        body             everything after the frontmatter
        has_frontmatter  whether a frontmatter block exists
        fm               the parsed frontmatter (a dict)
        current          the body above '## History' — what is true now
        history_section  the '## History' section, or ""
    """

    def __init__(self, root, path):
        self.path = path
        self.rel = relative(root, path)
        self.slug = path.stem
        parts = Path(self.rel).parts  # ('wiki', 'parties', 'acme.md')
        self.category = parts[1] if len(parts) > 2 else None

        self.text = read_text(path)
        frontmatter, self.body = split_frontmatter(self.text)
        self.has_frontmatter = frontmatter is not None
        self.fm = parse_frontmatter(frontmatter) if frontmatter else {}
        self.current, self.history_section = split_history(self.body)

    @property
    def sources(self):
        """The raw-source slugs in `sources:`, always as a list."""
        value = self.fm.get("sources", [])
        if isinstance(value, str):
            return [value] if value else []
        return value or []

    @property
    def is_public(self):
        """Personal wikis only: does `public:` say true?"""
        return str(self.fm.get("public", "")).lower() == "true"


# =============================================================================
# Links
# =============================================================================

def _blank_out_code(text):
    """Replace code blocks and `inline code` with nothing, keeping line numbers intact.

    Links written inside code are examples, not links.
    """
    lines, inside_fence = [], False
    for line in text.split("\n"):
        if FENCE_RE.match(line):
            inside_fence = not inside_fence
            lines.append("")
        elif inside_fence:
            lines.append("")
        else:
            lines.append(INLINE_CODE_RE.sub("", line))
    return "\n".join(lines)


def find_links(text):
    """Yield (kind, target, line_number) for every link in `text`, outside code.

    kind is 'wiki' for [[wikilinks]] and 'md' for [markdown](links). Web links
    (http:, mailto:, …) and same-page anchors (#heading) are skipped.
    """
    for line_number, line in enumerate(_blank_out_code(text).split("\n"), start=1):
        for match in WIKILINK_RE.finditer(line):
            target = match.group(1).strip()
            if target:
                yield "wiki", target, line_number
        for match in MDLINK_RE.finditer(line):
            target = match.group(1).strip()
            is_url = re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.IGNORECASE)
            if is_url or target.startswith("#"):
                continue
            yield "md", target, line_number


# =============================================================================
# The wiki
# =============================================================================

class Wiki:
    """Everything the tools need to know about one wiki folder.

    Attributes:
        root     absolute Path of the wiki (the folder holding AGENTS.md)
        config   the schema frontmatter (see read_schema_config)
        pages    every Page under wiki/, except wiki/assets/
        by_rel   the same pages keyed by their relative path
    """

    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            die(f"wiki root not found: {self.root}")
        self.config = read_schema_config(self.root)

        # --- the pages ---------------------------------------------------------------
        self.pages = []
        wiki_dir = self.root / "wiki"
        if wiki_dir.is_dir():
            for path in sorted(wiki_dir.rglob("*.md")):
                if path.relative_to(wiki_dir).parts[0] == "assets":
                    continue
                self.pages.append(Page(self.root, path))
        self.by_rel = {page.rel: page for page in self.pages}

        # --- lookup tables for resolving links -----------------------------------------
        # Obsidian resolves [[name]] by file name anywhere in the vault, and [[folder/name]]
        # by path; both case-insensitively. So we index every file (hidden ones excluded):
        #   by_name['acme']                 -> ['wiki/parties/acme.md', …]   (.md files by stem)
        #   by_name['diagram.svg']          -> ['wiki/assets/diagram.svg']   (other files by name)
        #   by_path['wiki/parties/acme']    -> 'wiki/parties/acme.md'        (with or without .md)
        self.by_name, self.by_path = {}, {}
        for path in self.root.rglob("*"):
            rel = relative(self.root, path)
            if not path.is_file() or any(part.startswith(".") for part in rel.split("/")):
                continue
            name_key = path.stem.lower() if path.suffix.lower() == ".md" else path.name.lower()
            self.by_name.setdefault(name_key, []).append(rel)
            self.by_path[rel.lower()] = rel
            if rel.lower().endswith(".md"):
                self.by_path[rel[:-3].lower()] = rel

        # Two files can share a name (raw/foo.md and wiki/summaries/foo.md). Like a reader
        # would, prefer the wiki page, then a file at the root, then anything else.
        def preference(rel):
            if rel.startswith("wiki/"):
                rank = 0
            elif "/" not in rel:
                rank = 1
            else:
                rank = 2
            return rank, len(rel)

        for candidates in self.by_name.values():
            candidates.sort(key=preference)

    # -------------------------------------------------------------------------------------
    # Links
    # -------------------------------------------------------------------------------------

    def resolve(self, source_rel, kind, target):
        """The relative path a link points to, or None when it points nowhere (broken).

        source_rel  the file the link is written in (markdown links are relative to it)
        kind        'wiki' or 'md' (see find_links)
        target      the link target as written
        """
        target = unquote(target.split("#")[0]).strip()  # drop '#heading', decode '%20'
        if not target:
            return source_rel  # a link to a heading on the same page

        if kind == "wiki":
            wanted = target.replace("\\", "/").lstrip("/")
            if wanted.lower() in self.by_path:
                return self.by_path[wanted.lower()]
            name = wanted.split("/")[-1].lower()
            if name.endswith(".md"):
                name = name[:-3]
            candidates = self.by_name.get(name)
            return candidates[0] if candidates else None

        # A markdown link: a path relative to the file it's written in.
        base_folder = (self.root / source_rel).parent
        try:
            path = (base_folder / target).resolve()
            rel = relative(self.root, path)
        except ValueError:
            return None  # points outside the wiki
        if path.is_file():
            return rel
        if path.with_name(path.name + ".md").is_file():  # written without the .md extension
            return rel + ".md"
        return None

    def link_graph(self, extra_files=("index.md",)):
        """Who links to whom.

        Returns (outgoing, records):
            outgoing  {file: set of files it links to}, for every page plus `extra_files`
            records   one (source, kind, target, line_number, resolved_or_None) per link
        """
        texts = [(page.rel, page.text) for page in self.pages]
        for name in extra_files:
            path = self.root / name
            if path.exists():
                texts.append((name, read_text(path)))

        outgoing, records = {}, []
        for source, text in texts:
            links_from_here = outgoing.setdefault(source, set())
            for kind, target, line_number in find_links(text):
                resolved = self.resolve(source, kind, target)
                records.append((source, kind, target, line_number, resolved))
                if resolved and resolved != source:
                    links_from_here.add(resolved)
        return outgoing, records

    # -------------------------------------------------------------------------------------
    # The log
    # -------------------------------------------------------------------------------------

    def log_files(self):
        """The monthly log files, oldest first: log/2026-09.md, log/2026-10.md, …

        log/legacy-log.md (a migrated pre-1.2.0 log) is deliberately not included.
        """
        log_dir = self.root / "log"
        if not log_dir.is_dir():
            return []
        return sorted(path for path in log_dir.glob("*.md")
                      if re.match(r"^\d{4}-\d{2}\.md$", path.name))

    def log_entries(self):
        """Yield (date, verb, line) for every log entry, oldest first."""
        for path in self.log_files():
            for line in read_text(path).split("\n"):
                match = LOG_ENTRY_RE.match(line)
                if match:
                    verb = match.group(2).rstrip("|").lower()
                    yield match.group(1), verb, line.rstrip()


# =============================================================================
# Secrets
# =============================================================================

def find_secret(line):
    """The name of the first secret pattern matching `line`, or None."""
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(line):
            return name
    return None


def redact_secrets(text):
    """Replace everything that looks like a secret with [REDACTED:<kind>].

    Returns (new text, number of replacements).
    """
    total = 0
    for name, pattern in SECRET_PATTERNS:
        text, count = pattern.subn(f"[REDACTED:{name}]", text)
        total += count
    return text, total
