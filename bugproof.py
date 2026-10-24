#!/usr/bin/env python3
"""Capture verifiable evidence from a local test command."""

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def run_test(command, project_dir):
    """Run command in project_dir and capture its real process result."""
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=project_dir,
        shell=True,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    duration = time.monotonic() - started
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_seconds": round(duration, 6),
        "ran_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(Path(project_dir).resolve()),
    }


def _fence(content):
    """Choose a Markdown fence longer than any backtick run in content."""
    longest = max((len(run) for run in re.findall(r"`+", content)), default=0)
    return "`" * max(3, longest + 1)


def write_evidence(record, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bugproof.json"
    markdown_path = output_dir / "bugproof.md"
    json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    status = "PASS" if record["exit_code"] == 0 else "FAIL"
    stdout_fence = _fence(record["stdout"])
    stderr_fence = _fence(record["stderr"])
    command_fence = "`" if "`" not in record["command"] else "~"
    project_fence = "`" if "`" not in record["project_dir"] else "~"
    stdout_text = record["stdout"] if record["stdout"] else "(empty)\n"
    stderr_text = record["stderr"] if record["stderr"] else "(empty)\n"
    if stdout_text and not stdout_text.endswith("\n"):
        stdout_text += "\n"
    if stderr_text and not stderr_text.endswith("\n"):
        stderr_text += "\n"
    markdown = (
        "# BugProof test evidence\n\n"
        f"- **Status:** {status} (observed exit code {record['exit_code']})\n"
        f"- **Command:** {command_fence}{record['command']}{command_fence}\n"
        f"- **Project directory:** {project_fence}{record['project_dir']}{project_fence}\n"
        f"- **Run time (UTC):** {record['ran_at_utc']}\n"
        f"- **Duration:** {record['duration_seconds']:.6f} seconds\n\n"
        "## Standard output\n\n"
        f"{stdout_fence}text\n{stdout_text}{stdout_fence}\n\n"
        "## Standard error\n\n"
        f"{stderr_fence}text\n{stderr_text}{stderr_fence}\n"
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a local test command and save its actual output as evidence.")
    parser.add_argument("--project-dir", default=".", help="Working directory for the test command (default: current directory)")
    parser.add_argument("--output-dir", default="bugproof-evidence", help="Directory for bugproof.json and bugproof.md")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Test command, optionally after --")
    args = parser.parse_args(argv)
    command = args.command[0] if len(args.command) == 1 else " ".join(args.command)
    if command.startswith("-- "):
        command = command[3:]
    if not command:
        parser.error("provide a test command, for example: python3 -m unittest discover -s tests")
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        parser.error(f"project directory does not exist: {project_dir}")
    record = run_test(command, project_dir)
    json_path, markdown_path = write_evidence(record, args.output_dir)
    print(f"Command: {record['command']}")
    print(f"Exit code: {record['exit_code']}")
    print(f"Duration: {record['duration_seconds']:.6f}s")
    print(f"JSON evidence: {json_path.resolve()}")
    print(f"Markdown report: {markdown_path.resolve()}")
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
