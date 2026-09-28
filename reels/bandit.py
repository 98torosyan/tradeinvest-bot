"""Thompson-sampling choice between variants (CTA types, hook formulas...),
updated weekly from real Instagram results."""
import random


def choose(state, category, arms, avoid=None):
    b = state.setdefault("bandit", {}).setdefault(category, {})
    best, best_v = None, -1.0
    for arm in arms:
        a, n = b.get(arm, [1, 1])
        v = random.betavariate(a, n)
        if arm == avoid:
            v *= 0.5                      # rarely repeat the same variant twice in a row
        if v > best_v:
            best, best_v = arm, v
    return best


def update(state, category, arm, success):
    b = state.setdefault("bandit", {}).setdefault(category, {})
    a, n = b.get(arm, [1, 1])
    b[arm] = [a + (1 if success else 0), n + (0 if success else 1)]
