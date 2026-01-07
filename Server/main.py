import socket
import sys
import threading
from protocol import *
from logger import logger
from client_handler import ClientHandler
from cryptography.fernet import Fernet

def start_server():
    # Derive encryption key
    try:
        key = get_protocol_key()
        cipher = Fernet(key)
        logger.info(f"Server starting.")
    except Exception as e:
        logger.error(f"Failed to generate key: {e}")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse address to avoid 'Address already in use' during testing
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(("", DEFAULT_PORT)) # Bind to all interfaces
        server_socket.listen(5)
        logger.info(f"Server listening on port {DEFAULT_PORT}")
        
        while True:
            conn, addr = server_socket.accept()
            handler = ClientHandler(conn, addr, cipher)
            handler.start()
            
    except Exception as e:
        logger.error(f"Server crashed: {e}")
    finally:
        server_socket.close()

from game_manager import game_manager

def udp_beacon(port, server_code):
    """Broadcasting server existence and active lobbies."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    logger.info("UDP Beacon started.")
    
    while True:
        try:
            # 2. Announce Active Lobbies
            active_lobbies = list(game_manager.lobbies.keys())
            for code in active_lobbies:
                lobby = game_manager.get_lobby(code)
                host = lobby.get_host_name() if lobby else "Unknown"
                msg_lobby = f"IMPOSTOR_GAME:{code}:{host}".encode()
                sock.sendto(msg_lobby, ('<broadcast>', port))
            
            threading.Event().wait(2.0)
        except Exception as e:
            logger.error(f"Beacon error: {e}")
            break

if __name__ == "__main__":
    # Start UDP Beacon in background
    beacon_thread = threading.Thread(target=udp_beacon, args=(DEFAULT_PORT, "CENTRAL"), daemon=True)
    beacon_thread.start()
    
    start_server()
