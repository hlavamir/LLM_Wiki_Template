"""
`capture` — step 1 of the Ingest operation for the conversation itself.

Ingesting a chat means saving it to raw/ first. Having the model re-type the whole
conversation costs a lot of output tokens; this command copies it from the transcript
file Claude Code already keeps on disk:

    ~/.claude/projects/<working directory, non-alphanumerics replaced by '-'>/<session id>.jsonl

(CLAUDE_CONFIG_DIR overrides ~/.claude.) Each line of that file is one JSON event. We
keep the user's and the assistant's text, list tool calls as one line each, leave tool
output out (unless --tool-output asks for some), skip sub-agent and system chatter, and
replace anything that looks like a credential with [REDACTED:<kind>].

Which session: --file, else --session, else $CLAUDE_CODE_SESSION_ID (set inside Claude
Code), else the newest transcript for the working directory (--cwd).

Other agents: use their own transcript export instead; there is no shared format.

Usage:  wiki.py capture --out raw/<slug>.md [--title T] [--session ID | --file PATH]
                        [--cwd DIR] [--tool-output N]
"""

import json
import os
import re
from pathlib import Path

from wiki_common import die, read_text, redact_secrets, today

# Tool-call arguments worth showing, in order of preference: the first one present wins.
TOOL_ARGUMENT_KEYS = ("file_path", "path", "command", "pattern", "url", "query", "description", "prompt")
TOOL_ARGUMENT_MAX = 140  # characters of that argument to show


# =============================================================================
# Command-line registration
# =============================================================================

def register(subcommands):
    parser = subcommands.add_parser("capture", help="Claude Code session transcript -> raw/<slug>.md")
    parser.add_argument("--out", required=True, help="e.g. raw/my-slug.md (relative to the wiki root)")
    parser.add_argument("--session",
                        help="session id (default: $CLAUDE_CODE_SESSION_ID, else newest transcript for --cwd)")
    parser.add_argument("--file", help="explicit .jsonl transcript path")
    parser.add_argument("--cwd", help="the session's working directory (default: current directory)")
    parser.add_argument("--title", help="title for the raw file (default: the session's title)")
    parser.add_argument("--tool-output", type=int, default=0,
                        help="include up to N chars of each tool result (default 0: omit)")
    parser.set_defaults(run=run_capture)


# =============================================================================
# The command
# =============================================================================

def run_capture(args):
    transcript = _find_transcript(args)

    out = Path(args.out)
    if not out.is_absolute():
        out = Path(args.root).resolve() / out
    if out.exists():
        die(f"{out} already exists — raw/ files are immutable; pick another slug")

    session_title, turns = _read_transcript(transcript, args.tool_output)
    if not turns:
        die(f"no conversation found in {transcript}")
    title = args.title or session_title or out.stem
    session_id = transcript.stem

    markdown = _to_markdown(title, session_id, turns, args.tool_output)
    markdown, redactions = redact_secrets(markdown)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8", newline="\n")
    user_turns = sum(1 for role, _, _ in turns if role == "user")
    print(f"wrote {out} ({len(markdown) // 1024} KB, {user_turns} user turn(s), "
          f"{redactions} secret(s) redacted) from {transcript}")
    return 0


# =============================================================================
# Finding the transcript
# =============================================================================

def _claude_config_dir():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def _find_transcript(args):
    if args.file:
        path = Path(args.file)
        if not path.is_file():
            die(f"transcript not found: {path}")
        return path

    projects = _claude_config_dir() / "projects"
    if not projects.is_dir():
        die(f"no Claude Code transcripts under {projects} — pass --file, "
            f"or capture the conversation another way")

    # Claude Code names a project's folder after its working directory:
    # 'D:\Repos\My Wiki' -> 'D--Repos-My-Wiki'.
    working_dir = str(Path(args.cwd or os.getcwd()).resolve())
    project_dir = projects / re.sub(r"[^A-Za-z0-9]", "-", working_dir)

    session = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if session:
        # Look in this project's folder first, then in every project folder.
        candidates = [project_dir / f"{session}.jsonl"] if project_dir.is_dir() else []
        candidates += list(projects.glob(f"*/{session}.jsonl"))
        candidates = [path for path in candidates if path.is_file()]
        if not candidates:
            die(f"no transcript for session {session} under {projects}")
        return candidates[0]

    if not project_dir.is_dir():
        die(f"no transcript folder for this directory ({project_dir}) — pass --session or --file")
    transcripts = sorted(project_dir.glob("*.jsonl"), key=lambda path: path.stat().st_mtime)
    if not transcripts:
        die(f"no .jsonl transcripts in {project_dir}")
    return transcripts[-1]  # the most recently written one: normally the current session


