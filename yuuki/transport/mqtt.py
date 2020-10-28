"""
MQTT Transport

Contains the transport class to instantiate, and its config to customize.

The tranport receives messages, then sends them on to a handler,
and awaits a response to send back.

Use as an argument to a Consumer constructor, eg:

mqtt_config = MqttConfig(broker=...)
mqtt_transport = Mqtt(mqtt_config)
my_openc2_consumer = Consumer(transport=mqtt_transport, ...)
my_openc2_consumer.start()

"""

import asyncio
import socket
import logging
from math import inf
from dataclasses import dataclass, field
from typing import List, Optional
import pprint
import paho.mqtt.client as mqtt
from .base import Transport

# ----- Configuration ----

@dataclass
class Authorization():
    enable : bool = False
    user_name : Optional[str] = None
    pw : Optional[str] = None

@dataclass
class Authentication():
    enable : bool = False
    certfile: Optional[str] = None
    keyfile:  Optional[str] = None
    ca_certs: Optional[str] = None

@dataclass
class BrokerConfig():
    socket : str = '127.0.0.1:1833'
    client_id : str = ''
    keep_alive : int = 60
    authorization : Authorization = field(default_factory=Authorization)
    authentication : Authentication = field(default_factory=Authentication)

@dataclass
class Subscription():
    '''Topic Filter and QoS for one subscription.
    
    Create one of these for each command source.
    '''
    topic_filter : str = 'yuuki_user/oc2/cmd'
    qos : int = 1

@dataclass
class Publish():
    '''Topic Name and QoS for one publish destination.
    
    Create one of these for each response destination.
    '''
    topic_name : str = 'yuuki_user/oc2/rsp'
    qos : int = 1

@dataclass
class OpenC2Options():
    use_oc2_mqtt_header : bool = True

@dataclass
class MqttConfig():
    '''Configuration object to be passed to Mqtt Transport init.

    Accept the defaults or customize as necessary.

    broker: socket, client_id, authorization, authentication
    subscriptions: list of topic_name/qos objects for commands
    publishes: list of topic_filter/qos objects for responses
    '''
    broker : BrokerConfig = field(default_factory=BrokerConfig)
    subscriptions : List[Subscription] = field(default_factory=lambda : [Subscription()])
    publishes : List[Publish] = field(default_factory=lambda : [Publish()])
    oc2_options : OpenC2Options = field(default_factory=OpenC2Options)
    


# ----- Transport ----

class Mqtt(Transport):
    '''Implements Transport base class for MQTT'''

    def __init__(self, mqtt_config: MqttConfig):
        super().__init__(mqtt_config)
        self.in_msg_queue = asyncio.Queue()

    def process_config(self):
        self.host, port = self.config.broker.socket.split(':')
        self.port = int(port)
    
    def start(self):
        mqtt_client = _MqttClient(cmd_subs = self.config.subscriptions,
                                  rsp_pubs = self.config.publishes,
                                  host = self.host,
                                  port = self.port,
                                  keep_alive = self.config.broker.keep_alive,
                                  use_credentials =self.config.broker.authorization.enable,
                                  user_name = self.config.broker.authorization.user_name,
                                  password  = self.config.broker.authorization.pw,
                                  client_id = self.config.broker.client_id,
                                  use_tls   = self.config.broker.authentication.enable,
                                  ca_certs  = self.config.broker.authentication.ca_certs,
                                  certfile  = self.config.broker.authentication.certfile,
                                  keyfile   = self.config.broker.authentication.keyfile)
        


        mqtt_client.msg_handler = self.on_oc2_msg
        mqtt_client.connect()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(mqtt_client.main())

    def handle_byte_header_in(self, raw_data: bytes):
        header_bytes = raw_data[0:2]
        raw_data = raw_data[2:]
        error_msgs = []

        fixed_4 = int(header_bytes.hex(), 16) >> 12
        msg_type_4 = (int(header_bytes.hex(), 16) & int('0FFF',16)) >> 8
        serial_8 = int(header_bytes.hex(), 16) & int('00FF', 16)

        if fixed_4 != 9:
            error_msgs.append('First 4 bits of header should be 1001 (decimal 9), but header is {}'.format(header_bytes))
        if msg_type_4 != 0:
            error_msgs.append('Second 4 bits of header should be 0 for request, but header is {}'.format(header_bytes))
        if serial_8 != 1:
            error_msgs.append('Second byte of header should be 1 for hardcoded JSON, but header is {}'.format(header_bytes))

        if len(error_msgs) > 0:
            for msg in error_msgs:
                logging.error(msg)
            raise ValueError('Bad MQTT 2 byte header. Is it missing? Received {}'.format(header_bytes))
        return raw_data
    
    def handle_byte_header_out(self, serialized_msg):
        header_bytes = bytes.fromhex('9101')
        serialized_msg = header_bytes + bytes(serialized_msg, 'utf-8')
        return serialized_msg

    
    async def on_oc2_msg(self, raw_data, response_queue):
        '''Called whenever our real mqtt client gets a message'''
        if self.config.oc2_options.use_oc2_mqtt_header:
            raw_data = self.handle_byte_header_in(raw_data)
        try:
            result = await self.get_response(raw_data)
            if self.config.oc2_options.use_oc2_mqtt_header:
                result = self.handle_byte_header_out(result)

            response_queue.put_nowait(result)
        except Exception as e:
            logging.error('Message Handling Failed {}'.format(e))


