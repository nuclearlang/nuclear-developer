#!/usr/bin/env python3
"""The local developer's evaluation and training loop (README.md, "Evaluation").

    ../../nuclear-graph/.venv/bin/python run.py reference   # Sonnet answers every task once (paid, cached)
    ../../nuclear-graph/.venv/bin/python run.py distill     # the validated train answers become graph examples
    ../../nuclear-graph/.venv/bin/python run.py local       # the local developer answers every task
    ../../nuclear-graph/.venv/bin/python run.py report      # results/REPORT.md

`[[feature]]` entries are several files: Sonnet writes them all in one answer; the local developer plans them
(`/developer/plan`), writes each piece with the pieces before it as context, and gets one repair pass with the
project's errors. Both are checked as a fresh `dragonfly new` project (`nuclear check .`).

An answer passes when `nuclear check` reports no errors and it contains every `must` text of its task. The local
developer is equivalent to Sonnet on a task when both pass. Only `train` answers reach the graph; `test` tasks are
held out, so the test score measures what the graph teaches, not what it copied.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

import httpx

from nuclear_graph import secrets_store
from nuclear_graph.paths import URL as GRAPH_URL
from nuclear_graph.toolchain import Toolchain, strip_fences

HERE = Path(__file__).parent
RESULTS = HERE / "results"
DEVELOPER = "http://127.0.0.1:7879"
BUDGET_USD = 18.0  # the user approved up to USD 20 for the references
REFERENCE_MODEL = "sonnet"
tools = Toolchain()


# the local agents write Nuclear for a platform; the dialect of a task only builds the reference's check
PLATFORM = {"fastapi": "backend", "nestjs": "backend", "flutter": "mobile", "react": "web"}


def tasks() -> tuple[list[dict], dict[str, str]]:
    data = tomllib.loads((HERE / "tasks.toml").read_text())
    return data["task"], data["context"]


def features() -> list[dict]:
    return tomllib.loads((HERE / "tasks.toml").read_text()).get("feature", [])


def every_task() -> list[dict]:
    return tasks()[0] + features()


FILE_HEADER = re.compile(r"^//\s*file:\s*(\S+\.nuc)\s*$", re.MULTILINE)


def files_of(answer: str) -> dict[str, str]:
    """`// file: <path>` + its code, for every ```nuclear block of an answer."""
    out: dict[str, str] = {}
    for block in re.findall(r"```[a-z]*\n(.*?)```", answer, re.DOTALL):
        m = FILE_HEADER.search(block)
        if m:
            out[m.group(1)] = block[m.end():].strip() + "\n"
    return out


async def check_feature(f: dict, files: dict[str, str]) -> str:
    """The files written into a fresh project of the feature's platform; the project's errors (`ok`)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(["dragonfly", "new", "app", "-p", f["platform"], "-d", f["dialect"]], cwd=tmp, capture_output=True, text=True)
        root = Path(tmp) / "app"
        if not (root / "config.nuc").is_file():
            return f"dragonfly new failed: {out.stdout}{out.stderr}"
        for path, code in files.items():
            target = root / path
            if root.resolve() not in target.resolve().parents:
                return f"{path}: outside the project"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code)
        return (await tools.check_project(str(root))).replace(str(root) + "/", "")


def errors_by_file(check: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in check.splitlines():
        path = line.split(":", 1)[0]
        if path.endswith(".nuc"):
            out[path] = out.get(path, "") + line + "\n"
    return out


def context_of(task: dict, snippets: dict[str, str]) -> str:
    names = [n for n in task.get("context", "").split(",") if n]
    return "\n".join(f"```nuclear\n{snippets[n].strip()}\n```" for n in names)


def score(task: dict, code: str, check: str) -> dict:
    missing = [m for m in task["must"] if m not in code]
    return {"check": check, "missing": missing, "pass": check == "ok" and not missing}


def load(name: str) -> dict:
    f = RESULTS / f"{name}.json"
    return json.loads(f.read_text()) if f.is_file() else {}


def save(name: str, data: dict) -> None:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n")


def claude(prompt: str, system: str) -> tuple[str, float]:
    args = ["claude", "-p", prompt, "--model", REFERENCE_MODEL, "--tools", "", "--output-format", "json",
            "--no-session-persistence", "--system-prompt", system, "--max-budget-usd", "1"]
    out = subprocess.run(args, capture_output=True, text=True, timeout=600)
    data = json.loads(out.stdout)
    return data.get("result", ""), float(data.get("total_cost_usd", 0))


async def reference() -> None:
    """Sonnet with the same guide and the dialect's sheet (no graph examples), plus one repair with the errors."""
    all_tasks, snippets = tasks()
    refs = load("reference")
    spent = sum(r.get("cost", 0) for r in refs.values())
    guide = (Path(__file__).parents[2] / "nuclear-graph/src/nuclear_graph/prompts/piece.md").read_text()
    for t in all_tasks:
        if t["id"] in refs:
            continue
        if spent >= BUDGET_USD:
            print(f"budget reached (USD {spent:.2f}): stopping")
            break
        system = await tools.brief(t["dialect"])
        prompt = f"{guide}\n\n## The files it uses\n\n{context_of(t, snippets)}\n\n## Task\n\nDialect `{t['dialect']}`. File `{t['path']}`. Its kind: `{t['kind']}`.\n\n{t['task']}"
        started = time.time()
        answer, cost = claude(prompt, system)
        code = strip_fences(answer)
        check = await tools.check(code, t["dialect"])
        attempts = 1
        if check != "ok":
            answer, more = claude(f"{prompt}\n\n## Your last answer\n\n```nuclear\n{code}```\n\n## The compiler's errors: fix exactly these\n\n{check}", system)
            cost += more
            code = strip_fences(answer)
            check = await tools.check(code, t["dialect"])
            attempts = 2
        spent += cost
        refs[t["id"]] = {"code": code, "cost": round(cost, 4), "attempts": attempts, "seconds": round(time.time() - started, 1), **score(t, code, check)}
        save("reference", refs)
        print(f"{t['id']:<28} {'PASS' if refs[t['id']]['pass'] else 'fail'}  USD {cost:.3f}  total {spent:.2f}")


async def reference_features() -> None:
    """Sonnet writes every file of a feature in one answer, with one repair given the project's errors."""
    refs = load("reference")
    spent = sum(r.get("cost", 0) for r in refs.values())
    root = Path(__file__).parents[2] / "nuclear-graph/src/nuclear_graph/prompts"
    guide = (root / "plan.md").read_text() + "\n\n" + (root / "piece.md").read_text()
    for f in features():
        if f["id"] in refs or spent >= BUDGET_USD:
            continue
        system = await tools.brief(f["dialect"])
        prompt = (f"{guide}\n\n## Feature\n\nPlatform `{f['platform']}`, dialect `{f['dialect']}`, in a project made by "
                  f"`dragonfly new`. Write every file. Each file is its own ```nuclear block whose first line is "
                  f"`// file: components/<component>/<layer>/<file>.nuc`.\n\n{f['spec']}")
        started = time.time()
        answer, cost = claude(prompt, system)
        files = files_of(answer)
        check = await check_feature(f, files)
        attempts = 1
        if check != "ok":
            shown = "\n\n".join(f"```nuclear\n// file: {p}\n{c}```" for p, c in files.items())
            answer, more = claude(f"{prompt}\n\n## Your last answer\n\n{shown}\n\n## The project's errors: fix exactly these, answer every file again\n\n{check}", system)
            cost += more
            files = files_of(answer) or files
            check = await check_feature(f, files)
            attempts = 2
        spent += cost
        code = "\n".join(f"// file: {p}\n{c}" for p, c in files.items())
        refs[f["id"]] = {"code": code, "files": files, "cost": round(cost, 4), "attempts": attempts, "seconds": round(time.time() - started, 1), **score(f, code, check)}
        save("reference", refs)
        print(f"{f['id']:<28} {'PASS' if refs[f['id']]['pass'] else 'fail'}  USD {cost:.3f}  total {spent:.2f}")


