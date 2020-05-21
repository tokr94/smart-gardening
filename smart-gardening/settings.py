import logging

##################################################################
##################### CUSTOMIZEABLE SETTINGS #####################
##################################################################
SETTINGS = {
    "LOG_LEVEL": logging.INFO,
    "MQTT": {
        "MQTT_HOST": "192.168.178.29",
        "MQTT_PORT": 1883,
        "MQTT_TOPIC": "thilokratzer/garden/watering",
    },
    "PLANTS": [
        {
            "NAME":                 "Tomaten",
            "MOISTURE_CHANNELS":    [1, 2],     # of MCP3008
            "MOISTURE_THRESHOLD":   450,        # above threshold the pump will turn on
            "WATER_PUMP_GPIO":      23,         # GPIO Number (BCM) for the relais
            "WATER_PUMP_CHANNEL":   "IN01",     # input channel for the relais
            "WATERING_TIME":        10,         # seconds, how long the pump should be turned on
        },
        {
            "NAME":                 "Salat",
            "MOISTURE_CHANNELS":    [3, 4],
            "MOISTURE_THRESHOLD":   450,
            "WATER_PUMP_GPIO":      24,
            "WATER_PUMP_CHANNEL":   "IN02",
            "WATERING_TIME":        12,
        },
    ]
}
##################################################################
################# END OF CUSTOMIZEABLE SETTINGS ##################
##################################################################