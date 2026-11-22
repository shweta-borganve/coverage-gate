"""Generate standalone SVG coverage badges."""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape


def _coverage_color(coverage: float) -> str:
    """Return the badge color for a coverage percentage."""
    if coverage < 60:
        return "#e05d44"
    if coverage < 80:
        return "#dfb317"
    return "#4c1"


def generate_badge(
    coverage: float,
    output_path: str | Path,
) -> Path:
    """Generate an SVG badge showing the coverage percentage."""
    try:
        percentage = float(coverage)
    except (TypeError, ValueError) as exc:
        raise ValueError("Coverage must be a valid number.") from exc

    if not math.isfinite(percentage) or not 0 <= percentage <= 100:
        raise ValueError("Coverage must be between 0 and 100.")

    destination = Path(output_path)
    label = "coverage"
    value = f"{percentage:.1f}%"

    label_width = 68
    value_width = max(38, len(value) * 7 + 12)
    total_width = label_width + value_width

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="{total_width}" height="20" role="img"
    aria-label="{escape(label)}: {escape(value)}">
  <title>{escape(label)}: {escape(value)}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20"
      fill="{_coverage_color(percentage)}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle"
    font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
    font-size="11">
    <text x="{label_width / 2}" y="14">{escape(label)}</text>
    <text x="{label_width + value_width / 2}" y="14">{escape(value)}</text>
  </g>
</svg>
"""

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")
    return destination
