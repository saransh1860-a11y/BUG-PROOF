#!/usr/bin/env python3
"""Capture local test-command evidence and compare two saved runs."""

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def _decode_output(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_test(command, project_dir, timeout=120):
    """Run a trusted local command and record its actual result.

    A timed-out command is recorded with exit code 124 and timed_out=True.
    Commands run through the platform shell for compatibility with the CLI.
    """
    started = time.monotonic()
    ran_at_utc = datetime.now(timezone.utc).isoformat()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=project_dir,
            shell=True,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=timeout,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = _decode_output(exc.stdout)
        stderr = _decode_output(exc.stderr)
        timeout_note = "\nBugProof: command exceeded timeout of {} seconds.\n".format(timeout)
        stderr = (stderr or "") + timeout_note
    duration = time.monotonic() - started
    return {
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "duration_seconds": round(duration, 6),
        "ran_at_utc": ran_at_utc,
        "project_dir": str(Path(project_dir).resolve()),
        "timeout_seconds": timeout,
        "timed_out": timed_out,
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
    status = "PASS" if record["exit_code"] == 0 and not record.get("timed_out", False) else "FAIL"
    stdout_fence = _fence(record["stdout"])
    stderr_fence = _fence(record["stderr"])
    command_fence = "`" if "`" not in record["command"] else "~"
    project_fence = "`" if "`" not in record["project_dir"] else "~"
    stdout_text = record["stdout"] if record["stdout"] else "(empty)\n"
    stderr_text = record["stderr"] if record["stderr"] else "(empty)\n"
    if not stdout_text.endswith("\n"):
        stdout_text += "\n"
    if not stderr_text.endswith("\n"):
        stderr_text += "\n"
    markdown = (
        "# BugProof test evidence\n\n"
        f"- **Status:** {status} (observed exit code {record['exit_code']})\n"
        f"- **Timed out:** {'yes' if record.get('timed_out', False) else 'no'}\n"
        f"- **Command:** {command_fence}{record['command']}{command_fence}\n"
        f"- **Project directory:** {project_fence}{record['project_dir']}{project_fence}\n"
        f"- **Run time (UTC):** {record['ran_at_utc']}\n"
        f"- **Duration:** {record['duration_seconds']:.6f} seconds\n"
        f"- **Timeout limit:** {record.get('timeout_seconds', 'not recorded')} seconds\n\n"
        "## Standard output\n\n"
        f"{stdout_fence}text\n{stdout_text}{stdout_fence}\n\n"
        "## Standard error\n\n"
        f"{stderr_fence}text\n{stderr_text}{stderr_fence}\n"
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path


def compare_evidence(before_path, after_path, output_dir):
    """Compare saved run records without changing either source report."""
    before_path = Path(before_path)
    after_path = Path(after_path)
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))
    required = ("command", "exit_code", "stdout", "stderr", "duration_seconds")
    for label, record in (("before", before), ("after", after)):
        missing = [key for key in required if key not in record]
        if missing:
            raise ValueError("{} report is missing required fields: {}".format(label, ", ".join(missing)))

    same_command = before["command"] == after["command"]
    before_pass = before["exit_code"] == 0 and not before.get("timed_out", False)
    after_pass = after["exit_code"] == 0 and not after.get("timed_out", False)
    if not same_command:
        outcome = "INCOMPARABLE"
        interpretation = "Commands differ; do not interpret this as a valid before/after regression comparison."
    elif not before_pass and after_pass:
        outcome = "FAIL_TO_PASS"
        interpretation = "The recorded command failed before and passed after. Review outputs to confirm the fix is meaningful."
    elif before_pass and not after_pass:
        outcome = "PASS_TO_FAIL"
        interpretation = "The recorded command passed before and failed after; this may indicate a regression."
    elif before_pass and after_pass:
        outcome = "PASS_TO_PASS"
        interpretation = "Both runs passed. These records alone do not prove a bug was fixed."
    else:
        outcome = "FAIL_TO_FAIL"
        interpretation = "Both runs failed. The change has not demonstrated a passing result."
    result = {
        "before_report": str(before_path),
        "after_report": str(after_path),
        "command_matches": same_command,
        "outcome": outcome,
        "interpretation": interpretation,
        "before": {
            "exit_code": before["exit_code"],
            "status": "PASS" if before_pass else "FAIL",
            "duration_seconds": before["duration_seconds"],
        },
        "after": {
            "exit_code": after["exit_code"],
            "status": "PASS" if after_pass else "FAIL",
            "duration_seconds": after["duration_seconds"],
        },
        "stdout_changed": before["stdout"] != after["stdout"],
        "stderr_changed": before["stderr"] != after["stderr"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": "Comparison summarizes recorded process results; it does not validate test quality, source changes, or report authenticity.",
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "bugproof-comparison.json"
    markdown_path = output_dir / "bugproof-comparison.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = (
        "# BugProof before/after comparison\n\n"
        f"- **Outcome:** {outcome}\n"
        f"- **Same command:** {'yes' if same_command else 'no'}\n"
        f"- **Before:** {result['before']['status']} (exit {result['before']['exit_code']}; {result['before']['duration_seconds']:.6f}s)\n"
        f"- **After:** {result['after']['status']} (exit {result['after']['exit_code']}; {result['after']['duration_seconds']:.6f}s)\n"
        f"- **Standard output changed:** {'yes' if result['stdout_changed'] else 'no'}\n"
        f"- **Standard error changed:** {'yes' if result['stderr_changed'] else 'no'}\n\n"
        f"**Interpretation:** {interpretation}\n\n"
        f"> Limitation: {result['limitations']}\n"
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return result, json_path, markdown_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Capture local test evidence or compare two saved runs.")
    parser.add_argument("--project-dir", default=".", help="Working directory for the test command")
    parser.add_argument("--output-dir", default="bugproof-evidence", help="Directory for report files")
    parser.add_argument("--timeout", type=float, default=120, help="Maximum command duration in seconds (default: 120)")
    parser.add_argument("--compare-before", help="Path to a saved before-run bugproof.json")
    parser.add_argument("--compare-after", help="Path to a saved after-run bugproof.json")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Trusted local test command, optionally after --")
    args = parser.parse_args(argv)

    if args.compare_before or args.compare_after:
        if not (args.compare_before and args.compare_after):
            parser.error("--compare-before and --compare-after must be provided together")
        if args.command:
            parser.error("do not provide a test command in comparison mode")
        try:
            result, json_path, markdown_path = compare_evidence(
                args.compare_before, args.compare_after, args.output_dir
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            parser.error("could not compare reports: {}".format(exc))
        print("Comparison: {}".format(result["outcome"]))
        print("JSON comparison: {}".format(json_path.resolve()))
        print("Markdown comparison: {}".format(markdown_path.resolve()))
        return 0 if result["outcome"] == "FAIL_TO_PASS" else 1

    command = args.command[0] if len(args.command) == 1 else " ".join(args.command)
    if command.startswith("-- "):
        command = command[3:]
    if not command:
        parser.error("provide a test command, or use --compare-before and --compare-after")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        parser.error("project directory does not exist: {}".format(project_dir))
    record = run_test(command, project_dir, timeout=args.timeout)
    json_path, markdown_path = write_evidence(record, args.output_dir)
    print("Command: {}".format(record["command"]))
    print("Exit code: {}".format(record["exit_code"]))
    print("Timed out: {}".format(record["timed_out"]))
    print("Duration: {:.6f}s".format(record["duration_seconds"]))
    print("JSON evidence: {}".format(json_path.resolve()))
    print("Markdown report: {}".format(markdown_path.resolve()))
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
