import tkinter as tk
from tkinter import messagebox
import random
import time
import datetime
import os

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
        # Set the initial geometry to be tall and narrow
        master.geometry("244x800")

        # Set the application icon. The file 'icon.ico' must be in the same directory.
        try:
            master.iconbitmap("icon.ico")
        except tk.TclError:
            print("Warning: icon.ico not found. The default icon will be used.")

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
        self.font_status = ("Segoe UI", 8, "italic")
        self.font_button = ("Segoe UI", 10, "bold")

        # --- Sensor Data Variables (all data is now in this one dictionary) ---
        # This makes the app highly dynamic and scalable.
        self.all_sensors = {
            "environmental_temp": {"device": "Environmental", "label": "Temp", "unit": "°C", "color": "#E57373", "type": "temperature", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "environmental_humidity": {"device": "Environmental", "label": "Humidity", "unit": "%", "color": "#64B5F6", "type": "humidity", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "cpu_die_temp": {"device": "CPU", "label": "Die Temp", "unit": "°C", "color": "#FFD54F", "type": "cpu_temp", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "cpu_core_usage": {"device": "CPU", "label": "Core Usage", "unit": "%", "color": "#FFB74D", "type": "cpu_usage", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "gpu1_temp": {"device": "GPU 1", "label": "Temp", "unit": "°C", "color": "#BA68C8", "type": "gpu_temp", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "gpu1_usage": {"device": "GPU 1", "label": "Usage", "unit": "%", "color": "#4DB6AC", "type": "gpu_usage", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "gpu2_temp": {"device": "GPU 2", "label": "Temp", "unit": "°C", "color": "#BA68C8", "type": "gpu_temp", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "gpu2_usage": {"device": "GPU 2", "label": "Usage", "unit": "%", "color": "#4DB6AC", "type": "gpu_usage", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            # New, non-GPU sensors
            "network_usage": {"device": "Network", "label": "Usage", "unit": "%", "color": "#29B6F6", "type": "network_usage", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "disk_temp": {"device": "Storage", "label": "Temp", "unit": "°C", "color": "#9E9E9E", "type": "disk_temp", "var": tk.DoubleVar(), "history": [], "has_reading": False},
            "pci_temp": {"device": "PCIe Bus", "label": "Temp", "unit": "°C", "color": "#D32F2F", "type": "pci_temp", "var": tk.DoubleVar(), "history": [], "has_reading": False},
        }

        # Dictionaries to track sensor state and GUI elements
        self.current_readings_for_log = {}
        self.graph_canvases = {}
        self.sensor_frames = {}
        self.frame_widget_rows = {}
        self.last_updated_text = tk.StringVar()
        self.temp_unit = "C" # New state variable for temperature unit

        # --- GUI Elements ---
        self.title_label = tk.Label(master, text="System Monitor", font=self.font_title, fg=self.fg_text_primary, bg=self.bg_main, pady=15)
        self.title_label.pack()

        self.status_label = tk.Label(master, textvariable=self.last_updated_text, font=self.font_status, fg=self.fg_text_secondary, bg=self.bg_main)
        self.status_label.pack(pady=(5, 10))

        # Container frame for the buttons
        button_frame = tk.Frame(master, bg=self.bg_main)
        button_frame.pack(pady=(10, 10))

        # Temperature unit toggle button
        self.unit_button = tk.Button(button_frame, text="Switch to °F",
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


        # Reverted: The canvas now fills the available space
        self.canvas = tk.Canvas(master, bg=self.bg_main, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=0)
        
        # Hiding the scrollbar as requested
        # self.scrollbar = tk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        # self.scrollbar.pack(side="right", fill="y")
        # self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_main)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

        # Initialize the GUI with all known sensors before starting the update loop
        self._initialize_sensor_gui()

        # Start the sensor update loop
        self.update_sensors()

    def _initialize_sensor_gui(self):
        """Initializes all sensor group frames and widgets at startup."""
        devices = list(set(s['device'] for s in self.all_sensors.values()))
        
        # Create a specific display order for key devices
        sorted_devices = []
        if "Network" in devices:
            sorted_devices.append("Network")
            devices.remove("Network")
        if "Environmental" in devices:
            sorted_devices.append("Environmental")
            devices.remove("Environmental")

        # Sort the remaining devices alphabetically
        devices.sort()
        sorted_devices.extend(devices)

        for device_name in sorted_devices:
            # Create a frame for the device
            device_frame = self._create_sensor_group_frame(self.scrollable_frame, device_name)
            # Reverted: The frames now expand horizontally to fill the canvas width
            device_frame.pack(pady=8, fill="x")
            self.sensor_frames[device_name] = device_frame
            
            # Populate the frame with widgets for each sensor in that device group
            for sensor_key, sensor_data in self.all_sensors.items():
                if sensor_data['device'] == device_name:
                    self._create_sensor_widgets(device_frame, device_name, sensor_data["label"], sensor_data["var"], sensor_data["unit"], sensor_data["color"], sensor_key)

    def _create_sensor_group_frame(self, parent, title_text):
        """Helper to create a consistent sensor group frame with a title and content that expands."""
        frame = tk.Frame(parent, bd=0, relief="flat", bg=self.bg_frame, highlightbackground=self.highlight_color, highlightthickness=1, padx=8, pady=3)
        
        # New: Configure columns with weights to ensure they are evenly distributed and aligned.
        frame.columnconfigure(0, weight=1)  # Label column will expand
        frame.columnconfigure(1, weight=1)  # Value column will expand
        frame.columnconfigure(2, weight=0)  # Unit column has fixed width
        frame.columnconfigure(3, weight=0)  # Graph column has fixed width
        
        # Reduced font size for group title
        group_title = tk.Label(frame, text=title_text, font=("Segoe UI", 10, "bold"), fg=self.fg_text_primary, bg=self.bg_frame)
        group_title.grid(row=0, column=0, columnspan=4, sticky="w", padx=3, pady=(3, 8))

        self.frame_widget_rows[title_text] = 1 # Start widget rows after the title
        return frame

    def _on_graph_resize(self, event, sensor_key):
        """Redraws the graph when its size changes."""
        self._draw_graph(event.widget, self.all_sensors[sensor_key]['history'], self.all_sensors[sensor_key]['color'])

    def _create_sensor_widgets(self, parent_frame, device_name, label_text, var, unit, color, sensor_key):
        """Helper to create sensor labels, values, and a mini-graph within a frame."""
        row = self.frame_widget_rows[device_name]
        self.frame_widget_rows[device_name] += 1

        label = tk.Label(parent_frame, text=f"{label_text}:", font=self.font_label, fg=self.fg_text_primary, bg=self.bg_frame)
        label.grid(row=row, column=0, sticky="w", padx=2, pady=3)

        value_label = tk.Label(parent_frame, textvariable=var, font=self.font_value, fg=color, bg=self.bg_frame)
        value_label.grid(row=row, column=1, sticky="e", padx=2, pady=3)

        # Use a dictionary to store the unit label widget so we can update it
        if 'unit_labels' not in self.sensor_frames[device_name].__dict__:
            self.sensor_frames[device_name].unit_labels = {}

        unit_label = tk.Label(parent_frame, text=unit, font=self.font_value, fg=self.fg_text_secondary, bg=self.bg_frame)
        unit_label.grid(row=row, column=2, sticky="w", padx=2, pady=3)
        self.sensor_frames[device_name].unit_labels[sensor_key] = unit_label

        # Set a fixed, smaller width for the graph canvas
        graph_canvas = tk.Canvas(parent_frame, width=50, height=25, bg=self.bg_frame, highlightthickness=0)
        graph_canvas.grid(row=row, column=3, sticky="e", padx=2, pady=3)
        graph_canvas.bind('<Configure>', lambda event, key=sensor_key: self._on_graph_resize(event, key))

        self.graph_canvases[sensor_key] = graph_canvas

    def on_frame_configure(self, event):
        """Update the scrollregion of the canvas when the inner frame's size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for Windows/macOS."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_linux(self, event):
        """Handle mouse wheel scrolling for Linux."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

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
            # New sensor types
            elif sensor_type == "network_usage":
                return round(random.uniform(0.0, 100.0), 1)
            elif sensor_type == "disk_temp":
                return round(random.uniform(30.0, 60.0), 1)
            elif sensor_type == "pci_temp":
                return round(random.uniform(35.0, 70.0), 1)
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
            # Fallback for cases where the widget size is not yet available
            return

        min_val = min(history_data)
        max_val = max(history_data)
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

        # Iterate through all sensor readings to convert them
        for sensor_key, sensor_data in self.all_sensors.items():
            if sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                current_val = sensor_data["var"].get()
                if self.temp_unit == "F":
                    converted_val = (current_val * 9/5) + 32
                else:
                    converted_val = (current_val - 32) * 5/9
                sensor_data["var"].set(round(converted_val, 1))

                # Also update the unit label text
                for frame in self.sensor_frames.values():
                    if hasattr(frame, 'unit_labels') and sensor_key in frame.unit_labels:
                        frame.unit_labels[sensor_key].config(text=new_unit_text)

        # Clear and update the history with converted values
        for sensor_key, sensor_data in self.all_sensors.items():
            if sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                # The history is now in the new unit, so we don't need to reconvert.
                # Just need to make sure the label is right.
                if 'unit_labels' not in self.sensor_frames[sensor_data['device']].__dict__:
                    self.sensor_frames[sensor_data['device']].unit_labels = {}
                unit_label = self.sensor_frames[sensor_data['device']].unit_labels[sensor_key]
                unit_label.config(text=new_unit_text)
                self._draw_graph(self.graph_canvases[sensor_key], sensor_data["history"], sensor_data["color"])


    def update_sensors(self):
        """
        Updates the sensor data dynamically and schedules the next update.
        """
        current_time = time.strftime("%H:%M:%S")

        for sensor_key, sensor_data in self.all_sensors.items():
            current_val_c = self.get_simulated_reading(sensor_data["type"])
            
            if current_val_c is not None:
                # Store the value in Celsius for internal use and conversions
                
                # If the current unit is Fahrenheit, convert the simulated Celsius reading
                if self.temp_unit == "F" and sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"]:
                    converted_val = (current_val_c * 9/5) + 32
                    sensor_data["var"].set(round(converted_val, 1))
                    
                    # Update history with the converted value
                    sensor_data["history"].append(round(converted_val, 1))
                    
                else:
                    sensor_data["var"].set(current_val_c)
                    sensor_data["history"].append(current_val_c)

                # Trim history if it's too long
                if len(sensor_data["history"]) > 20:
                    sensor_data["history"].pop(0)

                # Store the reading for the log file, using the correct unit
                current_value = sensor_data["var"].get()
                unit = "°F" if self.temp_unit == "F" and sensor_data['type'] in ["temperature", "cpu_temp", "gpu_temp", "disk_temp", "pci_temp"] else sensor_data['unit']
                self.current_readings_for_log[sensor_key] = f"{current_value}{unit}"
            else:
                self.current_readings_for_log[sensor_key] = "N/A"
            
            # Only redraw the graph if the canvas has been created
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
                    # Use a more descriptive label in the log file
                    f.write(f"{self.all_sensors[sensor_key]['device']} {self.all_sensors[sensor_key]['label']}: {value}\n")
                f.write("\n")

            messagebox.showinfo("Log Saved", f"Current readings appended to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorTrackerApp(root)
    root.mainloop()
