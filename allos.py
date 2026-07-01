import sys
import math
import asyncio
import httpx
import websockets
from itertools import cycle
from collections import deque
import random
import json
import os
import webbrowser
import base64
from datetime import datetime, timedelta
import time
try:
    import pyperclip as _pyperclip
except ImportError:
    _pyperclip = None

def _clipboard_copy(text):
    """Cross-platform clipboard copy. Silently fails if unavailable."""
    if _pyperclip is not None:
        try:
            _pyperclip.copy(text)
            return True
        except Exception:
            pass
    return False
import threading

VERSION = '2.1.4'

def hsv_to_rgb(h, s, v):
    h = float(h) % 360
    s = float(s)
    v = float(v)
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    if h < 60: r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

class _AnimationSkipper:
    def __init__(self, required_presses=2):
        self.required = required_presses
        self.count = 0
        self.skipped = False
        self._thread = None
        self._stop = False

    def start(self):
        self._stop = False
        self.skipped = False
        self.count = 0
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        try:
            if os.name == 'nt':
                import msvcrt
                while not self._stop and not self.skipped:
                    if msvcrt.kbhit():
                        key = msvcrt.getwch()
                        if key in ('\r', '\n'):
                            self.count += 1
                            if self.count >= self.required:
                                self.skipped = True
                                return
                    else:
                        time.sleep(0.05)
            else:
                import select
                import sys as _sys
                while not self._stop and not self.skipped:
                    if select.select([_sys.stdin], [], [], 0.05)[0]:
                        _sys.stdin.readline()
                        self.count += 1
                        if self.count >= self.required:
                            self.skipped = True
                            return
        except Exception:
            pass

    def stop(self):
        self._stop = True

    @property
    def should_skip(self):
        return self.skipped

__mode__ = None
__manual_mode__ = False


ALL_GRADIENTS = [
    ((0, 255, 255), (255, 0, 255)),   # Cyan to Magenta
    ((128, 0, 128), (255, 215, 0)),  # Purple to Gold
    ((0, 255, 0), (173, 255, 47)),   # Green to GreenYellow
    ((255, 0, 0), (255, 165, 0)),    # Red to Orange
    ((0, 0, 255), (255, 255, 255)),  # Blue to White
    ((255, 105, 180), (255, 255, 0)),# HotPink to Yellow
    ((255, 0, 0), (255, 255, 255)),  # Red to White
    ((180, 0, 255), (0, 255, 255)),  # Electric Purple to Cyan
    ((255, 20, 147), (139, 0, 0)),   # Deep Pink to Dark Red
    ((255, 0, 255), (148, 0, 211)),  # Magenta to DarkViolet
    ((255, 64, 64), (64, 64, 255)),  # Soft Red to Soft Blue
    ((0, 242, 255), (180, 40, 255)), # Sky Blue to Royal Purple
    ((255, 183, 77), (255, 82, 82)), # Peach to Coral
    ((100, 255, 218), (0, 188, 212)),# Aquamarine to Cyan
    ((255, 0, 100), (40, 0, 255)),   # Neon Rose to Electric Blue
    ((255, 255, 0), (255, 0, 0)),    # Yellow to Red
    ((224, 64, 251), (0, 229, 255)), # Purple to Light Blue
    ((118, 255, 3), (0, 229, 255)),  # Lime to Cyan
    ((255, 234, 0), (255, 0, 255)),  # Vivid Yellow to Magenta
    ((0, 255, 127), (0, 128, 128)),  # Spring Green to Teal
    ((255, 111, 0), (255, 255, 255)),# Deep Orange to White
    ((64, 224, 208), (255, 127, 80)),# Turquoise to Coral
    ((255, 105, 180), (75, 0, 130)), # Pink to Indigo
    ((0, 191, 255), (0, 0, 128)),    # Deep Sky Blue to Navy
    ((255, 215, 0), (40, 40, 40)),   # Gold to Dark Grey
    ((173, 216, 230), (25, 25, 112)),# Light Blue to Midnight Blue
    ((255, 69, 0), (255, 215, 0)),   # OrangeRed to Gold
    ((124, 252, 0), (0, 100, 0)),    # LawnGreen to DarkGreen
    ((147, 112, 219), (75, 0, 130)), # Medium Purple to Indigo
    ((240, 128, 128), (139, 0, 0)),  # Light Coral to Dark Red
    ((0, 255, 255), (0, 128, 255)),  # Cyan to Azure
    ((255, 20, 147), (255, 160, 122)),# DeepPink to LightSalmon
    ((0, 250, 154), (70, 130, 180)), # MediumSpringGreen to SteelBlue
    ((255, 0, 0), (0, 0, 255)),      # Red to Blue
    ((255, 140, 0), (153, 50, 204)), # DarkOrange to DarkOrchid
    ((172, 255, 47), (0, 191, 255)), # GreenYellow to DeepSkyBlue
    ((255, 20, 147), (0, 255, 127)), # DeepPink to SpringGreen
    ((135, 206, 235), (255, 182, 193)),# SkyBlue to LightPink
    ((255, 215, 0), (255, 69, 0)),   # Gold to OrangeRed
    ((0, 255, 255), (0, 0, 139)),    # Cyan to DarkBlue
    ((255, 0, 255), (75, 0, 130)),   # Magenta to Indigo
    ((0, 255, 127), (25, 25, 112)),  # SpringGreen to MidnightBlue
    ((255, 255, 240), (255, 140, 0)),# Ivory to DarkOrange
    ((255, 20, 147), (255, 255, 0)), # DeepPink to Yellow
    ((0, 206, 209), (138, 43, 226)), # DarkTurquoise to BlueViolet
    ((255, 165, 0), (0, 0, 255)),    # Orange to Blue
    ((0, 255, 0), (255, 20, 147)),   # Green to DeepPink
    ((255, 255, 255), (105, 105, 105)),# White to DimGrey
    ((255, 255, 0), (0, 0, 128)),    # Yellow to Navy
    ((30, 144, 255), (255, 20, 147)), # DodgerBlue to DeepPink
    ((255, 0, 0), (0, 255, 0)),      # Red to Green (Christmas/Toxic)
    ((135, 206, 250), (25, 25, 112)),# LightSkyBlue to MidnightBlue
    ((218, 112, 214), (0, 0, 255)),  # Orchid to Blue
    ((255, 20, 147), (124, 252, 0)), # DeepPink to LawnGreen
    ((0, 255, 255), (255, 215, 0)),  # Cyan to Gold
    ((255, 69, 0), (0, 255, 127)),   # OrangeRed to SpringGreen
    ((255, 105, 180), (0, 191, 255)),# HotPink to DeepSkyBlue
    ((255, 255, 0), (128, 0, 128)),   # Yellow to Purple
    ((255, 105, 180), (75, 0, 130)), # HotPink to Indigo
    ((255, 0, 0), (255, 255, 0)),    # Red to Yellow
    ((0, 255, 0), (0, 0, 255)),      # Green to Blue
    ((255, 255, 255), (255, 105, 180)),# White to HotPink
    ((255, 20, 147), (0, 206, 209)), # DeepPink to DarkTurquoise
    ((124, 252, 0), (139, 0, 0)),    # LawnGreen to DarkRed
    ((0, 191, 255), (255, 69, 0)),   # DeepSkyBlue to OrangeRed
    ((255, 215, 0), (0, 0, 128)),    # Gold to Navy
    ((186, 85, 211), (0, 255, 127)), # MediumOrchid to SpringGreen
    ((255, 140, 0), (30, 144, 255)), # DarkOrange to DodgerBlue
    ((0, 250, 154), (138, 43, 226)), # MediumSpringGreen to BlueViolet
    ((255, 0, 255), (255, 255, 0)),  # Magenta to Yellow
    ((0, 255, 255), (255, 0, 0)),    # Cyan to Red
    ((255, 165, 0), (0, 0, 255)),    # Orange to Blue
    ((0, 128, 0), (255, 192, 203)),  # Green to Pink
    ((128, 0, 128), (255, 255, 255)),# Purple to White
    ((0, 255, 0), (255, 20, 147)),   # Green to DeepPink
    ((0, 0, 255), (255, 255, 0)),    # Blue to Yellow
    ((255, 69, 0), (0, 255, 255)),   # OrangeRed to Cyan
    ((139, 0, 139), (127, 255, 0)),  # DarkMagenta to Chartreuse
    ((255, 105, 180), (0, 0, 128)),  # HotPink to Navy
    ((0, 255, 127), (255, 215, 0)),  # SpringGreen to Gold
    ((75, 0, 130), (255, 255, 255)), # Indigo to White
    ((30, 144, 255), (255, 20, 147)),# DodgerBlue to DeepPink
    ((124, 252, 0), (138, 43, 226)), # LawnGreen to BlueViolet
    ((0, 255, 255), (255, 165, 0)),  # Cyan to Orange
    ((255, 0, 255), (0, 128, 0)),    # Magenta to Green
    ((139, 0, 0), (0, 255, 0)),      # DarkRed to Green
    ((0, 191, 255), (255, 0, 255)),  # DeepSkyBlue to Magenta
    ((255, 255, 0), (0, 0, 255)),    # Yellow to Blue
]

