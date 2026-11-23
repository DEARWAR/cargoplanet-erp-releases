"""updater.py - checks the public GitHub Releases repo and updates the installed app.

Flow: app starts -> background check -> newer release found -> popup ->
download CargoPlanetERP-Setup.exe -> verify -> run it silently -> app closes, installer
replaces the files and re-opens the app.  The database lives in %APPDATA%\\CargoPlanetERP,
so an update never touches the data.

Only active in the installed .exe (set FREIGHT_ERP_FORCE_UPDATE_CHECK=1 to test from source).
Any network problem is ignored silently - the app just keeps working.
A release whose notes contain the word [mandatory] cannot be skipped.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import version

API_URL = f"https://api.github.com/repos/{version.UPDATE_REPO}/releases/latest"
INSTALLER_HINT = "setup"          # asset whose name contains this and ends with .exe


def parse_version(text):
    nums = [int(x) for x in re.findall(r"\d+", str(text).lstrip("vV").split("-")[0])][:3]
    return tuple(nums + [0] * (3 - len(nums)))


def pick_release(data, current=None):
    """Pure function (easy to test): returns info dict if `data` is newer, else None."""
    current = current or version.APP_VERSION
    tag = data.get("tag_name", "")
    if not tag or data.get("draft") or data.get("prerelease"):
        return None
    if parse_version(tag) <= parse_version(current):
        return None
    for asset in data.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".exe") and INSTALLER_HINT in name:
            digest = asset.get("digest") or ""
            notes = data.get("body") or ""
            return {
                "version": tag.lstrip("vV"),
                "url": asset.get("browser_download_url"),
                "size": asset.get("size") or 0,
                "sha256": digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else "",
                "notes": notes,
                "mandatory": "[mandatory]" in notes.lower(),
            }
    return None


def fetch_latest():
    req = urllib.request.Request(API_URL, headers={
        "User-Agent": "CargoPlanetERP-Updater", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return pick_release(json.loads(resp.read().decode("utf-8")))


def start_background_check(root):
    """Call once after the main window exists."""
    if not (getattr(sys, "frozen", False) or os.environ.get("FREIGHT_ERP_FORCE_UPDATE_CHECK")):
        return
    box = {"done": False, "info": None}

    def work():
        try:
            box["info"] = fetch_latest()
        except Exception as exc:
            print(f"[update] check skipped: {exc}")
        box["done"] = True

    threading.Thread(target=work, daemon=True).start()

    def poll(tries=[0]):
        tries[0] += 1
        if box["done"]:
            if box["info"]:
                _prompt(root, box["info"])
        elif tries[0] < 60:
            root.after(500, poll)

    root.after(2000, poll)


def _clean_notes(notes):
    return re.sub(r"\[mandatory\]", "", notes, flags=re.I).strip()[:700] or "Bug fixes and improvements."


def _prompt(root, info):
    msg = (f"A new version ({info['version']}) is available. You have {version.APP_VERSION}.\n\n"
           f"What's new:\n{_clean_notes(info['notes'])}\n\n"
           "Please save your work first. The software will close and re-open by itself.\n\n")
    if info["mandatory"]:
        messagebox.showinfo("Update required", msg + "This update is required.", parent=root)
        _download_and_install(root, info)
    elif messagebox.askyesno("Update available", msg + "Update now?", parent=root):
        _download_and_install(root, info)


def _download_and_install(root, info):
    dest = os.path.join(tempfile.gettempdir(), "CargoPlanetERP-Setup.exe")
    state = {"done": False, "err": None, "got": 0}

    win = ctk.CTkToplevel(root)
    win.title("Updating...")
    win.geometry("360x120")
    win.grab_set()
    win.protocol("WM_DELETE_WINDOW", lambda: None)
    ctk.CTkLabel(win, text=f"Downloading version {info['version']} ...",
                 font=("Segoe UI", 12, "bold")).pack(pady=(18, 8))
    bar = ctk.CTkProgressBar(win, width=300)
    bar.pack()
    bar.set(0)

    def work():
        try:
            req = urllib.request.Request(info["url"], headers={"User-Agent": "CargoPlanetERP-Updater"})
            sha = hashlib.sha256()
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
                while True:
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    sha.update(chunk)
                    state["got"] += len(chunk)
            if info["size"] and state["got"] != info["size"]:
                raise IOError("Download incomplete.")
            if info["sha256"] and sha.hexdigest().lower() != info["sha256"]:
                raise IOError("Downloaded file failed the integrity check.")
        except Exception as exc:
            state["err"] = str(exc)
        state["done"] = True

    threading.Thread(target=work, daemon=True).start()

    def poll():
        if info["size"]:
            bar.set(min(1.0, state["got"] / info["size"]))
        if not state["done"]:
            root.after(200, poll)
            return
        win.destroy()
        if state["err"]:
            messagebox.showerror("Update failed",
                                 f"Could not download the update.\n{state['err']}\n\n"
                                 "The current version will keep working.", parent=root)
            return
        _run_installer(root, dest)

    poll()


def _run_installer(root, path):
    try:
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0   # DETACHED | NEW_GROUP
        subprocess.Popen(
            [path, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"],
            close_fds=True, creationflags=flags)
    except Exception as exc:
        messagebox.showerror("Update failed", f"Could not start the installer.\n{exc}", parent=root)
        return
    try:
        root.destroy()
    finally:
        os._exit(0)
