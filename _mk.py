import time
import random
import math
import win32con
import ctypes
from ctypes import Structure, c_long, c_ulong, sizeof, POINTER, pointer, byref, c_ushort

# this uses SendInput from Windows API that emulates mouse / keyboard inputs
# i couldnt get this to work with other libraries i know of so this is a temporary solutionb

# mouse event flags
INPUT_MOUSE              =   0        # mouse input mode
MOUSEEVENTF_MOVE         =   0x0001   # mouse moved

MOUSEEVENTF_VIRTUALDESK  =   0x4000   # coordinates to the entire virtual desktop, useful for setups with more than one monitor
MOUSEEVENTF_ABSOLUTE     =   0x8000   # specifies dx and dy are absolute screen coordinates instead of relative

MOUSEEVENTF_LEFTDOWN     =   0x0002   # left mouse button pressed
MOUSEEVENTF_LEFTUP       =   0x0004   # left mouse button released

MOUSEEVENTF_RIGHTDOWN    =   0x0008   # right mouse button pressed
MOUSEEVENTF_RIGHTUP      =   0x0010   # right mouse button released

MOUSEEVENTF_MIDDLEDOWN   =   0x0020   # middle mouse button pressed
MOUSEEVENTF_MIDDLEUP     =   0x0040   # middle mouse button released

MOUSEEVENTF_WHEEL        =   0x0800   # vertical scroll
MOUSEEVENTF_HWHEEL       =   0x1000   # horizontal scroll

# keyboard event flags
INPUT_KEYBOARD           =   1        # keyboard input mode
KEYEVENTF_KEYUP          =   0x0002   # key release

SM_CXSCREEN              =   0        # system metric dimension X
SM_CYSCREEN              =   1        # system metric dimension Y

# input structures rahhhhhhh
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

class Mouse:
    def __init__(self):

        # load user32.dll to access windows ui functions with ctypes
        self.user32 = ctypes.windll.user32

        # get actual screen metrics stuff
        self.screen_width = self.user32.GetSystemMetrics(SM_CXSCREEN)
        self.screen_height = self.user32.GetSystemMetrics(SM_CYSCREEN)

        # set mouse button mappings
        self.button_mappings = {
            'l': [MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP],
            'r': [MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP],
            'm': [MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP]
        }

        # set mouse smoothing mappings 
        self.smoothing_mappings = {
            'ease_in': self._ease_in,
            'ease_out': self._ease_out,
            'ease_in_out': self._ease_in_out,
            'linear': self._linear
        }

    # create input structure
    def _create_input(self, flags, x=0, y=0, data=0):
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dx = x
        inp.union.mi.dy = y
        inp.union.mi.mouseData = data
        inp.union.mi.dwFlags = flags
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = pointer(c_ulong(0))
        return inp

    # get current primary monitor absolute coords
    def _abs_coords(self, x, y):

        # windows expects coordinates in range 0-65535
        x = max(0, min(x, self.screen_width))
        y = max(0, min(y, self.screen_height))

        # scale the coordinates
        scaled_x = int((x * 65535) / self.screen_width)
        scaled_y = int((y * 65535) / self.screen_height)

        # make sure to not exceed min/max values
        return (min(65535, scaled_x), min(65535, scaled_y))

    # movement smoothing methods
    def _ease_in(self, t):
        return t * t

    def _ease_out(self, t):
        return t * (2 - t)

    def _ease_in_out(self, t):
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t

    def _linear(self, t):
        return t

    # generate movement points path
    def _gen_path(self, start_x, start_y, end_x, end_y, steps, easing_fn = None):

        # default to ease_in_out if no easing function is provided
        if easing_fn is None:
            easing_fn = self._ease_in_out

        # set control points for generating path using the current cursor position and target position
        control_x = random.uniform(min(start_x, end_x), max(start_x, end_x))
        control_y = random.uniform(min(start_y, end_y), max(start_y, end_y))

        # precompute the easing values
        eased_t = [easing_fn(i / steps) for i in range(steps + 1)]

        # reutrn list of 2d points of quadratic bezier curve guhhh
        return [
            (
                int((1 - t)**2 * start_x + 2 * (1 - t) * t * control_x + t**2 * end_x),
                int((1 - t)**2 * start_y + 2 * (1 - t) * t * control_y + t**2 * end_y)
            )
            for t in eased_t
        ]

    # validate smoothing methods
    def _validate_smoothing(self, smoothing):
        if smoothing.lower() not in self.smoothing_mappings:
            raise ValueError(f"invalid smoothing option '{smoothing}', choose from: {list(self.smoothing_mappings.keys())}")
        return self.smoothing_mappings[smoothing.lower()]

    # validate mouse buttons
    def _validate_button(self, button: str) -> list:
        if button.lower() not in self.button_mappings:
            raise ValueError(f"invalid mouse button '{button}', choose from: {list(self.button_mappings.keys())}")
        return self.button_mappings[button.lower()]

    # so i dont have to repeat try excepts in every single thing yeah
    def _handle_exceptions(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f'error in {func.__name__}: {e}')
                return False
        return wrapper

    # move the cursor to screen coordinates
    @_handle_exceptions
    def move(self, x:int, y:int, duration:int = 500, smoothing='ease_in_out') -> bool:
        """
        move the mouse to x y location on current screen

        ---
        args:
            x (int): x coordinate
            y (int): y coordinate
            duration (int): duration it takes to move there (ms)
        returns:
            bool: true if press succeeded, false otherwise
        """

        # get current cursor position
        class POINT(Structure):
            _fields_ = [("x", c_long), ("y", c_long)]
        pt = POINT()
        self.user32.GetCursorPos(byref(pt))
        start_x, start_y = pt.x, pt.y

        # calculate distance of start and target coordinates, adjust steps
        distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)
        steps = max(10, min(50, int(distance / 10)))

        # generate movement path points
        smoothing = self._validate_smoothing(smoothing)
        points = self._gen_path(start_x, start_y, x, y, steps, smoothing)

        # move through points
        step_delay = duration / steps / 1000
        for px, py in points:

            # convert to absolute coordinates
            abs_x, abs_y = self._abs_coords(px, py)

            # create input structure
            inp = self._create_input(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, abs_x, abs_y)

            # send input
            self.user32.SendInput(1, byref(inp), sizeof(INPUT))

            # add small random delay in between each step
            time.sleep(random.uniform(step_delay * 0.8, step_delay * 1.2))
        
        # success
        return True

    # hold down a mouse button
    @_handle_exceptions
    def press(self, button:str) -> bool:
        """
        press mouse button

        ---
        args:
            button (str): mouse button to press, options are: 'l', 'r', 'm'
        returns:
            bool: true if press succeeded, false otherwise
        """

        # set flag for input structure
        flags = self._validate_button(button)[0]

        # create input structure with flag
        inp = self._create_input(flags)

        # send input
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

        # success
        return True

    # releases a mouse button
    @_handle_exceptions
    def release(self, button:str) -> bool:
        """
        release mouse button

        ---
        args:
            button (str): mouse button to release, options are: 'l', 'r', 'm'
        returns:
            bool: true if press succeeded, false otherwise
        """

        # set flag for input structure
        flags = self._validate_button(button)[1]

        # create input structure with flag
        inp = self._create_input(flags)

        # send input
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

        # success
        return True

    # click mouse button
    @_handle_exceptions
    def click(self, button:str = 'l', hold:int = 70) -> bool:
        """
        simulate a mouse click

        ---
        args:
            button (str): mouse button to click, options are: 'l', 'r', 'm'
            hold (int): time in milliseconds to hold the button down (default: 70)
        returns:
            bool: true if click succeeded, false otherwise
        """

        # add a 10% offset from original value to add randomness, also convert milliseconds to seconds
        hold_time = random.uniform(hold * 0.9 / 1000, hold * 1.1 / 1000)

        # press / release logic lol
        if not self.press(button):
            return False
        time.sleep(hold_time)
        return self.release(button)

    # scroll wheel
    @_handle_exceptions
    def scroll(self, delta:int) -> bool:
        """
        simluate mouse scroll

        ---
        args:
            delta (int): amount to scroll; positive for up, negative for down
        returns:
            bool: true if scroll succeeded, false otherwise
        """
        # create input structure with flag
        inp = self._create_input(MOUSEEVENTF_WHEEL, data=delta)
        
        # send input
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

        # success
        return True

