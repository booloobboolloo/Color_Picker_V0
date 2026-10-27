"""Screen color picker for Windows.

Runs quietly in the background. Ctrl+Shift+F3 shows a small tooltip that follows
the mouse pointer and reports the color under it (RGB, hex, nearest common name).
Press Ctrl+Shift+F3 again to close the tooltip. Ctrl+Shift+F12 exits the app.

Standard library only (ctypes + tkinter). Run with:  pythonw color_picker.py
"""
import ctypes
import queue
import sys
import threading
from ctypes import wintypes

import tkinter as tk

# ----------------------------------------------------------------------------- color names
# CSS/X11 named colors, plus a few everyday names.
NAMED_COLORS = {
    "Black": (0, 0, 0), "White": (255, 255, 255), "Gray": (128, 128, 128),
    "Dark Gray": (64, 64, 64), "Silver": (192, 192, 192), "Light Gray": (211, 211, 211),
    "Gainsboro": (220, 220, 220), "Dim Gray": (105, 105, 105), "Slate Gray": (112, 128, 144),
    "Light Slate Gray": (119, 136, 153), "Dark Slate Gray": (47, 79, 79), "Charcoal": (54, 69, 79),
    "Red": (255, 0, 0), "Dark Red": (139, 0, 0), "Maroon": (128, 0, 0), "Firebrick": (178, 34, 34),
    "Crimson": (220, 20, 60), "Indian Red": (205, 92, 92), "Light Coral": (240, 128, 128),
    "Salmon": (250, 128, 114), "Dark Salmon": (233, 150, 122), "Light Salmon": (255, 160, 122),
    "Tomato": (255, 99, 71), "Orange Red": (255, 69, 0), "Coral": (255, 127, 80),
    "Orange": (255, 165, 0), "Dark Orange": (255, 140, 0), "Gold": (255, 215, 0),
    "Yellow": (255, 255, 0), "Light Yellow": (255, 255, 224), "Lemon Chiffon": (255, 250, 205),
    "Khaki": (240, 230, 140), "Dark Khaki": (189, 183, 107), "Goldenrod": (218, 165, 32),
    "Dark Goldenrod": (184, 134, 11), "Pale Goldenrod": (238, 232, 170), "Olive": (128, 128, 0),
    "Olive Drab": (107, 142, 35), "Dark Olive Green": (85, 107, 47), "Yellow Green": (154, 205, 50),
    "Chartreuse": (127, 255, 0), "Lawn Green": (124, 252, 0), "Lime": (0, 255, 0),
    "Lime Green": (50, 205, 50), "Light Green": (144, 238, 144), "Pale Green": (152, 251, 152),
    "Green": (0, 128, 0), "Dark Green": (0, 100, 0), "Forest Green": (34, 139, 34),
    "Sea Green": (46, 139, 87), "Medium Sea Green": (60, 179, 113), "Spring Green": (0, 255, 127),
    "Mint": (189, 252, 201), "Dark Sea Green": (143, 188, 143), "Teal": (0, 128, 128),
    "Dark Cyan": (0, 139, 139), "Light Sea Green": (32, 178, 170), "Cyan": (0, 255, 255),
    "Light Cyan": (224, 255, 255), "Aquamarine": (127, 255, 212), "Turquoise": (64, 224, 208),
    "Dark Turquoise": (0, 206, 209), "Cadet Blue": (95, 158, 160), "Powder Blue": (176, 224, 230),
    "Light Blue": (173, 216, 230), "Sky Blue": (135, 206, 235), "Light Sky Blue": (135, 206, 250),
    "Deep Sky Blue": (0, 191, 255), "Dodger Blue": (30, 144, 255), "Cornflower Blue": (100, 149, 237),
    "Steel Blue": (70, 130, 180), "Light Steel Blue": (176, 196, 222), "Royal Blue": (65, 105, 225),
    "Blue": (0, 0, 255), "Medium Blue": (0, 0, 205), "Dark Blue": (0, 0, 139), "Navy": (0, 0, 128),
    "Midnight Blue": (25, 25, 112), "Slate Blue": (106, 90, 205), "Dark Slate Blue": (72, 61, 139),
    "Medium Slate Blue": (123, 104, 238), "Indigo": (75, 0, 130), "Purple": (128, 0, 128),
    "Dark Magenta": (139, 0, 139), "Dark Violet": (148, 0, 211), "Blue Violet": (138, 43, 226),
    "Dark Orchid": (153, 50, 204), "Medium Purple": (147, 112, 219), "Medium Orchid": (186, 85, 211),
    "Magenta": (255, 0, 255), "Violet": (238, 130, 238), "Plum": (221, 160, 221),
    "Orchid": (218, 112, 214), "Thistle": (216, 191, 216), "Lavender": (230, 230, 250),
    "Medium Violet Red": (199, 21, 133), "Deep Pink": (255, 20, 147), "Hot Pink": (255, 105, 180),
    "Pink": (255, 192, 203), "Light Pink": (255, 182, 193), "Pale Violet Red": (219, 112, 147),
    "Brown": (165, 42, 42), "Saddle Brown": (139, 69, 19), "Sienna": (160, 82, 45),
    "Chocolate": (210, 105, 30), "Peru": (205, 133, 63), "Sandy Brown": (244, 164, 96),
    "Burlywood": (222, 184, 135), "Tan": (210, 180, 140), "Rosy Brown": (188, 143, 143),
    "Wheat": (245, 222, 179), "Beige": (245, 245, 220), "Bisque": (255, 228, 196),
    "Navajo White": (255, 222, 173), "Moccasin": (255, 228, 181), "Peach Puff": (255, 218, 185),
    "Papaya Whip": (255, 239, 213), "Blanched Almond": (255, 235, 205), "Cornsilk": (255, 248, 220),
    "Antique White": (250, 235, 215), "Linen": (250, 240, 230), "Old Lace": (253, 245, 230),
    "Ivory": (255, 255, 240), "Seashell": (255, 245, 238), "Snow": (255, 250, 250),
    "Floral White": (255, 250, 240), "Ghost White": (248, 248, 255), "Alice Blue": (240, 248, 255),
    "Azure": (240, 255, 255), "Honeydew": (240, 255, 240), "Mint Cream": (245, 255, 250),
    "Lavender Blush": (255, 240, 245), "Misty Rose": (255, 228, 225), "White Smoke": (245, 245, 245),
}


