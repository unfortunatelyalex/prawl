import time
import threading
import winsound
import dearpygui.dearpygui as dpg
from typing import List, Optional, Callable
import logging
from scripts.constants import (
    EXP_PER_MINUTE_RATIO, 
    GOLD_PER_MINUTE_RATIO, 
    EXP_RATE_LIMIT_THRESHOLD,
    DEFAULT_RATE_LIMIT_WAIT_TIME_MINUTES
)

# Set up logging
logger = logging.getLogger(__name__)

def calculate_exp(minutes: float) -> float:
    """Calculate experience points based on minutes played."""
    return minutes * EXP_PER_MINUTE_RATIO

def calculate_gold(minutes: float) -> float:
    """Calculate gold based on minutes played."""
    return minutes * GOLD_PER_MINUTE_RATIO

class Timer:
    def __init__(self, config: dict, keyseq, state: dict):
        self.keyseq = keyseq
        self.state = state
        self.initial_time = 0
        self.remaining_time = 0
        self.waiting_time = config.get('rate_limit_wait_time', DEFAULT_RATE_LIMIT_WAIT_TIME_MINUTES) * 60
        self.running = False
        self.paused = False
        self.pressing = False
        self._timer_thread: Optional[threading.Thread] = None
        self.on_stop_callback: Optional[Callable] = None

    def set_on_stop_callback(self, callback: Callable) -> None:
        """Set callback function to be called when timer stops."""
        self.on_stop_callback = callback

    def start(self, minutes: int, sequence: List[str]) -> None:
        """
        Start the timer with specified duration and action sequence.
        
        Args:
            minutes: Duration in minutes
            sequence: List of action sequences to execute
        """
        if self.running:
            dpg.configure_item('farm_status', label='already active')
            return
            
        try:
            self.initial_time = minutes * 60
            self.remaining_time = self.initial_time
            self.sequence = sequence
            self.running = True
            self.paused = False
            self._timer_thread = threading.Thread(target=self._run, daemon=True)
            self._timer_thread.start()
            logger.info(f"Timer started for {minutes} minutes with sequence: {sequence}")
        except Exception as e:
            logger.error(f"Error starting timer: {e}")
            self.running = False

    def stop(self) -> None:
        """Stop the timer and clean up resources."""
        try:
            if self.on_stop_callback:
                self.on_stop_callback()
        except Exception as e:
            logger.error(f"Error in stop callback: {e}")
            
        dpg.configure_item('farm_status', label='stopping...')
        self.running = False
        
        # Wait for thread to finish with timeout
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=5)
            
        self._timer_thread = None
        dpg.configure_item('farm_status', label='inactive')
        logger.info("Timer stopped")

    def pause(self) -> None:
        """Toggle pause state of the timer."""
        if self.running:
            self.paused = not self.paused
            status = 'paused' if self.paused else 'resumed'
            dpg.configure_item('farm_status', label=f'{status}')
            logger.info(f"Timer {status}")

    def _run(self) -> None:
        """Main timer loop - runs in separate thread."""
        try:
            while self.running:
                self.pressing = True
                self.keyseq.action(self.sequence, lambda: self.running, self.state['hwnd'])
                self.pressing = False

                if 'lobby_setup_finish' in self.sequence:
                    self.stop()
                    return

                while self.remaining_time > 0 and self.running:
                    if self.paused:
                        while self.paused and self.running:
                            time.sleep(1)
                        continue
                        
                    mins, secs = divmod(self.remaining_time, 60)
                    dpg.configure_item('farm_status', label=f'active ({mins}:{secs:02})')
                    time.sleep(1)
                    self.remaining_time -= 1

                if self.remaining_time == 0 and self.running:
                    self._handle_timer_completion()

        except Exception as e:
            logger.error(f"Error in timer thread: {e}")
            self.running = False
        finally:
            dpg.configure_item('farm_status', label='inactive')

    def _handle_timer_completion(self) -> None:
        """Handle actions when timer completes a cycle."""
        try:
            # Play sound if enabled
            if dpg.get_value('timer_sound'):
                winsound.Beep(dpg.get_value('beep_frequency'), dpg.get_value('beep_duration'))

            # Update statistics
            exp_gain = calculate_exp(self.initial_time / 60)
            gold_gain = calculate_gold(self.initial_time / 60)
            self.state['total_games'] += 1
            self.state['total_gold'] += gold_gain
            self.state['total_exp'] += exp_gain
            self.state['current_exp'] += exp_gain
            
            # Update UI
            dpg.configure_item('total_games', label=int(self.state['total_games']))
            dpg.configure_item('total_gold', label=int(self.state['total_gold']))
            dpg.configure_item('total_exp', label=int(self.state['total_exp']))

            # Handle rate limiting
            if dpg.get_value('rate_limit_detect') and self.state['current_exp'] >= EXP_RATE_LIMIT_THRESHOLD:
                dpg.configure_item('farm_status', label='exp rate limit...')
                if dpg.get_value('rate_limit_wait'):
                    self._wait_for_rate_limit_reset()
                else:
                    self.stop()
                    return

            self.remaining_time = self.initial_time

            # Check max games limit
            if dpg.get_value('max_games') and self.state['total_games'] >= dpg.get_value('max_games_amount'):
                dpg.configure_item('farm_status', label='max games reached...')
                self.stop()
                return
                
        except Exception as e:
            logger.error(f"Error handling timer completion: {e}")

    def _wait_for_rate_limit_reset(self) -> None:
        """Wait for rate limit to reset."""
        self.remaining_time = self.waiting_time
        while self.remaining_time > 0 and self.running:
            mins, secs = divmod(self.remaining_time, 60)
            dpg.configure_item('farm_status', label=f'exp rate limit reset in {mins}:{secs:02}')
            time.sleep(1)
            self.remaining_time -= 1
        self.state['current_exp'] = 0
