from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys
from pathlib import Path

from hermes_ops.commands.doctor import run_doctor
from hermes_ops.commands.preflight import run_preflight
from hermes_ops.commands.worktree import run_worktree
from hermes_ops.core.results import Report
from hermes_ops.core.presentation import PublicSanitizer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermes-ops",
        description="Read-only operational checks for local projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "worktree", "preflight"):
        command = subparsers.add_parser(name)
        command.add_argument("--project", required=True, help="Project path to inspect")
        command.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            help="Output format (default: text)",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        public_root: str | Path = (
            Path(args.project).expanduser().resolve(strict=False)
        )
    except (OSError, RuntimeError):
        public_root = args.project
    sanitizer = PublicSanitizer.for_project(public_root)
    try:
        report = _dispatch(args.command, args.project)
    except Exception as exc:  # final boundary: expected callers get no traceback
        report = Report.from_results(
            args.command,
            [],
            forced_exit_code=4,
        )
        if args.format == "json":
            payload = report.to_dict()
            payload["error"] = {
                "code": "external_failure",
                "message": sanitizer.sanitize_text(str(exc)),
            }
            import json

            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        else:
            print(
                f"ERRO external_failure: {sanitizer.sanitize_text(str(exc))}",
                file=sys.stderr,
            )
            print("exit_code=4", file=sys.stderr)
        return 4

    print(
        report.to_json(sanitizer)
        if args.format == "json"
        else report.to_text(sanitizer)
    )
    return report.exit_code


def _dispatch(command: str, project: str) -> Report:
    if command == "doctor":
        return run_doctor(project)
    if command == "worktree":
        return run_worktree(project)
    if command == "preflight":
        return run_preflight(project)
    raise ValueError(f"Unknown command: {command}")
