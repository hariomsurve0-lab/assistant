from jarvis.memory import get_memory
from jarvis.logger import logger

def save_new_note(title: str, content: str) -> str:
    if not title or not content:
        return "Sir, title aur context dono batao na! Adha adhura notes mat likho."
    try:
        mem = get_memory()
        mem.add_note(title.strip(), content.strip())
        return f"Sir, Note '{title}' database mein permanently save ho gaya hai! Chinta mat karo."
    except Exception as e:
        logger.error(f"[Skill - Notes] Save failed: {e}")
        return f"Sir, Note save karne mein dikqat aa gayi: {e}"

def list_all_notes() -> str:
    try:
        mem = get_memory()
        notes = mem.get_all_notes()
        if not notes:
            return "Sir, abhi tak koi notes save nahi kiye hain aapne!"
        
        reply = "Sir, yeh rahe aapke saare saved notes:\n\n"
        for i, (title, content) in enumerate(notes, 1):
            reply += f"{i}. 📝 **{title}**\n   {content}\n\n"
        return reply.strip()
    except Exception as e:
        logger.error(f"[Skill - Notes] List failed: {e}")
        return f"Sir, notes load nahi ho paaye: {e}"

def remove_note(title: str) -> str:
    if not title:
        return "Sir, kaunsa note delete karna hai? Name toh batao!"
    try:
        mem = get_memory()
        mem.delete_note(title.strip())
        return f"Sir, Note '{title}' ko delete kar diya hai database se!"
    except Exception as e:
        logger.error(f"[Skill - Notes] Delete failed: {e}")
        return f"Sir, note delete nahi ho paaya: {e}"
