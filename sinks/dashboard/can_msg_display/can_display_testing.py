import time
import serial
import struct

import message_types as mt

COM_PORT = "COM3"

s = serial.Serial(COM_PORT, 9600)

# random data just for testing
msg_data = "$555:1,2,FF,3E,44,56,66,31\r\n"
msg_data = msg_data.encode('utf-8')

while 1:
    print(msg_data)
    s.write(msg_data)
    time.sleep(1)
