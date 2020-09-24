#!/usr/bin/python

import socket
import cv2

tello_video = cv2.VideoCapture("udp://@0.0.0.0:11111")

while True:
    try:
        ret, frame = tello_video.read()
        if ret:
            cv2.imshow('Tello', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except Exception as err:
        print(err)

tello_video.release()
cv2.destroyAllWindows()
