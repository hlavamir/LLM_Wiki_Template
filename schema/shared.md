# Shared-wiki notes

Read before handling pages that arrived from contributors, onboarding someone, or changing the schema.

- **Two halves.** This shared wiki sits on synced storage; each person keeps a personal wiki on their own machine, bootstrapped from `personal-template/` (steps for a new person: `personal-template/README.md`). Personal pages carry a boolean `public:`; only `public: true` pages ever reach this wiki.
- **How pages get here.** Not a file copy: a contributor's Push (in their personal `schema/sync.md`) compares their public pages with this wiki's by relative path, creates missing ones verbatim, and reconciles differing ones — newer wins, or it asks the human. A page that looks synthesized from several people: check `synthesized_from:` before assuming single authorship.
- **Contributors write this wiki's `index.md` and `log/`.** Each Push adds an index line per created page and a `push` log entry, under this wiki's `wiki.lock`. Push entries you didn't write yourself are expected.
- **Personal wikis copy their machinery from here.** At first run and whenever Pull sees a newer `schema_version` in `personal-template/AGENTS.md`, a personal wiki copies `schema/lock.md`, `schema/lint.md`, `schema/maintain.md` and `tools/wiki.py` from this wiki's root and `schema/sync.md` from `personal-template/schema/`, then rebuilds its own `AGENTS.md` core from `personal-template/AGENTS.md` (asking its owner first). So: to roll out a change, edit these files here **and bump `personal-template/AGENTS.md`'s `schema_version`** — an unchanged version means personal wikis skip the check entirely.
- **Keep `AGENTS.md` and `personal-template/AGENTS.md` structurally parallel** — same rules, conventions and operations; when one evolves, update the other.
- **This wiki's own schema** has no automatic update: diff it against the upstream template repo now and then and pull improvements in deliberately.
