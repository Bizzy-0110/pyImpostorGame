import json
import os
import random
import string
from logger import logger
from lobby_logic import Lobby

class GameManager:
    def __init__(self):
        self.lobbies = {} # code -> Lobby
        self.settings = self.load_settings()
        
        # Apply debug setting
        from logger import set_debug_mode
        set_debug_mode(self.settings.get("debug_mode", False))

    def load_settings(self):
        default_settings = {
            "server_port": 5555,
            "max_players": 10,
            "min_players": 3,
            "rounds_before_vote": 2,
            "anti_cheat_enabled": True,
            "debug_mode": False
        }
        try:
            path = os.path.join(os.path.dirname(__file__), 'settings.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return {**default_settings, **json.load(f)}
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
        return default_settings

    def create_lobby(self, settings_override=None):
        """Creates a new lobby with a unique 6-character code."""
        # Merge defaults with overrides
        lobby_settings = self.settings.copy()
        if settings_override:
            lobby_settings.update(settings_override)
            
        while True:
            # Uppercase + Digits
            chars = string.ascii_uppercase + string.digits
            code = ''.join(random.choices(chars, k=6))
            if code not in self.lobbies:
                break
        
        new_lobby = Lobby(code, lobby_settings)
        self.lobbies[code] = new_lobby
        logger.info(f"Created new Lobby: {code}")
        return code

    def get_lobby(self, code):
        return self.lobbies.get(code)

    def remove_lobby(self, code):
        if code in self.lobbies:
            del self.lobbies[code]
            logger.info(f"Lobby {code} removed (empty).")

    def cleanup_empty_lobbies(self):
        # Optional: remove lobbies with 0 players if old enough
        # Now handled by event-driven removal in client_handler
        pass

# Global instance
game_manager = GameManager()
