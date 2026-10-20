#!/usr/bin/env python3
"""LLM Wiki helper — the mechanical half of wiki upkeep, so the agent doesn't spend tokens on it.

Standard library only (Python 3.8+). Run from anywhere; the wiki root defaults to this
script's parent folder (tools/..), override with --root.

  check                     structural report for Maintain (frontmatter, links, orphans, index, log, sizes, secrets)
  scope [--since D|--all]   Lint scope: pages changed since the last lint, each with the pages it must be compared to
  log OP TITLE [--link L]   append one single-line entry to log/YYYY-MM.md
  recent [N]                last N log entries (default 10)
  news [--since D]          pages by `modified` date, newest first, plus log entries since D (use --root for the shared wiki)
  pair --shared PATH        Push/Pull: which pages are new on either side, identical, or differ (personal wikis)
  migrate-log               convert a legacy multi-line log.md into one-line log/YYYY-MM.md files
  capture --out raw/S.md    write a Claude Code session transcript to raw/ as markdown (secrets redacted)
  lock acquire|release|status --op OP --session ID   the wiki.lock protocol

Output is deliberately terse: an agent reads it, so every line should be worth reading.
"""

import argparse
import datetime as dt
import json
import os
import re
import socket
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import unquote

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---------------------------------------------------------------------------- limits
# Keep these in step with the numbers in AGENTS.md ('Page conventions') and schema/maintain.md.
PAGE_CURRENT_MAX = 8 * 1024     # bytes of a page body above its '## History' section
PAGE_HISTORY_MAX = 4 * 1024     # bytes of the '## History' section itself
HISTORY_CAP = 20                # frontmatter `history` entries before Maintain compacts them
INDEX_LINE_MAX = 120            # characters per index.md line
INDEX_SPLIT_LINES = 300         # index.md lines before suggesting a per-category split
LOG_LINE_MAX = 200              # characters per log entry
LOCK_STALE = dt.timedelta(hours=1)
LIST_LIMIT = 15                 # items shown per check category unless --full

JUNK_FILES = {"desktop.ini", "thumbs.db", ".ds_store", ".gitkeep"}
CATEGORY_TYPES = {"parties": "party", "entities": "entity", "concepts": "concept", "summaries": "summary"}
LOG_OPS = {"ingest", "query", "lint", "init", "maintain", "push", "pull"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOG_ENTRY_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\]\s*(\S+)")
WIKILINK_RE = re.compile(r"!?\[\[([^\]\|#]*)(#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
MDLINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

SECRET_PATTERNS = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai-key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{20,}")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{40,}")),
    ("aws-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("password-assignment", re.compile(r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|token)\s*[:=]\s*[\"']?[^\s\"'`]{8,}")),
]


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def today():
    return dt.date.today().isoformat()


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text(encoding="utf-8", errors="replace")


def rel(root, path):
    return Path(path).relative_to(root).as_posix()


# ---------------------------------------------------------------------------- frontmatter

def split_frontmatter(text):
    """Return (frontmatter_text or None, body)."""
    if text.startswith("﻿"):
        text = text[1:]
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return None, text


def _strip_comment(value):
    out, quote = [], None
    for i, ch in enumerate(value):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or value[i - 1].isspace()):
            break
        out.append(ch)
    return "".join(out).strip()


def _scalar(value):
    value = _strip_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(fm):
    """Minimal YAML for wiki frontmatter: scalars, inline [a, b] lists, and '- item' block lists."""
    data, key = {}, None
    for raw in fm.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", raw)
        if m and not raw.startswith((" ", "\t")):
            key, value = m.group(1), m.group(2)
            value = _strip_comment(value)
            if value == "":
                data[key] = []
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                data[key] = [_scalar(v.strip()) for v in inner.split(",")] if inner else []
            else:
                data[key] = _scalar(value)
            continue
        m = re.match(r"^\s+-\s*(.*)$", raw)
        if m and key is not None:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(_scalar(m.group(1)))
    return data


def schema_config(root):
    for name in ("AGENTS.md", "CLAUDE.md"):
        p = root / name
        if p.exists():
            fm, _ = split_frontmatter(read_text(p))
            if fm:
                cfg = parse_frontmatter(fm)
                if cfg.get("type") == "schema" or "schema_version" in cfg:
                    cfg["_file"] = name
                    return cfg
    return {}


# ---------------------------------------------------------------------------- wiki model

class Page:
    def __init__(self, root, path):
        self.path = path
        self.rel = rel(root, path)
        self.text = read_text(path)
        fm, self.body = split_frontmatter(self.text)
        self.has_fm = fm is not None
        self.fm = parse_frontmatter(fm) if fm else {}
        self.current, self.history_section = split_history(self.body)
        parts = Path(self.rel).parts
        self.category = parts[1] if len(parts) > 2 else None
        self.slug = path.stem

    @property
    def sources(self):
        s = self.fm.get("sources", [])
        return [s] if isinstance(s, str) and s else (s or [])


