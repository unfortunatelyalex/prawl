import time
import random
import win32con
import ctypes
from ctypes import Structure, c_long, c_ulong, sizeof, POINTER, pointer, byref, c_ushort
from typing import Union, List
import logging
from scripts.constants import RANDOM_VARIATION_FACTOR

logger = logging.getLogger(__name__)

# Windows API constants for keyboard input
INPUT_KEYBOARD = 1        # keyboard input mode
KEYEVENTF_KEYUP = 0x0002   # key release

# Input structures for Windows API
class MOUSEINPUT(Structure):
    """Structure for mouse input events."""
    _fields_ = [
        ('dx', c_long),
        ('dy', c_long),
        ('mouseData', c_ulong),
        ('dwFlags', c_ulong),
        ('time', c_ulong),
        ('dwExtraInfo', POINTER(c_ulong))
    ]

class KEYBDINPUT(Structure):
    """Structure for keyboard input events."""
    _fields_ = [
        ('wVk', c_ushort),
        ('wScan', c_ushort),
        ('dwFlags', c_ulong),
        ('time', c_ulong),
        ('dwExtraInfo', POINTER(c_ulong))
    ]

class _INPUTunion(ctypes.Union):
    """Union for different input types."""
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT)
    ]

class INPUT(Structure):
    """Main input structure for Windows API."""
    _fields_ = [
        ('type', c_ulong),
        ('union', _INPUTunion)
    ]

# Keyboard input emulation using Windows API
class Keyboard:
    """
    Keyboard input emulation using Windows SendInput API.
    Provides methods for pressing keys, combinations, and sequences.
    """
    
    def __init__(self):
        # Load user32.dll to access Windows UI functions
        try:
            self.user32 = ctypes.windll.user32
        except Exception as e:
            logger.error(f"Failed to load user32.dll: {e}")
            raise

        # Key mappings for special keys
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

        # Add number keys (0-9)
        for i in range(10):
            self.key_mapping[str(i)] = ord(str(i))

        # Add letter keys (a-z)
        for c in 'abcdefghijklmnopqrstuvwxyz':
            self.key_mapping[c] = ord(c.upper())

    def _create_input(self, key: Union[str, int], key_up: bool = False) -> INPUT:
        """
        Create Windows INPUT structure for keyboard event.
        
        Args:
            key: Key to create input for (string or virtual key code)
            key_up: Whether this is a key release event
            
        Returns:
            Windows INPUT structure
        """
        inp = INPUT()
        inp.type = INPUT_KEYBOARD

        # Determine virtual key code
        if isinstance(key, str) and len(key) == 1:
            vk_code = ord(key.upper())
        elif isinstance(key, str) and key.lower() in self.key_mapping:
            vk_code = self.key_mapping[key.lower()]
        else:
            vk_code = key

        # Get scan code from virtual key code
        scan_code = self.user32.MapVirtualKeyW(vk_code, 0)
        
        # Set up keyboard input structure
        inp.union.ki.wVk = vk_code
        inp.union.ki.wScan = scan_code
        inp.union.ki.dwFlags = KEYEVENTF_KEYUP if key_up else 0
        inp.union.ki.time = 0
        inp.union.ki.dwExtraInfo = pointer(c_ulong(0))
        
        return inp

    def press(self, key: Union[str, int]) -> bool:
        """
        Press down a key (without releasing).
        
        Args:
            key: Key to press
            
        Returns:
            True if successful, False otherwise
        """
        try:
            inp = self._create_input(key)
            result = self.user32.SendInput(1, byref(inp), sizeof(INPUT))
            return result == 1
        except Exception as e:
            logger.error(f"Error pressing key {key}: {e}")
            return False

    def release(self, key: Union[str, int]) -> bool:
        """
        Release a key.
        
        Args:
            key: Key to release
            
        Returns:
            True if successful, False otherwise
        """
        try:
            inp = self._create_input(key, key_up=True)
            result = self.user32.SendInput(1, byref(inp), sizeof(INPUT))
            return result == 1
        except Exception as e:
            logger.error(f"Error releasing key {key}: {e}")
            return False

    def keypress(self, key: Union[str, int], hold: int = 80) -> bool:
        """
        Perform a complete keypress (press and release).
        
        Args:
            key: Key to press
            hold: Hold duration in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add random variation to hold time
            variation = RANDOM_VARIATION_FACTOR
            hold_time = random.uniform(
                hold * (1 - variation) / 1000, 
                hold * (1 + variation) / 1000
            )
            
            if not self.press(key):
                return False
                
            time.sleep(hold_time)
            return self.release(key)
            
        except Exception as e:
            logger.error(f"Error in keypress for {key}: {e}")
            return False

    def combo(self, keys: List[Union[str, int]], hold: int = 80) -> bool:
        """
        Perform a key combination (press all keys, hold, then release all).
        
        Args:
            keys: List of keys to press in combination
            hold: Hold duration in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Press all keys in sequence
            for i, key in enumerate(keys):
                if not self.press(key):
                    # Clean up - release any keys that were pressed
                    for pressed_key in keys[:i]:
                        self.release(pressed_key)
                    return False
                time.sleep(random.uniform(0.01, 0.02))
            
            # Hold the combination
            variation = RANDOM_VARIATION_FACTOR
            hold_time = random.uniform(
                hold * (1 - variation) / 1000, 
                hold * (1 + variation) / 1000
            )
            time.sleep(hold_time)
            
            # Release all keys in reverse order
            for key in reversed(keys):
                if not self.release(key):
                    logger.warning(f"Failed to release key {key} in combo")
                time.sleep(random.uniform(0.01, 0.02))
                
            return True
            
        except Exception as e:
            logger.error(f"Error in key combo {keys}: {e}")
            return False
