import os
import psutil
import signal
import socket
import threading

from utils import ServerLog, socket_context


class Server(object):
    """Manages a session between two or more clients.

       All inter-client communication remains encrypted between endpoints.

       client_conn_addr_map: (dict) Mapping of socket objects to their endpoint
         addresses

       log: (ServerLog) Handles server event logging. See utils.py
    """

    def __init__(self, host='0.0.0.0', port=4440):
        # Unassigned port:
        # https://www.iana.org/assignments/service-names-port-numbers/
        self.address = (host, port)
        self.client_conn_addr_map = dict()
        self.log = ServerLog(self.address)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow server to reuse address between sessions
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        """Bind address and listen for client connections.

           Only public method of the class
        """

        self.log.server_start()
        self.socket.bind(self.address)
        self.socket.listen(100)
        self._run()

    def _run(self):
        """Accept client connections and create a client thread for each

           KeyboardInterrupt shuts down the server
        """

        # Python2 doesn't manage socket contexts, here's a hand-rolled manager
        with socket_context(self.socket) as client_connection:
            while True:
                try:
                    conn, addr = client_connection.accept()
                    self.log.client_connect(addr)
                    self.client_conn_addr_map[conn] = addr
                    # Notify existing clients of new connection
                    self._relay_message('Peer connected', conn)
                    self._create_client_thread(conn, addr)
                except KeyboardInterrupt:
                    break
            return

    def _create_client_thread(self, conn, addr):
        """Create thread for newly connected client"""

        t = threading.Thread(
            target=self._client_thread, name=None, args=(conn, addr))
        t.setDaemon(True)
        t.start()

    def _client_thread(self, conn, addr):
        """Prepare client connection to begin receiving messages"""

        self._sendall(conn, 'Connected to Wisper server')
        if len(self.client_conn_addr_map) < 2:
            self._sendall(conn, 'Waiting for peers to connect. ' +
                'When connected, type your messages below')
        else:
            self._update_peer_count()
            self._sendall(conn, 'Type your messages below')
        while True:
            try:
                self._route_messages(conn, addr)
            except:
                continue

    def _sendall(self, conn, message):
        """Delineate an"""

        message += '\n'
        conn.sendall(message)

    def _route_messages(self, conn, addr):
        """Route client messages to expected recipients"""

        inbound_message = conn.recv(1024)
        if inbound_message:
            self.log.message_received(addr, inbound_message)
            # When only one client is connected, sent messages have nowhere to go
            if len(self.client_conn_addr_map) == 1:
                self._sendall(conn, 'Message not delivered... ' +
                    'Waiting for peers to connect')
            else:
                self._relay_message(inbound_message, conn)
        else:
            # If no data received
            self._remove_client(conn)
            return

    def _relay_message(self, message, conn):
        """Send message to every client but sender"""

        for client in self.client_conn_addr_map.keys():
            if client != conn:
                try:
                    self._sendall(client, message)
                except socket.error:
                    self._remove_client(client)

    def _remove_client(self, conn):
        """Remove unresponsive client connection"""

        removed_client_addr = self.client_conn_addr_map[conn]
        del self.client_conn_addr_map[conn]
        self.log.client_disconnect(removed_client_addr)
        # Notify remaining clients of disconnection
        self._relay_message('Peer disconnected', conn)
        conn.close()
        self._update_peer_count()
        # No more client connections, kill server
        if not self.client_conn_addr_map:
            self._shutdown()

    def _update_peer_count(self):
        """Notify connected clients with number of connected peers"""

        for client in self.client_conn_addr_map.keys():
            self._sendall(client, 'Number of connected peers: ' + str(
                len(self.client_conn_addr_map) - 1))

    def _shutdown(self):
        """End service session

           The subprocess is interrupted to handle TIME_WAIT.
             See http://man7.org/linux/man-pages/man8/netstat.8.html
        """

        self.log.shutdown()
        self.socket.close()
        pid = os.getpid()
        psutil.Process(pid).send_signal(signal.SIGINT)
