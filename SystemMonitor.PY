import tkinter as tk
from tkinter import messagebox
import random
import time
import datetime
import os
import json

class SensorTrackerApp:
    def __init__(self, master):
        """
        Initializes the Sensor Tracker Application GUI.

        Args:
            master: The root Tkinter window.
        """
        self.master = master
        master.title("System Monitor - FrenzyPenguin Media")
        master.resizable(True, True)

        # --- ICON LOADING ---
        # Robustly tries to load the icon.ico file without crashing if it's not found.
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        self.icon_path = icon_path # Store for use in Toplevel windows
        if os.path.exists(icon_path):
            try:
                master.iconbitmap(icon_path)
            except tk.TclError:
                print("Warning: Could not load the icon.ico file.")
        
        # --- THEME AND FONT CONFIGURATION ---
        # Define multiple color themes as dictionaries
        self.themes = [
            # Default Dark Theme
            {
                "bg_main": "#263238",
                "bg_frame": "#37474F",
                "fg_text_primary": "#ECEFF1",
                "fg_text_secondary": "#B0BEC5",
                "highlight_color": "#607D8B",
                "accent_color": "#66BB6A",
            },
            # Blue Dusk Theme
            {
                "bg_main": "#122026",
                "bg_frame": "#1F313B",
                "fg_text_primary": "#C8D9E0",
                "fg_text_secondary": "#8FA5B2",
                "highlight_color": "#4A687D",
                "accent_color": "#42A5F5",
            },
            # Crimson Twilight Theme
            {
                "bg_main": "#261214",
                "bg_frame": "#3B1F20",
                "fg_text_primary": "#E0C8C8",
                "fg_text_secondary": "#B28F8F",
                "highlight_color": "#7D4A4B",
                "accent_color": "#F54242",
            },
            # Forest Theme
            {
                "bg_main": "#1A2E2A",
                "bg_frame": "#26413A",
                "fg_text_primary": "#D5E8D1",
                "fg_text_secondary": "#9BB295",
                "highlight_color": "#4E665F",
                "accent_color": "#5A9E66",
            },
            # Sunset Theme
            {
                "bg_main": "#3D1A25",
                "bg_frame": "#5A2A38",
                "fg_text_primary": "#F7D1BA",
                "fg_text_secondary": "#C78D8D",
                "highlight_color": "#8C4E61",
                "accent_color": "#F38562",
            },
        ]
        
        self.current_theme_index = 0
        self.bg_main = ""
        self.bg_frame = ""
        self.fg_text_primary = ""
        self.fg_text_secondary = ""
        self.highlight_color = ""
        self.accent_color = ""
        self.button_fg = "#FFFFFF" # This color remains constant for readability

        # Font definitions
        self.font_title = ("Segoe UI", 18, "bold")
        self.font_label = ("Segoe UI", 11)
        self.font_value = ("Segoe UI", 16, "bold")
        self.font_unit = ("Segoe UI", 11)
        self.font_status = ("Segoe UI", 8, "italic")
        self.font_button = ("Segoe UI", 10, "bold")
        self.font_message_title = ("Segoe UI", 12, "bold")
        self.font_message_text = ("Segoe UI", 10)
        
        # Define colors for dynamic temperature changes
        self.stable_color = "#33A368"  # A nice green for stability
        self.rising_color = "#FF4B3E"  # A striking red for rising temp
        self.falling_color = "#4287F5" # A cool blue for falling temp
        self.temp_change_threshold = 2.0 # Threshold for a "big" change

        # --- SENSOR DATA VARIABLES ---
        self.all_sensors = {
            "environmental_temp": {"device": "Environmental", "label": "Temp", "unit": "°C", "type": "temperature", "var": tk.StringVar(), "history": [], "last_celsius_reading": None, "last_valid_reading": None},
            "environmental_humidity": {"device": "Environmental", "label": "Humidity", "unit": "%", "type": "humidity", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "cpu_die_temp": {"device": "CPU", "label": "Die Temp", "unit": "°C", "type": "cpu_temp", "var": tk.StringVar(), "history": [], "last_celsius_reading": None, "last_valid_reading": None},
            "cpu_core_usage": {"device": "CPU", "label": "Core Usage", "unit": "%", "type": "cpu_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "fan_speed": {"device": "CPU", "label": "Fans", "unit": "RPM", "type": "fan_speed", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "gpu1_temp": {"device": "GPU 1", "label": "Temp", "unit": "°C", "type": "gpu_temp", "var": tk.StringVar(), "history": [], "last_celsius_reading": None, "last_valid_reading": None},
            "gpu1_usage": {"device": "GPU 1", "label": "Usage", "unit": "%", "type": "gpu_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "gpu2_temp": {"device": "GPU 2", "label": "Temp", "unit": "°C", "type": "gpu_temp", "var": tk.StringVar(), "history": [], "last_celsius_reading": None, "last_valid_reading": None},
            "gpu2_usage": {"device": "GPU 2", "label": "Usage", "unit": "%", "type": "gpu_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "network_usage": {"device": "Network", "label": "Usage", "unit": "%", "type": "network_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "disk_temp": {"device": "Storage", "label": "Temp", "unit": "°C", "type": "disk_temp", "var": tk.StringVar(), "history": [], "last_celsius_reading": None, "last_valid_reading": None},
            "pci_temp": {"device": "PCIe Bus", "label": "Temp", "unit": "°C", "type": "pci_temp", "var": tk.StringVar(), "history": [], "last_celsius_reading": None, "last_valid_reading": None},
            "ram_usage": {"device": "Memory", "label": "Usage", "unit": "%", "type": "ram_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "disk_io_read": {"device": "Storage", "label": "Read", "unit": "MB/s", "type": "disk_io_read", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "disk_io_write": {"device": "Storage", "label": "Write", "unit": "MB/s", "type": "disk_io_write", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
            "network_ping": {"device": "Network", "label": "Ping", "unit": "ms", "type": "network_ping", "var": tk.StringVar(), "history": [], "last_valid_reading": None},
        }

        # Dictionaries to track sensor state and GUI elements
        self.current_readings_for_log = {}
        self.graph_canvases = {}
        self.sensor_frames = {}
        self.frame_widget_rows = {}
        self.last_updated_text = tk.StringVar()
        self.temp_unit = "C"

        # List stores the user's preferred order of device names
        self.ordered_devices = []
        
        # New variable to track the current number of columns for stable redrawing
        self.last_columns = 0
        
        self.after_id = None

        # --- Load settings on startup ---
        self._load_settings()

        # --- GUI Elements ---
        self.title_label = tk.Label(master, text="System Monitor", font=self.font_title, pady=15)
        self.title_label.pack()

        self.status_label = tk.Label(master, textvariable=self.last_updated_text, font=self.font_status)
        self.status_label.pack(pady=(5, 10))

        # Container frame for the buttons
        button_frame = tk.Frame(master)
        button_frame.pack(pady=(10, 10), fill="x", padx=15)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Left-aligned buttons
        left_button_frame = tk.Frame(button_frame)
        left_button_frame.grid(row=0, column=0, sticky="w")
        
        self.unit_button = tk.Button(left_button_frame, text=f"Switch to °{'F' if self.temp_unit == 'C' else 'C'}",
                                     command=self._toggle_temp_unit,
                                     font=self.font_button,
                                     relief="flat", bd=0, padx=10, pady=5)
        self.unit_button.pack(side="left", padx=(0, 10))
        
        self.save_log_button = tk.Button(left_button_frame, text="Save Log",
                                         command=self.save_to_log,
                                         font=self.font_button,
                                         relief="flat", bd=0, padx=10, pady=5)
        self.save_log_button.pack(side="left")

        # Right-aligned button
        right_button_frame = tk.Frame(button_frame)
        right_button_frame.grid(row=0, column=1, sticky="e")
        
        self.theme_button = tk.Button(right_button_frame, text="Theme",
                                      command=self._change_theme,
                                      font=self.font_button,
                                      relief="flat", bd=0, padx=10, pady=5)
        self.theme_button.pack(side="right")

        # Create a frame to hold the canvas and scrollable content
        main_content_frame = tk.Frame(master)
        main_content_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main_content_frame, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind the main window's configure event to handle resizing and the close event to save settings
        self.master.bind("<Configure>", self._on_window_resize)
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Bind mousewheel events for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)
        
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)

        self._initialize_sensor_gui()
        self._apply_theme() # Apply initial theme after creating widgets
        self.update_sensors()

    def _get_config_path(self):
        """Returns the path to the configuration file."""
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "system-monitor")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def _save_settings(self):
        """Saves the current application settings to a JSON file."""
        config_data = {
            "geometry": self.master.geometry(),
            "temp_unit": self.temp_unit,
            "ordered_devices": self.ordered_devices,
            "current_theme_index": self.current_theme_index
        }
        try:
            with open(self._get_config_path(), "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _load_settings(self):
        """Loads application settings from a JSON file."""
        try:
            with open(self._get_config_path(), "r") as f:
                config_data = json.load(f)
                
                # Apply geometry
                if "geometry" in config_data:
                    self.master.geometry(config_data["geometry"])
                else:
                    self.master.geometry("275x800")
                
                # Apply temperature unit
                if "temp_unit" in config_data:
                    self.temp_unit = config_data["temp_unit"]
                
                # Apply device order
                if "ordered_devices" in config_data and config_data["ordered_devices"]:
                    self.ordered_devices = config_data["ordered_devices"]
                
                # Apply theme index
                if "current_theme_index" in config_data:
                    self.current_theme_index = config_data["current_theme_index"]
        except (FileNotFoundError, json.JSONDecodeError):
            self.master.geometry("275x800")
            print("No config file found or file is invalid. Using default settings.")
        
        # We need a default order if none was loaded
        if not self.ordered_devices:
            devices = sorted(list(set(s['device'] for s in self.all_sensors.values())))
            
            # Prioritize Network and Environmental devices at the top
            self.ordered_devices = [d for d in ["Network", "Environmental"] if d in devices]
            remaining_devices = [d for d in devices if d not in self.ordered_devices]
            self.ordered_devices.extend(remaining_devices)

    def _on_closing(self):
        """Saves settings and then closes the window."""
        self._save_settings()
        self.master.destroy()

    def _apply_theme(self):
        """Applies the colors from the current theme to all widgets."""
        current_theme = self.themes[self.current_theme_index]
        self.bg_main = current_theme["bg_main"]
        self.bg_frame = current_theme["bg_frame"]
        self.fg_text_primary = current_theme["fg_text_primary"]
        self.fg_text_secondary = current_theme["fg_text_secondary"]
        self.highlight_color = current_theme["highlight_color"]
        self.accent_color = current_theme["accent_color"]

        # Update root and main labels
        self.master.configure(bg=self.bg_main)
        self.title_label.config(bg=self.bg_main, fg=self.fg_text_primary)
        self.status_label.config(bg=self.bg_main, fg=self.fg_text_secondary)
        self.canvas.configure(bg=self.bg_main)
        
        # Update button container frames
        self.master.winfo_children()[2].config(bg=self.bg_main) # main button frame
        self.master.winfo_children()[2].winfo_children()[0].config(bg=self.bg_main) # left button frame
        self.master.winfo_children()[2].winfo_children()[1].config(bg=self.bg_main) # right button frame

        # Update buttons
        self.theme_button.config(bg=self.highlight_color, fg=self.button_fg, activebackground=self.highlight_color, activeforeground=self.button_fg)
        self.unit_button.config(bg=self.highlight_color, fg=self.button_fg, activebackground=self.highlight_color, activeforeground=self.button_fg)
        self.save_log_button.config(bg=self.accent_color, fg=self.button_fg, activebackground=self.accent_color, activeforeground=self.button_fg)

        # Update all sensor frames and their children
        for device_frame in self.sensor_frames.values():
            device_frame.config(bg=self.bg_frame, highlightbackground=self.highlight_color)
            for widget in device_frame.winfo_children():
                widget.config(bg=self.bg_frame)
                if isinstance(widget, tk.Frame): # For the header frame
                    for child in widget.winfo_children():
                        child.config(bg=self.bg_frame)
                
        # Re-apply theme to sensor widgets (labels and graphs)
        for sensor_key, sensor_data in self.all_sensors.items():
            # Update the graph and value color
            sensor_data["color"] = self.accent_color
            if sensor_key in self.graph_canvases:
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], self.accent_color)
                
            # Find the value label and update its foreground color
            device_frame = self.sensor_frames[sensor_data['device']]
            children = device_frame.winfo_children()
            # Iterate through children to find the correct value label
            for row in range(1, self.frame_widget_rows[sensor_data['device']]):
                label = device_frame.grid_slaves(row=row, column=1)[0]
                value_label = device_frame.grid_slaves(row=row, column=2)[0]
                unit_label = device_frame.grid_slaves(row=row, column=3)[0]

                if label.cget("text").replace(":", "") == sensor_data["label"]:
                    label.config(bg=self.bg_frame, fg=self.fg_text_primary)
                    # Non-temperature values get the accent color, temperature values are handled by update_sensors()
                    if sensor_data['type'] not in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                        value_label.config(bg=self.bg_frame, fg=self.accent_color)
                    else:
                        # Ensure temperature labels have the theme's accent color initially
                        value_label.config(bg=self.bg_frame, fg=self.accent_color)
                    unit_label.config(bg=self.bg_frame, fg=self.fg_text_secondary)
                    break
                    
    def _change_theme(self):
        """Cycles to the next theme in the list and applies it."""
        self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)
        self._apply_theme()
        self._save_settings()

    def _initialize_sensor_gui(self):
        """Initializes all sensor group frames and widgets at startup."""
        for device_name in self.ordered_devices:
            device_frame = self._create_sensor_group_frame(self.scrollable_frame, device_name)
            self.sensor_frames[device_name] = device_frame
            
            for sensor_key, sensor_data in self.all_sensors.items():
                if sensor_data['device'] == device_name:
                    self._create_sensor_widgets(device_frame, device_name, sensor_data["label"], sensor_data["var"], sensor_data["unit"], sensor_key)
        
        self._repack_frames()
    
    def _on_window_resize(self, event):
        """Handles window resize event with a debounce to prevent excessive updates."""
        if self.after_id:
            self.master.after_cancel(self.after_id)
        
        self.after_id = self.master.after(100, lambda: self._repack_frames(force=False))
        self._save_settings()

    def _repack_frames(self, force=False):
        """Dynamically re-layouts frames based on window width and the user's reordering."""
        width = self.master.winfo_width()
        
        min_frame_width = 240
        new_columns = max(1, int(width // min_frame_width))

        if new_columns == self.last_columns and not force:
            return

        for frame in self.scrollable_frame.winfo_children():
            frame.grid_forget()

        for i, device_name in enumerate(self.ordered_devices):
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
        """Helper to create a consistent sensor group frame with a title and content that expands."""
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
        """Moves a given frame up or down in the ordered list."""
        current_index = self.ordered_devices.index(device_name)
        new_index = current_index + direction
        
        if 0 <= new_index < len(self.ordered_devices):
            self.ordered_devices[current_index], self.ordered_devices[new_index] = self.ordered_devices[new_index], self.ordered_devices[current_index]
            self._repack_frames(force=True)
            self._save_settings()

    def _create_sensor_widgets(self, parent_frame, device_name, label_text, var, unit, sensor_key):
        """Helper to create sensor labels, values, and a mini-graph within a frame."""
        row = self.frame_widget_rows[device_name]
        self.frame_widget_rows[device_name] += 1

        label = tk.Label(parent_frame, text=f"{label_text}:", font=self.font_label)
        label.grid(row=row, column=1, sticky="w", padx=2, pady=3)

        value_label = tk.Label(parent_frame, textvariable=var, font=self.font_value)
        value_label.grid(row=row, column=2, sticky="e", padx=2, pady=3)
        # Store a direct reference to the value label widget for dynamic coloring
        self.all_sensors[sensor_key]["value_label_widget"] = value_label

        # Store a reference to the unit label for dynamic updates
        if not hasattr(self.sensor_frames[device_name], 'unit_labels'):
            self.sensor_frames[device_name].unit_labels = {}

        unit_label = tk.Label(parent_frame, text=unit, font=self.font_unit)
        unit_label.grid(row=row, column=3, sticky="w", padx=2, pady=3)
        self.sensor_frames[device_name].unit_labels[sensor_key] = unit_label

        graph_canvas = tk.Canvas(parent_frame, width=50, height=25, highlightthickness=0)
        graph_canvas.grid(row=row, column=4, sticky="e", padx=2, pady=3)
        graph_canvas.bind('<Configure>', lambda event, key=sensor_key: self._on_graph_resize(event, key))

        self.graph_canvases[sensor_key] = graph_canvas
        
        # Initialize the StringVar with "N/A"
        var.set("N/A".rjust(5))

    def _on_frame_configure(self, event):
        """Update the scrollregion of the canvas when the inner frame's size changes."""
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for Windows/macOS."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_linux(self, event):
        """Handle mouse wheel scrolling for Linux."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
            
    def _on_graph_resize(self, event, sensor_key):
        """Recalculates and redraws the graph when the canvas is resized."""
        if sensor_key in self.all_sensors and sensor_key in self.graph_canvases:
            history = self.all_sensors[sensor_key]['history']
            color = self.accent_color
            self._draw_graph(self.graph_canvases[sensor_key], history, color)

    def _refactored_get_reading(self, sensor_type):
        """
        Simulates a sensor reading based on type using a more concise structure.
        Randomly returns None to simulate a missed reading.
        """
        # A dictionary mapping sensor types to their min/max values
        ranges = {
            "temperature": (20.0, 30.0),
            "humidity": (40.0, 70.0),
            "cpu_temp": (40.0, 75.0),
            "cpu_usage": (5.0, 95.0),
            "gpu_temp": (45.0, 80.0),
            "gpu_usage": (0.0, 100.0),
            "network_usage": (0.0, 100.0),
            "disk_temp": (30.0, 60.0),
            "pci_temp": (35.0, 70.0),
            "ram_usage": (20.0, 95.0),
            "disk_io_read": (0.0, 500.0),
            "disk_io_write": (0.0, 300.0),
        }
        
        # 10% chance of returning None to simulate a sensor reading failure
        if random.random() < 0.10:
            return None

        if sensor_type in ranges:
            min_val, max_val = ranges[sensor_type]
            return round(random.uniform(min_val, max_val), 1)
        elif sensor_type == "network_ping":
            return random.randint(10, 150)
        elif sensor_type == "fan_speed":
            return random.randint(800, 4000)
        return None

    def _draw_graph(self, canvas, history_data, color):
        """
        Draws a simple line graph on the given canvas, handling empty data gracefully.
        """
        canvas.delete("all")

        if len(history_data) < 2:
            return

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        min_val = min(history_data)
        max_val = max(history_data)
        range_val = max(1, max_val - min_val) # Avoid division by zero

        points = []
        for i, val in enumerate(history_data):
            x = i * (width / (len(history_data) - 1))
            y = height - ((val - min_val) / range_val) * height
            points.append((x, y))

        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=1.5)

    def _toggle_temp_unit(self):
        """Toggles the temperature unit between Celsius and Fahrenheit."""
        is_f_to_c = self.temp_unit == "F"
        self.temp_unit = "C" if is_f_to_c else "F"
        new_unit_text = "°C" if is_f_to_c else "°F"
        
        self.unit_button.config(text=f"Switch to °{'F' if self.temp_unit == 'C' else 'C'}")

        # Update all temperature-related sensor values and unit labels
        for sensor_key, sensor_data in self.all_sensors.items():
            if sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                # Convert the history data
                sensor_data["history"] = [(v - 32) * 5/9 if is_f_to_c else (v * 9/5) + 32 for v in sensor_data["history"]]
                sensor_data["history"] = [round(v, 1) for v in sensor_data["history"]]
                
                # Convert the last valid reading if it exists
                if sensor_data["last_valid_reading"] is not None:
                    last_val = sensor_data["last_valid_reading"]
                    converted_val = (last_val - 32) * 5/9 if is_f_to_c else (last_val * 9/5) + 32
                    sensor_data["last_valid_reading"] = round(converted_val, 1)
                    
                # Update the displayed value
                current_val_str = sensor_data["var"].get()
                if current_val_str.strip().upper() != "N/A":
                    current_val = float(current_val_str)
                    converted_val = (current_val - 32) * 5/9 if is_f_to_c else (current_val * 9/5) + 32
                    formatted_value = f"{converted_val:5.1f}"
                    sensor_data["var"].set(formatted_value)
                
                # Update the unit label on the GUI
                for frame in self.sensor_frames.values():
                    if hasattr(frame, 'unit_labels') and sensor_key in frame.unit_labels:
                        frame.unit_labels[sensor_key].config(text=new_unit_text)
                
                # Redraw the graph to reflect the new values
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], self.accent_color)
        
        self._save_settings()

    def update_sensors(self):
        """
        Updates the sensor data dynamically and schedules the next update.
        """
        current_time = time.strftime("%H:%M:%S")
        self.current_readings_for_log = {}

        for sensor_key, sensor_data in self.all_sensors.items():
            current_val_c = self._refactored_get_reading(sensor_data["type"])
            
            if current_val_c is not None:
                # Valid reading received, update everything
                sensor_data["last_valid_reading"] = current_val_c
                
                display_val = current_val_c
                unit = sensor_data['unit']
                
                # Check for temperature and apply dynamic coloring
                if sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                    fg_color = self.accent_color # Default to theme accent color
                    if sensor_data["last_celsius_reading"] is not None:
                        temp_diff = current_val_c - sensor_data["last_celsius_reading"]
                        if temp_diff > self.temp_change_threshold:
                            fg_color = self.rising_color
                        elif temp_diff < -self.temp_change_threshold:
                            fg_color = self.falling_color
                        else:
                            fg_color = self.stable_color
                    
                    # Update the color of the value label
                    sensor_data["value_label_widget"].config(fg=fg_color)
                    
                    # Update the last reading for the next check
                    sensor_data["last_celsius_reading"] = current_val_c
                    
                    if self.temp_unit == "F":
                        display_val = (current_val_c * 9/5) + 32
                        unit = "°F"
                else:
                    # For non-temperature sensors, just use the current theme accent color
                    sensor_data["value_label_widget"].config(fg=self.accent_color)

                # Use f-string formatting to pad numbers to 5 characters with one decimal place
                if isinstance(display_val, float):
                    formatted_value = f"{display_val:5.1f}"
                else:
                    formatted_value = f"{display_val:5d}"
                
                sensor_data["var"].set(formatted_value)
                sensor_data["history"].append(round(display_val, 1))

                if len(sensor_data["history"]) > 20:
                    sensor_data["history"].pop(0)

                self.current_readings_for_log[sensor_key] = {"value": formatted_value, "unit": unit}
            else:
                # Reading is None, display last known reading or "N/A"
                if sensor_data["last_valid_reading"] is not None:
                    display_val = sensor_data["last_valid_reading"]
                    unit = sensor_data['unit']
                    
                    if self.temp_unit == "F" and sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                        display_val = (display_val * 9/5) + 32
                        unit = "°F"
                    
                    if isinstance(display_val, float):
                        formatted_value = f"{display_val:5.1f}"
                    else:
                        formatted_value = f"{display_val:5d}"
                    sensor_data["var"].set(formatted_value)
                else:
                    # If there's no last valid reading, display N/A
                    formatted_value = "N/A".rjust(5)
                    sensor_data["var"].set(formatted_value)
                    
            if sensor_key in self.graph_canvases:
                # The graph always uses the theme's accent color, and only draws if history has data
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], self.accent_color)

        self.last_updated_text.set(f"Last Updated: {current_time}")
        self.master.after(2000, self.update_sensors)

    def save_to_log(self):
        """
        Saves the current sensor readings to a text log file.
        """
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(documents_path, exist_ok=True)
        file_name = f"System_Monitor_Log_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(documents_path, file_name)

        try:
            with open(file_path, "a") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"--- Log Entry: {timestamp} ---\n")
                
                # Group sensors by device to maintain the correct order
                device_sensors = {device: [] for device in self.ordered_devices}
                for sensor_key, sensor_data in self.all_sensors.items():
                    device_sensors[sensor_data['device']].append(sensor_key)

                # Write the log file with the correct device and sensor order
                for device_name in self.ordered_devices:
                    f.write(f"\n[{device_name}]\n")
                    for sensor_key in device_sensors[device_name]:
                        sensor_data = self.all_sensors[sensor_key]
                        
                        # Get the value directly from the StringVar
                        value = sensor_data["var"].get()
                        
                        # Determine the correct unit, handling temperature unit changes
                        unit = sensor_data["unit"]
                        if self.temp_unit == "F" and sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                            unit = "°F"
                            
                        f.write(f"  {sensor_data['label']}: {value.strip()}{unit}\n")
                f.write("\n")
            
            self._show_message("Log Saved", f"Current readings appended to:\n{file_path}")

        except Exception as e:
            self._show_message("Error", f"Failed to save log: {e}")

    def _show_message(self, title, message):
        """Displays a custom messagebox that fits the app's theme."""
        top = tk.Toplevel(self.master)
        top.title(title)
        top.geometry("350x150")
        top.resizable(False, False)
        top.grab_set()

        # Set the icon for the Toplevel window
        if os.path.exists(self.icon_path):
            try:
                top.iconbitmap(self.icon_path)
            except tk.TclError:
                pass

        # Center the Toplevel window on the main window
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        top_width = 350
        top_height = 150
        
        top_x = master_x + (master_width // 2) - (top_width // 2)
        top_y = master_y + (master_height // 2) - (top_height // 2)
        top.geometry(f"+{top_x}+{top_y}")

        # Apply theme colors to the messagebox
        top.configure(bg=self.bg_frame)

        tk.Label(top, text=title, font=self.font_message_title, bg=self.bg_frame, fg=self.fg_text_primary, pady=10).pack()
        tk.Label(top, text=message, font=self.font_message_text, bg=self.bg_frame, fg=self.fg_text_secondary, wraplength=300).pack(pady=(0, 20))
        tk.Button(top, text="OK", command=top.destroy, font=self.font_button, bg=self.highlight_color, fg=self.button_fg, relief="flat", bd=0, padx=10, pady=5).pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorTrackerApp(root)
    root.mainloop()
