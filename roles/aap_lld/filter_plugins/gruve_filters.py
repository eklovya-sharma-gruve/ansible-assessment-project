"""Tiny, dependency-free filters shipped with the aap_lld role."""
from __future__ import annotations


def gruve_pick(item, keys):
    """Return a dict with only the requested keys from a (possibly nested) dict."""
    if not isinstance(item, dict):
        return {}
    return {k: item.get(k) for k in keys}


def gruve_counter(seq):
    """Count occurrences in a list -> dict(value: count). Replaces community.general.counter."""
    out = {}
    for v in (seq or []):
        key = "unknown" if v is None else v
        out[key] = out.get(key, 0) + 1
    return out


def gruve_get(item, key, default=None):
    """Safe get from a dict; returns default if absent or not a dict."""
    if not isinstance(item, dict):
        return default
    val = item.get(key, default)
    return default if val is None else val


def gruve_ratio(numerator, denominator, places=3):
    """Safe division -> float, 0 when denominator is 0."""
    try:
        d = float(denominator)
        if d == 0:
            return 0.0
        return round(float(numerator) / d, places)
    except (TypeError, ValueError):
        return 0.0


def gruve_pct(numerator, denominator):
    """Safe percentage 0-100 (int)."""
    try:
        d = float(denominator)
        if d == 0:
            return 0
        return int(round(100.0 * float(numerator) / d))
    except (TypeError, ValueError):
        return 0


class FilterModule(object):
    def filters(self):
        return {
            "gruve_pick": gruve_pick,
            "gruve_counter": gruve_counter,
            "gruve_get": gruve_get,
            "gruve_ratio": gruve_ratio,
            "gruve_pct": gruve_pct,
        }
