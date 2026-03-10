#server_app.py
import os
import socket
import threading
import http.server
import socketserver
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageDraw
import qrcode
import subprocess
import time
import sys
from functools import partial  # STEP 3: Required for the partial handler fix

ctk.set_appearance_mode("Dark")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Global debug logger to help catch EXE crashes
def debug_to_file(message):
    try:
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        log_path = os.path.join(desktop, "netshare_debug.txt")
        with open(log_path, "a") as f:
            f.write(f"[{time.ctime()}] {message}\n")
    except:
        pass


class LoggingHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        path = self.translate_path(self.path)
        self.file_to_track = path if os.path.isfile(path) else None
        return super().do_GET()

    def copyfile(self, source, outputfile):
        if hasattr(source, 'fileno') or self.file_to_track:
            try:
                file_path = self.file_to_track if self.file_to_track else source.name
                file_size = os.path.getsize(file_path)
                file_name = os.path.basename(file_path)

                start_time = time.time()
                bytes_sent = 0
                chunk_size = 512 * 1024

                row = app.add_history_row(file_name, file_size)

                while True:
                    buf = source.read(chunk_size)
                    if not buf:
                        break

                    outputfile.write(buf)
                    outputfile.flush()
                    bytes_sent += len(buf)

                    elapsed = time.time() - start_time
                    progress = bytes_sent / file_size if file_size > 0 else 1
                    speed = (bytes_sent / 1024 / 1024) / elapsed if elapsed > 0 else 0

                    app.after(1, lambda p=progress, s=speed: row.update_progress(p, s))

                total_time = time.time() - start_time
                app.after(1, lambda t=total_time: row.complete(t))
                return

            except Exception as e:
                debug_to_file(f"Transfer Error: {str(e)}")

        super().copyfile(source, outputfile)


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class TransferRow(ctk.CTkFrame):

    def __init__(self, master, name, size):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", padx=10, pady=10)

        size_mb = size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb > 0.1 else f"{size/1024:.1f} KB"

        self.info_label = ctk.CTkLabel(
            self,
            text=f"{name[:20]:<20} | {size_str:>10} | Calculating...",
            font=("Consolas", 11),
            text_color="#eeeeee"
        )
        self.info_label.pack(side="top", anchor="w", padx=5)

        self.pbar = ctk.CTkProgressBar(
            self,
            height=6,
            progress_color="#2ecc71",
            fg_color="#1e1e1e"
        )
        self.pbar.set(0)
        self.pbar.pack(fill="x", padx=5, pady=8)

        self.status_label = ctk.CTkLabel(
            self,
            text="Transferring...",
            font=("Arial", 10, "bold"),
            text_color="#aaaaaa"
        )
        self.status_label.pack(side="left", padx=5)

        self.name = name
        self.size_str = size_str

    def update_progress(self, progress, speed):
        self.pbar.set(progress)
        self.status_label.configure(text=f"Speed: {speed:.2f} MB/s")

    def complete(self, total_time):
        self.pbar.set(1.0)
        time_ms = total_time * 1000
        time_str = f"{time_ms:.2f}s" if time_ms > 1000 else f"{time_ms:.0f}ms"
        self.info_label.configure(
            text=f"{self.name[:20]:<20} | {self.size_str:>10} | {time_str:>10}"
        )
        self.status_label.configure(text="COMPLETED ✓", text_color="#2ecc71")