async def distill() -> None:
    """Every validated train answer is an example in the graph: the task, then the code."""
    all_tasks, _ = tasks()
    refs = load("reference")
    headers = {"Authorization": f"Bearer {secrets_store.owner_token()}"}
    n = 0
    async with httpx.AsyncClient(base_url=GRAPH_URL, timeout=120, headers=headers) as http:
        for t in all_tasks + features():
            r = refs.get(t["id"])
            if t["split"] != "train" or not r or not r["pass"]:
                continue
            if "spec" in t:  # a feature: one example per file, as the coder writes them (one piece at a time)
                for path, code in r["files"].items():
                    first = next((ln.split()[0] for ln in code.splitlines() if ln.strip() and not ln.startswith(("//", "@", " "))), "")
                    names = re.findall(r"^(?:[a-z]+\s+)?([A-Z][A-Za-z0-9]*)", code, re.MULTILINE)
                    said = ". ".join(x for x in t["spec"].split(". ") if any(re.search(rf"\b{n}\b", x) for n in names))
                    text = f"[example] {first} — {path}\n\nTask: {said or t['spec']}\n\n```nuclear\n{code.strip()}\n```"
                    meta = {"source": f"eval:{t['id']}", "kind": first, "dialect": t["dialect"], "platform": t["platform"], "validated": "sonnet+nuclear check"}
                    doc = {"collection": "examples", "id": f"eval-{t['id']}-{path.replace('/', '-')}", "text": text, "meta": meta}
                    (await http.post("/v1/documents", json=doc)).raise_for_status()
                    n += 1
                await http.delete(f"/v1/documents/examples/eval-{t['id']}")  # the whole-feature example of before
                continue
            text = f"[example] {t['kind']} — {t['path']}\n\nTask: {t['task']}\n\n```nuclear\n{r['code'].strip()}\n```"
            meta = {"source": f"eval:{t['id']}", "kind": t["kind"], "dialect": t["dialect"], "platform": PLATFORM[t["dialect"]], "validated": "sonnet+nuclear check"}
            (await http.post("/v1/documents", json={"collection": "examples", "id": f"eval-{t['id']}", "text": text, "meta": meta})).raise_for_status()
            n += 1
    print(f"{n} examples in the graph")


