#!/usr/bin/python3
import logging
import os
import paho.mqtt.client as mqtt

from settings import *
from threading import Event, Lock, Thread

try:
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

except ImportError as ie:
    logging.warning(str(ie) + " - using mock instead")
    from mocks.GPIOMock import GPIO


lock = Lock()  # lock for relay usage
event_per_channel = dict()


def _turn_on(pin, turn_off_event):
    logging.debug("Trying to acquire lock for pin " + str(pin))
    lock.acquire(blocking=True)

    if turn_off_event.is_set():
        logging.info("Shutdown event already set for pin " + str(pin) + ": ignore")
        lock.release()
        return

    logging.info("Turn on pin " + str(pin))
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    turn_off_event.wait()
    _turn_off(pin)


def _turn_off(pin):
    logging.info("Turn off pin " + str(pin))
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
    try:
        lock.release()
    except RuntimeError as e:
        logging.warning("Failed to release lock for pin " + str(pin) + ": " + str(e))


def _get_plants_by_channel(chan):
    return [plant for plant in PLANTS if plant["WATER_PUMP_CHANNEL"] == chan]


# The callback for when the client receives a CONNACK response from the server.
def _on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    topic = os.path.join(MQTT_TOPIC, "#")
    rc, _ = client.subscribe(topic)
    if rc == mqtt.MQTT_ERR_SUCCESS:
        logging.info("Successfully subscribed topic " + topic)
    else:
        msg = mqtt.error_string(rc)
        logging.error("Subscription failed: " + msg)


# The callback for when a PUBLISH message is received from the server.
def _on_message(client, userdata, msg):
    cmd = msg.payload.decode("utf-8").lower()
    logging.info("Received message on " + msg.topic + ": " + cmd)

    chan = os.path.basename(msg.topic)
    plants = _get_plants_by_channel(chan)

    if not plants:
        logging.warning("No plants defined for channel " + chan)

    if len(plants) > 1:
        logging.warning("Multiple plants for same channel - this can cause serious trouble")

    else:
        pin = plants[0]["WATER_PUMP_GPIO"]

        if cmd == "on":
            if event_per_channel.get(chan) is not None:
                logging.warning("Pump already running and waiting for shutdown event")
            else:
                event = Event()
                event_per_channel[chan] = event
                thread = Thread(target=_turn_on, args=(pin, event))
                thread.daemon = True
                thread.start()

        elif cmd == "off":
            event = event_per_channel.get(chan)
            if event is None:
                logging.warning("No waiting thread found for channel " + chan)
            else:
                event.set()
                event_per_channel.pop(chan)

        else:
            logging.warning("Received unknown command " + cmd)


def _on_disconnect(client, userdata, flags, rc):
    msg = mqtt.error_string(rc)
    logging.warning("Disconnected from client: " + msg)


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
        client.loop_stop()

    finally:
        # make sure pumps are turned off if program crashes
        for plant in PLANTS:
            pin = plant["WATER_PUMP_GPIO"]
            _turn_off(pin)

        GPIO.cleanup()
