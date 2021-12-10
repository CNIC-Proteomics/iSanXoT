from abc import abstractmethod

from typing import cast, Any, Dict, Optional


__all__ = [
    'Serializer',
    'Pickle',
]


class Serializer:
    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        raise NotImplemented

    @abstractmethod
    def deserialize(self, msg: bytes) -> Any:
        raise NotImplemented


try:  # pragma: nocover
    import cPickle
except:  # pragma: nocover
    cPickle = None
    import pickle
else:  # pragma: nocover
    pickle = cPickle


class Pickle(Serializer):
    def __init__(self, protocol=pickle.DEFAULT_PROTOCOL) -> None:
        self.protocol = protocol

    def serialize(self, value: Any) -> bytes:
        return pickle.dumps(value, self.protocol)

    def deserialize(self, msg: bytes) -> Any:
        return pickle.loads(msg)


try:
    import msgpack
except:  # pragma: nocover
    pass
else:
    __all__ += [
        'Msgpack',
    ]


    class Msgpack(Serializer):
        def __init__(self, pack_kwargs: Optional[Dict[str, Any]]=None, unpack_kwargs: Optional[Dict[str, Any]]=None) -> None:
            self.pack_kwargs = pack_kwargs or dict(use_bin_type=True)
            self.unpack_kwargs = unpack_kwargs or dict(raw=False)

        def serialize(self, value: Any) -> bytes:
            return cast(bytes, msgpack.packb(value, **self.pack_kwargs))

        def deserialize(self, msg: bytes) -> Any:
            return msgpack.unpackb(msg, **self.unpack_kwargs)
