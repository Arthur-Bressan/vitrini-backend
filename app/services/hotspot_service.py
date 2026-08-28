from __future__ import annotations


def to_percent(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 4)


def build_hotspot(page_width: float, page_height: float, x: float, y: float, *, width: float | None = None, height: float | None = None) -> dict[str, float | None]:
    return {
        "x_percent": to_percent(x, page_width),
        "y_percent": to_percent(y, page_height),
        "width_percent": to_percent(width, page_width) if width is not None else None,
        "height_percent": to_percent(height, page_height) if height is not None else None,
    }
