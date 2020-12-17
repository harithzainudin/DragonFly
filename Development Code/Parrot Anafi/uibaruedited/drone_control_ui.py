# This source code is create UI with Tkinter, glue a some components.

import sys
import numpy as np
from PIL import Image
from PIL import ImageTk
import Tkinter as tki

from Tkinter import Button, Frame, Label, OptionMenu, Scale, Text, Toplevel
# from Tkinter import *
import threading
import pytz
import datetime
import cv2
import os
import time
from drone_ar_flight import Drone_AR_Flight
import platform
from movement_controller import Movement
from status_controller import Status

TIMEZONE = 'Asia/Kuala_Lumpur'


class DroneUI:
    def __init__(self, drone, outputpath):
        self.drone = drone
        self.ar_cmd = 'MANUAL'
        self.ar_val = 0

        self.auto_pilot = False
        self.takeoff = False
        self.distance = 40
        self.degree = 10
        self.FRAME_W = 1300
        self.FRAME_H = 370

        self.now_battery = int(0)
        self.now_height = int(0)

        #GET FROM THE MOVEMENT N STATUS CONTROLLER file
        self.movement = Movement(drone)
        self.status = Status(drone)

        # hijau dekat screen variable initiliaze dia
        self.drone_ar = Drone_AR_Flight()
        self.frame_no = 0
        self.frame_lock = threading.Lock()
        self.blank_frame = np.zeros((self.FRAME_H, self.FRAME_W, 3), np.uint8)
        self.frame = self.blank_frame

        self.root = tki.Tk()

        topFrame = Frame(self.root)
        topFrame.pack(side="top")

        #ui frame hitam
        self.image = Image.fromarray(self.frame)
        self.image = ImageTk.PhotoImage(self.image)

        self.panel = Label(topFrame, image=self.image)
        self.panel.image = self.image
        self.panel.pack( padx=5, pady=5) #frame hitam berada di atas 


        bottomFrame = Frame(self.root)
        bottomFrame.pack(side="bottom")

        leftFrame = Frame(bottomFrame)
        leftFrame.pack(side="left")

         #if code dekat atas, in ui dia dekat bawah sekali
         # ui list qr (paling bawah sekali)
        self.barcode_str = tki.StringVar()
        self.barcode_str.set('QR List')
        # self.barcode_indicate = tki.Label(textvariable=self.barcode_str, width=5, height=5,  anchor=tki.W, justify='left',
        #                                   foreground='#000000', background='#ffffff', font=("",12))
        # self.barcode_indicate.pack(fill="both", anchor=tki.W)
        self.barcode_latest_str = ''

        # buat dalam text. kalau dalam label nanti dia tak jadi list, dia akan keep on replace
        self.qr_txt = Text(leftFrame, height=15, width=35)
        self.qr_txt.pack(fill="both", expand="yes", padx=10, pady=10, side="bottom")

         # ui altitude percent
        self.height_str = tki.StringVar()

        # get height status kat bawah ni dari status controller file
        self.height_str.set(
            'Altitude : ' + str(self.status.get_heightStatus()) + ' [cm]')
        self.height_indicate = Label(leftFrame, textvariable=self.height_str, width=35, anchor=tki.W, justify='left',
                                         background='#d5d8dc', foreground='#000000', font=("", 14), relief="flat", borderwidth=2)
        self.height_indicate.pack( anchor=tki.W, side="bottom")


       # ui battery level
        self.battery_str = tki.StringVar()

        # get battery status kat bawah ni dari status controller file
        self.battery_str.set(
            'Battery : ' + str(self.status.get_batteryStatus()) + ' [%]')
        self.battery_indicate = Label(leftFrame, textvariable=self.battery_str, width=35, anchor=tki.W, justify='left',
                                          background='#d5d8dc', foreground='#000000', font=("", 14), relief="flat", borderwidth=2)
        self.battery_indicate.pack( anchor=tki.W, side="bottom")

        
        middleFrame = Frame(bottomFrame)
        middleFrame.pack(side="left")

        drones = ["DJI TELLO",
                     "PARROT ANAFI"]

        tkvarq = tki.StringVar(middleFrame)
        tkvarq.set(drones[0])
        question_menu = OptionMenu(middleFrame,tkvarq, *drones)
        question_menu.pack( padx=10, pady=10)

        # ui w s a d up down left right ...
        self.tmp_f = Frame(middleFrame, width=5, height=2)
        self.tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
        self.tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        self.tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        self.tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        self.tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        self.tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        self.tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        self.tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        self.tmp_f.pack(side="bottom")
        self.tmp_f.focus_set()

        self.hist_txt = Text(middleFrame, height=15, width=45)
        self.hist_txt.pack(fill='both',expand='yes', padx=10, pady=10,side="bottom")


        # clicked = tki.StringVar()
        # drop = chooseDrone(middleFrame,clicked, "DJI Tello","Anafi")
        # drop.pack()

        rightFrame = Frame(bottomFrame)
        rightFrame.pack(side="right")



        # ui button land
        self.btn_landing = Button(
            rightFrame, text="Land", relief="raised", bg="black", fg="white", command=self.droneLanding, height=3)
        self.btn_landing.pack( fill="both",
                              expand="yes", padx=5, pady=5, side="bottom")

        # ui button takeoff
        self.btn_takeoff = Button(
            rightFrame, text="Takeoff", relief="raised", bg="black", fg="white", command=self.droneTakeOff, height=3)
        self.btn_takeoff.pack( fill="both",
                              expand="yes", padx=5, pady=5, side="bottom")

         # ui button command
        self.btn_command = Button(
            rightFrame, text="Command", relief="raised", bg="black", fg="white", command=self._autoCommand, height=3)
        self.btn_command.pack( fill="both",
                              expand="yes", padx=5, pady=5, side="bottom")

        #ui instruction
        self.text1 = Label(rightFrame, text=
                               'W - Up\t\tArrow U - Forward\n'
                               'S - Down\t\tArrow D - Backward\n'
                               'A - Rotate Left\tArrow L - Left\n'
                               'D - Rotate Right\tArrow R - Right\n',
                               justify="left", foreground='#000000', background='#f7f9f9', width=50, relief="groove", borderwidth=8)
        self.text1.pack(side="bottom")

        # nama tab atas
        self.root.wm_title("Drone UI")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        self.video_thread_stop = threading.Event()
        self.video_thread = threading.Thread(target=self._video_loop, args=())
        self.video_thread.daemon = True
        self.video_thread.start()

        self.get_GUI_Image_thread_stop = threading.Event()
        self.get_GUI_Image_thread = threading.Thread(target=self._getGUIImage)
        self.get_GUI_Image_thread.daemon = True
        self.get_GUI_Image_thread.start()

        self.sending_command_thread_stop = threading.Event()
        self.sending_command_thread = threading.Thread(
            target=self._sendingCommand)
        self.sending_command_thread.daemon = True
        self.sending_command_thread.start()

        self._add_log('Command display  here...')

    def _video_loop(self):
        time.sleep(0.5)
        while not self.video_thread_stop.is_set():
            if hasattr(self.drone, 'read'):
                self.frame_lock.acquire()
                try:
                    self.frame = self.drone.read_video_frame()
                except:
                    print('Err : caught a RuntimeError')
                self.frame_lock.release()
            time.sleep(0.011)

        return

    def _getGUIImage(self):
        while not self.get_GUI_Image_thread_stop.is_set():
            if hasattr(self.drone, 'read_video_frame'):
                self.frame_lock.acquire()
                try:
                    self.frame = self.drone.read_video_frame()
                except:
                    print('Err : caught a RuntimeError')
                self.frame_lock.release()

            if self.frame is None or self.frame.size == 0:
                continue

            if self.frame.shape[1] != 960:
                continue

            if self.get_GUI_Image_thread_stop.is_set():
                break

            self.frame_lock.acquire()
            self.drone_ar.renew_frame(
                self.frame, self.frame_no, self.now_height, self.ar_cmd, self.ar_val)
            self.frame_no += 1
            self.image = Image.fromarray(self.frame)
            #self.drone_ar.draw_txt(self.image, self.ar_cmd, self.ar_val)
            self.frame_lock.release()

            self.image = ImageTk.PhotoImage(self.image)
            self.panel.configure(image=self.image)
            self.panel.image = self.image
            time.sleep(0.033)

        return

    def _sendingCommand(self):
        poling_counter = 0
        while not self.sending_command_thread_stop.is_set():
            # and toggle == 0:
            if self.takeoff and (poling_counter % 12) == 0 and self.auto_pilot:
                self.ar_cmd, self.ar_val = self.drone_ar.get_command()
                if self.ar_cmd == 'up':
                    self.movement.droneUp(self.ar_val)
                elif self.ar_cmd == 'down':
                    self.movement.droneDown(self.ar_val)
                elif self.ar_cmd == 'forward':
                    self.movement.droneMoveForward(self.ar_val)
                elif self.ar_cmd == 'back':
                    self.movement.droneMoveBackward(self.ar_val)
                elif self.ar_cmd == 'left':
                    self.movement.droneMoveLeft(self.ar_val)
                elif self.ar_cmd == 'right':
                    self.movement.droneMoveRight(self.ar_val)
                elif self.ar_cmd == 'rotateLeft':
                    self.movement.droneCCW(self.ar_val)
                elif self.ar_cmd == 'rotateRight':
                    self.movement.droneCW(self.ar_val)
                elif self.ar_cmd == 'stay':
                    print('>> stay')

