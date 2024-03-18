import logging
import os
from abc import ABC, abstractmethod
from threading import Thread

import paho.mqtt.client as mqtt

MQTT_BROKER_HOST = os.environ['MS_MQTT_BROKER_HOST']
TOPIC_REQUEST = os.environ['MS_TOPIC_REQUEST']

logger = logging.getLogger(__name__)
logger.propagate = False


class MessageProcessor(ABC):
    @abstractmethod
    def process(self, message: bytes) -> bytes:
        pass


class MessageAdapter:
    def __init__(self, processor: MessageProcessor):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5, userdata=processor)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_unsubscribe = self._on_unsubscribe
        self.client = client
        client.connect(MQTT_BROKER_HOST)
        self.loop_thread = Thread(target=client.loop_forever, args=(), daemon=True)
        self.loop_thread.start()

    def close(self):
        self.client.unsubscribe(TOPIC_REQUEST)
        self.loop_thread.join()

    @staticmethod
    def _on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            # loop_forever() will retry connection.
            logger.error("Failed to connect; reason=%s", reason_code)
        else:
            # We should always subscribe from on_connect callback to be sure
            # our subscription is persisted across reconnections.
            client.subscribe(TOPIC_REQUEST)

    @staticmethod
    def _on_message(client, userdata, message):
        logger.debug(
            "Request received; topic=%s, payload=%s, properties=%s",
            message.topic, message.payload, message.properties
        )

        response = userdata.process(message.payload)

        try:
            response_topic = message.properties.ResponseTopic
        except AttributeError:
            pass
        else:
            client.publish(response_topic, response, qos=1)

    @staticmethod
    def _on_unsubscribe(client, userdata, mid, reason_code_list, properties):
        # The reason_code_list is only present in MQTTv5. In MQTTv3 it will always be empty.
        if reason_code_list and reason_code_list[0].is_failure:
            logger.error('Failed to unsubscribe; reason=%s', reason_code_list[0])

        client.disconnect()
