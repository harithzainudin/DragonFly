import argparse
import cv2
from pyzbar import pyzbar
import numpy as np
import imutils

# construct argument parse and parse the argument
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv", help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())

cap = cv2.VideoCapture("udp://@0.0.0.0:11111")
# opening webcam
# cap = cv2.VideoCapture(0)

# initialize target and counter for fps
target = 5
counter = 0

# loop over frames from VideoCapture
while True:
    if counter == target:
        ret, frame = cap.read()
        barcodes = pyzbar.decode(frame) # find barcode/QR code in frame and decode it

        if ret:
            # loop over detected barcode/QR code
            for barcode in barcodes:
                # extract bounding box location of barcode/QR code and draw bounding box surrounding it
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # convert output(bytes) to string
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type

                # draw barcode data and type on the frame/image
                text = "{} ({})".format(barcodeData, barcodeType)
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # show output
            cv2.imshow("Scanner", frame)
        counter = 0

    else:
        ret = cap.grab()
        counter += 1

        # if `q` key was pressed, break from the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()








