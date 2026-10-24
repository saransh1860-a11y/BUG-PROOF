# BugProof test evidence

- **Status:** FAIL (observed exit code 1)
- **Command:** `python3 -m unittest tests.test_broken_example`
- **Project directory:** `/tmp/bugproof-work/bugproof`
- **Run time (UTC):** 2026-10-24T09:10:37.724016+00:00
- **Duration:** 0.865638 seconds

## Standard output

```text
(empty)
```

## Standard error

```text
..FF
======================================================================
FAIL: test_negative_odd_integer_is_odd (tests.test_broken_example.BrokenExampleRegressionTests.test_negative_odd_integer_is_odd)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/bugproof-work/bugproof/tests/test_broken_example.py", line 8, in test_negative_odd_integer_is_odd
    self.assertTrue(is_odd(-3))
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: False is not true

======================================================================
FAIL: test_positive_odd_integer_is_odd (tests.test_broken_example.BrokenExampleRegressionTests.test_positive_odd_integer_is_odd)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/bugproof-work/bugproof/tests/test_broken_example.py", line 11, in test_positive_odd_integer_is_odd
    self.assertTrue(is_odd(3))
    ~~~~~~~~~~~~~~~^^^^^^^^^^^
AssertionError: False is not true

----------------------------------------------------------------------
Ran 4 tests in 0.001s

FAILED (failures=2)
```
