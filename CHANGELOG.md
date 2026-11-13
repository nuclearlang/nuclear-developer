# Changelog

## Unreleased (2026-11-11)

- The agents read the graph as a library (ADR-0104): the coder and the tester get the card of the kind they write, the
  pitfalls of that kind, solved tasks and an example file of that kind; a repair gets the card of each error code the
  compiler named (prompt `agents/repair.md`); the assistant searches every shelf and answers in the developer's
  language; the diagnoser gets the cards of the codes in a log and the closest known failures. `defs/` regenerated for
  the new client (`search(shelves, platform, kind, type, agents, expand, kinds)`, `card(id)`).
- The coder holds its answer to the task's own words (quoted texts, decorators, calls, status codes; prompt
  `agents/faithful.md`) and, given the project's folder (`root` in a request; the Loop and the chat send it), reads by
  itself the files that declare the names of its task (`nuclear_graph.workspace.Workspace`, read-only).
- The planner reads how people write each kind from the graph ("application component" is `appcomponent`), answers the
  plan also as a tree (parts, tasks, pieces) and says what of the spec is beyond the platform or the local agents
  (`limits`: the capabilities whose trigger words the spec writes, a spec too long, a plan without pieces).
- `eval/run.py chat` asks the assistant the questions of `data/questions.toml` that carry `says`; both quote styles
  score as the same string.
- `eval/run.py distill` builds and ingests the knowledge base (the solved tasks are its rows `solved:`);
  `NUCLEAR_DEVELOPER_URL` chooses the Developer it measures.
- Agents: coder, tester, security reviewer, planner (2026-11-10); documenter (`/developer/document`), assistant
  (`/developer/chat`, the editor's chat), diagnoser (`/developer/diagnose`: kind by rules, evidence by the tools, the
  next step) (2026-11-11).
- Every prompt a model reads is a file of the graph (`prompts/agents/*.md`, `Workbench.prompt`); the agents hold no
  prompt text.
- The agents write only Nuclear: `platform` instead of `dialect`, the graph's `nuclear` collection, a piece's errors by
  line (no scratch-file path), the diagnoser reads failures told in Nuclear.
- The planner builds paths from the platform's `[layout]`, takes kinds and forgotten pieces from the spec's words and
  appends the spec's own sentence to each piece.
- The tester gets only the plan's names (also when it repairs a test file), is told when there is nothing to inject,
  and its search no longer leans on `inject`.
- The assistant reports the size of the prompt it read (`context` in its trace) for the editor's context meter.
- Evaluation: 45 tasks (18 held out), rounds 1–23. Rounds 22 and 23: 43 of 45 against Sonnet's 39, 16 of 18 held
  out against 17; one, then two of the three features by the local agents alone.
- The **analyst** (ADR-0105; `analyst.nuc`, `POST /developer/analyze`, prompt `agents/analyze.md`): before a run generates or
  plans anything it says which kind of request the spec is (a strategy row of the graph), the stages that run, the generator
  calls a request in plain words asks for (each kept only if its dry run accepts it), the pieces the tools already gave (the
  files that declare what changes; every file of a rename, rewritten) and the facts the request lacks. 4 Nuclear tests;
  `eval/run.py analyze` measures its one model call.
- The planner knows the project (`PlanRequest.root`): what the project already declares and the spec only uses is not planned
  again, what the spec introduces with its kind's word is a change of its file, and new pieces go to the component of the
  declarations the spec uses (it had planned an existing entity and its repository again, in a component of its own).
- The set-up of the AI services installs and starts it (ADR-0106): the `nuclear-developer` command starts with the
  models of the machine's profile (`~/.config/nuclearlang/ai.env`) unless its caller gives others. README: the
  profiles and what each was measured to do.
