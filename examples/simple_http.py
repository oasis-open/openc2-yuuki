from yuuki import *


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
    http_config = yuuki_config['transports']['http']
    
    consumer = Consumer(
        profile=ProfileSLPF(validator=validate_cmd),
        transport=Http(http_config),
        serialization=Json )

    consumer.start()