
from functools import partial
from .util import OC2PairMeta


class ActuatorProfile(metaclass=OC2PairMeta):
    def __init__(self,validator=None, nsid=None):
        self.nsid = nsid
        self.validator = validator
    
    def get_actuator_func(self,data_dict):
        func = None
        oc2_cmd = self.validator(data_dict)

        for func_name in self.oc2_methods:
            func = getattr(self, func_name)
            if (func.action_name == oc2_cmd.action and 
                func.target_name == oc2_cmd.target_name):
                break
            else:
                func = None

        if func is not None:
            my_callable = partial(func, oc2_cmd)
            return my_callable
        else:
            func_name = getattr(self, 'oc2_not_found_method')
            func = getattr(self, func_name)
            my_callable = partial(func, oc2_cmd)
            return my_callable
        
        raise NotImplementedError