class FileSharingApp(ctk.CTk):

    def on_close(self):
        self.stop_server()
        self.destroy()

    def port_in_use(self, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    def __init__(self):
        super().__init__()
        self.title("Local NetShare Pro")
        self.geometry("1100x750")
        self.configure(fg_color="#0f111a")

        self.httpd = None
        self.server_thread = None
        self.selected_path = ""

        self.top_label = ctk.CTkLabel(
            self,
            text="CONNECT BOTH DEVICES TO THE SAME WIFI ",
            font=ctk.CTkFont(size=14, weight="bold", slant="italic"),
            text_color="#3a7ebf"
        )
        self.top_label.pack(pady=(20, 10))

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(expand=True, fill="both", padx=20, pady=10)

        card_kwargs = {
            "fg_color": "#161922",
            "corner_radius": 15,
            "border_width": 1,
            "border_color": "#1f222c"
        }

        # WIFI CARD
        self.wifi_card = ctk.CTkFrame(self.main_container, **card_kwargs)
        self.wifi_card.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.wifi_card, text="Windows WiFi ", font=("Arial", 16, "bold", "italic")).pack(pady=(20, 10))
        self.ssid_entry = ctk.CTkEntry(self.wifi_card, placeholder_text="WiFi Name", width=200, fg_color="#0f111a", border_color="#2a2e3a")
        self.ssid_entry.pack(pady=5)
        ctk.CTkButton(self.wifi_card, text="Fetch Current SSID", width=140, height=28, fg_color="#3a7ebf", command=self.get_current_ssid).pack(pady=5)
        self.pw_entry = ctk.CTkEntry(self.wifi_card, placeholder_text="Password", show="*", width=200, fg_color="#0f111a", border_color="#2a2e3a")
        self.pw_entry.pack(pady=5)
        ctk.CTkButton(self.wifi_card, text="Generate WIFI QR", width=140, height=28, fg_color="#3a7ebf", command=self.generate_wifi_qr).pack(pady=10)
        self.wifi_qr_display = ctk.CTkLabel(self.wifi_card, text="")
        self.wifi_qr_display.pack(side="bottom", pady=(0, 50))

        # SERVER CARD
        self.server_card = ctk.CTkFrame(self.main_container, **card_kwargs)
        self.server_card.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.server_card, text="Share Files ", font=("Arial", 16, "bold", "italic")).pack(pady=(20, 10))
        ctk.CTkButton(self.server_card, text="Select Files/Folder", width=140, height=32, fg_color="#3a7ebf", command=self.select_folder).pack(pady=5)
        self.start_btn = ctk.CTkButton(self.server_card, text="Start Server", width=140, height=32, fg_color="#2ecc71", hover_color="#27ae60", command=self.start_server)
        self.start_btn.pack(pady=5)
        self.stop_btn = ctk.CTkButton(self.server_card, text="Stop Server", width=140, height=32, fg_color="#e74c3c", hover_color="#c0392b", command=self.stop_server, state="disabled")
        self.stop_btn.pack(pady=5)
        self.server_qr_display = ctk.CTkLabel(self.server_card, text="")
        self.server_qr_display.pack(side="bottom", pady=(0, 50))

        # STATUS CARD
        self.status_card = ctk.CTkFrame(self.main_container, **card_kwargs)
        self.status_card.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.status_card, text="Transfer Status ", font=("Arial", 16, "bold", "italic")).pack(pady=20)
        self.scroll_frame = ctk.CTkScrollableFrame(self.status_card, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.console = ctk.CTkTextbox(self, height=80, fg_color="#0f111a", text_color="#2ecc71", font=("Consolas", 11), border_width=1, border_color="#1f222c")
        self.console.pack(fill="x", padx=30, pady=(10, 20))

        self.update_log(">>> System Initialized. Ready to share.\n")
        debug_to_file("App Started Successfully")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def run_http_server(self):
        try:
            # STEP 3: Replace lambda with partial for PyInstaller stability
            handler = partial(LoggingHandler, directory=self.selected_path)
            self.httpd = ReusableTCPServer(("0.0.0.0", 54321), handler)
            
            # STEP 4: Add debug log
            self.update_log("Server thread started\n")
            
            self.httpd.serve_forever()
        except Exception as e:
            debug_to_file(f"Server thread crash: {e}")
            self.update_log(f"Thread Error: {e}\n")

    def start_server(self):
        if self.httpd is not None:
            self.update_log("Error: Server already running on port 54321\n")
            return
        if not self.selected_path:
            self.update_log("Error: Please select a folder first!\n")
            return

        try:
            self.server_thread = threading.Thread(
                target=self.run_http_server,
                daemon=True
            )
            self.server_thread.start()

            ip = self.get_ip()
            url = f"http://{ip}:54321"
            self.render_qr(url, self.server_qr_display)
            self.update_log(f"SUCCESS: Server Live!\nURL: {url}\n")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        except Exception as e:
            self.update_log(f"Server Error: {e}\n")
            debug_to_file(f"Server start failed: {e}")

    def stop_server(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except:
                pass
            self.httpd = None
            self.server_thread = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.update_log("Server Stopped.\n")

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.selected_path = path
            self.update_log(f"Folder Linked: {path}\n")

    def get_current_ssid(self):
        try:
            results = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"]
            ).decode("utf-8", errors="ignore")
            for line in results.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    name = line.split(":")[1].strip()
                    self.ssid_entry.delete(0, "end")
                    self.ssid_entry.insert(0, name)
                    return
        except:
            pass

    def generate_wifi_qr(self):
        ssid = self.ssid_entry.get()
        pw = self.pw_entry.get()
        if ssid:
            self.render_qr(f"WIFI:T:WPA;S:{ssid};P:{pw};;", self.wifi_qr_display)

    def add_history_row(self, name, size):
        return TransferRow(self.scroll_frame, name, size)

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return socket.gethostbyname(socket.gethostname())

    def render_qr(self, data, label_widget):
        qr = qrcode.QRCode(box_size=15, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(
            fill_color="black",
            back_color="white"
        ).convert("RGBA")
        ctk_img = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(180, 180)
        )
        label_widget.configure(image=ctk_img, text="")

    def update_log(self, msg):
        self.console.configure(state="normal")
        self.console.insert("end", msg)
        self.console.see("end")
        self.console.configure(state="disabled")


if __name__ == "__main__":
    app = FileSharingApp()
    app.mainloop()