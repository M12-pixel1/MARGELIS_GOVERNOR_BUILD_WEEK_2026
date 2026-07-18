"""Fail-fast repository checks used before the human submission gate."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_WEEK_START = datetime.fromisoformat("2026-07-13T09:00:00-07:00")
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".deps",
    ".demo-data",
    ".pytest_cache",
    "__pycache__",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def verify_commit_dates() -> list[str]:
    result = subprocess.run(
        ["git", "log", "--format=%aI%x09%cI%x09%H"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    errors: list[str] = []
    for line in result.stdout.splitlines():
        author_raw, commit_raw, commit_hash = line.split("\t")
        author_time = datetime.fromisoformat(author_raw)
        commit_time = datetime.fromisoformat(commit_raw)
        if author_time < BUILD_WEEK_START or commit_time < BUILD_WEEK_START:
            errors.append(f"commit outside Build Week window: {commit_hash}")
    if not result.stdout.strip():
        errors.append("repository has no commits")
    return errors


def verify_content(paths: list[Path]) -> list[str]:
    forbidden_claims = [
        "world" + "-first",
        "ai act " + "compliant",
        "ai act " + "certified",
        "fully " + "autonomous",
        "guaran" + "teed",
        "zero " + "hallucination",
    ]
    secret_prefix = "s" + "k-"
    private_marker = "BEGIN " + "PRIVATE KEY"
    errors: list[str] = []
    for path in paths:
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.casefold()
        if path.name != "verify_repo.py":
            if secret_prefix in text:
                errors.append(f"possible API secret in {path.relative_to(ROOT)}")
            if private_marker in text:
                errors.append(f"private key material in {path.relative_to(ROOT)}")
        if path.suffix in {".md", ".html", ".js"}:
            for claim in forbidden_claims:
                if claim in lowered:
                    errors.append(f"forbidden product claim in {path.relative_to(ROOT)}")
        if re.search(r"[\w.+-]+@(?![\w.-]+\.(?:example|test)\b)[\w.-]+\.[A-Za-z]{2,}", text):
            if path.name not in {"README.md", "BUILD_WEEK_SUBMISSION.md"}:
                errors.append(f"non-synthetic email-like value in {path.relative_to(ROOT)}")
    return errors


def main() -> None:
    errors = verify_commit_dates() + verify_content(tracked_files())
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        raise SystemExit(1)
    print("PASS: commit dates, claims, secret markers, and synthetic-data checks")


if __name__ == "__main__":
    main()
