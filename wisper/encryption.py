from cryptography.fernet import Fernet, InvalidToken


class Cipher(object):
    """Message cipher for Client instances

       fernet_key: (Fernet) Symmetric encryption object.  Can only decrypt data
         that has been encrypted with a cipher created using a matching
         secret key
    """

    def __init__(self, secret_key):
        self.fernet_key = Fernet(secret_key)

    def encrypt(self, token):
        cipher_text = self.fernet_key.encrypt(token)
        return cipher_text

    def decrypt(self, token):
        plain_text = self.fernet_key.decrypt(token)
        return plain_text

    def is_encrypted(self, token):
        """Check if token is encrypted

           If token cannot be decrypted, it is assumed to be unencrypted
        """

        try:
            self.fernet_key.decrypt(token)
            return True
        except InvalidToken:
            return False


def generate_secret_key():
    """Generate new secret key"""

    secret_key = Fernet.generate_key()
    return secret_key


# Reassign so cryptography.fernet module only needs to be imported here
InvalidToken = InvalidToken