def split_history(body):
    m = re.search(r"(?m)^## History\s*$", body)
    if not m:
        return body, ""
    return body[: m.start()], body[m.start():]


def strip_code(text):
    out, fenced = [], False
    for line in text.split("\n"):
        if FENCE_RE.match(line):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else INLINE_CODE_RE.sub("", line))
    return "\n".join(out)


def extract_links(text):
    """Yield (kind, target, line_no) for wikilinks and local markdown links, outside code."""
    for n, line in enumerate(strip_code(text).split("\n"), 1):
        for m in WIKILINK_RE.finditer(line):
            target = m.group(1).strip()
            if target:
                yield "wiki", target, n
        for m in MDLINK_RE.finditer(line):
            target = m.group(1).strip()
            if re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.I) or target.startswith("#"):
                continue
            yield "md", target, n


class Wiki:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            die(f"wiki root not found: {self.root}")
        self.cfg = schema_config(self.root)
        self.pages = []
        wiki_dir = self.root / "wiki"
        if wiki_dir.is_dir():
            for p in sorted(wiki_dir.rglob("*.md")):
                if "assets" in p.relative_to(wiki_dir).parts[:1]:
                    continue
                self.pages.append(Page(self.root, p))
        self.by_rel = {p.rel: p for p in self.pages}
        # Obsidian-style resolution: lowercase basename (without .md) and lowercase root-relative path.
        self.files = []
        for p in self.root.rglob("*"):
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(self.root).parts):
                self.files.append(p)
        self.by_name, self.by_path = {}, {}
        for f in self.files:
            r = rel(self.root, f)
            stem_key = f.stem.lower() if f.suffix.lower() == ".md" else f.name.lower()
            self.by_name.setdefault(stem_key, []).append(r)
            self.by_path[r.lower()] = r
            if r.lower().endswith(".md"):
                self.by_path[r[:-3].lower()] = r
        # On a name clash (raw/foo.md vs wiki/summaries/foo.md) prefer wiki pages, then root files.
        for hits in self.by_name.values():
            hits.sort(key=lambda r: (0 if r.startswith("wiki/") else 1 if "/" not in r else 2, len(r)))

    def resolve(self, source_rel, kind, target):
        target = unquote(target.split("#")[0]).strip()
        if not target:
            return source_rel  # same-page anchor
        if kind == "wiki":
            t = target.replace("\\", "/").lstrip("/")
            if t.lower() in self.by_path:
                return self.by_path[t.lower()]
            name = t.split("/")[-1].lower()
            if name.endswith(".md"):
                name = name[:-3]
            hits = self.by_name.get(name)
            return hits[0] if hits else None
        base = (self.root / source_rel).parent
        try:
            p = (base / target).resolve()
            r = rel(self.root, p)
        except ValueError:
            return None
        if p.is_file():
            return r
        if (p.with_name(p.name + ".md")).is_file():
            return r + ".md"
        return None

    def link_graph(self, extra=("index.md",)):
        """outgoing[rel] = set(rel), plus raw link records for checks."""
        outgoing, records = {}, []
        sources = [(p.rel, p.text) for p in self.pages]
        for name in extra:
            f = self.root / name
            if f.exists():
                sources.append((name, read_text(f)))
        for src, text in sources:
            outs = outgoing.setdefault(src, set())
            for kind, target, line in extract_links(text):
                hit = self.resolve(src, kind, target)
                records.append((src, kind, target, line, hit))
                if hit and hit != src:
                    outs.add(hit)
        return outgoing, records

    def log_files(self):
        d = self.root / "log"
        if not d.is_dir():
            return []
        return sorted(p for p in d.glob("*.md") if re.match(r"^\d{4}-\d{2}\.md$", p.name))

    def log_entries(self):
        """Yield (date, op, line) from log/YYYY-MM.md files, oldest file first."""
        for f in self.log_files():
            for line in read_text(f).split("\n"):
                m = LOG_ENTRY_RE.match(line)
                if m:
                    yield m.group(1), m.group(2).rstrip("|").lower(), line.rstrip()


# ---------------------------------------------------------------------------- check

