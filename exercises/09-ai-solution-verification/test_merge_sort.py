"""Tests that (a) demonstrate the bug and (b) verify the fixed implementation."""
import random
import threading
import unittest

from merge_sort import merge_sort, merge_sort_buggy


class TestMergeSort(unittest.TestCase):
    def test_fixed_sorts_correctly(self):
        cases = [
            [],
            [1],
            [2, 1],
            [5, 2, 9, 1, 5, 6],
            [3, 3, 3, 1, 2, 2],
            list(range(10, 0, -1)),
            [1, 2, 3, 4, 5],          # already sorted
            [-3, 5, 0, -8, 10, 7],    # negatives
        ]
        for c in cases:
            self.assertEqual(merge_sort(c), sorted(c), f"failed on {c}")

    def test_fixed_does_not_mutate_input(self):
        data = [3, 1, 2]
        merge_sort(data)
        self.assertEqual(data, [3, 1, 2])

    def test_fixed_matches_sorted_on_random_data(self):
        for _ in range(200):
            data = [random.randint(-50, 50) for _ in range(random.randint(0, 40))]
            self.assertEqual(merge_sort(data), sorted(data))

    def test_buggy_infinite_loops_on_leftover_left(self):
        # The bug never advances i in the leftover-left loop, so it fails to
        # terminate whenever the left half still has elements. We run it in a
        # daemon thread and assert it does NOT finish within a short timeout.
        finished = threading.Event()

        def run():
            merge_sort_buggy([1, 4, 2, 3])  # left half [1,4] outlives right [2,3]
            finished.set()

        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(timeout=1.0)
        self.assertFalse(finished.is_set(),
                         "buggy merge sort unexpectedly terminated")


if __name__ == "__main__":
    unittest.main()
