import logging
import time

from sensors import Pump, _clean_up
from settings import SETTINGS


def _initialize_clients():

    clients = []
    host = SETTINGS["MQTT"]["MQTT_HOST"]
    port = SETTINGS["MQTT"]["MQTT_PORT"]

    for plant in SETTINGS["PLANTS"]:
        pump = Pump(
            pin=plant["MOISTURE_PIN"],
            topic=SETTINGS["MQTT"]["MQTT_TOPIC"],
            channel=plant["WATER_PUMP_CHANNEL"])

        pump.connect(host, port)
        pump.loop_start()

        name, chan = plant["NAME"], plant["WATER_PUMP_CHANNEL"]
        logging.info("initialized water pump client for plant '%s' (%s)" % (name, chan))

        clients.append(pump)

    return clients


def watering_plants():

    clients = _initialize_clients()

    while True:
        _any_connected = False

        for pump in clients:
            if pump.is_connected():
                pump.publish_status_async()
                _any_connected = True

        if not _any_connected:
            break

        time.sleep(SETTINGS["STATUS_TIMEOUT_IN_SEC"])


if __name__ == "__main__":
    logging.getLogger().setLevel(SETTINGS["LOG_LEVEL"])
    logging.info("start watering plants")

    try:
        watering_plants()

    except Exception as e:
        logging.error("received exception - exiting script")
        logging.error(e)

    finally:
        _clean_up()
        logging.info("all clients were shut down - exiting script")








