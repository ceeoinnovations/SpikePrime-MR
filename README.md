# SpikePrime-MindRender
Connecting the LEGO SPIKE Prime system to Mind Render – an educational programming tool (check it out [here!](https://mindrender.jp/en_mindrender/)). 

We've developed two ways to connect a Prime hub to MR. The first is through UDP over WiFi, and the second is over Bluetooth. Note that the Prime doesn't have WiFi capabilities so we connected an ESP to talk to the hub via serial and then used that board's antenna to send and receive UDP packets. The second method is just your standard BLE, which the SPIKE supports. 

The BLE folder has the BLE stuff and the Spike-ESP connection folder has the WiFi stuff. Have fun!