def pick_random_gradient():
    return random.choice(ALL_GRADIENTS)

W_START, W_END = pick_random_gradient()
WIZZLER_ASCII_ALT_4 = [
    " __   __  ___   __   ________  ________   ___       _______   _______    ________         ______    _______   ",
    "|\"  |/  \\|  \"| |\" \\ (\"      \"\\(\"      \"\\ |\"  |     /\"     \"| /\"      \\  /\"       )       /    \" \\  |   __ \"\\  ",
    "|'  /    \\:  | ||  | \\___/   :)\\___/   :)||  |    (: ______)|:        |(:   \\___/       // ____  \\ (. |__) :) ",
    "|: /'        | |:  |   /  ___/   /  ___/ |:  |     \\/    |  |_____/   ) \\___  \\        /  /    ) :)|:  ____/  ",
    " \\//  /\\'    | |.  |  //  \\__   //  \\__   \\  |___  // ___)_  //      /   __/  \\\\      (: (____/ // (|  /      ",
    " /   /  \\\\   | /\\  |\\(:   / \"\\ (:   / \"\\ ( \\_|:  \\(:      \"||:  __   \\  /\" \\   :)      \\        / /|__/ \\     ",
    "|___/    \\___|(__\\_|_)\\_______) \\_______) \\_______)\\_______)|__|  \\___)(_______/        \\\"_____/ (_______)    ",
]
WIZZLER_START = W_START
WIZZLER_END = W_END

D_START, D_END = pick_random_gradient()
DEADLIZER_START = D_START
DEADLIZER_END = D_END

SUCCESS_GRADIENTS = [
    ((0, 255, 150), (0, 60, 20)),   # Deep Mint to Jungle
    ((50, 255, 80), (0, 40, 10)),   # Electric Mint to Forest
    ((20, 255, 20), (0, 15, 0)),    # Viral Dark Neon Green
    ((127, 255, 0), (0, 100, 0)),   # Chartreuse to Dark Green
    ((0, 255, 127), (0, 128, 0)),   # Spring Green to Green
    ((173, 255, 47), (85, 107, 47)),# GreenYellow to DarkOliveGreen
    ((0, 255, 64), (0, 32, 0)),     # Bright green to Deep shadow
    ((64, 255, 208), (16, 64, 48)), # Turquoise Green to Dark Slate
    ((200, 255, 0), (20, 40, 0)),   # Lime Yellow to Dark Moss
    ((0, 255, 255), (0, 64, 64)),   # Cyan to Dark Teal
    ((152, 251, 152), (0, 100, 0)), # PaleGreen to DarkGreen
    ((0, 250, 154), (46, 139, 87)), # MediumSpringGreen to SeaGreen
    ((144, 238, 144), (34, 139, 34)),# LightGreen to ForestGreen
    ((50, 205, 50), (0, 100, 0)),    # LimeGreen to DarkGreen
    ((0, 255, 0), (0, 40, 0)),       # Neon Green to Forest
    ((127, 255, 0), (20, 60, 20)),   # Chartreuse to Deep Green
    ((0, 255, 127), (0, 30, 0)),     # Spring Green to Abyss
    ((152, 251, 152), (0, 50, 0)),   # PaleGreen to Moss
    ((0, 250, 154), (0, 20, 10)),    # MediumSpringGreen to Shadow
    ((144, 238, 144), (20, 40, 20)), # LightGreen to Swamp
    ((0, 255, 64), (0, 10, 5)),      # Bright Green to Void
    ((64, 255, 208), (0, 32, 16)),   # Turquoise to Dark Teal
    ((200, 255, 0), (10, 20, 0)),    # Lime Yellow to Mud
]
S_START, S_END = random.choice(SUCCESS_GRADIENTS)
GREEN_START = S_START
GREEN_END = S_END
ERROR_GRADIENTS = [
    ((255, 0, 0), (20, 0, 0)),      # Red to Black
    ((255, 69, 0), (45, 0, 0)),     # Orange Red to Black
    ((255, 20, 147), (40, 0, 10)),  # Deep Pink to Dark Maroon
    ((139, 0, 0), (20, 0, 0)),      # Dark Red to Black
    ((255, 0, 255), (40, 0, 40)),   # Magenta to Dark Purple
    ((255, 48, 48), (64, 0, 0)),    # Firebrick to Shadow
    ((255, 127, 80), (80, 20, 0)),  # Coral to Burnt Umber
    ((255, 0, 127), (32, 0, 16)),   # Rose to Void
    ((255, 64, 0), (32, 8, 0)),     # Hot Orange to Pitch
    ((220, 20, 60), (40, 0, 0)),    # Crimson to Darkness
    ((255, 99, 71), (139, 0, 0)),   # Tomato to DarkRed
    ((250, 128, 114), (128, 0, 0)), # Salmon to Maroon
    ((255, 0, 0), (75, 0, 130)),    # Red to Indigo
    ((255, 0, 0), (30, 0, 0)),       # Pure Red to Blood
    ((220, 20, 60), (40, 0, 0)),     # Crimson to Dark
    ((178, 34, 34), (10, 0, 0)),     # Firebrick to Pit
    ((255, 69, 0), (20, 5, 0)),      # OrangeRed to Ash
    ((255, 20, 147), (40, 0, 20)),   # DeepPink to Night
    ((255, 127, 80), (30, 10, 0)),   # Coral to Burnt
    ((255, 0, 127), (40, 0, 40)),    # Rose to Shadow
    ((128, 0, 0), (60, 0, 0)),       # Maroon to Dark Maroon
]
E_START, E_END = random.choice(ERROR_GRADIENTS)
RED_START = E_START
RED_END = E_END
PINK_GRADIENTS = [
    ((255, 105, 180), (40, 0, 130)), # HotPink to Indigo
    ((255, 20, 147), (75, 0, 130)),  # DeepPink to Indigo
    ((218, 112, 214), (139, 0, 139)),# Orchid to DarkMagenta
    ((255, 182, 193), (199, 21, 133)),# LightPink to MediumVioletRed
    ((255, 0, 255), (25, 25, 112)),  # Magenta to MidnightBlue
    ((255, 105, 180), (20, 0, 40)),  # HotPink to Dark Purple
    ((218, 112, 214), (40, 0, 40)),  # Orchid to Void
    ((255, 192, 203), (128, 0, 128)),# Pink to Purple
    ((255, 182, 193), (75, 0, 130)), # LightPink to Indigo
]
P_START, P_END = random.choice(PINK_GRADIENTS)
PINK_START = P_START
PINK_END = P_END

