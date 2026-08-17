"""Optimised product-combination finder.

Original: O(n^2) double loop over all ordered pairs, with an O(results) duplicate
scan *inside* the inner loop (so worst case approaches O(n^2 * R)).

Optimised: sort products by price once, then for each product use binary search
(bisect) to locate only the partners whose price lands in the valid window
[target - margin - price, target + margin - price]. Pairing only j > i means each
unordered pair is produced exactly once, so the expensive duplicate scan is gone.

Complexity: O(n log n) for the sort + O(n log n + R) for the search/collection,
where R is the number of matching pairs. Same results as the original.
"""

from bisect import bisect_left, bisect_right


def find_product_combinations(products, target_price, price_margin=10):
    """Find all pairs of products whose combined price is within
    ``target_price ± price_margin``.

    Args:
        products: list of dicts with 'id', 'name', 'price' keys.
        target_price: ideal combined price.
        price_margin: acceptable deviation from the target.

    Returns:
        List of pair dicts (product1, product2, combined_price, price_difference),
        sorted by ascending distance from the target price.
    """
    # Sort a copy by price so we can binary-search partner windows.
    sorted_products = sorted(products, key=lambda p: p['price'])
    prices = [p['price'] for p in sorted_products]
    n = len(sorted_products)

    results = []
    low_bound = target_price - price_margin
    high_bound = target_price + price_margin

    for i in range(n):
        p1_price = prices[i]
        # Valid partner prices so that p1 + p2 is within [low_bound, high_bound].
        lo = low_bound - p1_price
        hi = high_bound - p1_price

        # Only look to the right of i (j > i) → each unordered pair once.
        start = bisect_left(prices, lo, i + 1)
        end = bisect_right(prices, hi, i + 1)

        product1 = sorted_products[i]
        for j in range(start, end):
            product2 = sorted_products[j]
            combined_price = p1_price + prices[j]
            results.append({
                'product1': product1,
                'product2': product2,
                'combined_price': combined_price,
                'price_difference': abs(target_price - combined_price),
            })

    results.sort(key=lambda x: x['price_difference'])
    return results
