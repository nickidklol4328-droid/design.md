"""


stream_camera.py — live MJPEG camera feed you can watch in a browser.


Run on the Pi:
    python3 stream_camera.py

Then on any device on the same network, open:
    http://<pi-ip>:8000/         (e.g. http://firestingray.local:8000/)

Ctrl+C to stop. Note: only ONE program can use the camera at a time, so stop
this before running app.py (which also needs the camera).

This is the official picamera2 MJPEG example, lightly trimmed.
"""

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

PAGE = """<!DOCTYPE html>
<html><head><title>Pi Camera</title></head>
<body style="margin:0;background:#111;text-align:center">
  <img src="stream.mjpg" style="max-width:100%;height:auto" />
</body></html>"""


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Content-Type",
                             "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception as e:
                logging.warning("Client %s left: %s", self.client_address, e)
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    print("Streaming on http://<pi-ip>:8000/  (Ctrl+C to stop)")
    StreamingServer(("", 8000), StreamingHandler).serve_forever()
finally:
    picam2.stop_recording()
