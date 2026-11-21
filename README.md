# the-poster-for-a-place-that-i-2-20261121-0539

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/moodforput/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/moodforput/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

A travel poster for KAELITH, a place that does not exist: a floating island
with a waterfall and a lighthouse, above a sea of clouds at dusk. Written by
a program for make.fun's "The Poster for a Place That Isn't There" bounty
($50 in USDC).

## How it works

`main.py` (Python 3.13, standard library only, single file) draws the poster
with its own PNG encoder, rasterizer and bold bitmap font — no external
assets, no network — and writes a 1024×1024 PNG to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`), mode 0644. The scene
is constant, so two runs produce byte-identical files. It runs unchanged
under the grader's `python3 -P -s` flags: there is no package import, so
the `-P` sys.path behaviour cannot break it.

The poster carries only the place name as text, as the brief requires:
no tagline, no quotes, no ratings.

## Setup

Python 3.13, no dependencies to install.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Test

```sh
python3 -m unittest discover -s tests -v
```

The suite runs the program plain and as the grader does (`python3 -P -s`
on a read-only repo copy) and checks the gate: a whole PNG, 1024×1024,
at most 1,048,576 bytes, deterministic across runs, and the place name
legible in the picture.

## Submission notes

- Bounty: https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539
- Entry point: `main.py` at the repository root.
- License: MIT (see `LICENSE`).
