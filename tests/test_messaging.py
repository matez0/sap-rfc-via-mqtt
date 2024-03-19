import os
from contextlib import closing, contextmanager
from pathlib import Path
from shlex import split
from signal import SIGINT
from subprocess import Popen
from threading import Thread
from time import sleep
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from sap_rfc_via_mqtt.messaging import MessageAdapter, MessageProcessor

TIMEOUT = 5
MQTT_BROKER_HOST = os.environ['MS_MQTT_BROKER_HOST']
TOPIC_REQUEST = os.environ['MS_TOPIC_REQUEST']
TOPIC_RESPONSE_BASE = f'{TOPIC_REQUEST}/resp'


@pytest.fixture
def mqtt_broker():
    with start_mqtt_broker() as broker:
        yield broker


@contextmanager
def start_mqtt_broker():
    BASE_DIR = Path(__file__).resolve().parent

    proc = Popen(split('python startbroker.py'), cwd=BASE_DIR / 'paho.mqtt.testing' / 'interoperability')
    try:
        wait_for_broker_start()
        yield proc
    finally:
        proc.send_signal(SIGINT)
        proc.wait()


def wait_for_broker_start():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    error = None
    for retry in range(9):
        sleep(.2)
        try:
            client.connect(MQTT_BROKER_HOST)
        except OSError as exc:
            error = exc
        else:
            client.disconnect()
            break
    else:
        raise error


@pytest.fixture
def processor_mock():
    processor = MagicMock(spec_set=MessageProcessor)
    processor.process.return_value = b'my-response'
    return processor


@pytest.fixture
def message_adapter(processor_mock):
    with closing(MessageAdapter(processor_mock)) as instance:
        yield instance


@pytest.fixture
def client():
    return Client()


class Client:
    def request(self, request: str | bytes):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
        client.on_connect = self.on_connect
        client.on_subscribe = self.on_subscribe
        client.on_message = self.on_message
        client.on_unsubscribe = self.on_unsubscribe
        userdata = {
            'request': request,
            'response_topic': f'{TOPIC_RESPONSE_BASE}/{uuid4()}',
        }
        client.user_data_set(userdata)
        client.connect(MQTT_BROKER_HOST)

        loop_thread = Thread(target=client.loop_forever, args=(), daemon=True)
        loop_thread.start()
        loop_thread.join(TIMEOUT)
        try:
            assert not loop_thread.is_alive(), 'Request timed out'
        finally:
            if client.is_connected():
                client.disconnect()

        return userdata['response']

    @staticmethod
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"Client failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # We should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            client.subscribe(userdata['response_topic'])
            print('---- Client subscribed for response ----', userdata['response_topic'])

    @staticmethod
    def on_subscribe(client, userdata, mid, reason_code_list, properties):
        assert not reason_code_list[0].is_failure, \
            f"Client failed to subscribe: {reason_code_list[0]}"

        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

        properties = Properties(PacketTypes.PUBLISH)
        properties.ResponseTopic = userdata['response_topic']

        client.publish(TOPIC_REQUEST, userdata['request'], qos=2, properties=properties, retain=True)
        print('>>>> Request sent >>>>', TOPIC_REQUEST, userdata['request'])

    @staticmethod
    def on_message(client, userdata, message):
        print('<<<< Response received <<<<', message.topic, message.payload)
        userdata['response'] = message.payload

        client.unsubscribe(userdata['response_topic'])

    @staticmethod
    def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
        # The reason_code_list is only present in MQTTv5. In MQTTv3 it will always be empty.
        assert not reason_code_list or not reason_code_list[0].is_failure, \
            f"Client failed to unsubscribe: {reason_code_list[0]}"

        client.disconnect()


def test_call_process_with_message_and_respond_with_return_value(mqtt_broker, message_adapter, processor_mock, client):
    request = b'my-request'

    assert client.request(request) == processor_mock.process.return_value

    processor_mock.process.assert_called_once_with(request)


def test_keep_working_when_broker_gets_lost_temporarily(mqtt_broker, message_adapter, processor_mock):
    sleep(1)  # Wait for adapter to connect.
    mqtt_broker.send_signal(SIGINT)
    mqtt_broker.wait()

    with start_mqtt_broker() as restarted_broker:
        assert Client().request(b'my-request') == processor_mock.process.return_value


def test_no_interference_when_sending_multiple_requests(mqtt_broker, message_adapter, processor_mock, client):
    requests = [b'my-request', b'my-other-request']
    responses = [b'my-response', b'my-other-response']
    processor_mock.process.side_effect = responses

    assert client.request(requests[0]) == responses[0]

    processor_mock.process.assert_called_once_with(requests[0])

    assert client.request(requests[1]) == responses[1]

    processor_mock.process.assert_called_with(requests[1])
