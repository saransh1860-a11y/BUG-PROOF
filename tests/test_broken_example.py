import unittest

from broken_example import is_odd


class BrokenExampleRegressionTests(unittest.TestCase):
    def test_negative_odd_integer_is_odd(self):
        self.assertTrue(is_odd(-3))

    def test_positive_odd_integer_is_odd(self):
        self.assertTrue(is_odd(3))

    def test_negative_even_integer_is_not_odd(self):
        self.assertFalse(is_odd(-4))

    def test_even_integer_is_not_odd(self):
        self.assertFalse(is_odd(4))


if __name__ == "__main__":
    unittest.main()