# =============================================================================
# Reading it
# =============================================================================

def _read_transcript(path, tool_output_chars):
    """Return (session title or None, turns), where each turn is (role, timestamp, text).

    role is 'user', 'assistant', 'tool' (a tool call) or 'result' (tool output).
    """
    title, turns = None, []
    for raw_line in read_text(path).split("\n"):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue  # a half-written last line, for instance

        kind = event.get("type")
        if kind == "custom-title":
            title = event.get("customTitle") or title
            continue
        # Skip everything that isn't the main conversation: sub-agents (sidechains),
        # injected system messages (meta), bookkeeping events.
        if kind not in ("user", "assistant") or event.get("isSidechain") or event.get("isMeta"):
            continue

        content = (event.get("message") or {}).get("content")
        timestamp = (event.get("timestamp") or "")[:16].replace("T", " ")  # '2026-10-20 09:15'
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if not isinstance(content, list):
            continue

        for block in content:
            turn = _block_to_turn(kind, block, tool_output_chars)
            if turn:
                turns.append((turn[0], timestamp, turn[1]))
    return title, turns


def _block_to_turn(kind, block, tool_output_chars):
    """One content block -> (role, text), or None to skip it (e.g. the model's thinking)."""
    block_type = block.get("type")

    if block_type == "text":
        # Drop the system reminders Claude Code wraps around user messages.
        text = re.sub(r"<system-reminder>.*?</system-reminder>", "", block.get("text", ""),
                      flags=re.DOTALL).strip()
        return (kind, text) if text else None

    if block_type == "tool_use" and kind == "assistant":
        return "tool", _describe_tool_call(block)

    if block_type == "tool_result" and tool_output_chars > 0:
        output = block.get("content")
        if isinstance(output, list):
            output = "\n".join(part.get("text", "") for part in output if isinstance(part, dict))
        output = str(output or "").strip()
        if not output:
            return None
        if len(output) > tool_output_chars:
            output = output[:tool_output_chars] + "…"
        return "result", output

    if block_type == "image":
        return kind, "*(image)*"

    return None


def _describe_tool_call(block):
    """'Read — D:\\notes\\x.md': the tool's name plus its most telling argument."""
    name = block.get("name", "tool")
    arguments = block.get("input") or {}
    for key in TOOL_ARGUMENT_KEYS:
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            value = " ".join(value.split())
            if len(value) > TOOL_ARGUMENT_MAX:
                value = value[:TOOL_ARGUMENT_MAX] + "…"
            return f"{name} — {value}"
    return name


# =============================================================================
# Writing it
# =============================================================================

def _to_markdown(title, session_id, turns, tool_output_chars):
    output_note = "" if tool_output_chars == 0 else f" beyond {tool_output_chars} chars"
    lines = [
        "---",
        f'title: "{title}"',
        "type: raw-transcript",
        f"session_id: {session_id}",
        f"captured: {today()}",
        "---",
        "",
        f"# {title}",
        "",
        f"*Captured: {today()} from Claude Code session `{session_id}` "
        f"(tool calls listed, tool output omitted{output_note}).*",
        "",
    ]

    previous_role = None
    for role, timestamp, text in turns:
        if role == "tool":
            lines.append(f"- *tool:* {text}")  # tool calls become a compact bullet list
            previous_role = role
            continue
        if role == "result":
            lines += ["", "```", text, "```", ""]
            continue
        if previous_role == "tool":
            lines.append("")  # close the bullet list before the next message
        speaker = "User" if role == "user" else "Assistant"
        lines += [f"**{speaker}** ({timestamp}):", "", text, ""]
        previous_role = role

    return "\n".join(lines).rstrip() + "\n"
