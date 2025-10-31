#!/usr/bin/env python3
"""
SoraStitcher — MP4 Stitcher for Sora 2 videos

Features
- Choose a starting MP4; the rest are shuffled randomly after it
- Works on all .mp4 files in a folder (non-recursive)
- Normalizes clips (codec, fps, size, audio) before concat to avoid mismatches
- Optional fixed seed for repeatable shuffles
- Zero external Python deps (uses `subprocess` to call ffmpeg)

Prereqs
- Python 3.8+
- ffmpeg installed and available on PATH (https://ffmpeg.org)

Usage examples
$ python SoraStitcher.py --folder /path/to/mp4s --start intro.mp4
$ python SoraStitcher.py --folder . --start 0001.mp4 -o intro.mp4 --fps 30 --width 1920 --height 1080
$ python SoraStitcher.py --folder ./sora2_out --start take1.mp4 --seed 42

Tip: If all your clips already share the same encoding, you can pass --fast to skip the normalize pass.
"""

from __future__ import annotations
import argparse
import os
import random
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

# ----------------------- Utilities -----------------------

def run(cmd: List[str], quiet: bool = False) -> None:
    if not quiet:
        print("→", " ".join(shlex.quote(c) for c in cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


def check_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            print(f"Error: {tool} not found on PATH. Install ffmpeg from https://ffmpeg.org and ensure it's accessible.", file=sys.stderr)
            sys.exit(1)


def probe_size(path: Path) -> Tuple[int, int]:
    """Return (width, height) using ffprobe; fallback to (1920, 1080) if unknown."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0:s=x",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        s = result.stdout.strip()
        if "x" in s:
            w_str, h_str = s.split("x")
            return int(w_str), int(h_str)
    except Exception:
        pass
    return 1920, 1080


# ----------------------- Core logic -----------------------

def normalize_clip(
    src: Path,
    dst: Path,
    *,
    fps: int,
    size: Tuple[int, int],
    crf: int = 20,
    preset: str = "medium",
    audio_bitrate: str = "192k",
) -> None:
    """Re-encode a clip to a consistent format for safe concatenation."""
    width, height = size
    vf = (
        f"scale=w={width}:h={height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,fps={fps}"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
        "-ar",
        "48000",
        "-ac",
        "2",
        str(dst),
    ]
    run(cmd)


def concat_via_list(file_list: List[Path], output: Path) -> None:
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        for p in file_list:
            tf.write(f"file '{p.as_posix().replace("'", "'\\''")}'\n")
        list_path = Path(tf.name)
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(output),
        ]
        run(cmd)
    finally:
        try:
            list_path.unlink()
        except Exception:
            pass


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="SoraStitcher — MP4 Stitcher for Sora 2 videos.")
    parser.add_argument("--folder", required=True, help="Folder containing .mp4 clips (non-recursive)")
    parser.add_argument("--start", required=True, help="Filename of the first clip (must be inside --folder)")
    parser.add_argument("-o", "--output", default="Sora_Reel.mp4", help="Output video filename")
    parser.add_argument("--fps", type=int, default=30, help="Output frames per second (default: 30)")
    parser.add_argument("--width", type=int, default=None, help="Output width (default: use first clip's width or 1920)")
    parser.add_argument("--height", type=int, default=None, help="Output height (default: use first clip's height or 1080)")
    parser.add_argument("--crf", type=int, default=20, help="x264 CRF quality (lower = higher quality; default 20)")
    parser.add_argument("--preset", default="medium", help="x264 preset (ultrafast..veryslow; default medium)")
    parser.add_argument("--audio-bitrate", default="192k", help="Audio bitrate (default 192k)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible shuffles")
    parser.add_argument("--fast", action="store_true", help="Skip normalize pass and try direct concat (clips must match)")

    args = parser.parse_args(argv)

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Error: folder not found: {folder}", file=sys.stderr)
        return 2

    check_ffmpeg()

    clips = sorted([p for p in folder.iterdir() if p.suffix.lower() == ".mp4" and p.is_file()])
    if not clips:
        print("Error: no .mp4 files found in folder.", file=sys.stderr)
        return 3

    start_path = (folder / args.start).resolve()
    if not start_path.exists():
        candidates = [p for p in clips if p.name == args.start]
        if candidates:
            start_path = candidates[0]
        else:
            print(f"Error: start file '{args.start}' not found in {folder}", file=sys.stderr)
            return 4

    others = [p for p in clips if p != start_path]
    if args.seed is not None:
        random.seed(args.seed)
    random.shuffle(others)
    ordered = [start_path] + others

    print("Found", len(clips), "clips. Starting with:", start_path.name)

    if args.width and args.height:
        size = (args.width, args.height)
    else:
        w, h = probe_size(start_path)
        size = (args.width or w, args.height or h)
    print(f"Target size: {size[0]}x{size[1]} @ {args.fps}fps")

    output = Path(args.output).expanduser().resolve()

    if args.fast:
        print("FAST mode: Attempting direct concat without re-encode. All clips must match.")
        try:
            concat_via_list(ordered, output)
            print(f"Done → {output}")
            return 0
        except SystemExit as e:
            return e.code

    with tempfile.TemporaryDirectory(prefix="sorastitcher_") as td:
        norm_dir = Path(td)
        norm_paths: List[Path] = []
        print("Normalizing clips (this may take a while)...")
        for idx, src in enumerate(ordered):
            dst = norm_dir / f"part_{idx:04d}.mp4"
            print(f"[{idx+1}/{len(ordered)}] {src.name} → {dst.name}")
            normalize_clip(
                src,
                dst,
                fps=args.fps,
                size=size,
                crf=args.crf,
                preset=args.preset,
                audio_bitrate=args.audio_bitrate,
            )
            norm_paths.append(dst)

        print("Concatenating...")
        concat_via_list(norm_paths, output)

    print(f"Done → {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
