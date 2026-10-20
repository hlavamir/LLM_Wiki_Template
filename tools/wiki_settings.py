"""
Settings shared by every wiki tool: limits, folder names, and text patterns.

This is the one file to edit when you want to tune a number. The limits below are also
written into the schema (AGENTS.md, "Page conventions" and "Navigation", and
schema/maintain.md) — if you change one here, change it there too, so the agent and the
script agree.
"""

import datetime as dt
import re


# =============================================================================
# Limits
# =============================================================================

# A wiki page is "current state first": what is true now, then an optional
# "## History" section holding superseded facts. Each part has its own size limit.
PAGE_CURRENT_MAX = 8 * 1024   # bytes of a page above its "## History" heading
PAGE_HISTORY_MAX = 4 * 1024   # bytes of the "## History" section itself

# The `history:` list in a page's frontmatter gets one entry per edit. Past this many
# entries, Maintain folds the oldest ones into a single summary entry.
HISTORY_CAP = 20

# index.md is a catalog the agent browses, so its lines are kept short and its length bounded.
INDEX_LINE_MAX = 120      # characters per catalog line
INDEX_SPLIT_LINES = 300   # lines before Maintain should split index.md per category

# Every log entry is a single line; anything longer belongs in a wiki page.
LOG_LINE_MAX = 200

# A wiki.lock older than this is presumed abandoned (a crashed session) and may be taken over.
LOCK_STALE_AFTER = dt.timedelta(hours=1)

# How many findings to print per category before cutting off with "… +N more".
# The output is read by an agent, and every line costs tokens.
LIST_LIMIT = 15


# =============================================================================
# Wiki vocabulary
# =============================================================================

# Each wiki/ sub-folder and the `type:` its pages must declare.
CATEGORY_TYPES = {
    "parties": "party",
    "entities": "entity",
    "concepts": "concept",
    "summaries": "summary",
}

# The verbs allowed in log entries ("## [date] <verb> | title").
LOG_OPS = {"ingest", "query", "lint", "init", "maintain", "push", "pull"}

# Files that operating systems and sync clients drop into folders. They are never sources.
JUNK_FILES = {"desktop.ini", "thumbs.db", ".ds_store", ".gitkeep"}


# =============================================================================
# Text patterns
# =============================================================================

# A slug is lowercase words joined by single hyphens: "acme-corp", "mock-mot-subsystem".
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Dates are always ISO: 2026-10-20.
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A log entry line: "## [2026-10-20] ingest | Some title → [[some-summary]]".
# Group 1 is the date, group 2 the verb.
LOG_ENTRY_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\]\s*(\S+)")

# Obsidian wikilinks, also as embeds: [[target]], [[target#heading]], [[target|label]], ![[image.svg]].
# Group 1 is the target.
WIKILINK_RE = re.compile(r"!?\[\[([^\]\|#]*)(#[^\]\|]*)?(?:\|[^\]]*)?\]\]")

# Markdown links and images: [label](path), [label](<path with spaces>), [label](path "title").
# Group 1 is the path.
MDLINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")

# Code is skipped when looking for links: fenced blocks (``` or ~~~) and `inline code`.
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

# Things that look like credentials. `check` reports them (without printing the value) and
# `capture` replaces them with [REDACTED:<name>]. The list errs on the side of false alarms.
SECRET_PATTERNS = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{20,}")),
    ("github-token", re.compile(
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{40,}")),
    ("aws-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("jwt", re.compile(
        r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("password-assignment", re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|token)\s*[:=]\s*[\"']?[^\s\"'`]{8,}")),
]
