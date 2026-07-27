"""
app.py — AI image detection for the mining-robot car.

Author: Andrew (camera + AI mineral detection)

Detection only. Captures frames from the Raspberry Pi camera and recognises
minerals with a trained YOLO model, printing each frame's detections. The
driving / decision (motion) layer is owned by the rest of the team and is not
part of this file.

Pipeline:  camera frame  ->  detector  ->  detections
"""

import time
from pathlib import Path

# The heavy / hardware-only libraries (ultralytics, picamera2) are imported
# lazily inside the classes that use them, so this file imports on any machine
# and each class can be tested on its own.


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

CAMERA_WIDTH = 480           # camera frame width, in pixels
CAMERA_HEIGHT = 480          # camera frame height, in pixels
TARGET_FPS = 30              # target detection-loop rate (frames per second)

# Trained mineral-detection weights. A stock yolo11n.pt will NOT work here — the
# model must first be trained on labeled mineral images (see train.py).
MODEL_PATH = "models/ore_best.pt"
CONFIDENCE_THRESHOLD = 0.5   # ignore detections scored below this (scale 0-1)


# --------------------------------------------------------------------------- #
# Camera
# --------------------------------------------------------------------------- #

class Camera:
    """Wraps the Raspberry Pi camera and hands single frames to the detector."""

    def __init__(self, width=CAMERA_WIDTH, height=CAMERA_HEIGHT):
        # Imported here (not at the top) so this file still imports on a laptop
        # with no picamera2 — only creating a Camera() actually needs the Pi.
        from picamera2 import Picamera2

        # Configure for RGB frames at the requested size, then start the camera.
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_preview_configuration(
            main={"format": "RGB888", "size": (width, height)}))
        self.cam.start()
        time.sleep(1.0)  # give auto-exposure / white-balance a moment to settle

    def read(self):
        """Return the latest frame as a numpy array (or None if unavailable)."""
        # capture_array() returns an OpenCV-style array, which YOLO accepts as-is.
        return self.cam.capture_array()

    def close(self):
        """Stop the camera and release it for other programs."""
        self.cam.stop()


# --------------------------------------------------------------------------- #
# Detector
# --------------------------------------------------------------------------- #

class Detector:
    """Loads the trained YOLO model and finds minerals in a frame."""

    def __init__(self, model_path=MODEL_PATH, confidence=CONFIDENCE_THRESHOLD):
        # Imported here (not at the top) so Camera stays usable without
        # ultralytics installed. Class names are stored inside the weights file.
        from ultralytics import YOLO

        # Fail early with a clear message if the trained model is missing.
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Detection model not found at '{model_path}'. Train one with "
                f"train.py, then copy runs/detect/train/weights/best.pt to "
                f"'{model_path}' (on the Pi, scp it into models/)."
            )
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):
        """
        Run the model on one frame and return the minerals it found.

        Each detection is a dict:
            {"label": str, "confidence": float, "box": (x, y, w, h)}
        where box is (top-left x, top-left y, width, height) in pixels.
        """
        results = self.model(frame, verbose=False)[0]
        detections = []
        # Convert each raw model box into our simple detection dict.
        for box in results.boxes:
            score = float(box.conf[0])
            # Skip anything the model isn't confident enough about.
            if self.confidence is not None and score < self.confidence:
                continue
            # Convert the box from corner-corner (x1,y1,x2,y2) to (x,y,w,h).
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "label": self.model.names[int(box.cls[0])],
                "confidence": score,
                "box": (x1, y1, x2 - x1, y2 - y1),
            })
        return detections


# --------------------------------------------------------------------------- #
# Detection loop
# --------------------------------------------------------------------------- #

def run():
    """Continuously capture frames and print detections until Ctrl-C."""
    camera = None
    detector = None

    try:
        # Build the model first so a missing-model error happens before we
        # bother opening the camera.
        detector = Detector()
        camera = Camera()

        # Main loop: capture -> detect -> report, paced to TARGET_FPS.
        while True:
            frame = camera.read()
            if frame is None:
                continue                       # no frame this cycle; try again
            detections = detector.detect(frame)
            print(detections)
            if TARGET_FPS:
                time.sleep(1 / TARGET_FPS)     # pace the loop to the target rate

    except KeyboardInterrupt:
        # The normal way to stop the program.
        print("\nStopped by user (Ctrl-C).")
    except FileNotFoundError as e:
        # Model file missing — expected until train.py has produced weights.
        print(f"Cannot start: {e}")
    except Exception as e:
        # Anything else: report it clearly instead of dumping a traceback.
        print(f"Unexpected error while running: {type(e).__name__}: {e}")
    finally:
        # Always release the camera, even after an error, so it isn't left
        # locked for the next program that needs it.
        if camera is not None:
            try:
                camera.close()
            except Exception:
                pass


if __name__ == "__main__":
    run()
