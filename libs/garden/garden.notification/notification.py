import os
import sys
import traceback
from ast import literal_eval
from kivy.utils import platform
from subprocess import check_output
from os.path import dirname, abspath, join
from kivy.garden.notification import utils

# platform dependent imports
if platform == 'win':
    import ctypes
    import win32gui
    from win32con import (
        SW_HIDE, SW_SHOW,
        GWL_EXSTYLE, WS_EX_TOOLWINDOW
    )

# get platform dependent values
RESOLUTION = utils.sys_resolution()
_TB = utils.taskbar()

# get width or height only for appropriate sides
TASKBAR = {
    'width': _TB['width'] if _TB['pos'] in ('right', 'left') else 0,
    'height': _TB['height'] if _TB['pos'] in ('bottom', 'top') else 0,
    'pos': _TB['pos']
}

# convert dict passed as a str arg back
KWARGS = literal_eval(sys.argv[1])

# fetch values from Notification.open kwargs
WIDTH = KWARGS['width']
HEIGHT = KWARGS['height']
OFFSET = {
    'x': KWARGS['offset_x'],
    'y': KWARGS['offset_y']
}

# set window from Notification.open arguments
from kivy.config import Config
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'borderless', 1)
Config.set('graphics', 'position', 'custom')

Config.set('graphics', 'width', WIDTH)
Config.set('graphics', 'height', HEIGHT)

# position the notification window according to taskbar
if TASKBAR['pos'] == 'top':
    Config.set(
        'graphics', 'left',
        RESOLUTION['x'] - WIDTH - OFFSET['x'] - TASKBAR['width']
    )
    Config.set(
        'graphics', 'top',
        TASKBAR['height'] + OFFSET['y']
    )
elif TASKBAR['pos'] == 'left':
    Config.set(
        'graphics', 'left',
        TASKBAR['width'] + OFFSET['x']
    )
    Config.set(
        'graphics', 'top',
        RESOLUTION['y'] - HEIGHT - OFFSET['y'] - TASKBAR['height']
    )
else:
    Config.set(
        'graphics', 'left',
        RESOLUTION['x'] - WIDTH - OFFSET['x'] - TASKBAR['width']
    )
    Config.set(
        'graphics', 'top',
        RESOLUTION['y'] - HEIGHT - OFFSET['y'] - TASKBAR['height']
    )

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import StringProperty, ListProperty


class Notification(App):
    title = StringProperty(KWARGS['title'].replace(' ', '') + str(os.getpid()))
    notif_title = StringProperty(KWARGS['title'])
    message = StringProperty(KWARGS['message'])
    notif_icon = StringProperty(KWARGS['icon'])
    background_color = ListProperty(KWARGS['background_color'])
    line_color = ListProperty(KWARGS['line_color'])
    color = ListProperty(KWARGS['color'])

    def build(self):
        if not self.notif_icon:
            self.notif_icon = self.get_application_icon()
        Clock.schedule_once(self._hide_window, 0)
        if KWARGS['timeout_close']:
            Clock.schedule_once(self.stop, KWARGS['timeout'])
        if KWARGS['kv']:
            path = dirname(abspath(__file__))
            kv = Builder.load_file(join(path, 'notification.kv'))
            kv.ids.container.clear_widgets()
            kv.ids.container.add_widget(
                Builder.load_string(KWARGS['kv'])
            )
            return kv

    def _hide_window(self, *args):
        if platform == 'win':
            self._hide_w32_window()
        elif platform in ('linux', 'osx'):
            self._hide_x11_window()

    def _hide_w32_window(self):
        try:
            w32win = win32gui.FindWindow(None, self.title)
            win32gui.ShowWindow(w32win, SW_HIDE)
            win32gui.SetWindowLong(
                w32win,
                GWL_EXSTYLE,
                win32gui.GetWindowLong(
                    w32win, GWL_EXSTYLE) | WS_EX_TOOLWINDOW
            )
            win32gui.ShowWindow(w32win, SW_SHOW)
            self._return_focus_w32()
        except Exception:
            tb = traceback.format_exc()
            Logger.error(
                'Notification: An error occured in {}\n'
                '{}'.format(self.title, tb)
            )

    def _hide_x11_window(self):
        try:
            # Ubuntu's Unity for some reason ignores this if there are
            # multiple windows stacked to a single icon on taskbar.
            # Unity probably calls the same thing to stack the running
            # programs to a single icon, which makes this command worthless.
            x11_command = [
                'xprop', '-name', '{}'.format(self.title), '-f',
                '_NET_WM_STATE', '32a', '-set', '_NET_WM_STATE',
                '_NET_WM_STATE_SKIP_TASKBAR'
            ]
            check_output(x11_command)
        except Exception as e:
            tb = traceback.format_exc()
            Logger.error(
                'Notification: An error occured in {}\n'
                '{}'.format(self.title, tb)
            )

    def _return_focus_w32(self):
        w32win = win32gui.FindWindow(None, KWARGS['parent_title'])
        win32gui.SetForegroundWindow(w32win)


if __name__ == '__main__':
    Notification().run()
