"""
train.py — train yolo11n on a locally-downloaded Roboflow detection dataset.

Run on a LAPTOP or Google Colab with a GPU (Colab: Runtime -> Change runtime
type -> GPU). NOT on the Pi — the Pi only runs the finished model.

    pip install ultralytics

STEP 1 — download the dataset into ./dataset (run this in YOUR terminal; it
won't work from an automated sandbox because Roboflow is behind Cloudflare):

    cd image_recognition/dataset
    curl -L "https://universe.roboflow.com/ds/14smBRPuZT?key=mH44JgpySY" > roboflow.zip
    unzip roboflow.zip && rm roboflow.zip

That produces dataset/data.yaml plus train/ valid/ test/ folders (images +
YOLO-format box labels).

STEP 2 — train:

    python3 train.py

No Roboflow API key needed: the zip already contains the images and labels.
"""

import sys
from pathlib import Path

import torch
from ultralytics import YOLO

# --- config ------------------------------------------------------------------
# The data.yaml that the downloaded zip extracts into ./dataset.
DATA_YAML = Path(__file__).parent / "dataset" / "data.yaml"

# Lowered for a local CPU run (no GPU). Raise EPOCHS/IMGSZ (e.g. 100/640) and
# retrain on Colab's free GPU later for a stronger model.
EPOCHS = 20
IMGSZ = 416
MODEL = "yolo11n.pt"   # nano detection model, small enough to run on the Pi

# Pick the fastest available device: Apple GPU (mps), NVIDIA (cuda), else cpu.
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"


def main():
    if not DATA_YAML.exists():
        sys.exit(
            f"Dataset not found at {DATA_YAML}.\n"
            f"Download it first (see STEP 1 in this file's docstring):\n"
            f"  cd {DATA_YAML.parent}\n"
            f'  curl -L "https://universe.roboflow.com/ds/14smBRPuZT?key=mH44JgpySY" > roboflow.zip\n'
            f"  unzip roboflow.zip && rm roboflow.zip"
        )

    print(f"Training on device: {DEVICE}")
    model = YOLO(MODEL)
    model.train(data=str(DATA_YAML), epochs=EPOCHS, imgsz=IMGSZ, device=DEVICE)

    # Best weights land in runs/detect/train/weights/best.pt
    # Copy that to the Pi as models/ore_best.pt (what app.py loads), e.g.:
    #   scp runs/detect/train/weights/best.pt \
    #       firestingray:~/tokyo_robotics/image_recognition/models/ore_best.pt


if __name__ == "__main__":
    main()
