"""
DVD Backup Tool (ISO or Folder)
Updated: includes explicit DRM/disclaimer and educational-use acknowledgement.

Save as: dvd_backup_with_disclaimer.py
Requires: psutil, tqdm
Install: pip install psutil tqdm

IMPORTANT: This program DOES NOT and WILL NOT bypass DRM/encryption (CSS, AACS, etc.).
It is intended for lawful, educational, and personal backup use only on discs you legally own.
"""

import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
from tqdm import tqdm

# ---------- Config ----------
READ_BLOCK = 1024 * 64  # 64 KB read blocks for raw copy
# ----------------------------

DISCLAIMER_TEXT = (
    "IMPORTANT: This tool DOES NOT bypass DRM/encryption (CSS, AACS, etc.).\n"
    "Do NOT use it to circumvent copy protection. Only use this software to back up or inspect\n"
    "discs that you own and are legally allowed to copy. This program is provided for\n"
    "educational and personal-use purposes only."
)


def list_dvd_drives():
    """Return list of candidate DVD drive paths (Windows like 'D:\\' or raw devices on Unix)."""
    drives = []
    for p in psutil.disk_partitions(all=False):
        try:
            opts = p.opts.lower() if p.opts else ""
        except Exception:
            opts = ""
        if 'cdrom' in opts or p.fstype == '':
            drives.append(p.device)
    # Add common unix device paths
    for candidate in ['/dev/sr0', '/dev/cdrom', '/dev/dvd', '/dev/disk2']:
        if candidate not in drives and os.path.exists(candidate):
            drives.append(candidate)
    # On Windows, include existing drive letters (best-effort)
    if os.name == 'nt':
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            p = f"{letter}:\\"
            if os.path.exists(p) and p not in drives:
                drives.append(p)
    if not drives:
        drives = ["No DVD drive found"]
    return drives


def build_raw_device_path(drive_path):
    """Convert a friendly drive path to raw device path for reading.
    Windows: 'D:\\' -> '\\\\\.\\D:' (requires admin)
    Unix-like: use provided device or common devices.
    """
    if os.name == 'nt':
        if isinstance(drive_path, str) and len(drive_path) >= 1:
            letter = drive_path[0].upper()
            return r"\\\\.\\%s:" % letter
        return drive_path
    else:
        if os.path.exists(drive_path) and drive_path.startswith("/dev"):
            return drive_path
        for cand in ['/dev/sr0', '/dev/cdrom', '/dev/dvd']:
            if os.path.exists(cand):
                return cand
        return drive_path


def raw_copy_to_iso(raw_device, iso_output_path, progress_callback=None):
    """Create a bit-for-bit ISO by reading the raw device.
    Note: raw reads often require elevated privileges (Administrator/root).
    """
    try:
        with open(raw_device, 'rb') as src, open(iso_output_path, 'wb') as dst:
            copied = 0
            total = None
            try:
                total = os.path.getsize(raw_device)
            except Exception:
                total = None
            while True:
                buf = src.read(READ_BLOCK)
                if not buf:
                    break
                dst.write(buf)
                copied += len(buf)
                if progress_callback:
                    progress_callback(copied, total)
        return True, None
    except PermissionError as e:
        return False, f"Permission denied reading raw device. Try running as administrator/root. ({e})"
    except FileNotFoundError as e:
        return False, f"Raw device not found: {raw_device}. ({e})"
    except Exception as e:
        return False, f"Raw copy failed: {e}"


