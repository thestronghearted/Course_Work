import unittest

from calculator import calculate


class TestCompoundInterestCalculator(unittest.TestCase):
    def test_basic_interest_no_additions(self):
        # 1000 principal, 5% rate, monthly compounding for 1 year
        result = calculate(principal=1000, rate=5, time=1, additional=0)
        self.assertAlmostEqual(result["final_amount"], 1051.16, places=2)
        self.assertAlmostEqual(result["interest_earned"], 51.16, places=2)
        self.assertEqual(result["total_contributions"], 1000)

    def test_with_additional_contributions(self):
        result = calculate(principal=1000, rate=5, time=3, additional=500)
        self.assertAlmostEqual(result["final_amount"], 2234.51, places=2)
        self.assertAlmostEqual(result["interest_earned"], 234.51, places=2)
        self.assertEqual(result["total_contributions"], 2000)

    def test_different_compounding_frequency(self):
        result_quarterly = calculate(principal=10000, rate=4, time=2, frequency=4)
        result_monthly = calculate(principal=10000, rate=4, time=2, frequency=12)
        self.assertLess(result_quarterly["final_amount"], result_monthly["final_amount"])

    def test_zero_interest(self):
        result = calculate(principal=5000, rate=0, time=5, additional=1000)
        self.assertEqual(result["final_amount"], 9000)
        self.assertEqual(result["interest_earned"], 0)
        self.assertEqual(result["total_contributions"], 9000)


if __name__ == "__main__":
    unittest.main()
