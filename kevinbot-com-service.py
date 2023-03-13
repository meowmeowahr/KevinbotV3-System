import datetime
import os
import subprocess
import threading
import logging
import json
import time

import playsound
import pyttsx3
import serial
import zmq
from xbee import XBee

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

XB_SERIAL_PORT = settings["com-service"]["serial"]["xb-port"]
XB_BAUD_RATE = settings["com-service"]["serial"]["xb-baud"]

P2_SERIAL_PORT = settings["com-service"]["serial"]["p2-port"]
P2_BAUD_RATE = settings["com-service"]["serial"]["p2-baud"]

ZMQ_PORT = settings["com-service"]["zmq"]["port"]
ZMQ_INTERVAL = settings["com-service"]["zmq"]["interval"]

USING_BATT_2 = False
BATT_LOW_VOLT = 99

speech_engine = "espeak"

last_alive_msg = datetime.datetime.now()
is_alive = True

sensors = {"batts": [-1, -1]}

shown_batt1_notif = False
shown_batt2_notif = False

enabled = False


def speak_festival(text):
    os.system('echo "{}" | festival --tts'.format(text.replace("Kevinbot",
                                                               "Kevinbought")))


def data_to_remote(data):
    xbee.send("tx", dest_addr=b'\x00\x00',
              data=bytes("{}".format(data), 'utf-8'))


def recv_loop():
    global shown_batt1_notif, shown_batt2_notif
    global sensors, enabled

    while True:
        try:
            line = p2_ser.readline().decode().strip("\n").split("=")

            data_to_remote("{}={}\r".format(line[0], line[1]))

            if line[0] == "batt_volts":
                line[1] = line[1].split(",")

                sensors["batts"][0] = float(line[1][0]) / 10
                sensors["batts"][1] = float(line[1][1]) / 10

                if int(line[1][0]) < BATT_LOW_VOLT:
                    playsound.playsound(os.path.join(os.curdir,
                                                     "sounds/low-battery.mp3"))
                    if not shown_batt1_notif:
                        subprocess.run(["notify-send", "Kevinbot System",
                                        f"Battery #1 is critically low. \
                                        \nVoltage: {float(line[1][0]) / 10}V",
                                        "-u", "critical", "-t", "0"])
                        shown_batt1_notif = True

                if int(line[1][1]) < BATT_LOW_VOLT and USING_BATT_2:
                    playsound.playsound(os.path.join(os.curdir,
                                                     "sounds/low-battery.mp3"))
                    if not shown_batt2_notif:
                        subprocess.run(["notify-send", "Kevinbot System",
                                        f"Battery #2 is critically low. \
                                        \nVoltage: {float(line[1][1]) / 10}V",
                                        "-u", "critical", "-t", "0"])
                        shown_batt2_notif = True
            elif line[0] == "robot.disable":
                enabled = not line[1].lower() in ["true", "t"]
                logging.info(f"Enabled: {enabled}")
        except ValueError:
            # data is corrupt
            pass


def remote_recv_loop():
    global speech_engine
    global enabled

    while True:
        try:
            data = xbee.wait_read_frame()

            if (not data['rf_data'].decode().startswith('no-pass')) and enabled:
                print("en")
                p2_ser.write(data['rf_data'])
            data = data['rf_data'].decode().strip("\r\n").split('=', 1)

            logging.debug(f"Recieved from XBee: {data}")

            if data[0] == "no-pass.speech":
                if speech_engine == "festival":
                    speak_festival(data[1].strip("\r\n"))
                elif speech_engine == "espeak":
                    espeak_engine.say(data[1].strip("\r\n"))
                    espeak_engine.runAndWait()
            elif data[0] == "no-pass.speech-engine":
                speech_engine = data[1].strip("\r\n")
            elif data[0] == "robot.disable":
                enabled = not data[1].lower() in ["true", "t"]
                logging.info(f"Enabled: {enabled}")

            if data[0] == "shutdown":
                subprocess.run(["systemctl", "poweroff"])
        except Exception as e:
            data_to_remote("robot.disable=True")
            disable()


def disable():
    p2_ser.write("shutdown".encode("UTF-8"))


def update_zmq():
    while True:
        socket.send_json(sensors)
        time.sleep(ZMQ_INTERVAL)


if __name__ == "__main__":
    # banner
    try:
        import pyfiglet
        print("\033[94m", end=None)
        print(pyfiglet.Figlet().renderText("Kevinbot COM"))
    except ImportError:
        print("\033[94mKevinbot COM")
    print("\033[0m", end=None)

    # logging
    logging.basicConfig(level=logging.DEBUG)

    # serial
    xb_ser = serial.Serial(XB_SERIAL_PORT, baudrate=XB_BAUD_RATE)
    xbee = XBee(xb_ser, escaped=True)

    p2_ser = serial.Serial(P2_SERIAL_PORT, baudrate=P2_BAUD_RATE)

    # speech
    espeak_engine = pyttsx3.init("espeak")

    # zmq
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{ZMQ_PORT}")

    # threads
    recv_thread = threading.Thread(target=recv_loop)
    recv_thread.start()

    remote_recv_thread = threading.Thread(target=remote_recv_loop, daemon=True)
    remote_recv_thread.start()

    zmq_thread = threading.Thread(target=update_zmq, daemon=True)
