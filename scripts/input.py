import time
import random
import win32api
import win32con
import dearpygui.dearpygui as dpg
from typing import Optional, List, Dict, Any, Callable, Tuple
import logging
from scripts.window import activate
from scripts._direct import Keyboard
from scripts.constants import (
    DEFAULT_KEYPRESS_HOLD_MS, 
    DEFAULT_KEYPRESS_DELAY_MS, 
    RANDOM_VARIATION_FACTOR,
    DEFAULT_MATCH_TIME_MINUTES
)

logger = logging.getLogger(__name__)

class KeyListener:
    """Handles keyboard input detection for hotkey configuration."""
    
    def __init__(self):
        # Virtual key code mappings for input detection
        self.VK_CODE = {
            'enter': 13, 'esc': 27, 'spacebar': 32,
            'left': 37, 'up': 38, 'right': 39, 'down': 40,
            **{str(i): 48 + i for i in range(10)},  # 0-9
            **{chr(65 + i): 65 + i for i in range(26)},  # A-Z
            **{f'numpad_{i}': 96 + i for i in range(10)},  # Numpad 0-9
            'left_shift': 160, 'right_shift': 161, 
            'left_control': 162, 'right_control': 163,
            '+': 187, ',': 188, '-': 189, '.': 190, '/': 191, 
            '`': 192, ';': 186, '[': 219, '\\': 220, ']': 221, "'": 222
        }
        self.VK_NAME = {v: k for k, v in self.VK_CODE.items()}

    def hotkey(self) -> Optional[str]:
        """
        Wait for and capture a hotkey press.
        
        Returns:
            Key name if captured, None if escaped
        """
        try:
            # Wait for all keys to be released first
            while any(win32api.GetAsyncKeyState(key) for key in self.VK_CODE.values()):
                time.sleep(0.01)
                
            # Wait for key press
            while True:
                for key_code in self.VK_NAME:
                    if win32api.GetAsyncKeyState(key_code) & 0x8000:
                        key_name = self.VK_NAME[key_code]
                        if key_name == 'esc':
                            return None
                        return key_name
                time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in hotkey detection: {e}")
            return None

