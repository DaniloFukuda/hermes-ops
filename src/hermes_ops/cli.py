from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys
from pathlib import Path

from hermes_ops.commands.doctor import run_doctor
from hermes_ops.commands.preflight import run_preflight
from hermes_ops.commands.worktree import run_worktree
from hermes_ops.commands.evidence import evidence_analysis_json, evidence_analysis_text, run_evidence_analysis
from hermes_ops.commands.skill import (
    run_skill_command,
    skill_result_json,
    skill_result_text,
)
from hermes_ops.core.errors import (
    SkillCatalogError,
    SkillContractError,
    SkillExecutionError,
    SkillPolicyError,
    SkillRegistryError,
    AnalysisError,
)
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
    skill = subparsers.add_parser("skill")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    skill_run = skill_commands.add_parser("run")
    skill_run.add_argument("skill_id")
    skill_run.add_argument("--project", required=True, help="Target project path to inspect")
    skill_run.add_argument("--mission", help="Directed audit mission (mission-audit only)")
    skill_run.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    evidence = subparsers.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_analyze = evidence_commands.add_parser("analyze")
    evidence_analyze.add_argument("--evidence-pack", required=True)
    evidence_analyze.add_argument("--question", required=True)
    evidence_analyze.add_argument("--context-budget-chars", required=True, type=int)
    evidence_analyze.add_argument("--dry-run", action="store_true")
    evidence_analyze.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        public_root: str | Path = (
            Path(getattr(args, "project", "")).expanduser().resolve(strict=False)
        )
    except (OSError, RuntimeError):
        public_root = getattr(args, "project", None)
    sanitizer = PublicSanitizer.for_project(public_root)
    if args.command == "skill":
        return _run_skill_cli(args, sanitizer)
    if args.command == "evidence":
        return _run_evidence_cli(args, sanitizer)
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


def _run_skill_cli(args: argparse.Namespace, sanitizer: PublicSanitizer) -> int:
    try:
        result = run_skill_command(args.project, args.skill_id, args.mission)
    except (
        SkillCatalogError,
        SkillContractError,
        SkillRegistryError,
        SkillPolicyError,
        SkillExecutionError,
    ) as exc:
        exit_code = 2 if getattr(exc, "code", "") in {"SKILL_EXECUTION_INVALID", "MISSION_TERM_LIMIT_EXCEEDED"} else 3
        payload = {
            "skill_id": args.skill_id,
            "exit_code": exit_code,
            "error": {
                "code": getattr(exc, "code", type(exc).__name__),
                "message": sanitizer.sanitize_text(str(exc)),
            },
        }
        if args.format == "json":
            import json

            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        else:
            print(f"ERRO {payload['error']['code']}: {payload['error']['message']}", file=sys.stderr)
            print(f"exit_code={exit_code}", file=sys.stderr)
        return exit_code
    except Exception as exc:
        payload = {
            "skill_id": args.skill_id,
            "exit_code": 4,
            "error": {
                "code": "external_failure",
                "message": sanitizer.sanitize_text(str(exc)),
            },
        }
        if args.format == "json":
            import json

            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        else:
            print(f"ERRO external_failure: {payload['error']['message']}", file=sys.stderr)
            print("exit_code=4", file=sys.stderr)
        return 4
    print(
        skill_result_json(result, sanitizer)
        if args.format == "json"
        else skill_result_text(result, sanitizer)
    )
    return result.exit_code


def _run_evidence_cli(args: argparse.Namespace, sanitizer: PublicSanitizer) -> int:
    try:
        payload = run_evidence_analysis(args.evidence_pack, args.question, args.context_budget_chars, dry_run=args.dry_run)
    except AnalysisError as exc:
        exit_code = 2 if exc.code in {"ANALYSIS_PACK_INVALID","ANALYSIS_PACK_TOO_LARGE","ANALYSIS_PATH_FORBIDDEN","ANALYSIS_QUESTION_INVALID","ANALYSIS_BUDGET_INVALID"} else 3
        error={"exit_code":exit_code,"error":{"code":exc.code,"message":sanitizer.sanitize_text(str(exc))}}
        if args.format=="json":
            import json
            print(json.dumps(error,ensure_ascii=False,sort_keys=True,separators=(",",":")))
        else:
            print(f"ERRO {exc.code}: {error['error']['message']}",file=sys.stderr); print(f"exit_code={exit_code}",file=sys.stderr)
        return exit_code
    except Exception as exc:
        message=sanitizer.sanitize_text(str(exc)); print(f"ERRO external_failure: {message}",file=sys.stderr); print("exit_code=4",file=sys.stderr); return 4
    print(evidence_analysis_json(payload,sanitizer) if args.format=="json" else evidence_analysis_text(payload,sanitizer))
    return 0
