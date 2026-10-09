#!/usr/bin/env python3
"""Plot an approximate Fibonacci spiral: tiled Fibonacci squares with a quarter-circle arc in each.

Usage:
    python3 fibonacci_spiral.py                       # 10 squares, interactive window
    python3 fibonacci_spiral.py -n 14 --cmap plasma   # more squares, different colors
    python3 fibonacci_spiral.py --axes                # show x-y axes and grid
    python3 fibonacci_spiral.py --save spiral.png     # write an image instead

Run with --help for all options. The plotting code can also be imported:

    from fibonacci_spiral import SpiralOptions, plot_spiral
    fig = plot_spiral(SpiralOptions(n=12, show_axes=True))
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Rectangle


@dataclass(frozen=True)
class SpiralOptions:
    """User-adjustable plot settings."""

    n: int = 8                   # number of squares
    cmap: str = "gist_rainbow"    # colormap for the squares
    arc_color: str = "crimson"    # color of the spiral line
    arc_width: float = 2.5        # line width of the spiral
    show_axes: bool = True       # draw x-y axes and grid
    show_labels: bool = True      # write side lengths in the squares
    figsize: tuple[float, float] = (9.0, 7.0)


Tile = tuple[int, int, int, tuple[int, int], float, float]


def fibonacci(n: int) -> list[int]:
    """Return the first n Fibonacci numbers starting 1, 1, 2, 3, ..."""
    seq = [1, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]


def fibonacci_tiles(n: int) -> list[Tile]:
    """Returns (x0, y0, side, arc_center, theta1, theta2) for each square.

    Each new square is attached to the right, top, left, then the bottom of the
    bounding box of all previous squares, so arcs join into a continuous
    counterclockwise spiral.
    """
    xmin = ymin = xmax = ymax = 0
    tiles: list[Tile] = []
    for i, s in enumerate(fibonacci(n)):
        if i == 0:
            x0, y0 = 0, 0
            center, t1 = (x0 + s, y0 + s), 180
        else:
            direction = (i - 1) % 4
            if direction == 0:    # attach on the right
                x0, y0 = xmax, ymin
                center, t1 = (x0, y0 + s), 270
            elif direction == 1:  # attach on top
                x0, y0 = xmin, ymax
                center, t1 = (x0, y0), 0
            elif direction == 2:  # attach on the left
                x0, y0 = xmin - s, ymin
                center, t1 = (x0 + s, y0), 90
            else:                 # attach below
                x0, y0 = xmin, ymin - s
                center, t1 = (x0 + s, y0 + s), 180
        tiles.append((x0, y0, s, center, t1, t1 + 90))
        xmin, ymin = min(xmin, x0), min(ymin, y0)
        xmax, ymax = max(xmax, x0 + s), max(ymax, y0 + s)
    return tiles


def plot_spiral(options: SpiralOptions = SpiralOptions()) -> Figure:
    """Draw the spiral and return a figure."""
    tiles = fibonacci_tiles(options.n)
    largest = tiles[-1][2]
    cmap = plt.get_cmap(options.cmap)

    fig, ax = plt.subplots(figsize=options.figsize)
    outline = [patheffects.withStroke(linewidth=3, foreground="black")]

    for i, (x0, y0, s, center, t1, t2) in enumerate(tiles):
        color = cmap(i / max(options.n - 1, 1))
        ax.add_patch(Rectangle((x0, y0), s, s, facecolor=color, alpha=0.35,
                               edgecolor="black", linewidth=1))
        ax.add_patch(Arc(center, 2 * s, 2 * s, theta1=t1, theta2=t2,
                         color=options.arc_color, linewidth=options.arc_width))
        # Label squares that are big enough to hold text
        if options.show_labels and s >= largest / 40:
            fontsize = 6 + 18 * (s / largest) ** 0.5
            ax.text(x0 + s / 2, y0 + s / 2, str(s), ha="center", va="center",
                    fontsize=fontsize, color="white", path_effects=outline)

    ax.set_aspect("equal")
    ax.autoscale_view()
    if options.show_axes:
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.3)
    else:
        ax.axis("off")
    ax.set_title(f"Fibonacci spiral ({options.n} squares)", fontsize=14)
    fig.tight_layout()
    return fig


def positive_int(value: str) -> int:
    """argparse type: an integer >= 1."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    defaults = SpiralOptions()
    parser = argparse.ArgumentParser(
        description="Plot the Fibonacci spiral.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-n", "--squares", type=positive_int, default=defaults.n,
                        help="number of squares to draw")
    parser.add_argument("--cmap", default=defaults.cmap,
                        help="matplotlib colormap for the squares (e.g. viridis, plasma)")
    parser.add_argument("--arc-color", default=defaults.arc_color,
                        help="color of the spiral line (name or hex, e.g. '#1f77b4')")
    parser.add_argument("--arc-width", type=float, default=defaults.arc_width,
                        help="line width of the spiral")
    parser.add_argument("--axes", action=argparse.BooleanOptionalAction,
                        default=defaults.show_axes, help="show x-y axes and grid")
    parser.add_argument("--labels", action=argparse.BooleanOptionalAction,
                        default=defaults.show_labels, help="label squares with their side length")
    parser.add_argument("--save", type=Path, metavar="FILE",
                        help="save to FILE (png, pdf, svg, ...) instead of showing a window")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmap not in plt.colormaps():
        parser.error(f"unknown colormap {args.cmap!r}; see "
                     "https://matplotlib.org/stable/gallery/color/colormap_reference.html")

    options = SpiralOptions(
        n=args.squares,
        cmap=args.cmap,
        arc_color=args.arc_color,
        arc_width=args.arc_width,
        show_axes=args.axes,
        show_labels=args.labels,
    )
    fig = plot_spiral(options)

    if args.save:
        fig.savefig(args.save, dpi=200, bbox_inches="tight")
        print(f"Saved to {args.save}")
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
