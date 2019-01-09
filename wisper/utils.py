from contextlib import contextmanager


class ServerLog(object):
    """Anonymous event logger for TCP servers"""

    def __init__(self, address):
        self.address = address
        self.peers = dict()

    def server_start(self):
        print 'Wisper server started'
        print 'Listening at', self.address

    def client_connect(self, addr):
        peer_id = len(self.peers) + 1
        self.peers[addr] = peer_id
        print 'Peer %d connected' % self.peers[addr]

    def client_disconnect(self, addr):
        print 'Peer %d disconnected' % self.peers[addr]
        del self.peers[addr]

    def message_received(self, addr, message):
        print 'Received from Peer %d: %s' % (self.peers[addr], message)

    @staticmethod
    def shutdown():
        print 'Wisper server shutdown'


@contextmanager
def socket_context(socket):
    """Socket context manager"""

    s = socket
    try:
        yield s
    finally:
        s.close()