def cmd_check(args):
    w = Wiki(args.root)
    root, cfg = w.root, w.cfg
    style = cfg.get("link_style", "")
    mode = cfg.get("mode", "")
    issues = {}

    def add(cat, msg):
        issues.setdefault(cat, []).append(msg)

    # layout
    for d in ("raw", "wiki/parties", "wiki/entities", "wiki/concepts", "wiki/summaries", "wiki/assets", "log"):
        if not (root / d).is_dir():
            add("layout", f"missing folder {d}/")
    for f in ("index.md", "wiki-maintenance.md"):
        if not (root / f).exists():
            add("layout", f"missing {f}")
    if mode == "personal" and not (root / "wiki-shared-link.md").exists():
        add("layout", "missing wiki-shared-link.md")
    lock = root / "wiki.lock"
    if lock.exists():
        info = parse_frontmatter(read_text(lock))
        add("lock", f"wiki.lock present (host={info.get('host')}, op={info.get('operation')}, created={info.get('created')}) — active write or abandoned")

    # pages
    raw_slugs = {p.stem for p in (root / "raw").rglob("*") if p.is_file() and p.name.lower() not in JUNK_FILES} if (root / "raw").is_dir() else set()
    cited = set()
    for p in w.pages:
        fm = p.fm
        cited.update(p.sources)
        if not SLUG_RE.match(p.slug):
            add("naming", f"{p.rel}: filename is not a lowercase-hyphenated slug")
        if not p.has_fm:
            add("frontmatter", f"{p.rel}: no frontmatter")
            continue
        missing = [k for k in ("title", "type", "created", "modified") if not fm.get(k)]
        if missing:
            add("frontmatter", f"{p.rel}: missing {', '.join(missing)}")
        expected = CATEGORY_TYPES.get(p.category)
        if expected and fm.get("type") and fm.get("type") != expected:
            add("frontmatter", f"{p.rel}: type '{fm.get('type')}' but folder implies '{expected}'")
        for k in ("created", "modified"):
            v = fm.get(k)
            if v and not DATE_RE.match(str(v)):
                add("frontmatter", f"{p.rel}: {k} '{v}' is not YYYY-MM-DD")
        if DATE_RE.match(str(fm.get("created", ""))) and DATE_RE.match(str(fm.get("modified", ""))) and fm["modified"] < fm["created"]:
            add("frontmatter", f"{p.rel}: modified is before created")
        if mode == "personal" and str(fm.get("public", "")).lower() not in ("true", "false"):
            add("frontmatter", f"{p.rel}: `public:` missing or not true/false (set it to default_public)")
        hist = fm.get("history")
        if isinstance(hist, list) and len(hist) > HISTORY_CAP:
            add("history", f"{p.rel}: {len(hist)} history entries (cap {HISTORY_CAP}) — compact the oldest")
        for s in p.sources:
            if raw_slugs and s not in raw_slugs:
                add("sources", f"{p.rel}: sources lists '{s}' but raw/ has no such file")
        cur, hist_b = len(p.current.encode("utf-8")), len(p.history_section.encode("utf-8"))
        if cur > PAGE_CURRENT_MAX:
            add("size", f"{p.rel}: {cur // 1024} KB above '## History' (max {PAGE_CURRENT_MAX // 1024}) — split or condense")
        if hist_b > PAGE_HISTORY_MAX:
            add("size", f"{p.rel}: '## History' is {hist_b // 1024} KB (max {PAGE_HISTORY_MAX // 1024}) — condense to one line per superseded fact")
        sup = [n for n, line in enumerate(p.current.split("\n"), 1) if re.search(r"supersed", line, re.I)]
        if sup:
            add("superseded", f"{p.rel}: {len(sup)} 'superseded' mention(s) above '## History' — move old facts down (review)")
        if p.category == "summaries" and raw_slugs and p.slug not in raw_slugs:
            add("sources", f"{p.rel}: summary without a raw/{p.slug}.* source")

    summary_slugs = {p.slug for p in w.pages if p.category == "summaries"}
    for s in sorted(raw_slugs - summary_slugs):
        add("raw-only", f"raw/{s}: no summary page (fine if raw-only was intended)")

    # links
    outgoing, records = w.link_graph()
    wrong_style = {}
    for src, kind, target, line, hit in records:
        if hit is None:
            add("broken-links", f"{src}:{line}: {target}")
        if style == "wikilinks" and kind == "md" and target.split("#")[0].lower().endswith(".md"):
            wrong_style[src] = wrong_style.get(src, 0) + 1
        elif style == "markdown" and kind == "wiki":
            wrong_style[src] = wrong_style.get(src, 0) + 1
    for src, n in sorted(wrong_style.items()):
        other = "markdown links" if style == "wikilinks" else "[[wikilinks]]"
        add("link-style", f"{src}: {n} {other} (link_style is {style})")

    inbound = {}
    for src, outs in outgoing.items():
        for t in outs:
            inbound.setdefault(t, set()).add(src)
    for p in w.pages:
        if p.category == "summaries":
            if p.slug not in cited and not inbound.get(p.rel):
                add("orphans", f"{p.rel}: no page cites it in `sources:` or links to it")
        elif not inbound.get(p.rel):
            add("orphans", f"{p.rel}: no inbound links")

    # index
    idx = root / "index.md"
    if idx.exists():
        lines = read_text(idx).split("\n")
        indexed = outgoing.get("index.md", set())
        long_lines = [(n, len(l)) for n, l in enumerate(lines, 1) if len(l) > INDEX_LINE_MAX and l.lstrip().startswith(("-", "*"))]
        if long_lines:
            worst = max(long_lines, key=lambda x: x[1])
            add("index", f"index.md: {len(long_lines)} catalog line(s) over {INDEX_LINE_MAX} chars (longest: line {worst[0]}, {worst[1]} chars) — trim to one short clause")
        listed_summaries = [t for t in indexed if t.startswith("wiki/summaries/")]
        if listed_summaries:
            add("index", f"index.md lists {len(listed_summaries)} summary page(s) — summaries stay out of the index (reached via `sources:` and log/)")
        listed_raw = [t for t in indexed if t.startswith("raw/")]
        if listed_raw:
            add("index", f"index.md lists {len(listed_raw)} raw file(s) — raw/ stays out of the index (each summary links its source)")
        for p in w.pages:
            if p.category != "summaries" and p.rel not in indexed:
                add("index", f"{p.rel}: not in index.md")
        if len(lines) > INDEX_SPLIT_LINES:
            add("index", f"index.md has {len(lines)} lines — consider splitting into index/<category>.md")

    # log
    if (root / "log.md").exists():
        add("log", "legacy log.md present — run `wiki.py migrate-log`")
    for f in w.log_files():
        body = [l for l in read_text(f).split("\n") if l.strip() and not l.startswith("# ")]
        extra = [l for l in body if not LOG_ENTRY_RE.match(l)]
        long_ = [l for l in body if LOG_ENTRY_RE.match(l) and len(l) > LOG_LINE_MAX]
        if extra:
            add("log", f"log/{f.name}: {len(extra)} non-entry line(s) — entries are one line each, details belong in pages")
        if long_:
            add("log", f"log/{f.name}: {len(long_)} entr(y/ies) over {LOG_LINE_MAX} chars")

    # secrets (wiki/ + raw/ + root files)
    scan = list(w.pages) + [Page(root, p) for p in (root / "raw").rglob("*.md")] if (root / "raw").is_dir() else list(w.pages)
    for p in scan:
        for n, line in enumerate(p.text.split("\n"), 1):
            for name, rx in SECRET_PATTERNS:
                if rx.search(line):
                    add("secrets", f"{p.rel}:{n}: looks like a {name} (value not shown)")
                    break

    # report
    print(f"wiki check  root={root}  pages={len(w.pages)}  schema={cfg.get('schema_version', '?')}  link_style={style or '?'}  mode={mode or '?'}")
    if not issues:
        print("clean — no issues")
        return 0
    order = ["lock", "layout", "frontmatter", "naming", "sources", "broken-links", "link-style", "orphans",
             "index", "log", "size", "superseded", "history", "secrets", "raw-only"]
    for cat in sorted(issues, key=lambda c: order.index(c) if c in order else 99):
        items = issues[cat]
        print(f"\n[{cat}] {len(items)}")
        shown = items if args.full else items[:LIST_LIMIT]
        for i in shown:
            print(f"  {i}")
        if len(items) > len(shown):
            print(f"  … +{len(items) - len(shown)} more (--full)")
    total = sum(len(v) for v in issues.values())
    print(f"\n{total} issue(s) in {len(issues)} categor{'y' if len(issues) == 1 else 'ies'}")
    return 1 if args.strict else 0


