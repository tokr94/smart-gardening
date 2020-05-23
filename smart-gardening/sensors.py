import asyncio
import board
import busio
import digitalio
import logging
import os
import paho.mqtt.client as mqtt
import time

from abc import ABC, abstractmethod
from adafruit_mcp3xxx.analog_in import AnalogIn
from adafruit_mcp3xxx.mcp3008 import MCP3008
from threading import Thread

try:
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
except ImportError:
    logging.info("Error importing RPi.GPIO! Using mock instead.")
    from RPi.GPIOMock import GPIO


def _clean_up():
    GPIO.cleanup()


class MQTTClient(ABC):
    def __init__(self, name):
        self.name = name
        self._mqttc = mqtt.Client()
        self._mqttc.on_connect = self._on_connect
        self._mqttc.on_disconnect = self._on_disconnect
        self._mqttc.on_message = self._on_message
        self._connected = False

    @abstractmethod
    def _on_connect(self, client, userdata, flags, rc):
        pass

    @abstractmethod
    def _on_disconnect(self, client, userdata, flags, rc):
        pass

    @abstractmethod
    def _on_message(self):
        pass

    def _log_debug(self, msg):
        logging.debug("[%s] %s" % (self.name, msg))

    def _log_info(self, msg):
        logging.info("[%s] %s" % (self.name, msg))

    def _log_warning(self, msg):
        logging.warning("[%s] %s" % (self.name, msg))

    def is_connected(self):
        return self._connected

    def connect(self, host="localhost", port=1883):
        rc = self._mqttc.connect(host, port, 60)
        self._connected = (rc == 0)
        return rc

    def loop_start(self):
        if self.is_connected():
            self._log_info("start client loop")
            self._mqttc.loop_start()

    def loop_stop(self):
        self._log_info("received shutdown signal")
        self._mqttc.loop_stop()
        self._mqttc.disconnect()
        self._connected = False


class MoistureSensor(MQTTClient):

    def __init__(self, pin, topic, channel, threshold, timeout):
        self.pin = pin
        self.topic = os.path.join(topic, channel)
        self.thresh = threshold
        self.timeout = timeout

        # create the mcp object
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.CE0)
        self._mcp = MCP3008(spi, cs)

        super().__init__(channel)
        self._log_debug("moisture sensor publishing to topic '%s'" % self.topic)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._log_info("successfully connected to client")
        else:
            self._log_warning("connection failed with result code " + str(rc))

    def _on_disconnect(self, client, userdata, flags, rc):
        self._log_info("disconnected from client")

    def _on_message(self, client, userdata, msg):
        pass

    def publish_reading_async(self):
        thread = Thread(target=self._publish(), args=())
        thread.daemon = True
        thread.start()
        self._log_debug("started new thread for publishing")

    def _publish(self):
        if self.is_connected():
            val = self.read(10)
            if val > self.thresh:
                self._mqttc.publish(self.topic, "on")
                time.sleep(self.timeout)
                self._log_info("async publish received timeout")

            self._mqttc.publish(self.topic, "off")
        else:
            self._log_warning("publish failed - client not connected yet")

    def read(self, n=1):
        val = 0.0
        for _ in range(n):
            val += self._mcp.read(self.pin)

        val /= n
        self._log_debug("obtained moisture level %.2f" % val)
        return val

    def voltage(self):
        chan = AnalogIn(self._mcp, self.pin)
        self._log_debug("fetched voltage: %.2f" % chan.voltage)
        return chan.voltage


class Pump(MQTTClient):

    def __init__(self, pin, topic, channel):
        self.pin = pin
        self.topic = os.path.join(topic, channel)
        self._stat = "off"

        super().__init__(channel)
        self._turn_off()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._log_info("subscribe to topic '%s'" % self.topic)
            self._mqttc.subscribe(self.topic)
        else:
            self._log_warning("connection failed with result code " + str(rc))

    def _on_disconnect(self, client, userdata, flags, rc):
        self._log_info("disconnected from client")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        self._log_debug("received message %s: %s" % (msg.topic, payload))

        if payload == "shutdown":
            self.loop_stop()
        elif payload == "off":
            self._turn_off()
        elif payload == "on":
            self._turn_on()
        else:
            self._log_warning("received unknown command '%s'" % payload)

    def _turn_on(self):
        self._log_info("turning on pump")
        self._stat = "on"
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)

    def _turn_off(self):
        self._log_info("turning off pump")
        self._stat = "off"
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.HIGH)

    @asyncio.coroutine
    def publish_status_async(self):
        topic = os.path.join(self.topic, "state")
        self._mqttc.publish(topic, self._stat)