async def local(only: str = "") -> None:
    all_tasks, snippets = tasks()
    runs = load("local")
    round_no = max([r.get("round", 0) for r in runs.values()] + [0]) + 1
    async with httpx.AsyncClient(base_url=DEVELOPER, timeout=1800) as http:
        for t in all_tasks:
            if only and t["split"] != only:
                continue
            body = {"task": t["task"], "platform": PLATFORM[t["dialect"]], "path": t["path"], "kind": t["kind"], "context": context_of(t, snippets)}
            started = time.time()
            r = (await http.post("/developer/code", json=body)).json()
            runs[t["id"]] = {"round": round_no, "code": r["code"], "attempts": r["attempts"], "seconds": round(time.time() - started, 1),
                             "trace": r["trace"], **score(t, r["code"], r["check"])}
            save("local", runs)
            print(f"{t['id']:<28} {'PASS' if runs[t['id']]['pass'] else 'fail'}  {runs[t['id']]['seconds']:>5}s  {r['attempts']} attempt(s)  {runs[t['id']]['missing'] or ''}")


async def local_features(only: str = "") -> None:
    """Plan → one piece at a time (the pieces before it as context) → the project's errors → one repair per file."""
    runs = load("local")
    round_no = max([r.get("round", 0) for r in runs.values()] + [0])
    round_no = round_no if any(r.get("round") == round_no for r in runs.values()) else round_no + 1
    async with httpx.AsyncClient(base_url=DEVELOPER, timeout=3600) as http:
        for f in features():
            if only and f["split"] != only:
                continue
            started = time.time()
            plan = (await http.post("/developer/plan", json={"spec": f["spec"], "platform": f["platform"]})).json()
            files: dict[str, str] = {}
            attempts = 0
            for piece in plan["pieces"]:
                context = "\n".join(f"```nuclear\n// file: {p}\n{c}```" for p, c in files.items())
                # the piece as the Loop sends it: the planner's task already ends with the spec's sentences about it
                body = {"task": piece["task"], "platform": f["platform"], "path": piece["path"], "kind": piece["kind"], "context": context}
                r = (await http.post("/developer/code", json=body)).json()
                files[piece["path"]] = r["code"]
                attempts += r["attempts"]
            check = await check_feature(f, files)
            if check != "ok":  # pieces that compile alone but not together: one local repair pass
                for path, errs in errors_by_file(check).items():
                    if path not in files:
                        continue
                    others = "\n".join(f"```nuclear\n// file: {p}\n{c}```" for p, c in files.items() if p != path)
                    body = {"task": f"Fix this file of the feature. Its code:\n\n```nuclear\n{files[path]}```\n\nThe project's errors in it: fix exactly these and answer the whole file\n\n{errs}",
                            "platform": f["platform"], "path": path, "kind": "", "context": others}
                    r = (await http.post("/developer/code", json=body)).json()
                    files[path] = r["code"]
                    attempts += r["attempts"]
                check = await check_feature(f, files)
            code = "\n".join(f"// file: {p}\n{c}" for p, c in files.items())
            runs[f["id"]] = {"round": round_no, "code": code, "files": files, "plan": plan["pieces"], "attempts": attempts,
                             "seconds": round(time.time() - started, 1), "trace": plan["trace"], **score(f, code, check)}
            save("local", runs)
            print(f"{f['id']:<28} {'PASS' if runs[f['id']]['pass'] else 'fail'}  {runs[f['id']]['seconds']:>5}s  {len(files)} files  {runs[f['id']]['missing'] or ''}  {'' if check == 'ok' else check.splitlines()[0]}")