class _MqttClient():
    '''Wrapper around the paho mqtt client'''
    def __init__(self,
                 cmd_subs,
                 rsp_pubs,
                 host,
                 port,
                 keep_alive,
                 use_credentials,
                 user_name,
                 password,
                 client_id,
                 use_tls,
                 ca_certs,
                 certfile,
                 keyfile):
        self.cmd_subs = cmd_subs
        self.rsp_pubs = rsp_pubs
        self.host = host
        self.port = port
        self.keep_alive = keep_alive
        self.use_credentials = use_credentials
        self.user_name = user_name
        self.password = password
        self.client_id = client_id
        self.use_tls = use_tls
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile


        self._client = None
        self.msg_handler = None
        self.loop = asyncio.get_event_loop()
        self.misc_loop_task = None
        self.in_msg_queue = asyncio.Queue()
        self.out_msg_queue = asyncio.Queue()

        self.setup_client()
        self.disconnected = self.loop.create_future()

    def setup_client(self):
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.on_connect     = self._on_connect
        self._client.on_disconnect  = self._on_disconnect
        self._client.on_subscribe   = self._on_subscribe
        self._client.on_unsubscribe = self._on_unsubscribe
        self._client.on_message     = self._on_message
        self._client.on_publish     = self._on_publish
        self._client.on_log         = self._on_log
        self._client.on_socket_open = self.on_socket_open
        self._client.on_socket_close = self.on_socket_close
        self._client.on_socket_register_write = self.on_socket_register_write
        self._client.on_socket_unregister_write = self.on_socket_unregister_write
        
        if self.use_credentials:
            self._client.username_pw_set(self.user_name, password=self.password)

    def _on_log(self, client, userdata, level, buf):
        pass

    def _on_connect(self, client, userdata, flags, rc):
        logging.debug('OnConnect')
        for sub_info in self.cmd_subs:
            self.subscribe(sub_info.topic_filter, sub_info.qos)

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        logging.debug('OnSubscribe')

    def _on_unsubscribe(self, client, userdata, mid):
        pass

    def _on_publish(self, client, userdata, mid):
        logging.debug('OnPublish')

    def _on_message(self, client, userdata, msg):
        logging.debug('OnMessage: {}'.format( msg.payload))
        self.in_msg_queue.put_nowait(msg.payload)
        
    def _on_disconnect(self, client, userdata, rc):
        logging.debug('OnDisconnect')
        self.disconnected.set_result('disconnected')
    
    def on_socket_open(self, client, userdata, sock):
        def cb():
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc_loop_task = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        self.loop.remove_reader(sock)
        self.misc_loop_task.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        def cb():
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        while True:
            if self._client.loop_misc() != mqtt.MQTT_ERR_SUCCESS:
                break
            while self.out_msg_queue.qsize() > 0:
                response = self.out_msg_queue.get_nowait()
                self.out_msg_queue.task_done()
                for rsp_pub_info in self.rsp_pubs:
                    self.publish(rsp_pub_info.topic_name, response, rsp_pub_info.qos)
            if self.in_msg_queue.qsize() > 0:
                msg = self.in_msg_queue.get_nowait()
                self.in_msg_queue.task_done()
                try:
                    await self.msg_handler(msg, self.out_msg_queue)
                except Exception as e:
                    logging.error(e)
                    raise
            
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError as e:
                break

    def connect(self):
        try:
            if self.use_tls:
                logging.info('Will use TLS')
                self._client.tls_set(ca_certs=self.ca_certs, certfile=self.certfile, keyfile=self.keyfile)
            logging.info('Connecting --> {}:{} --> keep_alive:{} ...'.format(self.host, self.port, self.keep_alive))
            self._client.connect(self.host, self.port, keepalive=self.keep_alive)
            
        except ConnectionRefusedError:
            logging.error('BrokerConfig at {}:{} refused connection'.format(self.host,self.port))
            raise
        
        self._client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def subscribe(self,topic_filter, qos):
        logging.info('Subscribing --> {} {} ...'.format( topic_filter, qos))
        self._client.subscribe(topic_filter, qos)
    
    def publish(self, topic, payload, qos):
        try:
            msg_info = self._client.publish(topic, payload=payload, qos=qos)
            logging.info('Publishing --> qos: {} \n{}'.format(qos, payload ))
        except Exception as e:
            logging.error('Publish failed', e)
    
    def disconnect(self):
        self._client.disconnect()

    async def main(self):
        try:
            await self.disconnected 
        except asyncio.CancelledError:
            pass
    