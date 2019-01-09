import time

from client import Client
from server import Server
from aws.api_gateway import lambda_proxy
from encryption import Cipher, generate_secret_key
from multiprocessing.pool import ThreadPool


"""run_server and run_client act as console scripts, and are registered by 
     setuptools in setup.py when installed with pip.
   
   These two functions are also the entry (run_client) and exit (run_server)
     points of the application server's lifespan
"""


def run_server():
    """Run a server instance

       This function runs on EC2 instance when 'wisper-runserver' is run in the
         console by a Lambda function. See aws.EC2.run_wisper_server
    """

    new_server = Server()
    new_server.start()
    print 'Stopping EC2 server instance...'
    lambda_proxy('stop_instance')
    print 'Server stopped.'
    exit(0)


def run_client():
    """Start a new chat session

       This function runs as the console command 'wisper' to initiate user session
    """


    ec2_async_result = start_ec2()
    new_session = Session()
    try:
        # Client fetches the server IP address asynchronously
        new_session.start_client(ec2_async_result)
    except KeyboardInterrupt:
        lambda_proxy('stop_instance')
        exit(0)


def start_ec2():
    """Create new thread to start EC2 instance

       This thread runs in the background and asynchronously returns the
         instance's public IP address.

       EC2 instance can take ~30 seconds for cold start, so this allows the
         thread to execute instance start-up in the background

       For instance startup details: See aws.api_gateway.lambda_proxy
    """
    print 'Starting EC2 server instance...'
    ec2_async_result = ThreadPool(processes=1).apply_async(
        func=lambda_proxy, args=('start_instance',))
    return ec2_async_result


class Session(object):
    """Container for user session data

       Executes a series of prompts to collect required fields for new
         Client instance

       cipher: (Cipher) Object used by Client to encrypt/decrypt messages
       alias: (str) Username for the session
       client: (Client) The new Client instance that will be started
    """

    def __init__(self):
        self.host = None
        # Unassigned port:
        # https://www.iana.org/assignments/service-names-port-numbers/
        self.port = 4440
        self.cipher = None
        self.alias = None
        self.client = None

    def start_client(self, ec2_async_result):
        """Collect required client attributes and start client"""

        self._generate_new_secret_key()
        self.cipher = self._construct_cipher()
        self.alias = self._set_alias()
        self.host = fetch_async_host_address(ec2_async_result)
        self.client = Client(self.host, self.port, self.alias, self.cipher)
        self.client.start()

    @staticmethod
    def _generate_new_secret_key():
        resp = ''
        while resp != 'y' and resp != 'n':
            resp = raw_input('Need a new key? (y/n): ').lower()
        if resp == 'y':
            print 'New secret key: ' + generate_secret_key()

    def _construct_cipher(self):
        """Construct a Cipher object for new Client instance"""

        while True:
            key = raw_input('Enter secret key: ')
            try:
                cipher = Cipher(key)
                print 'Key accepted'
                return cipher
            except:
                print 'Invalid key'

    def _set_alias(self):
        entered_alias = raw_input('Enter alias: ')
        while not entered_alias.isalnum():
            print 'Alias must only contain alphanumeric characters'
            entered_alias = raw_input('Enter alias: ')
        return entered_alias


def fetch_async_host_address(ec2_async_result):
    """Retrieve EC2 Instance public IPv4 address from async thread pool"""

    # EC2 instance status checks in progress while waiting for the async result
    print 'Running server checks...'
    ip_address = ec2_async_result.get()
    # When IP address returns, instance is started
    print 'Server started'
    # Sometimes client connects too soon and fails, give the server a second
    time.sleep(1)
    return ip_address
