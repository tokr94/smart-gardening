#!/usr/bin/python3
import logging
import os
import paho.mqtt.client as mqtt

from settings import *

try:
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

except ImportError as ie:
    logging.warning(str(ie) + " - using mock instead")
    from mocks.GPIOMock import GPIO


def _turn_on(pin):
    logging.debug("Turn on pin " + str(pin))
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)


def _turn_off(pin):
    logging.debug("Turn off pin " + str(pin))
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)


def _get_plants_by_channel(chan):
    return [plant for plant in PLANTS if plant["WATER_PUMP_CHANNEL"] == chan]


# The callback for when the client receives a CONNACK response from the server.
def _on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    topic = os.path.join(MQTT_TOPIC, "#")
    client.subscribe(topic)


# The callback for when a PUBLISH message is received from the server.
def _on_message(client, userdata, msg):
    cmd = msg.payload.decode("utf-8").lower()
    logging.info("Received message on " + msg.topic + ": " + cmd)

    chan = os.path.basename(msg.topic)
    plants = _get_plants_by_channel(chan)

    if not plants:
        logging.warning("No plants defined for channel " + chan)

    for plant in plants:
        pin = plant["WATER_PUMP_GPIO"]
        logging.info("Set pump for " + plant["NAME"] + ": " + str(pin))

        if cmd == "on":
            _turn_on(pin)

        elif cmd == "off":
            _turn_off(pin)

        else:
            logging.warning("Received unknown command " + cmd)


def _on_disconnect(client, userdata, flags, rc):
    logging.warning("Disconnected from client")


if __name__ == '__main__':
    logging.getLogger().setLevel(LOG_LEVEL)
    logging.info("Start watering plants")

    try:
        client = mqtt.Client()
        client.on_connect = _on_connect
        client.on_disconnect = _on_disconnect
        client.on_message = _on_message

        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_forever()

    except KeyboardInterrupt as e:
        logging.info("Interrupt: " + str(e))
        GPIO.cleanup()