# Simplified banner for small screens
WIZZLER_ASCII = [
    "██╗    ██╗██╗███████╗███████╗██╗     ███████╗██████╗ ███████╗     ██████╗ ██████╗ ",
    "██║    ██║██║╚══███╔╝╚══███╔╝██║     ██╔════╝██╔══██╗██╔════╝    ██╔═══██╗██╔══██╗",
    "██║ █╗ ██║██║  ███╔╝   ███╔╝ ██║     █████╗  ██████╔╝███████╗    ██║   ██║██████╔╝",
    "██║███╗██║██║ ███╔╝   ███╔╝  ██║     ██╔══╝  ██╔══██╗╚════██║    ██║   ██║██╔═══╝ ",
    "╚███╔███╔╝██║███████╗███████╗███████╗███████╗██║  ██║███████║    ╚██████╔╝██║     ",
    " ╚══╝╚══╝ ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═╝     ",
]

DEADLIZER_ASCII = [
    "  ██████╗ ███████╗ █████╗ ██████╗ ██╗     ██╗███████╗███████╗██████╗ ",
    "  ██╔══██╗██╔════╝██╔══██╗██╔══██╗██║     ██║╚══███╔╝██╔════╝██╔══██╗",
    "  ██║  ██║█████╗  ███████║██║  ██║██║     ██║  ███╔╝ █████╗  ██████╔╝",
    "  ██║  ██║██╔══╝  ██╔══██║██║  ██║██║     ██║ ███╔╝  ██╔══╝  ██╔══██╗",
    "  ██████╔╝███████╗██║  ██║██████╔╝███████╗██║███████╗███████╗██║  ██║",
    "  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝",
]

WIZZLER_ASCII_ALT_1 = [
    "█     █░ ██▓▒███████▒▒███████▒ ██▓    ▓█████  ██▀███    ██████     ▒█████   ██▓███  ",
    "▓█░ █ ░█░▓██▒▒ ▒ ▒ ▄▀░▒ ▒ ▒ ▄▀░▓██▒    ▓█   ▀ ▓██ ▒ ██▒▒██    ▒    ▒██▒  ██▒▓██░  ██▒",
    "▒█░ █ ░█ ▒██▒░ ▒ ▄▀▒░ ░ ▒ ▄▀▒░ ▒██░    ▒███   ▓██ ░▄█ ▒░ ▓██▄      ▒██░  ██▒▓██░ ██▓▒",
    "░█░ █ ░█ ░██░  ▄▀▒   ░  ▄▀▒   ░▒██░    ▒▓█  ▄ ▒██▀▀█▄    ▒   ██▒   ▒██   ██░▒██▄█▓▒ ▒",
    "░░██▒██▓ ░██░▒███████▒▒███████▒░██████▒░▒████▒░██▓ ▒██▒▒██████▒▒   ░ ████▓▒░▒██▒ ░  ░",
    "░ ▓░▒ ▒  ░▓  ░▒▒ ▓░▒░▒░▒▒ ▓░▒░▒░ ▒░▓  ░░░ ▒░ ░░ ▒▓ ░▒▓░▒ ▒▓▒ ▒ ░   ░ ▒░▒░▒░ ▒▓▒░ ░  ░",
    "  ▒ ░ ░   ▒ ░░░▒ ▒ ░ ▒░░▒ ▒ ░ ▒░ ░ ▒  ░ ░ ░  ░  ░▒ ░ ▒░░ ░▒  ░ ░     ░ ▒ ▒░ ░▒ ░     ",
    "  ░   ░   ▒ ░░ ░ ░ ░ ░░ ░ ░ ░ ░  ░ ░      ░     ░░   ░ ░  ░  ░     ░ ░ ░ ▒  ░░       ",
    "    ░     ░    ░ ░      ░ ░        ░  ░   ░  ░   ░           ░         ░ ░           ",
]

WIZZLER_ASCII_ALT_2 = [
    " _       ________________   __    __________  _____    ____  ____ ",
    "| |     / /  _/__  /__  /  / /   / ____/ __ \/ ___/   / __ \/ __ \ ",
    "| | /| / // /   / /  / /  / /   / __/ / /_/ /\\__ \\   / / / / /_/ / ",
    "| |/ |/ // /   / /__/ /__/ /___/ /___/ _, _/___/ /  / /_/ / ____/  ",
    "|__/|__/___/  /____/____/_____/_____/_/ |_|/____/   \\____/_/       ",
]

WIZZLER_ASCII_ALT_3 = [
    " █████   ███   █████ █████ ███████████ ███████████ █████       ██████████ ███████████    █████████        ███████    ███████████ ",
    "▒▒███   ▒███  ▒▒███ ▒▒███ ▒█▒▒▒▒▒▒███ ▒█▒▒▒▒▒▒███ ▒▒███       ▒▒███▒▒▒▒▒█▒▒███▒▒▒▒▒███  ███▒▒▒▒▒███     ███▒▒▒▒▒███ ▒▒███▒▒▒▒▒███",
    " ▒███   ▒███   ▒███  ▒███ ▒     ███▒  ▒     ███▒   ▒███        ▒███  █ ▒  ▒███    ▒███ ▒███    ▒▒▒     ███     ▒▒███ ▒███    ▒███",
    " ▒███   ▒███   ▒███  ▒███      ███         ███     ▒███        ▒██████    ▒██████████  ▒▒█████████    ▒███      ▒███ ▒██████████ ",
    " ▒▒███  █████  ███   ▒███     ███         ███      ▒███        ▒███▒▒█    ▒███▒▒▒▒▒███  ▒▒▒▒▒▒▒▒███   ▒███      ▒███ ▒███▒▒▒▒▒▒  ",
    "  ▒▒▒█████▒█████▒    ▒███   ████     █  ████     █ ▒███      █ ▒███ ▒   █ ▒███    ▒███  ███    ▒███   ▒▒███     ███  ▒███        ",
    "    ▒▒███ ▒▒███      █████ ███████████ ███████████ ███████████ ██████████ █████   █████▒▒█████████     ▒▒▒███████▒   █████       ",
    "     ▒▒▒   ▒▒▒      ▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒   ▒▒▒▒▒  ▒▒▒▒▒▒▒▒▒        ▒▒▒▒▒▒▒    ▒▒▒▒▒        ",
]