def _srgb_to_lab(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(c)) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


_LAB_TABLE = [(name, _srgb_to_lab(rgb)) for name, rgb in NAMED_COLORS.items()]


def nearest_color_name(rgb):
    """Nearest named color by CIE76 ΔE in Lab space. Returns (name, delta_e)."""
    L, a, b = _srgb_to_lab(rgb)
    name, lab = min(_LAB_TABLE, key=lambda e: (e[1][0] - L) ** 2 + (e[1][1] - a) ** 2 + (e[1][2] - b) ** 2)
    return name, ((lab[0] - L) ** 2 + (lab[1] - a) ** 2 + (lab[2] - b) ** 2) ** 0.5


# ----------------------------------------------------------------------------- Win32
if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    try:  # per-monitor DPI aware so cursor coords match physical pixels
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
    except (OSError, AttributeError):
        user32.SetProcessDPIAware()

    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.GetPixel.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.GetPixel.restype = wintypes.DWORD
    user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
    user32.MonitorFromPoint.restype = wintypes.HMONITOR

class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x4000
VK_F3, VK_F12 = 0x72, 0x7B
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
HK_TOGGLE, HK_EXIT = 1, 2
CLR_INVALID = 0xFFFFFFFF


def cursor_pos():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def pixel_at(x, y):
    hdc = user32.GetDC(None)
    try:
        c = gdi32.GetPixel(hdc, x, y)
    finally:
        user32.ReleaseDC(None, hdc)
    if c == CLR_INVALID:
        return None
    return c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF   # COLORREF is 0x00BBGGRR


def monitor_rect(x, y):
    mi = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
    user32.GetMonitorInfoW(user32.MonitorFromPoint(wintypes.POINT(x, y), 2), ctypes.byref(mi))
    r = mi.rcMonitor
    return r.left, r.top, r.right, r.bottom


