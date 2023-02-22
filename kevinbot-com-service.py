import datetime
import os
import subprocess
import threading
import logging

import playsound
import pyttsx3
import serial
import zmq
from xbee import XBee

XB_SERIAL_PORT = "/dev/ttyS0"
XB_BAUD_RATE = 230400

P2_SERIAL_PORT = "/dev/ttyAMA1"
P2_BAUD_RATE = 230400

USING_BATT_2 = False
BATT_LOW_VOLT = 99

speech_engine = "espeak"

last_alive_msg = datetime.datetime.now()
is_alive = True

sensors = {"batts": [-1, -1]}

shown_batt1_notif = False
shown_batt2_notif = False

# TODO: Implement zmq support
"""
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

while True:
    #  Wait for next request from client
    message = socket.recv()
    print("Received request: %s" % message)
"""


def speak_festival(text):
    os.system('echo "{}" | festival --tts'.format(text.replace("Kevinbot",
                                                               "Kevinbought")))


def data_to_remote(data):
    xbee.send("tx", dest_addr=b'\x00\x00',
              data=bytes("{}".format(data), 'utf-8'))


def recv_loop():
    global shown_batt1_notif, shown_batt2_notif
    global sensors

    while True:
        line = p2_ser.readline().decode().strip("\n").split("=")

        data_to_remote("{}={}\r".format(line[0], line[1]))

        try:
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
        except ValueError:
            # data is corrupt
            pass


def remote_recv_loop():
    global speech_engine

    while True:
        data = xbee.wait_read_frame()

        if not data['rf_data'].decode().startswith('no-pass'):
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

        if data[0] == "shutdown":
            subprocess.run(["systemctl", "poweroff"])


if __name__ == "__main__":
    # logging
    logging.basicConfig(level=logging.DEBUG)

    # serial
    xb_ser = serial.Serial(XB_SERIAL_PORT, baudrate=XB_BAUD_RATE)
    xbee = XBee(xb_ser, escaped=True)

    p2_ser = serial.Serial(P2_SERIAL_PORT, baudrate=P2_BAUD_RATE)

    # speech
    espeak_engine = pyttsx3.init("espeak")

    # threads
    recv_thread = threading.Thread(target=recv_loop)
    recv_thread.start()

    remote_recv_thread = threading.Thread(target=remote_recv_loop)
    remote_recv_thread.start()
