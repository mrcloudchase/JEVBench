"""The pipeline from the command line. Run from the project root.

    python -m tdm build <task>                     # stage 1: tasks/<task>/build.py -> manifest.jsonl, data.jsonl
    python -m tdm run <experiment> [--model M] [--task T] [--date YYYY-MM-DD]
    python -m tdm score <experiment>               # no API calls
    python -m tdm report <experiment>              # no API calls
"""

import argparse
import runpy
import sys

from .project import Project
from .report import report_experiment
from .run import execute, load_env
from .score import score_experiment


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tdm", description="Evaluate typed decision models' beliefs.")
    sub = parser.add_subparsers(dest="stage", required=True)
    sub.add_parser("build", help="build a task from its source").add_argument("task")
    run = sub.add_parser("run", help="run an experiment's models on its tasks")
    run.add_argument("experiment")
    run.add_argument("--model", action="append", help="only these models")
    run.add_argument("--task", action="append", help="only these tasks")
    run.add_argument("--date", help="the run date in its id (default: today)")
    sub.add_parser("score", help="score an experiment's latest runs").add_argument("experiment")
    sub.add_parser("report", help="write an experiment's tables").add_argument("experiment")
    args = parser.parse_args(argv)
    project = Project()

    if args.stage == "build":
        build = project.root / "tasks" / args.task / "build.py"
        if not build.exists():
            sys.exit(f"no build script tasks/{args.task}/build.py")
        runpy.run_path(str(build), run_name="__main__")
    elif args.stage == "run":
        load_env(project.root / ".env")
        exp = project.experiment(args.experiment)
        stale = [t for t in args.task or exp["tasks"] if project.task_version(exp, t) != project.task(t).version]
        if stale:
            sys.exit(f"{args.experiment} pins earlier versions of {', '.join(stale)}: it can be scored, not run")
        for task in args.task or exp["tasks"]:
            for model in args.model or exp["models"]:
                r = execute(project, task, model, args.date).meta
                print(f"{r['id']}: {r['status']}, {r.get('rows', 0)}/{r.get('expected_rows', '?')} rows, "
                      f"served {', '.join(r.get('served', []))}, ${r.get('cost_usd', 0):.4f}", file=sys.stderr, flush=True)
    elif args.stage == "score":
        score_experiment(project, args.experiment)
    elif args.stage == "report":
        print(report_experiment(project, args.experiment))


if __name__ == "__main__":
    main()
