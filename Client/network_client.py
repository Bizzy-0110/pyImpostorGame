import socket
import threading
import json
import base64
import hashlib
from cryptography.fernet import Fernet

# Replicating Protocol constants here to avoid import issues 
# if Client is run separately (though we could share the file)
MSG_LOGIN = "LOGIN"
MSG_CREATE_GAME = "CREATE_GAME"
MSG_GAME_START = "GAME_START"
MSG_CLUE = "CLUE"
MSG_VOTE = "VOTE"
MSG_STATE_UPDATE = "STATE_UPDATE"
MSG_GAME_OVER = "GAME_OVER"
MSG_ERROR = "ERROR"

DEFAULT_PORT = 5555
BUFFER_SIZE = 4096

class NetworkClient:
    def __init__(self):
        self.sock = None
        self.cipher = None
        self.nickname = ""
        self.running = False
        self.on_message_callback = None # Function to call when message received
        self.on_disconnect_callback = None
        
        # Hardcoded match with Server
        key_source = "IMPOSTOR_GAME_GLOBAL_SECURE_KEY_2026"
        self.global_key = base64.urlsafe_b64encode(hashlib.sha256(key_source.encode()).digest())

    def connect(self, ip, port, nickname):
        """Connects to server. Lobby join happens via messages later."""
        try:
            self.cipher = Fernet(self.global_key)
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.running = True
            
            # Start listener thread
            thread = threading.Thread(target=self.listen_loop, daemon=True)
            thread.start()

            # Send Login (Initial Handshake)
            self.send({
                "type": MSG_LOGIN,
                "nickname": nickname
            })
            self.nickname = nickname
            return True, None
        except Exception as e:
            return False, str(e)

    def find_servers(self, timeout=3.0):
        """Listens for UDP beacons. Returns list of (ip, code)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Allow multiple clients to bind to the same port on the same machine (essential for local testing)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", DEFAULT_PORT))
        except OSError as e:
            print(f"Warning: Could not bind to discovery port: {e}")
            return []
            
        sock.settimeout(timeout)
        
        found_servers = [] # List of dicts
        
        # We just listen for 'timeout' seconds
        import time
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                if msg.startswith("IMPOSTOR_GAME:"):
                    parts = msg.split(":")
                    code = parts[1]
                    host = parts[2] if len(parts) > 2 else "Unknown"
                    
                    server_info = {"ip": addr[0], "code": code, "host": host}
                    # Avoid duplicates (check code/ip)
                    # We use a tuple key for checking
                    existing = False
                    for s in found_servers:
                        if s["code"] == code and s["ip"] == addr[0]:
                           existing = True
                           break
                    if not existing:
                        found_servers.append(server_info)
            except socket.timeout:
                break
            except Exception:
                pass
        
        sock.close()
        return found_servers
        try:
            sock.bind(("", DEFAULT_PORT))
        except OSError as e:
            print(f"Warning: Could not bind to discovery port: {e}")
            return []
            
        sock.settimeout(timeout)
        
        found_servers = [] # List of dicts
        
        start_time = threading.Timer(timeout, lambda: None)
        # We just listen for 'timeout' seconds
        import time
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                if msg.startswith("IMPOSTOR_GAME:"):
                    code = msg.split(":")[1]
                    server_info = {"ip": addr[0], "code": code}
                    if server_info not in found_servers:
                        found_servers.append(server_info)
            except socket.timeout:
                break
            except Exception:
                pass
        
        sock.close()
        return found_servers


    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        if self.on_disconnect_callback:
            self.on_disconnect_callback()

    def send(self, data: dict):
        if not self.sock:
            return
        try:
            json_data = json.dumps(data).encode('utf-8')
            encrypted = self.cipher.encrypt(json_data)
            self.sock.sendall(encrypted)
        except Exception as e:
            print(f"Send Error: {e}")

    def listen_loop(self):
        while self.running:
            try:
                data = self.sock.recv(BUFFER_SIZE)
                if not data:
                    break
                
                decrypted_data = self.cipher.decrypt(data)
                message = json.loads(decrypted_data.decode('utf-8'))
                
                if self.on_message_callback:
                    self.on_message_callback(message)
                    
            except Exception as e:
                print(f"Listen Error: {e}")
                self.disconnect()
                break