DEADLIZER_ASCII_ALT_2 = [
    "▓█████▄ ▓█████ ▄▄▄      ▓█████▄  ██▓     ██▓▒███████▒▓█████  ██▀███  ",
    "▒██▀ ██▌▓█   ▀▒████▄    ▒██▀ ██▌▓██▒    ▓██▒▒ ▒ ▒ ▄▀░▓█   ▀ ▓██ ▒ ██▒",
    "░██   █▌▒███  ▒██  ▀█▄  ░██   █▌▒██░    ▒██▒░ ▒ ▄▀▒░ ▒███   ▓██ ░▄█ ▒",
    "░▓█▄   ▌▒▓█  ▄░██▄▄▄▄██ ░▓█▄   ▌▒██░    ░██░  ▄▀▒   ░▒▓█  ▄ ▒██▀▀█▄  ",
    "░▒████▓ ░▒████▒▓█   ▓██▒░▒████▓ ░██████▒░██░▒███████▒░▒████▒░██▓ ▒██▒",
    " ▒▒▓  ▒ ░░ ▒░ ░▒▒   ▓▒█░ ▒▒▓  ▒ ░ ▒░▓  ░░▓  ░▒▒ ▓░▒░▒░░ ▒░ ░░ ▒▓ ░▒▓░",
    " ░ ▒  ▒  ░ ░  ░ ▒   ▒▒ ░ ░ ▒  ▒ ░ ░ ▒  ░ ▒ ░░░▒ ▒ ░ ▒ ░ ░ ░  ░  ░▒ ░ ▒░",
    " ░ ░  ░    ░    ░   ▒    ░ ░  ░   ░ ░    ▒ ░░ ░ ░ ░ ░   ░     ░░   ░ ",
    "   ░       ░  ░     ░  ░   ░        ░  ░ ░    ░ ░       ░  ░   ░     ",
    " ░                       ░                  ░                        ",
]

DEADLIZER_ASCII_ALT_3 = [
    "    ____  _________    ____  __    _________   __________ ",
    "   / __ \\/ ____/   |  / __ \\/ /   /  _/__  /  / ____/ __ \\ ",
    "  / / / / __/ / /| | / / / / /    / /   / /  / __/ / /_/ / ",
    " / /_/ / /___/ ___ |/ /_/ / /____/ /   / /__/ /___/ _, _/  ",
    "/_____/_____/_/  |_/_____/_____/___/  /____/_____/_/ |_|   ",
]

DEADLIZER_ASCII_ALT_4 = [
    " ██████████   ██████████   █████████   ██████████   █████       █████ ███████████ ██████████ ███████████  ",
    "▒▒███▒▒▒▒███ ▒▒███▒▒▒▒▒█  ███▒▒▒▒▒███ ▒▒███▒▒▒▒███ ▒▒███       ▒▒███ ▒█▒▒▒▒▒▒███ ▒▒███▒▒▒▒▒█▒▒███▒▒▒▒▒███ ",
    " ▒███   ▒▒███ ▒███  █ ▒  ▒███    ▒███  ▒███   ▒▒███ ▒███        ▒███ ▒     ███▒   ▒███  █ ▒  ▒███    ▒███ ",
    " ▒███    ▒███ ▒██████    ▒███████████  ▒███    ▒███ ▒███        ▒███      ███     ▒██████    ▒██████████  ",
    " ▒███    ▒███ ▒███▒▒█    ▒███▒▒▒▒▒███  ▒███    ▒███ ▒███        ▒███     ███      ▒███▒▒█    ▒███▒▒▒▒▒███ ",
    " ▒███    ███  ▒███ ▒   █ ▒███    ▒███  ▒███    ███  ▒███      █ ▒███   ████     █ ▒███ ▒   █ ▒███    ▒███ ",
    " ██████████   ██████████ █████   █████ ██████████   ███████████ █████ ███████████ ██████████ █████   █████",
    "▒▒▒▒▒▒▒▒▒▒   ▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒   ▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒   ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒   ▒▒▒▒▒ ",
]


FORDEADLIZER_ASCII_ALT_5 = [
    " ________    _______       __       ________   ___        __   ________    _______   _______   ",
    "|\"      \"\\  /\"     \"|     /\"\"\\     |\"      \"\\ |\"  |      |\" \\ (\"      \"\\  /\"     \"| /\"      \\  ",
    "(.  ___  :)(: ______)    /    \\    (.  ___  :)||  |      ||  | \\___/   :)(: ______)|:        | ",
    "|: \\   ) || \\/    |     /' /\\  \\   |: \\   ) |||:  |      |:  |   /  ___/  \\/    |  |_____/   ) ",
    "(| (___\\ || // ___)_   //  __'  \\  (| (___\\ || \\  |___   |.  |  //  \\__   // ___)_  //      /  ",
    "|:       :)(:      \"| /   /  \\\\  \\ |:       :)( \\_|:  \\  /\\  |\\(:   / \"\\ (:      \"||:  __   \\  ",
    "(________/  \\_______)(___/    \\___)(________/  \\_______)(__\\_|_)\\_______) \\_______)|__|  \\___) ",
]

WIZZLER_ASCII_STYLES = [WIZZLER_ASCII, WIZZLER_ASCII_ALT_1, WIZZLER_ASCII_ALT_2, WIZZLER_ASCII_ALT_3, WIZZLER_ASCII_ALT_4]
DEADLIZER_ASCII_STYLES = [DEADLIZER_ASCII, DEADLIZER_ASCII_ALT_2, DEADLIZER_ASCII_ALT_3, DEADLIZER_ASCII_ALT_4, FORDEADLIZER_ASCII_ALT_5]

# Simplified startup banner for small screens
STARTUP_BANNER = [
    "                             __xxxxxxxxxxxxxxxx___.                    ",
    "                        _gxXXXXXXXXXXXXXXXXXXXXXXXX!x_                ",
    "                   __x!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!x_           ",
    "                ,gXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx_         ",
    "              ,gXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!_       ",
    "            _!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!.     ",
    "          gXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXs    ",
    "        ,!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!.  ",
    "       g!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!   ",
    "      iXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!  ",
    "     ,XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx ",
    "     !XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx",
    "   ,XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx",
    "   !XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXi",
    "  dXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "  !XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "   XXXXXXXXXXXXXXXXXXXf~~~VXXXXXXXXXXXXXXXXXXXXXXXXXXvvvvvvvvXXXXXXXXXXXXXX!",
    "   !XXXXXXXXXXXXXXXf`       'XXXXXXXXXXXXXXXXXXXXXXf`          '~XXXXXXXXXXP",
    "    vXXXXXXXXXXXX!            !XXXXXXXXXXXXXXXXXX!              !XXXXXXXXX",
    "     XXXXXXXXXXv`              'VXXXXXXXXXXXXXXX                !XXXXXXXX!",
    "     !XXXXXXXXX.                 YXXXXXXXXXXXXX!                XXXXXXXXX",
    "      XXXXXXXXX!                 ,XXXXXXXXXXXXXX                VXXXXXXX!",
    "      'XXXXXXXX!                ,!XXXX ~~XXXXXXX               iXXXXXX~",
    "       'XXXXXXXX               ,XXXXXX   XXXXXXXX!             xXXXXXX!",
    "        !XXXXXXX!xxxxxxs______xXXXXXXX   'YXXXXXX!          ,xXXXXXXXX",
    "         YXXXXXXXXXXXXXXXXXXXXXXXXXXX`    VXXXXXXX!s. __gxx!XXXXXXXXXP",
    "          XXXXXXXXXXXXXXXXXXXXXXXXXX!      'XXXXXXXXXXXXXXXXXXXXXXXXX!",
    "          XXXXXXXXXXXXXXXXXXXXXXXXXP        'YXXXXXXXXXXXXXXXXXXXXXXX!",
    "          XXXXXXXXXXXXXXXXXXXXXXXX!     i    !XXXXXXXXXXXXXXXXXXXXXXXX",
    "          XXXXXXXXXXXXXXXXXXXXXXXX!     XX   !XXXXXXXXXXXXXXXXXXXXXXXX",
    "          XXXXXXXXXXXXXXXXXXXXXXXXx_   iXX_,_dXXXXXXXXXXXXXXXXXXXXXXXX",
    "          XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXP",
    "          XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "           ~vXvvvvXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXf",
    "                    'VXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXvvvvvv~",
    "                      'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX~",
    "                  _    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXv`",
    "                 -XX!  !XXXXXXX~XXXXXXXXXXXXXXXXXXXXXX~   Xxi",
    "                  YXX  '~ XXXXX XXXXXXXXXXXXXXXXXXXX`     iXX`",
    "                  !XX!    !XXX` XXXXXXXXXXXXXXXXXXXX      !XX",
    "                  !XXX    '~Vf  YXXXXXXXXXXXXXP YXXX     !XXX",
    "                  !XXX  ,_      !XXP YXXXfXXXX!  XXX     XXXV",
    "                  !XXX !XX           'XXP 'YXX!       ,.!XXX!",
    "                  !XXXi!XP  XX.                  ,_  !XXXXXX!",
    "                  iXXXx X!  XX! !Xx.  ,.     xs.,XXi !XXXXXXf",
    "                   XXXXXXXXXXXXXXXXX! _!XXx  dXXXXXXX.iXXXXXX",
    "                   VXXXXXXXXXXXXXXXXXXXXXXXxxXXXXXXXXXXXXXXX!",
    "                   YXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXV",
    "                    'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
    "                    'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXf",
    "                       VXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXf",
    "                         VXXXXXXXXXXXXXXXXXXXXXXXXXXXXv`",
    "                          ~vXXXXXXXXXXXXXXXXXXXXXXXf`",
    "                              ~vXXXXXXXXXXXXXXXXv~",
    "                                 '~VvXXXXXXXV~~",
    "                                       ~~",
]

