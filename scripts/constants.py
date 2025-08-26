"""
Constants for the Prawl application.
Centralizes magic numbers and configuration values.
"""

# Timer and gameplay constants
DEFAULT_MATCH_TIME_MINUTES = 25
EXP_PER_MINUTE_RATIO = 1000 / 25  # 1000 exp per 25 minutes
GOLD_PER_MINUTE_RATIO = 250 / 25  # 250 gold per 25 minutes

# Rate limiting constants
EXP_RATE_LIMIT_THRESHOLD = 13000
DEFAULT_RATE_LIMIT_WAIT_TIME_MINUTES = 45

# Input timing constants (in milliseconds)
DEFAULT_KEYPRESS_HOLD_MS = 70
DEFAULT_KEYPRESS_DELAY_MS = 150
RANDOM_VARIATION_FACTOR = 0.1  # ±10% variation

# Threading and timing constants
DEFAULT_UPDATE_TIMEOUT_SECONDS = 10
GRACEFUL_SHUTDOWN_WAIT_SECONDS = 2
COOLDOWN_TIMER_DURATION_SECONDS = 2.0

# Audio constants
DEFAULT_BEEP_FREQUENCY = 500
DEFAULT_BEEP_DURATION_MS = 72

# UI constants
MIN_WINDOW_WIDTH = 291
MIN_WINDOW_HEIGHT = 169
WINDOW_TITLE = 'prawl'

# File paths
CONFIG_FILENAME = 'config.ini'
ICON_PATH = 'res/prawl-app.ico'
MAIN_FONT_PATH = 'res/cq-pixel-min.ttf'
ICON_FONT_PATH = 'res/Piconic.ttf'

# Default configuration values
DEFAULT_CONFIG = {
    'match_time': DEFAULT_MATCH_TIME_MINUTES,
    'timer_sound': False,
    'always_on_top': True,
    'game_start_spam': 12,
    'game_restart_delay': 4,
    'game_load_time': 15,
    'menu_key_presses': 2,
    'menu_key_presses_delay': 0,
    'disconnect_delay': 100,
    'reconnect_delay': 4,
    'open_menu_default': True,
    'open_menu_fix': False,
    'open_menu_fix2': False,
    'open_menu_hold': False,
    'open_menu_enter': True,
    'direct_input': False,
    'keypress_hold': DEFAULT_KEYPRESS_HOLD_MS,
    'keypress_delay': DEFAULT_KEYPRESS_DELAY_MS,
    'beep_frequency': DEFAULT_BEEP_FREQUENCY,
    'beep_duration': DEFAULT_BEEP_DURATION_MS,
    'rate_limit_detect': True,
    'rate_limit_wait': True,
    'rate_limit_wait_time': DEFAULT_RATE_LIMIT_WAIT_TIME_MINUTES,
    'max_games': False,
    'max_games_amount': 16,
    'auto_launch': False,
    'key_light': 'c',
    'key_heavy': 'x',
    'key_throw': 'v',
    'key_left': 'left',
    'key_up': 'up',
    'key_right': 'right',
    'key_down': 'down',
}