# Personal wiki — quick start

Set up your own personal wiki for this project, connected to the shared one this folder lives in.

## Setup

1. **Create a new, empty folder** anywhere on your own machine — this will be your personal wiki. (Keep it *outside* the shared folder.)
2. **Start an agent session** (Claude Code, Codex CLI, …) with that empty folder as the working directory.
3. **Give it this prompt** — with the real path to the `AGENTS.md` next to this README, as it appears on your machine:

   ```
   Read <full path to this folder>\AGENTS.md and set up my personal wiki here.
   ```

   For example, if the shared wiki is a Shared Drive mounted as `H:\Shared drives\MyProject`, that's `H:\Shared drives\MyProject\personal-template\AGENTS.md`.
4. **The agent asks you four quick things** before it builds anything:
   - your **full name** — written surname-first in every edit's `history` record from now on,
   - a **nickname** — the short form used in casual references and log attributions,
   - the **local path of a related code repo**, or `none`,
   - whether new pages should be **public** (shared with the team on your next Push) or **private** by default.

## What the agent does from there

- Scaffolds a full personal wiki in your folder — its own `AGENTS.md`, `CLAUDE.md`, `index.md`, `log.md`, `wiki-maintenance.md`, `raw/`, `wiki/`.
- Writes a `wiki-shared-link.md` pointing back at the shared wiki — it reads the location straight from the path you gave it, so there's nothing to look up.
- Pulls in **everything currently in the shared wiki**.

## Staying in sync

From then on your folder is a fully independent personal wiki: ingest your own notes, chats and documents into it, and use these standing commands (all documented in your own copy of `AGENTS.md`) to talk to the shared one:

| Say… | What happens |
|---|---|
| `sync` | Pull, then ingest anything new from the session, then push — stops and asks if the two sides really disagree. |
| `push` | Send your `public: true` pages to the shared wiki, reconciling where both sides differ. |
| `pull` | Bring the shared wiki's pages into yours (and pick up any new schema rules). |
| `fetch news` | Read-only summary of what's changed in the shared wiki. |
| `ingest` | Capture the current conversation into `raw/` and update the wiki. |
| `lint` | Check pages for contradicting facts and resolve them with you. |
| `maintain` | Work the structural backlog: links, frontmatter, naming, orphans. |

See `AGENTS.md` in this folder for the full schema this bootstraps from.