# keyboard input emulation
class Keyboard:
    def __init__(self):

        # load user32.dll to access windows ui functions with ctypes
        self.user32 = ctypes.windll.user32

        # add misc key mappings, will extend later
        self.key_mapping = {
            'shift': win32con.VK_SHIFT,
            'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU,
            'enter': win32con.VK_RETURN,
            'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB,
            'backspace': win32con.VK_BACK,
            'delete': win32con.VK_DELETE,
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
    @_handle_exceptions
    def press(self, key) -> bool:
        """
        press down a keyboard key

        ---
        args:
            key (str or vk): key to press
        returns:
            bool: true if press succeeded, false otherwise
        """
        inp = self._create_input(key)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))
        return True

    # release the key
    @_handle_exceptions
    def release(self, key) -> bool:
        """
        release a keyboard key

        ---
        args:
            key (str or vk): key to release
        returns:
            bool: true if release succeeded, false otherwise
        """
        inp = self._create_input(key, key_up=True)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))
        return True

    # simple keypress
    @_handle_exceptions
    def keypress(self, key, hold:int = 80) -> bool:
        """
        simluate a keypress

        ---
        args:
            key (str or vk): key to release
        returns:
            bool: true if keypress succeeded, false otherwise
        """
        hold_time = random.uniform(hold * 0.9 / 1000, hold * 1.1 / 1000)
        if not self.press(key):
            return False
        time.sleep(hold_time)
        return self.release(key)

    # combination of two or more keys
    @_handle_exceptions
    def combo(self, keys:list, hold:int = 80) -> bool:
        """
        simluate pressing a combination of keys

        ---
        args:
            keys (list): list of keys to press
        returns:
            bool: true if combo succeeded, false otherwise
        """
        # press keys
        for key in keys:
            if not self.press(key):
                return False
            time.sleep(random.uniform(0.01, 0.02)) 

        # hold
        hold_time = random.uniform(hold * 0.9 / 1000, hold * 1.1 / 1000)
        time.sleep(hold_time)

        # release keys
        for key in reversed(keys):
            if not self.release(key):
                return False
            time.sleep(random.uniform(0.01, 0.02))

        return True



if __name__ == '__main__':
    mouse = Mouse()
    print(mouse.move(1200,500, smoothing='ease_in_out'))
    print(mouse.click())
    keyboard = Keyboard()
    print(keyboard.keypress(win32con.VK_SPACE))