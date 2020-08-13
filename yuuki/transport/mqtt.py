import asyncio
import socket
from math import inf
import paho.mqtt.client as mqtt
from .base import Transport

class Mqtt(Transport):
    def __init__(self, mqtt_config):
        super().__init__(mqtt_config)
        self.in_msg_queue = asyncio.Queue()

    @property
    def max_responses_per_input_message(self):
        return inf
    
    @property
    def rate_limit(self):
        return 30
    
    def parse_config(self):
        socket = self.config['broker']['socket']
        self.host, self.port = socket.split(':')
        self.port = int(self.port)
        self.client_id = self.config['broker']['client_id']
        self.use_credentials = self.config['broker']['authorization']['enable']
        self.user_name = self.config['broker']['authorization']['user_name']
        self.password = self.config['broker']['authorization']['pw']

        self.cmd_subs = self.config['subscribe']['commands']
        self.rsp_pubs = self.config['publish']['responses']
    
    def start(self):
        mqtt_client = _MqttClient(self.cmd_subs,
                                  self.rsp_pubs,
                                  self.host,
                                  self.port,
                                  self.use_credentials,
                                  self.user_name,
                                  self.password,
                                  self.client_id)
        
        mqtt_client.msg_handler = self.on_oc2_msg
        mqtt_client.connect()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(mqtt_client.main())

    async def on_oc2_msg(self, raw_data, response_queue):
        result = await self.get_response(raw_data)
        response_queue.put_nowait(result)



class _MqttClient():
    def __init__(self,
                 cmd_subs,
                 rsp_pubs,
                 host,
                 port,
                 use_credentials,
                 user_name,
                 password,
                 client_id):
        self.cmd_subs = cmd_subs
        self.rsp_pubs = rsp_pubs
        self.host = host
        self.port = port
        self.use_credentials = use_credentials
        self.user_name = user_name
        self.password = password
        self.client_id = client_id
        
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

    async def worker(self, in_msg_queue):
        oc2_msg = await in_msg_queue.get()

    def _on_log(self, client, userdata, level, buf):
        pass
    def _on_connect(self, client, userdata, flags, rc):
        for sub_info in self.cmd_subs:
            self.subscribe(sub_info['topic_filter'])
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        pass
    def _on_unsubscribe(self, client, userdata, mid):
        pass
    def _on_publish(self, client, userdata, mid):
        pass
    def _on_message(self, client, userdata, msg):
        self.in_msg_queue.put_nowait(msg.payload)
        
    def _on_disconnect(self, client, userdata, rc):
        pass
    
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
                    self.publish(rsp_pub_info['topic_name'], response)
            if self.in_msg_queue.qsize() > 0:
                msg = self.in_msg_queue.get_nowait()
                self.in_msg_queue.task_done()
                await self.msg_handler(msg, self.out_msg_queue)
            
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    def connect(self):
        try:
            self._client.connect(self.host, self.port, keepalive=5)
        except ConnectionRefusedError:
            print('Broker refused connection')
            return
        self._client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def subscribe(self,topic_filter):
        self._client.subscribe(topic_filter)
    
    def publish(self, topic, payload):
        try:
            msg_info = self._client.publish(topic, payload=payload)
        except Exception as e:
            print('problem ', e)
    
    def disconnect(self):
        self._client.disconnect()

    async def main(self):
        try:
            await self.disconnected 
        except asyncio.CancelledError:
            pass
    