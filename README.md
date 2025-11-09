# DVD Backup

A professional Python tool to copy DVDs to folders or ISO, and convert VOBs to MP4 (educational/personal use).

**Disclaimer:** This tool **DOES NOT bypass DRM (CSS/AACS)**. Use only on DVDs you legally own and are allowed to back up, including educational materials, personal recordings, or public domain content. This software is intended for **educational and personal-use purposes only**.

---

## Features

- Copy DVD as Folder (VIDEO_TS)
- Create ISO Image
- Convert VOBs to MP4
- GUI with progress bars, file counts, and speed
- Activity logging
- Cross-platform (Windows/macOS/Linux)
- Cancel backup operations
- Settings persistence
- Built-in Help Menu

---

## Requirements

- Python 3.11+
- ffmpeg installed and added to PATH
- Python packages: psutil, tqdm

### Install dependencies:

```bash
python -m pip install psutil tqdm
```
---
## How to Use
Open Python:

You can use IDLE, VS Code, PyCharm, or Command Prompt.

Run the script:

Navigate to the folder containing your Python script:

cd C:\Users\YourName\Documents\DVD_Backup
python dvd_backup_pro_full.py


GUI Overview:

Show Disclaimer: Click to read the legal disclaimer about DRM.

Select DVD Drive: Choose the drive containing your DVD.

Select Destination Folder: Pick where the backup will be saved.

Start Backup: Begin copying the DVD.

Progress Bar and Status: Monitor progress in the GUI.

Stop/Cancel: You can stop backup at any time.

Backup Options:

Copy DVD as Folder (VIDEO_TS): Copies the entire DVD structure.

Create ISO: Make a complete, bit-for-bit ISO image of the DVD.

Convert to MP4: (Optional) Converts DVD video files (VOB) into a single MP4 file.

Check Logs:

All activity is logged in dvd_copy_log.txt for troubleshooting.
---
## Using Without Python (EXE version)
If you want to use the AutoTyper without installing Python, you can convert the script to a standalone executable using **PyInstaller**.

## 1. Convert Your Script to EXE
1. Open Command Prompt
2. Navigate to your project folder:
```bash
cd C:\Users\YourName\Documents\AutoTyper
```
3. Run PyInstaller:
```bash
pyinstaller --onefile --windowed auto_typer.py
```
**Explanation of options:**

**--onefile** → Packages everything into a single ''**.exe**'' file.

**--windowed** → Hides the console window (good for GUI apps).

---
## 2. Locate the EXE

After conversion, check the `dist` folder inside your project folder.  
You will see `auto_typer.exe`.  

---

## 3. Share or Use the EXE

- You can now **share `auto_typer.exe`** with anyone.  
- They don’t need Python installed.  
- Double-clicking the EXE will open the GUI.  

---

If you want, I can **merge this into your full GitHub README** with all sections, including:

- Python usage  
- EXE usage  
- How to run  
- Notes & license  

So your README is **complete and ready to upload**.
