# First run — setup wizard

Read this when `AGENTS.md` sends you here (no `index.md` or `wiki/` yet) — including right after downloading the template in the same session: start at once, don't ask the user to restart or to ask again. This file deletes itself at the end; a running wiki never needs it again.

## How to talk during setup

The person may never have heard of an LLM wiki. Setup is their first impression, so:

- **Plain words, short messages.** Never say: lock, scaffold, frontmatter, schema, prune, placeholder, `link_style`, `mode`, session id, `check`, "Windows Store stub". Do the mechanical work silently; don't narrate it or list files you created.
- **Ask with your question tool when you have one** — a tool that shows the question with clickable answers (Claude Code: `AskUserQuestion`; other agents: their equivalent). **One question per call, in the order below**, so a later question can depend on an earlier answer. Put your proposal first, marked "(Recommended)", give each option a one-line description in plain words, and rely on the tool's own "Other" choice for typed answers. Such tools need at least two options: for a question you can't propose anything for, ask in a normal message instead.
- **No question tool:** ask one question per message, numbered ("Question 2 of 6"), with lettered options.
- **Propose, don't interrogate.** Fill in proposals from what you can see (`git config user.name`, the folder name, a README, the git remote); the user only confirms or corrects. If they already answered something — even several things in one message — don't ask it again.

## 1. Welcome — one short message, then the first question

Something like:

> Let's set up your wiki. The idea: you give me things worth remembering — chats, documents, notes — and I organize them into linked pages you can read and search. Later, when you ask something, I answer from those pages instead of starting from scratch. A few quick questions and it's ready.

## 2. The questions

Ask them in this order. The wording is a suggestion; keep it this plain. *Stored as* is for you — never show it.

1. **"What name should go on your edits?"** — *Every page keeps a record of who changed it and when, written surname first.* Options: your best proposal in `Lastname Firstname` form (from git, the e-mail address, the OS account), plus a variant (other order, or short first name). If the split between first name and surname is unclear, ask. *Stored as* `owner_name` (solo) and in every `history` entry.
2. **"What should I call you?"** — Options: the first name, a short form of it. *Stored as* `owner_nickname`.
3. **"What's this wiki about?"** — Draft a short name and a one-line description from the folder name, a README, the git remote or top-level files. Options: your draft (Recommended); a second, different draft. *Stored as* `project` and **About this wiki**.
4. **"Who will use this wiki?"** — Options:
   - **Just me (Recommended)** — *"One wiki for you, on this computer. You can turn it into a team wiki later, but that takes some manual work."* → `mode: solo`.
   - **My team** — *"A wiki in a shared folder (Google Drive, OneDrive, Dropbox …) that several people add to. Each person also gets a private wiki of their own, where they work before sharing."* → `mode: shared`. Follow up: **"Is this folder somewhere everyone on the team can open?"** — *Yes* / *No, not yet*. If not yet: explain they should move this folder to the shared location (or start again there), and offer to continue as "just me" instead. Mention, in one plain sentence, that on shared drives two people saving at the very same moment can occasionally clash.
5. **"How will you read the wiki?"** — Options:
   - **Obsidian** — *"A free notes app that shows the pages and how they connect."* → `link_style: wikilinks`.
   - **On GitHub or in a browser** → `markdown`.
   - **Both, or not sure (Recommended)** — *"Works everywhere, including Obsidian."* → `markdown`.
   In shared mode, personal wikis inherit this and never ask it.
6. **Solo only — "Is this wiki about a code project on this computer?"** — *"If so, I can look at its code when answering questions. I'll never change it."* Options: **No**, plus up to two plausible project folders you can see (else ask for a path in a normal message if they say yes). *Stored as* `repo_path` (or `none`).

## 3. Build it — silently

While or after asking, without telling the user about each step:

1. **Find Python:** try `python3 --version`, `python --version`, `py --version`; the first that reports Python 3.8+ is `<python>`, else `none`. Only if none works, add one plain sentence to the final message: *"Optional: installing Python 3 (for example `winget install Python.Python.3.12` on Windows) lets me do routine housekeeping faster and cheaper. Everything works without it."*
2. **Lock:** generate a session id (any random string) and run `<python> tools/wiki.py lock acquire --op init --session <id>` (no Python: `schema/lock.md`). Hold it until step 7.
3. **Create** next to `AGENTS.md`: `index.md` (a `# <project> — Index` heading and empty `## Parties`, `## Entities`, `## Concepts` sections), `wiki-maintenance.md` (`## Open tasks` and `## Log`), and the folders `raw/`, `log/`, `wiki/parties/`, `wiki/entities/`, `wiki/concepts/`, `wiki/summaries/`, `wiki/assets/` (a `.gitkeep` in each empty one).
4. **Personalize `AGENTS.md`** with targeted edits: `project`, **About this wiki**, `mode`, `link_style`, `python`, and `created`/`modified` = today. Solo: fill `owner_name`, `owner_nickname`, `repo_path`. Shared: delete those three lines — the schema belongs to the team.
5. **Prune `AGENTS.md`:**
   - Delete everything from the `template-only` marker comment through its `/template-only` closing comment (the bootstrap and first-run sections), and the `TEMPLATE FILE` comment at the top.
   - Spans fenced by `shared-only` / `solo-only` marker comments (closed by `/shared-only` / `/solo-only`; inline or whole blocks): for the chosen mode delete only the two markers; for the other mode delete the markers and everything between them. No marker comments may remain.
   - **Solo:** delete `schema/shared.md` and the `personal-template/` folder, and remove their two lines from the Layout tree.
6. **Shared only — prepare `personal-template/`.** If the folder is missing, download it from the source you bootstrapped from, else from `hlavamir/LLM_Wiki_Template` on `main` (`personal-template/AGENTS.md`, `README.md`, `schema/first-run.md`, `schema/sync.md`); no network → ask the user to copy it in, never invent it. In `personal-template/AGENTS.md` replace `{{PROJECT_NAME}}`, `{{PROJECT_ONE_LINE}}` and `{{wikilinks|markdown}}` with this wiki's values; leave the other `{{…}}` placeholders.
7. **Log, verify, release:** `<python> tools/wiki.py log init "<project name>"` (shared: `"<project name> (shared, set up by Lastname Firstname)"`); `<python> tools/wiki.py check` should report nothing but the lock you hold (anything else: fix it quietly); `lock release --session <id>`. Finally delete this file.

## 4. Done — one short, friendly message

No settings table, no file list, no internals (offer them only if asked). Something like:

> Your wiki is ready. Some things to try:
> - Tell me something worth keeping, or share a document, and say **ingest** — I'll file it into pages.
> - Ask me anything about the project — I'll answer from the wiki and tell you where each fact came from.
> - Open this folder in Obsidian to browse the pages. *(only if they chose Obsidian or Both)*
>
> Now and then, say **maintain** to tidy up the wiki's structure, or **lint** to check that pages don't contradict each other. At the end of a useful conversation I'll offer to save it.

**Shared:** add, in plain words, that each teammate (the user included) now sets up a private wiki in a separate folder on their own computer — the steps are in `personal-template/README.md` in this folder, ready to send round.
