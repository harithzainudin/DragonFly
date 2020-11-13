import argparse
import cv2
from pyzbar import pyzbar
import numpy as np
import imutils
import datetime
import time
from csv import writer
from anafiRequestPost import Anafi_Request_Post


# FUNCTION - decode barcode
def decode_barcode(frame):
    tempBarcodes = pyzbar.decode(frame)  # find barcode/QR code in frame and decode it
    return tempBarcodes

# FUNCTION - Draw bounding box around barcodes and print data in the frame
def draw_box_data(barcode, frame):
    # extract bounding box location of barcode/QR code and draw bounding box surrounding it
    (x, y, w, h) = barcode.rect
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # convert output(bytes) to string
    tempBarcodeData = barcode.data.decode("utf-8")
    tempBarcodeType = barcode.type

    # draw barcode data and type on the frame/image
    text = "{}".format(tempBarcodeData)
    cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return tempBarcodeData, tempBarcodeType

# FUNCTION - write the barcodeData, timestamps, barcodeType in the CSV file
def write_csv_file(data):
    if data not in found:
        csv.write("{},{}\n".format(datetime.datetime.now(), barcodeData))
        csv.flush()
        found.add(data)

# FUNCTION - scale the window
def scale_window(frame):
    scale_percent = 50
    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
    return resized

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv", help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())

request_post = Anafi_Request_Post()

video = cv2.VideoCapture(0)
print("Starting camera... Please wait")
#video = cv2.VideoCapture(0)

# initialize tarsget and counter for fps
target = 5
counter = 0

# open the output CSV file for writing and initialize the set of barcodes found
csv = open(args["output"], "w")
found = set()

# loop over frames from VideoCapture
while True:
    if counter == target:
        ret, frame = video.read()
        barcodes = decode_barcode(frame)
        if ret:
            for barcode in barcodes:
                barcodeData, barcodeType = draw_box_data(barcode, frame)
                write_csv_file(barcodeData)
            resized = scale_window(frame)
            cv2.imshow("Scanner", resized)
        counter = 0

    else:
        ret = video.grab()
        counter += 1
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

csv.close()
video.release()
cv2.destroyAllWindows()