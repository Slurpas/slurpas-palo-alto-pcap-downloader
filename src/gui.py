# This file will contain the GUI code for the application. 

import customtkinter
from api_handler import PaloAltoAPI
import json
import os
import threading
import time
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'settings.json')

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Slurpas Palo Alto PCAP Downloader")
        self.geometry("800x600")

        # Set a lighter, high-contrast background color for better readability
        app_bg = '#e5e5e5'  # light gray
        text_fg = '#222222'  # dark text
        self.configure(bg=app_bg)

        # Responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=0)

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # --- SCROLLABLE MAIN FRAME ---
        self.scroll_canvas = customtkinter.CTkCanvas(self, borderwidth=0, highlightthickness=0, bg=app_bg)
        self.scroll_canvas.grid(row=0, column=0, rowspan=4, columnspan=5, sticky="nsew", padx=0, pady=0)
        self.scrollbar = customtkinter.CTkScrollbar(self, orientation="vertical", command=self.scroll_canvas.yview)
        self.scrollbar.grid(row=0, column=5, rowspan=4, sticky="ns")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame = customtkinter.CTkFrame(self.scroll_canvas, corner_radius=0, fg_color=app_bg)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox("all")
            )
        )
        self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_frame = self.scrollable_frame

        # Set a single, consistent background color for the app and all frames
        self.configure(bg=app_bg)
        self.scroll_canvas.configure(bg=app_bg)
        self.scrollable_frame.configure(fg_color=app_bg)

        # --- FIREWALL CONNECTION FIELDS (now in main_frame) ---
        self.ip_label = customtkinter.CTkLabel(self.main_frame, text="Firewall IP/Hostname:")
        self.ip_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
        self.ip_entry = customtkinter.CTkEntry(self.main_frame)
        self.ip_entry.grid(row=0, column=1, padx=20, pady=5, sticky="ew")
        # Add a grey label below the Firewall IP field to clarify format
        self.ip_format_label = customtkinter.CTkLabel(self.main_frame, text="e.g. 192.168.1.1, 192.168.1.2, ...", font=customtkinter.CTkFont(size=12), text_color="#888", anchor="w")
        self.ip_format_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 5), sticky="w")
        # Move username and password fields down
        self.user_label = customtkinter.CTkLabel(self.main_frame, text="Username:")
        self.user_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        self.user_entry = customtkinter.CTkEntry(self.main_frame)
        self.user_entry.grid(row=2, column=1, padx=20, pady=5, sticky="ew")
        self.pass_label = customtkinter.CTkLabel(self.main_frame, text="Password:")
        self.pass_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")
        self.pass_entry = customtkinter.CTkEntry(self.main_frame, show="*")
        self.pass_entry.grid(row=3, column=1, padx=20, pady=5, sticky="ew")

        # --- NEW CONTINUOUS DOWNLOAD CONTROLS ---
        self.project_name_label = customtkinter.CTkLabel(self.main_frame, text="Project Name:")
        self.project_name_label.grid(row=15, column=0, padx=20, pady=5, sticky="w")
        self.project_name_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. MyProject")
        self.project_name_entry.grid(row=15, column=1, padx=20, pady=5, sticky="ew")

        # --- INTERVAL SLIDERS WITH VALUE LABELS ---
        self.interval_label = customtkinter.CTkLabel(self.main_frame, text="Interval Between Downloads:")
        self.interval_label.grid(row=16, column=0, padx=20, pady=5, sticky="w")
        self.minutes_slider = customtkinter.CTkSlider(self.main_frame, from_=0, to=59, number_of_steps=59, width=150, command=self.update_minutes_label)
        self.minutes_slider.set(0)
        self.minutes_slider.grid(row=17, column=1, padx=(20, 80), pady=5, sticky="w")
        self.minutes_value_label = customtkinter.CTkLabel(self.main_frame, text="0 min")
        self.minutes_value_label.grid(row=17, column=1, padx=(180, 0), pady=5, sticky="w")
        self.seconds_slider = customtkinter.CTkSlider(self.main_frame, from_=0, to=59, number_of_steps=59, width=150, command=self.update_seconds_label)
        self.seconds_slider.set(10)
        self.seconds_slider.grid(row=18, column=1, padx=(20, 80), pady=5, sticky="w")
        self.seconds_value_label = customtkinter.CTkLabel(self.main_frame, text="10 sec")
        self.seconds_value_label.grid(row=18, column=1, padx=(180, 0), pady=5, sticky="w")
        self.count_label = customtkinter.CTkLabel(self.main_frame, text="Stop after this many downloads:")
        self.count_label.grid(row=19, column=0, padx=20, pady=5, sticky="w")
        self.count_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. 10")
        self.count_entry.grid(row=19, column=1, padx=20, pady=5, sticky="ew")

        self.save_dir_label = customtkinter.CTkLabel(self.main_frame, text="Save Directory:")
        self.save_dir_label.grid(row=20, column=0, padx=20, pady=5, sticky="w")
        self.save_dir_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="Select directory...")
        self.save_dir_entry.grid(row=20, column=1, padx=20, pady=5, sticky="ew")
        self.save_dir_button = customtkinter.CTkButton(self.main_frame, text="Browse", command=self.browse_save_dir)
        self.save_dir_button.grid(row=20, column=2, padx=10, pady=5, sticky="w")

        self.progress_label = customtkinter.CTkLabel(self.main_frame, text="Time until next download:")
        self.progress_label.grid(row=21, column=0, padx=20, pady=5, sticky="w")
        self.progress_bar = customtkinter.CTkProgressBar(self.main_frame, width=300)
        self.progress_bar.grid(row=21, column=1, padx=20, pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.start_dl_button = customtkinter.CTkButton(self.main_frame, text="Start Downloading", command=self.start_continuous_download)
        self.start_dl_button.grid(row=22, column=0, padx=20, pady=15, sticky="ew")
        self.stop_dl_button = customtkinter.CTkButton(self.main_frame, text="Stop Downloading", command=self.stop_continuous_download, state="disabled")
        self.stop_dl_button.grid(row=22, column=1, padx=20, pady=15, sticky="ew")

        # --- FILTER FIELDS (always create as attributes, even if tab is hidden) ---
        self.stage_name_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. debug-dns-issue")
        self.src_ip_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. 192.168.1.10")
        self.dest_ip_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. 8.8.8.8")
        self.src_port_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. 53")
        self.dest_port_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. 443")
        self.protocol_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. TCP")
        self.max_packets_entry = customtkinter.CTkEntry(self.main_frame, placeholder_text="e.g. 10000")

        # --- LOGGING TABS ---
        self.log_tabview = customtkinter.CTkTabview(self.main_frame, width=700, height=180)
        self.log_tabview.grid(row=102, column=0, columnspan=5, padx=10, pady=(10, 0), sticky="ew")
        self.summary_tab = self.log_tabview.add("Summary")
        self.advanced_tab = self.log_tabview.add("Advanced Log")
        self.summary_textbox = customtkinter.CTkTextbox(self.summary_tab, width=680, height=160, state="disabled")
        self.summary_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.advanced_textbox = customtkinter.CTkTextbox(self.advanced_tab, width=680, height=160, state="disabled")
        self.advanced_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self._downloaded_count = 0
        self._downloaded_errors = []
        self._downloaded_total = 0
        self._downloaded_expected = 0

        # Set default values
        self.api_handler = None
        self.load_settings()
        self.log_message("Welcome to the Palo Alto Packet Capture utility!")
        # Pre-fill fields if loaded
        if hasattr(self, 'last_ip') and self.last_ip:
            self.ip_entry.insert(0, self.last_ip)
        if hasattr(self, 'last_user') and self.last_user:
            self.user_entry.insert(0, self.last_user)

        # --- VALUE LABEL UPDATERS ---
    def update_minutes_label(self, value):
        self.minutes_value_label.configure(text=f"{int(float(value))} min")
    def update_seconds_label(self, value):
        self.seconds_value_label.configure(text=f"{int(float(value))} sec")

        # --- ABOUT DIALOG ---
    def show_about_dialog(self):
        import tkinter.messagebox
        tkinter.messagebox.showinfo("About", "Palo Alto PCAP Downloader\nModern GUI\nDeveloped by YourName\n2024")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                self.last_ip = data.get('ip')
                self.last_user = data.get('username')
        except Exception:
            self.last_ip = ''
            self.last_user = ''

    def save_settings(self, ip, username):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({'ip': ip, 'username': username}, f)
        except Exception as e:
            self.log_message(f"Warning: Could not save settings: {e}")

    def start_capture_event(self):
        self.log_message("Start Capture button clicked!")
        
        firewall_ip = self.ip_entry.get()
        username = self.user_entry.get()
        password = self.pass_entry.get()

        if not all([firewall_ip, username, password]):
            self.log_message("Error: Please fill in all firewall connection details.")
            return

        self.log_message(f"Attempting to connect to {firewall_ip}...")
        
        self.api_handler = PaloAltoAPI(firewall_ip, username, password)
        success, message = self.api_handler.connect()
        
        self.log_message(message)

        if not success:
            return

        # Save last used IP and username
        self.save_settings(firewall_ip, username)

        # Collect filter options
        stage_name = self.stage_name_entry.get()
        filters = {
            "src_ip": self.src_ip_entry.get(),
            "dest_ip": self.dest_ip_entry.get(),
            "src_port": self.src_port_entry.get(),
            "dest_port": self.dest_port_entry.get(),
            "protocol": self.protocol_entry.get(),
            "max_packets": self.max_packets_entry.get(),
        }
        success, message = self.api_handler.start_packet_capture(stage_name, filters)
        self.log_message(message)

    def stop_capture_event(self):
        self.log_message("Stop Capture button clicked!")
        if not self.api_handler:
            self.log_message("Error: Not connected to firewall.")
            return
        stage_name = self.stage_name_entry.get()
        success, message = self.api_handler.stop_packet_capture(stage_name)
        self.log_message(message)

    def download_capture_event(self):
        self.log_message("Download Capture button clicked!")
        if not self.api_handler:
            self.log_message("Error: Not connected to firewall.")
            return
        stage_name = self.stage_name_entry.get()
        # For now, save to current directory with a default filename
        save_path = f"{stage_name or 'capture'}.pcap"
        success, message = self.api_handler.download_packet_capture(stage_name, save_path)
        self.log_message(message)

    def log_message(self, message):
        # Log to advanced log tab
        if hasattr(self, 'advanced_textbox'):
            self.advanced_textbox.configure(state="normal")
            self.advanced_textbox.insert("end", message + "\n")
            self.advanced_textbox.configure(state="disabled")
            self.advanced_textbox.see("end")

    def browse_save_dir(self):
        import tkinter.filedialog
        dir_selected = tkinter.filedialog.askdirectory()
        if dir_selected:
            self.save_dir_entry.delete(0, "end")
            self.save_dir_entry.insert(0, dir_selected)

    def start_continuous_download(self):
        # Reset download counters for a fresh run
        self._downloaded_count = 0
        self._downloaded_errors = []
        self._downloaded_expected = 0
        self.log_message("Starting continuous download...")
        self.start_dl_button.configure(state="disabled")
        self.stop_dl_button.configure(state="normal")
        self._stop_download = threading.Event()
        self.progress_bar.set(0)
        # Gather settings
        firewall_ips = [ip.strip() for ip in self.ip_entry.get().split(',') if ip.strip()]
        username = self.user_entry.get()
        password = self.pass_entry.get()
        project_name = self.project_name_entry.get().strip() or "Project"
        save_dir = self.save_dir_entry.get().strip() or os.getcwd()
        try:
            count = int(self.count_entry.get())
        except Exception:
            self.log_message("Error: Invalid number of downloads.")
            self.start_dl_button.configure(state="normal")
            self.stop_dl_button.configure(state="disabled")
            return
        minutes = int(self.minutes_slider.get())
        seconds = int(self.seconds_slider.get())
        interval = minutes * 60 + seconds
        if interval < 0:
            self.log_message("Error: Interval must be at least 0 seconds.")
            self.start_dl_button.configure(state="normal")
            self.stop_dl_button.configure(state="disabled")
            return
        # Start a thread for each firewall
        self._firewall_threads = []
        for fw_ip in firewall_ips:
            t = threading.Thread(target=self._continuous_download_loop_multi_fw, args=(fw_ip, username, password, project_name, save_dir, count, interval), daemon=True)
            t.start()
            self._firewall_threads.append(t)

    def stop_continuous_download(self):
        self.log_message("Stopping continuous download...")
        if hasattr(self, '_stop_download'):
            self._stop_download.set()
        self.start_dl_button.configure(state="normal")
        self.stop_dl_button.configure(state="disabled")

    def _write_log(self, log_file, message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            self.log_message(f"Warning: Could not write to log file: {e}")

    # Make the progress bar green and update smoothly
    def _smooth_progress_bar(self, duration, stop_event):
        steps = int(duration * 20)  # 20 updates per second
        for j in range(steps):
            if stop_event.is_set():
                break
            self.progress_bar.set((j + 1) / steps)
            time.sleep(1 / 20)
        self.progress_bar.set(0)

    def _continuous_download_loop_multi_fw(self, firewall_ip, username, password, project_name, save_dir, count, interval):
        self._downloaded_expected += count * 3  # 3 files per download per firewall
        local_count = 0
        local_errors = []
        api_handler = PaloAltoAPI(firewall_ip, username, password)
        self.log_message(f"Connecting to {firewall_ip}...")
        success, message = api_handler.connect()
        self.log_message(f"{firewall_ip}: {message}")
        if not success:
            local_errors.append(f"{firewall_ip}: {message}")
            self._downloaded_errors.append(f"{firewall_ip}: {message}")
            self._update_summary()
            return
        log_file = os.path.join(save_dir, f"{project_name}_{firewall_ip}_download.log")
        for i in range(count):
            if self._stop_download.is_set():
                self.log_message(f"{firewall_ip}: Download stopped by user.")
                self._write_log(log_file, "Download stopped by user.")
                break
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filenames = {ftype: os.path.join(save_dir, f"{project_name}_{timestamp}_{firewall_ip}_{ftype}.pcap") for ftype in ["rx", "tx", "drp"]}
            threads = []
            results = {}
            def download_file(ftype):
                fw = getattr(api_handler, 'fw', None)
                if not api_handler or fw is None:
                    results[ftype] = (False, "Not connected to firewall.")
                    return
                api_key = fw.api_key
                hostname = api_handler.hostname
                fname = f"{ftype}.pcap"
                save_path = filenames[ftype]
                from api_handler import download_filtered_pcap
                success, msg = download_filtered_pcap(hostname, api_key, fname, save_path)
                results[ftype] = (success, msg)
            for ftype in ["rx", "tx", "drp"]:
                t = threading.Thread(target=download_file, args=(ftype,))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            for ftype in ["rx", "tx", "drp"]:
                success, msg = results.get(ftype, (False, "No result."))
                log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {firewall_ip} {ftype.upper()}: {msg}"
                self.log_message(log_entry)
                self._write_log(log_file, log_entry)
                if success:
                    self._downloaded_count += 1
                    local_count += 1
                else:
                    self._downloaded_errors.append(log_entry)
                    local_errors.append(log_entry)
                self._update_summary()
            if i < count - 1:
                stop_event = self._stop_download
                t = threading.Thread(target=self._smooth_progress_bar, args=(interval, stop_event))
                t.start()
                t.join()
        self.log_message(f"{firewall_ip}: Continuous download finished.")
        self._write_log(log_file, "Continuous download finished.")
        self.start_dl_button.configure(state="normal")
        self.stop_dl_button.configure(state="disabled")
        self._update_summary(final=True)

    def _update_summary(self, final=False):
        if not hasattr(self, 'summary_textbox'):
            return
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        self.summary_textbox.insert("end", f"Files downloaded so far: {self._downloaded_count} / {self._downloaded_expected}\n")
        if self._downloaded_errors:
            self.summary_textbox.insert("end", f"Errors so far: {len(self._downloaded_errors)}\n")
        if final:
            self.summary_textbox.insert("end", "\n--- SUMMARY ---\n")
            self.summary_textbox.insert("end", f"Total files downloaded: {self._downloaded_count}\n")
            if self._downloaded_errors:
                self.summary_textbox.insert("end", "Errors encountered:\n")
                for err in self._downloaded_errors:
                    self.summary_textbox.insert("end", err + "\n")
            else:
                self.summary_textbox.insert("end", "No errors encountered.\n")
        self.summary_textbox.configure(state="disabled")
        self.summary_textbox.see("end")

        # Move about-text to the bottom of the app, below the status log
        self.about_label = customtkinter.CTkLabel(self.main_frame, text="Palo Alto PCAP Downloader | Modern GUI | Developed by YourName 2024", font=customtkinter.CTkFont(size=12), text_color="#555")
        self.about_label.grid(row=200, column=0, columnspan=5, padx=10, pady=(10, 10), sticky="ew") 