from flask import Flask, Response, request, jsonify
import cv2
import time
import threading
import subprocess
import os
import json

app = Flask(__name__)

# Global variable to track MiningCar subprocess
mining_process = None
SENSOR_DATA_FILE = '/tmp/mining_sensor_data.json'

# Try to use picamera2 for Raspberry Pi
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    USE_PICAMERA = True
    print("Using picamera2")
except ImportError:
    print("picamera2 not available, using OpenCV")
    USE_PICAMERA = False
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Motor will be initialized when MiningCar starts, not at server startup
motor = None

# Global FPS tracking
frame_count = 0
fps_counter = 0
last_fps_time = time.time()

@app.route('/')
def index():
    with open('/home/pi/interface/main.html', 'r') as f:
        return f.read()

def generate_frames():
    global frame_count, fps_counter, last_fps_time
    
    if USE_PICAMERA:
        while True:
            try:
                frame = picam2.capture_array()
                if frame is not None:
                    frame_count += 1
                    
                    # Calculate FPS every second
                    current_time = time.time()
                    if current_time - last_fps_time >= 1.0:
                        fps_counter = frame_count / (current_time - last_fps_time)
                        frame_count = 0
                        last_fps_time = current_time
                    
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                               frame_bytes + b'\r\n')
                time.sleep(0.03)
            except Exception as e:
                print(f"picamera2 error: {e}")
                time.sleep(0.5)
    else:
        while True:
            ret, frame = camera.read()
            if ret:
                frame_count += 1
                
                # Calculate FPS every second
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    fps_counter = frame_count / (current_time - last_fps_time)
                    frame_count = 0
                    last_fps_time = current_time
                
                frame = cv2.resize(frame, (640, 480))
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                           frame_bytes + b'\r\n')
            else:
                print("Failed to read frame from OpenCV camera")
                time.sleep(0.5)

@app.route('/video_feed')
def video_feed():
    print("Video feed requested")
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/sensor_data')
def sensor_data():
    global fps_counter
    
    # Default values
    distance = None
    motor_speed = None
    battery = 85
    co2_ppm = None
    
    # Try to read from shared sensor data file (written by MiningCar)
    try:
        if os.path.exists(SENSOR_DATA_FILE):
            with open(SENSOR_DATA_FILE, 'r') as f:
                data = json.load(f)
                distance = data.get('distance')
                motor_speed = data.get('motor_speed')
                battery = data.get('battery', 85)
                co2_ppm = data.get('co2_ppm')
    except Exception as e:
        print(f"Error reading sensor data file: {e}")
    
    return {
        'distance': distance,
        'battery': battery,
        'motor_speed': motor_speed,
        'co2_ppm': co2_ppm,
        'fps': round(fps_counter, 1)
    }

@app.route('/api/start_mining', methods=['POST'])
def start_mining():
    global mining_process
    
    data = request.json
    action = data.get('action', 'start')

    if mining_process is not None and mining_process.poll() is not None:
        mining_process = None
    
    if action == 'start' and mining_process is None:
        try:
            # Start MiningCar.py as a subprocess
            mining_process = subprocess.Popen(
                ['python3', '/home/pi/MiningCar.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return jsonify({'running': True, 'message': 'Mining car started'})
        except Exception as e:
            return jsonify({'running': False, 'message': f'Error starting: {str(e)}'})
    
    elif action == 'stop' and mining_process is not None:
        try:
            # Stop MiningCar process
            mining_process.terminate()
            mining_process.wait(timeout=5)
            mining_process = None
            return jsonify({'running': False, 'message': 'Mining car stopped'})
        except subprocess.TimeoutExpired:
            mining_process.kill()
            mining_process = None
            return jsonify({'running': False, 'message': 'Mining car force stopped'})
        except Exception as e:
            mining_process = None
            return jsonify({'running': False, 'message': f'Error stopping: {str(e)}'})
    
    return jsonify({'running': mining_process is not None, 'message': 'No change'})

def start_server():
    """Start the Flask server"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

if __name__ == '__main__':
    start_server()
