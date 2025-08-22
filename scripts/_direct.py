import time
import random
import win32con
import ctypes
from ctypes import Structure, c_long, c_ulong, sizeof, POINTER, pointer, byref, c_ushort

# this uses SendInput from Windows API that emulates synthetic mouse / keyboard inputs
# i couldnt get this to work with other libraries i know of so this is a temporary solutionb

# keyboard event flags
INPUT_KEYBOARD     =    1        # keyboard input mode
KEYEVENTF_KEYUP    =    0x0002   # key release

# input structures
class MOUSEINPUT(Structure):
    _fields_ = [
        ('dx', c_long),
        ('dy', c_long),
        ('mouseData', c_ulong),
        ('dwFlags', c_ulong),
        ('time', c_ulong),
        ('dwExtraInfo', POINTER(c_ulong))
    ]

class KEYBDINPUT(Structure):
    _fields_ = [
        ('wVk', c_ushort),
        ('wScan', c_ushort),
        ('dwFlags', c_ulong),
        ('time', c_ulong),
        ('dwExtraInfo', POINTER(c_ulong))
    ]

class _INPUTunion(ctypes.Union):
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT)
    ]

class INPUT(Structure):
    _fields_ = [
        ('type', c_ulong),
        ('union', _INPUTunion)
    ]

# keyboard input emulation
class Keyboard:
    def __init__(self):

        # load user32.dll to access windows ui functions with ctypes
        self.user32 = ctypes.windll.user32

        # add misc key mappings
        self.key_mapping = {
            'shift': win32con.VK_SHIFT,
            'enter': win32con.VK_RETURN,
            'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB,
            'backspace': win32con.VK_BACK,
            'escape': win32con.VK_ESCAPE,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
        }

        # add number keys
        for i in range(10):
            self.key_mapping[str(i)] = ord(str(i))

        # add letter keys
        for c in 'abcdefghijklmnopqrstuvwxyz':
            self.key_mapping[c] = ord(c.upper())

    # thing
    def _handle_exceptions(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f'error in {func.__name__}: {e}')
                return False
        return wrapper

    # create keyboard input structure
    def _create_input(self, key, key_up=False):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD

        # single characters
        if isinstance(key, str) and len(key) == 1:
            vk_code = ord(key.upper())

        # special keys
        elif isinstance(key, str) and key.lower() in self.key_mapping:
            vk_code = self.key_mapping[key.lower()]

        # misc keys
        else:
            vk_code = key

        # get scan code from virtual key code
        scan_code = self.user32.MapVirtualKeyW(vk_code, 0)
        inp.union.ki.wVk = vk_code
        inp.union.ki.wScan = scan_code
        inp.union.ki.dwFlags = KEYEVENTF_KEYUP if key_up else 0
        inp.union.ki.time = 0
        inp.union.ki.dwExtraInfo = pointer(c_ulong(0))
        return inp

    # hold down key
    def press(self, key) -> bool:
        inp = self._create_input(key)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))
        return True

    # release the key
    def release(self, key) -> bool:
        inp = self._create_input(key, key_up=True)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))
        return True

    # simple keypress
    def keypress(self, key, hold:int = 80) -> bool:
        hold_time = random.uniform(hold * 0.9 / 1000, hold * 1.1 / 1000)
        if not self.press(key):
            return False
        time.sleep(hold_time)
        return self.release(key)

    # combination of two or more keys
    def combo(self, keys:list, hold:int = 80) -> bool:
        for key in keys:
            if not self.press(key):
                return False
            time.sleep(random.uniform(0.01, 0.02))
        hold_time = random.uniform(hold * 0.9 / 1000, hold * 1.1 / 1000)
        time.sleep(hold_time)
        for key in reversed(keys):
            if not self.release(key):
                return False
            time.sleep(random.uniform(0.01, 0.02))
        return True
