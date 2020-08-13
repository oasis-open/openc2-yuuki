

def oc2_pair(action_name, target_name):
    def _register(method):
        method.is_oc2_pair = True
        method.action_name = action_name
        method.target_name = target_name
        return method
    return _register

def oc2_not_found(method):
    method.is_oc2_not_found = True
    return method


class OC2PairMeta(type):
    
    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        class OC2MethodGrabber(dict):
            def __init__(self):
                self.oc2_methods = []
                self.oc2_not_found_method = None
            def __setitem__(self, key, value):
                if key not in self.oc2_methods:
                    if hasattr(value, 'is_oc2_pair'):
                        self.oc2_methods.append(key)
                if self.oc2_not_found_method is None:
                    if hasattr(value, 'is_oc2_not_found'):
                        self.oc2_not_found_method = key
                dict.__setitem__(self, key, value)
        return OC2MethodGrabber()
    
    def __new__(cls, name, bases, classdict):
        retval = type.__new__(cls, name, bases, dict(classdict))
        retval.oc2_methods = classdict.oc2_methods
        retval.oc2_not_found_method = classdict.oc2_not_found_method
        return retval