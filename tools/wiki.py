#!/usr/bin/env python3
"""
LLM Wiki helper — the mechanical half of wiki upkeep, so the agent doesn't spend tokens on it.

This file is the only one you run. It reads the command line and hands over to the module
that implements the command. Each wiki operation from the schema has its own file:

    Command                         File               Used by (schema)
    ------------------------------  -----------------  -------------------------------------
    check                           wiki_maintain.py   Maintain   (schema/maintain.md)
    scope                           wiki_lint.py       Lint       (schema/lint.md)
    log, recent, migrate-log        wiki_log.py        every write; the log/ timeline
    capture                         wiki_ingest.py     Ingest     (AGENTS.md, Operations)
    pair, news                      wiki_sync.py       Push / Pull / Fetch news (schema/sync.md)
    lock                            wiki_lock.py       every write (schema/lock.md)

Shared by all of them:
    wiki_settings.py   limits, folder names, patterns — the numbers you might tune
    wiki_common.py     reading pages and frontmatter, resolving links, the log, secrets

Requirements: Python 3.8 or newer, standard library only — nothing to install.

Run it from anywhere:   python3 tools/wiki.py <command> [options]
The wiki root defaults to the folder above tools/; pass --root to work on another wiki
(e.g. the shared one, from a personal wiki). `wiki.py <command> --help` explains a command.

Output is deliberately terse: an agent reads it, so every line should be worth reading.
"""

import argparse
import sys
from pathlib import Path

# The modules live next to this file. Python adds this file's folder to its search path
# when you run `python tools/wiki.py`, which is what makes these imports work from anywhere.
import wiki_ingest
import wiki_lint
import wiki_lock
import wiki_log
import wiki_maintain
import wiki_sync

# Each module adds its own command(s) through a register() function. This order is the
# order commands appear in `wiki.py --help`.
COMMAND_MODULES = [
    wiki_maintain,  # check
    wiki_lint,      # scope
    wiki_log,       # log, recent, migrate-log
    wiki_sync,      # pair, news
    wiki_ingest,    # capture
    wiki_lock,      # lock
]


def main():
    # Windows consoles default to a legacy code page; page titles with '→' or umlauts
    # would crash print(). Force UTF-8 and never fail on an unprintable character.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="LLM Wiki helper — the mechanical half of wiki upkeep.",
        epilog="Run 'wiki.py <command> --help' for a command's options.")
    default_root = Path(__file__).resolve().parent.parent  # tools/.. = the wiki root
    parser.add_argument("--root", default=str(default_root),
                        help="wiki root (default: the folder above tools/)")

    subcommands = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    for module in COMMAND_MODULES:
        module.register(subcommands)

    args = parser.parse_args()
    sys.exit(args.run(args))  # every command returns its exit code


if __name__ == "__main__":
    main()
