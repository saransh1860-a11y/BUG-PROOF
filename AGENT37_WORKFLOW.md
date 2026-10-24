# Agent37 Bug-Fix Evidence Workflow

1. Inspect `broken_example.py` and `tests/test_broken_example.py`. The four tests remain unchanged between the failing and passing runs.
2. To reproduce the baseline bug, temporarily replace the return line in `broken_example.py` with `return number % 2 == -1`.
3. Run and capture the failing baseline from the project root:

   ```sh
   python3 bugproof.py --project-dir . --output-dir bugproof-before -- python3 -m unittest tests.test_broken_example
   ```

   Verify the observed nonzero exit code and failures for odd inputs. If it does not fail, investigate; do not report reproduction.
4. Apply the minimal correction: `return number % 2 != 0`.
5. Rerun the exact same test command from the same directory and capture separately:

   ```sh
   python3 bugproof.py --project-dir . --output-dir bugproof-after -- python3 -m unittest tests.test_broken_example
   ```

   Verify the observed exit code is 0. Leave `broken_example.py` corrected after the demonstration.
6. Inspect both JSON and Markdown reports. Confirm that they reflect actual commands, test counts, exit codes, outputs and durations. Distinguish the failing baseline from the passing corrected run. Never manually edit a report to simulate a result.
7. Clearly say **NOT RUN** for tests not executed. Explanations or model expectations are not test evidence. Never claim execution or success unless the actual process result supports it.

For a real bug in another project, use that project's same unchanged regression test for the failing baseline and passing corrected run. Never label a test PASS based only on reasoning.
