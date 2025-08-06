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
        master.title("System Monitor")
        master.geometry("500x900") # Retained window size
        master.resizable(True, True)

        # Set a modern background color for the main window
        self.bg_main = "#263238" # Darker, more uniform background (Deep Blue Gray)
        self.bg_frame = "#37474F" # Slightly lighter for frames (Blue Gray)
        self.fg_text_primary = "#ECEFF1" # Light text for readability
        self.fg_text_secondary = "#B0BEC5" # Muted text for status/units
        self.highlight_color = "#607D8B" # Subtle highlight for frames
        self.button_bg = "#66BB6A" # Green for save log button
        self.button_fg = "#FFFFFF" # White text for button

        master.configure(bg=self.bg_main)

        # Configure attractive fonts - slightly smaller for compactness
        self.font_title = ("Segoe UI", 24, "bold")
        self.font_label = ("Segoe UI", 14)
        self.font_value = ("Segoe UI", 24, "bold")
        self.font_status = ("Segoe UI", 10, "italic")
        self.font_button = ("Segoe UI", 12, "bold")

        # --- Sensor Data Variables ---
        self.temperature = tk.DoubleVar()
        self.humidity = tk.DoubleVar()
        self.cpu_temp = tk.DoubleVar()
        self.cpu_usage = tk.DoubleVar()
        self.gpu_temp_1 = tk.DoubleVar() # GPU 1 Temperature
        self.gpu_usage_1 = tk.DoubleVar() # GPU 1 Usage
        self.gpu_temp_2 = tk.DoubleVar() # GPU 2 Temperature
        self.gpu_usage_2 = tk.DoubleVar() # GPU 2 Usage
        self.last_updated_text = tk.StringVar()

        # Dictionary to track if a sensor has ever given a reading
        self.sensor_has_reading_ever = {
            "temperature": False,
            "humidity": False,
            "cpu_temp": False,
            "cpu_usage": False,
            "gpu_temp_1": False,
            "gpu_usage_1": False,
            "gpu_temp_2": False,
            "gpu_usage_2": False,
        }

        # Store last known readings for logging and graph history
        self.current_readings_for_log = {
            "Motherboard Temp": "N/A",
            "Motherboard Humidity": "N/A",
            "CPU Die Temp": "N/A",
            "CPU Core Usage": "N/A",
            "GPU 1 Temp": "N/A",
            "GPU 1 Usage": "N/A",
            "GPU 2 Temp": "N/A",
            "GPU 2 Usage": "N/A",
        }

        # Store history of numerical readings for graphs
        self.sensor_history = {
            "temperature": [],
            "humidity": [],
            "cpu_temp": [],
            "cpu_usage": [],
            "gpu_temp_1": [],
            "gpu_usage_1": [],
            "gpu_temp_2": [],
            "gpu_usage_2": [],
        }

        # Dictionary to store references to each sensor's graph canvas
        self.graph_canvases = {}

        # --- GUI Elements ---

        # Title Label (remains at the top)
        self.title_label = tk.Label(master, text="System Monitor", font=self.font_title, fg=self.fg_text_primary, bg=self.bg_main, pady=15)
        self.title_label.pack(fill="x")

        # Status/Last Updated Label (appears directly below the title)
        self.status_label = tk.Label(master, textvariable=self.last_updated_text, font=self.font_status, fg=self.fg_text_secondary, bg=self.bg_main)
        self.status_label.pack(pady=(5, 10), fill="x")

        # --- Save to Log Button (appears below status label, above canvas) ---
        self.save_log_button = tk.Button(master, text="Save to Log",
                                         command=self.save_to_log,
                                         font=self.font_button,
                                         bg=self.button_bg, fg=self.button_fg,
                                         activebackground=self.button_bg, activeforeground=self.button_fg,
                                         relief="flat", bd=0, padx=10, pady=5)
        self.save_log_button.pack(pady=(10, 10))

        # --- Scrollable Area Setup ---
        self.canvas = tk.Canvas(master, bg=self.bg_main, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_main)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

        # --- Sensor Group Frames (packed into self.scrollable_frame) ---

        self.environmental_frame = self._create_sensor_group_frame(self.scrollable_frame, "Environmental")
        self._create_sensor_widgets(self.environmental_frame, "Motherboard", "Temp:", self.temperature, "°C", "#E57373", row=0, sensor_key="temperature")
        self._create_sensor_widgets(self.environmental_frame, "Motherboard", "Humidity:", self.humidity, "%", "#64B5F6", row=1, sensor_key="humidity")

        self.cpu_frame = self._create_sensor_group_frame(self.scrollable_frame, "CPU")
        self._create_sensor_widgets(self.cpu_frame, "CPU Die", "Temp:", self.cpu_temp, "°C", "#FFD54F", row=0, sensor_key="cpu_temp")
        self._create_sensor_widgets(self.cpu_frame, "CPU Core", "Usage:", self.cpu_usage, "%", "#FFB74D", row=1, sensor_key="cpu_usage")

        self.gpu_frame_1 = self._create_sensor_group_frame(self.scrollable_frame, "GPU 1")
        self._create_sensor_widgets(self.gpu_frame_1, "GPU 1", "Temp:", self.gpu_temp_1, "°C", "#BA68C8", row=0, sensor_key="gpu_temp_1")
        self._create_sensor_widgets(self.gpu_frame_1, "GPU 1", "Usage:", self.gpu_usage_1, "%", "#4DB6AC", row=1, sensor_key="gpu_usage_1")

        self.gpu_frame_2 = self._create_sensor_group_frame(self.scrollable_frame, "GPU 2")
        self._create_sensor_widgets(self.gpu_frame_2, "GPU 2", "Temp:", self.gpu_temp_2, "°C", "#BA68C8", row=0, sensor_key="gpu_temp_2")
        self._create_sensor_widgets(self.gpu_frame_2, "GPU 2", "Usage:", self.gpu_usage_2, "%", "#4DB6AC", row=1, sensor_key="gpu_usage_2")

        # Start the sensor update loop
        self.update_sensors()

    def _create_sensor_group_frame(self, parent, title_text):
        """Helper to create a consistent sensor group frame with a title."""
        frame = tk.Frame(parent, bd=0, relief="flat", bg=self.bg_frame, highlightbackground=self.highlight_color, highlightthickness=1, padx=8, pady=3)
        frame.columnconfigure(1, weight=1) # Value column
        frame.columnconfigure(2, weight=0) # Unit column
        frame.columnconfigure(3, weight=0) # Graph column

        group_title = tk.Label(frame, text=title_text, font=("Segoe UI", 12, "bold"), fg=self.fg_text_primary, bg=self.bg_frame)
        group_title.grid(row=0, column=0, columnspan=4, sticky="w", padx=3, pady=(3, 8)) # Span across 4 columns

        frame.content_row_offset = 1
        return frame

    def _create_sensor_widgets(self, parent_frame, device_name, label_text, var, unit, color, row=0, sensor_key=None):
        """Helper to create sensor labels, values, and a mini-graph within a frame."""
        actual_row = row + parent_frame.content_row_offset

        full_label_text = f"{device_name} {label_text}"

        label = tk.Label(parent_frame, text=full_label_text, font=self.font_label, fg=self.fg_text_primary, bg=self.bg_frame)
        label.grid(row=actual_row, column=0, sticky="w", padx=10, pady=3)

        value_label = tk.Label(parent_frame, textvariable=var, font=self.font_value, fg=color, bg=self.bg_frame)
        value_label.grid(row=actual_row, column=1, sticky="e", padx=3, pady=3)

        unit_label = tk.Label(parent_frame, text=unit, font=self.font_value, fg=self.fg_text_secondary, bg=self.bg_frame)
        unit_label.grid(row=actual_row, column=2, sticky="w", padx=3, pady=3)

        # Create a small canvas for the graph
        graph_canvas = tk.Canvas(parent_frame, width=80, height=25, bg=self.bg_frame, highlightthickness=0)
        graph_canvas.grid(row=actual_row, column=3, sticky="e", padx=5, pady=3)

        if sensor_key:
            self.graph_canvases[sensor_key] = graph_canvas # Store reference to the canvas

    def on_frame_configure(self, event):
        """Update the scrollregion of the canvas when the inner frame's size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for Windows/macOS."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_linux(self, event):
        """Handle mouse wheel scrolling for Linux."""
        if event.num == 4: # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5: # Scroll down
            self.canvas.yview_scroll(1, "units")

    def get_simulated_reading(self, sensor_type):
        """
        Simulates a sensor reading. Randomly returns a value or None.
        In a real application, this would read from actual hardware sensors.
        """
        # 80% chance to have a reading, 20% chance to have no reading
        if random.random() < 0.8:
            if sensor_type == "temperature":
                return round(random.uniform(20.0, 30.0), 1)
            elif sensor_type == "humidity":
                return round(random.uniform(40.0, 70.0), 1)
            elif sensor_type == "cpu_temp":
                return round(random.uniform(40.0, 75.0), 1)
            elif sensor_type == "cpu_usage":
                return round(random.uniform(5.0, 95.0), 1)
            elif sensor_type == "gpu_temp_1":
                return round(random.uniform(45.0, 80.0), 1)
            elif sensor_type == "gpu_usage_1":
                return round(random.uniform(0.0, 100.0), 1)
            elif sensor_type == "gpu_temp_2":
                return round(random.uniform(40.0, 75.0), 1)
            elif sensor_type == "gpu_usage_2":
                return round(random.uniform(0.0, 90.0), 1)
        return None

    def _draw_graph(self, canvas, history_data, color):
        """
        Draws a simple line graph on the given canvas.
        """
        canvas.delete("all") # Clear previous drawings

        if len(history_data) < 2:
            return # Need at least two points to draw a line

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        # Fallback for initial rendering where width/height might be 1
        if width <= 1 or height <= 1:
            width = 80
            height = 25

        min_val = min(history_data)
        max_val = max(history_data)

        # Avoid division by zero if all values are the same
        range_val = max_val - min_val if (max_val - min_val) != 0 else 1

        points = []
        # Calculate points for the line graph
        for i, val in enumerate(history_data):
            x = i * (width / (len(history_data) - 1)) if len(history_data) > 1 else width / 2
            # Invert Y-axis so higher values are higher on the graph
            y = height - ((val - min_val) / range_val) * height
            points.append((x, y))

        # Draw lines connecting the points
        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=1.5)


    def update_sensors(self):
        """
        Updates the sensor data and schedules the next update.
        Dynamically shows/hides sensor frames based on readings.
        Also updates current_readings_for_log for logging and draws graphs.
        """
        current_time = time.strftime("%H:%M:%S")

        # Helper to process each sensor's reading, update history, and draw graph
        def _process_sensor(sensor_key, tk_var, log_key, unit_str, graph_color):
            current_val = self.get_simulated_reading(sensor_key)
            if current_val is not None:
                tk_var.set(current_val)
                self.sensor_has_reading_ever[sensor_key] = True
                self.current_readings_for_log[log_key] = f"{current_val}{unit_str}"
                self.sensor_history[sensor_key].append(current_val)
                # Keep history to a fixed number of points (e.g., last 20 readings)
                if len(self.sensor_history[sensor_key]) > 20:
                    self.sensor_history[sensor_key].pop(0) # Remove oldest reading
            elif not self.sensor_has_reading_ever[sensor_key]:
                self.current_readings_for_log[log_key] = "N/A"

            # Draw graph if sensor has ever had a reading and its canvas exists
            if self.sensor_has_reading_ever[sensor_key] and sensor_key in self.graph_canvases:
                self._draw_graph(self.graph_canvases[sensor_key], self.sensor_history[sensor_key], graph_color)

        # --- Update all sensors ---
        _process_sensor("temperature", self.temperature, "Motherboard Temp", "°C", "#E57373")
        _process_sensor("humidity", self.humidity, "Motherboard Humidity", "%", "#64B5F6")
        _process_sensor("cpu_temp", self.cpu_temp, "CPU Die Temp", "°C", "#FFD54F")
        _process_sensor("cpu_usage", self.cpu_usage, "CPU Core Usage", "%", "#FFB74D")
        _process_sensor("gpu_temp_1", self.gpu_temp_1, "GPU 1 Temp", "°C", "#BA68C8")
        _process_sensor("gpu_usage_1", self.gpu_usage_1, "GPU 1 Usage", "%", "#4DB6AC")
        _process_sensor("gpu_temp_2", self.gpu_temp_2, "GPU 2 Temp", "°C", "#BA68C8")
        _process_sensor("gpu_usage_2", self.gpu_usage_2, "GPU 2 Usage", "%", "#4DB6AC")

        # --- Manage frame visibility based on 'has_reading_ever' for any sensor in the group ---

        # Environmental Frame
        if self.sensor_has_reading_ever["temperature"] or self.sensor_has_reading_ever["humidity"]:
            if not self.environmental_frame.winfo_ismapped():
                self.environmental_frame.pack(pady=8, fill="x", padx=20)

        # CPU Frame
        if self.sensor_has_reading_ever["cpu_temp"] or self.sensor_has_reading_ever["cpu_usage"]:
            if not self.cpu_frame.winfo_ismapped():
                self.cpu_frame.pack(pady=8, fill="x", padx=20)

        # GPU 1 Frame
        if self.sensor_has_reading_ever["gpu_temp_1"] or self.sensor_has_reading_ever["gpu_usage_1"]:
            if not self.gpu_frame_1.winfo_ismapped():
                self.gpu_frame_1.pack(pady=8, fill="x", padx=20)

        # GPU 2 Frame
        if self.sensor_has_reading_ever["gpu_temp_2"] or self.sensor_has_reading_ever["gpu_usage_2"]:
            if not self.gpu_frame_2.winfo_ismapped():
                self.gpu_frame_2.pack(pady=8, fill="x", padx=20)

        # --- Update Status Message ---
        self.last_updated_text.set(f"Last Updated: {current_time}")

        # Schedule the next update after 2000 milliseconds (2 seconds)
        self.master.after(2000, self.update_sensors)

    def save_to_log(self):
        """
        Saves the current sensor readings to a text log file.
        """
        # Get the user's Documents directory
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        
        # Ensure the directory exists
        os.makedirs(documents_path, exist_ok=True)

        # Create a filename with today's date
        file_name = f"System_Monitor_Log_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(documents_path, file_name)

        try:
            with open(file_path, "a") as f: # Open in append mode
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"--- Log Entry: {timestamp} ---\n")
                for sensor_name, value in self.current_readings_for_log.items():
                    f.write(f"{sensor_name}: {value}\n")
                f.write("\n") # Add a blank line for separation

            messagebox.showinfo("Log Saved", f"Current readings appended to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SensorTrackerApp(root)
    root.mainloop()