# ---------------------------------------------------------------------------- scope

def cmd_scope(args):
    w = Wiki(args.root)
    since = None
    if not args.all:
        since = args.since
        if not since:
            lints = [d for d, op, _ in w.log_entries() if op == "lint"]
            since = max(lints) if lints else None
    outgoing, records = w.link_graph(extra=())
    mentions = {}  # target -> [(source, line_no)]
    for src, _, _, line, hit in records:
        if hit and hit != src and hit in w.by_rel:
            mentions.setdefault(hit, []).append((src, line))
    by_source = {}
    for p in w.pages:
        for s in p.sources:
            by_source.setdefault(s, set()).add(p.rel)
    changed = [p for p in w.pages if since is None or str(p.fm.get("modified", "9999")) >= since]
    if since is None:
        print(f"lint scope: ALL {len(w.pages)} pages (no previous lint, or --all)")
    else:
        print(f"lint scope since {since}: {len(changed)} changed page(s)")
    print("same-source: read in full and compare | links-to: check the linking lines' claims against that page | "
          "mentioned-by: check only the mentioning lines (--excerpts prints them).  Paths are under wiki/, no .md")

    def short(r):
        return r[5:-3] if r.startswith("wiki/") and r.endswith(".md") else r

    def excerpt(src, line):
        lines = w.by_rel[src].text.split("\n")
        text = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        return f"{short(src)}:{line}: {text[:240]}{'…' if len(text) > 240 else ''}"

    # A page changed because of a source ingested since the last lint; only those sources are a reason
    # to compare whole pages. Older shared sources were already linted when they arrived.
    recent = {p.slug for p in changed if p.category == "summaries"} if since else None
    full, checked = set(), set()
    for p in sorted(changed, key=lambda x: x.rel):
        same = set()
        for s in p.sources:
            if recent is None or s in recent:
                same |= by_source.get(s, set())
        same.discard(p.rel)
        links_to = sorted(t for t in outgoing.get(p.rel, set()) if t in w.by_rel and t not in same and t != p.rel)
        inbound = sorted({s for s, _ in mentions.get(p.rel, []) if s not in same and s not in links_to and s != p.rel})
        full |= same | {p.rel}
        checked |= set(links_to) | set(inbound)
        print(f"\n{short(p.rel)}")
        if same:
            print(f"  same-source: {', '.join(short(r) for r in sorted(same))}")
        if links_to:
            print(f"  links-to: {', '.join(short(r) for r in links_to)}")
        if inbound and args.excerpts:
            print(f"  mentioned-by {len(inbound)}:")
            for src, line in mentions[p.rel]:
                if src in inbound:
                    print(f"    {excerpt(src, line)}")
        elif inbound:
            print(f"  mentioned-by: {', '.join(short(r) for r in inbound)}")
    print(f"\n{len(full)} page(s) to read in full; {len(checked - full)} more to spot-check by their linking lines")
    return 0


