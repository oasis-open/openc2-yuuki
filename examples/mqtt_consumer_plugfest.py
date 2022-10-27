"""
Example Implementation of an OpenC2 MQTT Consumer
"""
from oc2_arch.transports import (
    MqttTransport, MqttConfig, MQTTAuthorization, MQTTAuthentication, BrokerConfig, Publication, Subscription
)

from oc2_arch import Consumer
# import actuator profiles for your consumer

from actuators.database import database
from actuators.sbom import sbom
from actuators.slpf import slpf


consumer = Consumer(rate_limit=60, versions=['1.0'], actuators=[sbom, database, slpf])

host = '35.221.11.97'
port = 1883
topics = ['oc2/cmd', 'oc2/cmd/ap/slpf', 'oc2/cmd/ap/database', 'oc2/cmd/ap/sbom']

mqtt_config = MqttConfig(
    broker=BrokerConfig(
        host=host,
        port=port,
        client_id='',
        keep_alive=300,
        authorization=MQTTAuthorization(
            enable=True,
            username='plug',
            password='fest'
        ),
        authentication=MQTTAuthentication(
            enable=False,
            certfile=None,
            keyfile=None,
            ca_certs=None
        )
    ),
    subscriptions=[Subscription(topic=t, qos=1) for t in topics],
    publications=[
        Publication(
            topic='oc2/rsp',
            qos=1
        )
    ]
)

mqtt_consumer = MqttTransport(consumer=consumer, config=mqtt_config)
print("starting consumer")
mqtt_consumer.start()
