import customtkinter as ctk

class GameFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.my_turn = False
        
        # Header Info
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", pady=5)
        
        self.lbl_role = ctk.CTkLabel(self.header_frame, text="Role: ???", font=("Arial", 16, "bold"))
        self.lbl_role.pack(side="left", padx=10)
        
        self.lbl_word = ctk.CTkLabel(self.header_frame, text="Word: ???", font=("Arial", 16))
        self.lbl_word.pack(side="right", padx=10)
        
        # Turn Info
        self.lbl_status = ctk.CTkLabel(self, text="Waiting for game start...", font=("Arial", 14))
        self.lbl_status.pack(pady=5)
        
        # Game Log (Chat/Clues)
        self.log_scroll = ctk.CTkScrollableFrame(self, label_text="Game Chat")
        self.log_scroll.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Input Area
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, fill="x", padx=10)
        
        self.entry_clue = ctk.CTkEntry(self.input_frame, placeholder_text="Type your one-word clue here...")
        self.entry_clue.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_clue.bind("<Return>", lambda event: self.on_send())
        
        self.btn_send = ctk.CTkButton(self.input_frame, text="Send Clue", command=self.on_send)
        self.btn_send.pack(side="right", padx=5)
        
        # Vote Area (Initially Hidden)
        self.vote_frame = ctk.CTkFrame(self)
        self.lbl_vote = ctk.CTkLabel(self.vote_frame, text="Vote for Imposter:", font=("Arial", 14, "bold"))
        self.lbl_vote.pack(pady=5)
        self.vote_buttons_frame = ctk.CTkFrame(self.vote_frame)
        self.vote_buttons_frame.pack(pady=5)

    def setup_game(self, role, word):
        self.lbl_role.configure(text=f"Role: {role}", text_color=("red" if role == "IMPOSTER" else "green"))
        self.lbl_word.configure(text=f"Word: {word}")
        self.log("Game Started! Good Luck.")
        # Hide vote frame if visible
        self.vote_frame.pack_forget()

    def set_status(self, text):
        self.lbl_status.configure(text=text)

    def log(self, message):
        # We try to parse sender if possible, or just default log
        # "Sender: Message"
        if ": " in message:
            parts = message.split(": ", 1)
            sender = parts[0]
            text = parts[1]
            
            is_me = (sender == self.controller.my_nickname)
            self.add_bubble(sender, text, is_me)
        else:
            # System message
            lbl = ctk.CTkLabel(self.log_scroll, text=message, text_color="gray", font=("Arial", 12, "italic"))
            lbl.pack(pady=2, fill="x")

    def clear_log(self):
        for widget in self.log_scroll.winfo_children():
            widget.destroy()
            
    def add_bubble(self, sender, text, is_me):
        # Frame wrapper for alignment
        container = ctk.CTkFrame(self.log_scroll, fg_color="transparent")
        container.pack(pady=5, fill="x")
        
        # Bubbles
        color = "#1f6aa5" if is_me else "#2b2b2b" # Blue for me, Dark for others
        align = "right" if is_me else "left"
        
        bubble = ctk.CTkFrame(container, fg_color=color, corner_radius=15)
        bubble.pack(side=align, padx=10)
        
        # Sender Name (Bigger, Bold, Colored)
        if not is_me:
            # Generate color from name
            name_hash = sum(ord(c) for c in sender)
            hue = name_hash % 360
            # Simple HSL to Hex (using fixed Saturation/Lightness)
            # Or just a palette
            colors = ["#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#33FFF5", "#F5FF33", "#FF8C33", "#9D33FF"]
            name_color = colors[name_hash % len(colors)]
            
            lbl_sender = ctk.CTkLabel(bubble, text=sender, font=("Arial", 14, "bold"), text_color=name_color)
            lbl_sender.pack(padx=10, pady=(5,0), anchor="w")
            
        lbl_text = ctk.CTkLabel(bubble, text=text, font=("Arial", 16), text_color="white", wraplength=350)
        lbl_text.pack(padx=15, pady=5)

    def set_turn(self, current_player, is_me):
        self.my_turn = is_me
        self.vote_frame.pack_forget() # Ensure voting is hidden during clues
        if is_me:
            self.set_status("It's YOUR turn! Give a clue.")
            self.entry_clue.configure(state="normal")
            self.btn_send.configure(state="normal")
        else:
            self.set_status(f"It's {current_player}'s turn.")
            self.entry_clue.configure(state="disabled")
            self.btn_send.configure(state="disabled")

    def setup_voting(self, candidates):
        self.set_status("VOTING PHASE - Choose the Imposter!")
        self.entry_clue.configure(state="disabled")
        self.btn_send.configure(state="disabled")
        
        self.vote_frame.pack(pady=20, fill="x")
        
        # Clear old buttons
        for widget in self.vote_buttons_frame.winfo_children():
            widget.destroy()
            
        for player in candidates:
            # Don't vote for yourself? (Optional rule, usually allowed/dumb)
            btn = ctk.CTkButton(self.vote_buttons_frame, text=player, 
                                command=lambda p=player: self.on_vote(p))
            btn.pack(side="left", padx=5, pady=5)

    def on_vote(self, suspect):
        self.controller.send_vote(suspect)
        self.vote_frame.pack_forget()
        self.set_status(f"You voted for {suspect}. Waiting for others...")

    def on_send(self):
        clue = self.entry_clue.get()
        if not clue:
            return
        # Basic validation: one word
        if " " in clue.strip():
            self.log("System: Please provide only ONE word.")
            return

        self.controller.send_clue(clue)
        self.entry_clue.delete(0, "end")
        
        # Disable temporarily until server confirms next turn
        self.entry_clue.configure(state="disabled")
        self.btn_send.configure(state="disabled")