def show_startup_banner():
    """Simplified startup banner with minimal animation for small screens"""
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
    except Exception:
        cols = 80
        rows = 24
    
    # Skip animation if screen is too small
    if rows < 20 or cols < 60:
        for line in STARTUP_BANNER:
            print(line[:cols-1])
        time.sleep(1)
        os.system("cls") if os.name == "nt" else os.system("clear")
        return
    
    sys.stdout.write("\033[?25l")  # Hide cursor
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    
    # Simple fade-in for small screens
    banner_block = STARTUP_BANNER
    total_lines = min(len(banner_block), rows - 4)
    banner_block = banner_block[:total_lines]
    
    max_width = max(len(line) for line in banner_block)
    max_width = min(max_width, cols - 4)
    
    # Simple reveal animation
    frames = 10  # Reduced from original
    for frame in range(frames):
        if skipper.should_skip:
            break
        sys.stdout.write("\033[H")
        t = frame / max(frames - 1, 1)
        
        for row_idx, line in enumerate(banner_block):
            if row_idx >= rows - 2:
                break
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, char in enumerate(line[:max_width]):
                if char == ' ':
                    output += " "
                    continue
                # Simple color cycle
                hue = (col_idx * 2 + row_idx * 3 + frame * 8) % 360
                r, g, b = hsv_to_rgb(hue, 0.8, 0.6 + 0.4 * t)
                output += f"\033[38;2;{r};{g};{b}m{char}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.05)
    
    if not skipper.should_skip:
        time.sleep(0.3)
    skipper.stop()
    sys.stdout.write("\033[?25h")  # Show cursor
    os.system("cls") if os.name == "nt" else os.system("clear")


