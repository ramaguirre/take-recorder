"""Local helper for Take Recorder on a PC: serves the app and keeps takes in a real folder.

    python take_server.py [--root DIR] [--port 8000]

Takes go to <root>/<YYYYMMDD_HHMMSS>/<file>. The app detects this helper through
/api/info and then saves here instead of browser storage, can open Explorer on a session,
and can change <root> through a native folder picker (remembered in
%APPDATA%/TakeRecorder/config.json; --root overrides it). Stdlib only. Listens on 127.0.0.1; API calls must carry the X-Take-Recorder
header, which other websites cannot send without a CORS preflight that is never granted.
"""
import argparse
import json
import mimetypes
import re
import shutil
import os
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

APP = Path(__file__).resolve().parent
SESSION = re.compile(r"^\d{8}_\d{6}$")
NAME = re.compile(r"^[\w.-]+\.(mp4|webm)$")
CONFIG = Path(os.environ.get("APPDATA", Path.home())) / "TakeRecorder" / "config.json"
DEFAULT_ROOT = Path.home() / "Videos" / "TakeRecorder"
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("text/javascript", ".js")

# Runs in its own process so Tk never shares a thread with the server. The hidden topmost
# root keeps the dialog above the browser.
PICK_FOLDER = r"""
import sys, tkinter as tk
from tkinter import filedialog
root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); root.update()
print(filedialog.askdirectory(parent=root, initialdir=sys.argv[1], mustexist=False,
                              title='Folder for Take Recorder takes') or '', end='')
"""


def load_root():
    try:
        return Path(json.loads(CONFIG.read_text(encoding="utf-8"))["root"])
    except (OSError, ValueError, KeyError):
        return DEFAULT_ROOT


def save_root(root):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"root": str(root)}), encoding="utf-8")


def raise_explorer(folder, timeout=5.0):
    """Explorer started by a background process opens behind the browser: find its window and raise it."""
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    name = folder.name.lower()
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def check(hwnd, _):
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        if cls.value == "CabinetWClass" and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, title, n + 1)
            t = title.value.lower()
            if t.startswith(name) or str(folder).lower() in t:
                found.append(hwnd)
        return True

    end = time.time() + timeout
    while not found and time.time() < end:
        time.sleep(0.2)
        user32.EnumWindows(check, 0)
    if found:
        user32.keybd_event(0x12, 0, 0, 0)        # a tap of Alt lifts Windows' foreground lock
        user32.keybd_event(0x12, 0, 2, 0)
        user32.ShowWindow(found[0], 9)           # SW_RESTORE
        user32.SetForegroundWindow(found[0])


class Handler(SimpleHTTPRequestHandler):
    root: Path = None

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(APP), **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    # ---------- plumbing ----------
    def _send(self, code, body=None, ctype="application/json"):
        data = b"" if body is None else body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _path(self, session, name=None):
        if not SESSION.match(session) or (name is not None and not NAME.match(name)):
            raise ValueError("bad name")
        p = self.root / session
        return p / name if name else p

    def _route(self, method):
        if self.headers.get("X-Take-Recorder") != "1":
            return self._send(403, {"error": "missing header"})
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.split("/")[2:]]
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            return getattr(self, f"api_{method}_{parts[0]}")(*parts[1:], **query)
        except (AttributeError, TypeError, IndexError):
            return self._send(404, {"error": "unknown route"})
        except (ValueError, FileNotFoundError) as e:
            return self._send(400, {"error": str(e)})

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._route("GET")
        return super().do_GET()

    def do_PUT(self):
        return self._route("PUT")

    def do_POST(self):
        return self._route("POST")

    def do_DELETE(self):
        return self._route("DELETE")

    # ---------- API ----------
    def api_GET_info(self):
        self._send(200, {"root": str(self.root)})

    def api_GET_list(self):
        sessions = []
        if self.root.exists():
            for d in sorted(self.root.iterdir(), reverse=True):
                if d.is_dir() and SESSION.match(d.name):
                    files = [{"name": f.name, "size": f.stat().st_size}
                             for f in sorted(d.iterdir()) if f.is_file() and NAME.match(f.name)]
                    sessions.append({"session": d.name, "files": files})
        self._send(200, sessions)

    def api_GET_file(self, session, name):
        p = self._path(session, name)
        self._send(200, p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream")

    def api_PUT_file(self, session, name):
        p = self._path(session, name)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".part")
        left = int(self.headers["Content-Length"])
        with open(tmp, "wb") as f:
            while left:
                chunk = self.rfile.read(min(left, 1 << 20))
                if not chunk:
                    raise ValueError("upload cut short")
                f.write(chunk)
                left -= len(chunk)
        tmp.replace(p)
        self._send(204)

    def api_DELETE_file(self, session, name):
        self._path(session, name).unlink()
        self._send(204)

    def api_POST_rename(self, session, name, to):
        src, dst = self._path(session, name), self._path(session, to)
        src.replace(dst)
        self._send(204)

    def api_DELETE_session(self, session):
        shutil.rmtree(self._path(session))
        self._send(204)

    def api_POST_reveal(self, session="", name=""):
        target = self.root
        if session:
            target = self._path(session, name or None)
            if not target.exists():
                target = target.parent if name else self.root
        self.root.mkdir(parents=True, exist_ok=True)
        folder = target if target.is_dir() else target.parent
        if sys.platform == "win32":
            args = ["explorer", f"/select,{target}"] if target.is_file() else ["explorer", str(target)]
        else:
            args = ["open" if sys.platform == "darwin" else "xdg-open", str(folder)]
        subprocess.Popen(args)
        threading.Thread(target=raise_explorer, args=(folder,), daemon=True).start()
        self._send(204)

    def api_POST_choose(self):
        picked = subprocess.run([sys.executable, "-c", PICK_FOLDER, str(self.root)],
                                capture_output=True, text=True).stdout.strip()
        if picked:
            Handler.root = Path(picked).resolve()
            Handler.root.mkdir(parents=True, exist_ok=True)
            save_root(Handler.root)
        self._send(200, {"root": str(Handler.root), "changed": bool(picked)})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", help="folder for the takes (default: last folder chosen in the app, "
                                   "else ~/Videos/TakeRecorder)")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    Handler.root = (Path(args.root).expanduser() if args.root else load_root()).resolve()
    Handler.root.mkdir(parents=True, exist_ok=True)
    print(f"Take Recorder on http://localhost:{args.port}  ·  takes in {Handler.root}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
