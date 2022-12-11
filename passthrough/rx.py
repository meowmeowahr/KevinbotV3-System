# A demo of the XBee AP mode in Python connected to raspberry pi gpio pins


from xbee import XBee
import threading
import serial
import speech
import time

XB_SERIAL_PORT   = "/dev/ttyS0"
XB_BAUD_RATE     = 230400

P2_SERIAL_PORT   = "/dev/ttyAMA1"
P2_BAUD_RATE     = 230400

ROBOT_VERSION    = "Unknown"

global ENABLED
ENABLED          = True

ERRORS           = ["Invalid Arm Startup Position", "Invalid Command"]

xb_ser = serial.Serial(XB_SERIAL_PORT, baudrate=XB_BAUD_RATE)
xbee = XBee(xb_ser, escaped=True)

p2_ser = serial.Serial(P2_SERIAL_PORT, baudrate=P2_BAUD_RATE)
p2_ser.write(b"robot_version\r")

speech_engine = "espeak"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def send_data(data):
    xbee.send("tx", dest_addr=b'\x00\x00', data=bytes("{}".format(data), 'utf-8'))

def p2_loop():
    while True:
        try:
            line = p2_ser.readline().decode().strip("\n").split("=")

            if line[0] == "version":
                ROBOT_VERSION = line[1]
            elif line[0] == "error":
                print(bcolors.WARNING + "Error: " + ERRORS[int(line[1]) - 1] + bcolors.ENDC)
                

            print(bcolors.HEADER + "Command: " + line[0])
            print("Value: " + str(line[1]) + bcolors.ENDC)
            print("===========================")

            send_data("{}={}\r".format(line[0], line[1]))
        except Exception as e:
            print(bcolors.FAIL + "Error: {}".format(e) + bcolors.ENDC)

def loop():
    global ENABLED
    global speech_engine

    while True:
        if ENABLED:
                data = xbee.wait_read_frame()
                if not data['rf_data'].decode().startswith('no-pass'):
                    p2_ser.write(data['rf_data'])
                print(bcolors.OKBLUE + "RX Data: " + data['rf_data'].decode())
                data = data['rf_data'].decode().split('=', 1)
            
                command = data[0]
                try:
                    value = data[1]
                    no_value = False
                except IndexError:
                    no_value = True
                    value = None

                if not "no-pass" in command:
                    pass
                else:
                    print(bcolors.OKGREEN + "No Passthrough Command" + bcolors.ENDC)
                    if command == "no-pass.speech":
                        if speech_engine == "festival":
                            print('fest')
                            speech.SayText(value)
                        elif speech_engine == "espeak":
                            speech.SayTextEspeak(value)
                    elif command == "no-pass.speech-engine":
                        speech_engine = value.strip()


if __name__ == '__main__':
    p2thread = threading.Thread(target=p2_loop)
    p2thread.start()
    loop()