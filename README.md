# BugProof

BugProof is a standard-library-only Python CLI that runs a trusted local test command and preserves the process result as JSON and Markdown. It records the command, observed exit code, stdout/stderr, elapsed duration, UTC timestamp, project directory, and timeout status.

Its differentiator is a small **before/after evidence comparison**: compare two saved runs of the same command and get a cautious summary of whether the result changed from fail to pass, pass to fail, or stayed the same.

## Requirements

Python 3.8 or newer. No installation, third-party packages, databases, or API keys are needed.

## Capture a test run

From the project root:

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-evidence -- python3 -m unittest tests.test_regression
```

BugProof writes `bugproof.json` and `bugproof.md` in the output directory and returns the test command's exit code. The default timeout is 120 seconds. Change it with `--timeout 30`, for example.

The command is executed through the platform shell to support ordinary shell command syntax. **Only run commands you trust.** BugProof is not a sandbox. A timeout is recorded as a failure with exit code 124 and `timed_out: true`.

## Compare two saved runs

Capture the failing baseline and corrected run into separate directories. Then compare their JSON reports:

```sh
python3 bugproof.py \
  --compare-before bugproof-before/bugproof.json \
  --compare-after bugproof-after/bugproof.json \
  --output-dir bugproof-comparison
```

The comparison produces `bugproof-comparison.json` and `bugproof-comparison.md`. It classifies the outcome as:

- `FAIL_TO_PASS`: same command failed before and passed after.
- `PASS_TO_FAIL`: same command passed before and failed after.
- `PASS_TO_PASS`: both runs passed.
- `FAIL_TO_FAIL`: both runs failed.
- `INCOMPARABLE`: the commands differ, so BugProof refuses to claim a valid before/after improvement.

The comparison command exits 0 only for `FAIL_TO_PASS`; other outcomes return 1 so they can be noticed in scripts. Read the interpretation and outputs before drawing conclusions.

**Important:** This compares saved process records; it does not prove the reports are authentic, that the same source revision was used, or that the tests are complete and meaningful. Keep the reports from actual runs and do not edit them to simulate results.

## Reproduce the demo

`tests/test_broken_example.py` has four regression checks for `broken_example.py`. The checked-in implementation is corrected. To reproduce a failing baseline, temporarily change the return line to:

```python
return number % 2 == -1
```

Run the same command for both baseline and corrected states, using different output directories:

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-before -- python3 -m unittest tests.test_broken_example
```

Restore the correct implementation:

```python
return number % 2 != 0
```

Then rerun the exact command with `--output-dir bugproof-after` and compare the two JSON reports using the command above. Leave `broken_example.py` corrected. If the expected baseline does not fail, stop and investigate rather than claiming a reproduced bug.

## Run tests

```sh
python3 -m unittest tests.test_bugproof tests.test_regression tests.test_broken_example -v
```

GitHub Actions runs compilation and all three test modules on pushes and pull requests.

## Limitations and safety

- Shell execution is platform-dependent and is not sandboxed.
- Timeout handling bounds the command's wait, but this is not a secure process-isolation mechanism.
- Captured output is held in memory and written without truncation; very large output may consume memory or disk.
- Environment scrubbing, secret redaction, log rotation, cryptographic signing, and source revision verification are not implemented.
- Exit codes and output are evidence of a process run, not proof that the test suite is complete or the fix is correct.
- The comparison does not parse framework-specific test counts or independently verify source changes.

## Dependencies

Python standard library only.
