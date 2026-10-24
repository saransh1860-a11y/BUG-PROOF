import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from bugproof import compare_evidence, main, run_test, write_evidence


class BugProofEvidenceTests(unittest.TestCase):
    def test_captures_real_process_output_status_and_duration(self):
        record = run_test("printf 'out'; printf 'err' >&2; exit 7", ".", timeout=5)
        self.assertEqual(record["exit_code"], 7)
        self.assertEqual(record["stdout"], "out")
        self.assertEqual(record["stderr"], "err")
        self.assertGreaterEqual(record["duration_seconds"], 0)
        self.assertFalse(record["timed_out"])
        self.assertTrue(record["ran_at_utc"])

    def test_timeout_is_recorded_as_failure_and_does_not_hang(self):
        record = run_test("sleep 2", ".", timeout=0.1)
        self.assertEqual(record["exit_code"], 124)
        self.assertTrue(record["timed_out"])
        self.assertIn("exceeded timeout", record["stderr"])

    def test_writes_json_and_markdown_with_truthful_status(self):
        record = run_test("printf 'observed'; exit 3", ".", timeout=5)
        with tempfile.TemporaryDirectory() as directory:
            json_path, markdown_path = write_evidence(record, directory)
            parsed = json.loads(Path(json_path).read_text(encoding="utf-8"))
            report = Path(markdown_path).read_text(encoding="utf-8")
        self.assertEqual(parsed, record)
        self.assertIn("FAIL (observed exit code 3)", report)
        self.assertIn("observed", report)
        self.assertIn("Timed out:** no", report)

    def test_run_test_preserves_command_string_with_spaces_and_quotes(self):
        command = "python3 -c \"print('two words')\""
        record = run_test(command, ".", timeout=5)
        self.assertEqual(record["command"], command)
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["stdout"], "two words\n")

    def test_cli_preserves_quoted_argument_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = main(["--project-dir", directory, "--output-dir", str(out_dir), "--", "python3 -c \"print('one two')\""])
            saved = json.loads((out_dir / "bugproof.json").read_text(encoding="utf-8"))
            report = (out_dir / "bugproof.md").read_text(encoding="utf-8")
        self.assertEqual(status, 0)
        self.assertEqual(saved["command"], "python3 -c \"print('one two')\"")
        self.assertEqual(saved["stdout"], "one two\n")
        self.assertIn("one two", report)

    def test_empty_stdout_and_stderr_have_closing_fences_on_new_lines(self):
        record = run_test("true", ".", timeout=5)
        with tempfile.TemporaryDirectory() as directory:
            _, markdown_path = write_evidence(record, directory)
            report = Path(markdown_path).read_text(encoding="utf-8")
        self.assertIn("```text\n(empty)\n```\n\n## Standard error\n\n```text\n(empty)\n```\n", report)

    def test_markdown_fences_do_not_swallow_captured_output(self):
        record = run_test("printf '```'", ".", timeout=5)
        with tempfile.TemporaryDirectory() as directory:
            _, markdown_path = write_evidence(record, directory)
            report = Path(markdown_path).read_text(encoding="utf-8")
        self.assertEqual(record["stdout"], "```")
        self.assertIn("````text\n```\n````", report)

    def test_comparison_detects_fail_to_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = {"command": "python -m unittest", "exit_code": 1, "stdout": "", "stderr": "FAIL", "duration_seconds": 1, "timed_out": False}
            after = {"command": "python -m unittest", "exit_code": 0, "stdout": "OK", "stderr": "", "duration_seconds": 0.5, "timed_out": False}
            before_path = root / "before.json"
            after_path = root / "after.json"
            before_path.write_text(json.dumps(before), encoding="utf-8")
            after_path.write_text(json.dumps(after), encoding="utf-8")
            result, json_path, md_path = compare_evidence(before_path, after_path, root / "comparison")
            self.assertEqual(result["outcome"], "FAIL_TO_PASS")
            self.assertTrue(Path(json_path).is_file())
            self.assertTrue(Path(md_path).is_file())

    def test_comparison_refuses_to_claim_improvement_when_commands_differ(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"exit_code": 1, "stdout": "", "stderr": "", "duration_seconds": 1}
            (root / "before.json").write_text(json.dumps(dict(base, command="test A")), encoding="utf-8")
            (root / "after.json").write_text(json.dumps(dict(base, command="test B")), encoding="utf-8")
            result, _, _ = compare_evidence(root / "before.json", root / "after.json", root / "out")
            self.assertEqual(result["outcome"], "INCOMPARABLE")

    def test_comparison_rejects_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "before.json").write_text(json.dumps({"command": "test"}), encoding="utf-8")
            (root / "after.json").write_text(json.dumps({"command": "test"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required fields"):
                compare_evidence(root / "before.json", root / "after.json", root / "out")

    def test_cli_rejects_incomplete_comparison_arguments(self):
        with self.assertRaises(SystemExit):
            main(["--compare-before", "before.json"])


if __name__ == "__main__":
    unittest.main()
