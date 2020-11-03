#!/usr/bin/env python

# NOTE: Line numbers of this example are referenced in the user guide.
# Don't forget to update the user guide after every modification of this example.

import csv
import cv2
import math
import os
import queue
import shlex
import subprocess
import tempfile
import threading
import traceback
from anafiStreaming import AnafiStreaming
import socket

import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing
from olympe.messages.ardrone3.Piloting import moveBy
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.PilotingSettings import MaxTilt
from olympe.messages.ardrone3.GPSSettingsState import GPSFixStateChanged

olympe.log.update_config({"loggers": {"olympe": {"level": "WARNING"}}})

DRONE_IP = "192.168.42.1"


class AnafiConnection():

    def __init__(self):
        # Create the olympe.Drone object from its IP address
        self.drone = olympe.Drone(DRONE_IP)
        super().__init__()

    def start(self):
        # Connect the the drone
        self.drone.connect()

        #call start_video fx from anafiStreaming file
        AnafiStreaming.start_video(self, self.drone)

        # Start video streaming
        self.drone.start_video_streaming()


    def stop(self):
        # Properly stop the video stream and disconnect
        self.drone.stop_video_streaming()
        self.drone.disconnect()
        self.h264_stats_file.close()
        

    def fly(self):
        # Takeoff, fly, land, ...
        print("Takeoff if necessary...")
        self.drone(
            FlyingStateChanged(state="hovering", _policy="check")
            | FlyingStateChanged(state="flying", _policy="check")
            | (
                GPSFixStateChanged(fixed=1, _timeout=10, _policy="check_wait")
                >> (
                    TakeOff(_no_expect=True)
                    & FlyingStateChanged(
                        state="hovering", _timeout=10, _policy="check_wait")
                )
            )
        ).wait()
        self.drone(MaxTilt(40)).wait().success()
        for i in range(3):
            print("Moving by ({}/3)...".format(i + 1))
            self.drone(moveBy(10, 0, 0, math.pi, _timeout=20)).wait().success()

        print("Landing...")
        self.drone(
            Landing()
            >> FlyingStateChanged(state="landed", _timeout=5)
        ).wait()
        print("Landed\n")
        

if __name__ == "__main__":
    anafi_connection = AnafiConnection()
    # Start the video stream
    anafi_connection.start()
    # Perform some live video processing while the drone is flying
    anafi_connection.fly()
    # Stop the video stream
    anafi_connection.stop()
