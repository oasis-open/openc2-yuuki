

class Consumer():
    def __init__(self, *, profile=None, transport=None, serialization=None):
        self.profile = profile
        self.transport = transport
        self.serialization = serialization

    def start(self):
        self.transport.set_profile(self.profile)
        self.transport.set_serialization(self.serialization)
        

        self.transport.start()