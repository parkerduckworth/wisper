========
*Wisper*
========
**Cloud-hosted IRC with symmetric authenticated encryption**

|Version|

Quick Links
-----------
* `Description and Features`_
* `System Requirements`_
* `Installation`_
* `Usage`_
* `Architecture`_
* `Contribute`_

Description and Features
------------------------
Privacy is at a premium, and the need for a secure means of communication is greater than ever.

- Wisper messages use `Fernet <https://cryptography.io/en/latest/fernet/>`_ encryption, which employs 128-bit AES in CBC mode, with CMS padding, and HMAC using SHA256 for authentication.
- Using Wisper requires a mutual secret key, and messages cannot be decoded without one.
- Messages remain fully encrypted between end-points.
- The server operates from an AWS EC2 instance and is available at all times. It is automatically started by an AWS Lambda function which is triggered on application start-up.
- Messages are serialized with Google protocol buffers, enabling both a smaller packet size and an encrypted sender alias.

System Requirements
-------------------
- `Unix-like OS <https://en.wikipedia.org/wiki/Unix-like>`_
- `GCC <https://gcc.gnu.org/>`_
- `Python 2.7 <https://www.python.org/downloads/release/python-2715/>`_
- `pip <https://pip.pypa.io/en/stable/>`_

Installation
------------

    ::

    $ pip install wisper

Usage
-----
It is a requirement for all users to possess a mutual secret key.  This must be negotiated ahead of time. To generate a new key, type ``y`` into the ``Need a new key? (y/n)`` prompt at start-up.

*To start a chat session:*

    ::

    $ wisper
    $ Starting EC2 server instance...
    $ Need a new key? (y/n): <selection>
    $ Enter secret key: <secret-key>
    $ Key accepted
    $ Enter alias: <alias>
    $ Running server checks...
    $ Server started
    $ Establishing connection with server...
    $ Connected to Wisper server

- Wisper will send a notification when peers are connected/disconnected.

*To end a session:*

- Enter ``exit()`` or  press ``^C``

Architecture
------------
**Connection:**

When the Wisper client is started by the user, an HTTP request is made to an AWS API Gateway endpoint. The request triggers a Lambda function which checks to see if any Wisper server EC2 instances are running. If not, one is spun up. The Lambda function returns the instance's public IP address, relayed to the client via an HTTP response by the API Gateway. The client collects the secret key and user's alias, and connects to the server.

.. image:: https://s3.us-east-2.amazonaws.com/wisper-diagrams/wisper-connection-diagram.png
    :scale: 100 %
    :height: 600 px

**Communication:**

Wisper messages are serialized, encrypted, and sent to all connected clients through the server.  All client-to-client communication is encrypted between end-points.  All server-to-client messages are sent unencrypted.

.. image:: https://s3.us-east-2.amazonaws.com/wisper-diagrams/wisper-communication-diagram.png
    :scale: 100 %
    :height: 600 px

**Shutdown:**

The server instance detects when all clients are disconnected. This event triggers an HTTP request to API Gateway, invoking a Lambda function, which shuts down the server, and stops the EC2 instance.

.. image:: https://s3.us-east-2.amazonaws.com/wisper-diagrams/wisper-shutdown-diagram.png
    :scale: 100 %
    :height: 600 px

Contribute
----------
Contribution Guideline can be found `here <https://github.com/parkerduckworth/wisper/blob/master/CONTRIBUTING.rst>`_. Please feel free to use, share, and extend this project. PR's welcome.

.. |Version| image:: http://img.shields.io/pypi/v/wisper.svg?style=for-the-badge
   :target: https://pypi.python.org/pypi/wisper/
