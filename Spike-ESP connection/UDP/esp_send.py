import network, socket, time

class send_message():
    """Connects device to WiFi and allows device to send UDP
    
    IP is the address of the computer running MR
    port must be the same port used in MR specified in the receive UDP block
    """
    def __init__(self, IP, port):
        wlan = network.WLAN(network.STA_IF)

        if not wlan.isconnected():
            wlan.active(True)

            # Try to connect to Tufts_Wireless (if connecting to Tufts_Wireless 
            # make sure to register your esp at https://it.tufts.edu/it-
            # computing/wifi-network/manual-non-browser-device-registration)
            ssid = "Tufts_Wireless"
            print("Connecting to {}...".format(ssid))
            wlan.connect(ssid)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.connect((IP, port))
        
        print("Connected!")
        print("IP address:", wlan.ifconfig()[0])
        
    def send(self, msg):
        msg = bytes(msg, "utf-8")
        
        self.s.send(msg)

    def close(self):
        self.s.close()
