import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import datetime
import os
import subprocess
import webbrowser
import platform
import json
import urllib.request
import urllib.parse
import sys

# ─────────────────────────────────────────
#  JARVIS CONFIG
# ─────────────────────────────────────────
NOTES_FILE = os.path.join(os.path.dirname(__file__), "jarvis_notes.json")
BG        = "#0a0e1a"
BG2       = "#111827"
ACCENT    = "#00d4ff"
ACCENT2   = "#7c3aed"
TEXT      = "#e2e8f0"
TEXT_DIM  = "#64748b"
GREEN     = "#10b981"
RED       = "#ef4444"
YELLOW    = "#f59e0b"
FONT      = ("Segoe UI", 11)
FONT_B    = ("Segoe UI", 11, "bold")
FONT_T    = ("Segoe UI", 13, "bold")
FONT_S    = ("Segoe UI", 9)

# ─────────────────────────────────────────
#  NOTES HELPER
# ─────────────────────────────────────────
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r") as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

# ─────────────────────────────────────────
#  COMMAND PROCESSOR
# ─────────────────────────────────────────
def process_command(cmd):
    cmd = cmd.strip()
    low = cmd.lower()

    # ── TIME / DATE ──────────────────────
    if any(x in low for x in ["time", "what time"]):
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}."

    if any(x in low for x in ["date", "today", "day"]):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %d %B %Y')}."

    # ── GREETINGS ────────────────────────
    if any(x in low for x in ["hello", "hi", "hey", "good morning", "good evening", "good night"]):
        hour = datetime.datetime.now().hour
        if hour < 12:   greeting = "Good morning"
        elif hour < 17: greeting = "Good afternoon"
        else:           greeting = "Good evening"
        return f"{greeting}, Gopal! I'm Jarvis, fully operational and at your service. How can I assist you today?"

    # ── SYSTEM INFO ──────────────────────
    if any(x in low for x in ["system info", "system", "cpu", "ram", "memory", "computer info", "pc info"]):
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            bat  = psutil.sensors_battery()
            bat_str = f"{bat.percent:.0f}% ({'Charging' if bat.power_plugged else 'Discharging'})" if bat else "N/A"
            return (
                f"System Report for ZORO:\n"
                f"  OS       : {platform.system()} {platform.release()}\n"
                f"  Python   : {platform.python_version()}\n"
                f"  CPU      : {cpu}% usage\n"
                f"  RAM      : {ram.percent}% used ({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)\n"
                f"  Disk C:  : {disk.percent}% used ({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)\n"
                f"  Battery  : {bat_str}"
            )
        except ImportError:
            return (
                f"System Info (basic):\n"
                f"  OS      : {platform.system()} {platform.release()}\n"
                f"  Machine : {platform.node()}\n"
                f"  Python  : {platform.python_version()}\n"
                f"  User    : {os.environ.get('USERNAME','Gopal')}\n"
                f"  Tip: Run 'pip install psutil' for full system stats."
            )

    # ── WEATHER ──────────────────────────
    if any(x in low for x in ["weather", "temperature", "forecast", "rain"]):
        city = "Pune"
        for word in low.split():
            if word not in ["weather","temperature","forecast","rain","in","at","for","the","what","is","today"]:
                city = word.capitalize()
                break
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
            with urllib.request.urlopen(url, timeout=5) as r:
                result = r.read().decode()
            return f"Weather update:\n  {result}"
        except:
            return f"Could not fetch weather for {city}. Please check your internet connection."

    # ── OPEN APPS ────────────────────────
    app_map = {
        "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "google":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "notepad":      "notepad.exe",
        "calculator":   "calc.exe",
        "paint":        "mspaint.exe",
        "explorer":     "explorer.exe",
        "files":        "explorer.exe",
        "task manager": "taskmgr.exe",
        "cmd":          "cmd.exe",
        "powershell":   "powershell.exe",
        "vs code":      "code",
        "vscode":       "code",
        "word":         r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel":        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    }
    for app, path in app_map.items():
        if f"open {app}" in low or f"launch {app}" in low or f"start {app}" in low:
            try:
                subprocess.Popen(path, shell=True)
                return f"Opening {app.capitalize()} for you, Gopal!"
            except:
                return f"Could not open {app}. It may not be installed."

    # ── YOUTUBE ──────────────────────────
    if any(x in low for x in ["youtube", "play music", "open youtube"]):
        query = low.replace("play","").replace("on youtube","").replace("youtube","").replace("open","").replace("music","").strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        else:
            url = "https://www.youtube.com"
        webbrowser.open(url)
        return f"Opening YouTube{' and searching for: ' + query if query else ''}!"

    # ── WEB SEARCH ───────────────────────
    if any(x in low for x in ["search", "google", "look up", "find"]):
        query = low
        for word in ["search for", "search", "google", "look up", "find"]:
            query = query.replace(word, "").strip()
        if query:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Searching Google for: '{query}'"
        else:
            webbrowser.open("https://www.google.com")
            return "Opening Google for you!"

    # ── GITHUB ───────────────────────────
    if "github" in low:
        webbrowser.open("https://github.com/hariomsurve0-lab")
        return "Opening your GitHub profile!"

    # ── GMAIL ────────────────────────────
    if "gmail" in low or "email" in low or "mail" in low:
        webbrowser.open("https://mail.google.com")
        return "Opening Gmail for you, Gopal!"

    # ── NOTES ADD ────────────────────────
    if any(low.startswith(x) for x in ["note:", "add note", "remember", "save note"]):
        note_text = cmd
        for prefix in ["note:", "add note", "remember", "save note"]:
            note_text = note_text.replace(prefix, "").replace(prefix.lower(), "").strip()
        notes = load_notes()
        notes.append({"text": note_text, "time": datetime.datetime.now().strftime("%d %b %Y %I:%M %p")})
        save_notes(notes)
        return f"Note saved: \"{note_text}\""

    # ── NOTES SHOW ───────────────────────
    if any(x in low for x in ["show notes", "my notes", "list notes", "show my notes"]):
        notes = load_notes()
        if not notes:
            return "You have no saved notes yet. Say 'add note: your message' to save one!"
        result = f"You have {len(notes)} note(s):\n"
        for i, n in enumerate(notes, 1):
            result += f"\n  {i}. [{n['time']}]\n     {n['text']}"
        return result

    # ── NOTES CLEAR ──────────────────────
    if any(x in low for x in ["clear notes", "delete notes", "remove notes"]):
        save_notes([])
        return "All notes cleared!"

    # ── JOKES ────────────────────────────
    if any(x in low for x in ["joke", "funny", "make me laugh"]):
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "Why did the developer go broke? Because he used up all his cache! 💸",
            "I told my computer I needed a break. Now it won't stop sending me Kit Kat ads.",
            "Why do Java developers wear glasses? Because they don't C#! 😄",
            "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
        ]
        import random
        return random.choice(jokes)

    # ── MOTIVATION ───────────────────────
    if any(x in low for x in ["motivate", "motivation", "inspire", "quote"]):
        quotes = [
            "The only way to do great work is to love what you do. — Steve Jobs",
            "Code is like humor. When you have to explain it, it's bad. — Cory House",
            "First, solve the problem. Then, write the code. — John Johnson",
            "Talk is cheap. Show me the code. — Linus Torvalds",
            "Make it work, make it right, make it fast. — Kent Beck",
        ]
        import random
        return f"Here's some motivation for you, Gopal:\n\n\"{random.choice(quotes)}\""

    # ── SHUTDOWN / RESTART ───────────────
    if any(x in low for x in ["shutdown", "shut down", "turn off"]):
        return "For safety, I won't auto-shutdown your PC. Run 'shutdown /s /t 0' in PowerShell if you're sure!"

    if "restart" in low or "reboot" in low:
        return "For safety, I won't auto-restart your PC. Run 'shutdown /r /t 0' in PowerShell if you're sure!"

    # ── HELP ─────────────────────────────
    if any(x in low for x in ["help", "what can you do", "commands", "features"]):
        return (
            "Here's what I can do for you, Gopal:\n\n"
            "  Time & Date  : 'what time is it', 'what's today's date'\n"
            "  Weather      : 'weather in Bangalore'\n"
            "  Open Apps    : 'open chrome', 'open notepad', 'open calculator'\n"
            "  Web Search   : 'search for Python tutorials'\n"
            "  YouTube      : 'play lofi music on youtube'\n"
            "  Gmail        : 'open gmail'\n"
            "  GitHub       : 'open github'\n"
            "  System Info  : 'system info', 'cpu usage', 'ram'\n"
            "  Notes        : 'add note: buy groceries', 'show notes'\n"
            "  Jokes        : 'tell me a joke'\n"
            "  Motivation   : 'motivate me', 'give me a quote'\n"
            "  Help         : 'help', 'what can you do'"
        )

    # ── DEFAULT ──────────────────────────
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(cmd)}")
    return f"I searched Google for: '{cmd}'\nTip: Say 'help' to see all my commands!"

