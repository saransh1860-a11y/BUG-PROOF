# BugProof

BugProof is a small, standard-library-only Python CLI that runs a local test command and preserves process evidence as JSON and Markdown. It records the command, actual exit code, stdout, stderr, elapsed duration, UTC timestamp, and project directory. It does not infer success from source code or explanations.

## Setup

Requires Python 3.8 or newer. No installation or third-party packages are needed. From this directory, use `python3` (or your platform's Python executable). BugProof invokes the provided command through the local shell, with the selected project directory as its working directory.

## Run

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-evidence -- python3 -m unittest tests.test_regression
```

The command writes `bugproof-evidence/bugproof.json` and `bugproof-evidence/bugproof.md`, and exits with the test command's exit code. The report records the real captured output and uses the observed exit code for PASS/FAIL. Use a trusted command: shell metacharacters are interpreted by the local shell. Avoid output directory overlap with tracked files if you do not want to add generated evidence to version control.

## Demo: reproduce, fix, prove

`tests/test_broken_example.py` contains four regression checks for `broken_example.py`. The checked-in `broken_example.py` is in its corrected state. To reproduce the failing baseline, temporarily replace its return line with `return number % 2 == -1`, then run:

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-before -- python3 -m unittest tests.test_broken_example
```

The baseline should fail the positive-odd and negative-odd checks. The command must produce a nonzero exit code. Then restore the correct implementation, `return number % 2 != 0`, and run the same test command, saving the passing evidence separately:

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-after -- python3 -m unittest tests.test_broken_example
```

Inspect both JSON and Markdown reports. They should show the same command, four tests, and actual nonzero/zero exit codes for the before/after runs. Leave `broken_example.py` in the corrected state. `AGENT37_WORKFLOW.md` describes the red/green sequence and evidence requirements.

## Tests

Run the main green suite:

```sh
python3 -m unittest tests.test_bugproof tests.test_regression -v
```

Run the four-test demonstration suite separately, after ensuring `broken_example.py` is in its corrected state:

```sh
python3 -m unittest tests.test_broken_example -v
```

The demonstration suite is expected to pass in the checked-in state. It should fail only during the documented temporary broken-baseline experiment. All test commands use Python's built-in `unittest` runner.

## Limitations

- Shell command execution is platform-shell dependent; this is not a sandbox. Run only commands you trust.
- Output is captured in memory and written without truncation; very large outputs can consume memory and disk.
- No timeout, process-tree management, environment scrubbing, secret redaction, log rotation, or cryptographic signing is provided.
- Captured output and timestamps are evidence of a local process run, not proof that the test suite is complete or the fix is correct.
- Markdown uses dynamically sized fences to keep output fences from terminating the report early. The JSON record is the source for exact output strings.

## Dependencies

Python standard library only. No paid APIs, external model APIs, databases, authentication, or third-party packages.
