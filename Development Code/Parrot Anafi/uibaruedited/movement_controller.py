import os
import time
import sys

class Movement:
    def __init__(self,drone):
        self.drone = drone
        self.distance = 40

    def droneTakeOff(self):
        self.drone.set_speed(75)
        time.sleep(0.2)
        self.drone.takeoff()
        time.sleep(0.2)
        return

    # function droneLanding
    def droneLanding(self):
        self.takeoff = False
        self.drone.land()
        self.drone.land()
        self.drone.land()
        self.drone.land()
        self.drone.land()
        time.sleep(0.1)
        return        
    
    def droneCW(self, degree):
        print('Rotate right %d m' % degree)
        self.drone.rotate_cw(degree)
        return

    def droneCCW(self, degree):
        print('Rotate left %d degree' % degree)
        self.drone.rotate_ccw(degree)
        return

    def droneMoveForward(self, distance):
        print('forward %d cm' % distance)
        self.drone.move_forward(distance)
        return

    def droneMoveBackward(self, distance):
        print('backward %d cm' % distance)
        self.drone.move_backward(distance)
        return

    def droneMoveLeft(self, distance):
        print('left %d cm' % distance)
        self.drone.move_left(distance)
        return

    def droneMoveRight(self, distance):
        print('right %d cm' % distance)
        self.drone.move_right(distance)
        return

    def droneUp(self, distance):
        up = 'Up %d cm' % distance
        print(up)
        self.drone.move_up(distance)
        return

    def droneDown(self, distance):
        down = 'Down %d cm' % distance
        print(down)
        self.drone.move_down(distance)
        return

