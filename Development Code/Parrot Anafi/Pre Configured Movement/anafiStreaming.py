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
from anafiRequestPost import Anafi_Request_Post
from anafiScanning import Anafi_Scanning

import olympe
import olympe_deps as od
from olympe.messages.ardrone3.Piloting import TakeOff, Landing
from olympe.messages.ardrone3.Piloting import moveBy
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.PilotingSettings import MaxTilt
from olympe.messages.ardrone3.GPSSettingsState import GPSFixStateChanged
from olympe.messages.skyctrl.CoPiloting import setPilotingSource

olympe.log.update_config({"loggers": {"olympe": {"level": "WARNING"}}})

DRONE_IP = "192.168.42.1"
CONTROLLER_IP = "192.168.53.1"


class AnafiConnection(threading.Thread):

    def __init__(self):
        # Create the olympe.Drone object from its IP address
        self.drone = olympe.Drone(
            DRONE_IP, drone_type=od.ARSDK_DEVICE_TYPE_ANAFI4K)

        self.tempd = tempfile.mkdtemp(prefix="olympe_streaming_test_")

        self.h264_frame_stats = []
        self.h264_stats_file = open(os.path.join(
            self.tempd, 'h264_stats.csv'), 'w+')
        self.h264_stats_writer = csv.DictWriter(
            self.h264_stats_file, ['fps', 'bitrate'])
        self.h264_stats_writer.writeheader()
        self.frame_queue = queue.Queue()
        self.flush_queue_lock = threading.Lock()

        self.request_post = Anafi_Request_Post()
        self.scanning_decode = Anafi_Scanning()
        self.listOfLocation = self.request_post.readLocation()
        print(self.listOfLocation)
        self.currentLocation = None
        self.currentLocationStatus = False
        self.barcodeDataList = []

        # get location from server
        

        super().__init__()
        print("Initialization succesfull, Drone is ready to FLY")
        super().start()

    def start(self):
        # Connect the the drone
        self.drone.connect()

        # Setup your callback functions to do some live video processing
        self.drone.set_streaming_callbacks(
            raw_cb=self.yuv_frame_cb,
            h264_cb=self.h264_frame_cb,
            start_cb=self.start_cb,
            end_cb=self.end_cb,
            flush_raw_cb=self.flush_cb,
        )
        # Start video streaming
        self.drone.start_video_streaming()

    def stop(self):
        # Properly stop the video stream and disconnect
        self.drone.stop_video_streaming()
        self.drone.disconnect()
        self.h264_stats_file.close()

    # This function will be called by Olympe for each decoded YUV frame.
    def yuv_frame_cb(self, yuv_frame):

        yuv_frame.ref()
        self.frame_queue.put_nowait(yuv_frame)

    def flush_cb(self):
        with self.flush_queue_lock:
            while not self.frame_queue.empty():
                self.frame_queue.get_nowait().unref()
        return True

    def start_cb(self):
        pass

    def end_cb(self):
        pass

    # This function will be called by Olympe for each new h264 frame.
    def h264_frame_cb(self, h264_frame):

        # Get a ctypes pointer and size for this h264 frame
        frame_pointer, frame_size = h264_frame.as_ctypes_pointer()

        # Compute some stats and dump them in a csv file
        info = h264_frame.info()
        frame_ts = info["ntp_raw_timestamp"]
        if not bool(info["h264"]["is_sync"]):
            if len(self.h264_frame_stats) > 0:
                while True:
                    start_ts, _ = self.h264_frame_stats[0]
                    if (start_ts + 1e6) < frame_ts:
                        self.h264_frame_stats.pop(0)
                    else:
                        break
            self.h264_frame_stats.append((frame_ts, frame_size))
            h264_fps = len(self.h264_frame_stats)
            h264_bitrate = (
                8 * sum(map(lambda t: t[1], self.h264_frame_stats)))
            self.h264_stats_writer.writerow(
                {'fps': h264_fps, 'bitrate': h264_bitrate})

    def show_yuv_frame(self, window_name, yuv_frame):
        # the VideoFrame.info() dictionary contains some useful information
        # such as the video resolution
        info = yuv_frame.info()
        height, width = info["yuv"]["height"], info["yuv"]["width"]

        # yuv_frame.vmeta() returns a dictionary that contains additional
        # metadata from the drone (GPS coordinates, battery percentage, ...)

        # convert pdraw YUV flag to OpenCV YUV flag
        cv2_cvt_color_flag = {
            olympe.PDRAW_YUV_FORMAT_I420: cv2.COLOR_YUV2BGR_I420,
            olympe.PDRAW_YUV_FORMAT_NV12: cv2.COLOR_YUV2BGR_NV12,
        }[info["yuv"]["format"]]

        # yuv_frame.as_ndarray() is a 2D numpy array with the proper "shape"
        # i.e (3 * height / 2, width) because it's a YUV I420 or NV12 frame

        # Use OpenCV to convert the yuv frame to RGB
        self.cv2frame = cv2.cvtColor(
            yuv_frame.as_ndarray(), cv2_cvt_color_flag)

        # scan the barcode, draw box and data in the frame
        self.barcodeData = self.scanning_decode.startScanning(self.cv2frame)

        # if there is no data in the barocodeData. contain None
        if not self.barcodeData:
            pass
        elif (self.barcodeData in self.listOfLocation):
            self.currentLocation = self.barcodeData
            self.currentLocationStatus = True
        else:
            if (self.barcodeData not in self.barcodeDataList) and (self.currentLocationStatus == True):
                # print("data tengh scan, xde dalam list")
                self.barcodeDataList.append(self.barcodeData)
                self.request_post.sendData(self.barcodeData, self.currentLocation)            

        # Use OpenCV to show this frame
        cv2.imshow(window_name, self.cv2frame)
        cv2.waitKey(1)  # please OpenCV for 1 ms...

    def run(self):
        window_name = "Olympe Streaming"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        main_thread = next(
            filter(lambda t: t.name == "MainThread", threading.enumerate())
        )
        
        while main_thread.is_alive():
            with self.flush_queue_lock:
                try:
                    yuv_frame = self.frame_queue.get(timeout=0.01)
                except queue.Empty:
                    continue
                try:
                    self.show_yuv_frame(window_name, yuv_frame)
                    
                except Exception:
                    # We have to continue popping frame from the queue even if
                    # we fail to show one frame
                    traceback.print_exc()
                    
                finally:
                    # Don't forget to unref the yuv frame. We don't want to
                    # starve the video buffer pool
                    yuv_frame.unref()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                anafi_connection.stop()
       
        cv2.destroyWindow(window_name)

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
