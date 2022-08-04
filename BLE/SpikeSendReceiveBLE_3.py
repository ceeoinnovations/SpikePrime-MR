"""
!!!!
As of 8/1/22 this is no longer in development. This program is not functional.
!!!!


Based on SpikeSendReceiveBLE.py, this code is ported for Atlantis.

To do
- Get the BLE feedback to work (rumble doesn't activate for some reason)
- Put in a coast function, e.g. motor.motor_move_by_degrees(p2, degrees, speed,motor.MOTOR_END_STATE_FLOAT)
- Test it all

Changelog
7/22/22
- Chris told me how to get motor position so putting that in now and testing
7/20/22
- Created file
"""

# Initialize the hub and get your imports
import bluetooth, struct
import motor, force_sensor, display, port
from micropython import const
from time import sleep


# Set up Bluetooth structure data, provided to us by the Mind Render folks
# This takes up a lot of the code, to skip to the main content jump to line ~150
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

def advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0, free=None):
    payload = bytearray()

    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value

    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)),)

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

    # org.bluetooth.characteristic.gap.appearance.xml
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

class BLEPeripheral:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._payload = advertising_payload(name="wheel0", services=[_UART_UUID]) # Change name here, keep it < 9 characters
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

            #self._advertise()
            print("Disconnected", conn_handle)

        elif event == _IRQ_GATTS_WRITE:
            # print('Read')
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx:
                msg = float(value.decode()) # Decoding what we read and turning it into a decimal
                # print("received |", msg)
                steer.motor_move_at_speed(4,100*round(msg)) # Creating force feedback based on the input from MR
                sleep(.2)
                steer.motor_move_at_speed(4,100*round(-msg))
                sleep(.2)
                steer.motor_stop()
                # print('0 steer')
                # steer.run_for_seconds(.3, round(msg))
                # print('1 steer')
                # steer.run_for_seconds(.3, round(-msg))
                # print('2 steer')
                # steer.stop()
                # print('done steer')

    def _advertise(self):
        self._ble.gap_advertise(500000, adv_data=self._payload)
        print("Advertise")



# This is where our code really begins, post BLE setup stuff
ble = BLEPeripheral()

# Quick light to make sure code is working
display.display_clear()
sleep(.5)
display.display_set_pixel(2,2,100)

# Set up the motor and force sensor on the Prime
steer = motor # Make sure to switch this and the next two to the right port
#gas = force_sensor('B')
#brake = force_sensor('A')
#steer.set_stop_action('coast')
steer.motor_stop()

while True:
    # We need to manually tell the SPIKE to send data but receiving happens automatically from setup
    # Note that if we're receiving the collision speed from MR, that is acted upon directly at line ~125
    payload = str(port.port_getSensor(0)[2]) + "," + str(force_sensor.get_force(5)) + "," + str(force_sensor.get_force(4))
    ble.send(payload)
    print(payload)        # Uncomment if you think things are sus and wanna see what's being sent
    #sleep(.1)

# Sanity check
print('If this is printing then something is very wrong with the loop.')
