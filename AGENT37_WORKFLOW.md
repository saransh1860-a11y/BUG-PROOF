# Agent37 Bug-Fix Evidence Workflow

1. Inspect `example.py` and `tests/test_regression.py`; this is the same regression test used for both baseline and corrected runs.
2. To reproduce the known negative-odd bug, temporarily replace the return line in `example.py` with `return number % 2 == -1`. Do not change the test.
3. Run and capture the failing baseline from the project root:

   ```sh
   python3 bugproof.py --project-dir . --output-dir bugproof-before -- python3 -m unittest tests.test_regression
   ```

   Verify actual exit code 1 and failure for `is_odd(-3)`. If it does not fail, investigate; do not report reproduction.
4. Apply the smallest correction: `return number % 2 != 0`.
5. Rerun the exact same test command from the same directory and capture separately:

   ```sh
   python3 bugproof.py --project-dir . --output-dir bugproof-after -- python3 -m unittest tests.test_regression
   ```

   Verify actual exit code 0. Leave `example.py` corrected after the demonstration.
6. Inspect both JSON and Markdown reports. Report the actual command, exit codes, outputs and durations, distinguishing the red baseline from the passing corrected run. Keep only evidence generated from these actual runs of the final test workflow.
7. Clearly say **NOT RUN** for tests not executed. Explanations or model expectations are not test evidence. Never claim execution or success unless the actual process result supports it.

For a real bug in another project, use that project's same unchanged regression test for the failing baseline and passing corrected run. Never label a test PASS based only on reasoning.
