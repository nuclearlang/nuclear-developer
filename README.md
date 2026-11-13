# Nuclear Developer

Local AI agents for [NuclearLang](https://github.com/nuclearlang/nuclear) and Dragonfly, on models of at most 3B
parameters, as the junior developer of a frontier model: **coder**, **tester**, **security reviewer**, **planner**,
**analyst**, **documenter**, **diagnoser** and **assistant**.
What a small model cannot hold in its head comes from the [Nuclear Smart Graph](https://github.com/nuclearlang/nuclear-graph)
(the ecosystem's private knowledge base); what it writes is checked by the Nuclear compiler before it answers.

It is itself a Dragonfly backend written in Nuclear (platform `backend`, dialect `fastapi`): FastAPI + LangGraph,
generated from the `.nuc` files of this repository. Decision record:
[ADR-0102](https://github.com/nuclearlang/nuclear/blob/main/docs/adr/0102-ai-loop.md).

## How an agent works

A small model follows fixed steps better than it chooses tools, so each agent is a LangGraph graph with fixed steps:

```
recall ──► write ──► nuclear check ──ok──► answer
  │          ▲            │
  │          └── repair ◄─┘ errors (at most 3 attempts), each with the card of its code
  └─ from the Smart Graph, for the kind it is about to write: the kind's own card, the mistakes
     small models repeat with that kind, the closest rules, solved tasks and an example file
```

Three more things happen by rule, never by the model's choice:

- **It reads the project by itself.** A request may carry `root` (the project's folder): the coder then gets, as its
  context, the files that declare the names its task writes (`Workspace.context`, read-only, never outside the
  project), besides what the caller pasted. An order can be short: the path, the kind, every name.
- **Its answer is held to the order's own words.** When the answer compiles, the quoted texts, the decorators with
  their arguments, the calls (`books.byAuthor(name)`) and the status codes the task writes must be in it; what is
  missing is asked for once more, without the examples (`agents/faithful.md`), and the first answer is kept when
  the second is not better. (In round 19 it fired four times and changed no answer; it exists for the short orders
  of a lead, where a renamed call breaks the next piece.)
- **The plan says what is beyond the agents.** `POST /developer/plan` answers the pieces, the same plan as a tree
  (`tree`: the big parts, one per component; the tasks of each, a layer; the pieces of each task, a file) and
  `limits`: the rows of the graph's capabilities whose trigger words the spec writes ("authentication" on the
  backend, "form" on the web), a spec longer than a local model reads at once, a plan without pieces or with too
  many. How people write a kind ("application component", "use case") comes from the graph's cards of the kinds.
- **The plan knows the project.** With the project's folder (`root`), a declaration the project already has and the
  spec only uses (`repository: BookRepository`) is not planned again; one the spec introduces with its kind's word ("a
  repository BookRepository with...") is planned as a change of its file; and new pieces go to the component of the
  declarations the spec uses, whatever component the model names.

The whole toolbox of an agent is one row of the graph, `service:agent-toolbox`: the graph, the compiler, the
`dragonfly` commands, the project's files and the internet.

What an agent reads is not a search over documents: the graph is a library of cards (ADR-0104). The coder asks for
`kind:<platform>.<kind>` by its id, for the pitfalls whose `kinds` list has that kind, for solved tasks and an example
file of that kind; a repair asks for `error:<code>` of each code the compiler named; the assistant searches every
shelf with the question and gets each card with the rows it links to; the diagnoser gets the cards of the codes in a
log and the closest known failures.

| Agent | Model | Route | Does | Does not |
|---|---|---|---|---|
| Coder | `qwen2.5-coder:3b` | `POST /developer/code` | writes ONE `.nuc` file from a precise task, repairs it with the compiler | choose names, data or architecture |
| Tester | `qwen2.5-coder:3b` | `POST /developer/test` | writes the Nuclear tests (`tests` kind) of a piece of code | delete a failing test |
| Security | `gemma4:e2b` | `POST /developer/security` | reviews code against the platform's security rules + the compiler | change the code |
| Documenter | `gemma4:e2b` | `POST /developer/document` | reads a run's journal and writes what was done: what it built, how it checked it, what is left (only facts of the journal) | change the code |
| Assistant | `gemma4:e2b` | `POST /developer/chat` | answers a message of the editor's chat about the project, from the project's map, the session's last messages and the graph | change a file (an order is a Loop run) |
| Diagnoser | `gemma4:e2b` | `POST /developer/diagnose` | when a pipeline stage fails: the kind of failure by fixed rules (transient, environment, code, test, spec), the evidence from the tools (`nuclear check`, `dragonfly doctor`) and the next step in plain words | change anything |
| Planner | `gemma4:e2b` | `POST /developer/plan` | splits a spec into pieces of one file, in order; each path comes from the platform's layout (`nuclear help layout`), each kind and forgotten piece from the spec's own words | choose a folder, or plan what the spec does not name |

Chat: `{message, platform, map, history, root}` → the same answer (`report`). Request (`code`, `test`, `security`,
`document`: the journal in `context`): `{task, platform = "backend", path, kind, context, root}`; answer: `{code, report,
check, attempts, trace: [{step, detail}]}`. Plan: `{spec, platform, root}` → `{pieces: [{path, kind, task}], raw, trace, tree,
limits}`.
Analysis (`POST /developer/analyze`, before a run generates or plans anything; ADR-0105): `{spec, platform, root,
strategy}` → `{strategy, title, why, mode, stages, lead, source, generate, pieces, questions, limits, report, trace}`:
which kind of request the spec is (a strategy row of the graph, chosen by the request's exact signs, then its meaning,
and by which of its names the project has), the stages that run, the generator calls a request in plain words asks
for (the one thing a model is asked: each line it answers is kept only if `dragonfly gen ... --dry-run` accepts it),
the pieces the tools already gave (the files that declare what changes; every file of a rename, rewritten) and the
facts the request lacks, as questions.
Each request runs on a thread of its own. **The agents write only Nuclear**: they name a platform (`backend`, `mobile`,
`web`), never a dialect, read only the graph's rows for agents (`agents`: no target-language code) and check with
`nuclear check --platform` (ADR-0102 §11).

The sources: `components/developer/ai/` (`workbench.nuc` — what every agent shares —, `coder.nuc`, `tester.nuc`,
`security.nuc`, `documenter.nuc`, `assistant.nuc`, `diagnoser.nuc`, `planner.nuc`, `analyst.nuc`, `states/piece_state.nuc`), `components/developer/domain/models/`,
`components/developer/api/developer_controller.nuc`, `config/project_config.nuc` (the two Ollama models),
`config.nuc` (`dependencies(nuclear_graph = "../nuclear-graph")`), `defs/` (the type definitions of
`nuclear_graph.client`, `nuclear_graph.toolchain` and `nuclear_graph.workspace`, generated with `tools/defs/python/gen.py`).

**The prompts are files**, never strings in the code: every prompt a model reads is
`nuclear-graph/src/nuclear_graph/prompts/agents/<step>.md` (`{{name}}` filled by `Workbench.prompt`, an empty `## `
section dropped; the list is that folder's README), over the use-case guides `prompts/<use case>.md`.

## Run it

The set-up of the AI services installs it, with the Smart Graph and the models that fit the machine, and starts it at
every login ([Set up the AI services](https://github.com/nuclearlang/nuclear/blob/main/docs/ai/setup.md)):

```sh
nuclear-loop setup            # or the installer's last step, or VS Code: Nuclear: Set Up the AI Services
nuclear-loop setup --status   # what is installed and running
```

By hand, in this folder (what the set-up does):

```sh
ollama pull qwen2.5-coder:3b && ollama pull gemma4:e2b
nuclear-graph serve &                                   # the Smart Graph (see its README)
nuclear-graph connect nuclear-developer --scopes read,write
dragonfly install                                       # build/ from the .nuc files, and its environment
cd build && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 7879
```

### The models: a profile for the machine

| Profile | Models | Downloads | Memory | Measured with the Developer's evaluation |
|---|---|---|---|---|
| `lite` | `qwen2.5-coder:1.5b` | 1.6 GB | 8 GB (4 GB at least) | not measured yet |
| `medium` | `qwen2.5-coder:3b` | 2.5 GB | 12 GB (8 GB at least) | as coder, the model of hard: 43 of 45 single-file tasks, 16 of 18 never seen; as assistant, 6 of the first 8 chat questions (hard: 10 of 10) |
| `hard` | `qwen2.5-coder:3b` + `gemma4:e2b` | 9.7 GB | 24 GB (16 GB at least) | 43 of 45 single-file tasks (Claude Sonnet: 39), 16 of 18 never seen, 2 of 3 whole features, 10 of 10 chat questions, 10 of 11 analyses |
| `remote` | none | nothing but the MCP server (33 MB) | any | nothing runs on the machine |

Every local profile also downloads `embeddinggemma` (0.6 GB, counted above), which makes the graph's vectors. No model is larger than 3B parameters of effective size.

The set-up suggests the heaviest profile that runs well with the machine's memory; the choice is the user's, and a
profile's models are the defaults of `CODER_MODEL` and `ASSISTANT_MODEL` on that machine. How each was measured:
`eval/run.py chat`, `analyze` and `local` against a Developer started with those models. `lite`, and `medium` as
assistant beyond 8 chat questions, are not measured yet.

```sh
curl -s -X POST 127.0.0.1:7879/developer/code -H 'content-type: application/json' \
  -d '{"task": "A model NewTask with a title (string, at least 3 characters) and a priority (int, default 2).",
       "path": "components/tasks/domain/models/task_models.nuc", "kind": "model"}'
```

Models: `CODER_MODEL`, `ASSISTANT_MODEL`, `OLLAMA_URL`. The set-up writes the ones of the chosen profile in
`~/.config/nuclearlang/ai.env`, and the `nuclear-developer` command starts with them unless its caller gives others
(the editor's *Settings and integrations* page does, with the models chosen there). Each model runs with a context window of `CONTEXT_TOKENS` (8192 by default; the editor
passes its `nuclear.ai.contextTokens`).

## What it knows

The knowledge base of the whole project is [`data/`](data/README.md): its own repository (`nuclear-knowledge`), rows
on nine shelves: what NuclearLang is for, how each thing is written, every kind and decorator, every tool (the four
CLIs, the MCP tools, the generators), every diagnostic and failure with its fix, what can and cannot be done, how
each task is done step by step, and validated code. Most rows are generated from the working tree; the rest are
written by hand and reviewed when their sources change. The Smart Graph ingests it; the agents read every row but
the ones about the target languages and the dialects underneath (`agents: false`). After a change:
`nuclear-graph knowledge build`, `knowledge check`, then `nuclear-graph ingest`; `nuclear-graph knowledge ask` asks
the graph the questions people ask.

## Where it works

| Who calls it | How | What the Developer does |
|---|---|---|
| The **Loop** (VS Code `Ctrl+Alt+P`, Android Studio *Nuclear Loop*, `nuclear-loop run`) | spec → plan → tests first → code → verification → security → artifacts → deploy | the planner splits the spec, the tester writes the tests first (and fixes a test file the project rejects), the coder writes each piece and repairs it with the compiler and with failing tests told in Nuclear (`dragonfly explain`), the security reviewer reads each new file; when a stage fails the **diagnoser** says why; at the end the **documenter** writes the journal's summary |
| The **chat** (VS Code `Ctrl+Alt+A`, *Nuclear agent*) | a question, or `/task <order>` | the **assistant** answers from the project's map and the graph; an order is a Loop run with the local agents only |
| A **frontier model** over MCP (Claude Code, Codex, Cursor: `nuclear-graph mcp`) | `developer_task` first, then validate, correct, `developer_review`; `developer_retry` after a failure | the whole task by the local agents (`nuclear-loop run --lead local`), documented in the run's journal; the lead's corrected files become graph examples |

**Every run is documented.** `.nuclear/loop/runs/<id>.md` (beside the `.json` with every log whole): the documenter's
summary (what it built, how it checked it, what is left), why it failed (the diagnoser), the files written, what is
left for the reviewer, and each step with its agent, its trace and what it read; a frontier model's review is
`<id>.review.md`.

**When something fails.** A call to the Developer that fails for a passing reason (down, busy, 408/425/429/5xx) is
retried by its caller with exponential backoff and full jitter (5 tries, 1–30 s by default; `Retry-After` wins); a
compiler error or a failing test is never retried blindly — it goes to the repair rounds, then to the diagnoser (kind by
rules: transient, environment, code, test, spec; evidence from `nuclear check` or `dragonfly doctor`; the next step).
A failed run goes on from the step that failed (*↻ Retry*, `nuclear-loop retry <run>`, `developer_retry`): every step
that passed is kept, the earlier attempt stays in the run file.

**When the editor closes in the middle.** A run keeps a trace log (`.nuclear/loop/runs/<id>.log`), a heartbeat and a
ledger of the files it writes; an orphaned run is recovered (its unfinished step's files undone) and goes on from that
step. A call to the Developer nothing works on (the Developer silent, Ollama holding no model) is cut and retried, and
every run first checks that the Developer, the graph, Ollama and the models it needs answer.

**What the agents may read.** Only Nuclear and the platform (`backend`, `mobile`, `web`): a row the agents read
has no target-language code (the build of the knowledge base refuses one that has), a failing test reaches them told in `.nuc` terms, a piece's errors are given by
line, and the diagnoser's prompt forbids speaking of the generated code.

## Evaluation: how it was trained

There is no dedicated GPU here, so the agents are not trained by changing weights: they are trained by **retrieval
and distillation**, measured by `eval/run.py` over the tasks of `eval/tasks.toml`, each with acceptance texts (`must`): 42 tasks of one
file (every backend kind, and the mobile and web platforms) and 3 **features** (`[[feature]]`) of 4–6 files that the
planner splits, the coder writes piece by piece and the compiler checks together as a fresh `dragonfly new` project:

1. `reference` — Claude Sonnet answers every task once, with the same guide and the dialect's sheet, and one repair
   with the compiler's errors (USD 0.89 for the 45). A feature is one answer with every file.
2. `distill` — the Sonnet answers of the `train` tasks that pass become examples in the graph's `examples`
   collection (a feature as one example per file). The 18 `test` tasks are held out: their answers never reach the
   graph.
3. `local` — the local coder answers every task through the Developer; an answer passes when `nuclear check` reports
   no errors and it has every acceptance text. The local developer is **equivalent** to Sonnet on a task when both pass.
4. A failure is studied and fixed with a **general rule or more knowledge** in the graph (never the answer), then a
   new round.

| Round | What changed | Local / Sonnet (all 32) | Local / Sonnet (12 held out) |
|---|---|---|---|
| 1 | the ingested knowledge only (Sonnet's references were still running: its numbers here are partial) | 23 / — | 9 / — |
| 2 | + 15 distilled Sonnet examples | 26 / 25 | 8 / 10 |
| 3 | + 7 rules in the coder's guide (decorators above their field, `gte(...)` in queries, graph nodes, `replaceAll`...); two acceptance texts that were wrong for both models fixed | **28 / 26** | **10 / 11** |

From round 4 the bank has 45 tasks (18 held out):

| Round | What changed | Local / Sonnet (all 45) | Local / Sonnet (18 held out) |
|---|---|---|---|
| 4 | + 10 mobile and web tasks, 3 features; the web platform's brief (Sonnet 0/4 → 4/4 on web); `dragonfly new`'s mobile skeleton fixed; N0116 through runtime classes, N0013 for a dangling decorator | 38 / 39 | 14 / 17 |
| 5–7 | the planner: paths from the platform's `[layout]`, kinds and forgotten pieces from the spec's words, the spec's sentence in each task; the coder's rule "only what the task declares" | 38 / 39 | 14 / 17 |
| 8–9 | a feature distilled as one example per file (a whole-feature example made the coder write every file into each piece) | 37 / 39 | 14 / 17 |
| 10–11 | the agents write only Nuclear (`platform`, the graph's `nuclear` collection, the platform sheets); each piece's task is the spec's own sentence; few-shots (aliases, columns, `replaceAll`, state models, a test file); the entity by folder accepted | 37 / 39, first feature passed | 13 / 17 |
| 12 | void: an `ingest` run from the wrong folder had emptied the graph (fixed: an ingest removes only its own roots' sources) | (29 / 39) | (8 / 17) |
| 13 | every prompt moved to a file (`prompts/agents/*.md`, the same text) on the re-ingested graph | **38 / 39** | **15 / 17** |
| 14 | void: `/tmp` filled up during the run | — | — |
| 15 | the tester: only the plan's names, nothing to inject for models, a search without `inject`; errors by line | **38 / 39**, 1 of 3 features | **15 / 17** |
| 16 | void: stopped at 10 minutes while another agent held Ollama | — | — |
| 17 | the words of the kinds in Nuclear only (`[underneath]` for the framework), the compiler gaps fixed | 37 / 39, 1 of 3 features | 14 / 17 (`entity-reader`: the decorator written after its field, not repaired) |
| 18 | the graph as a library (ADR-0104): the coder reads the card of its kind, the pitfalls of that kind and examples; a repair reads the card of each error code; both quote styles score as the same string | 39 / 39, 1 of 3 features | 16 / 17 |
| 19 | the planner reads how people write a kind from the graph ("application component"); the coder holds its answer to the task's words | **40 / 39**, 2 of 3 features | **16 / 17** |
| 20–21 | measured and discarded: the coder's guide without its general rules and shapes (only the kind's own rules, from the graph): it gained the state model and a graph and lost `replaceAll`, a renamed method and a service's shape | 39 / 39, 1 of 3 features | 14 / 17 |
| 22 | the general rules stay in the guide and every rule of the kind comes from the graph (the two closest whole, the rest in a line); examples of the same kind only; the answer held also to the signatures the task writes | **43 / 39**: every task of one file passes (42 of 42), 1 of 3 features | **16 / 17** |
| 23 | the answer held also to the signatures without parameters (`all()`) | **43 / 39**, 2 of 3 features | 16 / 17 |

On single files the local 3B coder passes every task of the bank in round 22 and all but one in round 23 (42 and
41 of 42; Sonnet 36). On features of
several files written by the local agents alone it passes one or two of the three, depending on the round, where
Sonnet passes all three: a piece renames a method the spec writes, or two pieces declare the same thing. That is why
a feature goes through the generators first and, when it has a design of its own, under a lead.
Measured and discarded: giving the coder the file `dragonfly make` writes (29 of 42 against 37). Each local answer takes 1.5–10 s on the CPU, a feature 1–1.5 min. The full table,
task by task, is `eval/results/REPORT.md`.

```sh
cd eval
../../nuclear-graph/.venv/bin/python run.py reference   # paid: Claude, cached in results/reference.json
../../nuclear-graph/.venv/bin/python run.py distill
../../nuclear-graph/.venv/bin/python run.py local        # the Developer must be running
../../nuclear-graph/.venv/bin/python run.py report
```

**The analyst** (ADR-0105) is measured apart: `run.py analyze` gives eleven requests, as a user writes them in English
and Spanish, to `/developer/analyze` in a fresh project (`[[analysis]]` in `tasks.toml`) and checks the strategy each
gets, the `dragonfly gen` call a request in plain words becomes, the pieces the tools give, the questions it asks and
the stages that run. First measure: **10 of 11**, 4 of the 5 that ask the model (the one that fails drops a field
twice, and then asks the user for the fields instead of generating). Which strategy a request gets asks no model: it
is tested with the knowledge base (`nuclear-graph knowledge ask`: 62 requests, all to their strategy).

## Known limits

The agents know their own limits: they are rows of the graph (`limit:agent-one-file`, `limit:agent-context`,
`limit:agent-reasoning`, `limit:agent-features`, `limit:agent-nuclear-only`, `limit:agent-internet`) with the
procedure to follow when a task is beyond them (`playbook:escalate`).

- The 3B tester copies a solved example of the graph when it is close to the task (a spec that declares only a model
  got a test of an application component from the examples): the run now fails at *Tests first* with the diagnosis
  instead of passing without tests; Claude-led runs fix it.
- The planner maps a kind only from its own word ("application component" is not `appcomponent`) and names a
  component after the first model of a plain spec (`newbooks`).
- A value that comes from a library method has no known type: declare it (`card: string = ~knowledge.card(...)`)
  before using a member of the standard library on it.

## Development

```sh
nuclear check . && nuclear build .
cd build && ../../tools/python/.venv/bin/pyright --pythonpath .venv/bin/python app   # 0 errors (strict)
```

Never edit `build/`: change the `.nuc` files.

## License

Apache-2.0.
