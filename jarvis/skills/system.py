import os
import platform
import psutil
import subprocess
from jarvis.logger import logger

def get_system_report() -> str:
    try:
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.1)
        used_mem = round(mem.used / (1024**3), 1)
        total_mem = round(mem.total / (1024**3), 1)
        
        report = (
            f"Sir, system report ekdum ready hai!\n\n"
            f"● OS : {platform.system()} {platform.release()} ({platform.architecture()[0]})\n"
            f"● CPU Usage : {cpu_pct}%\n"
            f"● Memory : {used_mem} GB / {total_mem} GB used\n"
            f"● Computer Name : {platform.node()}\n\n"
            f"Sab kuch mast chal raha hai, tension mat lo!"
        )
        return report
    except Exception as e:
        logger.error(f"[Skill - System] Report failed: {e}")
        return f"Sir, system metrics report load nahi ho paayi: {e}"

def open_application(app_name: str) -> str:
    app_name = app_name.lower().strip()
    try:
        if "chrome" in app_name:
            subprocess.Popen(["cmd.exe", "/c", "start chrome"])
            return "Lo Sir, Chrome khol diya! Mast surfing karo!"
        elif "notepad" in app_name:
            subprocess.Popen(["notepad.exe"])
            return "Notepad open kar diya hai, Sir! Notes likh lo."
        elif "calculator" in app_name or "calc" in app_name:
            subprocess.Popen(["calc.exe"])
            return "Lo Sir, Calculator hazir hai!"
        else:
            # Try to run it as a command line startup shortcut
            subprocess.Popen(["cmd.exe", "/c", f"start {app_name}"], shell=True)
            return f"Theek hai Sir, {app_name} open karne ki koshish kar raha hoon!"
    except Exception as e:
        logger.error(f"[Skill - System] Failed to open {app_name}: {e}")
        return f"Sir, application '{app_name}' kholne mein error aaya: {e}"
