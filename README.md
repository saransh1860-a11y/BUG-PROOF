# BugProof

BugProof is a small, standard-library-only Python CLI that runs a local test command and preserves process evidence as JSON and Markdown. It records the command, actual exit code, stdout, stderr, elapsed duration, UTC timestamp, and project directory. It does not infer success from source code or explanations.

## Setup

Requires Python 3.8 or newer. No installation or third-party packages are needed. From this directory, use `python3` (or your platform's Python executable). BugProof invokes the provided command through the local shell, with the selected project directory as its working directory.

## Run

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-evidence -- python3 -m unittest discover -s tests
```

The command writes `bugproof-evidence/bugproof.json` and `bugproof-evidence/bugproof.md`, and exits with the test command's exit code. The report records the real captured output and uses the observed exit code for PASS/FAIL. Use a trusted command: shell metacharacters are interpreted by the local shell. Avoid output directory overlap with tracked files if you do not want to add generated evidence to version control.

## Demo: reproduce, fix, prove

`tests/test_regression.py` is the same regression suite in both stages. To capture the red baseline, temporarily replace the return line in `example.py` with `return number % 2 == -1`, then run:

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-before -- python3 -m unittest tests.test_regression
```

Confirm the negative-odd and positive-odd checks fail. Then make the minimal correction, `return number % 2 != 0`, and rerun the same regression suite, saving the passing evidence separately:

```sh
python3 bugproof.py --project-dir . --output-dir bugproof-after -- python3 -m unittest tests.test_regression
```

Inspect both JSON and Markdown reports. The before and after records must show actual nonzero and zero exit codes, respectively. Keep `example.py` in the corrected state. `AGENT37_WORKFLOW.md` describes this red/green sequence and evidence requirements.

## Tests

```sh
python3 -m unittest tests.test_bugproof tests.test_regression -v
```

The green suite covers fixed regression behavior and BugProof's process evidence, command handling, and report generation. `tests.test_broken_example` is an intentionally failing demonstration test; run it separately as shown above, not as part of the green suite. All test commands use Python's built-in `unittest` runner.

## Limitations

- Shell command execution is platform-shell dependent; this is not a sandbox. Run only commands you trust.
- Output is captured in memory and written without truncation; very large outputs can consume memory and disk.
- No timeout, process-tree management, environment scrubbing, secret redaction, log rotation, or cryptographic signing is provided.
- Captured output and timestamps are evidence of a local process run, not proof that the test suite is complete or the fix is correct.
- Markdown uses dynamically sized fences to keep output fences from terminating the report early. The JSON record is the source for exact output strings.

## Dependencies

Python standard library only. No paid APIs, external model APIs, databases, authentication, or third-party packages.
