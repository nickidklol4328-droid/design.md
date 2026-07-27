"""
download_images.py — pull ore images from web search to build a training set.

Run this on your LAPTOP (where you train), not the robot. It saves images into
per-query folders under --out. You then LABEL them (Roboflow / labelImg) and
train yolo11n on the result.

Setup:
    pip install bing-image-downloader

Usage:
    python3 download_images.py "iron ore rock" "gold ore rock" --limit 120

Notes:
  * Web results are noisy — expect diagrams, product photos, and wrong rocks.
    You MUST review each folder and delete junk before labeling. Bad images
    teach the model the wrong thing.
  * Use specific queries ("raw iron ore chunk") over vague ones ("ore").
"""

import argparse
from pathlib import Path

from bing_image_downloader import downloader


def fetch(queries, out_dir, limit):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for q in queries:
        print(f"\n=== downloading up to {limit} for: {q!r} ===")
        downloader.download(
            q,
            limit=limit,
            output_dir=str(out),
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
        )
    print(f"\nDone. Review and clean the folders under: {out.resolve()}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Download ore images from web search.")
    p.add_argument("queries", nargs="+", help="one or more search phrases")
    p.add_argument("--out", default="dataset/raw", help="output directory")
    p.add_argument("--limit", type=int, default=100, help="images per query")
    args = p.parse_args()

    fetch(args.queries, args.out, args.limit)
