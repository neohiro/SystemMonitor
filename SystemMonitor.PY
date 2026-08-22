import tkinter as tk
from tkinter import messagebox
import time
import datetime
import os
import sys
import json
import subprocess
import psutil
import ping3
import glob


class WidgetPersistence:
    """Keeps the window visible across Show Desktop (Win+D), Win+M and
    virtual-desktop switches on Windows, Linux and macOS.

    Strategy per platform:
    - Windows: WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE styling plus a poll that
      restores the window whenever Explorer minimizes it (Show Desktop) or a
      virtual-desktop switch hides it.
    - Linux/X11: dock window type (sticky/above/no-taskbar where the WM
      honours it), optional wmctrl hints, plus polling fallback.
    - macOS: always-on-top plus polling fallback (joining all Spaces needs
      PyObjC; best-effort only).
    """

    POLL_MS = 800

    def __init__(self, root):
        self.root = root
        self.enabled = False
        self._job = None
        self._hwnd = None

    def enable(self):
        if self.enabled:
            return True
        self.enabled = True
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass
        self._apply_platform_style()
        self._poll()
        return True

    def disable(self):
        if not self.enabled:
            return False
        self.enabled = False
        if self._job:
            try:
                self.root.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self._restore_platform_style()
        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass
        return False

    def toggle(self):
        return self.disable() if self.enabled else self.enable()

    # ---- platform styling --------------------------------------------
    def _apply_platform_style(self):
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                GWL_EXSTYLE = -20
                WS_EX_TOOLWINDOW = 0x00000080   # no taskbar button, skips Alt-Tab
                WS_EX_NOACTIVATE = 0x08000000   # never steals focus when clicked
                style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE,
                                         style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
                self._hwnd = hwnd
            except Exception:
                self._hwnd = None
        elif sys.platform.startswith("linux"):
            try:
                # Dock type: sticky + above + skip-taskbar on mutter/KDE/XFCE.
                self.root.attributes("-type", "dock")
            except Exception:
                pass
            try:
                import shutil
                if shutil.which("wmctrl"):
                    subprocess.Popen(
                        ["wmctrl", "-i", "-r", hex(self.root.winfo_id()),
                         "-b", "add,sticky,above,skip_taskbar"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:  # macOS: topmost already applied; all-Spaces needs PyObjC
            pass

    def _restore_platform_style(self):
        if sys.platform == "win32" and self._hwnd:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                GWL_EXSTYLE = -20
                WS_EX_TOOLWINDOW = 0x00000080
                WS_EX_NOACTIVATE = 0x08000000
                style = user32.GetWindowLongPtrW(self._hwnd, GWL_EXSTYLE)
                user32.SetWindowLongPtrW(self._hwnd, GWL_EXSTYLE,
                                         style & ~(WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE))
            except Exception:
                pass
        self._hwnd = None

    # ---- persistence loop ---------------------------------------------
    def _poll(self):
        if not self.enabled:
            return
        try:
            if sys.platform == "win32" and self._hwnd:
                import ctypes
                user32 = ctypes.windll.user32
                if user32.IsIconic(self._hwnd) or not user32.IsWindowVisible(self._hwnd):
                    SW_SHOWNOACTIVATE = 4
                    HWND_TOPMOST = -1
                    SWP_NOSIZE = 0x1; SWP_NOMOVE = 0x2
                    SWP_NOACTIVATE = 0x10; SWP_SHOWWINDOW = 0x40
                    user32.ShowWindow(self._hwnd, SW_SHOWNOACTIVATE)
                    user32.SetWindowPos(self._hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            state = ""
            try:
                state = self.root.state()
            except Exception:
                pass
            if state in ("iconic", "icon", "withdrawn"):
                self.root.deiconify()
                self.root.attributes("-topmost", True)
                self.root.lift()
        except Exception:
            pass
        self._job = self.root.after(self.POLL_MS, self._poll)



class SensorTrackerApp:
    def __init__(self, master):
        self.master = master
        master.title("System Monitor - FrenzyPenguin Media")
        master.resizable(True, True)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        self.icon_path = icon_path
        if os.path.exists(icon_path):
            try:
                master.iconbitmap(icon_path)
            except tk.TclError:
                pass

        self.themes = [
            {
                "bg_main": "#263238",
                "fg_text_primary": "#ECEFF1",
                "fg_text_secondary": "#B0BEC5",
                "highlight_color": "#607D8B",
                "accent_color": "#66BB6A",
            },
            {
                "bg_main": "#122026",
                "fg_text_primary": "#C8D9E0",
                "fg_text_secondary": "#8FA5B2",
                "highlight_color": "#4A687D",
                "accent_color": "#42A5F5",
            },
            {
                "bg_main": "#261214",
                "fg_text_primary": "#E0C8C8",
                "fg_text_secondary": "#B28F8F",
                "highlight_color": "#7D4A4B",
                "accent_color": "#F54242",
            },
            {
                "bg_main": "#1A2E2A",
                "fg_text_primary": "#D5E8D1",
                "fg_text_secondary": "#9BB295",
                "highlight_color": "#4E665F",
                "accent_color": "#5A9E66",
            },
            {
                "bg_main": "#3D1A25",
                "fg_text_primary": "#F7D1BA",
                "fg_text_secondary": "#C78D8D",
                "highlight_color": "#8C4E61",
                "accent_color": "#F38562",
            },
            {
                "bg_main": "#4E342E",
                "fg_text_primary": "#FFFDE7",
                "fg_text_secondary": "#D7CCC8",
                "highlight_color": "#8D6E63",
                "accent_color": "#FFC107",
            }
        ]

        self.current_theme_index = 0
        self.bg_main = ""
        self.fg_text_primary = ""
        self.fg_text_secondary = ""
        self.highlight_color = ""
        self.accent_color = ""
        self.button_fg = "#FFFFFF"

        self.font_title = ("Segoe UI", 18, "bold")
        self.font_label = ("Segoe UI", 11)
        self.font_value = ("Segoe UI", 16, "bold")
        self.font_unit = ("Segoe UI", 11)
        self.font_status = ("Segoe UI", 8, "italic")
        self.font_button = ("Segoe UI", 10, "bold")
        self.font_message_title = ("Segoe UI", 12, "bold")
        self.font_message_text = ("Segoe UI", 10)
        
        self.all_sensors = {
            "cpu_core_usage": {"device": "CPU", "label": "Core Usage", "unit": "%", "type": "cpu_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "cpu_cores": {"device": "CPU", "label": "Cores", "unit": "", "type": "static", "var": tk.StringVar(), "value": psutil.cpu_count(logical=True), "history": [0]},
            "cpu_freq": {"device": "CPU", "label": "Frequency", "unit": "GHz", "type": "cpu_freq", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "cpu_uptime": {"device": "CPU", "label": "Uptime", "unit": "", "type": "uptime", "var": tk.StringVar(), "history": [0]},
            "ram_usage": {"device": "Memory", "label": "Usage", "unit": "%", "type": "ram_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "ram_total": {"device": "Memory", "label": "Total", "unit": "GB", "type": "static", "var": tk.StringVar(), "value": round(psutil.virtual_memory().total / (1024**3), 2), "history": [0]},
            "ram_used": {"device": "Memory", "label": "Used", "unit": "GB", "type": "ram_used", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "disk_usage": {"device": "Disk", "label": "Usage", "unit": "%", "type": "disk_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "disk_total": {"device": "Disk", "label": "Total", "unit": "GB", "type": "static", "var": tk.StringVar(), "value": round(psutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\" if os.name == "nt" else "/").total / (1024**3), 2), "history": [0]},
            "disk_free": {"device": "Disk", "label": "Free", "unit": "GB", "type": "disk_free", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "net_down": {"device": "Network", "label": "Download", "unit": "MB/s", "type": "net_down", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "net_up": {"device": "Network", "label": "Upload", "unit": "MB/s", "type": "net_up", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "ping_latency": {"device": "Network", "label": "Latency", "unit": "ms", "type": "ping_latency", "var": tk.StringVar(), "history": [], "last_valid_reading": None}
        }
        
        can_get_temp = False
        if hasattr(psutil, 'sensors_temperatures') and psutil.sensors_temperatures():
            can_get_temp = True
        elif os.name == 'posix' and (glob.glob('/sys/class/thermal/thermal_zone*/temp') or glob.glob('/sys/class/hwmon/hwmon*/temp*_input')):
            can_get_temp = True
        elif os.name == 'nt' and self._windows_cpu_temp() is not None:
            # Windows: WMI MSAcpi_ThermalZoneTemperature (many boards expose it)
            can_get_temp = True

        if can_get_temp:
            self.all_sensors["cpu_temperature"] = {"device": "CPU", "label": "Temperature", "unit": "°C", "type": "cpu_temp", "var": tk.StringVar(), "history": [], "last_valid_reading": None}
        

        # --- Optional sensors: battery ------------------------------------
        try:
            has_battery = hasattr(psutil, 'sensors_battery') and psutil.sensors_battery() is not None
        except Exception:
            has_battery = False
        if has_battery:
            self.all_sensors["battery"] = {"device": "Power", "label": "Battery", "unit": "%", "type": "battery", "var": tk.StringVar(), "history": [], "last_valid_reading": None}

        # --- Optional sensors: NVIDIA GPU (via nvidia-smi when present) ----
        self._nvidia_smi = self._detect_nvidia_smi()
        if self._nvidia_smi:
            self.all_sensors["gpu_usage"] = {"device": "GPU", "label": "Usage", "unit": "%", "type": "gpu_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None}
            self.all_sensors["gpu_temperature"] = {"device": "GPU", "label": "Temperature", "unit": "\u00b0C", "type": "gpu_temp", "var": tk.StringVar(), "history": [], "last_valid_reading": None}
        self.ping_target = "8.8.8.8"

        # Desktop-widget mode (always visible across Win+D / virtual desktops)
        self.widget_mode_enabled = False
        self._widget_var = tk.BooleanVar(value=False)
        self.widget = WidgetPersistence(master)

        # System drive for disk metrics ('/' is unreliable on Windows)
        self.disk_root = (os.environ.get("SystemDrive", "C:") + "\\") if os.name == "nt" else "/"

        self.current_readings_for_log = {}
        self.graph_canvases = {}
        self.sensor_frames = {}
        self.frame_widget_rows = {}
        self.last_updated_text = tk.StringVar()
        
        self.last_columns = 0
        
        self.after_id = None
        
        self.net_io_last_time = time.time()
        self.net_io_last_sent = psutil.net_io_counters().bytes_sent
        self.net_io_last_recv = psutil.net_io_counters().bytes_recv

        self.ordered_devices = []
        
        self._load_settings()

        self.title_label = tk.Label(master, text="System Monitor", font=self.font_title, pady=15)
        self.title_label.pack()
        self.title_label.bind("<Button-3>", self._show_title_menu)

        self.status_label = tk.Label(master, textvariable=self.last_updated_text, font=self.font_status)
        self.status_label.pack(pady=(5, 10))

        button_frame = tk.Frame(master)
        button_frame.pack(pady=(10, 10), fill="x", padx=15)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        left_button_frame = tk.Frame(button_frame)
        left_button_frame.grid(row=0, column=0, sticky="w")
        
        self.save_log_button = tk.Button(left_button_frame, text="Save Log",
                                         command=self.save_to_log,
                                         font=self.font_button,
                                         relief="flat", bd=0, padx=10, pady=5)
        self.save_log_button.pack(side="left")

        right_button_frame = tk.Frame(button_frame)
        right_button_frame.grid(row=0, column=1, sticky="e")
        
        self.theme_button = tk.Button(right_button_frame, text="Theme",
                                      command=self._change_theme,
                                      font=self.font_button,
                                      relief="flat", bd=0, padx=10, pady=5)
        self.theme_button.pack(side="right")

        main_content_frame = tk.Frame(master)
        main_content_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main_content_frame, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.master.bind("<Configure>", self._on_window_resize)
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)
        
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)

        self._initialize_sensor_gui()
        self._apply_theme()
        self.update_sensors()

        # Restore desktop-widget mode if it was enabled last session
        if self.widget_mode_enabled:
            self.widget.enable()
        self._widget_var.set(self.widget_mode_enabled)

    def _show_title_menu(self, event):
        """Right-click menu on the title: toggle always-visible widget mode."""
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_checkbutton(label="Widget mode (always visible)",
                             variable=self._widget_var,
                             command=self._toggle_widget_mode)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _toggle_widget_mode(self):
        """Enable/disable persistence across Show Desktop and virtual desktops."""
        self.widget_mode_enabled = self.widget.toggle()
        self._widget_var.set(self.widget_mode_enabled)
        self._save_settings()
        state = "enabled" if self.widget_mode_enabled else "disabled"
        self.last_updated_text.set(f"Widget mode {state}")

    def _get_config_path(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "system-monitor")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def _save_settings(self):
        config_data = {
            "geometry": self.master.geometry(),
            "ordered_devices": self.ordered_devices,
            "current_theme_index": self.current_theme_index,
            "widget_mode": bool(getattr(self, "widget_mode_enabled", False))
        }
        try:
            with open(self._get_config_path(), "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            pass

    def _load_settings(self):
        try:
            with open(self._get_config_path(), "r") as f:
                config_data = json.load(f)
                
                if "geometry" in config_data:
                    self.master.geometry(config_data["geometry"])
                else:
                    self.master.geometry("275x800")
                
                live_devices = sorted(list(set(s['device'] for s in self.all_sensors.values())))
                if "ordered_devices" in config_data and config_data["ordered_devices"]:
                    self.ordered_devices = [d for d in config_data["ordered_devices"] if d in live_devices]
                
                if "current_theme_index" in config_data:
                    self.current_theme_index = config_data["current_theme_index"]

                if config_data.get("widget_mode"):
                    self.widget_mode_enabled = True
        except (FileNotFoundError, json.JSONDecodeError):
            self.master.geometry("275x800")
        
        if not self.ordered_devices:
            self.ordered_devices = sorted(list(set(s['device'] for s in self.all_sensors.values())))

    def _on_closing(self):
        self._save_settings()
        self.master.destroy()

    def _apply_theme(self):
        current_theme = self.themes[self.current_theme_index]
        self.bg_main = current_theme["bg_main"]
        self.fg_text_primary = current_theme["fg_text_primary"]
        self.fg_text_secondary = current_theme["fg_text_secondary"]
        self.highlight_color = current_theme["highlight_color"]
        self.accent_color = current_theme["accent_color"]
        
        self.bg_frame = self.bg_main

        self.master.configure(bg=self.bg_main)
        self.title_label.config(bg=self.bg_main, fg=self.fg_text_primary)
        self.status_label.config(bg=self.bg_main, fg=self.fg_text_secondary)
        self.canvas.configure(bg=self.bg_main)
        self.scrollable_frame.configure(bg=self.bg_main)
        
        button_frame = self.master.winfo_children()[2]
        left_button_frame = button_frame.winfo_children()[0]
        right_button_frame = button_frame.winfo_children()[1]
        
        button_frame.config(bg=self.bg_main)
        left_button_frame.config(bg=self.bg_main)
        right_button_frame.config(bg=self.bg_main)

        self.theme_button.config(bg=self.highlight_color, fg=self.button_fg, activebackground=self.highlight_color, activeforeground=self.button_fg)
        self.save_log_button.config(bg=self.accent_color, fg=self.button_fg, activebackground=self.accent_color, activeforeground=self.button_fg)
        
        for device_frame in self.sensor_frames.values():
            device_frame.config(bg=self.bg_frame, highlightbackground=self.highlight_color)
            for widget in device_frame.winfo_children():
                widget.config(bg=self.bg_frame)
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        child.config(bg=self.bg_frame)
                
        for sensor_key, sensor_data in self.all_sensors.items():
            sensor_data["color"] = self.accent_color
            if sensor_key in self.graph_canvases:
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], self.accent_color)
            
            if sensor_data['device'] in self.sensor_frames:
                device_frame = self.sensor_frames[sensor_data['device']]
                for row in range(1, self.frame_widget_rows.get(sensor_data['device'], 1)):
                    try:
                        label = device_frame.grid_slaves(row=row, column=1)[0]
                        value_label = device_frame.grid_slaves(row=row, column=2)[0]
                        unit_label = device_frame.grid_slaves(row=row, column=3)[0]
    
                        if label.cget("text").replace(":", "") == sensor_data["label"]:
                            label.config(bg=self.bg_frame, fg=self.fg_text_primary)
                            
                            if sensor_key == "cpu_temperature":
                                pass
                            else:
                                value_label.config(bg=self.bg_frame, fg=self.accent_color)
                                
                            unit_label.config(bg=self.bg_frame, fg=self.fg_text_secondary)
                            break
                    except IndexError:
                        continue
                        
    def _change_theme(self):
        self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)
        self._apply_theme()
        self._save_settings()

    def _initialize_sensor_gui(self):
        for device_name in self.ordered_devices:
            if device_name in self.sensor_frames:
                continue

            device_frame = self._create_sensor_group_frame(self.scrollable_frame, device_name)
            self.sensor_frames[device_name] = device_frame
            
            for sensor_key, sensor_data in self.all_sensors.items():
                if sensor_data['device'] == device_name:
                    self._create_sensor_widgets(device_frame, device_name, sensor_data["label"], sensor_data["var"], sensor_data["unit"], sensor_key)
        
        self._repack_frames()
    
    def _on_window_resize(self, event):
        if self.after_id:
            self.master.after_cancel(self.after_id)
        
        self.after_id = self.master.after(100, lambda: self._repack_frames(force=False))
        self._save_settings()

    def _repack_frames(self, force=False):
        width = self.master.winfo_width()
        
        min_frame_width = 240
        new_columns = max(1, int(width // min_frame_width))

        if new_columns == self.last_columns and not force:
            return

        for frame in self.scrollable_frame.winfo_children():
            frame.grid_forget()

        for i, device_name in enumerate(self.ordered_devices):
            if device_name in self.sensor_frames:
                frame = self.sensor_frames[device_name]
                row = i // new_columns
                column = i % new_columns
                frame.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")

        for i in range(new_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)
        
        self.master.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.last_columns = new_columns

    def _create_sensor_group_frame(self, parent, title_text):
        frame = tk.Frame(parent, bd=0, relief="flat", highlightthickness=1, padx=8, pady=3)
        
        header_frame = tk.Frame(frame)
        header_frame.grid(row=0, column=0, columnspan=5, sticky="ew", padx=3, pady=(3, 8))
        header_frame.columnconfigure(1, weight=1)

        up_button = tk.Button(header_frame, text="▲", font=("Segoe UI", 8), bd=0, relief="flat", command=lambda name=title_text: self._move_frame(name, -1))
        up_button.pack(side="left", padx=(0, 2))
        
        down_button = tk.Button(header_frame, text="▼", font=("Segoe UI", 8), bd=0, relief="flat", command=lambda name=title_text: self._move_frame(name, 1))
        down_button.pack(side="left", padx=(0, 5))

        group_title = tk.Label(header_frame, text=title_text, font=("Segoe UI", 10, "bold"))
        group_title.pack(side="left", fill="x", expand=True)

        self.frame_widget_rows[title_text] = 1

        frame.columnconfigure(1, weight=1, minsize=80)
        frame.columnconfigure(2, weight=0, minsize=50)
        frame.columnconfigure(3, weight=0, minsize=40)
        frame.columnconfigure(4, weight=0)

        return frame

    def _move_frame(self, device_name, direction):
        if device_name not in self.ordered_devices:
            return
            
        current_index = self.ordered_devices.index(device_name)
        new_index = current_index + direction
        
        if 0 <= new_index < len(self.ordered_devices):
            self.ordered_devices[current_index], self.ordered_devices[new_index] = self.ordered_devices[new_index], self.ordered_devices[current_index]
            self._repack_frames(force=True)
            self._save_settings()

    def _create_sensor_widgets(self, parent_frame, device_name, label_text, var, unit, sensor_key):
        row = self.frame_widget_rows.get(device_name, 1)
        self.frame_widget_rows[device_name] = row + 1
        
        if self.all_sensors[sensor_key]["type"] == "static":
            var.set(str(self.all_sensors[sensor_key]["value"]).rjust(5))

        label = tk.Label(parent_frame, text=f"{label_text}:", font=self.font_label)
        label.grid(row=row, column=1, sticky="w", padx=2, pady=3)

        value_label = tk.Label(parent_frame, textvariable=var, font=self.font_value)
        value_label.grid(row=row, column=2, sticky="e", padx=2, pady=3)
        self.all_sensors[sensor_key]["value_label_widget"] = value_label

        unit_label = tk.Label(parent_frame, text=unit, font=self.font_unit)
        unit_label.grid(row=row, column=3, sticky="w", padx=2, pady=3)

        if self.all_sensors[sensor_key]["type"] not in ["static", "uptime"]:
            graph_canvas = tk.Canvas(parent_frame, width=50, height=25, highlightthickness=0)
            graph_canvas.grid(row=row, column=4, sticky="e", padx=2, pady=3)
            graph_canvas.bind('<Configure>', lambda event, key=sensor_key: self._on_graph_resize(event, key))
            self.graph_canvases[sensor_key] = graph_canvas
        
        if self.all_sensors[sensor_key]["type"] not in ["static", "uptime"]:
            var.set("N/A".rjust(5))

    def _on_frame_configure(self, event):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
            
    def _on_graph_resize(self, event, sensor_key):
        if sensor_key in self.all_sensors and sensor_key in self.graph_canvases:
            history = self.all_sensors[sensor_key]['history']
            color = self.accent_color
            self._draw_graph(self.graph_canvases[sensor_key], history, color)

    def _draw_graph(self, canvas, history_data, color):
        canvas.delete("all")

        if len(history_data) < 2:
            return

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        min_val = min(history_data)
        max_val = max(history_data)
        range_val = max(1, max_val - min_val)

        points = []
        for i, val in enumerate(history_data):
            x = i * (width / (len(history_data) - 1))
            y = height - ((val - min_val) / range_val) * height
            points.append((x, y))

        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=1.5)

    def _get_real_readings(self):
        readings = {}
        
        readings["cpu_core_usage"] = psutil.cpu_percent(interval=None)
        
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            readings["cpu_freq"] = cpu_freq.current / 1000
        
        uptime_seconds = time.time() - psutil.boot_time()
        readings["cpu_uptime"] = str(datetime.timedelta(seconds=int(uptime_seconds)))
        
        ram_info = psutil.virtual_memory()
        readings["ram_usage"] = ram_info.percent
        readings["ram_used"] = ram_info.used / (1024**3)
        
        disk_info = psutil.disk_usage(getattr(self, "disk_root", "/" if os.name != "nt" else "C:\\"))
        readings["disk_usage"] = disk_info.percent
        readings["disk_free"] = disk_info.free / (1024**3)
        
        net_io = psutil.net_io_counters()
        current_time = time.time()
        
        if self.net_io_last_time and self.net_io_last_sent and self.net_io_last_recv:
            time_diff = current_time - self.net_io_last_time
            if time_diff > 0:
                bytes_sent_per_sec = (net_io.bytes_sent - self.net_io_last_sent) / time_diff
                bytes_recv_per_sec = (net_io.bytes_recv - self.net_io_last_recv) / time_diff
                
                readings["net_up"] = bytes_sent_per_sec / (1024 * 1024)
                readings["net_down"] = bytes_recv_per_sec / (1024 * 1024)
        
        self.net_io_last_time = current_time
        self.net_io_last_sent = net_io.bytes_sent
        self.net_io_last_recv = net_io.bytes_recv

        try:
            latency = ping3.ping(self.ping_target, unit="ms", timeout=1)
            if isinstance(latency, float):
                readings["ping_latency"] = latency
            else:
                readings["ping_latency"] = None
        except Exception:
            readings["ping_latency"] = None
        
        temp_found = False
        if hasattr(psutil, 'sensors_temperatures'):
            temperatures = psutil.sensors_temperatures()
            cpu_temps = []
            
            for sensor_name, sensor_list in temperatures.items():
                if "cpu" in sensor_name.lower() or "core" in sensor_name.lower():
                    total_temp = sum([t.current for t in sensor_list])
                    if sensor_list:
                        cpu_temps.append(total_temp / len(sensor_list))
                elif not cpu_temps and sensor_list:
                    cpu_temps.append(sensor_list[0].current)

            if cpu_temps:
                readings["cpu_temperature"] = sum(cpu_temps) / len(cpu_temps)
                temp_found = True
        
        if not temp_found and os.name == 'posix':
            temp_paths = glob.glob('/sys/class/thermal/thermal_zone*/temp') + glob.glob('/sys/class/hwmon/hwmon*/temp*_input')
            for path in temp_paths:
                try:
                    with open(path, 'r') as f:
                        temp_raw = int(f.read().strip())
                        readings["cpu_temperature"] = temp_raw / 1000.0
                        temp_found = True
                        break
                except (IOError, ValueError):
                    continue

        # Windows fallback: WMI thermal zone (best-effort; needs board support)
        if not temp_found and os.name == 'nt':
            wmi_temp = self._windows_cpu_temp()
            if wmi_temp is not None:
                readings["cpu_temperature"] = wmi_temp
                temp_found = True

        # GPU metrics via nvidia-smi when available (usage % + temperature)
        if getattr(self, "_nvidia_smi", None):
            try:
                out = subprocess.run(
                    [self._nvidia_smi, "--query-gpu=utilization.gpu,temperature.gpu",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=2)
                if out.returncode == 0 and out.stdout.strip():
                    parts = out.stdout.strip().splitlines()[0].split(",")
                    if len(parts) >= 2:
                        readings["gpu_usage"] = float(parts[0])
                        readings["gpu_temperature"] = float(parts[1])
            except Exception:
                pass

        # Battery percentage (laptops)
        try:
            bat = psutil.sensors_battery() if hasattr(psutil, 'sensors_battery') else None
            if bat is not None:
                readings["battery"] = round(float(bat.percent), 1)
        except Exception:
            pass

        if not temp_found and "cpu_temperature" in self.all_sensors:
            readings["cpu_temperature"] = None

        return readings

    def _detect_nvidia_smi(self):
        """Return the nvidia-smi executable path if a query succeeds, else None."""
        try:
            import shutil
            smi = shutil.which("nvidia-smi")
            if not smi:
                return None
            out = subprocess.run(
                [smi, "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=3)
            if out.returncode == 0 and out.stdout.strip():
                return smi
        except Exception:
            pass
        return None

    def _windows_cpu_temp(self):
        """Best-effort CPU temperature on Windows via WMI MSAcpi_ThermalZoneTemperature.

        Returns degrees Celsius or None. The optional `wmi` package
        (pip install wmi) plus admin rights / board support are required.
        """
        if getattr(self, "_no_wmi_temp", False):
            return None
        try:
            import wmi  # optional dependency
        except ImportError:
            self._no_wmi_temp = True
            return None
        try:
            w = getattr(self, "_wmi_conn", None)
            if w is None:
                w = wmi.WMI(namespace="root\\wmi")
                self._wmi_conn = w
            zones = w.MSAcpi_ThermalZoneTemperature()
            temps = [float(z.CurrentTemperature) / 10.0 - 273.15
                     for z in zones if z.CurrentTemperature]
            if temps:
                return sum(temps) / len(temps)
        except Exception:
            self._no_wmi_temp = True   # don't retry-spam every cycle
        return None

    def update_sensors(self):
        current_time = time.strftime("%H:%M:%S")
        self.current_readings_for_log = {}
        
        real_readings = self._get_real_readings()

        for sensor_key, sensor_data in self.all_sensors.items():
            
            current_val = real_readings.get(sensor_key)
            
            if sensor_data["type"] == "static":
                self.current_readings_for_log[sensor_key] = {"value": sensor_data["var"].get().strip(), "unit": sensor_data["unit"]}
                continue
            
            if current_val is not None:
                sensor_data["last_valid_reading"] = current_val
                
                if sensor_key == "cpu_temperature":
                    if current_val < 50:
                        color = "#66BB6A"
                    elif 50 <= current_val < 70:
                        color = "#FFA726"
                    else:
                        color = "#EF5350"
                    if "value_label_widget" in sensor_data:
                        sensor_data["value_label_widget"].config(fg=color)
                else:
                    if "value_label_widget" in sensor_data:
                        sensor_data["value_label_widget"].config(fg=self.accent_color)
                
                if isinstance(current_val, float):
                    if sensor_key == "ping_latency":
                        formatted_value = f"{current_val:5.2f}"
                    elif sensor_key in ["net_up", "net_down", "cpu_freq", "ram_used", "disk_free"]:
                        formatted_value = f"{current_val:5.2f}"
                    else:
                        formatted_value = f"{current_val:5.1f}"
                elif sensor_data["type"] == "uptime":
                    formatted_value = current_val
                else:
                    formatted_value = f"{current_val:5d}"
                
                sensor_data["var"].set(formatted_value)
                
                if sensor_data["type"] not in ["static", "uptime"]:
                    sensor_data["history"].append(round(current_val, 1))
                    if len(sensor_data["history"]) > 20:
                        sensor_data["history"].pop(0)

                self.current_readings_for_log[sensor_key] = {"value": formatted_value, "unit": sensor_data["unit"]}
            else:
                formatted_value = "N/A".rjust(5)
                sensor_data["var"].set(formatted_value)
                
                if sensor_data["type"] not in ["static", "uptime"]:
                    sensor_data["history"].append(0)
                    if len(sensor_data["history"]) > 20:
                        sensor_data["history"].pop(0)
                        
            if sensor_key in self.graph_canvases:
                graph_color = self.accent_color
                if sensor_key in ("cpu_temperature", "gpu_temperature"):
                    if current_val is not None:
                        if current_val < 50:
                            graph_color = "#66BB6A"
                        elif 50 <= current_val < 70:
                            graph_color = "#FFA726"
                        else:
                            graph_color = "#EF5350"
                
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], graph_color)

        self.last_updated_text.set(f"Last Updated: {current_time}")
        self.master.after(2000, self.update_sensors)

    def save_to_log(self):
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(documents_path, exist_ok=True)
        file_name = f"System_Monitor_Log_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(documents_path, file_name)

        try:
            with open(file_path, "a") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"--- Log Entry: {timestamp} ---\n")
                
                device_sensors = {device: [] for device in self.ordered_devices}
                for sensor_key, sensor_data in self.all_sensors.items():
                    device_sensors[sensor_data['device']].append(sensor_key)

                for device_name in self.ordered_devices:
                    f.write(f"\n[{device_name}]\n")
                    for sensor_key in device_sensors[device_name]:
                        if sensor_key in self.all_sensors:
                            sensor_data = self.all_sensors[sensor_key]
                            
                            value = sensor_data["var"].get()
                                
                            f.write(f"  {sensor_data['label']}: {value.strip()}{sensor_data['unit']}\n")
                f.write("\n")
            
            self._show_message("Log Saved", f"Current readings appended to:\n{file_path}")

        except Exception as e:
            self._show_message("Error", f"Failed to save log: {e}")

    def _show_message(self, title, message):
        top = tk.Toplevel(self.master)
        top.title(title)
        top.geometry("350x150")
        top.resizable(False, False)
        top.grab_set()

        if os.path.exists(self.icon_path):
            try:
                top.iconbitmap(self.icon_path)
            except tk.TclError:
                pass

        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        top_width = 350
        top_height = 150
        
        top_x = master_x + (master_width // 2) - (top_width // 2)
        top_y = master_y + (master_height // 2) - (top_height // 2)
        top.geometry(f"+{top_x}+{top_y}")

        top.configure(bg=self.bg_frame)

        tk.Label(top, text=title, font=self.font_message_title, bg=self.bg_frame, fg=self.fg_text_primary, pady=10).pack()
        tk.Label(top, text=message, font=self.font_message_text, bg=self.bg_frame, fg=self.fg_text_secondary, wraplength=300).pack(pady=(0, 20))
        tk.Button(top, text="OK", command=top.destroy, font=self.font_button, bg=self.highlight_color, fg=self.button_fg, relief="flat", bd=0, padx=10, pady=5).pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorTrackerApp(root)
    root.mainloop()