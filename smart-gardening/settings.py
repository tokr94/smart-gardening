#!/usr/bin/python3
import adafruit_mcp3xxx.mcp3008 as MCP
import logging

##################################################################
##################### CUSTOMIZEABLE SETTINGS #####################
##################################################################

LOG_LEVEL    = logging.INFO

CRON_PATTERN = "* 18 * * *"

MQTT_HOST    = "192.168.178.29"
MQTT_PORT    = 1883
MQTT_TOPIC   = "thilokratzer/garden/watering/"

PLANTS = [
    {
        "NAME":                 "Olive",
        "MOISTURE_PIN":         MCP.P0,     # pin of MCP3008
        "MOISTURE_THRESHOLD":   450,        # above threshold the pump will turn on
        "CHECK_MOISTURE_LEVEL": False,      # whether to use moisture sensor
        "WATER_PUMP_GPIO":      26,         # GPIO Number (BCM) for the relay
        "WATER_PUMP_CHANNEL":   "in01",     # input channel for the relay
        "WATERING_TIME":        20,         # seconds, how long the pump should be turned on
    },
    {
        "NAME":                 "Chilli",
        "MOISTURE_PIN":         MCP.P1,
        "MOISTURE_THRESHOLD":   450,
        "CHECK_MOISTURE_LEVEL": False,
        "WATER_PUMP_GPIO":      19,
        "WATER_PUMP_CHANNEL":   "in02",
        "WATERING_TIME":        8,
    },
    {
        "NAME":                 "Salbei/Minze",
        "MOISTURE_PIN":         MCP.P2,
        "MOISTURE_THRESHOLD":   450,
        "CHECK_MOISTURE_LEVEL": False,
        "WATER_PUMP_GPIO":      13,
        "WATER_PUMP_CHANNEL":   "in03",
        "WATERING_TIME":        15,
    },
    {
        "NAME":                 "Tomate",
        "MOISTURE_PIN":         MCP.P3,
        "MOISTURE_THRESHOLD":   450,
        "CHECK_MOISTURE_LEVEL": False,
        "WATER_PUMP_GPIO":      6,
        "WATER_PUMP_CHANNEL":   "in04",
        "WATERING_TIME":        10,
    }
]

##################################################################
################# END OF CUSTOMIZEABLE SETTINGS ##################
##################################################################
