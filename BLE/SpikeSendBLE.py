"""
Program that connects to Mind Render via bluetooth and controls a shuffleboard 
disc using the hub's built in accelerometer sensor.

Accompanying MR environment: shuffleboard9; share code: shuffleboard

To do
- Add comments to the BLEPeripheral class

Changelog
6/28/22
- Created new file based off of SpikeSend.py but uses BLE protocol to communicate with MR
"""

import bluetooth, hub, math, utime, struct
from spike import PrimeHub
from math import *
from hub import motion
from micropython import const

# Set up Bluetooth structure data, provided to us by the Mind Render folks and 
# then modified.
# This takes up a lot of the code, to skip to the main content jump to line 
# 149. Remember to change the name of your SPIKE (if you want) on line 102.
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
        car = "car" + str(rand)
        self._payload = advertising_payload(name=car, services=[_UART_UUID])
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

ble = BLEPeripheral()
hub = PrimeHub()

while True:
    #empty array to hold acceleration values
    accs = []
    
    #wait until left button is pressed
    hub._left_button.wait_until_pressed()
    while hub._left_button.is_pressed():
        #instantaneous x y z acceleration
        (a_x, a_y, a_z) = motion.accelerometer()
        
        #take magnitude of x and y acceleration (since on flat table) and add to array
        mag = math.sqrt(a_x**2 + a_y**2)
        accs.append(mag)
        
        #samples acceleration every 0.01 seconds
        utime.sleep(0.01)
    
    #find maximum acceleration while left button was held
    acc = max(accs)
    
    # uncomment if you want to see the accel data
    # print(accs)

    ble.send(str(acc))
    print(acc)
    
    #display an arrow on hub display with increasing brightness
    for i in range(11):
        hub.light_matrix.show_image('ARROW_N', brightness=i*10)
        utime.sleep(.1)
