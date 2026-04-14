#!/usr/bin/env python3
"""
SLAM System Launcher with Dynamic Camera IP Configuration
Allows user to input camera IPs before starting the system
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Add paths
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))

try:
    import customtkinter as ctk
    from tkinter import messagebox
    HAS_CTK = True
except:
    HAS_CTK = False
    import tkinter as tk
    from tkinter import messagebox

import json


class CameraIPConfigDialog:
    """Dialog for configuring camera IPs"""
    
    def __init__(self):
        self.left_ip = "192.168.1.47"
        self.right_ip = "192.168.1.48"
        self.use_synthetic = True
        self.cancelled = False
        
        # Load saved IPs if available
        self.load_saved_config()
    
    def load_saved_config(self):
        """Load previously saved camera IPs"""
        config_file = ROOT / "camera_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.left_ip = config.get('left_ip', self.left_ip)
                    self.right_ip = config.get('right_ip', self.right_ip)
                    self.use_synthetic = config.get('use_synthetic', self.use_synthetic)
            except:
                pass
    
    def save_config(self):
        """Save camera IPs for next time"""
        config_file = ROOT / "camera_config.json"
        config = {
            'left_ip': self.left_ip,
            'right_ip': self.right_ip,
            'use_synthetic': self.use_synthetic
        }
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass
    
    def show_dialog(self):
        """Show configuration dialog"""
        if HAS_CTK:
            return self._show_ctk_dialog()
        else:
            return self._show_tk_dialog()
    
    def _show_ctk_dialog(self):
        """CustomTkinter dialog"""
        root = ctk.CTk()
        root.title("SLAM Camera Configuration")
        root.geometry("500x450")
        root.resizable(False, False)
        
        # Title
        title = ctk.CTkLabel(root, text="🎥 Stereo Camera Configuration",
                            font=("Arial", 18, "bold"))
        title.pack(pady=20)
        
        # Camera mode selection
        mode_frame = ctk.CTkFrame(root)
        mode_frame.pack(pady=10, padx=20, fill="x")
        
        mode_label = ctk.CTkLabel(mode_frame, text="Camera Mode:",
                                 font=("Arial", 12, "bold"))
        mode_label.pack(pady=5)
        
        self.mode_var = ctk.StringVar(value="synthetic" if self.use_synthetic else "real")
        
        radio1 = ctk.CTkRadioButton(mode_frame, text="Use Real ESP32 Cameras",
                                    variable=self.mode_var, value="real")
        radio1.pack(pady=5)
        
        radio2 = ctk.CTkRadioButton(mode_frame, text="Use Synthetic Cameras (Testing)",
                                    variable=self.mode_var, value="synthetic")
        radio2.pack(pady=5)
        
        # IP Configuration (only for real cameras)
        ip_frame = ctk.CTkFrame(root)
        ip_frame.pack(pady=10, padx=20, fill="x")
        
        ip_label = ctk.CTkLabel(ip_frame, text="ESP32 Camera URLs:",
                               font=("Arial", 12, "bold"))
        ip_label.pack(pady=5)
        
        # Left camera
        left_label = ctk.CTkLabel(ip_frame, text="Left Camera IP:")
        left_label.pack(pady=(10, 0))
        
        self.left_entry = ctk.CTkEntry(ip_frame, width=300, placeholder_text="192.168.1.47")
        self.left_entry.insert(0, self.left_ip)
        self.left_entry.pack(pady=5)
        
        # Right camera
        right_label = ctk.CTkLabel(ip_frame, text="Right Camera IP:")
        right_label.pack(pady=(10, 0))
        
        self.right_entry = ctk.CTkEntry(ip_frame, width=300, placeholder_text="192.168.1.48")
        self.right_entry.insert(0, self.right_ip)
        self.right_entry.pack(pady=5)
        
        # Info label
        info = ctk.CTkLabel(root, text="💡 IPs will be saved for next launch",
                           font=("Arial", 10), text_color="gray")
        info.pack(pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(root)
        button_frame.pack(pady=20)
        
        def on_start():
            self.use_synthetic = (self.mode_var.get() == "synthetic")
            if not self.use_synthetic:
                self.left_ip = self.left_entry.get().strip()
                self.right_ip = self.right_entry.get().strip()
                
                if not self.left_ip or not self.right_ip:
                    messagebox.showerror("Error", "Please enter both camera IPs!")
                    return
            
            self.save_config()
            root.destroy()
        
        def on_cancel():
            self.cancelled = True
            root.destroy()
        
        start_btn = ctk.CTkButton(button_frame, text="Start SLAM System",
                                 command=on_start, width=150,
                                 fg_color="green", hover_color="darkgreen")
        start_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel",
                                   command=on_cancel, width=150,
                                   fg_color="gray", hover_color="darkgray")
        cancel_btn.pack(side="left", padx=10)
        
        root.mainloop()
        return not self.cancelled
    
    def _show_tk_dialog(self):
        """Fallback Tkinter dialog"""
        root = tk.Tk()
        root.title("SLAM Camera Configuration")
        root.geometry("450x400")
        
        tk.Label(root, text="🎥 Stereo Camera Configuration",
                font=("Arial", 16, "bold")).pack(pady=20)
        
        # Mode selection
        self.mode_var = tk.StringVar(value="synthetic" if self.use_synthetic else "real")
        
        tk.Label(root, text="Camera Mode:", font=("Arial", 11, "bold")).pack(pady=5)
        tk.Radiobutton(root, text="Use Real ESP32 Cameras",
                      variable=self.mode_var, value="real").pack()
        tk.Radiobutton(root, text="Use Synthetic Cameras (Testing)",
                      variable=self.mode_var, value="synthetic").pack()
        
        # IP inputs
        tk.Label(root, text="\nESP32 Camera IPs:", font=("Arial", 11, "bold")).pack(pady=10)
        
        tk.Label(root, text="Left Camera IP:").pack()
        self.left_entry = tk.Entry(root, width=30)
        self.left_entry.insert(0, self.left_ip)
        self.left_entry.pack(pady=5)
        
        tk.Label(root, text="Right Camera IP:").pack()
        self.right_entry = tk.Entry(root, width=30)
        self.right_entry.insert(0, self.right_ip)
        self.right_entry.pack(pady=5)
        
        tk.Label(root, text="💡 IPs will be saved for next launch",
                fg="gray").pack(pady=10)
        
        def on_start():
            self.use_synthetic = (self.mode_var.get() == "synthetic")
            if not self.use_synthetic:
                self.left_ip = self.left_entry.get().strip()
                self.right_ip = self.right_entry.get().strip()
                
                if not self.left_ip or not self.right_ip:
                    messagebox.showerror("Error", "Please enter both camera IPs!")
                    return
            
            self.save_config()
            root.destroy()
        
        def on_cancel():
            self.cancelled = True
            root.destroy()
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Start SLAM System", command=on_start,
                 bg="green", fg="white", width=15).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=on_cancel,
                 bg="gray", fg="white", width=15).pack(side="left", padx=10)
        
        root.mainloop()
        return not self.cancelled


def main():
    """Main launcher"""
    print("="*60)
    print(" "*15 + "SLAM SYSTEM LAUNCHER")
    print("="*60)
    
    # Show configuration dialog
    config_dialog = CameraIPConfigDialog()
    if not config_dialog.show_dialog():
        print("\nCancelled by user")
        return
    
    # Import and launch appropriate system
    if config_dialog.use_synthetic:
        print("\n✓ Using Synthetic Cameras")
        from ultimate_slam_rl_gui import UltimateSLAMRLSystem
        system = UltimateSLAMRLSystem(use_synthetic=True)
    else:
        print(f"\n✓ Using Real ESP32 Cameras")
        print(f"   Left:  http://{config_dialog.left_ip}/stream")
        print(f"   Right: http://{config_dialog.right_ip}/stream")
        
        # Patch camera URLs
        from camera_stream_handler import StereoCameraManager
        from ultimate_slam_rl_gui import UltimateSLAMRLSystem
        
        # Create custom system with real cameras
        system = UltimateSLAMRLSystem(use_synthetic=False)
        system.camera_manager = StereoCameraManager(
            f"http://{config_dialog.left_ip}/stream",
            f"http://{config_dialog.right_ip}/stream"
        )
    
    # Start the system
    print("\nStarting SLAM system...\n")
    system.start()


if __name__ == "__main__":
    main()
