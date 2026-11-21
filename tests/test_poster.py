"""Tests for the KAELITH poster (make.fun the-poster-for-a-place-that-i-2-20261121-0539).

They run the program as the grader does (python3 -P -s, read-only repo copy)
as well as plain, and check the gate in RULES.txt: a whole PNG, 1024x1024,
at most 1,048,576 bytes, deterministic output, plus the poster's own
requirements (the place name legible in the picture, one landmark).
"""

import hashlib
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ENTRY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PY = os.path.join(ENTRY_DIR, "main.py")

MAX_BYTES = 1_048_576
CREAM = (255, 243, 214)


def run_main(env_extra, use_grader_flags=False, repo_dir=None):
    """Run main.py in a subprocess; return (returncode, stdout, stderr)."""
    script = os.path.join(repo_dir, "main.py") if repo_dir else MAIN_PY
    cmd = [sys.executable]
    if use_grader_flags:
        cmd += ["-P", "-s"]
    cmd += [script]
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=120
    )


def read_png(path):
    """Decode our PNG (filter 0 rows) into (width, height, pixels)."""
    with open(path, "rb") as handle:
        data = handle.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, ctype = struct.unpack(">IIBB", chunk[:10])
            assert depth == 8 and ctype == 2, "expected 8-bit RGB"
        elif tag == b"IDAT":
            idat += chunk
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 3
    assert len(raw) == height * (1 + stride), "unexpected pixel data length"
    pixels = bytearray()
    for y in range(height):
        assert raw[y * (1 + stride)] == 0, "expected filter 0"
        pixels += raw[y * (1 + stride) + 1:(y + 1) * (1 + stride)]
    return width, height, bytes(pixels)


def pixel(pixels, width, x, y):
    i = (y * width + x) * 3
    return (pixels[i], pixels[i + 1], pixels[i + 2])


class TestPoster(unittest.TestCase):
    def test_writes_entry_png_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as out_dir:
            proc = run_main({"MAKEFUN_OUTPUT_DIR": out_dir})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(os.path.join(out_dir, "entry.png")))

    def test_grader_flags_run(self):
        """The grader runs `python3 -P -s /bot/main.py` on a read-only repo."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_copy = os.path.join(tmp, "bot")
            out_dir = os.path.join(tmp, "out")
            os.makedirs(out_dir)
            os.makedirs(repo_copy)
            shutil.copy(MAIN_PY, os.path.join(repo_copy, "main.py"))
            os.chmod(repo_copy, 0o555)
            os.chmod(os.path.join(repo_copy, "main.py"), 0o444)
            try:
                proc = run_main(
                    {"MAKEFUN_OUTPUT_DIR": out_dir},
                    use_grader_flags=True,
                    repo_dir=repo_copy,
                )
            finally:
                os.chmod(repo_copy, 0o755)
                os.chmod(os.path.join(repo_copy, "main.py"), 0o644)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(os.path.join(out_dir, "entry.png")))

    def test_png_is_1024x1024(self):
        with tempfile.TemporaryDirectory() as out_dir:
            run_main({"MAKEFUN_OUTPUT_DIR": out_dir})
            width, height, _ = read_png(os.path.join(out_dir, "entry.png"))
            self.assertEqual((width, height), (1024, 1024))

    def test_size_at_most_1_mib(self):
        with tempfile.TemporaryDirectory() as out_dir:
            run_main({"MAKEFUN_OUTPUT_DIR": out_dir})
            size = os.path.getsize(os.path.join(out_dir, "entry.png"))
            self.assertLessEqual(size, MAX_BYTES)

    def test_deterministic_two_runs_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_a = os.path.join(tmp, "a")
            out_b = os.path.join(tmp, "b")
            run_main({"MAKEFUN_OUTPUT_DIR": out_a})
            run_main({"MAKEFUN_OUTPUT_DIR": out_b})
            with open(os.path.join(out_a, "entry.png"), "rb") as h:
                digest_a = hashlib.sha256(h.read()).hexdigest()
            with open(os.path.join(out_b, "entry.png"), "rb") as h:
                digest_b = hashlib.sha256(h.read()).hexdigest()
            self.assertEqual(digest_a, digest_b)

    def test_file_mode_0644(self):
        with tempfile.TemporaryDirectory() as out_dir:
            run_main({"MAKEFUN_OUTPUT_DIR": out_dir})
            mode = stat.S_IMODE(os.stat(os.path.join(out_dir, "entry.png")).st_mode)
            self.assertEqual(mode, 0o644)

    def test_creates_missing_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "deep", "deeper")
            proc = run_main({"MAKEFUN_OUTPUT_DIR": nested})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(os.path.join(nested, "entry.png")))

    def test_name_band_has_cream_type(self):
        """The place name must be set into the picture, in cream type."""
        with tempfile.TemporaryDirectory() as out_dir:
            run_main({"MAKEFUN_OUTPUT_DIR": out_dir})
            width, _, pixels = read_png(os.path.join(out_dir, "entry.png"))
            count = 0
            for y in range(64, 184):
                for x in range(100, 924):
                    if pixel(pixels, width, x, y) == CREAM:
                        count += 1
            self.assertGreater(count, 10000, "name type not visible")

    def test_sky_island_and_sun_colours(self):
        with tempfile.TemporaryDirectory() as out_dir:
            run_main({"MAKEFUN_OUTPUT_DIR": out_dir})
            width, _, pixels = read_png(os.path.join(out_dir, "entry.png"))
            r, g, b = pixel(pixels, width, 512, 30)
            self.assertLess(r, 40)
            self.assertLess(g, 60)
            self.assertGreater(b, r)  # dusk sky is dark indigo overhead
            self.assertEqual(pixel(pixels, width, 512, 500), (31, 58, 68))
            self.assertEqual(pixel(pixels, width, 730, 610), (251, 210, 122))

    def test_font_draws_letter_a(self):
        sys.path.insert(0, ENTRY_DIR)
        import main
        canvas = main.Canvas(200, 200)
        width = main.draw_text(canvas, "A", 10, 10, 2, main.CREAM)
        self.assertEqual(width, 8 * 2)
        self.assertEqual(canvas.get(10 + 2 * 2, 10), main.CREAM)
        self.assertEqual(canvas.get(10, 10 + 9 * 2), main.CREAM)


if __name__ == "__main__":
    unittest.main()
