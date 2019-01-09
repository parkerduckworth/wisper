import select
import socket
import sys

from encryption import InvalidToken
from protobuf import deserialize, serialize
from utils import socket_context


class Client(object):
    """Each client-side initialization is an instance of this class.

         alias: (str) Username for the duration of a session. Set at startup

         cipher: (Fernet) Cipher object, required for
           encryption/decryption. Must be matching for all connected clients.
           Otherwise, connection will close. Set at startup. See encryption.py
    """

    def __init__(self, host, port, alias, cipher):
        self.server_address = (host, port)
        self.alias = alias
        self.cipher = cipher
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """Initiate connection with the server.

           Only public method of the class. Will call _run() if successful.
        """

        print 'Establishing connection with server...'
        try:
            self.socket.connect(self.server_address)
            self.socket.setblocking(False)
            # Run if connection is successful
            self._run()
        except socket.error, e:
            print 'Server not responding: ' + str(e)
            return

    def _run(self):
        """Detect and select readable sockets until shutdown"""

        # Python2 doesn't manage socket contexts, here's a hand-rolled manager
        with socket_context(self.socket) as server_connection:
            try:
                while True:
                    read_list, write_list, except_list = select.select(
                        [sys.stdin, server_connection], [], [])
                    for sock in read_list:
                        # Check socket type and switch as necessary
                        self._inspect_socket_origin(sock, server_connection)
            except KeyboardInterrupt:
                self._shutdown(server_connection)

    def _inspect_socket_origin(self, current_socket, server_connection):
        """Determine whether selected socket is inbound or outbound"""

        if current_socket == server_connection:
            self._handle_inbound_message(server_connection)
        else:
            self._handle_outbound_message(server_connection)

    def _handle_inbound_message(self, inbound_socket):
        """Receive inbound data and decrypt if necessary

             A message sent by another client will always be encrypted.
             If the message is a status update from the server, it is
             not encrypted.
        """
        inbound_messages = self._receive_data(inbound_socket)
        for message in inbound_messages:
            if self.cipher.is_encrypted(message):
                self._display_client_message(inbound_socket, message)
            else:
                self._display_server_message(message)

    def _receive_data(self, inbound_socket):
        """Receive inbound data and split at delineation

           Messages are read into a list. Separate messages are delineated
             by newlines. A complete packet is delineated by a message with
             an empty string.
        """

        # Remove message delineation
        data = [msg for msg in inbound_socket.recv(1024).split('\n')]
        if data and data[-1] != '':
            print 'Inbound packet was dropped'
        # Remove packet delineation and return list of messages
        return data[:-1]

    def _display_client_message(self, inbound_socket, inbound_message):
        """Display encrypted message sent by peers"""

        try:
            # Decrypt and deserialize
            inbound_message = deserialize(self.cipher.decrypt(inbound_message))
            print '<' + inbound_message.sender + '>', inbound_message.body
        except InvalidToken:
            print 'Secret key does not match.'
            self._shutdown(inbound_socket)

    def _display_server_message(self, server_update):
        """Display status message sent by server"""

        print server_update

    def _handle_outbound_message(self, outbound_socket):
        """Send data to another client"""

        read_in = sys.stdin.readline()
        if read_in.lower() == 'exit()\n':
            self._shutdown(outbound_socket)
        # Serialize and encrypt
        outbound_message = self.cipher.encrypt(
            serialize(read_in, self.alias))
        outbound_socket.sendall(outbound_message)
        # Move shell cursor to beginning of previous line
        # Ref: http://tldp.org/HOWTO/Bash-Prompt-HOWTO/x361.html
        print '%sSent: %s' % ('\033[F', read_in)

    def _shutdown(self, server_connection):
        """Close connection with server"""

        print '\nDisconnected from Secure Messaging Service'
        server_connection.close()
        self.socket.close()
        exit(0)
