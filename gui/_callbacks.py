import subprocess
import time
import winsound
import webbrowser
import threading
import dearpygui.dearpygui as dpg
import scripts.window as window
import logging
from typing import Optional, Tuple
from scripts.timer import calculate_exp, calculate_gold
from scripts.input import KeyListener

logger = logging.getLogger(__name__)

class CooldownTimer:
    def __init__(self, duration, callback):
        self._duration = duration
        self._callback = callback
        self._timer = None

    def start(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self._duration, self._callback)
        self._timer.start()

    def cancel(self):
        if self._timer:
            self._timer.cancel()

class Callbacks:
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.config = self.gui.config
        self.timer = self.gui.timer
        self.keyseq = self.gui.keyseq
        self.state = self.gui.state
        self.update = self.gui.update
        self.listener = KeyListener()
        self.launch_timer = CooldownTimer(2.0, self._launch_state_reset)
        self.launch_count = 0
        self.timing_timer = CooldownTimer(2.0, self._general_state_reset)
        self.timing_count = 0

    # ui nav buttons
    # ---------------------------------------------------
    def show_main_group(self, sender, app_data, user_data):
        dpg.hide_item('settings_group')
        dpg.hide_item('help_group')
        dpg.show_item('main_group')

    def show_settings_group(self, sender, app_data, user_data):
        dpg.hide_item('main_group')
        dpg.hide_item('help_group')
        dpg.show_item('settings_group')

    def show_help_group(self, sender, app_data, user_data):
        dpg.hide_item('main_group')
        dpg.hide_item('settings_group')
        dpg.show_item('help_group')

    # main page
    # ---------------------------------------------------
    def run_button(self):
        if self.timer.running:
            self.timer.stop()
        else:
            self.state['hwnd'] = window.find()
            if self.state['hwnd']:
                sequence = ['wait_restart', 'spam_menu', 'open_menu', 'disconnect', 'reconnect']
                if dpg.get_value('open_menu_hold'):
                    sequence = ['open_menu_hold' if item == 'open_menu' else item for item in sequence]
                if dpg.get_value('open_menu_fix'):
                    sequence = ['open_menu_fix' if item == 'open_menu' else item for item in sequence]
                if dpg.get_value('open_menu_fix2'):
                    sequence = [sub for item in sequence for sub in (['open_menu_fix', 'open_menu_fix'] if item == 'open_menu' else [item])]
                self.timer.start(dpg.get_value('match_time'), sequence)
                if self.timer.running:
                    dpg.configure_item('run_button', label='ä')
                    dpg.configure_item('run_button_tooltip', default_value='stop')

            else:
                dpg.configure_item('farm_status', label='brawlhalla window not found')

    def stop_button(self):
        self.timer.stop()

    def on_timer_stopped(self):
        with dpg.mutex():
            dpg.set_frame_callback(
                dpg.get_frame_count() + 1,
                callback=lambda: [dpg.configure_item('run_button', label='â'), dpg.configure_item('run_button_tooltip', default_value='start')]
            )

    # ---------------------------------------------------

    def oops_button(self):
        self.state['hwnd'] = window.find()
        if self.state['hwnd'] and self.timer.running and not self.timer.pressing:
            self.timer.pause()
            sequence = ['open_menu', 'disconnect', 'reconnect']
            if dpg.get_value('open_menu_hold'):
                sequence = ['open_menu_hold' if item == 'open_menu' else item for item in sequence]
            self.keyseq.action(sequence, lambda: self.timer.running, self.state['hwnd'])
            self.timer.pause()
        else:
            dpg.configure_item('farm_status', label='not running')

    def toggle_button(self):
        self.state['hwnd'] = window.find()
        if not self.state['hwnd']:
            dpg.configure_item('farm_status', label='brawlhalla window not found')
            return
        if window.visible(self.state['hwnd']):
            window.hide(self.state['hwnd'])
            dpg.configure_item('farm_status', label='brawlhalla window hidden')
            dpg.configure_item('toggle_button', label='N')
            dpg.configure_item('toggle_button_tooltip', default_value='show brawlhalla window')
        else:
            window.show(self.state['hwnd'])
            dpg.configure_item('farm_status', label='brawlhalla window shown')
            dpg.configure_item('toggle_button', label='O')
            dpg.configure_item('toggle_button_tooltip', default_value='hide brawlhalla window')

    def _launch_state_reset(self):
        self.launch_count = 0
        text = 'stop brawlhalla' if window.running() else 'start brawlhalla'
        dpg.configure_item('farm_status', label='inactive')
        dpg.configure_item('launch_button_tooltip', default_value=text)
    def launch_button(self):
        """Handle Brawlhalla launch/close button with error recovery."""
        try:
            if window.running():
                self.launch_count += 1
                if self.launch_count == 1:
                    dpg.configure_item('farm_status', label='already running! (close?)')
                    dpg.configure_item('launch_button_tooltip', default_value='click again to stop')
                    self.launch_timer.start()
                elif self.launch_count == 2:
                    dpg.configure_item('farm_status', label='terminating brawlhalla...')
                    dpg.configure_item('launch_button_tooltip', default_value='start brawlhalla')
                    
                    # Safely close the game
                    if window.close():
                        dpg.configure_item('farm_status', label='brawlhalla terminated')
                    else:
                        dpg.configure_item('farm_status', label='failed to terminate brawlhalla')
                        
                    self.launch_count = 0
                    self.launch_timer.cancel()
                    self.timer.stop()
            else:
                try:
                    # Launch Brawlhalla through Steam
                    result = subprocess.run(
                        'cmd /c start steam://rungameid/291550', 
                        check=False, 
                        timeout=10,
                        capture_output=True
                    )
                    
                    dpg.configure_item('farm_status', label='starting brawlhalla...')
                    dpg.configure_item('launch_button_tooltip', default_value='stop brawlhalla')
                    
                    # Wait for game to start with timeout
                    start_time = time.time()
                    timeout = 60  # 60 seconds timeout
                    
                    while not window.running() and (time.time() - start_time) < timeout:
                        time.sleep(0.5)
                        
                    if window.running():
                        self.state['hwnd'] = window.find()
                        dpg.configure_item('farm_status', label='brawlhalla started')
                    else:
                        dpg.configure_item('farm_status', label='brawlhalla failed to start (timeout)')
                        dpg.configure_item('launch_button_tooltip', default_value='start brawlhalla')
                        
                except subprocess.TimeoutExpired:
                    dpg.configure_item('farm_status', label='launch command timed out')
                except Exception as e:
                    logger.error(f"Error launching Brawlhalla: {e}")
                    dpg.configure_item('farm_status', label='failed to launch brawlhalla')
                    
        except Exception as e:
            logger.error(f"Error in launch_button: {e}")
            dpg.configure_item('farm_status', label='launch error occurred')

    # ---------------------------------------------------

    def update_values(self, sender, app_data):
        """Update estimated values with input validation."""
        try:
            # Validate input range
            minutes = max(1, min(25, app_data))  # Clamp between 1-25 minutes
            
            estimated_exp = calculate_exp(minutes)
            estimated_gold = calculate_gold(minutes)
            
            dpg.set_value('estimated_values', f'gold: {int(estimated_gold)} | exp: {int(estimated_exp)}')
        except Exception as e:
            logger.error(f"Error updating values: {e}")
            dpg.set_value('estimated_values', 'calculation error')

    def update_slider_format(self, value: int) -> None:
        """Update slider format text with validation."""
        try:
            # Validate value
            value = max(1, min(25, int(value)))
            
            if value == 1:
                dpg.configure_item('match_time', format=f"{value} minute")
            else:
                dpg.configure_item('match_time', format=f"{value} minutes")
        except Exception as e:
            logger.error(f"Error updating slider format: {e}")

    def match_time_slider(self, sender, app_data):
        """Handle match time slider changes with validation."""
        try:
            # Validate and clamp the value
            value = max(1, min(25, int(app_data)))
            
            self.update_slider_format(value)
            self.update_values(sender, value)
        except Exception as e:
            logger.error(f"Error in match time slider: {e}")

    def beep_sound(self) -> None:
        """Play beep sound with error handling."""
        try:
            frequency = dpg.get_value('beep_frequency') if dpg.does_item_exist('beep_frequency') else 500
            duration = dpg.get_value('beep_duration') if dpg.does_item_exist('beep_duration') else 72
            
            # Validate frequency and duration ranges
            frequency = max(37, min(32767, frequency))  # Windows beep frequency limits
            duration = max(1, min(5000, duration))      # Reasonable duration limits
            
            winsound.Beep(int(frequency), int(duration))
        except Exception as e:
            logger.error(f"Error playing beep sound: {e}")

    def beep_reset(self) -> None:
        """Reset beep settings to defaults."""
        try:
            dpg.set_value('beep_frequency', 500)
            dpg.set_value('beep_duration', 72)
        except Exception as e:
            logger.error(f"Error resetting beep settings: {e}")

    # ---------------------------------------------------

    def mini_lobby_setup_start(self):
        self.state['hwnd'] = window.find()
        if self.state['hwnd']:
            self.timer.start(0, ['lobby_setup_game_rules', 'lobby_setup_finish'])

    def full_lobby_setup_start(self):
        self.state['hwnd'] = window.find()
        if self.state['hwnd']:
            self.timer.start(0, ['lobby_setup_game_rules', 'lobby_setup_lobby', 'lobby_setup_finish'])

    # ---------------------------------------------------

    def update_button(self):
        dpg.configure_item('update_button', enabled=False)
        dpg.configure_item('update_link', show=False)
        dpg.set_value('update_status_text', 'checking for updates...')
        thread = threading.Thread(target=self.update_worker, daemon=True)
        thread.start()

    def update_worker(self):
        results = self.update.check()
        with dpg.mutex():
            dpg.set_frame_callback(
                dpg.get_frame_count() + 1,
                callback=self.update_post,
                user_data=results
            )

    def update_post(self, sender, app_data, user_data):
        message, is_update_available = user_data
        dpg.set_value('update_status_text', message)
        if is_update_available and self.update.release_url:
            dpg.configure_item(
                'update_link',
                show=True,
                label=f'download {self.update.latest_version}',
                callback=lambda: webbrowser.open(self.update.release_url)
            )
        dpg.configure_item('update_button', enabled=True)
