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
        # Checks for an 'icon.ico' file in the same directory and sets it as the window icon.
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        print(f"Checking for icon file at: {icon_path}")
        if os.path.exists(icon_path):
            try:
                master.iconbitmap(icon_path)
            except tk.TclError:
                # This handles cases where the platform doesn't support .ico,
                # or if the file is invalid.
                print("Warning: Could not load the icon.ico file.")

        # Set a modern background color for the main window
        self.bg_main = "#263238"
        self.bg_frame = "#37474F"
        self.fg_text_primary = "#ECEFF1"
        self.fg_text_secondary = "#B0BEC5"
        self.highlight_color = "#607D8B"
        self.button_bg = "#66BB6A"
        self.button_fg = "#FFFFFF"

        master.configure(bg=self.bg_main)

        # Configure attractive, smaller fonts for a compact overview
        self.font_title = ("Segoe UI", 18, "bold")
        self.font_label = ("Segoe UI", 11)
        self.font_value = ("Segoe UI", 16, "bold")
        self.font_unit = ("Segoe UI", 11)
        self.font_status = ("Segoe UI", 8, "italic")
        self.font_button = ("Segoe UI", 10, "bold")

        # --- Sensor Data Variables ---
        self.all_sensors = {}
        self.ordered_devices = []
        
        self.current_readings_for_log = {}
        self.graph_canvases = {}
        self.sensor_frames = {}
        self.frame_widget_rows = {}
        self.last_updated_text = tk.StringVar()
        self.temp_unit = "C"
        
        self.last_columns = 0
        self.after_id = None

        # --- Load settings and initialize GUI on startup ---
        self._load_settings()
        self._initialize_sensor_gui()
        self.update_sensors()
        
        # --- GUI Elements ---
        self.title_label = tk.Label(master, text="System Monitor", font=self.font_title, fg=self.fg_text_primary, bg=self.bg_main, pady=15)
        self.title_label.pack()

        self.status_label = tk.Label(master, textvariable=self.last_updated_text, font=self.font_status, fg=self.fg_text_secondary, bg=self.bg_main)
        self.status_label.pack(pady=(5, 10))

        # Container frame for the buttons
        button_frame = tk.Frame(master, bg=self.bg_main)
        button_frame.pack(pady=(10, 10))

        self.unit_button = tk.Button(button_frame, text="Switch to °F" if self.temp_unit == "C" else "Switch to °C",
                                     command=self._toggle_temp_unit,
                                     font=self.font_button,
                                     bg=self.highlight_color, fg=self.button_fg,
                                     activebackground=self.highlight_color, activeforeground=self.button_fg,
                                     relief="flat", bd=0, padx=10, pady=5)
        self.unit_button.pack(side="left", padx=(0, 10))
        
        self.save_log_button = tk.Button(button_frame, text="Save to Log",
                                         command=self.save_to_log,
                                         font=self.font_button,
                                         bg=self.button_bg, fg=self.button_fg,
                                         activebackground=self.button_bg, activeforeground=self.button_fg,
                                         relief="flat", bd=0, padx=10, pady=5)
        self.save_log_button.pack(side="right")
        
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
            "ordered_devices": self.ordered_devices
        }
        try:
            with open(self._get_config_path(), "w") as f:
                json.dump(config_data, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _load_settings(self):
        """Loads application settings from a JSON file."""
        try:
            with open(self._get_config_path(), "r") as f:
                config_data = json.load(f)
                
                if "geometry" in config_data:
                    self.master.geometry(config_data["geometry"])
                else:
                    self.master.geometry("275x800")
                
                if "temp_unit" in config_data:
                    self.temp_unit = config_data["temp_unit"]
                
                # Check if the ordered devices from the config are valid
                if "ordered_devices" in config_data and config_data["ordered_devices"]:
                    self.ordered_devices = config_data["ordered_devices"]
        except (FileNotFound, json.JSONDecodeError):
            self.master.geometry("275x800")
            print("No config file found or file is invalid. Using default settings.")
        
        # We need a default order if none was loaded
        self._create_sensor_list()
        if not self.ordered_devices:
            self._create_default_device_order()

    def _create_sensor_list(self):
        """Generates the sensor data dictionary with hardcoded device names."""
        self.all_sensors = {}
        
        # Core devices
        self.all_sensors["environmental_temp"] = {"device": "Environmental", "label": "Temp", "unit": "°C", "color": "#E57373", "type": "temperature", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["environmental_humidity"] = {"device": "Environmental", "label": "Humidity", "unit": "%", "color": "#64B5F6", "type": "humidity", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["cpu_die_temp"] = {"device": "CPU", "label": "Die Temp", "unit": "°C", "color": "#FFD54F", "type": "cpu_temp", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["cpu_core_usage"] = {"device": "CPU", "label": "Core Usage", "unit": "%", "color": "#FFB74D", "type": "cpu_usage", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["fan_speed"] = {"device": "CPU", "label": "Fans", "unit": "RPM", "color": "#B39DDB", "type": "fan_speed", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["network_usage"] = {"device": "Network", "label": "Usage", "unit": "%", "color": "#29B6F6", "type": "network_usage", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["network_ping"] = {"device": "Network", "label": "Ping", "unit": "ms", "color": "#F44336", "type": "network_ping", "var": tk.DoubleVar(), "history": []}
        self.all_sensors["ram_usage"] = {"device": "Memory", "label": "Usage", "unit": "%", "color": "#81D4FA", "type": "ram_usage", "var": tk.DoubleVar(), "history": []}
        
        # Dynamic devices
        num_gpus = 3
        num_storages = 3
        num_pcie_buses = 2
        
        for i in range(num_gpus):
            device_name = f"GPU {i + 1}"
            self.all_sensors[f"gpu{i+1}_temp"] = {"device": device_name, "label": "Temp", "unit": "°C", "color": "#BA68C8", "type": "gpu_temp", "var": tk.DoubleVar(), "history": []}
            self.all_sensors[f"gpu{i+1}_usage"] = {"device": device_name, "label": "Usage", "unit": "%", "color": "#4DB6AC", "type": "gpu_usage", "var": tk.DoubleVar(), "history": []}
        
        for i in range(num_storages):
            device_name = f"Storage {i + 1}"
            self.all_sensors[f"storage{i+1}_temp"] = {"device": device_name, "label": "Temp", "unit": "°C", "color": "#9E9E9E", "type": "disk_temp", "var": tk.DoubleVar(), "history": []}
            self.all_sensors[f"storage{i+1}_io_read"] = {"device": device_name, "label": "Read", "unit": "MB/s", "color": "#FBC02D", "type": "disk_io_read", "var": tk.DoubleVar(), "history": []}
            self.all_sensors[f"storage{i+1}_io_write"] = {"device": device_name, "label": "Write", "unit": "MB/s", "color": "#F57F17", "type": "disk_io_write", "var": tk.DoubleVar(), "history": []}

        for i in range(num_pcie_buses):
            device_name = f"PCIe Bus {i + 1}"
            self.all_sensors[f"pci{i+1}_temp"] = {"device": device_name, "label": "Temp", "unit": "°C", "color": "#D32F2F", "type": "pci_temp", "var": tk.DoubleVar(), "history": []}

    def _create_default_device_order(self):
        """Generates a default device order for a new installation."""
        devices = sorted(list(set(s['device'] for s in self.all_sensors.values())))
        # Prioritize core system components
        pre_ordered = []
        for dev in ["CPU", "Memory", "Network", "Environmental"]:
            if dev in devices:
                pre_ordered.append(dev)
                devices.remove(dev)
        
        # Sort the remaining dynamic devices to keep their order consistent
        devices.sort()
        self.ordered_devices = pre_ordered + devices
        
    def _on_closing(self):
        """Saves settings and then closes the window."""
        self._save_settings()
        self.master.destroy()

    def _initialize_sensor_gui(self):
        """Initializes all sensor group frames and widgets at startup."""
        main_content_frame = tk.Frame(self.master, bg=self.bg_main)
        main_content_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main_content_frame, bg=self.bg_main, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_main)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind events
        self.master.bind("<Configure>", self._on_window_resize)
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        
        # Create frames and widgets based on the ordered list
        for device_name in self.ordered_devices:
            device_frame = self._create_sensor_group_frame(self.scrollable_frame, device_name)
            self.sensor_frames[device_name] = device_frame
            
            for sensor_key, sensor_data in self.all_sensors.items():
                if sensor_data['device'] == device_name:
                    self._create_sensor_widgets(device_frame, device_name, sensor_data["label"], sensor_data["var"], sensor_data["unit"], sensor_data["color"], sensor_key)
        
        self._repack_frames()

    def _on_window_resize(self, event):
        """Handle window resize event with a debounce to prevent excessive updates."""
        if self.after_id:
            self.master.after_cancel(self.after_id)
        
        self.after_id = self.master.after(100, lambda: self._repack_frames(force=False))
        self._save_settings()

    def _repack_frames(self, force=False):
        """Dynamically re-layouts frames based on window width and the user's reordering."""
        width = self.master.winfo_width()
        
        min_frame_width = 240
        new_columns = max(1, int(width // min_frame_width))

        # Only repack if the column count changes or if forced
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
        frame = tk.Frame(parent, bd=0, relief="flat", bg=self.bg_frame, highlightbackground=self.highlight_color, highlightthickness=1, padx=8, pady=3)
        
        header_frame = tk.Frame(frame, bg=self.bg_frame)
        header_frame.grid(row=0, column=0, columnspan=5, sticky="ew", padx=3, pady=(3, 8))
        header_frame.columnconfigure(1, weight=1)

        up_button = tk.Button(header_frame, text="▲", font=("Segoe UI", 8), bg=self.bg_frame, fg=self.fg_text_primary, bd=0, relief="flat", command=lambda name=title_text: self._move_frame_up(name))
        up_button.pack(side="left", padx=(0, 2))
        
        down_button = tk.Button(header_frame, text="▼", font=("Segoe UI", 8), bg=self.bg_frame, fg=self.fg_text_primary, bd=0, relief="flat", command=lambda name=title_text: self._move_frame_down(name))
        down_button.pack(side="left", padx=(0, 5))

        group_title = tk.Label(header_frame, text=title_text, font=("Segoe UI", 10, "bold"), fg=self.fg_text_primary, bg=self.bg_frame)
        group_title.pack(side="left", fill="x", expand=True)

        self.frame_widget_rows[title_text] = 1

        frame.columnconfigure(1, weight=1, minsize=80)
        frame.columnconfigure(2, weight=0, minsize=50)
        frame.columnconfigure(3, weight=0, minsize=40)
        frame.columnconfigure(4, weight=0)

        return frame

    def _move_frame_up(self, device_name):
        """Moves a given frame up in the ordered list."""
        current_index = self.ordered_devices.index(device_name)
        if current_index > 0:
            self.ordered_devices[current_index], self.ordered_devices[current_index - 1] = self.ordered_devices[current_index - 1], self.ordered_devices[current_index]
            self._repack_frames(force=True)
            self._save_settings()

    def _move_frame_down(self, device_name):
        """Moves a given frame down in the ordered list."""
        current_index = self.ordered_devices.index(device_name)
        if current_index < len(self.ordered_devices) - 1:
            self.ordered_devices[current_index], self.ordered_devices[current_index + 1] = self.ordered_devices[current_index + 1], self.ordered_devices[current_index]
            self._repack_frames(force=True)
            self._save_settings()

    def _create_sensor_widgets(self, parent_frame, device_name, label_text, var, unit, color, sensor_key):
        """Helper to create sensor labels, values, and a mini-graph within a frame."""
        row = self.frame_widget_rows[device_name]
        self.frame_widget_rows[device_name] += 1

        label = tk.Label(parent_frame, text=f"{label_text}:", font=self.font_label, fg=self.fg_text_primary, bg=self.bg_frame)
        label.grid(row=row, column=1, sticky="w", padx=2, pady=3)

        value_label = tk.Label(parent_frame, textvariable=var, font=self.font_value, fg=color, bg=self.bg_frame)
        value_label.grid(row=row, column=2, sticky="e", padx=2, pady=3)

        if 'unit_labels' not in self.sensor_frames[device_name].__dict__:
            self.sensor_frames[device_name].unit_labels = {}

        unit_label = tk.Label(parent_frame, text=unit, font=self.font_unit, fg=self.fg_text_secondary, bg=self.bg_frame)
        unit_label.grid(row=row, column=3, sticky="w", padx=2, pady=3)
        self.sensor_frames[device_name].unit_labels[sensor_key] = unit_label

        graph_canvas = tk.Canvas(parent_frame, width=50, height=25, bg=self.bg_frame, highlightthickness=0)
        graph_canvas.grid(row=row, column=4, sticky="e", padx=2, pady=3)
        graph_canvas.bind('<Configure>', lambda event, key=sensor_key: self._on_graph_resize(event, key))

        self.graph_canvases[sensor_key] = graph_canvas

    def _on_frame_configure(self, event):
        """
        Update the scrollregion of the canvas when the inner frame's size changes.
        """
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
            color = self.all_sensors[sensor_key]['color']
            self._draw_graph(self.graph_canvases[sensor_key], history, color)

    def get_simulated_reading(self, sensor_type):
        """
        Simulates a sensor reading based on type.
        """
        if random.random() < 0.8:
            if sensor_type == "temperature":
                return round(random.uniform(20.0, 30.0), 1)
            elif sensor_type == "humidity":
                return round(random.uniform(40.0, 70.0), 1)
            elif sensor_type == "cpu_temp":
                return round(random.uniform(40.0, 75.0), 1)
            elif sensor_type == "cpu_usage":
                return round(random.uniform(5.0, 95.0), 1)
            elif "gpu_temp" in sensor_type:
                return round(random.uniform(45.0, 80.0), 1)
            elif "gpu_usage" in sensor_type:
                return round(random.uniform(0.0, 100.0), 1)
            elif sensor_type == "network_usage":
                return round(random.uniform(0.0, 100.0), 1)
            elif "disk_temp" in sensor_type:
                return round(random.uniform(30.0, 60.0), 1)
            elif "pci_temp" in sensor_type:
                return round(random.uniform(35.0, 70.0), 1)
            elif sensor_type == "ram_usage":
                return round(random.uniform(20.0, 95.0), 1)
            elif "disk_io_read" in sensor_type:
                return round(random.uniform(0.0, 500.0), 1)
            elif "disk_io_write" in sensor_type:
                return round(random.uniform(0.0, 300.0), 1)
            elif sensor_type == "network_ping":
                return random.randint(10, 150)
            elif sensor_type == "fan_speed":
                return random.randint(800, 4000)
        return None

    def _draw_graph(self, canvas, history_data, color):
        """
        Draws a simple line graph on the given canvas.
        """
        canvas.delete("all")

        if len(history_data) < 2:
            return

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        min_val = min(history_data) if history_data else 0
        max_val = max(history_data) if history_data else 1
        range_val = max_val - min_val if (max_val - min_val) != 0 else 1

        points = []
        for i, val in enumerate(history_data):
            x = i * (width / (len(history_data) - 1)) if len(history_data) > 1 else width / 2
            y = height - ((val - min_val) / range_val) * height
            points.append((x, y))

        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=1.5)

    def _toggle_temp_unit(self):
        """Toggles the temperature unit between Celsius and Fahrenheit."""
        if self.temp_unit == "C":
            self.temp_unit = "F"
            self.unit_button.config(text="Switch to °C")
            new_unit_text = "°F"
        else:
            self.temp_unit = "C"
            self.unit_button.config(text="Switch to °F")
            new_unit_text = "°C"

        for sensor_key, sensor_data in self.all_sensors.items():
            if sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                current_val = sensor_data["var"].get()
                if self.temp_unit == "F":
                    converted_val = (current_val * 9/5) + 32
                else:
                    converted_val = (current_val - 32) * 5/9
                sensor_data["var"].set(round(converted_val, 1))

                device_name = sensor_data['device']
                if device_name in self.sensor_frames and hasattr(self.sensor_frames[device_name], 'unit_labels') and sensor_key in self.sensor_frames[device_name].unit_labels:
                    self.sensor_frames[device_name].unit_labels[sensor_key].config(text=new_unit_text)
                    self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], sensor_data["color"])
        
        self._save_settings()

    def update_sensors(self):
        """
        Updates the sensor data dynamically and schedules the next update.
        """
        current_time = time.strftime("%H:%M:%S")

        for sensor_key, sensor_data in self.all_sensors.items():
            current_val_c = self.get_simulated_reading(sensor_data["type"])
            
            if current_val_c is not None:
                if self.temp_unit == "F" and sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                    converted_val = (current_val_c * 9/5) + 32
                    sensor_data["var"].set(round(converted_val, 1))
                    sensor_data["history"].append(round(converted_val, 1))
                    
                else:
                    sensor_data["var"].set(current_val_c)
                    sensor_data["history"].append(current_val_c)

                if len(sensor_data["history"]) > 20:
                    sensor_data["history"].pop(0)

                current_value = sensor_data["var"].get()
                unit = "°F" if self.temp_unit == "F" and sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"] else sensor_data['unit']
                self.current_readings_for_log[sensor_key] = f"{current_value}{unit}"
            else:
                self.current_readings_for_log[sensor_key] = "N/A"
            
            if sensor_key in self.graph_canvases:
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], sensor_data["color"])

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
                for sensor_key, value in self.current_readings_for_log.items():
                    f.write(f"{self.all_sensors[sensor_key]['device']} {self.all_sensors[sensor_key]['label']}: {value}\n")
                f.write("\n")

            messagebox.showinfo("Log Saved", f"Current readings appended to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorTrackerApp(root)
    root.mainloop()