class KeySequence:
    """Handles execution of keyboard action sequences for game automation."""
    
    def __init__(self, config: Dict[str, Any], keyboard: Keyboard):
        self.keyboard = keyboard
        self.config = config
        self._cache: Optional[Dict] = None
        self._last_d: Optional[str] = None
        self._last_a: Optional[int] = None
        self._last_menu_k: Optional[int] = None

    def _keypress(self, hwnd: int, key, hold: int = None, delay: int = None, direct: bool = False) -> None:
        """
        Send a keypress to the specified window.
        
        Args:
            hwnd: Window handle
            key: Key to press (string or virtual key code)
            hold: Hold duration in milliseconds
            delay: Delay after keypress in milliseconds
            direct: Whether to use direct input mode
        """
        if hold is None:
            hold = DEFAULT_KEYPRESS_HOLD_MS
        if delay is None:
            delay = DEFAULT_KEYPRESS_DELAY_MS
            
        try:
            vk = win32api.VkKeyScan(key) if isinstance(key, str) else key
            
            if direct:
                self.keyboard.keypress(key, hold)
                # Add random variation to delay
                delay_time = random.uniform(delay, delay + 40) / 1000
                time.sleep(delay_time)
            else:
                # Send key down
                win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
                
                # Hold time with variation
                hold_time = random.uniform(
                    (hold - 10) / 1000, 
                    (hold + 20) / 1000
                )
                time.sleep(hold_time)
                
                # Send key up
                win32api.SendMessage(hwnd, win32con.WM_KEYUP, vk, 0)
                
                # Delay with variation
                delay_time = random.uniform(delay, delay + 40) / 1000
                time.sleep(delay_time)
                
        except Exception as e:
            logger.error(f"Error sending keypress {key}: {e}")

    def _validate_dpg_value(self, tag: str, default: Any) -> Any:
        """
        Safely get value from DearPyGUI with fallback.
        
        Args:
            tag: DearPyGUI item tag
            default: Default value if tag doesn't exist
            
        Returns:
            Value from DPG or default
        """
        try:
            if dpg.does_item_exist(tag):
                return dpg.get_value(tag)
            else:
                logger.warning(f"DPG item '{tag}' not found, using default: {default}")
                return default
        except Exception as e:
            logger.error(f"Error getting DPG value for '{tag}': {e}")
            return default

    def _build(self, time_d, time_a, menu_k, hwnd):
        left, up, down, esc = self.config['key_left'], self.config['key_up'], self.config['key_down'], win32con.VK_ESCAPE
        light, heavy, throw = self.config['key_light'], self.config['key_heavy'], self.config['key_throw']

        sequences_data = {
            'wait_restart': [
                ('countdown', 'wait_restart', 'starting game in {}...'),
            ],
            'spam_menu': [
                ('status', 'spamming through menu!'),
                ('press', light, {'count': 'start_spam'}),
                ('countdown', 'wait_gameload', 'waiting for game {}...'),
            ],
            'open_menu': [
                ('status', 'open esc menu'),
                ('press', menu_k, {'count': 'menu_key_presses', 'delay_tag': 'menu_key_presses_delay'}),
            ],
            'disconnect': [
                ('status', 'wait disconnect delay'),
                ('wait', 'wait_disconnect'),
                ('press', up),
                ('press', light),
            ],
            'reconnect': [
                ('countdown', 'wait_reconnect', 'reconnecting in {}...'),
                ('status', 'pressing...'),
                ('press', light, {'count': 2}),
            ],
            'open_menu_fix': [
                ('status', 'esc menu fix...'),
                ('press', menu_k),
                ('press', up),
                ('press', light),
            ],
            'open_menu_hold': [
                ('status', 'open esc menu (hold)'),
                ('press', menu_k, {'count': 2}),
                ('press', menu_k, {'hold': 2}),
            ],
            'lobby_setup_game_rules': [
                ('status', 'GAME RULES'), ('press', heavy),
                ('status', 'selecting CREW BATTLE'), ('press', left, {'count': 6}),
                ('status', 'setting LIVES to 99'), ('press', down, {'count': 3}), ('press', left, {'count': 3}),
                ('status', f'setting MATCH TIME {dpg.get_value("match_time")}'), ('press', down), ('press', time_d, {'count': time_a}),
                ('status', 'setting DAMAGE'), ('press', down, {'count': 2}), ('press', left, {'count': 5}),
                ('status', 'turning gadgets off'), ('press', down, {'count': 2}), ('press', left),
                ('status', 'maps to Tournament 1v1'), ('press', down, {'count': 3}), ('press', left, {'count': 2}),
                ('status', 'setting MAX PLAYERS to 2'), ('press', down), ('press', left, {'count': 2}),
            ],
            'lobby_setup_lobby': [
                ('status', 'LOBBY'), ('press', ']'),
                ('status', 'turning off FRIENDS'), ('press', down, {'count': 3}), ('press', left),
                ('status', 'turning off CLANMATES'), ('press', down), ('press', left),
                ('status', 'setting MAP CHOOSING to Random'), ('press', down, {'count': 2}), ('press', left, {'count': 2}),
                ('status', 'turning on ALLOW HANDICAPS'), ('press', down, {'count': 2}), ('press', left),
                ('status', 'closing menu'), ('press', light, {'delay': 0.5}),
                ('status', 'opening MANAGE PARTY menu'), ('press', throw),
                ('status', 'adding and opening BOT menu'), ('press', light, {'count': 2, 'delay': 0.5}),
                ('status', 'set LIVES to 89'), ('press', down), ('press', left, {'count': 10}),
                ('status', 'set Dmg Done 50%'), ('press', down), ('press', left, {'count': 5}),
                ('status', 'set Dmg Taken 50%'), ('press', down), ('press', left, {'count': 5}),
                ('status', 'switching to P1 menu'), ('press', light), ('press', up), ('press', light),
                ('status', 'set Dmg Done 50%'), ('press', down, {'count': 2}), ('press', left, {'count': 5}),
                ('status', 'set Dmg Taken 50%'), ('press', down), ('press', left, {'count': 5}),
                ('status', 'close MANAGE PARTY menu'), ('press', throw)
            ],
            'lobby_setup_finish': [
                ('press', esc),
                ('status', 'finished lobby setup'),
            ]
        }

        action_map = {}
        for name, steps in sequences_data.items():
            action_list = []
            for step in steps:
                command, args = step[0], step[1:]

                if command == 'status':
                    action_list.append((lambda l=args[0]: dpg.configure_item('farm_status', label=l), 0))

                elif command == 'wait':
                    delay_sec = dpg.get_value(args[0]) / 1000
                    action_list.append((lambda: None, delay_sec))

                elif command == 'countdown':
                    duration_tag, label_template = args[0], args[1]
                    duration = dpg.get_value(duration_tag)
                    for i in range(duration):
                        label = label_template.format(duration - i)
                        action_list.append((lambda l=label: dpg.configure_item('farm_status', label=l), 1))

                elif command == 'press':
                    key = args[0]
                    overrides = args[1] if len(args) > 1 else {}

                    count_val = overrides.get('count', 1)
                    num_repeats = dpg.get_value(count_val) if isinstance(count_val, str) else count_val

                    hold_default = overrides.get('hold', dpg.get_value('keypress_hold'))
                    delay_ms_tag = overrides.get('delay_tag')
                    delay_after = overrides.get('delay', 0)
                    if delay_ms_tag and dpg.does_item_exist(delay_ms_tag):
                        delay_after = dpg.get_value(delay_ms_tag) / 1000

                    for _ in range(num_repeats):
                        action = (lambda k=key, h=hold_default: self._keypress(hwnd, k, h, dpg.get_value('keypress_delay'), dpg.get_value('direct_input')), delay_after)
                        action_list.append(action)

            action_map[name] = action_list
        return action_map

    def action(self, sequences, is_running, hwnd):
        def scrolls(start, target, pos=25):
            r_scroll = (target - start) % pos
            l_scroll = (start - target) % pos
            return (self.config['key_right'], r_scroll) if r_scroll <= l_scroll else (self.config['key_left'], l_scroll)

        TIME_D, TIME_A = scrolls(20, dpg.get_value('match_time'))
        MENU_K = win32con.VK_RETURN if dpg.get_value('open_menu_enter') else win32con.VK_ESCAPE

        action_map = self._build(TIME_D, TIME_A, MENU_K, hwnd)
        actions = [action for seq in sequences if seq in action_map for action in action_map[seq]]
        for action, delay in actions:
            if not is_running(): break
            if dpg.get_value('direct_input'): activate(hwnd)
            action()
            if delay >= 1:
                for _ in range(int(delay)):
                    if not is_running(): break
                    time.sleep(1)
            else:
                time.sleep(delay)