def gradient_text(text, start_color, end_color, bold=True):
    def rgb_to_256(r, g, b):
        r = round(r / 255 * 5)
        g = round(g / 255 * 5)
        b = round(b / 255 * 5)
        return 16 + (36 * r) + (6 * g) + b

    visible_length = 0
    i = 0
    while i < len(text):
        if text[i] == '\033':
            end = text.find('m', i)
            i = end + 1 if end != -1 else i + 1
        else:
            visible_length += 1
            i += 1
    
    if visible_length == 0:
        return text

    result = ""
    current_idx = 0
    i = 0
    while i < len(text):
        if text[i] == '\033':
            end = text.find('m', i)
            if end != -1:
                result += text[i:end+1]
                i = end + 1
            else:
                result += text[i]
                i += 1
        else:
            ratio = current_idx / max(visible_length - 1, 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            color_code = rgb_to_256(r, g, b)
            if bold:
                result += f"\033[1m\033[38;5;{color_code}m{text[i]}"
            else:
                result += f"\033[38;5;{color_code}m{text[i]}"
            current_idx += 1
            i += 1
    result += "\033[0m"
    return result


def get_mode_colors():
    if __mode__ == "deadlizer":
        return DEADLIZER_START, DEADLIZER_END
    else:
        return WIZZLER_START, WIZZLER_END


def format_log_message(status, message, padding=50):
    grey = "\033[90m"
    reset = "\033[0m"

    timestamp = f"{grey}[{datetime.now():%Y-%m-%d %H:%M:%S}]{reset}"
    user_tag = f"{grey}~ Codez On Top {reset}"

    mode_start, mode_end = get_mode_colors()

    # Calculate visible length for accurate padding
    visible_len = 0
    _t_idx = 0
    while _t_idx < len(message):
        if message[_t_idx] == '\033':
            _end = message.find('m', _t_idx)
            _t_idx = _end + 1 if _end != -1 else _t_idx + 1
        else:
            visible_len += 1
            _t_idx += 1
    
    padded_msg = message + " " * max(0, padding - visible_len)

    if status == "SUCCESS":
        status_text = gradient_text(
            "(+) SUCCESS", GREEN_START, GREEN_END, bold=True)
        msg_text = gradient_text(
            padded_msg,
            GREEN_START,
            GREEN_END,
            bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}"

    elif status == "ERROR":
        status_text = gradient_text("(-) ERROR", RED_START, RED_END, bold=True)
        msg_text = gradient_text(
            padded_msg,
            RED_START,
            RED_END,
            bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}"

    elif status == "INPUT":
        grey = "\033[90m"
        reset = "\033[0m"
        bracket_open = gradient_text(
            "(", WIZZLER_START, WIZZLER_END, bold=True)
        bracket_close = gradient_text(
            ")", WIZZLER_START, WIZZLER_END, bold=True)
        status_text = bracket_open + grey + "INP" + reset + bracket_close + \
            " " + gradient_text("INPUT", mode_start, mode_end, bold=True)
        msg_text = gradient_text(
            padded_msg,
            mode_start,
            mode_end,
            bold=True)
        arrow = gradient_text(">", mode_start, mode_end, bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}  {arrow}  "

    else:
        status_text = gradient_text(
            "(~) INFO", mode_start, mode_end, bold=True)
        msg_text = gradient_text(
            padded_msg,
            mode_start,
            mode_end,
            bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}"


def _carnage_effect():
    """SYMBIOTE APOCALYPSE - Simplified for small screens"""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    
    try:
        cols, rows = os.get_terminal_size()
        # Limit for small screens
        cols = min(cols, 100)
        rows = min(rows, 30)
    except Exception:
        cols, rows = 80, 24

    # Simplified color functions
    def blood_color(i, flicker=0.0):
        i = max(0.0, min(1.0, i))
        f = 1.0 + flicker * random.uniform(-0.2, 0.2)
        return (min(255, int((200 * i + 30) * f)), min(255, int(5 * i * f)), min(255, int(10 * i * f)))

    # Reduced frames and particles
    frames = 20  # Reduced from original
    tentacles = []
    num_tentacles = min(20, cols // 4)  # Fewer tentacles for small screens
    
    for i in range(num_tentacles):
        side = i % 4
        if side == 0:   tx, ty = random.randint(0, cols-1), 0
        elif side == 1: tx, ty = random.randint(0, cols-1), rows-1
        elif side == 2: tx, ty = 0, random.randint(0, rows-1)
        else:           tx, ty = cols-1, random.randint(0, rows-1)
        angle = math.atan2(rows//2 - ty, cols//2 - tx) + random.uniform(-0.5, 0.5)
        tentacles.append({
            'x': float(tx), 'y': float(ty),
            'angle': angle,
            'speed': random.uniform(1.0, 2.5),
            'wave_amp': random.uniform(0.5, 1.5),
            'wave_freq': random.uniform(0.1, 0.3),
            'wave_phase': random.uniform(0, math.pi * 2),
            'history': [(tx, ty)],
            'max_hist': random.randint(10, 25),
            'thickness': 2,
            'char': random.choice("╠╣╦╩╬╔╗╚╝║═▓█▒░@#&%$~≈≋"),
            'age': 0,
            'spawn_delay': i * 1.0,
            'pulse_offset': random.uniform(0, math.pi * 2),
        })

    TENTACLE_CHARS = "╠╣╦╩╬╔╗╚╝║═▓█▒░@#&%$~≈≋"
    VEIN_CHARS = "│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌"

    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]

        # Draw tentacles
        for tent in tentacles:
            if frame < tent['spawn_delay']: continue
            tent['age'] += 1
            perp_angle = tent['angle'] + math.pi / 2
            wave_offset = tent['wave_amp'] * math.sin(tent['age'] * tent['wave_freq'] + tent['wave_phase'])
            dx = cols // 2 - tent['x']
            dy = rows // 2 - tent['y']
            steer_angle = math.atan2(dy, dx)
            angle_diff = steer_angle - tent['angle']
            while angle_diff > math.pi: angle_diff -= 2*math.pi
            while angle_diff < -math.pi: angle_diff += 2*math.pi
            tent['angle'] += angle_diff * 0.05 + random.uniform(-0.1, 0.1)
            tent['x'] = (tent['x'] + math.cos(tent['angle']) * tent['speed'] + math.cos(perp_angle) * wave_offset) % cols
            tent['y'] = (tent['y'] + math.sin(tent['angle']) * tent['speed'] + math.sin(perp_angle) * wave_offset * 0.5) % rows
            px, py = int(tent['x']), int(tent['y'])
            if 0 <= px < cols and 0 <= py < rows:
                tent['history'].append((px, py))
            if len(tent['history']) > tent['max_hist']:
                tent['history'].pop(0)

            hist_len = len(tent['history'])
            for h_idx, (hx, hy) in enumerate(tent['history']):
                if not (0 <= hx < cols and 0 <= hy < rows): continue
                seg_t = h_idx / max(hist_len - 1, 1)
                body_pulse = 0.7 + 0.3 * math.sin(frame * 0.3 + tent['pulse_offset'] + seg_t * math.pi)
                r, g, b = blood_color(seg_t * body_pulse, flicker=0.1)
                ch = random.choice(TENTACLE_CHARS) if h_idx == hist_len - 1 else random.choice(VEIN_CHARS)
                grid[hy][hx] = ch
                cgrid[hy][hx] = (r, g, b)

        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                r, g, b = cgrid[r_idx][c_idx]
                line_out += f"\033[38;2;{r};{g};{b}m{ch}" if ch != " " else " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)

    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _cyberpunk_effect():
    """SINGULARITY REBOOT - Simplified for small screens"""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    
    try:
        cols, rows = os.get_terminal_size()
        cols = min(cols, 100)
        rows = min(rows, 30)
    except Exception:
        cols, rows = 80, 24

    def neon_color(t, hue_shift=0.0):
        h = (t * 360 + hue_shift) % 360
        s, v = 0.8, 1.0
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60:   r2, g2, b2 = c, x, 0
        elif h < 120: r2, g2, b2 = x, c, 0
        elif h < 180: r2, g2, b2 = 0, c, x
        elif h < 240: r2, g2, b2 = 0, x, c
        elif h < 300: r2, g2, b2 = x, 0, c
        else:         r2, g2, b2 = c, 0, x
        return int((r2+m)*255), int((g2+m)*255), int((b2+m)*255)

    # Simplified banner
    w_banner = [line.center(cols) for line in WIZZLER_ASCII]
    banner_start = rows // 2 - len(w_banner) // 2

    frames = 20  # Reduced
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / max(frames - 1, 1)
        shock_radius = t * max(cols, rows) * 0.6
        ring_width = 3 + frame * 0.2
        
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                dist = math.sqrt((c_idx - cols/2)**2 + ((r_idx - rows/2) * 2)**2)
                in_ring = abs(dist - shock_radius) < ring_width
                inside = dist < shock_radius
                line_idx = r_idx - banner_start
                is_banner = (0 <= line_idx < len(w_banner) and
                             c_idx < len(w_banner[line_idx]) and
                             w_banner[line_idx][c_idx] != " ")
                if in_ring:
                    ring_t = 1.0 - abs(dist - shock_radius) / ring_width
                    r2, g2, b2 = neon_color(frame * 0.04, hue_shift=c_idx * 1.5 + 200)
                    r2 = min(255, int(r2 * ring_t + 150 * ring_t))
                    g2 = min(255, int(g2 * ring_t + 150 * ring_t))
                    b2 = min(255, int(b2 * ring_t + 150 * ring_t))
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice('█▓▒░')}"
                elif inside and is_banner:
                    h_blend = c_idx / max(cols-1, 1)
                    r2 = int(WIZZLER_START[0]*(1-h_blend) + WIZZLER_END[0]*h_blend)
                    g2 = int(WIZZLER_START[1]*(1-h_blend) + WIZZLER_END[1]*h_blend)
                    b2 = int(WIZZLER_START[2]*(1-h_blend) + WIZZLER_END[2]*h_blend)
                    pulse = 0.8 + 0.2 * math.sin(frame * 0.3 + c_idx * 0.05)
                    line_out += f"\033[1m\033[38;2;{min(255,int(r2*pulse))};{min(255,int(g2*pulse))};{min(255,int(b2*pulse))}m{w_banner[line_idx][c_idx]}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)

    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _menu_fade_out(color_start, color_end):
    import sys
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
        cols = min(cols, 100)
        rows = min(rows, 30)
    except Exception:
        cols = 80
        rows = 24

    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    steps = 4  # Reduced from original
    for step in range(steps):
        if skipper.should_skip:
            break
        t = step / max(steps - 1, 1)
        fade = 1.0 - t
        sys.stdout.write("\033[H")
        for row in range(rows):
            line = ""
            for c in range(cols):
                if random.random() < fade * 0.3:
                    h_blend = c / max(cols - 1, 1)
                    r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                    g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                    b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                    r = min(255, int(r * fade))
                    g = min(255, int(g * fade))
                    b = min(255, int(b * fade))
                    line += f"\033[38;2;{r};{g};{b}m{random.choice('|||| ')}"
                else:
                    line += " "
            sys.stdout.write(line + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.04)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _animate_menu_options(options_text, color_start, color_end):
    import sys, math
    try:
        term_cols = os.get_terminal_size().columns
        term_cols = min(term_cols, 100)
    except Exception:
        term_cols = 80
    cols = max(term_cols, 80)

    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    raw_lines = options_text.split('\n')
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    lines = raw_lines

    sparkle_chars = "+*.:o^"

    def render_line(line, color_start, color_end, cols, sparkle=False, step=0, row_idx=0, visible_chars=None):
        pad = max((cols - len(line)) // 2, 0)
        output = ""
        for col_idx, ch in enumerate(line):
            h_blend = col_idx / max(len(line) - 1, 1)
            r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
            g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
            b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
            if visible_chars is not None and col_idx < visible_chars:
                if sparkle:
                    wave = math.sin(col_idx * 0.2 - step * 0.8 + row_idx * 0.3) * 0.5 + 0.5
                    if wave > 0.88 and ch.strip() and random.random() < 0.3:
                        output += f"\033[38;2;{min(255,r+80)};{min(255,g+80)};{min(255,b+80)}m{random.choice(sparkle_chars)}"
                        continue
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            else:
                output += " "
        return " " * pad + "\033[1m" + output + "\033[0m"

    n = len(lines)
    for _ in lines:
        sys.stdout.write("\n")

    slide_steps = 8  # Reduced from original
    for step in range(slide_steps + 1):
        if skipper.should_skip:
            break
        t = step / slide_steps
        sys.stdout.write(f"\033[{n}A")
        for row_idx, line in enumerate(lines):
            row_delay = row_idx * 0.3
            row_t = max(0.0, min(1.0, (t * (slide_steps + row_delay)) / (slide_steps + n * 0.3)))
            row_ease = 1 - (1 - row_t) ** 3
            visible_chars = int(row_ease * len(line))
            sys.stdout.write(render_line(line, color_start, color_end, cols,
                sparkle=True, step=step, row_idx=row_idx,
                visible_chars=visible_chars) + "\n")
        sys.stdout.flush()
        time.sleep(0.025)

    # Final render
    if skipper.should_skip:
        sys.stdout.write(f"\033[{n}A")
        for row_idx, line in enumerate(lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, ch in enumerate(line):
                h_blend = col_idx / max(len(line) - 1, 1)
                r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()

    skipper.stop()


def _animate_typewriter_log(status, message, padding=50):
    import sys, time, random
    full_msg = format_log_message(status, message, padding)
    segments = []
    current_esc = ""
    i = 0
    while i < len(full_msg):
        if full_msg[i] == '\033':
            end = full_msg.find('m', i)
            if end != -1:
                current_esc += full_msg[i:end + 1]
                i = end + 1
            else:
                current_esc += full_msg[i]
                i += 1
        else:
            segments.append((current_esc, full_msg[i]))
            current_esc = ""
            i += 1
    
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    # Speed up typing for small screens
    for k in range(1, len(segments) + 1):
        if skipper.should_skip:
            break
        sys.stdout.write("\r")
        out = "".join(e + c for e, c in segments[:k])
        cursor = "█" if k % 2 == 0 else " "
        sys.stdout.write(out + f"\033[38;2;255;255;255m{cursor}\033[0m")
        sys.stdout.flush()
        time.sleep(random.uniform(0.008, 0.02))
    
    skipper.stop()
    sys.stdout.write("\r" + full_msg + "   \n")
    sys.stdout.flush()


def _animate_guild_list(guilds, color_start, color_end):
    import sys, time, random, math
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    os.system("cls") if os.name == "nt" else os.system("clear")
    
    try:
        term_cols, term_rows = os.get_terminal_size()
        term_cols = min(term_cols, 100)
    except Exception:
        term_cols, term_rows = 80, 24

    header_text = "Available Guilds:"
    padding_val = min(70, term_cols - 10)
    box_top = "╭" + "─" * padding_val + "╮"
    box_bot = "╰" + "─" * padding_val + "╯"
    
    guild_lines = []
    for i, guild in enumerate(guilds):
        name = str(guild.get('name', 'Unknown'))[:30]
        gid = str(guild.get('id', 'N/A'))
        line = f"│ {i+1:>3} │ {name:<30} │ ID: {gid:<20}  │"
        guild_lines.append(line)

    all_lines = [box_top] + guild_lines + [box_bot]
    n = len(all_lines)

    def render_line(line, row_idx, step, visible_chars=None, sparkle=True):
        pad = max((term_cols - len(line)) // 2, 0)
        output = ""
        v_ratio = row_idx / max(n - 1, 1)
        for col_idx, ch in enumerate(line):
            h_ratio = col_idx / max(len(line)-1, 1)
            mix = (h_ratio * 0.4 + v_ratio * 0.6)
            r = int(color_start[0] * (1 - mix) + color_end[0] * mix)
            g = int(color_start[1] * (1 - mix) + color_end[1] * mix)
            b = int(color_start[2] * (1 - mix) + color_end[2] * mix)
            
            if visible_chars is not None and col_idx < visible_chars:
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            else:
                output += " "
        return " " * pad + "\033[1m" + output + "\033[0m"

    print(format_log_message("INFO", header_text, 50))
    
    # Faster reveal
    total_frames = 12
    for frame in range(total_frames):
        if skipper.should_skip:
            break
        if frame > 0:
            sys.stdout.write(f"\033[{n}A")
        
        t = frame / (total_frames - 1)
        for row_idx, line in enumerate(all_lines):
            row_delay = row_idx * 0.3
            row_t = max(0.0, min(1.0, (t * (8 + row_delay)) / 8))
            visible = int(row_t * len(line))
            sys.stdout.write(render_line(line, row_idx, frame, visible_chars=visible) + "\n")
        sys.stdout.flush()
        time.sleep(0.025)

    # Final static render
    if not skipper.should_skip:
        sys.stdout.write(f"\033[{n}A")
    else:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print(format_log_message("INFO", header_text, 50))

    for row_idx, line in enumerate(all_lines):
        pad = max((term_cols - len(line)) // 2, 0)
        v_ratio = row_idx / max(n - 1, 1)
        out = ""
        for col_idx, ch in enumerate(line):
            h_ratio = col_idx / max(len(line)-1, 1)
            mix = (h_ratio * 0.4 + v_ratio * 0.6)
            r = int(color_start[0] * (1 - mix) + color_end[0] * mix)
            g = int(color_start[1] * (1 - mix) + color_end[1] * mix)
            b = int(color_start[2] * (1 - mix) + color_end[2] * mix)
            out += f"\033[38;2;{r};{g};{b}m{ch}"
        sys.stdout.write(" " * pad + "\033[1m" + out + "\033[0m\n")
    sys.stdout.flush()
    
    skipper.stop()


def _menu_load_animation(banner_lines, color_start, color_end, mode_label):
    """Simplified menu loading animation for small screens"""
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    
    try:
        cols = os.get_terminal_size().columns
        term_rows = os.get_terminal_size().lines
        cols = min(cols, 100)
    except Exception:
        cols = 80
        term_rows = 24

    total_lines = len(banner_lines)
    max_width = min(max(len(line) for line in banner_lines) if banner_lines else 40, cols - 4)
    
    # Simple reveal animation
    phase1_frames = 12  # Reduced
    lock_frame = []
    for row_idx, line in enumerate(banner_lines):
        row_locks = []
        for col_idx in range(len(line)):
            cx, cy = max_width / 2, total_lines / 2
            dist = math.sqrt((col_idx - cx) ** 2 + ((row_idx - cy) * 3) ** 2)
            max_dist = math.sqrt(cx ** 2 + (cy * 3) ** 2)
            progress = dist / max(max_dist, 1)
            lock_at = int(3 + progress * (phase1_frames - 8)) + random.randint(-2, 2)
            lock_at = max(2, min(phase1_frames - 2, lock_at))
            row_locks.append(lock_at)
        lock_frame.append(row_locks)

    for frame in range(phase1_frames):
        if skipper.should_skip:
            break
        if frame > 0:
            sys.stdout.write(f"\033[{total_lines}A")
        t = frame / max(phase1_frames - 1, 1)
        hue_base = 240 if color_start == WIZZLER_START else 320

        for row_idx, line in enumerate(banner_lines):
            if len(line) > max_width:
                line = line[:max_width]
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, real_char in enumerate(line):
                locked = frame >= lock_frame[row_idx][col_idx]
                if real_char == ' ':
                    ch = ' '
                elif not locked:
                    reveal_chance = (frame / lock_frame[row_idx][col_idx]) ** 2
                    ch = real_char if random.random() < reveal_chance * 0.6 else ' '
                else:
                    ch = real_char
                if ch != ' ':
                    hue = hue_base + ((col_idx * 2 + row_idx * 6 + frame * 10) % 120)
                    val = min(1.0, t * 1.5)
                    r, g, b = hsv_to_rgb(hue, 0.8, val)
                    output += f"\033[38;2;{r};{g};{b}m{ch}"
                else:
                    output += " "
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.05)

    # Loading bar
    print()
    bar_width = min(30, cols - 20)
    label = f"  LOADING {mode_label.upper()}  "
    pad = max((cols - bar_width - len(label) - 4) // 2, 0)
    load_steps = bar_width
    for i in range(load_steps + 1):
        if skipper.should_skip:
            break
        filled = "|" * i
        empty = "|" * (bar_width - i)
        pct = int((i / load_steps) * 100)
        h_blend = i / max(load_steps, 1)
        r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
        g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
        b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
        bar_str = f"\033[38;2;{r};{g};{b}m\033[1m[{filled}{empty}] {pct:3d}%\033[0m"
        sys.stdout.write(f"\r{' ' * pad}{label}{bar_str}")
        sys.stdout.flush()
        time.sleep(0.02)
    sys.stdout.write("\n")

    ready_msg = format_log_message("SUCCESS", f"{mode_label} Menu Ready", 40)
    if not skipper.should_skip:
        print(ready_msg)
        time.sleep(0.3)
    else:
        print(ready_msg)

    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _wizzler_switch_hyperdrive():
    """HYPERDRIVE - Simplified for small screens"""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
        cols = min(cols, 100)
        rows = min(rows, 30)
    except Exception:
        cols, rows = 80, 24

    cx, cy = cols / 2, rows / 2
    stars = []
    num_stars = min(80, cols * 2)  # Reduced
    for _ in range(num_stars):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(2, 15)
        stars.append({'angle': angle, 'dist': dist, 'speed': random.uniform(0.1, 0.4), 'char': random.choice(".*+")})

    frames = 25  # Reduced
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]
        
        t = frame / frames
        speed_mult = 1.0 + t * 10.0

        for star in stars:
            star['dist'] += star['speed'] * speed_mult
            x = int(cx + math.cos(star['angle']) * star['dist'] * 1.5)
            y = int(cy + math.sin(star['angle']) * star['dist'])
            if 0 <= x < cols and 0 <= y < rows:
                if frame > frames * 0.6:
                    r = int(WIZZLER_START[0]*(1-t) + WIZZLER_END[0]*t)
                    g = int(WIZZLER_START[1]*(1-t) + WIZZLER_END[1]*t)
                    b = int(WIZZLER_START[2]*(1-t) + WIZZLER_END[2]*t)
                    grid[y][x] = random.choice("■█▓▒")
                    cgrid[y][x] = (r, g, b)
                else:
                    intensity = min(1.0, star['dist'] / 15.0)
                    val = int(200 * intensity)
                    grid[y][x] = star['char']
                    cgrid[y][x] = (val, val, 255)
            elif star['dist'] > max(cols, rows):
                star['dist'] = random.uniform(1, 4)
                star['angle'] = random.uniform(0, math.pi * 2)

        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.025)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _wizzler_switch_neural():
    """NEURAL GRID - Simplified for small screens"""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
        cols = min(cols, 100)
        rows = min(rows, 30)
    except Exception:
        cols, rows = 80, 24

    num_nodes = min(30, cols // 3)
    nodes = [{'x': random.randint(0, cols-1), 'y': random.randint(0, rows-1), 'active': False} for _ in range(num_nodes)]
    active_nodes = [nodes[0]]
    nodes[0]['active'] = True

    frames = 25  # Reduced
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        if frame % 3 == 0 and len(active_nodes) < len(nodes):
            inactive = [n for n in nodes if not n['active']]
            if inactive:
                new_node = random.choice(inactive)
                new_node['active'] = True
                active_nodes.append(new_node)
        
        for n1 in active_nodes:
            grid[n1['y']][n1['x']] = "◉"
            cgrid[n1['y']][n1['x']] = (255, 255, 255)
            for n2 in active_nodes:
                if n1 != n2:
                    dist = math.hypot(n1['x'] - n2['x'], n1['y'] - n2['y'])
                    if dist < 12:
                        steps = int(dist)
                        for s in range(1, steps):
                            nx = int(n1['x'] + (n2['x'] - n1['x']) * (s / steps))
                            ny = int(n1['y'] + (n2['y'] - n1['y']) * (s / steps))
                            if 0 <= nx < cols and 0 <= ny < rows:
                                grid[ny][nx] = random.choice(".-*")
                                r = int(WIZZLER_START[0]*(1-t) + WIZZLER_END[0]*t)
                                g = int(WIZZLER_START[1]*(1-t) + WIZZLER_END[1]*t)
                                b = int(WIZZLER_START[2]*(1-t) + WIZZLER_END[2]*t)
                                cgrid[ny][nx] = (r, g, b)
        
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.035)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


# Keep the rest of the functions but with reduced animation where needed
# The following functions are kept as-is or with minimal changes since they're
# called infrequently or are critical for functionality

async def switch_to_wizzler():
    global __mode__, WIZZLER_START, WIZZLER_END, __max_concurrent__
    __mode__ = "wizzler"
    __max_concurrent__ = __config__.get("max_concurrent", 50)
    WIZZLER_START, WIZZLER_END = pick_random_gradient()
    
    # Reduced set of effects
    effect = random.choice([
        _cyberpunk_effect, 
        _wizzler_switch_hyperdrive, 
        _wizzler_switch_neural
    ])

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    
    try:
        if asyncio.iscoroutinefunction(effect):
            await effect()
        else:
            effect()
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        
    return True


__bot_user_id__ = None
__bot_user_name__ = None
__bot_user_discriminator__ = None
__bot_guilds__ = []

__config__ = None
__loaded_configs__ = {}
__current_config_name__ = None
__config_index__ = 0
config_folder = "configs"


async def switch_to_deadlizer():
    global __mode__, __max_concurrent__, DEADLIZER_START, DEADLIZER_END
    __mode__ = "deadlizer"
    __max_concurrent__ = __config__.get("max_concurrent", 50) * 3 
    DEADLIZER_START, DEADLIZER_END = pick_random_gradient()
    
    effect = random.choice([
        _carnage_effect
    ])

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    
    try:
        if asyncio.iscoroutinefunction(effect):
            await effect()
        else:
            effect()
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        
    return True


# The rest of the code remains unchanged (switch_config, load_multiple_configs, 
# _passkey_gate, shakti class, etc.) since they contain the core functionality
# and the menu system which already handles screen size adaptively.

# Note: The shakti class and its menu method are large but already handle
# screen sizing with min() and max() operations. The menu options display
# will automatically adapt to the terminal width.

print("Codez On Top - Optimized for small screens")
