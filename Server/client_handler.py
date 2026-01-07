import threading
import socket
import json
from protocol import *
from logger import logger
from game_manager import game_manager

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr, cipher):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.cipher = cipher
        self.nickname = None
        self.lobby = None # Reference to current lobby
        self.running = True

    def run(self):
        logger.info(f"Connection from {self.addr}")
        try:
            while self.running:
                # Read length prefix (4 bytes generic) or just Read chunks
                # For simplicity with Python sockets, we'll try to read a reasonable buffer
                # In a robust system we'd use length-prefixing or delimiters.
                # Here we assume small JSON payloads < 4096 bytes for this simple game.
                data = self.conn.recv(BUFFER_SIZE)
                if not data:
                    break
                
                try:
                    # Attempt to decrypt
                    message = decrypt_message(data, self.cipher)
                    self.handle_message(message)
                except Exception as e:
                    logger.warning(f"Failed to decrypt or parse message from {self.addr}: {e}")
                    # If we can't decrypt, they probably have the wrong code.
                    # We might want to disconnect them immediately if it's the first message.
                    if not self.nickname:
                         self.send_error("Invalid Game Code or Encryption Error")
                         break
        
        except ConnectionResetError:
            logger.info(f"Connection reset by {self.addr}")
        except Exception as e:
            logger.error(f"Error in client loop: {e}")
        finally:
            self.cleanup()

    def handle_message(self, message):
        msg_type = message.get("type")
        
        if msg_type == MSG_LOGIN:
            # Just handshake / set nickname on connection?
            # User flow: Connect -> Send Login -> Server Says OK -> User sends JOIN/CREATE
            nick = message.get("nickname")
            if nick:
                self.nickname = nick
                self.send_message({"type": "LOGIN_SUCCESS", "nickname": nick})
            else:
                self.send_error("Invalid Nickname")

        elif msg_type == MSG_CREATE_GAME:
            if not self.nickname:
                self.send_error("Login first")
                return
            
            # Create Lobby
            settings_override = message.get("settings", {})
            code = game_manager.create_lobby(settings_override)
            lobby = game_manager.get_lobby(code)
            
            # Auto-join
            success, result_data = lobby.add_player(self.nickname, self)
            if success:
                self.lobby = lobby
                self.nickname = result_data # Update nickname in case of duplicate
                # Tell client the code
                self.send_message({
                    "type": "JOIN_SUCCESS", 
                    "code": code,
                    "nickname": self.nickname,
                    "lobby_state": "WAITING"
                })
            else:
                self.send_error(result_data)

        elif msg_type == "JOIN_GAME": # String literal or constant? Use Protocol constant if exists or string
            code = message.get("code")
            if not code:
                self.send_error("Missing Code")
                return
            
            lobby = game_manager.get_lobby(code)
            if not lobby:
                self.send_error("Lobby not found")
                return
            
            success, result_data = lobby.add_player(self.nickname, self)
            if success:
                self.lobby = lobby
                self.nickname = result_data # Update nickname
                self.send_message({
                    "type": "JOIN_SUCCESS", 
                    "code": code,
                    "nickname": self.nickname
                })
            else:
                self.send_error(result_data)

        elif msg_type == MSG_GAME_START:
            if self.lobby:
                success, err = self.lobby.start_game(self.nickname)
                if not success: self.send_error(err)

        elif msg_type == MSG_CLUE:
            if self.lobby:
                self.lobby.handle_clue(self.nickname, message.get("clue"))

        elif msg_type == MSG_VOTE:
            if self.lobby:
                self.lobby.handle_vote(self.nickname, message.get("suspect"))

    def send_message(self, message_dict):
        try:
            encrypted = encrypt_message(message_dict, self.cipher)
            self.conn.sendall(encrypted)
        except Exception as e:
            logger.error(f"Failed to send to {self.nickname}: {e}")

    def send_error(self, error_msg):
        self.send_message({"type": MSG_ERROR, "message": error_msg})

    def cleanup(self):
        if self.lobby and self.nickname:
            self.lobby.remove_player(self.nickname)
            # Check if lobby is empty
            if not self.lobby.players:
                game_manager.remove_lobby(self.lobby.code)
        try:
            self.conn.close()
        except:
            pass
        logger.info(f"Connection closed for {self.addr}")
