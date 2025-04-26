# ETS2 Modern Mod Manager (Threaded + Status Updates + Proper Extraction + Version Detection from Filename + 7z Support)
# Author: ChatGPT & You 🚛

import os
import shutil
import threading
import customtkinter as ctk
import zipfile
import subprocess
import patoolib
from tkinter import filedialog, messagebox
from PIL import Image
import webbrowser
import re
import sys

ETS2_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'Euro Truck Simulator 2')
ETS2_MOD_FOLDER = os.path.join(ETS2_FOLDER, 'mod')
GAME_LOG_PATH = os.path.join(ETS2_FOLDER, 'game.log.txt')

GITHUB_URL = "https://github.com/yourrepo"

def resource_path(relative_path):
    """ Get absolute path to resource (for PyInstaller and dev environment) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def detect_game_version():
    try:
        with open(GAME_LOG_PATH, 'r', encoding='utf-8') as file:
            for line in file:
                if "Euro Truck Simulator 2 init ver." in line:
                    version = line.split("ver.")[1].strip()
                    return version
    except Exception as e:
        print(f"Could not detect game version: {e}")
    return "Unknown"


CURRENT_GAME_VERSION = detect_game_version()


def ensure_mod_folder():
    if not os.path.exists(ETS2_MOD_FOLDER):
        os.makedirs(ETS2_MOD_FOLDER)


def is_7zip_installed():
    try:
        subprocess.run(["7z"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False


def threaded_install_mods():
    threading.Thread(target=install_mods, daemon=True).start()


def install_mods():
    files = filedialog.askopenfilenames(title="Select Mod Files", filetypes=[
        ("Mod Files", "*.scs *.zip *.rar *.7z")
    ])
    if not files:
        return

    install_button.configure(state="disabled")
    set_status("Installing mods...")

    for file in files:
        try:
            filename = os.path.basename(file)

            # Skip American Truck Simulator mods
            if "ats" in filename.lower():
                continue

            dest_path = os.path.join(ETS2_MOD_FOLDER, filename)

            if filename.endswith('.scs'):
                shutil.copy(file, ETS2_MOD_FOLDER)
            elif filename.endswith('.zip'):
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    for zip_file in zip_ref.namelist():
                        if zip_file.endswith('.scs'):
                            zip_ref.extract(zip_file, ETS2_MOD_FOLDER)
            elif filename.endswith('.rar') or filename.endswith('.7z'):
                if is_7zip_installed():
                    try:
                        subprocess.run(["7z", "e", file, "-o" + ETS2_MOD_FOLDER, "*.scs", "-y"], check=True)
                    except subprocess.CalledProcessError as e:
                        set_status(f"7z failed: {e}")
                else:
                    try:
                        patoolib.extract_archive(file, outdir=ETS2_MOD_FOLDER)
                    except Exception as e:
                        set_status(f"Patool error: {e}")
        except Exception as e:
            set_status(f"Error installing {file}: {e}")

    install_button.configure(state="normal")
    set_status("Mods installed successfully!")
    refresh_mod_list()


def get_mod_version(mod_path):
    try:
        with zipfile.ZipFile(mod_path, 'r') as archive:
            if "manifest.sii" in archive.namelist():
                with archive.open("manifest.sii") as manifest_file:
                    content = manifest_file.read().decode('utf-8', errors='ignore')
                    for line in content.splitlines():
                        if "package_version" in line:
                            return line.split(":")[1].strip().replace('"', '')
    except:
        pass
    # Try to guess version from filename if manifest version not found
    filename = os.path.basename(mod_path)
    match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', filename, re.IGNORECASE)
    if match:
        return match.group(1)
    return "Unknown"


def refresh_mod_list():
    for widget in mod_scrollable_frame.winfo_children():
        widget.destroy()

    checkbox_vars.clear()

    try:
        header_frame = ctk.CTkFrame(master=mod_scrollable_frame)
        header_frame.pack(fill="x", pady=(0, 5), padx=5)

        name_label = ctk.CTkLabel(master=header_frame, text="Name", font=("Helvetica", 16, "bold"))
        name_label.grid(row=0, column=0, sticky="w", padx=(10, 5))

        version_label = ctk.CTkLabel(master=header_frame, text="Version", font=("Helvetica", 16, "bold"))
        version_label.grid(row=0, column=1, sticky="e", padx=(5, 10))

        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        mods = [f for f in os.listdir(ETS2_MOD_FOLDER) if f.endswith('.scs')]

        if not mods:
            empty_label = ctk.CTkLabel(master=mod_scrollable_frame, text="No mods installed.", font=("Helvetica", 14))
            empty_label.pack(pady=20)
            return

        for i, mod in enumerate(mods):
            mod_path = os.path.join(ETS2_MOD_FOLDER, mod)
            version = get_mod_version(mod_path)

            row_frame = ctk.CTkFrame(master=mod_scrollable_frame)
            row_frame.pack(fill="x", pady=2, padx=5)

            var = ctk.StringVar(value="off")
            chk = ctk.CTkCheckBox(master=row_frame, text=mod, variable=var, onvalue="on", offvalue="off")
            chk.grid(row=0, column=0, sticky="w", padx=(10, 5))

            ver_label = ctk.CTkLabel(master=row_frame, text=version)
            ver_label.grid(row=0, column=1, sticky="e", padx=(5, 10))

            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=0)

            checkbox_vars.append((mod, var))
    except Exception as e:
        set_status(f"Error loading mod list: {e}")


def remove_selected_mods():
    removed_any = False

    for mod, var in checkbox_vars:
        if var.get() == "on":
            try:
                os.remove(os.path.join(ETS2_MOD_FOLDER, mod))
                removed_any = True
            except Exception as e:
                set_status(f"Error removing {mod}: {e}")

    if removed_any:
        set_status("Selected mods removed!")
    else:
        set_status("No mods selected to remove.")

    refresh_mod_list()


def open_settings():
    settings = ctk.CTkToplevel(root)
    settings.title("Settings")
    settings.geometry("400x400")
    settings.transient(root)
    settings.grab_set()
    settings.focus_force()

    ctk.CTkLabel(settings, text=f"Detected Version: {CURRENT_GAME_VERSION}", font=("Helvetica", 18)).pack(pady=20)

    ctk.CTkButton(settings, text="Open Mod Folder", command=lambda: subprocess.Popen(f'explorer "{ETS2_MOD_FOLDER}"')).pack(pady=5)

    def open_github():
        webbrowser.open(GITHUB_URL)

    ctk.CTkButton(settings, text="View on GitHub", command=open_github).pack(pady=5)

    ctk.CTkButton(settings, text="Close", command=settings.destroy).pack(pady=20)


def set_status(text):
    status_label.configure(text=text)


def create_gui():
    global root, mod_scrollable_frame, checkbox_vars, install_button, status_label

    ensure_mod_folder()

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("ETS2 Modern Mod Manager")
    root.geometry("700x850")

    frame = ctk.CTkFrame(master=root)
    frame.pack(pady=10, padx=20, fill="both", expand=True)

    ctk.CTkLabel(master=frame, text="ETS2 Mod Installer", font=("Helvetica", 24)).pack(pady=12)

    install_button = ctk.CTkButton(master=frame, text="Install Mods from PC", command=threaded_install_mods, font=("Helvetica", 16))
    install_button.pack(pady=10)

    mod_scrollable_frame = ctk.CTkScrollableFrame(master=frame, height=500)
    mod_scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

    checkbox_vars = []

    status_label = ctk.CTkLabel(master=frame, text="Welcome to ETS2 Mod Manager", font=("Helvetica", 14))
    status_label.pack(pady=10)

    bottom_frame = ctk.CTkFrame(master=frame)
    bottom_frame.pack(side="bottom", fill="x")

    gear_image = ctk.CTkImage(
        light_image=Image.open(resource_path("gear.png")),
        dark_image=Image.open(resource_path("gear.png")),
        size=(24, 24)
    )
    ctk.CTkButton(master=bottom_frame, image=gear_image, text="", width=40, command=open_settings).pack(side="left", padx=10)

    ctk.CTkButton(master=bottom_frame, text="Remove Selected", command=remove_selected_mods, font=("Helvetica", 16)).pack(side="left", padx=10)

    ctk.CTkButton(master=bottom_frame, text="Exit", command=root.destroy, font=("Helvetica", 16)).pack(side="right", padx=10)

    refresh_mod_list()
    root.mainloop()


if __name__ == "__main__":
    create_gui()
