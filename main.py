"""Entry for make.fun bounty the-poster-for-a-place-that-i-2-20261121-0539.

A travel poster for KAELITH, a place that does not exist: a floating island
with a waterfall and a lighthouse, above a sea of clouds at dusk. The program
writes the poster as a 1024x1024 PNG to /output/entry.png (or the directory
named by MAKEFUN_OUTPUT_DIR).

Python 3.13, standard library only, single file, no package import, so it
runs unchanged under the grader's `python3 -P -s` flags. The image is a
constant scene: two runs produce byte-identical files.
"""

import binascii
import os
import struct
import sys
import zlib

SIZE = 1024


def lerp(c1, c2, t):
    """Linear interpolation between two RGB colours."""
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(width, height, rgb):
    """Encode raw RGB bytes as a PNG (colour type 2, filter 0, zlib level 9)."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


class Canvas:
    """A mutable RGB raster with small drawing helpers."""

    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.px = bytearray(width * height * 3)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.px[i], self.px[i + 1], self.px[i + 2])

    def fill_rect(self, x0, y0, x1, y1, color):
        """Fill an inclusive rectangle, clipped to the canvas."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return
        row = bytes(color) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def vgrad(self, stops):
        """Vertical gradient. stops: list of (fraction 0..1, colour)."""
        for y in range(self.h):
            t = y / (self.h - 1)
            for k in range(len(stops) - 1):
                f0, c0 = stops[k]
                f1, c1 = stops[k + 1]
                if f0 <= t <= f1:
                    color = lerp(c0, c1, 0.0 if f1 == f0 else (t - f0) / (f1 - f0))
                    break
            else:
                color = stops[-1][1]
            self.fill_rect(0, y, self.w - 1, y, color)

    def disc(self, cx, cy, r, color):
        """Filled circle."""
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
            self.fill_rect(cx - dx, y, cx + dx, y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        """Filled ellipse."""
        for y in range(cy - ry, cy + ry + 1):
            dy = y - cy
            inside = 1.0 - (dy * dy) / float(ry * ry)
            if inside < 0:
                continue
            dx = int(rx * inside ** 0.5)
            self.fill_rect(cx - dx, y, cx + dx, y, color)

    def polygon(self, pts, color):
        """Scanline fill of a simple polygon."""
        ys = [p[1] for p in pts]
        y0 = max(0, min(ys))
        y1 = min(self.h - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, ya = pts[i]
                x1, yb = pts[(i + 1) % n]
                if (ya <= y < yb) or (yb <= y < ya):
                    t = (y - ya) / (yb - ya)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(round(xs[j])), y, int(round(xs[j + 1])), y, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        """DDA line, square brush of the given width."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            t = s / steps
            x = int(round(x0 + (x1 - x0) * t))
            y = int(round(y0 + (y1 - y0) * t))
            self.fill_rect(x - width // 2, y - width // 2,
                           x + width // 2, y + width // 2, color)

# --- Poster type: a bold 8x10 bitmap font, one glyph per letter. --------
# Only the letters of KAELITH are needed. Each glyph is 10 rows of 8 cells.
FONT = {
    "K": (
        "##....##",
        "##...##.",
        "##..##..",
        "##.##...",
        "####....",
        "##.##...",
        "##..##..",
        "##...##.",
        "##....##",
        "##....##",
    ),
    "A": (
        "..####..",
        ".##..##.",
        "##....##",
        "##....##",
        "########",
        "##....##",
        "##....##",
        "##....##",
        "##....##",
        "##....##",
    ),
    "E": (
        "########",
        "##......",
        "##......",
        "##......",
        "#####...",
        "##......",
        "##......",
        "##......",
        "##......",
        "########",
    ),
    "L": (
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "########",
    ),
    "I": (
        "########",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "########",
    ),
    "T": (
        "########",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
    ),
    "H": (
        "##....##",
        "##....##",
        "##....##",
        "##....##",
        "########",
        "##....##",
        "##....##",
        "##....##",
        "##....##",
        "##....##",
    ),
}

NAME = "KAELITH"
CELL = 12          # pixels per font cell
GAP = 14           # pixels between letters
NAME_Y = 64        # top of the name
CREAM = (255, 243, 214)
INK = (19, 30, 54)


def draw_text(canvas, text, x, y, cell, color):
    """Draw text in the bitmap font; returns the width in pixels."""
    cx = x
    for ch in text:
        glyph = FONT[ch]
        for row in range(10):
            for col in range(8):
                if glyph[row][col] == "#":
                    canvas.fill_rect(
                        cx + col * cell, y + row * cell,
                        cx + (col + 1) * cell - 1, y + (row + 1) * cell - 1,
                        color,
                    )
        cx += 8 * cell + GAP
    return cx - GAP - x


def name_width(text):
    return len(text) * 8 * CELL + (len(text) - 1) * GAP


def pine(canvas, x, y, size, color):
    """A small pine tree: two triangles and a trunk. (x, y) is the base."""
    canvas.polygon(
        [(x - size, y), (x + size, y), (x, y - int(size * 1.6))], color)
    canvas.polygon(
        [(x - int(size * 0.75), y - int(size * 0.9)),
         (x + int(size * 0.75), y - int(size * 0.9)),
         (x, y - int(size * 2.4))], color)
    canvas.fill_rect(x - 2, y, x + 2, y + 8, (46, 32, 22))


def render():
    """Draw the KAELITH poster and return the Canvas."""
    c = Canvas(SIZE, SIZE)

    # Dusk sky: indigo overhead, warming to peach at the horizon.
    c.vgrad([
        (0.00, (19, 30, 54)),
        (0.45, (70, 84, 126)),
        (0.66, (224, 138, 82)),
        (1.00, (240, 170, 100)),
    ])

    # Low sun with a soft glow, right of centre on the horizon.
    c.disc(730, 610, 132, (238, 166, 94))
    c.disc(730, 610, 100, (244, 190, 122))
    c.disc(730, 610, 64, (251, 210, 122))

    # Distant misty ridges across the horizon.
    c.polygon([(0, 700), (140, 648), (300, 688), (470, 640), (640, 690),
               (820, 652), (1024, 700), (1024, 760), (0, 760)], (91, 107, 140))
    c.polygon([(0, 730), (180, 682), (380, 722), (560, 680), (760, 724),
               (920, 686), (1024, 716), (1024, 780), (0, 780)], (70, 85, 122))

    # Far floating islets, small and faint.
    c.polygon([(150, 548), (210, 548), (196, 580), (180, 606),
               (168, 584)], (58, 74, 102))
    pine(c, 178, 550, 12, (48, 66, 92))
    c.polygon([(852, 500), (912, 500), (898, 532), (882, 556),
               (870, 534)], (58, 74, 102))
    pine(c, 880, 502, 12, (48, 66, 92))

    # Sea of clouds below the horizon.
    c.fill_rect(0, 760, SIZE - 1, SIZE - 1, (238, 166, 106))
    for (cx, cy, rx, ry, col) in [
        (140, 800, 190, 46, (242, 192, 138)),
        (420, 830, 230, 56, (251, 227, 176)),
        (760, 806, 210, 50, (242, 192, 138)),
        (980, 850, 180, 60, (251, 227, 176)),
        (240, 920, 220, 60, (251, 227, 176)),
        (620, 940, 260, 66, (242, 192, 138)),
        (940, 950, 200, 62, (251, 227, 176)),
        (60, 990, 180, 50, (242, 192, 138)),
        (520, 1010, 240, 56, (251, 227, 176)),
    ]:
        c.ellipse(cx, cy, rx, ry, col)

    # The hero island: plateau on top, rock tapering to a point below.
    island = [(240, 400), (800, 400), (770, 470), (700, 545), (620, 595),
              (520, 652), (430, 585), (330, 520), (262, 462)]
    c.polygon(island, (31, 58, 68))
    # Warm rim light on the sun side of the rock.
    c.polygon([(800, 400), (770, 470), (700, 545), (620, 595), (520, 652),
               (560, 620), (660, 540), (740, 462)], (232, 166, 106))
    # Grassy plateau.
    c.polygon([(240, 400), (800, 400), (796, 414), (244, 414)], (46, 93, 75))

    # Waterfall pouring off the plateau's left edge into the clouds.
    c.polygon([(296, 412), (326, 412), (322, 646), (296, 646)], (207, 232, 234))
    c.polygon([(304, 412), (318, 412), (316, 646), (304, 646)], (240, 244, 246))
    c.ellipse(310, 650, 34, 14, (240, 244, 246))
    c.ellipse(310, 658, 48, 12, (207, 232, 234))

    # Pines on the plateau.
    pine(c, 420, 402, 22, (28, 68, 52))
    pine(c, 480, 402, 18, (28, 68, 52))
    pine(c, 700, 402, 20, (28, 68, 52))

    # Lighthouse on the plateau, right of centre.
    c.fill_rect(592, 340, 616, 400, CREAM)
    c.fill_rect(590, 336, 618, 342, INK)
    c.polygon([(588, 336), (620, 336), (604, 318)], INK)
    c.disc(604, 330, 4, (251, 210, 122))

    # Birds in the dusk sky.
    for (bx, by) in [(300, 250), (362, 228), (700, 268), (762, 238), (824, 292)]:
        c.line(bx - 10, by, bx, by + 7, INK, 2)
        c.line(bx, by + 7, bx + 10, by, INK, 2)

    # The place name across the top: dark shadow, then cream.
    w = name_width(NAME)
    x0 = (SIZE - w) // 2
    draw_text(c, NAME, x0 + 5, NAME_Y + 6, CELL, INK)
    draw_text(c, NAME, x0, NAME_Y, CELL, CREAM)
    # A thin rule with a diamond under the name, decoration only.
    c.fill_rect(320, 208, 704, 211, CREAM)
    c.polygon([(512, 200), (522, 209), (512, 218), (502, 209)], CREAM)

    # A thin dark frame, the poster's edge.
    c.fill_rect(0, 0, SIZE - 1, 7, INK)
    c.fill_rect(0, SIZE - 8, SIZE - 1, SIZE - 1, INK)
    c.fill_rect(0, 0, 7, SIZE - 1, INK)
    c.fill_rect(SIZE - 8, 0, SIZE - 1, SIZE - 1, INK)

    return c


def main():
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "entry.png")
    data = encode_png(SIZE, SIZE, render().px)
    with open(path, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o644)
    return 0


if __name__ == "__main__":
    sys.exit(main())