# ---------------------------------------------------------------------------- log

def append_log(root, op, title, link=None, date=None):
    op = op.lower()
    if op not in LOG_OPS:
        die(f"log op must be one of {sorted(LOG_OPS)}")
    date = date or today()
    if not DATE_RE.match(date):
        die("date must be YYYY-MM-DD")
    title = " ".join(title.split())
    line = f"## [{date}] {op} | {title}" + (f" → {link}" if link else "")
    if len(line) > LOG_LINE_MAX:
        print(f"warning: entry is {len(line)} chars (max {LOG_LINE_MAX}); shorten the title", file=sys.stderr)
    d = Path(root) / "log"
    d.mkdir(exist_ok=True)
    f = d / f"{date[:7]}.md"
    new = not f.exists()
    with open(f, "a", encoding="utf-8", newline="\n") as fh:
        if new:
            fh.write(f"# Log — {date[:7]}\n\n")
        fh.write(line + "\n")
    return f, line


def cmd_log(args):
    f, line = append_log(Path(args.root), args.op, args.title, args.link, args.date)
    print(f"{rel(Path(args.root).resolve(), f.resolve())}: {line}")
    return 0


def cmd_recent(args):
    w = Wiki(args.root)
    entries = [e for e in w.log_entries() if (not args.since or e[0] >= args.since) and (not args.op or e[1] == args.op)]
    for _, _, line in entries[-args.n:] if not args.since else entries:
        print(line)
    if not entries:
        print("(no log entries)")
    return 0


def cmd_news(args):
    w = Wiki(args.root)
    rows = []
    for p in w.pages:
        m = str(p.fm.get("modified", ""))
        if not DATE_RE.match(m):
            m = dt.date.fromtimestamp(p.path.stat().st_mtime).isoformat() + "*"
        if not args.since or m >= args.since:
            rows.append((m, p.rel, p.fm.get("title", p.slug)))
    rows.sort(reverse=True)
    print(f"{len(rows)} page(s) modified{' since ' + args.since if args.since else ''} in {w.root}  (* = file mtime, no `modified`)")
    for m, r, t in rows[: args.limit]:
        print(f"{m}  {r}  — {t}")
    if len(rows) > args.limit:
        print(f"… +{len(rows) - args.limit} more (--limit)")
    entries = [e for e in w.log_entries() if not args.since or e[0] >= args.since]
    if entries:
        print(f"\nlog ({len(entries)} entr{'y' if len(entries) == 1 else 'ies'}):")
        for _, _, line in entries[-args.limit:]:
            print(line)
    return 0


# ---------------------------------------------------------------------------- pair (Push/Pull)

def _comparable(page):
    text = page.text.replace("\r\n", "\n")
    text = re.sub(r"(?m)^public:.*\n", "", text, count=1)
    return "\n".join(l.rstrip() for l in text.strip().split("\n"))


