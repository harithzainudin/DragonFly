#!/usr/bin/python

import socket
import cv2
import pyzbar.pyzbar as pyzbar


cap = cv2.VideoCapture("udp://@0.0.0.0:11111")
font = cv2.FONT_HERSHEY_PLAIN

target = 5
counter = 0

while True:
    try:
        if counter == target:
            ret, frame = cap.read()
            decodedObjects = pyzbar.decode(frame)
            if ret:
                for obj in decodedObjects:
                    print("Data", obj.data)
                    cv2.putText(frame, str(obj.data), (50, 50), font, 2, (255, 0, 0), 3)
                cv2.imshow('Tello', frame)
            counter = 0
        else:
            ret = cap.grab()
            counter += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as err:
        print(err)

cap.release()
cv2.destroyAllWindows()
