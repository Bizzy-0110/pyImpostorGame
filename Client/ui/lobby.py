import customtkinter as ctk

class LobbyFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.label_title = ctk.CTkLabel(self, text="Lobby", font=("Arial", 24, "bold"))
        self.label_title.pack(pady=10)
        
        self.label_code = ctk.CTkLabel(self, text="Code: ???", font=("Courier", 20))
        self.label_code.pack(pady=5)
        
        self.label_status = ctk.CTkLabel(self, text="", text_color="orange")
        self.label_status.pack(pady=5)

        self.players_frame = ctk.CTkScrollableFrame(self, label_text="Players")
        self.players_frame.pack(pady=10, fill="both", expand=True, padx=20)
        
        self.btn_start = ctk.CTkButton(self, text="Start Game", command=self.on_start, state="disabled")
        self.btn_start.pack(pady=10)
        
        self.btn_leave = ctk.CTkButton(self, text="Leave Game", command=self.on_leave, fg_color="red")
        self.btn_leave.pack(pady=10)

    def set_code(self, code):
        self.label_code.configure(text=f"Code: {code}")
        self.label_status.configure(text="")

    def set_status(self, text):
        self.label_status.configure(text=text)

    def update_players(self, player_list, host_name=None):
        self.current_player_list = player_list
        self.current_host_name = host_name
        self.refresh_player_list_ui()
        self.refresh_host_controls()

    def refresh_player_list_ui(self):
        for widget in self.players_frame.winfo_children():
            widget.destroy()
            
        host = self.current_host_name
        for p in self.current_player_list:
            display_text = p
            if p == host:
                display_text += " 👑"
            
            lbl = ctk.CTkLabel(self.players_frame, text=display_text, font=("Arial", 16))
            lbl.pack()

    def refresh_host_controls(self):
        # Called when player list updates OR when my nickname updates
        my_nick = self.controller.my_nickname
        host = getattr(self, 'current_host_name', None)
        players = getattr(self, 'current_player_list', [])
        
        is_me_host = (my_nick == host)
        
        if is_me_host and len(players) >= 3:
            self.btn_start.configure(state="normal", text="Start Game")
        elif not is_me_host:
            self.btn_start.configure(state="disabled", text="Waiting for Host...")
        else:
            self.btn_start.configure(state="disabled", text="Waiting for players (min 3)...")

    def on_start(self):
        self.controller.start_game_request()

    def on_leave(self):
        self.controller.leave_game()
