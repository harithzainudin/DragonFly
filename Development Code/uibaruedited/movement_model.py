# This source code from https://github.com/dji-sdk/Tello-Python, then amended.
# Thank you for the open source community.

from struct import Struct
import socket
import threading
import time
import numpy as np
import libh264decoder

CMD_REQ_IFRAME =(0xcc, 0x58, 0x00, 0x7c, 0x60, 0x25, 0x00, 0x00, 0x00, 0x6c, 0x95)
STATUS_TIMEOUT = (float)(0.5)

class Tellostatus:
    
    def takeoff(self):
        self.send_command('takeoff')
        return

    def set_speed(self, speed):
        self.send_command('speed %s' % speed)
        return

    def rotate_cw(self, degrees):
        self.send_command('cw %s' % degrees)
        return

    def rotate_ccw(self, degrees):
        self.send_command('ccw %s' % degrees)
        return

    def get_height(self):
#       self.send_command('height?')
        return self.last_height

    def get_battery(self):
#       self.send_command('battery?')
        return self.last_battery

    def land(self):
        self.send_command('land')
        return

    def move(self, direction, distance):
        self.send_command('%s %s' % (direction, distance))
        return

    def move_backward(self, distance):
        self.move('back', distance)
        return

    def move_down(self, distance):
        self.move('down', distance)
        return

    def move_forward(self, distance):
        self.move('forward', distance)
        return

    def move_left(self, distance):
        self.move('left', distance)
        return

    def move_right(self, distance):
        self.move('right', distance)
        return

    def move_up(self, distance):
        self.move('up', distance)
        return

    def req_iframe(self):
        self.send_command('iframe')
        return

#eof

