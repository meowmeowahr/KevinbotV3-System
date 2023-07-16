import sys
import os
import time
import uuid
import json
import logging

from paho.mqtt import client as mqtt_client

import board
from adafruit_bme280 import basic as adafruit_bme280


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

BROKER = settings["services"]["mqtt"]["address"]
PORT = settings["services"]["mqtt"]["port"]
TOPIC_TEMP = settings["services"]["bme"]["topic-temp"]
TOPIC_HUMI = settings["services"]["bme"]["topic-humidity"]
TOPIC_PRESSURE = settings["services"]["bme"]["topic-pressure"]
CLI_ID = f'kevinbot-bme-{uuid.uuid4()}'

i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)


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
        # publish over mqtt
        publish(TOPIC_TEMP, round(bme280.temperature, 2))
        publish(TOPIC_HUMI, round(bme280.relative_humidity, 2))
        publish(TOPIC_PRESSURE, round(bme280.pressure, 2))

        # wait
        time.sleep(settings["services"]["mpu"]["update-speed"])


if __name__ == "__main__":
    # logging
    logging.basicConfig(level=settings["logging"]["level"])

    loop()
