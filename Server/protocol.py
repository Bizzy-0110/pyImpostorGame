import json
import base64
import hashlib
from cryptography.fernet import Fernet

# Message Types
MSG_LOGIN = "LOGIN"
MSG_CREATE_GAME = "CREATE_GAME"
MSG_JOIN_GAME = "JOIN_GAME"
MSG_GAME_START = "GAME_START"
MSG_CLUE = "CLUE"
MSG_VOTE = "VOTE"
MSG_STATE_UPDATE = "STATE_UPDATE"
MSG_GAME_OVER = "GAME_OVER"
MSG_ERROR = "ERROR"

# Error Codes
ERR_NAME_TAKEN = "NAME_TAKEN"
ERR_INVALID_CODE = "INVALID_CODE"
ERR_GAME_FULL = "GAME_FULL"

# Network Defaults
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096

# Static Key for Initial Connection (In a real app, this should be better managed)
# We bake a key derived from a static string so both client and server know it.
GLOBAL_KEY_SOURCE = "IMPOSTOR_GAME_GLOBAL_SECURE_KEY_2026"
GLOBAL_KEY = base64.urlsafe_b64encode(hashlib.sha256(GLOBAL_KEY_SOURCE.encode()).digest())

def get_protocol_key() -> bytes:
    """Returns the fixed protocol key."""
    return GLOBAL_KEY

def encrypt_message(data: dict, cipher: Fernet) -> bytes:
    """Encrypts a dictionary payload."""
    json_data = json.dumps(data).encode('utf-8')
    return cipher.encrypt(json_data)

def decrypt_message(token: bytes, cipher: Fernet) -> dict:
    """Decrypts a token into a dictionary payload."""
    decrypted_data = cipher.decrypt(token)
    return json.loads(decrypted_data.decode('utf-8'))
