import json
import logging
from .base import _Serializer
from ..openc2.oc2_types import OC2Response, StatusCode



class Json(_Serializer):
    @staticmethod
    def serialize(obj : OC2Response):
        logging.debug('Json Serialize')
        return _JsonEncoder().encode(obj)

    @staticmethod
    def deserialize(obj):
        logging.debug('Json Deserialize')
        try:
            retval = json.loads(obj)
            if isinstance(retval, str):
                retval = json.loads(retval)
        except Exception as e:
            print('BAD',e)
            raise
        return retval

class _JsonEncoder(json.JSONEncoder):
    def __init__(self):
        super().__init__()
    def default(self, o : OC2Response):
        if isinstance(o, OC2Response):
            retval = {}
            for key in o.keys_for_serializing:
                retval[key] = getattr(o,key)
            return retval
        if isinstance(o, StatusCode):
            return o.text()
        return json.JSONEncoder.default(self, retval)
        