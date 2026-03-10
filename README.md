# 📡 NetShare Pro — Local WiFi File Sharing (Single-EXE Architecture)

NetShare Pro is a **lightweight local network file sharing application** that lets users instantly share files and folders between devices connected to the same WiFi network. The application runs entirely from **one executable file**, combining the graphical interface and HTTP file server into a single program.

---

## 🚀 Key Highlights

* **Single-EXE Distribution**: Everything runs inside one executable. No additional files required.
* **Local WiFi File Sharing**: Share movies, documents, and folders directly over the local network without uploading to the internet.
* **QR Code Access**: Devices can instantly open the download page by scanning the generated QR code.
* **Multi-Device Downloads**: Multiple phones, tablets, or laptops can download files simultaneously.
* **Real-Time Transfer Monitoring**: Displays progress bars, transfer speed, and completion time for every download.

---

## 🏗️ Architecture

This version uses a **single-process threaded architecture** where both the GUI and HTTP file server run inside the same application.

* **GUI Application** → Built with CustomTkinter.
* **Embedded HTTP Server** → Runs as a background thread using `ThreadingTCPServer`.
* **Transfer Handler** → Tracks download progress and updates the GUI in real time.

This design removes the need for an external backend server and simplifies distribution.

---

## 🛠️ Tech Stack

* **Language**: Python 3.12  
* **GUI Framework**: CustomTkinter  
* **Networking**: http.server + socketserver.ThreadingTCPServer  
* **QR Code Generation**: qrcode  
* **Image Processing**: Pillow (PIL)  
* **Packaging**: PyInstaller

---

## 🌐 Network Port

* **54321** → HTTP File Server

---

## 💻 How to Run Locally

1. **Launch the Application**: `NetShare.exe`
2. **Select Files or Folder**: Choose the content you want to share.
3. **Start Server**: Click **Start Server** to begin sharing.
4. **Scan QR Code**: Use another device to scan the generated QR code.
5. **Download Files**: Access files through the browser and download instantly.

---

## 📁 Project Structure

```
NetShare-Pro
│
├── server_app.py
├── NetShare.exe
└── README.md
```

---

## ⚡ Advantages of Single-EXE Version

* Easier distribution
* No dependency on external executables
* Faster server startup
* Cleaner architecture
* Reduced risk of missing files during installation

---


## ⭐ Future Improvements

* Custom mobile-optimized download page  
* Drag-and-drop file sharing  
* Multiple file selection support  
* Upload feature (phone → PC)  
* Browser download progress display
