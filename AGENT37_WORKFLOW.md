# Agent37 Bug-Fix Evidence Workflow

1. Inspect `broken_example.py` and `tests/test_broken_example.py`. Keep the same four tests unchanged between the failing and passing runs.
2. To reproduce the baseline bug, temporarily replace the return line in `broken_example.py` with `return number % 2 == -1`.
3. Capture the failing baseline:

   ```sh
   python3 bugproof.py --project-dir . --output-dir bugproof-before -- python3 -m unittest tests.test_broken_example
   ```

   Confirm the observed nonzero exit code. If it does not fail, investigate; do not claim reproduction.
4. Apply the minimal correction: `return number % 2 != 0`.
5. Run the exact same command from the same project directory, but use a separate output directory:

   ```sh
   python3 bugproof.py --project-dir . --output-dir bugproof-after -- python3 -m unittest tests.test_broken_example
   ```

   Confirm the observed exit code is 0. Leave `broken_example.py` corrected.
6. Compare the saved JSON reports:

   ```sh
   python3 bugproof.py --compare-before bugproof-before/bugproof.json --compare-after bugproof-after/bugproof.json --output-dir bugproof-comparison
   ```

   A `FAIL_TO_PASS` outcome means the same recorded command failed before and passed after. Review the original reports and source change yourself; the summary is not proof that the fix is correct.
7. Inspect both JSON and Markdown outputs. Never manually edit a report to simulate a result. Say **NOT RUN** for tests that were not executed.

BugProof runs commands through the local shell and is not a sandbox. Run only commands you trust. A timeout is recorded as a failure; it is not proof that all child processes were safely terminated.
