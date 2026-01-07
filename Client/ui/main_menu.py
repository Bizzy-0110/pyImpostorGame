import customtkinter as ctk

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.label_title = ctk.CTkLabel(self, text="The Imposter Game", font=("Arial", 24, "bold"))
        self.label_title.pack(pady=20)
        
        self.entry_nickname = ctk.CTkEntry(self, placeholder_text="Enter Nickname")
        self.entry_nickname.pack(pady=10)
        if self.controller.my_nickname:
            self.entry_nickname.insert(0, self.controller.my_nickname)
        
        self.btn_create = ctk.CTkButton(self, text="Create Game", command=self.on_create)
        self.btn_create.pack(pady=10)
        
        # Auto-scan label instead of button
        self.lbl_scan = ctk.CTkLabel(self, text="Scanning for games...", text_color="gray")
        self.lbl_scan.pack(pady=5)
        
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="orange")
        self.lbl_status.pack(pady=5)
        
        # Start auto-scan
        self.after(1000, self.start_auto_scan)
        
        self.conn_frame = ctk.CTkFrame(self)
        self.conn_frame.pack(pady=10, fill="x", padx=20)
        
        self.server_list_frame = ctk.CTkScrollableFrame(self.conn_frame, label_text="Found Games", height=150)
        self.server_list_frame.pack(fill="x")
        
        self.entry_code = ctk.CTkEntry(self, placeholder_text="Manual Game Code")
        self.entry_code.pack(pady=5)
        
        self.entry_ip = ctk.CTkEntry(self, placeholder_text="Manual IP (Optional)")
        self.entry_ip.pack(pady=5)
        
        self.btn_join_manual = ctk.CTkButton(self, text="Join Manually", command=self.on_join_manual)
        self.btn_join_manual.pack(pady=5)

    def on_create(self):
        nick = self.entry_nickname.get()
        ip = self.entry_ip.get() or self.controller.DEFAULT_SERVER_IP
        if not nick:
            return
            
        # Optional: Ask for settings in a dialog or just use defaults.
        # User requested "menu per le impostazioni".
        # Let's create a simple popup
        self.open_settings_dialog(nick, ip)

    def open_settings_dialog(self, nick, ip):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Game Settings")
        dialog.geometry("300x250")
        
        lbl = ctk.CTkLabel(dialog, text="Game Configuration", font=("Arial", 16, "bold"))
        lbl.pack(pady=10)
        
        lbl_rounds = ctk.CTkLabel(dialog, text="Rounds per Turn:")
        lbl_rounds.pack()
        entry_rounds = ctk.CTkEntry(dialog)
        entry_rounds.insert(0, "3")
        entry_rounds.pack(pady=5)
        
        def confirm():
            try:
                rounds = int(entry_rounds.get())
            except:
                rounds = 3
            
            # Close dialog
            dialog.destroy()
            # Send create request with settings (Controller needs update to accept settings)
            self.controller.create_game(nick, ip, settings={"rounds_before_vote": rounds})
            
        btn_ok = ctk.CTkButton(dialog, text="Create Lobby", command=confirm)
        btn_ok.pack(pady=20)
        
        dialog.transient(self) # On top of window
        dialog.grab_set()      # Modal

    def start_auto_scan(self):
        self.controller.scan_servers()
        # Schedule next scan in 5 seconds
        self.after(5000, self.start_auto_scan)

    def update_server_list(self, servers):
        # Clear existing
        for widget in self.server_list_frame.winfo_children():
            widget.destroy()
            
        for srv in servers:
            code = srv['code']
            ip = srv['ip']
            host = srv.get('host', 'Unknown')
            
            # Only show actual lobbies
            if code == "CENTRAL":
                continue
                
            text = f"{host}'s Game ({code})"
            fg_color = None
                
            btn = ctk.CTkButton(self.server_list_frame, text=text, fg_color=fg_color,
                                command=lambda s=srv: self.on_server_click(s))
            btn.pack(pady=2, fill="x")

    def on_server_click(self, server_info):
        code = server_info['code']
        ip = server_info['ip']
        
        # Always fill IP field
        self.entry_ip.delete(0, "end")
        self.entry_ip.insert(0, ip)
        
        # Joining specific game
        self.entry_code.delete(0, "end")
        self.entry_code.insert(0, code)

    def set_status(self, text):
        self.lbl_status.configure(text=text)

    def on_join_manual(self):
        nick = self.entry_nickname.get()
        code = self.entry_code.get()
        ip = self.entry_ip.get() or self.controller.DEFAULT_SERVER_IP
        
        if nick and code:
            self.controller.join_game(nick, code, ip)
