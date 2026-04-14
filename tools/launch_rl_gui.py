"""
Launcher for RL Training GUI Application
Provides an easy-to-use interface for training the RL keyframe selection agent
"""

import sys
import os

# Add the runtime directory to the path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

runtime_path = os.path.join(application_path, 'app', 'runtime')
if os.path.exists(runtime_path):
    sys.path.insert(0, runtime_path)

def main():
    """Launch the RL Training GUI"""
    try:
        # Import the RL_QUICK_START module and execute it
        # The module runs its GUI automatically on import
        import RL_QUICK_START
    except Exception as e:
        # For GUI apps, show error in a message box instead of console
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        import traceback
        error_msg = f"Error launching RL Training GUI:\n\n{str(e)}\n\n{traceback.format_exc()}"
        messagebox.showerror("RL Trainer Error", error_msg)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
