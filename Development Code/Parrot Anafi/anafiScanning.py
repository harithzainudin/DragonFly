import cv2
from pyzbar import pyzbar
import numpy as np

class Anafi_Scanning():

    def startScanning(self, cv2frame):
        decodedData = self.decodeFrame(cv2frame)
        for barcode in decodedData:
            barcodeData = self.drawBoxAndData(cv2frame, barcode)
            return barcodeData

    def decodeFrame(self, cv2frame):
        decoded = pyzbar.decode(cv2frame)
        return decoded

    def drawBoxAndData(self, cv2frame, barcode):
        # extract the bounding box location of the barcode and draw
        # the bounding box surrounding the barcode on the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(cv2frame, (x, y), (x + w, y + h), (0, 255, 0), 4)

        barcodeData, barcodeType = self.find_data_type_and_decode(barcode)

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(cv2frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

        return barcodeData

    def find_data_type_and_decode(self, barcode):
        # the barcode data is a bytes object so if we want to draw it
        # on our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        return barcodeData, barcodeType
    