# #function time- malaysia
#     def _add_log(self, arg_log):
#         now = datetime.datetime.now(pytz.timezone(TIMEZONE))
#         nowtimestr = str(now.strftime('%X'))
#         logstr = nowtimestr + ' : [' + arg_log + ']\n'
#         self.hist_txt.insert(tki.END, logstr)
#         self.hist_txt.see(tki.END)
#         return

    # yang kuar barcode
            tmpstr = self.drone_ar.get_latest_barcode()
            if self.barcode_latest_str != tmpstr:
                self.barcode_latest_str = tmpstr
                self.barcode_str.set(tmpstr)
                qr = tmpstr + '\n'  # nak suh dia tambah next qr link
                self.qr_txt.insert(tki.END, qr)  # dia masukkan qr link
                # for the command auto scroll to latest
                self.qr_txt.see(tki.END)

                # self._add_log(tmpstr)

            self.status.get_batteryStatus()
            self.status.get_heightStatus()
            poling_counter += 1
            time.sleep(0.3)

        return
        
# function droneTakeoff

    def droneTakeOff(self):
        self._add_log('takeoff')
        takeoff_response = None
        self.takeoff = True
        self.movement.droneTakeOff()
        return

# function droneLanding
    def droneLanding(self):
        self.takeoff = False
        self._add_log('landing ...')
        self.movement.droneLanding()
        return

    def _autoPilot(self):
        if self.auto_pilot:
            self.ar_cmd = 'MANUAL'
            self.auto_pilot = False
        else:
            self.auto_pilot = True
        return