def hotkey_thread(events, ready):
    """Registers global hotkeys and forwards presses to the Tk thread via a queue."""
    ok_toggle = user32.RegisterHotKey(None, HK_TOGGLE, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_F3)
    ok_exit = user32.RegisterHotKey(None, HK_EXIT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_F12)
    ready.put((ok_toggle, ok_exit, kernel32.GetCurrentThreadId()))
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY:
            events.put(msg.wParam)
    user32.UnregisterHotKey(None, HK_TOGGLE)
    user32.UnregisterHotKey(None, HK_EXIT)


# ----------------------------------------------------------------------------- UI
class ColorTip:
    OFFSET = 24          # px from the pointer, so the tooltip never samples itself
    PERIOD_MS = 40

    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.withdraw()
        frame = tk.Frame(self.win, bg="#202020", padx=8, pady=6)
        frame.pack()
        self.swatch = tk.Frame(frame, width=34, height=34, bg="#000000",
                               highlightthickness=1, highlightbackground="#808080")
        self.swatch.grid(row=0, column=0, rowspan=3, padx=(0, 8))
        font = ("Consolas", 10)
        self.l_name = tk.Label(frame, font=("Segoe UI", 10, "bold"), fg="white", bg="#202020", anchor="w")
        self.l_rgb = tk.Label(frame, font=font, fg="#e0e0e0", bg="#202020", anchor="w")
        self.l_pos = tk.Label(frame, font=("Consolas", 8), fg="#9a9a9a", bg="#202020", anchor="w")
        for i, w in enumerate((self.l_name, self.l_rgb, self.l_pos)):
            w.grid(row=i, column=1, sticky="w")
        self.active = False
        self._job = None

    def toggle(self):
        self.hide() if self.active else self.show()

    def show(self):
        self.active = True
        self.win.deiconify()
        self._tick()

    def hide(self):
        self.active = False
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        self.win.withdraw()

    def _tick(self):
        x, y = cursor_pos()
        rgb = pixel_at(x, y)
        if rgb:
            name, de = nearest_color_name(rgb)
            hexv = "#%02X%02X%02X" % rgb
            self.swatch.configure(bg=hexv)
            self.l_name.configure(text=name if de < 10 else f"~ {name}")
            self.l_rgb.configure(text=f"RGB({rgb[0]:3d}, {rgb[1]:3d}, {rgb[2]:3d})  {hexv}")
            self.l_pos.configure(text=f"x {x}  y {y}")
        self._place(x, y)
        self._job = self.root.after(self.PERIOD_MS, self._tick)

    def _place(self, x, y):
        self.win.update_idletasks()
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        left, top, right, bottom = monitor_rect(x, y)
        nx = x + self.OFFSET if x + self.OFFSET + w <= right else x - self.OFFSET - w
        ny = y + self.OFFSET if y + self.OFFSET + h <= bottom else y - self.OFFSET - h
        self.win.geometry(f"+{max(nx, left)}+{max(ny, top)}")


def main():
    if sys.platform != "win32":
        sys.exit("This app uses the Win32 API; run it with Windows Python.")
    events, ready = queue.Queue(), queue.Queue()
    threading.Thread(target=hotkey_thread, args=(events, ready), daemon=True).start()
    ok_toggle, ok_exit, hk_tid = ready.get()

    root = tk.Tk()
    root.withdraw()
    if not ok_toggle:
        from tkinter import messagebox
        messagebox.showerror("Color Picker", "Ctrl+Shift+F3 is already in use by another app "
                             "(or another copy of Color Picker is running).")
        root.destroy()
        return
    tip = ColorTip(root)

    def poll():
        while not events.empty():
            hk = events.get_nowait()
            if hk == HK_TOGGLE:
                tip.toggle()
            elif hk == HK_EXIT:
                user32.PostThreadMessageW(hk_tid, WM_QUIT, 0, 0)
                root.destroy()
                return
        root.after(30, poll)

    poll()
    root.mainloop()


if __name__ == "__main__":
    main()
