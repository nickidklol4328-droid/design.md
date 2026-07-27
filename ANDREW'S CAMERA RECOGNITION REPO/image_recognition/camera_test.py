"""
camera_test.py — quick check that the Pi camera works via picamera2.

This uses the same capture path as app.py's Camera class. Run on the Pi:

    python3 camera_test.py        # no sudo needed for the camera

It saves cam_test.jpg (a still) so you can confirm the camera sees the world,
and prints the frame shape so you know it's producing arrays YOLO can use.
View cam_test.jpg in VS Code Remote-SSH, or copy it to your laptop with scp.
"""

import time

from picamera2 import Picamera2

cam = Picamera2()
cam.configure(cam.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}))
cam.start()
time.sleep(2)  # let auto-exposure / white-balance settle

frame = cam.capture_array()      # numpy array, same as Camera.read()
print("captured frame shape:", frame.shape)

cam.capture_file("cam_test.jpg")  # a viewable still
print("saved cam_test.jpg")

cam.close()
