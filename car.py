#Written by Jianhong Huang
from motor import MotorController
from ultrasonic import Ultrasonic
import time

drive = MotorController()

drive.set_motor_direction(front_left=-1,rear_left=-1,front_right=-1,rear_right=-1)

def drive_fd():
    drive.set_motors(front_left=1000,rear_left=1000,front_right=1000,rear_right=1000)

def drive_bw():
    drive.set_motors(front_left=-1000,rear_left=-1000,front_right=-1000,rear_right=-1000)

def turn_lt():
    drive.set_motors(front_left=-1000,rear_left=-1000,front_right=1000,rear_right=1000)

def turn_rt():
    drive.set_motors(front_left=1000,rear_left=1000,front_right=-1000,rear_right=-1000)

def slide_rt():
    drive.set_motors(front_left=1000,rear_left=-1000,front_right=-1000,rear_right=1000)

def slide_lt():
    drive.set_motors(front_left=-1000,rear_left=1000,front_right=1000,rear_right=-1000)

def slide_d_fd_lt():
    drive.set_motors(front_left=0,rear_left=1000,front_right=1000,rear_right=-0)

def slide_d_bw_lt():
    drive.set_motors(front_left=-1000,rear_left=0,front_right=0,rear_right=-1000)

def slide_d_fd_rt():
    drive.set_motors(front_left=1000,rear_left=0,front_right=0,rear_right=1000)

def slide_d_bw_rt():
    drive.set_motors(front_left=0,rear_left=-1000,front_right=-1000,rear_right=0)

def stop():
    drive.set_motors(front_left=0,rear_left=0,front_right=0,rear_right=0)
