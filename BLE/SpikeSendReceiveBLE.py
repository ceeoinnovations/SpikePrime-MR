"""
Based on SpikeSendReceive.py, this code turns the SPIKE hub along with a motor/
position sensor and two force sensors into a force feedback (FF) steering wheel 
with gas and brake inputs. Oh, and it's Bluetooth.

Example LEGO FF steering wheel can be found in this folder

Accompanying MR environment: FF Driving BLE v8; share code: spikedriving

To do
- Make it faster maybe
- Add comments to the BLEPeripheral class

Changelog
7/27/22
- Cleaned it up
7/26/22
- Reworked the whole thing so it now runs on async, the rumble freeze bug has 
been fixed
7/20/22
- Created file
"""

# Initialize the hub and get your imports
import bluetooth, hub, struct
import uasyncio as ua
from spike import Motor, ForceSensor
from micropython import const
from time import sleep
from random import randint


# Set up Bluetooth structure data, provided to us by the Mind Render folks and 
# then modified.
# This takes up a lot of the code, to skip to the main content jump to line 
# 165. Remember to change the name of your SPIKE (if you want) on line 108.
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

class BLEPeripheral:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = \
            self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        # Change name here, keep it < 9 characters
        adv_name = "wheel" + str(randint(1, 100)) 
        self._payload = advertising_payload(name=adv_name, 
                                            services=[_UART_UUID])
        self._advertise(adv_name)

    def is_connected(self):
        return len(self._connections) > 0

    def send(self, data):
        if self.is_connected():
            for handle in self._connections:
                self._ble.gatts_notify(handle, self._handle_rx, data)
                self._ble.gatts_notify(handle, self._handle_tx, data)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            print('line 112|_IRQ_CENTRAL_CONNECT')
            hub.sound.beep(750,100) # A little sound effect when it connects
            sleep(.1)
            hub.sound.beep(800,100)
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Connected | Handle:", conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            print('line 119|_IRQ_CENTRAL_DISCONNECT')
            hub.sound.beep(800,100) # A little sound effect when it disconnects
            sleep(.1)
            hub.sound.beep(750,100)
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            print("Disconnected | Handle:", conn_handle)

        # Have to bypass this entire thing because for some reason it sleeps 
        # (I think it's from the BLE source code but don't know)
        # elif event == _IRQ_GATTS_WRITE:
            # print('line 130|_IRQ_GATTS_WRITE')
            # conn_handle, value_handle = data
            # value = self._ble.gatts_read(value_handle)
            # if value_handle == self._handle_rx:
            #    msg = float(value.decode()) # Decoding what we read and 
            #    turning it into a decimal
            #    # print("received |", msg)
            #    # await ua.create_task(rumble(msg))


    def _advertise(self, name):
        self._ble.gap_advertise(500000, adv_data=self._payload)
        hub.sound.beep(800,150) # A little sound effect when it starts advertising
        sleep(.18)
        hub.sound.beep(750,150)
        sleep(.18)
        hub.sound.beep(800,150)
        print("Advertising as", name)


# This is where our code really begins, post BLE setup stuff
ble = BLEPeripheral()

# Quick light to make sure code is up and running
hub.display.clear()
sleep(.5)
hub.display.pixel(2,2,10)

# Set up the motor and force sensor on the Prime
steer = Motor('A') # Make sure to switch this and the next two to the right ports
gas = ForceSensor('F')
brake = ForceSensor('E')
steer.set_stop_action('coast')
steer.stop()

# Async function for sending SPIKE data to MR
async def sending():
    while True:
        payload = str(steer.get_position()) + "," + str(gas.get_force_percentage()) + "," + str(brake.get_force_percentage())
        ble.send(payload)
        # print(payload) # Uncomment if you're sus at what data is being sent and you want to see
        await ua.sleep(.01)

# Async function for the force feedback, called from receiving()
async def rumble(speed):
    steer.start(round(speed))
    await ua.sleep(.25)
    steer.start(round(-speed))
    await ua.sleep(.25)
    steer.stop()

# Async function to get info from MR and process it as required
async def receiving():
    old_data = ""
    while True:
        value_handle = 12 # 10 for connection statuses, 12 for data Tx (from what I can tell); don't change
        new_data = ble._ble.gatts_read(value_handle)
        
        if (not new_data == old_data) and new_data:  # Need the second condition for edge case when it starts
            old_data = new_data
            msg = float(new_data.decode())
            # print("msg |", msg,"|| going to rumble")  # Uncomment to see if you're sus
            await rumble(msg)

        await ua.sleep(.01)

# Putting everything together
async def main():
    ua.create_task(receiving())
    await ua.create_task(sending())


# Run
ua.run(main())

# Sanity check
print('If this is printing then something is very wrong with the code.')
