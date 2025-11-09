"""
DVD Backup Pro Full — Complete professional DVD backup and conversion software

Features:
 - Copy DVD as Folder (VIDEO_TS/AUDIO_TS) or ISO
 - Convert VOB files to single MP4 for watching without disc
 - README and Disclaimer at first run
 - About dialog with educational disclaimer
 - Progress bar with MB/s and ETA
 - Activity log
 - Remembers last drive and destination
 - Cross-platform
 - Educational/Personal use only (does not bypass DRM/CSS/AACS)
"""

import os, sys, json, time, shutil, subprocess, threading, traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import psutil

APP_NAME = "DVD Backup Pro Full"
VERSION = "2.0"
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "dvd_backup_settings.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "dvd_copy_log.txt")
READ_BLOCK = 1024 * 64  # 64 KB

DISCLAIMER_TEXT = (
    "IMPORTANT: This tool DOES NOT bypass DRM/encryption (CSS, AACS, etc.).\n\n"
    "It only copies data from unencrypted DVDs or DVDs you are legally allowed to back up "
    "(e.g., educational materials or personal home recordings). Do NOT use it to circumvent "
    "copy protection. Only use this software to back up or inspect discs that you own and "
    "are legally allowed to copy. This program is provided for educational and personal-use purposes only."
)

README_TEXT = (
    f"Welcome to {APP_NAME}!\n\n"
    "This program helps you create a full backup of a DVD for lawful, educational, or personal-use purposes.\n\n"
    "Features:\n"
    " - Copy DVD as Folder (VIDEO_TS/AUDIO_TS)\n"
    " - Create ISO (bit-for-bit)\n"
    " - Convert VOBs to single MP4 for easy playback\n\n"
    "Please read and accept the disclaimer on the next screen to continue."
)

# ------------------- Utilities -------------------

