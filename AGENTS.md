# AGENTS.md — nuclear-developer

Nuclear Developer: local agents (coder, tester, security reviewer, planner, analyst, documenter, diagnoser, assistant) on
models of at most 3B parameters, fed by the Nuclear Smart Graph (a library of cards: ADR-0104). A Dragonfly backend
written in NuclearLang (`.nuc`), dialect `fastapi`. Read README.md first; the decision is ADR-0102 of the `nuclear`
repository; the working tree's rules are `../AGENTS.md`, its state `../STATUS.md`.

<!-- nuclearlang -->
## NuclearLang

This project is written in NuclearLang (`.nuc`), dialect `fastapi`. Its syntax is not TypeScript, Dart nor Python.

- Before writing code, read the sheet: `nuclear spec --brief --dialect fastapi`.
- After each change: `nuclear check . --json` must report no errors; fix exactly what each error says (most carry a `fix`).
- Look up instead of guessing: an API `nuclear defs show <Name> --dialect fastapi`; a kind or decorator
  `nuclear help <word> --dialect fastapi` (all: `nuclear help words --dialect fastapi`); a topic `nuclear help <topic>`.
- Never edit generated code (`build/` and the `.ts`/`.dart`/`.py` built from the `.nuc`): change the `.nuc` files.
<!-- /nuclearlang -->

- A change to an agent or to a prompt of the graph is measured: run `eval/run.py local` and keep the report.
- The models stay at 3B parameters or less (the user's rule).
- What an agent knows is a row of the knowledge base (`data/assets/`), never a text inside the code or a prompt: a new
  rule, pitfall, limit or procedure is a row there (`nuclear-graph knowledge build`, `check`, `ingest`).
