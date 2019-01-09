from secure_message_pb2 import SecureMessage


def serialize(body, sender):
    """Serialize outbound message with protobuf"""

    sm = SecureMessage()
    sm.body = body
    sm.sender = sender
    return sm.SerializeToString()


def deserialize(data):
    """Deserialize inbound message with protobuf"""

    sm = SecureMessage()
    sm.ParseFromString(data)
    return sm
