class Status:
    def __init__(self, drone):
        self.drone = drone
        self.now_battery = int(0)
        self.now_height = int(0)
    

    def get_batteryStatus(self):
        self.now_battery = int(self.drone.get_battery())
        str_val = 'Battery : ' + str(self.now_battery) + ' [%]'
        print(str_val)
        return

    def get_heightStatus(self):
        int_val = self.drone.get_height()
        if int_val != 0:
            int_val *=10
            if abs(int_val - self.now_height) < 100:
                self.now_height = int_val


        str_val = 'Altitude : ' + str(self.now_height) + ' [cm]'
        print(str_val)
        return