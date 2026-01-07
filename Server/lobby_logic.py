import random
from protocol import *
from logger import logger

class Lobby:
    def __init__(self, code, settings):
        self.code = code
        self.settings = settings
        self.players = {}  # nickname -> ClientHandler
        self.state = "WAITING"
        self.secret_word = ""
        self.imposter_nickname = None
        self.turn_order = []
        self.current_turn_index = 0
        self.round_count = 0
        self.votes = {}
        
        # Load words from file
        self.word_list = []
        try:
            with open("words.txt", "r", encoding="utf-8") as f:
                self.word_list = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Failed to load words.txt: {e}")
            self.word_list = ["Pizza", "Bicicletta", "Sole"] # Fallback

    def is_full(self):
        return len(self.players) >= self.settings["max_players"]

    def get_host_name(self):
        if not self.players:
            return "Unknown"
        # First player added is considered host
        return list(self.players.keys())[0]

    def add_player(self, nickname, handler):
        if self.settings["anti_cheat_enabled"]:
            # If anti-cheat is strict, maybe reject?
            # But for now we just want to handle duplicates for playability.
            pass
        
        if self.state != "WAITING":
            return False, ERR_GAME_FULL

        # Handle Duplicate Names
        original_nick = nickname
        count = 1
        while nickname in self.players:
            nickname = f"{original_nick} {count}"
            count += 1

        self.players[nickname] = handler
        handler.lobby = self # Link handler to this lobby
        logger.info(f"Player {nickname} joined Lobby {self.code}.")
        self.broadcast_state()
        return True, nickname

    def remove_player(self, nickname):
        if nickname in self.players:
            is_host_leaving = (nickname == self.get_host_name())
            del self.players[nickname]
            logger.info(f"Player {nickname} left Lobby {self.code}.")
            
            if self.players:
                # If host left, assign new host
                if is_host_leaving:
                    new_host = self.get_host_name()
                    info_msg = f"Host {nickname} left. {new_host} is the new Host."
                    # If game was in progress, we might need to reset or not?
                    # Plan says: "if state == PLAYING/VOTING -> reset".
                    # But if we reset, we still need a host for the lobby phase.
                else:
                    info_msg = f"Player {nickname} has left the game."

                if self.state == "PLAYING" or self.state == "VOTING":
                    # If game active, we generally reset if someone leaves (simple logic)
                    # Or we could try to continue if not crucial (but roles break)
                    self.reset_game("Player disconnected. Game Reset.", new_host_override=self.get_host_name())
                else:
                    self.broadcast({
                        "type": MSG_STATE_UPDATE,
                        "phase": "LOBBY",
                        "players": list(self.players.keys()),
                        "host": self.get_host_name(),
                        "info": info_msg
                    })
        
        # If empty, maybe the manager should delete this lobby? Handled by manager.

    def start_game(self, requestor_nickname):
        host = self.get_host_name()
        if requestor_nickname != host:
            return False, "Only the Host can start the game!"

        min_p = self.settings["min_players"]
        if len(self.players) < min_p: 
             return False, f"Not enough players (min {min_p})"

        self.state = "PLAYING"
        self.secret_word = random.choice(self.word_list)
        self.imposter_nickname = random.choice(list(self.players.keys()))
        self.turn_order = list(self.players.keys())
        random.shuffle(self.turn_order)
        self.current_turn_index = 0
        self.round_count = 0
        self.votes = {}

        logger.info(f"Lobby {self.code} Started. {self.secret_word} / {self.imposter_nickname}")
        
        for nick, handler in self.players.items():
            role = "IMPOSTER" if nick == self.imposter_nickname else "CITIZEN"
            word = "SECRET" if role == "IMPOSTER" else self.secret_word
            handler.send_message({
                "type": MSG_GAME_START,
                "role": role,
                "word": word,
                "turn_order": self.turn_order
            })
        
        self.broadcast_turn()
        return True, None

    def handle_clue(self, nickname, clue_word):
        if self.state != "PLAYING": return
        
        if self.turn_order[self.current_turn_index] != nickname: return

        self.broadcast({
            "type": MSG_CLUE,
            "sender": nickname,
            "clue": clue_word
        })

        self.current_turn_index += 1
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round_count += 1
            if self.round_count >= self.settings["rounds_before_vote"]: 
                self.start_voting()
                return

        self.broadcast_turn()

    def start_voting(self):
        self.state = "VOTING"
        self.votes = {}
        self.broadcast({
            "type": MSG_STATE_UPDATE,
            "phase": "VOTING",
            "candidates": list(self.players.keys())
        })

    def handle_vote(self, voter, suspect):
        if self.state != "VOTING": return
        if voter in self.votes: return
        
        self.votes[voter] = suspect
        logger.info(f"Vote received from {voter}. Total: {len(self.votes)}/{len(self.players)}")
        if len(self.votes) >= len(self.players):
            logger.info("All votes received. Calculating results...")
            self.calculate_results()

    def calculate_results(self):
        vote_counts = {}
        for suspect in self.votes.values():
            vote_counts[suspect] = vote_counts.get(suspect, 0) + 1
            
        # Find suspect with max votes
        max_votes = 0
        candidates = []
        for suspect, count in vote_counts.items():
            if count > max_votes:
                max_votes = count
                candidates = [suspect]
            elif count == max_votes:
                candidates.append(suspect)
        
        # Determine Result
        winner = ""
        reason = ""
        
        if not candidates:
            # Should not happen if votes checked, but safeguard
            winner = "IMPOSTER"
            reason = "No votes cast. Imposter wins by default."
        elif len(candidates) > 1:
            # Tie
            winner = "IMPOSTER"
            reason = f"Tie between {', '.join(candidates)}. No one ejected. Imposter wins!"
        else:
            # Single ejectee
            ejected = candidates[0]
            if ejected == self.imposter_nickname:
                winner = "CITIZENS"
                reason = f"Imposter {ejected} caught! Citizens Win!"
            else:
                winner = "IMPOSTER"
                reason = f"{ejected} was NOT the Imposter. {self.imposter_nickname} wins!"
            
        self.broadcast_game_over(winner, reason)

    def broadcast_game_over(self, winner, reason):
        self.state = "GAME_OVER"
        self.broadcast({
            "type": MSG_GAME_OVER,
            "winner": winner,
            "reason": reason,
            "imposter": self.imposter_nickname,
            "word": self.secret_word
        })
        
        # Reset lobby after a short delay (or let clients handle it)
        # For simplicity, we reset logic but keep players connected
        self.secret_word = ""
        self.imposter_nickname = None
        self.state = "WAITING"
        
        # We don't broadcast lobby state immediately to let them see the Game Over screen?
        # Or we broadcast it so they know they are back in lobby.
        # Let's send a lobby update too so client knows state changed.
        self.broadcast_state()

    def broadcast_turn(self):
        current_player = self.turn_order[self.current_turn_index]
        self.broadcast({
            "type": MSG_STATE_UPDATE,
            "phase": "CLUE_PHASE",
            "current_turn": current_player
        })

    def broadcast_state(self):
        self.broadcast({
            "type": MSG_STATE_UPDATE,
            "phase": "LOBBY",
            "players": list(self.players.keys()),
            "host": self.get_host_name()
        })

    def broadcast(self, message):
        for handler in self.players.values():
            handler.send_message(message)

    def reset_game(self, reason, new_host_override=None):
        self.state = "WAITING"
        self.secret_word = ""
        self.imposter_nickname = None
        self.broadcast({
            "type": MSG_STATE_UPDATE,
            "phase": "LOBBY",
            "players": list(self.players.keys()),
            "host": new_host_override if new_host_override else self.get_host_name(),
            "info": reason
        })
