import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import datetime
import os
from jarvis.logger import logger
from jarvis.config import get_config, save_config
from jarvis.memory import get_memory
from jarvis.tts import get_manager as get_tts_manager, speak
from jarvis.stt import STTListener, SR_AVAILABLE
from jarvis.core import process_command
from jarvis.gui.theme import BG, BG_L2, BG_L3, TEXT, TEXT_DIM, CYAN, PURPLE, GREEN, YELLOW, RED, FONT, FONT_S, FONT_B, FONT_L, FONT_M, FONT_MB

# ── Pulsing Live Core Widget ──────────────────────────────────────────────────
class JarvisCore(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.radius = 30
        self.direction = 1
        self.pulse_color = CYAN
        self.listening = False
        self._animate()

    def set_state(self, listening=False):
        self.listening = listening
        self.pulse_color = GREEN if listening else CYAN

    def _animate(self):
        self.delete("all")
        
        # Outer breathing neon aura
        self.radius += self.direction * 0.7
        if self.radius > 42 or self.radius < 24:
            self.direction *= -1

        # Glowing outer ring
        color = GREEN if self.listening else (PURPLE if self.radius > 33 else CYAN)
        self.create_oval(
            50 - self.radius, 50 - self.radius,
            50 + self.radius, 50 + self.radius,
            outline=color, width=2
        )
        
        # Mid circle
        self.create_oval(34, 34, 66, 66, outline=BG_L3, width=1)
        
        # Inner active power core
        core_color = GREEN if self.listening else PURPLE
        self.create_oval(40, 40, 60, 60, fill=core_color, outline="")
        
        self.after(50, self._animate)


# ── Jarvis Main GUI Window ───────────────────────────────────────────────────
class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.listening = False
        self.mute = False
        self.listener = STTListener() if SR_AVAILABLE else None
        
        self.root.title("JARVIS — Autonomous Desktop Assistant")
        self.root.geometry("900x740")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(720, 580)
        
        self._build_ui()
        self._welcome()

    def _build_ui(self):
        # ── TOP BAR (Header & pulsing core) ───────────────────────────────────
        top_bar = tk.Frame(self.root, bg=BG_L2, py=12)
        top_bar.pack(fill="x")
        
        # Pulse core on left
        self.core = JarvisCore(top_bar, width=100, height=100, bg=BG_L2)
        self.core.pack(side="left", padx=16)
        
        # Title info
        info_frame = tk.Frame(top_bar, bg=BG_L2)
        info_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(
            info_frame, text="JARVIS v3.1", font=FONT_L,
            bg=BG_L2, fg=CYAN
        ).pack(anchor="w", pady=(8, 0))
        
        self.status_lbl = tk.Label(
            info_frame, text="● SYSTEM ONLINE", font=FONT_B,
            bg=BG_L2, fg=GREEN
        ).pack(anchor="w", pady=(2, 0))
        
        # Clock
        self.time_lbl = tk.Label(
            top_bar, text="00:00:00 PM", font=FONT_MB,
            bg=BG_L2, fg=TEXT
        )
        self.time_lbl.pack(side="right", padx=24)
        self._tick()

        # ── QUICK ACTIONS BAR ─────────────────────────────────────────────────
        qbar = tk.Frame(self.root, bg=BG_L3, py=8)
        qbar.pack(fill="x")
        
        tk.Label(
            qbar, text="Quick Commands:", font=FONT_B,
            bg=BG_L3, fg=TEXT_DIM
        ).pack(side="left", padx=16)
        
        quick_cmds = [
            ("Time", "Kitne baje hain"),
            ("Weather", "Mausam batao"),
            ("System Info", "System stats"),
            ("Notes", "Notes dikhao"),
            ("Joke", "Joke sunao"),
            ("Help", "Help")
        ]
        for label, cmd in quick_cmds:
            btn = tk.Button(
                qbar, text=label, font=FONT_S, bg=BG, fg=CYAN,
                activebackground=CYAN, activeforeground="white",
                relief="flat", bd=0, cursor="hand2", padx=12, py=4,
                command=lambda c=cmd: self._send_quick_cmd(c)
            )
            btn.pack(side="left", padx=4)
            
        # Settings Button
        tk.Button(
            qbar, text="⚙ Settings", font=FONT_B, bg="#475569", fg=YELLOW,
            activebackground=YELLOW, activeforeground="black",
            relief="flat", bd=0, cursor="hand2", padx=14, py=4,
            command=self._open_settings
        ).pack(side="right", padx=16)

        # ── CONVERSATION DISPLAY AREA (Chat Bubble Style) ─────────────────────
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap="word", font=FONT_M, bg=BG, fg=TEXT,
            insertbackground=TEXT, relief="flat", bd=0, highlightthickness=0
        )
        self.chat.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Tags styling
        self.chat.tag_configure("user", foreground=CYAN, font=FONT_MB)
        self.chat.tag_configure("jarvis", foreground=PURPLE, font=FONT_MB)
        self.chat.tag_configure("system", foreground=YELLOW, font=FONT_B)

        # ── INPUT CONTROL PANEL ───────────────────────────────────────────────
        input_panel = tk.Frame(self.root, bg=BG_L2, py=12)
        input_panel.pack(fill="x")
        
        # Microphone Button
        self.mic_btn = tk.Button(
            input_panel, text="🎙 Listen", font=FONT_B, bg=CYAN, fg="white",
            activebackground=GREEN, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=12, py=8,
            command=self._toggle_voice
        )
        self.mic_btn.pack(side="left", padx=16)
        
        # Mute Button
        self.mute_btn = tk.Button(
            input_panel, text="🔊 Mute Off", font=FONT_B, bg=BG_L3, fg=TEXT,
            relief="flat", bd=0, cursor="hand2", width=12, py=8,
            command=self._toggle_mute
        )
        self.mute_btn.pack(side="left", padx=4)

        # Input box
        self.entry = tk.Entry(
            input_panel, font=FONT_M, bg=BG, fg=TEXT,
            insertbackground=TEXT, relief="flat", bd=0, highlightthickness=1,
            highlightcolor=CYAN, highlightbackground=BG_L3
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=12, ipady=8)
        self.entry.bind("<Return>", lambda e: self._send_text())
        
        # Send Button
        tk.Button(
            input_panel, text="Send 🚀", font=FONT_B, bg=PURPLE, fg="white",
            activebackground=CYAN, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=12, py=8,
            command=self._send_text
        ).pack(side="right", padx=16)

        # ── FOOTER STATUS BAR ─────────────────────────────────────────────────
        self.footer = tk.Label(
            self.root, text="Initialising Jarvis modules...",
            font=("Segoe UI", 9), bg=BG_L3, fg=TEXT_DIM, py=4
        )
        self.footer.pack(fill="x")
        self.root.after(2000, self._update_footer)

    def _tick(self):
        self.time_lbl.config(text=datetime.datetime.now().strftime("%I:%M:%S %p"))
        self.root.after(1000, self._tick)

    def _update_footer(self):
        tts_lbl = get_tts_manager().engine_label
        stt_lbl = "Ready" if SR_AVAILABLE else "needs speech_recognition"
        self.footer.config(
            text=f"Active TTS: {tts_lbl}  |  STT Status: {stt_lbl}  |  Double click Run_Jarvis.bat if disconnected"
        )
        self.root.after(3000, self._update_footer)

    def _welcome(self):
        now = datetime.datetime.now()
        g = "Good morning" if now.hour < 12 else ("Good afternoon" if now.hour < 17 else "Good evening")
        
        msg = (
            f"● {g} Sir!\n\n"
            f"JARVIS v3.1 is online and fully responsive.\n"
            f"Active Space : {os.getcwd()}\n"
            f"SQLite DB    : Connected & Synced\n\n"
            f"Aap commands type kar sakte hain ya microphone use kar sakte hain.\n"
            f"Boliye Sir, kya madad chahiye?"
        )
        self._append_message("SYSTEM", msg, "system")
        speak("Jarvis is online and ready, Sir!")

    def _append_message(self, sender: str, text: str, tag: str):
        self.chat.config(state="normal")
        self.chat.insert("end", f"[{sender}]:\n", tag)
        self.chat.insert("end", f"{text}\n\n")
        self.chat.config(state="disabled")
        self.chat.see("end")

    def _send_text(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append_message("YOU", text, "user")
        
        # Save to database memory
        get_memory().add_message("User", text)

        # Route processing asynchronously to avoid freezing GUI
        threading.Thread(target=self._process_cmd_async, args=(text,), daemon=True).start()

    def _send_quick_cmd(self, cmd: str):
        self._append_message("YOU", cmd, "user")
        get_memory().add_message("User", cmd)
        threading.Thread(target=self._process_cmd_async, args=(cmd,), daemon=True).start()

    def _process_cmd_async(self, text: str):
        reply = process_command(text)
        get_memory().add_message("Jarvis", reply)
        
        self.root.after(0, lambda: self._append_message("JARVIS", reply, "jarvis"))
        if not self.mute:
            speak(reply)

    def _toggle_voice(self):
        if not SR_AVAILABLE:
            messagebox.showerror("Error", "SpeechRecognition is not installed. Please run: pip install SpeechRecognition")
            return
        
        if self.listening:
            return
        
        self.listening = True
        self.core.set_state(listening=True)
        self.mic_btn.config(text="🎙 Listening...", bg=GREEN)
        
        def _on_success(text):
            self.root.after(0, lambda: [
                self.entry.delete(0, "end"),
                self.entry.insert(0, text),
                self._send_text(),
                self._reset_listening_state()
            ])
            
        def _on_error(err):
            logger.error(f"[GUI - Speech] Listening failed: {err}")
            self.root.after(0, lambda: [
                self._append_message("JARVIS", f"Suna nahi Sir! Kripya dobara boliye. Error: {err}", "jarvis"),
                self._reset_listening_state()
            ])

        self.listener.listen_async(_on_success, _on_error)

    def _reset_listening_state(self):
        self.listening = False
        self.core.set_state(listening=False)
        self.mic_btn.config(text="🎙 Listen", bg=CYAN)

    def _toggle_mute(self):
        self.mute = not self.mute
        get_tts_manager().mute = self.mute
        if self.mute:
            self.mute_btn.config(text="🔇 Muted", bg=RED)
            self._append_message("JARVIS", "Jarvis voice output has been muted.", "jarvis")
        else:
            self.mute_btn.config(text="🔊 Mute Off", bg=BG_L3)
            self._append_message("JARVIS", "Jarvis voice output active.", "jarvis")
            speak("Voice active, Sir!")

    # ── Settings Window ───────────────────────────────────────────────────────
    def _open_settings(self):
        from tkinter import ttk
        win = tk.Toplevel(self.root)
        win.title("Jarvis Engine Settings")
        win.geometry("540x740")
        win.configure(bg=BG)
        win.resizable(True, True)

        tk.Label(win, text="Jarvis Engine Settings", font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=CYAN).pack(pady=(16, 4))
        tk.Label(win, text="Configure speech engines, API keys, and voice models",
                 font=FONT_S, bg=BG, fg=TEXT_DIM).pack(pady=(0, 12))

        manager = get_tts_manager()
        cur = manager.engine_label
        avail = manager.available_engines

        tk.Label(win, text=f"Currently Active: {cur}", font=FONT_B, bg=BG, fg=GREEN).pack()

        # Engine selector
        frm = tk.Frame(win, bg=BG, pady=6)
        frm.pack(fill="x", padx=24)
        tk.Label(frm, text="Select Voice Engine:", font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w")
        
        engine_var = tk.StringVar(value=manager.active_name)
        options = [(k, v) for k, v in avail] if avail else [("edge_tts", "Edge TTS Neural")]
        for key, label in options:
            tk.Radiobutton(
                frm, text=label, variable=engine_var, value=key,
                font=FONT, bg=BG, fg=TEXT, selectcolor=BG_L2,
                activebackground=BG, activeforeground=CYAN
            ).pack(anchor="w", padx=12, pady=2)

        # ElevenLabs API Key
        tk.Label(win, text="ElevenLabs API Key (optional):",
                 font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=24, pady=(10,2))
        
        key_var = tk.StringVar(value=manager.config["elevenlabs"].get("api_key", ""))
        key_entry = tk.Entry(win, textvariable=key_var, font=FONT, bg=BG_L3, fg=TEXT,
                             relief="flat", show="*", highlightthickness=1,
                             highlightcolor=CYAN, highlightbackground=BG_L3)
        key_entry.pack(fill="x", padx=24, ipady=4)

        # ElevenLabs Voice ID / Dropdown
        tk.Label(win, text="ElevenLabs Voice ID / Preset:",
                 font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=24, pady=(8,2))
        
        voice_var = tk.StringVar(value=manager.config["elevenlabs"].get("voice_id", "pNInz6obpgDQGcFmaJgB"))
        voice_entry = tk.Entry(win, textvariable=voice_var, font=FONT, bg=BG_L3, fg=TEXT,
                               relief="flat", highlightthickness=1,
                               highlightcolor=CYAN, highlightbackground=BG_L3)
        voice_entry.pack(fill="x", padx=24, ipady=4)

        # Presets Frame
        pfrm = tk.Frame(win, bg=BG)
        pfrm.pack(fill="x", padx=24, pady=4)
        presets = [
            ("Adam (Warm Male)", "pNInz6obpgDQGcFmaJgB"),
            ("Rachel (Warm Female)", "21m00Tcm4TlvDq8ikWAM"),
            ("Antoni (Deep Male)", "ErXwobaYiN019PkySvjV"),
            ("Clyde (Deep Game)", "2EiwWnXF2V4j28gcXi8t")
        ]
        for name, vid in presets:
            tk.Button(
                pfrm, text=name.split()[0], font=FONT_S, bg=BG_L3, fg=CYAN,
                relief="flat", bd=0, cursor="hand2", padx=8, py=2,
                command=lambda v=vid, n=name: [voice_var.set(v), manager.config["elevenlabs"].update({"voice_name": n})]
            ).pack(side="left", padx=2)

        # Voice fetching
        ffrm = tk.Frame(win, bg=BG)
        ffrm.pack(fill="x", padx=24, pady=6)
        
        tk.Label(ffrm, text="Select Account Voice:", font=FONT_S, bg=BG, fg=TEXT_DIM).pack(side="left")
        
        voice_dropdown = ttk.Combobox(ffrm, state="readonly", width=28)
        voice_dropdown.pack(side="left", padx=6)
        voice_dropdown.set("Click Fetch to load voices")
        
        fetched_voices_dict = {}

        def _fetch_voices():
            api_key = key_var.get().strip()
            if api_key:
                manager.set_elevenlabs_key(api_key)
            voices_list = manager.fetch_elevenlabs_voices()
            if voices_list:
                voice_dropdown.config(state="readonly")
                voice_names = []
                for vid, vname in voices_list:
                    full_lbl = f"{vname} ({vid[:6]})"
                    fetched_voices_dict[full_lbl] = vid
                    voice_names.append(full_lbl)
                voice_dropdown['values'] = voice_names
                voice_dropdown.set(voice_names[0])
                voice_var.set(fetched_voices_dict[voice_names[0]])
                status_lbl.config(text=f"Loaded {len(voices_list)} custom voices successfully!", fg=GREEN)
            else:
                status_lbl.config(text="Could not load custom voices. Check API key!", fg=RED)

        def _on_dropdown_select(event):
            selected = voice_dropdown.get()
            if selected in fetched_voices_dict:
                voice_var.set(fetched_voices_dict[selected])

        voice_dropdown.bind("<<ComboboxSelected>>", _on_dropdown_select)

        tk.Button(
            ffrm, text="🔄 Fetch Voices", font=FONT_S, bg=PURPLE, fg="white",
            relief="flat", bd=0, cursor="hand2", padx=10, py=2,
            command=_fetch_voices
        ).pack(side="left", padx=2)

        # ElevenLabs Model Selection
        tk.Label(win, text="ElevenLabs Model:", font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=24, pady=(8,2))
        
        model_var = tk.StringVar(value=manager.config["elevenlabs"].get("model", "eleven_multilingual_v2"))
        mfrm = tk.Frame(win, bg=BG)
        mfrm.pack(fill="x", padx=24, pady=2)
        models = [
            ("Multilingual v2 (Best Quality)", "eleven_multilingual_v2"),
            ("Turbo v2.5 (Fast / Low Cost)", "eleven_turbo_v2_5"),
            ("Flash v2.5 (Super Fast)", "eleven_flash_v2_5")
        ]
        for label, mkey in models:
            tk.Radiobutton(
                mfrm, text=label, variable=model_var, value=mkey,
                font=FONT_S, bg=BG, fg=TEXT, selectcolor=BG_L2,
                activebackground=BG, activeforeground=CYAN
            ).pack(anchor="w", pady=1)

        # Status Label
        status_lbl = tk.Label(win, text="", font=FONT_S, bg=BG, fg=GREEN)
        status_lbl.pack(pady=6)

        def _apply():
            chosen = engine_var.get()
            api_key = key_var.get().strip()
            voice_id = voice_var.get().strip()
            model_id = model_var.get().strip()
            
            if chosen == "elevenlabs":
                manager.update_elevenlabs_settings(api_key, voice_id, model_id)
            else:
                manager.config["elevenlabs"]["api_key"] = api_key
                manager.config["elevenlabs"]["voice_id"] = voice_id
                manager.config["elevenlabs"]["model"] = model_id
                manager.set_engine(chosen)
                
            self._update_footer()
            status_lbl.config(text=f"Settings saved! Active Engine: {manager.engine_label}", fg=GREEN)
            speak("Settings saved successfully!")

        def _test():
            speak("Arre Sir! Yeh test speech hai. Awaaz mast aa rahi hai na?")
            status_lbl.config(text="Testing voice output... listen!", fg=YELLOW)

        # Controls Row
        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(pady=16)
        
        tk.Button(
            btn_row, text="✓ Apply Settings", font=FONT_B, bg=CYAN, fg="white",
            relief="flat", bd=0, padx=20, py=8, cursor="hand2",
            command=_apply
        ).pack(side="left", padx=6)
        
        tk.Button(
            btn_row, text="▶ Test Sound", font=FONT_B, bg=GREEN, fg="white",
            relief="flat", bd=0, padx=16, py=8, cursor="hand2",
            command=_test
        ).pack(side="left", padx=6)
        
        tk.Button(
            btn_row, text="✕ Close", font=FONT_B, bg=BG_L3, fg=TEXT,
            relief="flat", bd=0, padx=16, py=8, cursor="hand2",
            command=win.destroy
        ).pack(side="left", padx=6)
