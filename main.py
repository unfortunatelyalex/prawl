import dearpygui.dearpygui as dpg
import pywinstyles
import scripts.window as window
from scripts.config import Config, get_platform
from scripts.input import KeySequence
from scripts.timer import Timer
from scripts.update import Update
from scripts._direct import Keyboard
from gui.gui import PrawlGUI

if __name__ == '__main__' and get_platform():
    state = {
        'total_games': 0,
        'total_gold': 0,
        'total_exp': 0,
        'current_exp': 0,
        'hwnd': None
    }
    config = Config()
    keyboard = Keyboard()
    keyseq = KeySequence(config.data, keyboard)
    timer = Timer(config.data, keyseq, state)
    update = Update(config.version)

    # setup gui things
    gui = PrawlGUI(config.data, config.main_font, config.icon_font, timer, keyseq, state, update)
    dpg.create_viewport(
        title=f'prawl',
        min_width=291,
        min_height=169,
        width=291,
        height=169,
        small_icon=config.icon,
        large_icon=config.icon
    )
    dpg.set_viewport_always_top(dpg.get_value('always_on_top'))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window('main', True)

    pywinstyles.change_header_color(None, '#2a2a2d')
    pywinstyles.change_border_color(None, "#2a2a2d")
    pywinstyles.change_title_color(None, '#c0c3c7')

    if config.data['auto_launch']:
        gui._launch_callback()

    dpg.start_dearpygui()

    # save config, show window if hidden, and then die
    config.save()
    state['hwnd'] = window.find()
    if state['hwnd']:
        window.show(state['hwnd'])

    dpg.destroy_context()
