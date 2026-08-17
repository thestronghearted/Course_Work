"""Discount calculator (Exercise 13, Example 4 — Poor Formatting and Structure).

The original one-letter-variable, semicolon-packed ``discount`` function is
reformatted here into readable, structured code with helper functions. Behaviour
is preserved exactly (verified by ``test_discount.py``).

Note: the original applies the best single discount (promotions and the
status-based discount do not stack) and treats 'shipping' promos as a side
effect that sets ``free_shipping`` on the user. Both behaviours are kept.
"""


def _cart_total(cart):
    """Sum price x quantity across all cart items."""
    return sum(item['price'] * item['quantity'] for item in cart)


def _meets_minimum(promo, total):
    """True if the promo has no minimum, or the total meets it."""
    minimum = promo.get('min_purchase')
    return minimum is None or total >= minimum


def _promo_discount(promo, total, user):
    """Return the discount value a single promo yields (0 if not applicable).

    A 'shipping' promo has no monetary discount but sets free shipping on the
    user as a side effect (preserving the original behaviour).
    """
    if promo['type'] == 'percent' and _meets_minimum(promo, total):
        return total * promo['value'] / 100
    if promo['type'] == 'fixed' and _meets_minimum(promo, total):
        return min(promo['value'], total)
    if promo['type'] == 'shipping' and total >= promo['min_purchase']:
        user['free_shipping'] = True
    return 0


def _status_discount(user, total):
    """Return the loyalty discount based on the user's status."""
    if user['status'] == 'vip':
        return total * 0.05
    if user['status'] == 'member' and user['months'] > 6:
        return total * 0.02
    return 0


def discount(cart, promos, user):
    """Compute the best available discount for a cart.

    Promotions and the status-based loyalty discount do not stack: the single
    largest applicable discount wins.

    Returns:
        dict with ``original`` (cart total), ``discount`` (best discount),
        ``final`` (total minus discount) and ``free_shipping`` (bool).
    """
    total = _cart_total(cart)

    best_discount = 0
    for promo in promos:
        best_discount = max(best_discount, _promo_discount(promo, total, user))

    best_discount = max(best_discount, _status_discount(user, total))

    return {
        'original': total,
        'discount': best_discount,
        'final': total - best_discount,
        'free_shipping': user.get('free_shipping', False),
    }
