import asyncio
from ..openc2.oc2_types import OC2Response, StatusCode


class Transport():
    """Base class for any transports implemented."""
    
    def __init__(self, transport_config):
        self.config = transport_config
        self.process_config()
    
    def process_config(self):
        raise NotImplementedError

    def set_cmd_handler(self, cmd_handler):
        self.cmd_handler = cmd_handler

    def set_serialization(self, serialization):
        self.serialization = serialization
    
    def start(self):
        raise NotImplementedError

    async def get_response(self, raw_data):
        
        try:
            data_dict = self.serialization.deserialize(raw_data)
        except Exception as e:
            retval = OC2Response(status=StatusCode.BAD_REQUEST,
                                 status_text='Deserialization failed: {}'.format(e))
            return self.serialization.serialize(retval)
        try:
            actuator_func = self.cmd_handler.get_actuator_func(data_dict)
        except Exception as e:
            retval = OC2Response(status=StatusCode.BAD_REQUEST,
                                 status_text='Validation failed: {}'.format(e))
            return self.serialization.serialize(retval)
        
        loop = asyncio.get_running_loop()
        try:
            oc2_rsp = await loop.run_in_executor(None, actuator_func)
        except Exception as e:
            retval = OC2Response(status=StatusCode.INTERNAL_ERROR,
                                 status_text='Actuator failed: {}'.format(e))
            return self.serialization.serialize(retval)

        try:
            return self.serialization.serialize(oc2_rsp)
        except Exception as e:
            retval = OC2Response(status=StatusCode.INTERNAL_ERROR,
                                 status_text='Serialization failed: {}'.format(e))
            return self.serialization.serialize(retval)