def cmd_pair(args):
    local, shared = Wiki(args.root), Wiki(args.shared)
    L, S = local.by_rel, shared.by_rel
    is_public = lambda p: str(p.fm.get("public", "")).lower() == "true"
    rows = {"push-new": [], "pull-new": [], "differ": [], "private-collision": []}
    identical = private = 0
    for r, p in sorted(L.items()):
        if r not in S:
            if is_public(p):
                rows["push-new"].append(r)
            else:
                private += 1
        elif not is_public(p):
            rows["private-collision"].append(r)
        elif _comparable(p) == _comparable(S[r]):
            identical += 1
        else:
            lm, sm = str(p.fm.get("modified", "?")), str(S[r].fm.get("modified", "?"))
            newer = "local" if lm > sm else "shared" if sm > lm else "same date"
            rows["differ"].append(f"{r}  (local {lm}, shared {sm}: {newer} newer)")
    rows["pull-new"] = [r for r in sorted(S) if r not in L]
    print(f"pair  local={local.root}  shared={shared.root}")
    print(f"identical: {identical}   private (never pushed): {private}")
    notes = {"push-new": "public here, missing on shared — Push creates them verbatim",
             "pull-new": "on shared, missing here — Pull copies them in (public: true)",
             "differ": "on both, content differs — read both and reconcile (rule 2/3)",
             "private-collision": "public: false here but a shared page has the same path — never push; Pull files a maintenance task"}
    for k, items in rows.items():
        if items:
            print(f"\n[{k}] {len(items)} — {notes[k]}")
            for i in (items if args.full else items[:LIST_LIMIT * 2]):
                print(f"  {i}")
            if not args.full and len(items) > LIST_LIMIT * 2:
                print(f"  … +{len(items) - LIST_LIMIT * 2} more (--full)")
    return 0


# ---------------------------------------------------------------------------- migrate-log

def cmd_migrate_log(args):
    root = Path(args.root).resolve()
    legacy = root / "log.md"
    if not legacy.exists():
        print("no legacy log.md — nothing to migrate")
        return 0
    text = read_text(legacy)
    entries, cur = [], None
    for line in text.split("\n"):
        m = LOG_ENTRY_RE.match(line)
        if m:
            cur = {"date": m.group(1), "head": line.strip(), "body": []}
            entries.append(cur)
        elif cur is not None:
            cur["body"].append(line)
    # Find a summary link in each entry's body, so the one-liner still points at the details.
    # Long legacy titles are cut; the full text stays in log/legacy-log.md.
    # Long legacy titles are cut; the full text stays in log/legacy-log.md.
    for e in entries:
        head = e["head"]
        if len(head) > LOG_LINE_MAX - 60:
            m = re.match(r"^(## \[[^\]]+\][^|]*\|)(.*)$", head)
            if m:
                head = m.group(1) + m.group(2)[: LOG_LINE_MAX - 60 - len(m.group(1))].rstrip() + "…"
        if "summaries/" not in head:
            body = "\n".join(e["body"])
            m = re.search(r"\[\[[^\]]*summaries/[^\]]+\]\]|\[[^\]]*\]\([^)]*summaries/[^)]+\)", body)
            if m and len(m.group(0)) < 80:
                head = f"{head} → {m.group(0)}"
        e["line"] = head
    entries.sort(key=lambda e: e["date"])  # stable: same-day order preserved
    by_month = {}
    for e in entries:
        by_month.setdefault(e["date"][:7], []).append(e["line"])
    if args.dry_run:
        for month, lines in sorted(by_month.items()):
            print(f"log/{month}.md: {len(lines)} entr{'y' if len(lines) == 1 else 'ies'}")
        print(f"would move log.md -> log/legacy-log.md ({len(text) // 1024} KB, kept as an archive, never read)")
        return 0
    d = root / "log"
    target = d / "legacy-log.md"
    if target.exists():
        die("log/legacy-log.md already exists — move it aside first")
    d.mkdir(exist_ok=True)
    for month, lines in sorted(by_month.items()):
        f = d / f"{month}.md"
        existing = read_text(f).split("\n") if f.exists() else [f"# Log — {month}", ""]
        have = set(existing)
        merged = existing[:] if existing[-1:] != [""] else existing[:-1]
        merged += [l for l in lines if l not in have]
        f.write_text("\n".join(merged).rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        print(f"log/{month}.md: {len(lines)} entr{'y' if len(lines) == 1 else 'ies'}")
    legacy.rename(target)
    print(f"moved log.md -> log/legacy-log.md ({len(text) // 1024} KB archive — never read it in normal operation)")
    return 0


# ---------------------------------------------------------------------------- capture

def claude_config_dir():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def find_transcript(args):
    if args.file:
        p = Path(args.file)
        if not p.is_file():
            die(f"transcript not found: {p}")
        return p
    projects = claude_config_dir() / "projects"
    if not projects.is_dir():
        die(f"no Claude Code transcripts under {projects} — pass --file, or capture the conversation another way")
    session = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(args.cwd or os.getcwd()).resolve()))
    proj = projects / slug
    if session:
        hits = ([proj / f"{session}.jsonl"] if proj.is_dir() else []) + list(projects.glob(f"*/{session}.jsonl"))
        hits = [h for h in hits if h.is_file()]
        if not hits:
            die(f"no transcript for session {session} under {projects}")
        return hits[0]
    if not proj.is_dir():
        die(f"no transcript folder for this directory ({proj}) — pass --session or --file")
    files = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not files:
        die(f"no .jsonl transcripts in {proj}")
    return files[-1]


