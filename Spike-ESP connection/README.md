# ESP/WiFi
The WiFi method is a little bit more involved than the BLE method, and requires you to hack a SPIKE cable so that you can connect the SPIKE to an ESP. Make sure you have Backpack_Code.py saved onto the SPIKE and esp_send.py onto the ESP. If you're doing this from scratch, Rebecca has some more instructions on installing stuff with LabVIEW and the ESP wiring [here](https://github.com/acceber1473/ThingWorxAnalytics).

File descriptions:
- SpikeSend.py: SPIKE code that sets up the SPIKE and ESP to send UDP messages to MR for the shuffleboard environment
- SpikeSendReceive.py: SPIKE code that sets up the SPIKE and ESP to send/recieve UDP messages to/from MR