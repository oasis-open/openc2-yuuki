from abc import ABC, abstractmethod

class _Serializer(ABC):
    
    @staticmethod
    @abstractmethod
    def serialize(obj):
        pass

    @staticmethod
    @abstractmethod
    def deserialize(obj):
        pass