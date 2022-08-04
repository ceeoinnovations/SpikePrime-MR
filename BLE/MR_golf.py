"""
Program that connects to Mind Render via bluetooth and controls a character 
in a wii-sports-esque golfing game using the hub's built-in accelerometer.

Accompanying MR environment: golf_spike; share code: golf_spike

To do
- Add comments to the BLEPeripheral class
"""

from spike import (PrimeHub, LightMatrix, Button, StatusLight, ForceSensor, 
                   MotionSensor, Speaker, ColorSensor, Motor, MotorPair)
from spike.control import wait_for_seconds, wait_until, Timer
from hub import motion
import math, bluetooth, time, struct, random
from micropython import const

# Set up Bluetooth structure data, provided to us by the Mind Render folks and 
# then modified.
# This takes up a lot of the code, to skip to the main content jump to line 
# 146. Remember to change the name of your SPIKE (if you want) on line 99.
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

def winning_display():
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
            for i in range(50):
                hub.light_matrix.show_image("ARROW_N", i*2)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            print("Disconnected")
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
                
            #self._advertise()
            print("Disconnected", conn_handle)

        elif event == _IRQ_GATTS_WRITE:
            print('Read')
            conn_handle, value_handle = data

            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx:
                msg = value.decode()
                print("Rx", msg)
                if  msg == "score":
                    winning_display()


    def _advertise(self):
        self._ble.gap_advertise(500000, adv_data=self._payload)
        #self._ble.gap_advertise(500, "MindRender")
        print("Advertising")

# Initialize hub
hub = PrimeHub()

# Indicate that hub is advertising
hub.light_matrix.show_image('HAPPY')

ble = BLEPeripheral()

def turning_mode():
    """Loop that controls the robot's turning"""
    print("turning mode")
    for i in range(50):
        hub.light_matrix.show_image("SQUARE_SMALL", i*2)

    while True:
        # Robot turns when -1 or 1 is sent, stops turning when 0 is sent
        if hub.left_button.is_pressed(): 
            ble.send(str(-1))
            print("sent left")
            hub.left_button.wait_until_released()
            ble.send(str(0))
            print("sent neutral")
        elif hub.right_button.is_pressed():
            ble.send(str(1))
            print("sent right")
            hub.right_button.wait_until_released()
            ble.send(str(0))
            print("sent neutral")
        # cycles to height_mode when tapped
        elif hub.motion_sensor.get_gesture() == "tapped":
            height_mode()
            break

def height_mode():
    """Loop that controls the trajectory's height"""
    print("height mode")

    # display double-edged arrow
    hub.light_matrix.off()
    for i in range(50):
        hub.light_matrix.set_pixel(2, 0, i*2)
        hub.light_matrix.set_pixel(1, 1, i*2)
        hub.light_matrix.set_pixel(3, 1, i*2)

        hub.light_matrix.set_pixel(2, 4, i*2)
        hub.light_matrix.set_pixel(1, 3, i*2)
        hub.light_matrix.set_pixel(3, 3, i*2)

    while True:
        # same mechanism as in turning_mode()
        if hub.left_button.is_pressed():
            ble.send(str(2))
            print("sent down")
            hub.left_button.wait_until_released()
            ble.send(str(3))
            print("sent neutral")
        elif hub.right_button.is_pressed():
            ble.send(str(4))
            print("sent up")
            hub.right_button.wait_until_released()
            ble.send(str(3))
            print("sent neutral")
        # cycles to main_loop() when tapped
        elif hub.motion_sensor.get_gesture() == "tapped":
            break

def main_loop():
    """Loop that is responsible for shooting ball based on accelerometer data"""
    while True:
        print("shooting mode")
        # Display forward arrow every time ball is prepared to be shot
        for i in range(50):
            hub.light_matrix.show_image("ARROW_N", i*2)

        accs = []

        while True:
            if hub.left_button.is_pressed():
                print("collecting data")
                # display slower arrow when left button is pressed
                for i in range(100):
                    hub.light_matrix.show_image("ARROW_N", i)
                    time.sleep(0.01)
                while hub.left_button.is_pressed():
                    # instantaneous x y z acceleration
                    (a_x, a_y, a_z) = motion.accelerometer()

                    # take magnitude of x, and y acceleration and append to array
                    mag = math.sqrt(a_x**2 + a_y**2)
                    accs.append(mag)

                    # samples acceleration every 0.01 seconds
                    time.sleep(0.01)
            
                try:
                    acc = max(accs)
                    print("Acceleration: ", acc)
                    ble.send(str(acc))
                # if no acc data was collected before button was released
                except ValueError:
                    print("Hold down the button for longer!")
            # cycles to turning_mode() when tapped
            elif hub.motion_sensor.get_gesture() == "tapped":
                turning_mode()
                break

#  Minimizes lag during first connection
while True:
    if ble.is_connected():
        time.sleep(1)
        main_loop()

    time.sleep(0.1)