"""
Program that connects to Mind Render via UDP using an external ESP with WiFi 
and controls a shuffleboard disc using the hub's built-in accelerometer 
sensor.

To do
- Clean up code in general
- Comment out code and describe what it's doing
- Add debug things (the first chunk of code is essentially a test to make sure 
  serial is working, that can probably be thrown into a debug section that can 
  be turned on/off)

Changelog
6/15/22
- Cleaned up the code a little bit
6/14/22
- Gave code a proper name
"""

# Make sure you have Backpack_Code.py "installed" (aka saved) on the Spike and 
# esp_send.py installed on the ESP

# Initialize the hub and get your imports
from Backpack_Code import Backpack
import hub, math, utime, os, sys
from hub import motion
from spike import PrimeHub

file = '''
print('testing')
'''
file = file.replace("\'",'"')

# Make sure you change the port to wherever you have the ESP plugged in on the 
# Prime
dongle = Backpack(hub.port.F, verbose = True) 

dongle.setup()
filename = 'test.py'
dongle.load(filename,file)
reply = dongle.get(filename)

if (reply == file):
    print("Testing done.")
print("_________________________________________________________")


# On first run of this code, we need to get the ESP to import our send library
dongle.ask('from esp_send import send_message')
# We then need to set up our connection over wifi - change the IP address 
# address and port below.
# The IP should be the computer that is running MR. DO NOT change anything else 
# - leave the quotes, slashes, and commas the way they are.
#                                   IP          port 
#                                   ↓            ↓
dongle.ask('x = send_message(\"10.247.98.69\", 21024)')


hub.display.clear()
utime.sleep(.5)
hub.display.pixel(2,2,10)

hub = PrimeHub()

while True:
    # Empty array to hold acceleration values
    accs = []
    
    # Wait until left button is pressed
    hub._left_button.wait_until_pressed()
    while hub._left_button.is_pressed():
        # Instantaneous x y z acceleration
        (a_x, a_y, a_z) = motion.accelerometer()
        
        # Take magnitude of x and y acceleration (since on flat table) and add 
        # to array
        mag = math.sqrt(a_x**2 + a_y**2)
        accs.append(mag)
        
        # Sample acceleration every 0.01 seconds
        utime.sleep(0.01)
    
    # find maximum acceleration while left button was held
    acc = max(accs)
    
    # Uncomment these if you want to see the accel data
    # print(accs)
    # print(acc)
    message = "x.send(\'" + str(acc) + "\')"
    dongle.ask(message)
    print(message)
    
    # Display an arrow on hub display with increasing brightness
    for i in range(11):
        hub.light_matrix.show_image('ARROW_N', brightness=i*10)
        utime.sleep(.1)
        

