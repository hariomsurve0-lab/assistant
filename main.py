import tkinter as tk
import sys
from jarvis.logger import logger
from jarvis.gui.app import JarvisApp

def main():
    logger.info("=========================================")
    logger.info("      JARVIS Autonomous Assistant")
    logger.info("=========================================")
    
    try:
        root = tk.Tk()
        app = JarvisApp(root)
        logger.info("[Main] GUI initialized successfully. Starting main loop...")
        root.mainloop()
        logger.info("[Main] GUI main loop finished. Exiting...")
    except Exception as e:
        logger.critical(f"[Main] Unhandled crash: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
