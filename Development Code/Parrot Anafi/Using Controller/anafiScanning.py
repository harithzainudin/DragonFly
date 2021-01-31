import cv2
from pyzbar import pyzbar


class Anafi_Scanning():

    def startScanning(self, cv2frame, focalLength, known_width):
        decodedData = self.decodeFrame(cv2frame)
        for barcode in decodedData:
            barcodeData = self.drawBoxAndData(cv2frame, barcode, focalLength, known_width)
            return barcodeData, known_width

    def decodeFrame(self, cv2frame):
        decoded = pyzbar.decode(cv2frame)
        return decoded

    def drawBoxAndData(self, cv2frame, barcode, focalLength, known_width):
        # extract the bounding box location of the barcode and draw
        # the bounding box surrounding the barcode on the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(cv2frame, (x, y), (x + w, y + h), (0, 255, 0), 4)

        barcodeData, barcodeType = self.find_data_type_and_decode(barcode)

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(cv2frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

        # find distance by calculating the inches from known width
        inches = self.distance_to_camera(known_width, focalLength, w)
        self.draw_distance(cv2frame, inches)

        return barcodeData

    def find_data_type_and_decode(self, barcode):
        # the barcode data is a bytes object so if we want to draw it
        # on our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        return barcodeData, barcodeType

    def distance_to_camera(self, knownWidth, focalLength, perWidth):
        # compute and return the distance from the maker to the camera
        return (knownWidth * focalLength) / perWidth

    def draw_distance(self, frame, inches):
        cv2.putText(frame, "%.2fcm" % inches,
                    (frame.shape[1] - 200, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
                    1.3, (0, 255, 0), 3)
