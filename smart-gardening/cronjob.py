#!/usr/bin/python3
import board
import busio
import digitalio
import logging
import os
import paho.mqtt.client as mqtt
import time

from adafruit_mcp3xxx.mcp3008 import MCP3008
from threading import Thread

from settings import *


def _publish_reading_async(client, topic, timeout_in_sec=10):
    logging.info("Publishing on " + topic)
    client.publish(topic, "on")
    time.sleep(timeout_in_sec)
    client.publish(topic, "off")
    logging.info("Exit publishing on " + topic)


def get_reading(pin):
    val = 0.0

    try:
        n_values = 10
        # create the mcp object
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.CE0)
        mcp = MCP3008(spi, cs)

        for _ in range(n_values):
            val += mcp.read(pin)

        val /= n_values
        logging.debug("Obtained moisture level %.2f" % val)

    except Exception as e:
        # fails when no sensor attached
        logging.error(str(e) + ": ignore reading pin " + str(pin))

    return val


if __name__ == '__main__':
    logging.getLogger().setLevel(LOG_LEVEL)
    logging.info("Run cronjob")

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT)

    threads = []

    for plant in PLANTS:
        chan    = plant["WATER_PUMP_CHANNEL"]  # relay channel
        pin     = plant["MOISTURE_PIN"]
        timeout = plant["WATERING_TIME"]

        topic = os.path.join(MQTT_TOPIC, chan)

        if plant["CHECK_MOISTURE_LEVEL"]:
            val = get_reading(pin)
            if val > plant["MOISTURE_THRESHOLD"]:
                # skip plant when moisture above threshold
                logging.info("Moisture level above threshold - skipping " + plant["NAME"])
                continue

        # publish "on" and "off" signal with timeout
        _publish_reading_async(client, topic, timeout)
        time.sleep(.1)

    logging.info("Cronjob finished successfully")
