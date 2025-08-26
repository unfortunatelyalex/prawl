import sys
import logging
import dearpygui.dearpygui as dpg
import pywinstyles
import scripts.window as window
from scripts.config import Config, get_platform
from scripts.input import KeySequence
from scripts.timer import Timer
from scripts.update import Update
from scripts._direct import Keyboard
from scripts.constants import WINDOW_TITLE, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
from gui.gui import PrawlGUI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = ['dearpygui', 'win32api', 'win32gui', 'requests']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"Missing required modules: {', '.join(missing_modules)}\n"
        error_msg += "Please install them using: pip install -r requirements.txt"
        logger.error(error_msg)
        print(error_msg)
        return False
    
    return True

def main():
    """Main application entry point."""
    try:
        # Check platform compatibility
        platform = get_platform()
        logger.info(f"Running on platform: {platform}")
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Initialize application state
        state = {
            'total_games': 0,
            'total_gold': 0,
            'total_exp': 0,
            'current_exp': 0,
            'hwnd': None
        }
        
        # Initialize core components
        logger.info("Initializing configuration...")
        config = Config()
        
        logger.info("Initializing keyboard interface...")
        keyboard = Keyboard()
        
        logger.info("Initializing input sequences...")
        keyseq = KeySequence(config.data, keyboard)
        
        logger.info("Initializing timer...")
        timer = Timer(config.data, keyseq, state)
        
        logger.info("Initializing update checker...")
        update = Update(config.version)

        # Setup GUI
        logger.info("Initializing GUI...")
        gui = PrawlGUI(config.data, config.main_font, config.icon_font, timer, keyseq, state, update)
        
        # Create viewport with constants
        dpg.create_viewport(
            title=WINDOW_TITLE,
            min_width=MIN_WINDOW_WIDTH,
            min_height=MIN_WINDOW_HEIGHT,
            width=MIN_WINDOW_WIDTH,
            height=MIN_WINDOW_HEIGHT,
            small_icon=config.icon,
            large_icon=config.icon
        )
        
        # Configure viewport
        if dpg.does_item_exist('always_on_top'):
            dpg.set_viewport_always_top(dpg.get_value('always_on_top'))
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window('main', True)

        # Apply window styling
        try:
            pywinstyles.change_header_color(None, '#2a2a2d')
            pywinstyles.change_border_color(None, "#2a2a2d")
            pywinstyles.change_title_color(None, '#c0c3c7')
        except Exception as e:
            logger.warning(f"Could not apply window styling: {e}")

        # Auto-launch if configured
        if config.data.get('auto_launch', False):
            try:
                gui._launch_callback()
            except Exception as e:
                logger.error(f"Auto-launch failed: {e}")

        logger.info("Starting application...")
        dpg.start_dearpygui()

    except Exception as e:
        logger.error(f"Critical error during startup: {e}")
        return 1
    
    finally:
        # Cleanup
        try:
            logger.info("Saving configuration...")
            config.save()
            
            # Restore window if hidden
            hwnd = window.find()
            if hwnd:
                window.show(hwnd)
            
            logger.info("Destroying GUI context...")
            dpg.destroy_context()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("Application shutdown complete")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
