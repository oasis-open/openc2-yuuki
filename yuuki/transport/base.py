import asyncio
from abc import ABC, abstractmethod


class _TransportBehavior(ABC):
    @property
    @abstractmethod
    def max_responses_per_input_message(self):
        pass

    @property
    @abstractmethod
    def rate_limit(self):
        pass



class Transport(_TransportBehavior):
    def __init__(self, transport_config):
        self.config = transport_config
        self.parse_config()
    
    def parse_config(self):
        raise NotImplementedError

    def set_profile(self, profile):
        self.profile = profile

    def set_serialization(self, serialization):
        self.serialization = serialization
    
    def start(self):
        raise NotImplementedError

    async def get_response(self, raw_data):
        data_dict = self.serialization.deserialize(raw_data)
        actuator_func = self.profile.get_actuator_func(data_dict)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, actuator_func)
        return result