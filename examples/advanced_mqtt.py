from yuuki.openc2.profile import (
    ActuatorProfile,
    oc2_pair, 
    oc2_not_found
)

from yuuki.openc2.oc2_types import (
    OC2Response,
    StatusCode
)

from yuuki.consumer import (
    Consumer,
    parse_custom_config
)

from yuuki.openc2.validate import validate_cmd
from yuuki.serialize import Json
from yuuki.transport import Mqtt


class ProfileSLPF(ActuatorProfile):
    def __init__(self, validator=None, nsid='slpf'):
        super().__init__(validator, nsid)
    
    @oc2_pair('query', 'features')
    def func1(self, oc2_cmd):
        oc2_rsp = OC2Response(
            status=StatusCode.OK, 
            status_text='received {}'.format(str(oc2_cmd)))

        return Json.serialize(oc2_rsp)
    
    @oc2_pair('deny', 'domain')
    def func2(self, oc2_cmd):
        oc2_rsp = OC2Response(
            status=StatusCode.OK,
            status_text='received {}'.format(str(oc2_cmd)))

        return Json.serialize(oc2_rsp)
    
    @oc2_not_found
    def func3(self, oc2_cmd):
        oc2_rsp = OC2Response(
            status=StatusCode.NOT_FOUND,
            status_text='received {}'.format(str(oc2_cmd)))

        return Json.serialize(oc2_rsp)



if __name__ == '__main__':
    yuuki_config = parse_custom_config('yuuki_config.json')
    mqtt_config = yuuki_config['transports']['mqtt']
    
    consumer = Consumer(
        profile=ProfileSLPF(validator=validate_cmd),
        transport=Mqtt(mqtt_config),
        serialization=Json )

    consumer.start()