def copy_folder_contents(drive_mount_point, dest_dir, progress_callback=None):
    """Copy all files and folders from mount point to destination."""
    all_files = []
    for root, _, files in os.walk(drive_mount_point):
        for f in files:
            all_files.append(os.path.join(root, f))
    total = len(all_files)
    copied = 0
    for src in all_files:
        rel = os.path.relpath(src, drive_mount_point)
        dst = os.path.join(dest_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            print(f"Warning: failed to copy {src}: {e}")
        copied += 1
        if progress_callback:
            progress_callback(copied, total)
    return True, None


class DVDBackupApp:
    def __init__(self, root):
        self.root = root
        root.title("DVD Backup (ISO or Folder) — Educational Use")
        root.geometry("640x420")
        root.resizable(False, False)

        ttk.Label(root, text="DVD Backup Tool", font=("Segoe UI", 16, "bold")).pack(pady=8)

        # Disclaimer box (readonly Text) so user can read long message
        disclaimer_frame = ttk.Frame(root)
        disclaimer_frame.pack(padx=12, pady=6, fill='x')

        lbl = ttk.Label(disclaimer_frame, text="Disclaimer:")
        lbl.pack(anchor='w')

        self.disc_text = tk.Text(disclaimer_frame, height=4, wrap='word', padx=6, pady=6)
        self.disc_text.insert('1.0', DISCLAIMER_TEXT)
        self.disc_text.config(state='disabled')
        self.disc_text.pack(fill='x')

        # Acknowledge checkbox - must be checked to enable actions
        self.ack_var = tk.IntVar(value=0)
        ack_frame = ttk.Frame(root)
        ack_frame.pack(padx=12, pady=6, fill='x')
        self.ack_check = ttk.Checkbutton(ack_frame, text="I have read the disclaimer and will use this tool lawfully (educational/personal backup)", variable=self.ack_var, command=self._on_ack_change)
        self.ack_check.pack(anchor='w')

        # Drive selection
        ttk.Label(root, text="Select DVD drive:").pack(pady=(10, 0))
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(root, textvariable=self.drive_var, state="readonly", width=64)
        self.drive_combo.pack(pady=6)
        ttk.Button(root, text="Refresh drives", command=self.refresh_drives).pack()

        # Action buttons (disabled until ack)
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=12)

        self.iso_btn = ttk.Button(btn_frame, text="Create ISO (bit-for-bit)", command=self.create_iso, state='disabled')
        self.iso_btn.grid(row=0, column=0, padx=8)
        self.folder_btn = ttk.Button(btn_frame, text="Copy as Folder (files)", command=self.copy_as_folder, state='disabled')
        self.folder_btn.grid(row=0, column=1, padx=8)

        # Progress and status
        self.progress = ttk.Progressbar(root, length=600, mode="determinate")
        self.progress.pack(pady=12)
        self.status_label = ttk.Label(root, text="", foreground="blue")
        self.status_label.pack()

        # Menu with disclaimer/help
        menubar = tk.Menu(root)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="View Disclaimer", command=self.show_disclaimer)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        root.config(menu=menubar)

        self.refresh_drives()

    def _on_ack_change(self):
        enabled = self.ack_var.get() == 1
        self.iso_btn.config(state='normal' if enabled else 'disabled')
        self.folder_btn.config(state='normal' if enabled else 'disabled')

    def show_disclaimer(self):
        messagebox.showinfo("Disclaimer", DISCLAIMER_TEXT)

    def show_about(self):
        messagebox.showinfo("About", "DVD Backup Tool — educational/personal backup only.\nDoes NOT bypass DRM.")

    def refresh_drives(self):
        drives = list_dvd_drives()
        self.drive_combo['values'] = drives
        if drives:
            self.drive_combo.current(0)

    def update_progress(self, done, total):
        if total and total > 0:
            try:
                self.progress['maximum'] = total
                self.progress['value'] = done
            except Exception:
                pass
            frac = done / total
            pct = int(frac * 100)
            self.status_label.config(text=f"Progress: {pct}% ({done}/{total} bytes or files)")
        else:
            # Unknown total: show bytes/files copied as a running text
            self.status_label.config(text=f"Copied {done} bytes/files (total unknown)")

    def create_iso(self):
        if self.ack_var.get() != 1:
            messagebox.showwarning("Acknowledge disclaimer", "Please read and acknowledge the disclaimer before proceeding.")
            return
        drive = self.drive_var.get()
        if not drive or drive == "No DVD drive found":
            messagebox.showerror("No drive", "No DVD drive found. Please insert a disc and refresh drives.")
            return

        out_file = filedialog.asksaveasfilename(defaultextension=".iso", filetypes=[("ISO image","*.iso")], title="Save ISO as")
        if not out_file:
            return

        raw_device = build_raw_device_path(drive)
        confirm = messagebox.askyesno("Confirm", "Creating an ISO may require administrator/root privileges.\n\nProceed?")
        if not confirm:
            return

        self.progress['mode'] = 'determinate'
        self.progress['value'] = 0
        self.status_label.config(text="Starting ISO creation...")

        def worker():
            def progress_cb(done, total):
                self.root.after(0, self.update_progress, done, total if total else None)

            ok, err = raw_copy_to_iso(raw_device, out_file, progress_callback=progress_cb)
            if ok:
                self.root.after(0, lambda: messagebox.showinfo("Done", f"ISO created successfully:\n{out_file}"))
                self.root.after(0, lambda: self.status_label.config(text="ISO creation completed."))
            else:
                self.root.after(0, lambda: messagebox.showerror("Failed", f"ISO creation failed:\n{err}\n\nYou can try 'Copy as Folder' instead."))
                self.root.after(0, lambda: self.status_label.config(text="ISO creation failed."))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def copy_as_folder(self):
        if self.ack_var.get() != 1:
            messagebox.showwarning("Acknowledge disclaimer", "Please read and acknowledge the disclaimer before proceeding.")
            return
        drive = self.drive_var.get()
        if not drive or drive == "No DVD drive found":
            messagebox.showerror("No drive", "No DVD drive found. Please insert a disc and refresh drives.")
            return
        dest = filedialog.askdirectory(title="Select destination folder for DVD contents")
        if not dest:
            return
        self.progress['mode'] = 'determinate'
        self.progress['value'] = 0
        self.status_label.config(text="Starting folder copy...")

        def worker():
            def progress_cb(done, total):
                self.root.after(0, self.update_progress, done, total)

            ok, err = copy_folder_contents(drive, dest, progress_callback=progress_cb)
            if ok:
                self.root.after(0, lambda: messagebox.showinfo("Done", f"Files copied to:\n{dest}"))
                self.root.after(0, lambda: self.status_label.config(text="Folder copy completed."))
            else:
                self.root.after(0, lambda: messagebox.showerror("Failed", f"Folder copy failed:\n{err}"))
                self.root.after(0, lambda: self.status_label.config(text="Folder copy failed."))

        t = threading.Thread(target=worker, daemon=True)
        t.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DVDBackupApp(root)
    root.mainloop()
