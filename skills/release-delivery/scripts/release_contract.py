#!/usr/bin/env python3
"""Resolve and validate project-profile release contracts without deploying."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: python3 -m pip install pyyaml") from exc


HEX_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
RESULT_STATUSES = {"pass", "failed", "rolled_back", "blocked"}
ROLLBACK_STATUSES = {"not_needed", "ready", "executed", "failed"}
SUPPORTED_EVIDENCE = {
    "quality_gate_pass",
    "tested_commit_matches",
    "artifact_ready",
    "backup_ready",
    "rollback_ready",
    "migration_ready",
}


class ContractError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"missing file: {path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ContractError(f"invalid YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"YAML must contain a mapping: {path}")
    return value


def resolve_profile(project: Path, explicit: Path | None) -> Path:
    profile = explicit or project / ".agent/project-profile"
    if not profile.exists():
        raise ContractError(f"project profile is missing: {profile}")
    resolved = profile.resolve()
    if not resolved.is_dir():
        raise ContractError(f"project profile is not a directory: {resolved}")
    return resolved


def load_manifest(project: Path, explicit_profile: Path | None = None) -> tuple[dict[str, Any], Path, Path]:
    profile = resolve_profile(project, explicit_profile)
    manifest_path = profile / "release.yaml"
    manifest = load_yaml(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        raise ContractError("; ".join(errors))
    runbook = profile / str(manifest["runbook"])
    if not runbook.is_file():
        raise ContractError(f"manifest runbook is missing: {runbook}")
    return manifest, manifest_path, runbook


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for key in ("project", "runbook"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} is required")
    environments = data.get("environments")
    if not isinstance(environments, list) or not environments or not all(
        isinstance(item, str) and item.strip() for item in environments
    ):
        errors.append("environments must be a non-empty string list")
    approval = data.get("approval")
    if not isinstance(approval, dict):
        errors.append("approval must be a mapping")
    else:
        for key in ("merge_main", "production", "rollback"):
            if approval.get(key) not in {"human", "preauthorized", "not_required"}:
                errors.append(f"approval.{key} has invalid policy")
    required = data.get("required_evidence")
    if not isinstance(required, list) or not required or not all(
        isinstance(item, str) and item.strip() for item in required
    ):
        errors.append("required_evidence must be a non-empty list")
    elif unknown := sorted(set(required) - SUPPORTED_EVIDENCE):
        errors.append(f"required_evidence contains unsupported values: {unknown}")
    return errors


def validate_qg(path: Path, candidate: str) -> dict[str, Any]:
    data = load_yaml(path)
    if data.get("verdict") != "PASS":
        raise ContractError("Quality Gate verdict must be PASS")
    tested = str(data.get("tested_commit_sha") or "")
    qg_candidate = str(data.get("candidate_commit_sha") or tested)
    if tested != candidate or qg_candidate != candidate:
        raise ContractError(
            f"Quality Gate identity mismatch: tested={tested} candidate={qg_candidate} requested={candidate}"
        )
    return data


def inspect_runbook(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8").lower()
    return {
        "preflight": any(token in text for token in ("前置条件", "preflight", "prerequisite")),
        "deploy": any(token in text for token in ("部署生产", "deploy", "deployment")),
        "verify": any(token in text for token in ("部署后验证", "smoke", "verify", "verification")),
        "rollback": any(token in text for token in ("回滚", "rollback")),
    }


def build_plan(
    *,
    project: Path,
    profile_dir: Path | None,
    action: str,
    environment: str,
    candidate: str,
    artifact: str,
    quality_gate: Path | None,
    approval: str,
    merge_approval: str,
    backup_evidence: str,
    rollback_evidence: str,
    migration_evidence: str,
) -> dict[str, Any]:
    manifest, manifest_path, runbook = load_manifest(project, profile_dir)
    if environment not in manifest["environments"]:
        raise ContractError(
            f"environment {environment!r} is not declared; available={manifest['environments']}"
        )
    if not HEX_RE.fullmatch(candidate):
        raise ContractError("candidate must be a git/object hex identity")
    sections = inspect_runbook(runbook)
    missing_sections = [name for name, present in sections.items() if not present]
    if missing_sections:
        raise ContractError(f"runbook missing required sections: {missing_sections}")
    approval_policy = (
        manifest["approval"]["rollback"]
        if action == "rollback"
        else manifest["approval"].get(environment, "not_required")
    )
    if approval_policy == "human" and not approval.strip():
        raise ContractError(f"{action} to {environment} requires human approval evidence")
    if action == "deploy" and manifest["approval"]["merge_main"] == "human" and not merge_approval.strip():
        raise ContractError("deploy requires main-merge approval evidence")
    evidence = {
        "backup_ready": backup_evidence.strip(),
        "rollback_ready": rollback_evidence.strip(),
        "migration_ready": migration_evidence.strip(),
    }
    if action == "deploy":
        if not artifact.strip():
            raise ContractError("deploy requires artifact tag or digest")
        if quality_gate is None:
            raise ContractError("deploy requires Quality Gate evidence")
        validate_qg(quality_gate, candidate)
        for required in manifest["required_evidence"]:
            if required in evidence and not evidence[required]:
                raise ContractError(f"deploy requires {required} evidence")
    return {
        "schema_version": 1,
        "action": action,
        "project": manifest["project"],
        "environment": environment,
        "candidate_commit_sha": candidate,
        "artifact_digest_or_tag": artifact,
        "manifest": str(manifest_path),
        "runbook": str(runbook),
        "approval_policy": approval_policy,
        "approval_evidence": approval,
        "merge_approval_evidence": merge_approval,
        "quality_gate_evidence": str(quality_gate) if quality_gate else "",
        "readiness_evidence": evidence,
        "runbook_sections": sections,
        "required_evidence": manifest["required_evidence"],
        "execute": False,
    }


def validate_result(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    status = str(data.get("status") or "")
    if status not in RESULT_STATUSES:
        errors.append("status is invalid")
    for key in (
        "environment",
        "candidate_commit_sha",
        "artifact_digest_or_tag",
        "quality_gate_evidence",
        "approval_evidence",
        "runbook",
        "observation_result",
        "next_action",
    ):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} is required")
    if data.get("candidate_commit_sha") and not HEX_RE.fullmatch(str(data["candidate_commit_sha"])):
        errors.append("candidate_commit_sha is invalid")
    for key in ("deploy_steps", "smoke_results", "residual_risks"):
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")
    rollback = str(data.get("rollback_status") or "")
    if rollback not in ROLLBACK_STATUSES:
        errors.append("rollback_status is invalid")
    if status == "pass" and not data.get("smoke_results"):
        errors.append("passing release requires smoke_results")
    if status == "rolled_back" and rollback != "executed":
        errors.append("rolled_back release requires rollback_status: executed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("--project", type=Path, default=Path.cwd())
    inspect_cmd.add_argument("--profile-dir", type=Path)

    plan = sub.add_parser("plan")
    plan.add_argument("--project", type=Path, default=Path.cwd())
    plan.add_argument("--profile-dir", type=Path)
    plan.add_argument("--action", choices=("deploy", "rollback"), required=True)
    plan.add_argument("--environment", required=True)
    plan.add_argument("--candidate", required=True)
    plan.add_argument("--artifact", default="")
    plan.add_argument("--quality-gate", type=Path)
    plan.add_argument("--approval", default="")
    plan.add_argument("--merge-approval", default="")
    plan.add_argument("--backup-evidence", default="")
    plan.add_argument("--rollback-evidence", default="")
    plan.add_argument("--migration-evidence", default="")

    validate = sub.add_parser("validate-result")
    validate.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            manifest, manifest_path, runbook = load_manifest(
                args.project.resolve(), args.profile_dir
            )
            output = {
                "manifest": str(manifest_path),
                "runbook": str(runbook),
                "project": manifest["project"],
                "environments": manifest["environments"],
                "approval": manifest["approval"],
                "runbook_sections": inspect_runbook(runbook),
            }
        elif args.command == "plan":
            output = build_plan(
                project=args.project.resolve(),
                profile_dir=args.profile_dir,
                action=args.action,
                environment=args.environment,
                candidate=args.candidate,
                artifact=args.artifact,
                quality_gate=args.quality_gate,
                approval=args.approval,
                merge_approval=args.merge_approval,
                backup_evidence=args.backup_evidence,
                rollback_evidence=args.rollback_evidence,
                migration_evidence=args.migration_evidence,
            )
        else:
            data = load_yaml(args.result)
            errors = validate_result(data)
            if errors:
                raise ContractError("; ".join(errors))
            output = {"status": "valid", "result": str(args.result)}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except ContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
