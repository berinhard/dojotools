#-*- coding: utf-8 -*-
"""


Dojotools - tools for your coding dojo session

Copyright (C) 2009 Flávio Amieiro <amieiro.flavio@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2 dated June, 1991.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Library General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.

If you find any bugs or have any suggestions email: amieiro.flavio@gmail.com
"""
import os
import sys
import gtk
import gobject
import lang

try:
    import pynotify
except ImportError:
    pynotify = None
    sys.stderr.write(lang.PYNOTIFY_IMPORT_ERROR1+
                     lang.PYNOTIFY_IMPORT_ERROR2
    )


IMAGE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'images/')
PASS_ICON = os.path.join(IMAGE_DIR, 'green_belt.png')
FAIL_ICON = os.path.join(IMAGE_DIR, 'red_belt.png')

__all__ = ['UserInterface']
        
class UserInterface(object):

    def __init__(self, timer, use_thread):
        self.timer = timer
        self.current_status = 0
        
        self.thread = None
        self.use_thread = use_thread

        self.status_icon = gtk.StatusIcon()
        self.status_icon.set_from_file(PASS_ICON)
        self._create_menu()
        self.status_icon.set_visible(True)
        
        self.start_timer()

        gobject.timeout_add(1000, self.update_timer)

    def _timer_items_set_sensitive(self, value):
        self.timer_item.set_sensitive(value)
        self.reset_time_item.set_sensitive(value)

    def _create_menu(self):
        self.menu = gtk.Menu()
        
        if self.use_thread:
            self.separator2 = gtk.MenuItem()
            
            self.kill_item = gtk.MenuItem(lang.NO_RUNNING)
            self.kill_item.connect('activate', self.kill_process)

            self.menu.append(self.kill_item)
            self.menu.append(self.separator2)

        self.timer_item = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PAUSE)
        self.timer_item.connect('activate', self.timer_button)

        self.set_time_item = gtk.MenuItem(
            lang.SET_TIME % (self.timer.round_time)
        )
        self.set_time_item.connect('activate', self.set_time)
        
        self.reset_time_item = gtk.MenuItem(lang.RESET_TIME)
        self.reset_time_item.connect('activate', self.reset_time)
        
        self.separator = gtk.MenuItem()
        
        self.quit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit_item.connect('activate', self.main_quit, gtk)
            
        self.menu.append(self.timer_item)
        self.menu.append(self.set_time_item)
        self.menu.append(self.reset_time_item)
        self.menu.append(self.separator)
        self.menu.append(self.quit_item)
        
        self.status_icon.connect('popup-menu', self._show_menu, self.menu)

    def _show_menu(self, widget, button, time, data):
        data.show_all()
        data.popup(None, None, None, button, time)

   
    def _set_icon(self):
        self.status_icon.set_from_file(
            PASS_ICON if self.current_status == 0 else FAIL_ICON
        )
        
    def set_kill_label(self, label=lang.NO_RUNNING):
        """Change kill_item label"""
        self.kill_item.set_sensitive(not label == lang.NO_RUNNING)
        self.kill_item.set_label(label)
        
    def set_time(self, widget=None):
        """Shows dialog to set time"""
        self.timer_item.set_sensitive(False)
        if self.timer.running:
            self.pause_timer()
            self.warn_set_time()
            self.timer_item.set_sensitive(True)
            self.start_timer()
        else:
            self.warn_set_time()
            
    def reset_time(self, widget=None):
        self.timer.time_left = self.timer.round_time 
        
    def main_quit(self, arg, widget=None):
        if self.use_thread:
            self.thread.stop()
        gtk.main_quit(arg)
        
    def kill_process(self, widget=None):
        """Stop thread"""
        self.thread.stop()

    def timer_button(self, widget=None):
        """Pause or start timer"""
        self.pause_timer() if self.timer.running else self.start_timer()

    def start_timer(self, widget=None):
        """
        Change icon to started, start timer and 
        Change timer_item label to lang.PAUSE
        """
        self._set_icon()
        self.timer.start()
        self.timer_item.set_label(lang.PAUSE)
    
    def pause_timer(self, widget=None):
        """
        Change icon to paused, pause timer and 
        Change timer_item label to lang.START
        """
        self.status_icon.set_from_stock(gtk.STOCK_MEDIA_PAUSE)
        self.timer.pause()
        self.timer_item.set_label(lang.START)
          
    def warn(self, widgets, result_index=-1):
        """
        Shows a dilog with widgets from a list 
        Returns the get_text of result_index item from widgets list
        """
        dialog = gtk.Dialog('Dojotools', buttons=(gtk.STOCK_OK, 0))
        dialog.set_default_size(180, 120)
        dialog.set_keep_above(True)
        for widget in widgets:
            dialog.vbox.add(widget)
        dialog.show_all()
        dialog.run()
        result = widgets[result_index].get_text() if not result_index == -1 else None
        dialog.destroy()
        return result

    def warn_time_is_up(self):
        """Shows a dialog warning the pilot that his time is up"""
        self.warn([gtk.Label(lang.TIME_IS_UP)])
        
    def warn_set_time(self):
        """Shows a dialog to change round time"""   
        try:
            text_input = gtk.Entry(15)
            text_input.set_text(str(self.timer.round_time))
            
            time_text = self.warn([gtk.Label(lang.WRITE_TIME), text_input], result_index = 1)
            self.timer.round_time = int(time_text)
            self.set_time_item.set_label(lang.SET_TIME % (self.timer.round_time))
        except ValueError:
            self.warn([gtk.Label(lang.VALUE_ERROR)])

    def html_escape(self, text):
        """Produce entities within text."""		 
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        return "".join(html_escape_table.get(c,c) for c in text)

    def show_command_results(self, status, output):
        """
        Shows the output to the users.

        For now, it will write the output to stdout,
        change the icon depending on the status (green
        if the tests are passing, red otherwise) and,
        if pynotify is installed, show a notification.

        If you use this in Ubuntu, I'm sorry for you.
        Canonical just decided to break libnotify in so
        many ways that it is *impossible* to use it sanely.

        """

        sys.stdout.write(output)

        self.current_status = status

        if self.timer.running:
            self._set_icon()

        if pynotify is not None:
            pynotify.init('dojotools')
            message = pynotify.Notification('Dojotools', self.html_escape(output))
            message.attach_to_status_icon(self.status_icon)
            message.set_urgency(
                pynotify.URGENCY_NORMAL if status == 0
                else pynotify.URGENCY_CRITICAL
            )
            message.show() 

    def update_timer(self):
        if self.timer.time_left:
            time_str = '%02d:%02d' % (
                (self.timer.time_left / 60),
                (self.timer.time_left % 60)
            )
            self.status_icon.set_tooltip(time_str)
        else:
            self.pause_timer()
            self._timer_items_set_sensitive(False)
            self.warn_time_is_up()
            self._timer_items_set_sensitive(True)
            self.start_timer()
            
        return True
