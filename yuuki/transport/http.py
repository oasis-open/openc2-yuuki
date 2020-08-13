from quart import (
    Quart,
    request
)

from .base import Transport


class Http(Transport):
    def __init__(self, http_config):
        super().__init__(http_config)
        self.app = Quart(__name__)
        self.setup(self.app)
    
    @property
    def max_responses_per_input_message(self):
        return 1
    
    @property
    def rate_limit(self):
        return 30

    def parse_config(self):
        consumer_socket = self.config['consumer_socket']
        
        self.host, self.port = consumer_socket.split(':')

        use_tls = self.config['use_tls']
        if use_tls:
            raise ValueError('tls is not supported currently in http transport')
    
    def setup(self, app):
        @app.route('/', methods=['POST'])
        async def receive():
            raw_data = await request.get_data()
            result = await self.get_response(raw_data)
            return result

    def start(self):
        self.app.run(port=self.port, host=self.host)
        

