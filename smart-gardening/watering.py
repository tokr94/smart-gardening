#!/usr/bin/python3
import base64
import logging
import os
import paho.mqtt.client as mqtt
import sys

from ansible_vault import Vault
from pushnotifier.PushNotifier import PushNotifier
from argparse import ArgumentParser
from settings import *
from threading import Event, Lock, Thread

try:
    import RPi.GPIO as GPIO

except ImportError as ie:
    logging.warning(str(ie) + " - using mock instead")
    from mocks.GPIOMock import GPIO


lock = Lock()  # lock for relay usage
event_per_channel = dict()
credentials = None


def _send_text(text):
    if not credentials or credentials["USE_MOCK"]:
        pass
    else:
        username     = credentials["USER"]
        password     = credentials["PASSWORD"]
        package_name = credentials["PACKAGE"]
        api_key      = credentials["API_KEY"]
        devices      = credentials["DEVICES"]
        try:
            pn = PushNotifier(username, password, package_name, api_key)
            rc = pn.send_text(text, devices, silent=False)
            if rc != 200:
                raise Exception("`send_text` returned exit code " + str(rc))
            logging.debug("Successfully sent message to " + str(devices))
        except Exception as e:
            logging.error("Failed to send message to pushnotifier: " + str(e))


def _turn_on(pin, plant, turn_off_event):
    logging.debug("Trying to acquire lock for pin " + str(pin))
    lock.acquire(blocking=True)

    if turn_off_event.is_set():
        logging.info("Shutdown event already set for pin " + str(pin) + ": ignore")
        lock.release()
        return

    logging.info("Turn on pin " + str(pin))
    _send_text("Start watering " + plant)
    GPIO.output(pin, GPIO.LOW)

    turn_off_event.wait()
    _turn_off(pin, plant)


def _turn_off(pin, plant):
    logging.info("Turn off pin " + str(pin))
    _send_text("Stop watering " + plant)
    GPIO.output(pin, GPIO.HIGH)
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
        name = plants[0]["NAME"]

        if cmd == "on":
            if event_per_channel.get(chan) is not None:
                logging.warning("Pump already running and waiting for shutdown event")
            else:
                event = Event()
                event_per_channel[chan] = event
                thread = Thread(target=_turn_on, args=(pin, name, event))
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


def _initialize_gpio_pins():
    pins = [plant["WATER_PUMP_GPIO"] for plant in PLANTS]
    logging.info("Setup output pins (BCM): " + str(pins))
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pins, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setwarnings(False)


def _read_credentials(vault_password_file):
    file = os.path.expanduser(vault_password_file)
    _pass = open(file, "r").read().splitlines()[0]
    vault = Vault(_pass)
    data = vault.load(open("vault.yml", "r").read())
    return data["PUSHNOTIFIER"]


def main():
    try:
        _initialize_gpio_pins()

        client = mqtt.Client()
        client.on_connect = _on_connect
        client.on_disconnect = _on_disconnect
        client.on_message = _on_message

        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_forever()

    except (KeyboardInterrupt, Exception) as e:
        logging.error("Got exception in main loop: " + str(e))
        _send_text(credentials["PACKAGE"] + " got exception in main loop")
        client.loop_stop()

    finally:
        # make sure pumps are turned off if program crashes
        for plant in PLANTS:
            pin = plant["WATER_PUMP_GPIO"]
            name = plant["NAME"]
            _turn_off(pin, name)

        GPIO.cleanup()


if __name__ == '__main__':
    logging.getLogger().setLevel(LOG_LEVEL)
    logging.info("Start watering plants")

    parser = ArgumentParser()
    parser.add_argument('--vault-password-file', type=str, required=False, help='vault password file')

    args = parser.parse_args()
    file = args.vault_password_file

    if file:
        try:
            credentials = _read_credentials(file)

            logging.info("Successfully fetched credentials for pushnotifier")
            _send_text("Hello from " + credentials["PACKAGE"])

        except FileNotFoundError as e:
            logging.warning("Could not read vault password: " + str(e))
            credentials = None

    main()
