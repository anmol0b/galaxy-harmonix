"""Command-line interface: ``python -m processing input.mp4 -o output.mp4 --threshold 80``."""

import argparse
import sys
from pathlib import Path

from .pipeline import SonifyConfig, sonify, sonify_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m processing",
                                     description="Turn a space video into sound.")
    parser.add_argument("input", type=Path, help="input video file")
    parser.add_argument("-o", "--output", type=Path,
                        help="output file (.mp4 for video with sound, .wav for audio only); "
                             "defaults to <input>_sonified.mp4")
    parser.add_argument("-t", "--threshold", type=int, default=80,
                        help="brightness (0-255) above which a pixel counts as a star (default: 80)")
    args = parser.parse_args(argv)

    if not 0 <= args.threshold <= 255:
        parser.error("--threshold must be between 0 and 255")
    output = args.output or args.input.with_name(f"{args.input.stem}_sonified.mp4")
    config = SonifyConfig(threshold=args.threshold)

    def progress(fraction: float) -> None:
        print(f"\rAnalysing frames… {fraction:4.0%}", end="", file=sys.stderr, flush=True)

    run = sonify if output.suffix.lower() == ".wav" else sonify_video
    result = run(args.input, output, config, progress)
    print(f"\nWrote {output} — {result.duration:.0f}s, {result.frames_analysed} frames, "
          f"{result.notes_played} star notes", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
