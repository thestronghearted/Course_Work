"""Merge sort — buggy vs verified implementations.

This exercise starts from an AI-provided merge sort that contains a subtle bug
(the same one as the course's JavaScript sample: in the "copy the remaining left
elements" loop, the wrong index is advanced, so leftover left-hand elements are
never appended). Both versions are kept here so the difference — and the tests —
are explicit.
"""


def merge_sort_buggy(arr):
    """Merge sort with a subtle bug in the leftover-copy step (do NOT use)."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort_buggy(arr[:mid])
    right = merge_sort_buggy(arr[mid:])
    return _merge_buggy(left, right)


def _merge_buggy(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # BUG: appends left[i] but advances j instead of i. Because i never changes,
    # this loop NEVER terminates whenever the left half has leftover elements —
    # an infinite loop, not merely a wrong result.
    while i < len(left):
        result.append(left[i])
        j += 1  # <-- should be i += 1
    while j < len(right):
        result.append(right[j])
        j += 1
    return result


def merge_sort(arr):
    """Verified merge sort. Returns a new sorted list; input is not mutated.

    Stable, O(n log n) time, O(n) space.
    """
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left, right):
    """Merge two sorted lists into one sorted list (stable)."""
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:   # <= keeps the sort stable
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # Correct: advance the matching index in each leftover loop.
    result.extend(left[i:])
    result.extend(right[j:])
    return result


if __name__ == "__main__":
    sample = [5, 2, 9, 1, 5, 6]
    # NOTE: merge_sort_buggy(sample) is intentionally NOT called here — it would
    # hang (infinite loop) as soon as the left half has leftover elements.
    print("fixed :", merge_sort(sample))
