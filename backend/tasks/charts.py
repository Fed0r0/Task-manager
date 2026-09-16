import math

RADIUS = 46
CIRCUMFERENCE = 2 * math.pi * RADIUS


def donut_segments(segments):
    """segments: iterable of (label, value, color) tuples.

    Returns a list of dicts with the dasharray/dashoffset needed to draw
    each segment as a stacked <circle> inside one rotated <g>.
    """
    segments = list(segments)
    total = sum(value for _, value, _ in segments)
    cumulative = 0
    result = []
    for label, value, color in segments:
        length = (value / total) * CIRCUMFERENCE if total else 0
        result.append(
            {
                "label": label,
                "value": value,
                "color": color,
                "pct": round(value / total * 100) if total else 0,
                "dasharray": f"{length:.2f} {max(CIRCUMFERENCE - length, 0):.2f}",
                "dashoffset": f"{-cumulative:.2f}",
            }
        )
        cumulative += length
    return result


def bar_rows(rows, relative=True):
    """rows: iterable of (label, value, color) tuples.

    With relative=True, bar widths scale against the largest value in the
    set (for raw counts). With relative=False, the value is already a
    0-100 percentage and is used as the width directly.
    """
    rows = list(rows)
    if relative:
        max_value = max((value for _, value, _ in rows), default=0) or 1
        return [
            {"label": label, "value": value, "color": color, "width_pct": round(value / max_value * 100)}
            for label, value, color in rows
        ]
    return [
        {"label": label, "value": value, "color": color, "width_pct": max(0, min(100, value))}
        for label, value, color in rows
    ]
