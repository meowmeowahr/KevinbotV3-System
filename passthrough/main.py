from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from xbee import XBee
from queue import Queue
import threading
import serial
import speech
import os
import pyttsx3

XB_SERIAL_PORT   = "/dev/ttyS0"
XB_BAUD_RATE     = 230400

P2_SERIAL_PORT   = "/dev/ttyAMA1"
P2_BAUD_RATE     = 230400

ROBOT_VERSION    = "Unknown"

global ENABLED
ENABLED          = True

ERRORS           = ["Invalid Arm Startup Position", 
                    "Invalid Command", 
                    "BME280 Setup Failed", 
                    "BME280 Read Failed", 
                    "One Wire Bus Short", 
                    "One Wire Bus Error", 
                    "One Wire Device not Found"]

xb_ser = serial.Serial(XB_SERIAL_PORT, baudrate=XB_BAUD_RATE)
xbee = XBee(xb_ser, escaped=True)

p2_ser = serial.Serial(P2_SERIAL_PORT, baudrate=P2_BAUD_RATE)
p2_ser.write(b"robot_version\r")

espeak_engine = pyttsx3.init("espeak")

remote_name = None
remote_status = "disconnected"

speech_engine = "espeak"

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

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
                win.display(f'<span style="font-size:12pt; color:#fefe22;">=== Error: {ERRORS[int(line[1]) - 1]} ===</span>')  
                win.queue_needs_update = True      

            win.display(f'<span style="font-size:12pt; color:#ef8888;">BOT RX⇒ {"=".join(line)}</span>')
            win.queue_needs_update = True

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
                if command == "no-pass.speech":
                    if speech_engine == "festival":
                        speech.SayText(value)
                    elif speech_engine == "espeak":
                        xbee.send("tx", dest_addr=b'\x00\x00', data=bytes("remote.disableui=True\r", 'utf-8'))
                        win.display(f'<span style="font-size:12pt; color:#88ef88;">REM TX⇐ remote.disableui=True</span>')
                        win.queue_needs_update = True
                        espeak_engine.say(value)
                        espeak_engine.runAndWait()
                        xbee.send("tx", dest_addr=b'\x00\x00', data=bytes("remote.disableui=False\r", 'utf-8'))
                        win.display(f'<span style="font-size:12pt; color:#88ef88;">REM TX⇐ remote.disableui=False</span>')
                        win.queue_needs_update = True
                elif command == "no-pass.speech-engine":
                    speech_engine = value.strip()
                elif command == "no-pass.remote.status":
                    remote_status = value.strip()
                    if remote_status == "disconnected":
                        win.icon.setPixmap(QPixmap(os.path.join(CURRENT_DIR, "network-disconnected.svg")))
                        win.status.setText("Remote is Disconnected")
                    elif remote_status == "connected":
                        win.icon.setPixmap(QPixmap(os.path.join(CURRENT_DIR, "network-connected.svg")))
                        if remote_name:
                            win.status.setText(f"Connected to \"{remote_name}\"")
                        else:
                            win.status.setText("Connected to \"UNKNOWN\"")
                    elif remote_status == "error":
                        win.icon.setPixmap(QPixmap(os.path.join(CURRENT_DIR, "network-error.svg")))
                elif command == "no-pass.remote.name":
                    remote_name = value.strip()
                    win.status.setText(f"Connected to \"{remote_name}\"")
                    win.queue_needs_update = True

            win.display(f'<span style="font-size:12pt; color:#8888ef;">REM RX⇒ {"=".join(data)}</span>')
            win.queue_needs_update = True
                            
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # variables
        self.is_term_open = False
        self.terminal_queue = Queue(maxsize=10000)
        self.queue_needs_update = False

        self.setWindowTitle("Kevinbot Passthrough")
        self.setWindowIcon(QIcon(os.path.join(CURRENT_DIR, "icon.svg")))

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.root_layout = QHBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.main_layout = QVBoxLayout()
        self.root_layout.addLayout(self.main_layout)

        self.title = QLabel("Kevinbot Passthrough")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.main_layout.addWidget(self.title)

        # Status Text
        self.status = QLabel("Remote is Disconnected")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.main_layout.addWidget(self.status)

        self.main_layout.addStretch()

        # Status Icon
        self.icon = QLabel()
        self.icon.setPixmap(QPixmap(os.path.join(CURRENT_DIR, "network-disconnected.svg")))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.icon)

        self.main_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.main_layout.addWidget(self.close_button)

        # Terminal Popout Button
        self.term_button = QPushButton(">")
        self.term_button.setFixedSize(QSize(28, 28))
        self.term_button.setCheckable(True)
        self.term_button.clicked.connect(self.term_button_clicked)
        self.root_layout.addWidget(self.term_button)

        # Terminal
        self.terminal = QTextEdit()
        self.terminal.setObjectName("Kevinbot3_RemoteUI_TextEdit")
        self.terminal.setReadOnly(True)
        self.terminal.setVisible(self.is_term_open)
        self.terminal.setStyleSheet("font-family: monospace;")
        self.root_layout.addWidget(self.terminal)

        # Timer
        self.timer = QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.update_queue)
        self.timer.start()

    def display(self, s):
        self.terminal_queue.put(s)

    @pyqtSlot()
    def update_queue(self):
        if not self.terminal_queue.empty():
            self.terminal.append(self.terminal_queue.get())
            self.queue_needs_update = False

    def term_button_clicked(self):
        # invert self.is_term_open
        if self.is_term_open:
            self.is_term_open = False
        else:
            self.is_term_open = True
        self.terminal.setVisible(self.is_term_open)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Passthrough")
    app.setApplicationVersion("1.0")
    win = MainWindow()

    p2thread = threading.Thread(target=p2_loop, daemon=True)
    p2thread.start()

    main_thread = threading.Thread(target=loop, daemon=True)
    main_thread.start()

    win.show()

    sys.exit(app.exec())