def redact(text):
    count = 0
    for name, rx in SECRET_PATTERNS:
        text, n = rx.subn(f"[REDACTED:{name}]", text)
        count += n
    return text, count


def tool_summary(block):
    inp = block.get("input") or {}
    for k in ("file_path", "path", "command", "pattern", "url", "query", "description", "prompt"):
        v = inp.get(k)
        if isinstance(v, str) and v.strip():
            v = " ".join(v.split())
            return f"{block.get('name', 'tool')} — {v[:140]}{'…' if len(v) > 140 else ''}"
    return block.get("name", "tool")


def cmd_capture(args):
    src = find_transcript(args)
    out = Path(args.out)
    if not out.is_absolute():
        out = Path(args.root).resolve() / out
    if out.exists():
        die(f"{out} already exists — raw/ files are immutable; pick another slug")
    title, session_id, turns = args.title, src.stem, []
    for line in read_text(src).split("\n"):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("type")
        if t == "custom-title" and not args.title:
            title = d.get("customTitle") or title
            continue
        if t not in ("user", "assistant") or d.get("isSidechain") or d.get("isMeta"):
            continue
        content = (d.get("message") or {}).get("content")
        stamp = (d.get("timestamp") or "")[:16].replace("T", " ")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if not isinstance(content, list):
            continue
        for b in content:
            bt = b.get("type")
            if bt == "text":
                txt = re.sub(r"<system-reminder>.*?</system-reminder>", "", b.get("text", ""), flags=re.S).strip()
                if txt:
                    turns.append((t, stamp, txt))
            elif bt == "tool_use" and t == "assistant":
                turns.append(("tool", stamp, tool_summary(b)))
            elif bt == "tool_result" and args.tool_output > 0:
                c = b.get("content")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                c = str(c or "").strip()
                if c:
                    turns.append(("result", stamp, c[: args.tool_output] + ("…" if len(c) > args.tool_output else "")))
            elif bt == "image":
                turns.append((t, stamp, "*(image)*"))
    if not turns:
        die(f"no conversation found in {src}")
    title = title or out.stem
    lines = ["---", f'title: "{title}"', "type: raw-transcript", f"session_id: {session_id}", f"captured: {today()}", "---", "",
             f"# {title}", "", f"*Captured: {today()} from Claude Code session `{session_id}` (tool calls listed, tool output omitted"
             f"{'' if args.tool_output == 0 else f' beyond {args.tool_output} chars'}).*", ""]
    last = None
    for role, stamp, txt in turns:
        if role == "tool":
            lines.append(f"- *tool:* {txt}")
            last = role
            continue
        if role == "result":
            lines += ["", "```", txt, "```", ""]
            continue
        if last == "tool":
            lines.append("")
        lines += [f"**{'User' if role == 'user' else 'Assistant'}** ({stamp}):", "", txt, ""]
        last = role
    body, n = redact("\n".join(lines).rstrip() + "\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8", newline="\n")
    users = sum(1 for r, _, _ in turns if r == "user")
    print(f"wrote {out} ({len(body) // 1024} KB, {users} user turn(s), {n} secret(s) redacted) from {src}")
    return 0


# ---------------------------------------------------------------------------- lock

def lock_info(path):
    try:
        return parse_frontmatter(read_text(path))
    except FileNotFoundError:
        return None


def lock_age(info):
    try:
        created = dt.datetime.fromisoformat(str(info.get("created")))
        if created.tzinfo is None:
            created = created.astimezone()
        return dt.datetime.now(dt.timezone.utc) - created
    except Exception:
        return None


