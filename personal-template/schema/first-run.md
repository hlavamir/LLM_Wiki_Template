# First run — personal wiki setup

Read this when `personal-template/AGENTS.md` sends you here, and start at once — don't ask the user to restart or to ask again. Work in the NEW, empty folder the user gave you as the working directory — never write into the shared wiki's `personal-template/`. Copy files with copy commands (`cp`, `Copy-Item`), never by re-typing their content.

## How to talk during setup

Same rules as the shared wiki's own setup — the person may be new to all of this:

- **Plain words, short messages.** Never say: lock, scaffold, frontmatter, schema, placeholder, `public:`, `default_public`, session id, `check`. Do the mechanical work silently; don't narrate it or list files.
- **Ask with your question tool when you have one** (Claude Code: `AskUserQuestion`; other agents: their equivalent) — **one question per call, in the order below**, your proposal first and marked "(Recommended)", a one-line plain description per option, the tool's "Other" for typed answers. Free-text questions you can't propose anything for go in a normal message.
- **No question tool:** one question per message, numbered, with lettered options.
- **Propose, don't interrogate:** fill proposals from `git config user.name`, the e-mail address, the OS account; don't re-ask what the user already answered.

## 1. Check the shared wiki — silently

You were handed the path to `<shared>/personal-template/AGENTS.md`; the shared wiki's root `<shared>` is two levels up. Check it's reachable and its `AGENTS.md` says `mode: shared`. If not (drive not mounted, wrong path), stop and tell the user in plain words ("I can't reach the team wiki at <path> — is the drive connected?"). Read its `project`, `link_style` and **About this wiki** line; if they differ from this template's, trust the shared wiki.

## 2. Welcome — one short message, then the first question

Something like:

> Let's set up your personal wiki for **<project>**. It's your own space: you give me chats, documents and notes, and I organize them into linked pages. Pages you choose to share go to the team wiki when you say **push**; everything else stays private. Four quick questions, then I'll copy in what the team already has.

## 3. The questions

*Stored as* is for you — never show it. Project and viewing style come from the team wiki; don't ask them.

1. **"What name should go on your edits?"** — *"Every page keeps a record of who changed it and when, written surname first."* Options: your best `Lastname Firstname` proposal, plus a variant. Ask if the split is unclear. *Stored as* `owner_name` and in every `history` entry.
2. **"What should I call you?"** — Options: the first name, a short form. *Stored as* `owner_nickname`.
3. **"Should new pages be shared with the team by default?"** — Options:
   - **No, private by default (Recommended)** — *"New pages stay with you until you tell me to share them — nothing reaches the team by accident."* → `default_public: false`.
   - **Yes, share by default** — *"New pages go to the team wiki on your next push. You can still keep any single page private."* → `default_public: true`.
4. **"Is your work on a code project on this computer?"** — *"If so, I can look at its code when answering questions. I'll never change it."* Options: **No**, plus up to two plausible project folders you can see. *Stored as* `repo_path` (or `none`).

## 4. Build it — silently

1. **Find Python:** try `python3 --version`, `python --version`, `py --version`; the first reporting Python 3.8+ is `<python>`, else `none`. Only if none works, add to the final message: *"Optional: installing Python 3 lets me do routine housekeeping faster and cheaper. Everything works without it."*
2. **Copy the machinery** into the new folder:
   - `<shared>/personal-template/AGENTS.md` → `AGENTS.md`, `<shared>/personal-template/schema/sync.md` → `schema/sync.md`
   - `<shared>/schema/lock.md`, `lint.md`, `maintain.md` → `schema/`
   - every `.py` file in `<shared>/tools/` → `tools/` (`wiki.py` and the `wiki_*.py` modules it imports)
   - `<shared>/CLAUDE.md` → `CLAUDE.md` (its `@AGENTS.md` line makes Claude Code load the schema)
3. **Lock** the new wiki: generate a session id and run `<python> tools/wiki.py lock acquire --op init --session <id>` (no Python: `schema/lock.md`). Hold it until step 7.
4. **Personalize `AGENTS.md`** with targeted edits: fill `{{FULL_NAME}}`, `{{NICKNAME}}`, `{{DEFAULT_PUBLIC}}`, `{{REPO_PATH_OR_NONE}}` from the answers, `{{PYTHON_COMMAND}}` from step 1, any remaining `{{…}}` from the shared wiki (project, link style, About line), `created`/`modified` = today. Delete the `TEMPLATE FILE` comment and everything from the `template-only` marker comment through its `/template-only` closing comment.
5. **Create:** `wiki-shared-link.md` — frontmatter `type: shared-link` and `shared_wiki_path: <shared>`, plus a line saying the path is specific to this machine; `index.md` (heading + empty `## Parties`, `## Entities`, `## Concepts`); `wiki-maintenance.md` (`## Open tasks`, `## Log`); folders `raw/`, `log/`, `wiki/parties/`, `wiki/entities/`, `wiki/concepts/`, `wiki/summaries/`, `wiki/assets/`.
6. **Pull everything:** run Pull from `schema/sync.md` in full against `<shared>` — every shared page is copied in as shared. Skip nothing (the schema versions already match, so that step is a no-op). If a page needs a decision, ask in plain words.
7. **Log and release:** `<python> tools/wiki.py log init "<project> (bootstrapped from personal-template, pulled <n> pages)"`, run `check` once (anything beyond your own lock: fix it quietly), then `lock release --session <id>`.

## 5. Done — one short, friendly message

No settings table, no file list. Something like:

> Your personal wiki is ready, with the <n> pages the team already had. Some things to try:
> - Tell me something worth keeping, or share a document, and say **ingest** — I'll file it into pages.
> - Ask me anything about the project — I'll answer from the wiki and tell you where each fact came from.
> - Say **sync** now and then: I'll fetch what teammates added, save anything new from our chat, and share your pages with the team. (**pull**, **push** and **fetch news** do the single steps.)
>
> Say **maintain** to tidy up structure, or **lint** to check pages don't contradict each other.
