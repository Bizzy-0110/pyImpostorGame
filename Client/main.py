import customtkinter as ctk
import os
import sys
import subprocess
import random
import string
import threading

# Add parent directory to path to find other modules if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ui.lobby import LobbyFrame
from ui.game_screen import GameFrame
from ui.main_menu import MainMenu

# Import MSG_GAME_OVER locally if not imported or rely on string if network_client exports it.
# Check imports above... missing MSG_GAME_OVER in imports from network_client
from network_client import NetworkClient, MSG_LOGIN, MSG_GAME_START, MSG_CLUE, MSG_STATE_UPDATE, MSG_ERROR, MSG_CREATE_GAME, MSG_VOTE, MSG_GAME_OVER

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Default Server IP - Change this if you want to hardcode a LAN IP
DEFAULT_SERVER_IP = "127.0.0.1"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("The Imposter Game")
        self.geometry("600x650")
        
        self.DEFAULT_SERVER_IP = DEFAULT_SERVER_IP
        
        self.network = NetworkClient()
        self.network.on_message_callback = self.handle_network_message
        self.network.on_disconnect_callback = self.handle_disconnect
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        self.current_frame = None
        
        try:
            self.my_nickname = os.getlogin()
        except:
            self.my_nickname = "Player"
        self.game_code = ""
        self.is_host = False
        
        self.init_frames()
        self.show_frame("MainMenu")

    def init_frames(self):
        for F in (MainMenu, LobbyFrame, GameFrame):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            
    def show_frame(self, page_name):
        if self.current_frame:
            self.current_frame.pack_forget()
        
        frame = self.frames[page_name]
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

    def create_game(self, nickname, ip="127.0.0.1", settings=None):
        self.is_host = True
        self.target_ip = ip
        self.game_settings = settings or {}

        # We won't spawn the server anymore.
        self.join_game(nickname, None, ip) # Code=None means Create

    def join_game(self, nickname, code, ip):
        # We process 'code' as a Join Request AFTER connecting
        self.my_nickname = nickname
        self.game_code = code # Store intended code
        
        if self.frames.get("MainMenu"):
             self.frames["MainMenu"].set_status("Connecting to server...")
             self.update_idletasks() # Force UI update

        # 1. Connect first
        success, err = self.network.connect(ip, 5555, nickname)
        if not success:
             print(f"Connection Failed: {err}")
             if self.frames.get("MainMenu"):
                 self.frames["MainMenu"].set_status(f"Error: {err}")
             return

        # 2. If 'code' is provided (Join), send JOIN_GAME. 
        #    We wait for LOGIN_SUCCESS to send the actual request to avoid packet sticking
        #    since we don't have advanced framing.
        pass

    def scan_servers(self):
        # Run in thread to not freeze UI
        def scan():
            servers = self.network.find_servers()
            self.after(0, lambda: self.frames["MainMenu"].update_server_list(servers))
        threading.Thread(target=scan, daemon=True).start()

    def start_game_request(self):
        self.network.send({"type": MSG_GAME_START})
        
    def leave_game(self):
        self.network.disconnect()
        self.show_frame("MainMenu")

    def send_clue(self, clue):
        self.network.send({"type": MSG_CLUE, "clue": clue, "nickname": self.my_nickname})

    def handle_network_message(self, msg):
        # Must schedule UI updates on main thread
        self.after(0, lambda: self.process_message(msg))

    def process_message(self, msg):
        m_type = msg.get("type")
        
        if m_type == "LOGIN_SUCCESS":
            # 1. Login to Server OK. Now Create or Join Lobby.
            if self.frames.get("MainMenu"):
                 self.frames["MainMenu"].set_status("Login OK. Joining Lobby...")
            
            if self.is_host:
                 msg = {"type": MSG_CREATE_GAME, "nickname": self.my_nickname}
                 if hasattr(self, 'game_settings') and self.game_settings:
                     msg["settings"] = self.game_settings
                 self.network.send(msg)
            else:
                 self.network.send({"type": "JOIN_GAME", "code": self.game_code, "nickname": self.my_nickname})

        elif m_type == "JOIN_SUCCESS":
            # 2. Joined Lobby OK. Switch to Lobby UI.
            code = msg.get("code")
            nick = msg.get("nickname")
            if nick:
                self.my_nickname = nick # Update local nick if server changed it
                
            self.game_code = code
            self.show_frame("LobbyFrame")
            self.frames["LobbyFrame"].set_code(code)
            
            # Fix race condition: update buttons now that I know my final nickname
            self.frames["LobbyFrame"].refresh_host_controls()
            
            # If I was the creator (host), show a message?
            if self.is_host:
                self.frames["LobbyFrame"].set_status("Game Created! Share the code.")
            else:
                self.frames["LobbyFrame"].set_status("Joined successfully!")
        
        elif m_type == MSG_STATE_UPDATE:
            phase = msg.get("phase")
            if phase == "LOBBY":
                players = msg.get("players", [])
                host = msg.get("host")
                self.frames["LobbyFrame"].update_players(players, host)
                info = msg.get("info")
                if info:
                    self.frames["LobbyFrame"].set_status(info)

            elif phase == "CLUE_PHASE":
                current_turn = msg.get("current_turn")
                self.show_frame("GameFrame") # Ensure we are on game frame
                self.frames["GameFrame"].set_turn(current_turn, current_turn == self.my_nickname)
            elif phase == "VOTING":
                candidates = msg.get("candidates")
                self.show_frame("GameFrame")
                self.frames["GameFrame"].setup_voting(candidates)

        elif m_type == MSG_GAME_START:
            role = msg.get("role")
            word = msg.get("word")
            self.show_frame("GameFrame")
            self.frames["GameFrame"].clear_log()
            self.frames["GameFrame"].setup_game(role, word)

        elif m_type == MSG_CLUE:
            sender = msg.get("sender")
            clue = msg.get("clue")
            self.frames["GameFrame"].log(f"{sender}: {clue}")

        elif m_type == MSG_ERROR:
            err = msg.get("message")
            print(f"Server Error: {err}") 
            self.show_toast(f"Error: {err}", color="#FF5555")

        elif m_type == MSG_GAME_OVER:
            winner = msg.get("winner")
            reason = msg.get("reason")
            imposter = msg.get("imposter")
            word = msg.get("word")
            
            # Show game over dialog
            self.show_game_over_dialog(winner, reason, imposter, word)

    def show_game_over_dialog(self, winner, reason, imposter, word):
        # Create a top level window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Game Over")
        dialog.geometry("400x300")
        dialog.transient(self) # Make it modal-like relative to main window
        dialog.grab_set()      # Block input to main window
        
        # Colors
        bg_color = "#2b2b2b"
        text_color = "white"
        if winner == "CITIZENS":
            text_color = "#4CAF50" # Green
        elif winner == "IMPOSTER":
            text_color = "#F44336" # Red
            
        lbl_title = ctk.CTkLabel(dialog, text=f"{winner} WIN!", font=("Arial", 24, "bold"), text_color=text_color)
        lbl_title.pack(pady=20)
        
        lbl_reason = ctk.CTkLabel(dialog, text=reason, font=("Arial", 14), wraplength=350)
        lbl_reason.pack(pady=10)
        
        info_text = f"The Imposter was: {imposter}\nThe Secret Word was: {word}"
        lbl_info = ctk.CTkLabel(dialog, text=info_text, font=("Arial", 12), text_color="gray")
        lbl_info.pack(pady=10)
        
        def play_again():
            dialog.destroy()
            # We are already essentially in Lobby state due to server reset
            self.show_frame("LobbyFrame")
            
        def leave_game():
            dialog.destroy()
            self.leave_game()

        btn_container = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_container.pack(pady=20)

        btn_again = ctk.CTkButton(btn_container, text="Play Again", command=play_again, fg_color="green")
        btn_again.pack(side="left", padx=10)
        
        btn_leave = ctk.CTkButton(btn_container, text="Leave Game", command=leave_game, fg_color="red")
        btn_leave.pack(side="right", padx=10)

    def send_vote(self, suspect):
        self.network.send({"type": MSG_VOTE, "suspect": suspect})

    def handle_disconnect(self):
        print("Disconnected!")
        self.show_toast("Disconnected from server", color="#FF5555")
        self.after(2000, lambda: self.show_frame("MainMenu"))

    def show_toast(self, message, color="orange", duration=3000):
        """Displays a temporary floating label at the top."""
        toast = ctk.CTkLabel(self, text=message, fg_color=color, text_color="white", corner_radius=10, padx=10, pady=5)
        # Place at top center
        toast.place(relx=0.5, rely=0.1, anchor="n")
        
        # Auto-destroy
        self.after(duration, toast.destroy)

if __name__ == "__main__":
    app = App()
    app.mainloop()