# ─────────────────────────────────────────
#  JARVIS GUI
# ─────────────────────────────────────────
class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS — AI Personal Assistant")
        self.root.geometry("800x640")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(600, 500)
        self._build_ui()
        self._welcome()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=ACCENT2, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⬡  JARVIS", font=("Segoe UI", 18, "bold"),
                 bg=ACCENT2, fg="white").pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="AI Personal Assistant  •  Gopal's Laptop",
                 font=FONT_S, bg=ACCENT2, fg="#c4b5fd").pack(side="left", padx=4, pady=12)

        # Status dot
        self.status_dot = tk.Label(hdr, text="● ONLINE", font=FONT_S, bg=ACCENT2, fg=GREEN)
        self.status_dot.pack(side="right", padx=20)

        # Time label
        self.time_lbl = tk.Label(hdr, text="", font=FONT_S, bg=ACCENT2, fg="#c4b5fd")
        self.time_lbl.pack(side="right", padx=10)
        self._tick()

        # Quick command bar
        qbar = tk.Frame(self.root, bg=BG2, pady=8)
        qbar.pack(fill="x", padx=0)
        tk.Label(qbar, text="Quick:", font=FONT_S, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=12)

        quick_cmds = ["Time", "Weather", "System Info", "My Notes", "Joke", "Help"]
        for q in quick_cmds:
            btn = tk.Button(qbar, text=q, font=FONT_S, bg="#1e293b", fg=ACCENT,
                            relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                            activebackground=ACCENT2, activeforeground="white",
                            command=lambda c=q: self._quick(c))
            btn.pack(side="left", padx=4)

        # Chat area
        self.chat = scrolledtext.ScrolledText(
            self.root, font=FONT, bg=BG, fg=TEXT,
            relief="flat", bd=0, padx=16, pady=12,
            state="disabled", wrap="word",
            insertbackground=ACCENT
        )
        self.chat.pack(fill="both", expand=True, padx=0, pady=(0, 0))
        self.chat.tag_config("jarvis",  foreground=ACCENT,  font=FONT_B)
        self.chat.tag_config("user",    foreground=ACCENT2, font=FONT_B)
        self.chat.tag_config("msg",     foreground=TEXT,    font=FONT)
        self.chat.tag_config("dim",     foreground=TEXT_DIM,font=FONT_S)
        self.chat.tag_config("success", foreground=GREEN,   font=FONT)
        self.chat.tag_config("error",   foreground=RED,     font=FONT)

        # Input bar
        bar = tk.Frame(self.root, bg=BG2, pady=10)
        bar.pack(fill="x", padx=0)

        self.entry = tk.Entry(bar, font=FONT_T, bg="#1e293b", fg=TEXT,
                              relief="flat", bd=0, insertbackground=ACCENT,
                              highlightthickness=2, highlightcolor=ACCENT,
                              highlightbackground=BG2)
        self.entry.pack(side="left", fill="x", expand=True, padx=(16,8), ipady=10)
        self.entry.bind("<Return>", lambda e: self._send())
        self.entry.focus()

        send_btn = tk.Button(bar, text="▶  Send", font=FONT_B, bg=ACCENT2, fg="white",
                             relief="flat", bd=0, padx=20, pady=10, cursor="hand2",
                             activebackground="#6d28d9", activeforeground="white",
                             command=self._send)
        send_btn.pack(side="right", padx=(0,16))

        # Footer
        tk.Label(self.root, text="Tip: Type 'help' to see all commands  •  Powered by Jarvis",
                 font=FONT_S, bg=BG, fg=TEXT_DIM).pack(pady=(0,6))

    def _tick(self):
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.time_lbl.config(text=now)
        self.root.after(1000, self._tick)

    def _welcome(self):
        now = datetime.datetime.now()
        hour = now.hour
        if hour < 12:   g = "Good morning"
        elif hour < 17: g = "Good afternoon"
        else:           g = "Good evening"
        self._jarvis_msg(
            f"{g}, Gopal! I am JARVIS — your AI Personal Assistant.\n"
            f"Today is {now.strftime('%A, %d %B %Y')} and the time is {now.strftime('%I:%M %p')}.\n\n"
            f"I'm fully operational and ready to assist you.\n"
            f"Type 'help' to see everything I can do for you!"
        )

    def _append(self, text, tag="msg"):
        self.chat.config(state="normal")
        self.chat.insert("end", text, tag)
        self.chat.config(state="disabled")
        self.chat.see("end")

    def _jarvis_msg(self, msg):
        self._append("\nJARVIS  ", "jarvis")
        self._append(f"[{datetime.datetime.now().strftime('%I:%M %p')}]\n", "dim")
        self._append(f"{msg}\n", "msg")
        self._append("─" * 60 + "\n", "dim")

    def _user_msg(self, msg):
        self._append(f"\nGopal   ", "user")
        self._append(f"[{datetime.datetime.now().strftime('%I:%M %p')}]\n", "dim")
        self._append(f"{msg}\n", "msg")

    def _quick(self, cmd):
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self._send()

    def _send(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, "end")
        self._user_msg(cmd)
        threading.Thread(target=self._respond, args=(cmd,), daemon=True).start()

    def _respond(self, cmd):
        self.status_dot.config(text="● THINKING...", fg=YELLOW)
        try:
            response = process_command(cmd)
        except Exception as e:
            response = f"Error: {e}"
        self.root.after(0, lambda: self._jarvis_msg(response))
        self.root.after(0, lambda: self.status_dot.config(text="● ONLINE", fg=GREEN))

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = JarvisApp(root)
    root.mainloop()
