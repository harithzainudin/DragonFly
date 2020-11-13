import requests

class Anafi_Request_Post():

    def readLocation(self):
        locationList = []
        locationFile = 'listOfLocation.txt'

        file = open(locationFile, "r")
        locations = file.readlines()

        for location in locations:
            if location != '' and location != '\n':
                location = location.rstrip()
                locationList.append(location)
        return locationList


    def sendData(self, idData, locationData):
        response = requests.post('https://cpsdragonfly.herokuapp.com/api/item', data={'id': idData, 'location': locationData})
