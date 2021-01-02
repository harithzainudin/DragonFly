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
from videoUI import videoUI
from pyzbar import pyzbar

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


class streamVideo(threading.Thread):
    def __init__(self):
        # Create the olympe.Drone object from its IP address
        self.drone = olympe.Drone(DRONE_IP)
        self.tempd = tempfile.mkdtemp(prefix="olympe_streaming_test_")
        print("Olympe streaming example output dir: {}".format(self.tempd))
        self.h264_frame_stats = []
        self.h264_stats_file = open(os.path.join(
            self.tempd, 'h264_stats.csv'), 'w+')
        self.h264_stats_writer = csv.DictWriter(
            self.h264_stats_file, ['fps', 'bitrate'])
        self.h264_stats_writer.writeheader()
        self.frame_queue = queue.Queue()
        self.flush_queue_lock = threading.Lock()

        # assert self.drone(
        #     set_zoom_target(
        #         cam_id=0,
        #         control_mode=0.999,
        #         target=0.5,
        #         _timeout=10,
        #         _no_expect=False,
        #         _float_tol=(1e-07, 1e-09),

        #     )
        # )
        super().__init__()
        super().start()

    def start(self):
        # Connect the the drone
        self.drone.connect()
        self.drone(setPilotingSource(source="Controller")).wait()
        # self.drone.zoom_control_mode(0,1) #level,velocity
        # self.drone.white_balance_temperature(0)
        # self.drone(olympe.enums.camera.set_zoom_target(0,1))
        # You can record the video stream from the drone if you plan to do some
        # post processing.
        self.drone.set_streaming_output_files(
            h264_data_file=os.path.join(self.tempd, 'h264_data.264'),
            h264_meta_file=os.path.join(self.tempd, 'h264_metadata.json'),
            # Here, we don't record the (huge) raw YUV video stream
            # raw_data_file=os.path.join(self.tempd,'raw_data.bin'),
            # raw_meta_file=os.path.join(self.tempd,'raw_metadata.json'),
        )

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

    def yuv_frame_cb(self, yuv_frame):
        """
        This function will be called by Olympe for each decoded YUV frame.
            :type yuv_frame: olympe.VideoFrame
        """
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

    def h264_frame_cb(self, h264_frame):
        """
        This function will be called by Olympe for each new h264 frame.
            :type yuv_frame: olympe.VideoFrame
        """

        # Get a ctypes pointer and size for this h264 frame
        frame_pointer, frame_size = h264_frame.as_ctypes_pointer()

        # For this example we will just compute some basic video stream stats
        # (bitrate and FPS) but we could choose to resend it over an another
        # interface or to decode it with our preferred hardware decoder..

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
        cv2frame = cv2.cvtColor(yuv_frame.as_ndarray(), cv2_cvt_color_flag)

        # Use pyzbar to decode the QR code that shown in the frame
        decoded = pyzbar.decode(cv2frame)
        print(decoded)
        # loop over the detected barcodes
        for barcode in decoded:
            # extract the bounding box location of the barcode and draw
            # the bounding box surrounding the barcode on the image
            (x, y, w, h) = barcode.rect
            cv2.rectangle(cv2frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(cv2frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Use OpenCV to show this frame
        ui = videoUI(cv2frame, "name")
        ui.root.mainloop()
        #cv2.imshow(window_name, cv2frame)
        # cv2.waitKey(1)  # please OpenCV for 1 ms...

    def run(self):
        window_name = "Olympe Streaming Example"
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
        cv2.destroyWindow(window_name)

# hajar edit sini je!
# cari command delay sebelum takeoff n selepas landing , nak 5 sec
    # def fly(self):
    #     assert self.drone(
    #         TakeOff()
    #         >> FlyingStateChanged(state="hovering", _timeout=5)
    #     ).wait().success()

    #     #MOVE UP
    #     assert self.drone(
    #             moveBy(0, 0, -0.2, 0)
    #             >> FlyingStateChanged(state="hovering", _timeout=15)
    #         ).wait().success()
    #     print("---------------------------------------------------SUCCESSFUL UP---------------------------------------------------------------------")

    #     #move left 4 times
    #     for i in range(11):
    #         assert self.drone(
    #             moveBy(0, -0.5, 0, 0)
    #             >> FlyingStateChanged(state="hovering", _timeout=15)
    #         ).wait().success()
    #         print(i, "---------------------------------------------------SUCCESSFUL TO THE LEFT------------------------------------------------")

    #     #MOVE UP
    #     assert self.drone(
    #             moveBy(0, 0, -0.8, 0)
    #             >> FlyingStateChanged(state="hovering", _timeout=15)
    #         ).wait().success()
    #     print("---------------------------------------------------SUCCESSFUL UP---------------------------------------------------------------------")

    #     #MOVE RIGHT 4 TIMES
    #     for j in range(10):
    #         assert self.drone(
    #             moveBy(0, 0.5, 0, 0)
    #             >> FlyingStateChanged(state="hovering", _timeout=15)
    #         ).wait().success()
    #         print(j, "---------------------------------------------------SUCCESSFUL TO THE RIGHT------------------------------------------------")

    #     assert self.drone(Landing()).wait().success()

    def autonomous(self):
        file_name = '/home/dragonfly/DragonFlyReferences/ToyDroneWithAutopilotBarcodeReader1.0/cm.txt'

        f = open(file_name, "r")
        commands = f.readlines()

        for command in commands:
            if command != '' and command != '\n':
                command = command.rstrip()

                if command.find('delay') != -1:
                    sec = float(command.partition('delay')[2])
                    print('delay %s' % sec)
                    time.sleep(sec)
                    pass

                else:
                    self.send_command(command)

    def send_command(self, command):
        newCommand = command.split()

        if(newCommand[0] == 'Forward') or (newCommand[0] == 'Backward'):
            self.move_ForwardBackward(newCommand[1])

        if(newCommand[0] == 'Left') or (newCommand[0] == 'Right'):
            self.move_RightLeft(newCommand[1])

        if(newCommand[0] == 'Up') or (newCommand[0] == 'Down'):
            self.move_UpDown(newCommand[1])

        if(newCommand[0] == 'Rotate'):
            self.rotate(newCommand[1])

        if(newCommand[0] == 'Takeoff'):
            self.takeoff()

        if(newCommand[0] == 'Land'):
            self.land()

        return

    def takeoff(self):
        assert self.drone(
            TakeOff()
            >> FlyingStateChanged(state="hovering", _timeout=5)
        ).wait().success()
        print("---------------------------------------------------SUCCESSFUL TAKEOFF---------------------------------------------------------------------")

        return

    def land(self):
        assert self.drone(Landing()).wait().success()
        print("---------------------------------------------------SUCCESSFUL LAND---------------------------------------------------------------------")

    def move_ForwardBackward(self, range):
        distance = float(range)
        assert self.drone(
            moveBy(distance, 0, 0, 0)
            >> FlyingStateChanged(state="hovering", _timeout=5)
        ).wait().success()
        print("---------------------------------------------SUCCESSFUL FORWARD/BACKWARD---------------------------------------------------------------------")

        return

    def move_RightLeft(self, range):
        distance = float(range)
        assert self.drone(
            moveBy(0, distance, 0, 0)
            >> FlyingStateChanged(state="hovering", _timeout=5)
        ).wait().success()
        print("---------------------------------------------------SUCCESSFUL RIGHT/LEFT---------------------------------------------------------------------")

        return

    def move_UpDown(self, range):
        distance = float(range)
        assert self.drone(
            moveBy(0, 0, distance, 0)
            >> FlyingStateChanged(state="hovering", _timeout=5)
        ).wait().success()
        print("---------------------------------------------------SUCCESSFUL UP/DOWN---------------------------------------------------------------------")

        return

    def rotate(self, range):
        distance = float(range)
        assert self.drone(
            moveBy(0, 0, 0, distance)
            >> FlyingStateChanged(state="hovering", _timeout=5)
        ).wait().success()
        print("---------------------------------------------------SUCCESSFUL ROTATE/YAW---------------------------------------------------------------------")

        return

    def postprocessing(self):
        # Convert the raw .264 file into an .mp4 file
        h264_filepath = os.path.join(self.tempd, 'h264_data.264')
        mp4_filepath = os.path.join(self.tempd, 'h264_data.mp4')
        subprocess.run(
            shlex.split('ffmpeg -i {} -c:v copy -y {}'.format(
                h264_filepath, mp4_filepath)),
            check=True
        )

        # Replay this MP4 video file using the default video viewer (VLC?)
        # subprocess.run(
        #     shlex.split('xdg-open {}'.format(mp4_filepath)),
        #     check=True
        # )
