"""
Dynamic IP Configuration Module
Shared by all SLAM applications
"""

import json
from pathlib import Path
try:
    import customtkinter as ctk
    from tkinter import messagebox
    HAS_CTK = True
except:
    HAS_CTK = False
    import tkinter as tk
    from tkinter import messagebox


class DynamicIPConfig:
    """Manages camera IP configuration with GUI"""
    
    def __init__(self, config_file="camera_config.json"):
        self.config_file = Path(__file__).parent / config_file
        self.left_ip = "10.95.247.247"
        self.right_ip = "10.95.247.139"
        self.left_url = ""
        self.right_url = ""
        self.use_synthetic = False
        self.cancelled = False
        self.load_config()
    
    def load_config(self):
        """Load saved configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.left_ip = config.get('left_ip', self.left_ip)
                    self.right_ip = config.get('right_ip', self.right_ip)
                    self.use_synthetic = config.get('use_synthetic', True)
                    
                    # Build URLs from loaded IPs
                    if not self.use_synthetic:
                        self.left_url = f"http://{self.left_ip}/stream"
                        self.right_url = f"http://{self.right_ip}/stream"
            except:
                pass
    
    def save_config(self):
        """Save configuration"""
        config = {
            'left_ip': self.left_ip,
            'right_ip': self.right_ip,
            'use_synthetic': self.use_synthetic
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass
    
    def show_config_dialog(self, title="Camera Configuration"):
        """Show IP configuration dialog"""
        if HAS_CTK:
            return self._show_ctk_dialog(title)
        else:
            return self._show_tk_dialog(title)
    
    def _show_ctk_dialog(self, title):
        """CustomTkinter dialog"""
        root = ctk.CTk()
        root.title(title)
        root.geometry("550x500")
        root.resizable(False, False)
        
        # Title
        title_label = ctk.CTkLabel(root, text="🎥 ESP32 Camera Configuration",
                                   font=("Arial", 20, "bold"))
        title_label.pack(pady=20)
        
        # Mode frame
        mode_frame = ctk.CTkFrame(root)
        mode_frame.pack(pady=10, padx=30, fill="x")
        
        mode_label = ctk.CTkLabel(mode_frame, text="Select Camera Mode:",
                                 font=("Arial", 13, "bold"))
        mode_label.pack(pady=10)
        
        self.mode_var = ctk.StringVar(value="synthetic" if self.use_synthetic else "real")
        
        radio1 = ctk.CTkRadioButton(mode_frame, text="🌐 Real ESP32 Cameras (WiFi Required)",
                                    variable=self.mode_var, value="real",
                                    font=("Arial", 12))
        radio1.pack(pady=5, anchor="w", padx=20)
        
        radio2 = ctk.CTkRadioButton(mode_frame, text="🎨 Synthetic Cameras (Offline Testing)",
                                    variable=self.mode_var, value="synthetic",
                                    font=("Arial", 12))
        radio2.pack(pady=5, anchor="w", padx=20)
        
        # IP Configuration
        ip_frame = ctk.CTkFrame(root)
        ip_frame.pack(pady=15, padx=30, fill="both", expand=True)
        
        ip_title = ctk.CTkLabel(ip_frame, text="Camera IP Addresses:",
                               font=("Arial", 13, "bold"))
        ip_title.pack(pady=10)
        
        # Left camera
        left_frame = ctk.CTkFrame(ip_frame, fg_color="transparent")
        left_frame.pack(pady=5, fill="x", padx=20)
        
        left_label = ctk.CTkLabel(left_frame, text="Left Camera IP:",
                                 font=("Arial", 11))
        left_label.pack(anchor="w")
        
        self.left_entry = ctk.CTkEntry(left_frame, width=350, height=35,
                                       placeholder_text="e.g., 192.168.1.47",
                                       font=("Arial", 12))
        self.left_entry.insert(0, self.left_ip)
        self.left_entry.pack(pady=5)
        
        # Right camera
        right_frame = ctk.CTkFrame(ip_frame, fg_color="transparent")
        right_frame.pack(pady=5, fill="x", padx=20)
        
        right_label = ctk.CTkLabel(right_frame, text="Right Camera IP:",
                                  font=("Arial", 11))
        right_label.pack(anchor="w")
        
        self.right_entry = ctk.CTkEntry(right_frame, width=350, height=35,
                                        placeholder_text="e.g., 192.168.1.48",
                                        font=("Arial", 12))
        self.right_entry.insert(0, self.right_ip)
        self.right_entry.pack(pady=5)
        
        # Stream path info
        info_label = ctk.CTkLabel(ip_frame, 
                                 text="ℹ️ Full URL will be: http://<IP>/stream",
                                 font=("Arial", 10), text_color="gray")
        info_label.pack(pady=5)
        
        # Save info
        save_label = ctk.CTkLabel(root, text="💾 Configuration will be saved automatically",
                                 font=("Arial", 10), text_color="gray")
        save_label.pack(pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(root, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def on_start():
            self.use_synthetic = (self.mode_var.get() == "synthetic")
            
            if not self.use_synthetic:
                self.left_ip = self.left_entry.get().strip()
                self.right_ip = self.right_entry.get().strip()
                
                # Validate IPs
                if not self.left_ip or not self.right_ip:
                    messagebox.showerror("Error", "Please enter both camera IPs!")
                    return
                
                # Build URLs
                self.left_url = f"http://{self.left_ip}/stream"
                self.right_url = f"http://{self.right_ip}/stream"
            
            self.save_config()
            root.destroy()
        
        def on_cancel():
            self.cancelled = True
            root.destroy()
        
        start_btn = ctk.CTkButton(button_frame, text="▶ Start System",
                                 command=on_start, width=180, height=40,
                                 fg_color="green", hover_color="darkgreen",
                                 font=("Arial", 13, "bold"))
        start_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="✖ Cancel",
                                   command=on_cancel, width=180, height=40,
                                   fg_color="gray", hover_color="darkgray",
                                   font=("Arial", 13, "bold"))
        cancel_btn.pack(side="left", padx=10)
        
        root.mainloop()
        return not self.cancelled
    
    def _show_tk_dialog(self, title):
        """Fallback Tkinter dialog"""
        root = tk.Tk()
        root.title(title)
        root.geometry("500x450")
        
        tk.Label(root, text="🎥 ESP32 Camera Configuration",
                font=("Arial", 16, "bold")).pack(pady=20)
        
        # Mode
        self.mode_var = tk.StringVar(value="synthetic" if self.use_synthetic else "real")
        
        tk.Label(root, text="Select Camera Mode:", font=("Arial", 11, "bold")).pack(pady=10)
        tk.Radiobutton(root, text="Real ESP32 Cameras (WiFi Required)",
                      variable=self.mode_var, value="real",
                      font=("Arial", 10)).pack(anchor="w", padx=50)
        tk.Radiobutton(root, text="Synthetic Cameras (Offline Testing)",
                      variable=self.mode_var, value="synthetic",
                      font=("Arial", 10)).pack(anchor="w", padx=50)
        
        # IPs
        tk.Label(root, text="\nCamera IP Addresses:", font=("Arial", 11, "bold")).pack(pady=10)
        
        tk.Label(root, text="Left Camera IP:").pack()
        self.left_entry = tk.Entry(root, width=35, font=("Arial", 11))
        self.left_entry.insert(0, self.left_ip)
        self.left_entry.pack(pady=5)
        
        tk.Label(root, text="Right Camera IP:").pack()
        self.right_entry = tk.Entry(root, width=35, font=("Arial", 11))
        self.right_entry.insert(0, self.right_ip)
        self.right_entry.pack(pady=5)
        
        tk.Label(root, text="Full URL: http://<IP>/stream", fg="gray").pack(pady=5)
        tk.Label(root, text="💾 Configuration will be saved", fg="gray").pack(pady=10)
        
        def on_start():
            self.use_synthetic = (self.mode_var.get() == "synthetic")
            
            if not self.use_synthetic:
                self.left_ip = self.left_entry.get().strip()
                self.right_ip = self.right_entry.get().strip()
                
                if not self.left_ip or not self.right_ip:
                    messagebox.showerror("Error", "Please enter both camera IPs!")
                    return
                
                self.left_url = f"http://{self.left_ip}/stream"
                self.right_url = f"http://{self.right_ip}/stream"
            
            self.save_config()
            root.destroy()
        
        def on_cancel():
            self.cancelled = True
            root.destroy()
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Start System", command=on_start,
                 bg="green", fg="white", width=15, height=2,
                 font=("Arial", 11, "bold")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=on_cancel,
                 bg="gray", fg="white", width=15, height=2,
                 font=("Arial", 11, "bold")).pack(side="left", padx=10)
        
        root.mainloop()
        return not self.cancelled
    
    def get_camera_urls(self):
        """Get configured camera URLs"""
        if self.use_synthetic:
            return None, None
        return self.left_url, self.right_url
