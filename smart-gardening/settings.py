import logging


##################################################################
##################### CUSTOMIZEABLE SETTINGS #####################
##################################################################

LOG_LEVEL = logging.DEBUG

MQTT_HOST = "192.168.178.29"
MQTT_PORT = 1883
MQTT_TOPIC = "thilokratzer/garden/watering/"

# GPIO Number (BCM) for the relais
WATER_PUMP_GPIO = {
    "in01": 5,
    "in02": 6,
    "in03": 13,
    "in04": 19
}

WATER_PUMP_TIMEOUT_IN_SEC = {
    "in01": 10,
    "in02": 10,
    "in03": 10,
    "in04": 10
}

##################################################################
################# END OF CUSTOMIZEABLE SETTINGS ##################
##################################################################
