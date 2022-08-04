"""
Program based off MR_golf.py. This program changes the device(s) used to 
control the turning of the robot and height of the ball's trajectory from the 
two left and right buttons included on the hub to a wheel attached to a 
rotation sensor. This version also makes use of a light sensor to indicate when 
the user will swing.

The code uses a main loop that contains the shooting mode where the user can 
swing to send an acceleration value to MR. From shooting mode you can access 
turning mode and from turning mode you can access height mode.

Example LEGO golf club build can be found in this folder

Accompanying MR environment: golf_improved; share code: golf_improved

To do
- Add comments to the BLEPeripheral class
"""

from spike import (PrimeHub, LightMatrix, Button, ColorSensor, MotionSensor, 
                   Motor)
from spike.control import wait_for_seconds, wait_until, Timer
from hub import motion
import math, bluetooth, time, struct, random
from micropython import const

# Set up Bluetooth structure data, provided to us by the Mind Render folks and 
# then modified.
# This takes up a lot of the code, to skip to the main content jump to line 
# 155. Remember to change the name of your SPIKE (if you want) on line 109.
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)
_ADV_TYPE_SPECIFIC_DATA = const(0xFF)
_ADV_DATA_COMPANY_ID = const(0xFFFF)

def advertising_payload(limited_disc=False, br_edr=False, name=None, 
                        services=None, appearance=0, free=None):
    payload = bytearray()
    
    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value

    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr 
                                                             else 0x04)),
    )

    if name:
        _append(_ADV_TYPE_NAME, name)

    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)

    if appearance:
        _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))

    return payload

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_MTU_EXCHANGED = const(21)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,
)
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_NOTIFY,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


def won():
    """Display target when player completes the hole."""
    for i in range(50):
        hub.light_matrix.show_image("YES", i*2)

class BLEPeripheral:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = \ 
            self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        rand = random.randint(1, 100)
        golf = "golf" + str(rand)
        self._payload = advertising_payload(name=golf, services=[_UART_UUID])
        self._advertise()

    def is_connected(self):
        return len(self._connections) > 0

    def send(self, data):
        if self.is_connected():
            for handle in self._connections:
                self._ble.gatts_notify(handle, self._handle_rx, data)
                self._ble.gatts_notify(handle, self._handle_tx, data)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Connection", conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            print("Disconnected")
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
                
            # self._advertise()
            print("Disconnected", conn_handle)

        elif event == _IRQ_GATTS_WRITE:
            print('Read')
            conn_handle, value_handle = data

            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx:
                msg = value.decode()
                print("Rx", msg)
                if  msg == "score":
                    won()
                elif msg == "reset":
                    main_loop()

    def _advertise(self):
        self._ble.gap_advertise(500000, adv_data=self._payload)
        # self._ble.gap_advertise(500, "MindRender")
        print("Advertising")

# Initialize hub
hub = PrimeHub()

# Indicate that hub is advertising
hub.light_matrix.show_image('HAPPY')

ble = BLEPeripheral()

# Store the degrees counted by the sensor sensor when program exits turning 
# mode globally so it can be accessed next time the function is called. 
last_degrees_counted1 = 0
def turning_mode():
    """Loop that controls the robot's rotation
    
    The ratio of degrees rotated in real life to degrees rotated in MR is 5:1
    """
    print("turning mode")
    for i in range(50):
        hub.light_matrix.show_image("SQUARE_SMALL", i*2)
    
    # Initialize rotation sensor (make sure to change to whatever port you use)
    sensor = Motor('A')

    global last_degrees_counted1
    
    # Start degrees counted where the function last left off
    sensor.set_degrees_counted(last_degrees_counted1)
    while True:
        # Inverse degree reading to make clockwise rotation of sensor 
        # correspond to clockwise (right) rotation of robot
        degrees = sensor.get_degrees_counted() * -1
        
        # "turn:" tag indicates to MR that incoming data controls turning
        ble.send("turn:" + str(degrees / 5))
        # Sleep time should be tweaked for your system, but for the Microsoft 
        # Surface Studio Laptop we tested on, 0.02 seconds was optimal.
        time.sleep(0.02)

        # Cycles to height_mode when tapped
        if hub.motion_sensor.get_gesture() == "tapped":
            # Records last degrees counted
            last_degrees_counted1 = sensor.get_degrees_counted()
            
            height_mode()
            break

last_degrees_counted2 = 0
def height_mode():
    """Loop that controls the trajectory's height
    
    Overall mechanism and implementation is very similar to that of 
    turning_mode()
    """
    print("height mode")

    # Display double-edged arrow to indicate height mode
    hub.light_matrix.off()
    for i in range(50):
        hub.light_matrix.set_pixel(2, 0, i*2)
        hub.light_matrix.set_pixel(1, 1, i*2)
        hub.light_matrix.set_pixel(3, 1, i*2)

        hub.light_matrix.set_pixel(2, 4, i*2)
        hub.light_matrix.set_pixel(1, 3, i*2)
        hub.light_matrix.set_pixel(3, 3, i*2)

    sensor = Motor('A')

    global last_degrees_counted2

    sensor.set_degrees_counted(last_degrees_counted2)
    while True:
        # Since the height gauge in MR caps goes from 0 to 50 and starts at 
        # 25, degrees are capped at 250 which in turn is divided by ten which 
        # means the actual number sent is limited between 25 and -25.

        degrees = sensor.get_degrees_counted()
        if degrees > 250:
            degrees = 250
            sensor.set_degrees_counted(250)
        elif degrees < -250:
            degrees = -250
            sensor.set_degrees_counted(-250)

        ble.send("height:" + str(degrees / 10))
        time.sleep(0.02)

        # Cycles to main_loop() when tapped
        if hub.motion_sensor.get_gesture() == "tapped":
            last_degrees_counted2 = sensor.get_degrees_counted()
            break

def main_loop():
    # Initialize color sensor (make sure to change to whatever port you use)
    color = ColorSensor('E')

    # Record gesture first time program is run so program doesn't immediately 
    # switch to next mode
    hub.motion_sensor.get_gesture()
    """Loop that is responsible for shooting ball based on accelerometer data"""
    while True:
        print("shooting mode")
        # Display forward arrow every time ball is prepared to be shot
        for i in range(50):
            hub.light_matrix.show_image("ARROW_N", i*2)

        accs = []

        while True:
            # If sensor is covered
            if color.get_reflected_light() > 40:
                print("collecting data")

                # Turn off light matrix to indicate data collecting
                hub.light_matrix.off()

                while color.get_reflected_light() > 40:
                    # Instantaneous x y z acceleration
                    (a_x, a_y, a_z) = motion.accelerometer()

                    # Take magnitude of x, and y acceleration and append to 
                    # array
                    mag = math.sqrt(a_x**2 + a_y**2)
                    accs.append(mag)

                    # Samples acceleration every 0.01 seconds
                    time.sleep(0.01)
            
                try:
                    acc = max(accs)
                    print("Acceleration: ", acc)
                    for i in range(50):
                        hub.light_matrix.show_image("ARROW_N", i*2)
                    ble.send("shoot:" + str(acc))
                # If no acc data was collected before button was released
                except ValueError:
                    print("Hold down the button for longer!")
                    for i in range(50):
                        hub.light_matrix.show_image("ARROW_N", i*2)

            # Cycles to turning_mode() when tapped
            elif hub.motion_sensor.get_gesture() == "tapped":
                turning_mode()
                break

# Minimizes lag during first connection
while True:
    if ble.is_connected():
        time.sleep(1)
        main_loop()

    time.sleep(0.1)