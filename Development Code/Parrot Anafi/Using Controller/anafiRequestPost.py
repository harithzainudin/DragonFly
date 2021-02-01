import requests

class Anafi_Request_Post():

    # read the location from the txt file
    # and return the location back in list
    def readLocation(self):
        locationList = []
        # change the location file path according to your path
        locationFile = 'listOfLocation.txt'

        file = open(locationFile, "r")
        locations = file.readlines()

        # loop over the location and append it to the list
        for location in locations:
            if location != '' and location != '\n':
                location = location.rstrip()
                locationList.append(location)
        return locationList

    # get the list of location from the server
    # and return back the location in list
    def getLocation(self):
        locationList = []
        url = 'https://cpsdragonfly.herokuapp.com/api/location'
        auth = {'Authorization': '$2y$10$.wGNf1JYzHOjRF5xLFovSuEeJGk9XQ4hPaIGvY0D6jpaHR4Ib5/tO'}
        request_get = requests.get(url, headers=auth)

        # load the location in json
        loadLocation = request_get.json()

        # loop over the loaded location and append it to the list,
        # then return the location list in list
        for i in range(len(loadLocation)):
            tempLocation = loadLocation[i]
            locationList.append(tempLocation['location_description'])
        return locationList

    # send the idData and locationData to the server
    def sendData(self, idData, locationData):
        url = 'https://cpsdragonfly.herokuapp.com/api/item'
        auth = {'Authorization': '$2y$10$.wGNf1JYzHOjRF5xLFovSuEeJGk9XQ4hPaIGvY0D6jpaHR4Ib5/tO'}
        data = {'id': idData, 'location': locationData}
        response = requests.post(url, auth=auth, data=data)
