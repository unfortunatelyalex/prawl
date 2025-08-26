import win32gui
import win32con
import win32api
import win32process
import win32com.client
from typing import Optional
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find() -> Optional[int]:
    """
    Find the Brawlhalla window handle.
    
    Returns:
        Window handle if found, None otherwise
    """
    hwnd = win32gui.FindWindow(None, 'Brawlhalla')
    if hwnd:
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 
                False, 
                pid
            )
            try:
                proc_name = win32process.GetModuleFileNameEx(handle, 0)
                if 'brawlhalla.exe' in proc_name.lower():
                    return hwnd
            finally:
                # Always close the process handle
                win32api.CloseHandle(handle)
        except Exception as e:
            logger.warning(f"Error checking Brawlhalla process: {e}")
    return None

def running() -> bool:
    """Check if Brawlhalla is currently running."""
    return bool(find())

def show(hwnd: Optional[int]) -> bool:
    """
    Show the specified window.
    
    Args:
        hwnd: Window handle
        
    Returns:
        True if successful, False otherwise
    """
    if hwnd:
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            return True
        except Exception as e:
            logger.error(f"Error showing window: {e}")
    return False

def hide(hwnd: Optional[int]) -> bool:
    """
    Hide the specified window.
    
    Args:
        hwnd: Window handle
        
    Returns:
        True if successful, False otherwise
    """
    if hwnd:
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            return True
        except Exception as e:
            logger.error(f"Error hiding window: {e}")
    return False

def visible(hwnd: Optional[int]) -> bool:
    """
    Check if the window is visible.
    
    Args:
        hwnd: Window handle
        
    Returns:
        True if visible, False otherwise
    """
    if hwnd:
        try:
            return win32gui.IsWindowVisible(hwnd)
        except Exception as e:
            logger.error(f"Error checking window visibility: {e}")
    return False

def activate(hwnd: Optional[int]) -> bool:
    """
    Activate and bring window to foreground.
    
    Args:
        hwnd: Window handle
        
    Returns:
        True if successful, False otherwise
    """
    if hwnd:
        try:
            # Press Alt key before activating (Windows requirement)
            shell = win32com.client.Dispatch('WScript.Shell')
            shell.SendKeys('%')
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Error activating window: {e}")
    return False

def close() -> bool:
    """
    Safely close Brawlhalla process.
    
    Returns:
        True if successful, False otherwise
    """
    hwnd = find()
    if hwnd:
        try:
            # First try graceful close
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            # Give it a moment to close gracefully
            import time
            time.sleep(2)
            
            # Check if it's still running
            if find():
                # If still running, force terminate
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
                try:
                    win32api.TerminateProcess(handle, 0)
                    logger.info("Brawlhalla process terminated")
                    return True
                finally:
                    win32api.CloseHandle(handle)
            else:
                logger.info("Brawlhalla closed gracefully")
                return True
        except Exception as e:
            logger.error(f"Error closing Brawlhalla: {e}")
    return False
