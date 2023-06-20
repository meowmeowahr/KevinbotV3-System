"""
Kevinbot v3 MPU9250-2-MQTT
By: Kevin Ahr
"""

import sys
import os
import time
import smbus
import uuid
import json
import logging

from paho.mqtt import client as mqtt_client

from imusensor.MPU9250 import MPU9250

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

BROKER = settings["services"]["mqtt"]["address"]
PORT = settings["services"]["mqtt"]["port"]
TOPIC_ROLL = settings["services"]["mpu"]["topic-roll"]
TOPIC_PITCH = settings["services"]["mpu"]["topic-pitch"]
TOPIC_YAW = settings["services"]["mpu"]["topic-yaw"]
CLI_ID = f'kevinbot-mpu-{uuid.uuid4()}'


def on_connect(client, userdata, flags, rc):
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
    while True:
        # read from sensor
        imu.readSensor()
        imu.computeOrientation()

        # publish over mqtt
        publish(TOPIC_ROLL, round(imu.roll, 2))
        publish(TOPIC_PITCH, round(imu.pitch, 2))
        publish(TOPIC_YAW, round(imu.yaw, 2))

        # wait
        time.sleep(settings["services"]["mpu"]["update-speed"])


if __name__ == "__main__":
    logging.basicConfig(level=settings["logging"]["level"])
    if settings["services"]["mpu"]["enabled"]:
        bus = smbus.SMBus(1)
        imu = MPU9250.MPU9250(bus, int(settings["services"]["mpu"]["address"]))
        imu.begin()
        loop()
    else:
        logging.warning("MPU Service is not enabled, exiting")