def cmd_lock(args):
    root = Path(args.root).resolve()
    path = root / "wiki.lock"
    if args.action == "status":
        info = lock_info(path)
        if not info:
            print("unlocked")
            return 0
        age = lock_age(info)
        print(f"locked by host={info.get('host')} session={info.get('session')} op={info.get('operation')} "
              f"since {info.get('created')}{' (STALE)' if age and age > LOCK_STALE else ''}")
        return 1
    if not args.session:
        die("--session is required (generate one id per conversation and reuse it)")
    if args.action == "release":
        info = lock_info(path)
        if not info:
            print("not locked")
            return 0
        if info.get("session") != args.session and not args.force:
            die(f"lock belongs to session {info.get('session')} (host {info.get('host')}) — not yours; --force to remove", 3)
        path.unlink()
        print("released")
        return 0
    # acquire
    if not args.op:
        die("--op is required for acquire")
    content = (f"created: {dt.datetime.now().astimezone().isoformat(timespec='seconds')}\n"
               f"host: {socket.gethostname()}\nsession: {args.session}\noperation: {args.op}\n")
    for attempt in range(args.retries + 1):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            print(f"acquired (session {args.session}, op {args.op})")
            return 0
        except FileExistsError:
            info = lock_info(path) or {}
            if info.get("session") == args.session:
                print(f"already held by this session (op {info.get('operation')})")
                return 0
            age = lock_age(info)
            if age is not None and age > LOCK_STALE:
                path.write_text(content, encoding="utf-8", newline="\n")
                note = f"stale wiki.lock force-cleared (was host {info.get('host')}, session {info.get('session')}, op {info.get('operation')})"
                append_log(root, "maintain", note)
                print(f"acquired — {note}; logged")
                return 0
            if attempt < args.retries:
                time.sleep(args.wait)
                continue
            print(f"BLOCKED: wiki.lock held by host={info.get('host')} session={info.get('session')} "
                  f"op={info.get('operation')} since {info.get('created')} — ask the user whether to keep waiting or clear it")
            return 2
    return 2


# ---------------------------------------------------------------------------- main

def main():
    default_root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(default_root), help="wiki root (default: the folder above tools/)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="structural report for Maintain")
    p.add_argument("--full", action="store_true", help="list every item, not just the first few per category")
    p.add_argument("--strict", action="store_true", help="exit 1 when there are issues (for CI)")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("scope", help="Lint scope: changed pages and their neighbours")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--since", help="YYYY-MM-DD (default: date of the last lint entry in log/)")
    g.add_argument("--all", action="store_true", help="every page (full sweep)")
    p.add_argument("--excerpts", action="store_true", help="print the lines that mention each changed page")
    p.set_defaults(fn=cmd_scope)

    p = sub.add_parser("log", help="append a one-line log entry")
    p.add_argument("op", help="|".join(sorted(LOG_OPS)))
    p.add_argument("title")
    p.add_argument("--link", help="link to the page holding the details, e.g. [[my-summary]]")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p.set_defaults(fn=cmd_log)

    p = sub.add_parser("recent", help="last N log entries")
    p.add_argument("n", nargs="?", type=int, default=10)
    p.add_argument("--since")
    p.add_argument("--op")
    p.set_defaults(fn=cmd_recent)

    p = sub.add_parser("news", help="pages by modified date, newest first")
    p.add_argument("--since")
    p.add_argument("--limit", type=int, default=40)
    p.set_defaults(fn=cmd_news)

    p = sub.add_parser("pair", help="Push/Pull: classify page pairs between this wiki and the shared one")
    p.add_argument("--shared", required=True, help="the shared wiki's root (from wiki-shared-link.md)")
    p.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_pair)

    p = sub.add_parser("migrate-log", help="legacy log.md -> one-line log/YYYY-MM.md")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_migrate_log)

    p = sub.add_parser("capture", help="Claude Code session transcript -> raw/<slug>.md")
    p.add_argument("--out", required=True, help="e.g. raw/my-slug.md (relative to the wiki root)")
    p.add_argument("--session", help="session id (default: $CLAUDE_CODE_SESSION_ID, else newest transcript for --cwd)")
    p.add_argument("--file", help="explicit .jsonl transcript path")
    p.add_argument("--cwd", help="the session's working directory (default: current directory)")
    p.add_argument("--title")
    p.add_argument("--tool-output", type=int, default=0, help="include up to N chars of each tool result (default 0: omit)")
    p.set_defaults(fn=cmd_capture)

    p = sub.add_parser("lock", help="wiki.lock protocol")
    p.add_argument("action", choices=["acquire", "release", "status"])
    p.add_argument("--op", help="ingest|query|lint|maintain|init|push|pull")
    p.add_argument("--session", help="one random id per conversation, reused for every lock call")
    p.add_argument("--retries", type=int, default=6)
    p.add_argument("--wait", type=float, default=10)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_lock)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