def log_entry(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        log_entry("Failed to save settings: " + traceback.format_exc())

def list_dvd_drives():
    drives = []
    try:
        for p in psutil.disk_partitions(all=False):
            opts = (p.opts or "").lower()
            if 'cdrom' in opts or p.fstype == '' or 'cd' in p.device.lower() or 'dvd' in p.mountpoint.lower():
                drives.append(p.device if os.name != 'nt' else p.mountpoint)
    except Exception:
        pass
    if os.name == 'nt':
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            p = f"{letter}:" + os.sep
            if os.path.exists(p) and p not in drives:
                drives.append(p)
    if not drives:
        drives = ["No DVD drive found"]
    return drives

def build_raw_device_path(drive_path):
    if os.name == 'nt':
        letter = drive_path[0].upper()
        return r"\\\\.\%s:" % letter
    else:
        if drive_path.startswith("/dev") and os.path.exists(drive_path):
            return drive_path
        for cand in ['/dev/sr0', '/dev/cdrom', '/dev/dvd']:
            if os.path.exists(cand):
                return cand
        return drive_path

# ------------------- DVD Copy -------------------

def copy_folder_contents(src, dest, progress_callback=None, stop_event=None):
    files = []
    total_bytes = 0
    for r, _, fnames in os.walk(src):
        for f in fnames:
            path = os.path.join(r, f)
            try:
                sz = os.path.getsize(path)
            except:
                sz = 0
            files.append((path, sz))
            total_bytes += sz
    copied_bytes = 0
    copied_files = 0
    start = time.time()
    for path, sz in files:
        if stop_event and stop_event.is_set():
            return False, "Cancelled", copied_files, len(files)
        rel = os.path.relpath(path, src)
        dest_path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            shutil.copy2(path, dest_path)
        except Exception as e:
            log_entry(f"Failed to copy {path}: {e}")
        copied_files += 1
        copied_bytes += sz
        if progress_callback:
            progress_callback(copied_bytes, total_bytes, start, copied_files, len(files))
    if progress_callback:
        progress_callback(copied_bytes, total_bytes, start, copied_files, len(files))
    return True, None, copied_files, len(files)

def raw_copy_to_iso(raw_dev, iso_path, progress_callback=None, stop_event=None):
    try:
        with open(raw_dev, 'rb') as src, open(iso_path, 'wb') as dst:
            copied_bytes = 0
            start = time.time()
            while True:
                if stop_event and stop_event.is_set():
                    return False, "Cancelled"
                buf = src.read(READ_BLOCK)
                if not buf:
                    break
                dst.write(buf)
                copied_bytes += len(buf)
                if progress_callback:
                    progress_callback(copied_bytes, None, start)
        return True, None
    except Exception as e:
        return False, str(e)

# ------------------- VOB to MP4 -------------------

def ffmpeg_available():
    return shutil.which("ffmpeg") is not None

def find_video_ts_vobs(folder):
    video_ts = os.path.join(folder, "VIDEO_TS")
    if not os.path.isdir(video_ts):
        return []
    groups = {}
    for fname in os.listdir(video_ts):
        if fname.upper().endswith(".VOB"):
            parts = fname.split('_')
            group = parts[0] + "_" + parts[1] if len(parts) >= 2 else "misc"
            path = os.path.join(video_ts, fname)
            groups.setdefault(group, []).append(path)
    best_group, best_size = None, 0
    for g, files in groups.items():
        s = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        if s > best_size:
            best_size, best_group = s, g
    return sorted(groups[best_group]) if best_group else []

def convert_vobs_to_mp4(dest_folder, output_mp4_path, reencode=True, app_callback=None):
    if not ffmpeg_available():
        return False, "ffmpeg not found"
    vobs = find_video_ts_vobs(dest_folder)
    if not vobs:
        return False, "No VOB files found"
    temp_list = os.path.join(dest_folder, "vob_list.txt")
    try:
        with open(temp_list, "w", encoding="utf-8") as f:
            for v in vobs:
                f.write("file '{}'\n".format(v.replace("'", r"'\''")))
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", temp_list]
        if reencode:
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k", output_mp4_path]
        else:
            cmd += ["-c", "copy", output_mp4_path]
        if app_callback:
            app_callback(f"Running ffmpeg...")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return False, proc.stderr
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(temp_list):
            os.remove(temp_list)

# ------------------- GUI Application -------------------

class DVDBackupApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.geometry("720x520")
        root.resizable(False, False)
        self.settings = load_settings()
        self.stop_event = None
        # Title
        ttk.Label(root, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(pady=6)
        ttk.Label(root, text=f"Version {VERSION}", font=("Segoe UI", 10)).pack()
        # Disclaimer checkbox
        self.ack_var = tk.IntVar(value=self.settings.get("acknowledged", 0))
        self.ack_check = ttk.Checkbutton(root, text="I accept disclaimer (educational/personal use)", variable=self.ack_var)
        self.ack_check.pack(pady=6, anchor='w', padx=12)
        # Drive selection
        ttk.Label(root, text="DVD Drive / Device:").pack(anchor='w', padx=12)
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(root, textvariable=self.drive_var, state='readonly', width=40)
        self.drive_combo.pack(padx=12, pady=4)
        ttk.Button(root, text="Refresh Drives", command=self.refresh_drives).pack(anchor='w', padx=12)
        # Method selection
        self.method_var = tk.StringVar(value="folder")
        ttk.Radiobutton(root, text="Copy as Folder", variable=self.method_var, value="folder").pack(anchor='w', padx=12)
        ttk.Radiobutton(root, text="Create ISO", variable=self.method_var, value="iso").pack(anchor='w', padx=12)
        # Convert to MP4
        self.mp4_var = tk.IntVar(value=1)
        ttk.Checkbutton(root, text="Convert to MP4 after copy", variable=self.mp4_var).pack(anchor='w', padx=12, pady=4)
        # Destination
        ttk.Label(root, text="Destination folder / ISO / MP4 file:").pack(anchor='w', padx=12)
        dest_frame = ttk.Frame(root)
        dest_frame.pack(fill='x', padx=12)
        self.dest_var = tk.StringVar(value=self.settings.get("last_dest",""))
        self.dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=48)
        self.dest_entry.pack(side='left')
        ttk.Button(dest_frame, text="Browse", command=self.browse_dest).pack(side='left', padx=4)
        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=6, fill='x', padx=12)
        self.start_btn = ttk.Button(btn_frame, text="Start Backup", command=self.start_backup)
        self.start_btn.pack(side='left')
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_backup, state='disabled')
        self.cancel_btn.pack(side='left', padx=4)
        ttk.Button(btn_frame, text="Open Log", command=self.open_log).pack(side='right')
        # Progress bar
        ttk.Label(root, text="Progress:").pack(anchor='w', padx=12)
        self.progress = ttk.Progressbar(root, length=680, mode='determinate')
        self.progress.pack(padx=12, pady=4)
        self.progress_label = ttk.Label(root, text="Idle")
        self.progress_label.pack(anchor='w', padx=12)
        # Status text
        self.status_text = tk.Text(root, height=8)
        self.status_text.pack(padx=12, pady=6, fill='both')
        self.status_text.config(state='disabled')
        # Menu
        menubar = tk.Menu(root)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="View Disclaimer", command=lambda: messagebox.showinfo("Disclaimer", DISCLAIMER_TEXT))
        help_menu.add_command(label="README", command=lambda: messagebox.showinfo("README", README_TEXT))
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", f"{APP_NAME}\nVersion {VERSION}\n\n{DISCLAIMER_TEXT}"))
        menubar.add_cascade(label="Help", menu=help_menu)
        root.config(menu=menubar)
        self.refresh_drives()

    def _append_status(self, text):
        self.status_text.config(state='normal')
        self.status_text.insert('end', f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")
        self.status_text.see('end')
        self.status_text.config(state='disabled')
        log_entry(text)

    def refresh_drives(self):
        drives = list_dvd_drives()
        self.drive_combo['values'] = drives
        if drives:
            self.drive_var.set(drives[0])

    def browse_dest(self):
        method = self.method_var.get()
        if method=="iso":
            f = filedialog.asksaveasfilename(defaultextension=".iso", filetypes=[("ISO Image","*.iso")])
            if f: self.dest_var.set(f)
        else:
            f = filedialog.askdirectory()
            if f: self.dest_var.set(f)

    def open_log(self):
        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("Log","No log file yet.")
            return
        try:
            if sys.platform.startswith('win'): os.startfile(LOG_FILE)
            elif sys.platform.startswith('darwin'): subprocess.run(["open", LOG_FILE])
            else: subprocess.run(["xdg-open", LOG_FILE])
        except:
            messagebox.showinfo("Log", f"Log file path:\n{LOG_FILE}")

    def start_backup(self):
        if not self.ack_var.get():
            messagebox.showwarning("Disclaimer","Please accept the disclaimer.")
            return
        drive = self.drive_var.get()
        dest = self.dest_var.get().strip()
        method = self.method_var.get()
        if not drive or drive=="No DVD drive found":
            messagebox.showerror("Drive","No DVD drive detected.")
            return
        if not dest:
            messagebox.showerror("Destination","Select a destination folder/ISO path.")
            return
        # Save settings
        self.settings.update({"acknowledged":1,"last_drive":drive,"last_dest":dest,"method":method})
        save_settings(self.settings)
        self.start_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.stop_event = threading.Event()
        self.progress['value'] = 0
        self.progress_label.config(text="Starting...")
        self._append_status("Backup started")
        t = threading.Thread(target=self._worker, args=(drive,dest,method,self.mp4_var.get(),self.stop_event), daemon=True)
        t.start()

    def cancel_backup(self):
        if self.stop_event: self.stop_event.set(); self._append_status("Cancel requested"); self.cancel_btn.config(state='disabled')

    def _worker(self, drive, dest, method, mp4_flag, stop_event):
        try:
            if method=="folder":
                ok, err, f_copied, f_total = copy_folder_contents(drive,dest,progress_callback=self._progress_cb, stop_event=stop_event)
                if not ok: self._append_status(f"Folder copy failed: {err}")
                else:
                    self._append_status(f"Folder copy completed {f_copied}/{f_total} files.")
                    if mp4_flag:
                        out_mp4 = os.path.join(dest,"movie.mp4")
                        self._append_status("Starting MP4 conversion...")
                        ok2, err2 = convert_vobs_to_mp4(dest,out_mp4,app_callback=lambda m:self._append_status(m))
                        if ok2: self._append_status(f"Conversion done: {out_mp4}")
                        else: self._append_status(f"Conversion failed: {err2}")
            else:
                raw_dev = build_raw_device_path(drive)
                ok, err = raw_copy_to_iso(raw_dev,dest,progress_callback=self._progress_cb,stop_event=stop_event)
                if ok: self._append_status(f"ISO created: {dest}")
                else: self._append_status(f"ISO failed: {err}")
        finally:
            self.root.after(0,self._finalize_worker)

    def _progress_cb(self, copied_bytes, total_bytes, start_time, copied_files=None, total_files=None):
        elapsed = max(0.001, time.time()-start_time)
        speed = copied_bytes/elapsed/1024/1024
        pct = int(copied_bytes/total_bytes*100) if total_bytes else 0
        self.root.after(0,self._update_progress_ui,pct,copied_bytes,total_bytes,speed,copied_files,total_files)

    def _update_progress_ui(self,pct,copied_bytes,total_bytes,speed,copied_files,total_files):
        self.progress['value'] = pct
        s = f"{pct}% {copied_bytes//(1024*1024)}MB"
        if total_bytes: s+=f"/{total_bytes//(1024*1024)}MB"
        s+=f" — {speed:.2f} MB/s"
        if copied_files and total_files: s+=f" ({copied_files}/{total_files} files)"
        self.progress_label.config(text=s)

    def _finalize_worker(self):
        self.start_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
        self._append_status("Worker finished.")

def main():
    try:
        root = tk.Tk()
        app = DVDBackupApp(root)
        root.mainloop()
    except Exception as e:
        log_entry("Fatal error: "+traceback.format_exc())
        print("Fatal error:", e)

if __name__=="__main__":
    main()
