# This source code is only create instance, start.

import status_model
import movement_model
from drone_control_ui import DroneUI

def main():
    drone = status_model.Tellostatus('', 8889)  
    ui = DroneUI(drone,"./img/")
    ui.root.mainloop() 

if __name__ == "__main__":
    main()

#eof

