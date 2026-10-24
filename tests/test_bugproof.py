import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from bugproof import main, run_test, write_evidence


class BugProofEvidenceTests(unittest.TestCase):
    def test_captures_real_process_output_status_and_duration(self):
        record = run_test("printf 'out'; printf 'err' >&2; exit 7", ".")
        self.assertEqual(record["command"], "printf 'out'; printf 'err' >&2; exit 7")
        self.assertEqual(record["exit_code"], 7)
        self.assertEqual(record["stdout"], "out")
        self.assertEqual(record["stderr"], "err")
        self.assertGreaterEqual(record["duration_seconds"], 0)
        self.assertTrue(record["ran_at_utc"])

    def test_writes_json_and_markdown_with_truthful_status(self):
        record = run_test("printf 'observed'; exit 3", ".")
        with tempfile.TemporaryDirectory() as directory:
            json_path, markdown_path = write_evidence(record, directory)
            parsed = json.loads(Path(json_path).read_text(encoding="utf-8"))
            report = Path(markdown_path).read_text(encoding="utf-8")
        self.assertEqual(parsed, record)
        self.assertIn("FAIL (observed exit code 3)", report)
        self.assertIn("observed", report)

    def test_run_test_preserves_command_string_with_spaces_and_quotes(self):
        command = "python3 -c \"print('two words')\""
        record = run_test(command, ".")
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
        self.assertIn('python3 -c "print(\'one two\')"', report)

    def test_empty_stdout_and_stderr_have_closing_fences_on_new_lines(self):
        record = run_test("true", ".")
        with tempfile.TemporaryDirectory() as directory:
            _, markdown_path = write_evidence(record, directory)
            report = Path(markdown_path).read_text(encoding="utf-8")
        self.assertEqual(record["stdout"], "")
        self.assertEqual(record["stderr"], "")
        self.assertIn("```text\n(empty)\n```\n\n## Standard error\n\n```text\n(empty)\n```\n", report)

    def test_markdown_fences_do_not_swallow_captured_output(self):
        record = run_test("printf '```'", ".")
        with tempfile.TemporaryDirectory() as directory:
            _, markdown_path = write_evidence(record, directory)
            report = Path(markdown_path).read_text(encoding="utf-8")
        self.assertEqual(record["stdout"], "```")
        self.assertIn("````text\n```\n````", report)
        self.assertTrue(report.rstrip().endswith("```"))
        self.assertIn("\n```\n", report)


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
