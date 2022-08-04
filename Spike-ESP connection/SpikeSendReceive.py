"""
Based on SpikeSend.py, this code makes the SPIKE into a steering wheel 
with some force feedback.

To do
- Make faster(?)

Changelog
7/7/22
- Updated code, now it receives the speed from MR when the car hits something 
  and then shakes
- Added comments to explain code a bit
7/5/22
- Created file
"""

# Make sure you have Backpack_Code.py "installed" (aka saved) on the Spike and 
# esp_send.py installed on the ESP

# Initialize the hub and get your imports
from Backpack_Code import Backpack
import hub, math, utime, os, sys
from hub import motion
from spike import PrimeHub, Motor
from time import sleep

# Make sure you change the port to wherever you have the ESP plugged in on the 
# Prime
dongle = Backpack(hub.port.F, verbose = True)
dongle.setup()

# If dongle stuff starts giving you an error uncomment the following lines 
# and see if the serial communication is working. If everything works properly 
# then you should get "Success" after dongle.setup() above and "Testing done."
# after the below block.

# file = '''
# print('testing')
# '''
# file = file.replace("\'", '"')
# filename = 'test.py'
# dongle.load(filename, file)
# reply = dongle.get(filename)
# if (reply == file):
#     print("Testing done.")
# print("_________________________________________________________")


# On first run of this code, we need to get the ESP to import our send library
dongle.ask('from esp_send import send_message')
# We then need to set up our connection over wifi - change the IP address 
# address and port below.
# The IP should be the laptop that is running MR. DO NOT change anything else - 
# leave the quotes, 
# slashes, and commas the way they are.
#                                   IP          port 
#                                   ↓            ↓
dongle.ask('x = send_message(\"10.247.98.69\", 21024)')

    
# Quick light to make sure code is working
hub.display.clear()
utime.sleep(.5)
hub.display.pixel(2,2,10)

hub = PrimeHub()

# Set up the UDP connections on the ESP. Change the IP and port as needed to the IP of your ESP.
dongle.ask('import socket')
dongle.ask('UDP_IP = "10.245.81.17"')
dongle.ask('UDP_PORT = 21024')
dongle.ask('sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)')
dongle.ask('sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)')
dongle.ask('sock.bind((UDP_IP, UDP_PORT))')

# Set up the motor on the Prime
motor = Motor('E') # Make sure to switch this to the right port
motor.set_stop_action('coast')
motor.stop()

# Main loop, where the real stuff happens
while True:
    # Turn LEDs off, clear variables, get data from the socket
    hub._light_matrix.off()
    ESPraw = ""
    dongle.ask('data, addr = sock.recvfrom(1024)')
    dongle.ask("data = data.decode('UTF-8')")
    ESPraw = dongle.ask('print(data)')
    ESPclean = ""

    # Once we have data, we clean it up into something usable and turn the 
    # light on
    if not (ESPraw == ""): # Checks if MR sent data (which it always should)
        for i in ESPraw:
            if (i == "-"):
                ESPclean = ESPclean + i
            elif i.isdigit():
                ESPclean = ESPclean + i
            elif (i == "."):
                ESPclean = ESPclean + i
        hub._light_matrix.set_pixel(4,4,99)
        MRdata = float(ESPclean) # Convert the cleaned up string into a decimal

        # MR is set to send 1s when there's no collision so we handle that 
        # here; if we have data, then we set that as the rumble factor and 
        # shake the wheel
        if not (MRdata == 1):
            # hub._speaker.beep(80)
            motor.start(round(MRdata))
            sleep(.3)
            motor.start(round(-MRdata))
            sleep(.3)
            motor.start(round(MRdata))
            motor.stop()

    # We send our motor position back to MR at all times (because we need to 
    # steer)
    message = "x.send(\'" + str(motor.get_position()) + "\')"
    dongle.ask(message)
    # print(message)


# Sanity check
print('If this is printing then something is very wrong with the loop.')