# function command button
    def _autoCommand(self):
        file_name = '/home/dragonfly/DragonFlyReferences/ToyDroneWithAutopilotBarcodeReader1.0/cm.txt'

        f = open(
            '/home/dragonfly/DragonFlyReferences/ToyDroneWithAutopilotBarcodeReader1.0/cm.txt', "r")
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
                    self.drone.send_command(command)
                    self._add_log(command)
        
        return

    def on_keypress_w(self, event):
        self.distance = 40
        up = 'Up %d cm' % self.distance
        self._add_log(up)
        self.movement.droneUp(self.distance)
        return

    def on_keypress_s(self, event):
        self.distance = 20
        down = 'Down %d cm' % self.distance
        self._add_log(down)
        self.movement.droneDown(self.distance)
        return

    def on_keypress_a(self, event):
        self.degree = 10
        self._add_log('Rotate left %d degree' % self.degree)
        self.movement.droneCCW(self.degree)
        return

    def on_keypress_d(self, event):
        self.degree = 10
        self._add_log('Rotate right %d m' % self.degree)
        self.movement.droneCW(self.degree)
        return

    def on_keypress_up(self, event):
        self.distance = 20
        self._add_log('forward %d cm' % self.distance)
        self.movement.droneMoveForward(self.distance)
        return

    def on_keypress_down(self, event):
        self.distance = 20
        self._add_log('backward %d cm' % self.distance)
        self.movement.droneMoveBackward(self.distance)
        return

    def on_keypress_left(self, event):
        self.distance = 20
        self._add_log('left %d cm' % self.distance)
        self.movement.droneMoveLeft(self.distance)
        return

    def on_keypress_right(self, event):
        self.distance = 20
        self._add_log('right %d cm' % self.distance)
        self.movement.droneMoveRight(self.distance)
        return

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()
        return

# function close the ui
    def onClose(self):
        print('closing 1...')
        self.sending_command_thread_stop.set()
        self.sending_command_thread.join(1)
        if self.sending_command_thread.is_alive():
            print('sys exit()...')
            sys.exit()

        print('closing 2...')
        self.video_thread_stop.set()
        self.video_thread.join(1)
        if self.video_thread.is_alive():
            print('sys exit()...')
            sys.exit()

        print('closing 3...')
        self.get_GUI_Image_thread_stop.set()
        self.get_GUI_Image_thread.join(1)
        if self.get_GUI_Image_thread.is_alive():
            print('sys exit()...')
            sys.exit()

        print('closing 4...')
        self.drone.close()
        del self.drone
        self.root.quit()
        return

# function time- malaysia
    def _add_log(self, arg_log):
        now = datetime.datetime.now(pytz.timezone(TIMEZONE))
        nowtimestr = str(now.strftime('%X'))
        logstr = nowtimestr + ' : [' + arg_log + ']\n'
        self.hist_txt.insert(tki.END, logstr)
        self.hist_txt.see(tki.END)  # for the command auto scroll to latest
        return

# eof
