import time
from servo import Servo
servo = Servo()

def reset_Pos():
    servo.set_servo_pwm('0',120)
    servo.set_servo_pwm('1',80)

def test_Servo(x, y, increment, servon):
    for i in range(x, y, increment):
        servo.set_servo_pwm(servon, i)
        time.sleep(0.01)
