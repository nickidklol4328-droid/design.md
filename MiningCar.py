#INITIALLY WRITTEN BY HAND, ASSISTED BY AI
import car
from ultrasonic import Ultrasonic
import servemenya
import time
import json
import signal
import sys
import os
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent / "Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi" / "Code" / "Server"
if str(SERVER_DIR) not in sys.path:
    sys.path.append(str(SERVER_DIR))

try:
    from adc import ADC
except Exception as e:
    ADC = None
    print(f"ADC module unavailable: {e}")

robot = car

gasppmlvl = 0

dist_sensor = Ultrasonic()
serv = servemenya

capped = 60
SENSOR_DATA_FILE = '/tmp/mining_sensor_data.json'
running = True

adc_reader = None
try:
    if ADC is not None:
        adc_reader = ADC()
except Exception as e:
    print(f"Gas sensor ADC init failed: {e}")
    adc_reader = None

GAS_SENSOR_CHANNEL = int(os.environ.get('GAS_SENSOR_CHANNEL', '3'))
GAS_SENSOR_SCALE = float(os.environ.get('GAS_SENSOR_SCALE', '1000'))
BATTERY_CHANNEL = int(os.environ.get('BATTERY_CHANNEL', '2'))
BATTERY_MIN_VOLTAGE = float(os.environ.get('BATTERY_MIN_VOLTAGE', '6.0'))
BATTERY_MAX_VOLTAGE = float(os.environ.get('BATTERY_MAX_VOLTAGE', '8.4'))


def read_battery_percentage():
    """Estimate battery percentage from the ADC voltage reading."""
    if adc_reader is None:
        return None
    try:
        raw_voltage = adc_reader.read_adc(BATTERY_CHANNEL)
        if raw_voltage is None:
            return None
        actual_voltage = raw_voltage * (3 if adc_reader.pcb_version == 1 else 2)
        if actual_voltage <= BATTERY_MIN_VOLTAGE:
            return 0
        if actual_voltage >= BATTERY_MAX_VOLTAGE:
            return 100
        pct = int(round(((actual_voltage - BATTERY_MIN_VOLTAGE) / (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)) * 100))
        return max(0, min(100, pct))
    except Exception as e:
        print(f"Error reading battery: {e}")
        return None


def read_gas_sensor():
    """Read a rough CO2-style reading from the gas sensor when available."""
    if adc_reader is None:
        return None
    try:
        voltage = adc_reader.read_adc(GAS_SENSOR_CHANNEL)
        if voltage is None:
            return None
        ppm = round((voltage / 5.2) * GAS_SENSOR_SCALE, 1)
        gasppmlvl = ppm
        return ppm
    except Exception as e:
        print(f"Error reading gas sensor: {e}")
        return None


def write_sensor_data(distance=None, motor_speed=0, battery=None):
    """Write sensor data to shared file for web interface to read"""
    try:
        if distance is None:
            distance = dist_sensor.get_distance()
        if battery is None:
            battery = read_battery_percentage()
        gas_ppm = read_gas_sensor()
        data = {
            'distance': distance,
            'motor_speed': motor_speed,
            'battery': battery,
            'co2_ppm': gas_ppm
        }
        with open(SENSOR_DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing sensor data: {e}")


def stop_robot():
    global running
    running = False
    try:
        robot.stop()
    except Exception as e:
        print(f"Error stopping robot: {e}")
    write_sensor_data(distance=0, motor_speed=0)


def signal_handler(signum, frame):
    print(f"Received signal {signum}, stopping robot")
    stop_robot()
    sys.exit(0)


def driveit():
    while running:
        
        dist = dist_sensor.get_distance()
        print(f"Current distance is {dist} cm")
        if dist is None:
            print("Distance read failed, stopping")
            stop_robot()
            return False

        write_sensor_data(distance=dist, motor_speed=1000)
        robot.drive_fd()
        
        if dist < capped:
            print("I stopped!")
            robot.stop()
            return True
        time.sleep(0.2)
    return False

def flash_dist():
    dist = dist_sensor.get_distance()
    write_sensor_data()
    return dist

#OLD WAY OF HAVING ROBOT TURN AROUND
# def whichway():
#     #left
#     serv.reset_Pos()
#     left = 0
#     right = 0
#     robot.turn_lt()
#     time.sleep(.5)
#     robot.stop()
#     time.sleep(.5)
#     left = flash_dist()
#     time.sleep(.5)
#     robot.turn_rt()
#     time.sleep(.5)
#     robot.stop()
#     time.sleep(.5)
#     #right
#     robot.turn_rt()
#     time.sleep(.5)
#     robot.stop()
#     time.sleep(.5)
#     right = flash_dist()
#     time.sleep(.5)
#     robot.turn_lt()
#     time.sleep(.5)
#     robot.stop()

#     if left is None or right is None:
#         print("Direction check failed, stopping")
#         stop_robot()
#         return

#     if left > right:
#         robot.turn_lt()
#     elif right > left:
#         robot.turn_rt()
#     else:
#         robot.turn_lt()

#     time.sleep(0.5)
#     robot.stop()

def whichway():
    #left
    serv.reset_Pos()
    left = 0
    right = 0
    serv.test_Servo(120, 40, -1, "0")
    time.sleep(0.5)
    left = flash_dist()
    time.sleep(0.5)
    serv.reset_Pos()
    #right
    time.sleep(.5)
    serv.test_Servo(120, 200, 1, "0")
    time.sleep(0.5)
    right = flash_dist()
    time.sleep(0.5)
    serv.reset_Pos()

    if left is None or right is None:
        print("Direction check failed, stopping")
        stop_robot()
        return

    if left > right:
        robot.turn_lt()
    elif right > left:
        robot.turn_rt()
    else:
        robot.turn_lt()

    time.sleep(0.5)
    robot.stop()

def main():
    serv.reset_Pos()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    driveit()
    try:
        while running:
            if not driveit():
                break
            whichway()
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        stop_robot()


if __name__ == '__main__':
    main()