def rescore() -> None:
    """Every stored answer scored again with the current `must` of its task (a criterion fixed after a run)."""
    by_id = {t["id"]: t for t in every_task()}
    for name in ("reference", "local"):
        data = load(name)
        for k, v in data.items():
            if k in by_id:
                v.update(score(by_id[k], v["code"], v["check"]))
        if data:
            save(name, data)


def summary() -> dict:
    all_tasks = every_task()
    refs, runs = load("reference"), load("local")
    out = {}
    for split in ("train", "test", "all"):
        ts = [t for t in all_tasks if split in ("all", t["split"])]
        ref = sum(1 for t in ts if refs.get(t["id"], {}).get("pass"))
        loc = sum(1 for t in ts if runs.get(t["id"], {}).get("pass"))
        both = sum(1 for t in ts if refs.get(t["id"], {}).get("pass") and runs.get(t["id"], {}).get("pass"))
        out[split] = {"tasks": len(ts), "sonnet": ref, "local": loc, "equivalent": both}
    out["cost_usd"] = round(sum(r.get("cost", 0) for r in refs.values()), 2)
    out["local_seconds"] = round(sum(r.get("seconds", 0) for r in runs.values()), 1)
    return out


def report() -> None:
    all_tasks = every_task()
    refs, runs = load("reference"), load("local")
    s = summary()
    lines = ["# Nuclear Developer — evaluation", "",
             f"Local model: qwen2.5-coder:3b (coder) + the Nuclear Smart Graph. Reference: Claude {REFERENCE_MODEL}. "
             f"References cost USD {s['cost_usd']}; the local run took {s['local_seconds']} s on CPU.", "",
             "| split | tasks | Sonnet passes | local passes | equivalent (both pass) |", "|---|---|---|---|---|"]
    for split in ("train", "test", "all"):
        x = s[split]
        lines.append(f"| {split} | {x['tasks']} | {x['sonnet']} | {x['local']} | {x['equivalent']} |")
    hist = load("history")
    if hist:
        lines += ["", "## Rounds (test split: local passes / Sonnet passes)", ""]
        lines += [f"- round {k}: {v['test']['local']} / {v['test']['sonnet']} (all: {v['all']['local']} / {v['all']['sonnet']})" for k, v in hist.items()]
    lines += ["", "## Tasks", "", "| task | split | Sonnet | local | local attempts | what the local answer missed |", "|---|---|---|---|---|---|"]
    for t in all_tasks:
        r, l = refs.get(t["id"], {}), runs.get(t["id"], {})
        miss = "; ".join(l.get("missing", [])) or ("" if l.get("check") in (None, "ok") else l["check"].split("\n")[0])
        lines.append(f"| {t['id']} | {t['split']} | {'✓' if r.get('pass') else '✗'} | {'✓' if l.get('pass') else '✗'} | {l.get('attempts', '')} | {miss.replace('|', '/')[:120]} |")
    (RESULTS / "REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "reference":
        asyncio.run(reference())
        asyncio.run(reference_features())
    elif cmd == "distill":
        asyncio.run(distill())
    elif cmd == "local":
        asyncio.run(local(sys.argv[2] if len(sys.argv) > 2 else ""))
        asyncio.run(local_features(sys.argv[2] if len(sys.argv) > 2 else ""))
        runs = load("local")
        history = load("history")
        history[str(max(r.get("round", 0) for r in runs.values()))] = summary()
        save("history", history)
    rescore()
    report()
