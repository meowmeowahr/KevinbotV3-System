"""
Kevinbot v3 MPU9250-2-MQTT
By: Kevin Ahr
"""

import json
import logging
import os
import sys
import time
import uuid

import smbus
from imusensor.MPU9250 import MPU9250
from paho.mqtt import client as mqtt_client

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

BROKER = settings["services"]["mqtt"]["address"]
PORT = settings["services"]["mqtt"]["port"]
TOPIC_IMU = settings["services"]["mpu"]["topic-imu"]
CLI_ID = f'kevinbot-mpu-{uuid.uuid4()}'


def on_connect(_, __, ___, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker")
    else:
        logging.critical("Failed to connect, return code %d\n", rc)
        sys.exit()


client = mqtt_client.Client(CLI_ID)
client.on_connect = on_connect
client.connect(BROKER, PORT)


def publish(topic, msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status != 0:
        logging.error(f"Failed to send message to topic {topic}")


def loop():
    delay = settings["services"]["mpu"]["update-speed"]
    while True:
        # read from sensor
        imu.readSensor()
        imu.computeOrientation()

        # publish over mqtt
        publish(TOPIC_IMU, f"{round(imu.roll, 2)},{round(imu.pitch, 2)},{round(imu.yaw, 2)}")

        # wait
        time.sleep(delay)


if __name__ == "__main__":
    logging.basicConfig(level=settings["logging"]["level"])
    if settings["services"]["mpu"]["enabled"]:
        bus = smbus.SMBus(1)
        imu = MPU9250.MPU9250(bus, int(settings["services"]["mpu"]["address"]))
        imu.begin()
        loop()
    else:
        logging.warning("MPU Service is not enabled, exiting")
