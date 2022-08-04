# BLE
This method is pretty straightforward, you just build out your LEGO device and then run some code. Note that every python file in this folder is meant to run on a LEGO SPIKE Prime Hub. Also note that, for our purposes, SPIKE and hub refer to the same thing.

File descriptions:
- MR_car.py: SPIKE code that turns the hub into a gyroscope based steering wheel/accelerator that sends data to MR
- MR_golf.py: SPIKE code that turns the hub into a golf club and sends data to MR
- MR_golf_improved.py: SPIKE code that turns the hub into a golf club and sends data to MR with additional input from a motor/position sensor and color sensor
- SpikeSendBLE.py: SPIKE code that turns the hub into a steering wheel/accelerator that sends data to MR
- SpikeSendReceiveBLE.py: SpikeSendBLE.py but can receive data (for force feedback)
- SpikeSendReceiveBLE_3.py: SpikeSendBLE.py but ported to Atlantis, as of right now BLE on there is weird and not working properly