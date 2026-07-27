"""
collect_images.py — capture training images of ore from the Pi camera.

Run this ON THE ROBOT. It saves timestamped JPEGs you'll then label (Roboflow
/ labelImg) and train yolo11n on. Shoot from the car's real camera angle, in
varied lighting and backgrounds, with ore at different distances/angles.

Usage:
    python3 collect_images.py                 # capture every 1.0s, 100 shots
    python3 collect_images.py --count 300 --interval 0.5 --out dataset/ore

Copy them off the Pi with, e.g.:
    scp -r firestingray:~/tokyo_robotics/image_recognition/dataset ./dataset
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

from picamera2 import Picamera2


def collect(out_dir, count, interval):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cam = Picamera2()
    cam.configure(cam.create_still_configuration())
    cam.start()
    time.sleep(2)  # let exposure/white-balance settle

    try:
        for i in range(count):
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = out / f"ore_{stamp}.jpg"
            cam.capture_file(str(path))
            print(f"[{i + 1}/{count}] saved {path}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nstopped early")
    finally:
        cam.stop()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Capture ore training images.")
    p.add_argument("--out", default="dataset/ore", help="output directory")
    p.add_argument("--count", type=int, default=100, help="number of images")
    p.add_argument("--interval", type=float, default=1.0, help="seconds between shots")
    args = p.parse_args()

    collect(args.out, args.count, args.interval)
