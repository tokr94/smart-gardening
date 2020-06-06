#!/usr/bin/env python

import logging
import os
import paho.mqtt.client as mqtt
import time

from settings import *
from threading import Thread


def _publish_reading_async(client, topic, timeout_in_sec=10):
    logging.info("Started new thread for publishing on " + topic)
    client.publish(topic, "on")
    time.sleep(timeout_in_sec)
    client.publish(topic, "off")


if __name__ == '__main__':
    logging.getLogger().setLevel(LOG_LEVEL)
    logging.info("Run cronjob")

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT)

    threads = []

    for chan, timeout in WATER_PUMP_TIMEOUT_IN_SEC.items():
        topic = os.path.join(MQTT_TOPIC, chan)

        thread = Thread(name=chan, target=_publish_reading_async, args=(client, topic, timeout))
        thread.daemon = True
        thread.start()

        threads.append(thread)
        time.sleep(.1)

    for thread in threads:
        thread.join()

    logging.info("All threads finished successfully")
