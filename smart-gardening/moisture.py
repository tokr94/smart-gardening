import logging
import time

from sensors import MoistureSensor
from settings import SETTINGS


def _initialize_clients():

    clients = []
    host = SETTINGS["MQTT"]["MQTT_HOST"]
    port = SETTINGS["MQTT"]["MQTT_PORT"]

    for plant in SETTINGS["PLANTS"]:
        mcp = MoistureSensor(
            pin=plant["WATER_PUMP_GPIO"],
            topic=SETTINGS["MQTT"]["MQTT_TOPIC"],
            channel=plant["WATER_PUMP_CHANNEL"],
            threshold=plant["MOISTURE_THRESHOLD"],
            timeout=plant["WATERING_TIME"])

        mcp.connect(host, port)
        mcp.loop_start()

        name, chan = plant["NAME"], plant["WATER_PUMP_CHANNEL"]
        logging.info("initialized moisture sensor for plant %s (%s)" % (name, chan))

        clients.append(mcp)

    return clients


def check_moisture_level():

    clients = _initialize_clients()

    while True:
        _any_connected = False

        for mcp in clients:
            if mcp.is_connected():
                mcp.publish_reading_async()
                _any_connected = True

        if not _any_connected:
            break

        time.sleep(SETTINGS["STATUS_TIMEOUT_IN_SEC"])


if __name__ == '__main__':
    logging.getLogger().setLevel(SETTINGS["LOG_LEVEL"])
    logging.info("start measuring moisture level")

    try:
        check_moisture_level()

    except Exception as e:
        logging.error("received exception - exiting script")
        logging.error(e.message)
