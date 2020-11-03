import cv2
from pyzbar import pyzbar
import numpy as np


class Anafi_Scanning():

    def scanning(self, cv2frame):

        # Use pyzbar to decode the QR code that shown in the frame
        decoded = pyzbar.decode(cv2frame)
        # print(decoded)
        # loop over the detected barcodes
        for barcode in decoded:
            # extract the bounding box location of the barcode and draw
            # the bounding box surrounding the barcode on the image
            (x, y, w, h) = barcode.rect
            cv2.rectangle(cv2frame, (x, y), (x + w, y + h), (0, 255, 0), 4)

            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(cv2frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            return barcodeData