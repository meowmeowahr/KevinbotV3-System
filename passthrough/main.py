from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
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


remote_name = None
remote_status = "disconnected"

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
                    elif command == "no-pass.remote.status":
                        remote_status = value.strip()
                        if remote_status == "disconnected":
                            win.icon.setPixmap(QPixmap("network-disconnected.svg"))
                            win.status.setText("Remote is Disconnected")
                        elif remote_status == "connected":
                            win.icon.setPixmap(QPixmap("network-connected.svg"))
                            if remote_name:
                                win.status.setText(f"Connected to \"{remote_name}\"")
                            else:
                                win.status.setText("Connected to \"UNKNOWN\"")
                        elif remote_status == "error":
                            win.icon.setPixmap(QPixmap("network-error.svg"))
                    elif command == "no-pass.remote.name":
                        remote_name = value.strip()
                        win.status.setText(f"Connected to \"{remote_name}\"")
                        
                            

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot Passthrough")
        self.setWindowIcon(QIcon("icon.svg"))

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.main_layout = QVBoxLayout()
        self.widget.setLayout(self.main_layout)

        self.title = QLabel("Kevinbot Passthrough")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.main_layout.addWidget(self.title)

        self.status = QLabel("Remote is Disconnected")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.main_layout.addWidget(self.status)

        self.main_layout.addStretch()

        self.icon = QLabel()
        self.icon.setPixmap(QPixmap("network-disconnected.svg"))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.icon)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.main_layout.addWidget(self.close_button)

        self.main_layout.addStretch()
        

        self.show()


if __name__ == "__main__":

    p2thread = threading.Thread(target=p2_loop, daemon=True)
    p2thread.start()

    main_thread = threading.Thread(target=loop, daemon=True)
    main_thread.start()

    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Passthrough")
    app.setApplicationVersion("1.0")
    win = MainWindow()
    sys.exit(app.exec())
