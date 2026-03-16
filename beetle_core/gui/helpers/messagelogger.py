# Copyright © 2018-2026 Johan Cockx, Matic Kukovec & Kristof Mulier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# SPDX-License-Identifier: GPL-3.0-or-later

import os
import os.path
import collections
import traceback
import ast
import inspect
import math
import functools
import textwrap
import difflib
import re
import time
import settings
import functions
import gui
import qt
import data
import components.actionfilter
import themes

"""
----------------------------------------------------------------------------
Object for showing log messages across all widgets, mostly for debug purposes
----------------------------------------------------------------------------
"""


class MessageLogger(qt.QWidget):
    """Simple subclass for displaying log messages."""

    class MessageTextBox(qt.QTextEdit):
        def contextMenuEvent(self, event):
            event.accept()

    # Controls and variables of the log window  (class variables >> this means that these variables are shared accross instances of this class)
    displaybox = None  # QTextEdit that will display log messages
    layout = None  # The layout of the log window
    parent = None

    def __init__(self, parent):
        """Initialization routine."""
        # Initialize superclass, from which the current class is inherited, THIS MUST BE DONE SO THAT THE SUPERCLASS EXECUTES ITS __init__ !!!!!!
        super().__init__()

        # Initialize the log window
        self.setWindowTitle("LOGGING WINDOW")
        self.resize(500, 300)
        #        self.setWindowFlags(qt.Qt.WindowType.WindowStaysOnTopHint)

        # Initialize the display box
        self.displaybox = MessageLogger.MessageTextBox(self)
        self.displaybox.setReadOnly(True)
        # Make displaybox click/doubleclick event also fire the log window click/doubleclick method
        self.displaybox.mousePressEvent = self._event_mousepress
        self.displaybox.mouseDoubleClickEvent = self._event_mouse_doubleclick
        self.keyPressEvent = self._keypress

        # Initialize layout
        self.layout = qt.QGridLayout()
        self.layout.addWidget(self.displaybox)
        self.setLayout(self.layout)

        self.append_message("embeetle debug log window loaded")
        self.append_message("LOGGING Mode is enabled")
        self.parent = parent

        # Set the log window icon
        if os.path.isfile(data.application_icon_abspath):
            self.setWindowIcon(qt.QIcon(data.application_icon_abspath))

    def _event_mouse_doubleclick(self, mouse_event):
        """Rereferenced/overloaded displaybox doubleclick event."""
        self.clear_log()

    def _event_mousepress(self, mouse_event):
        """Rereferenced/overloaded displaybox click event."""
        # Reset the click&drag context menu action
        components.actionfilter.ActionFilter.clear_action()

    def _keypress(self, key_event):
        """Rereferenced/overloaded MessageLogger keypress event."""
        pressed_key = key_event.key()
        if pressed_key == qt.Qt.Key.Key_Escape:
            self.close()

    def clear_log(self):
        """Clear all messages from the log display."""
        self.displaybox.clear()

    def append_message(self, *args, **kwargs):
        """Adds a message as a string to the log display if logging mode is
        enabled."""
        if len(args) > 1:
            message = " ".join(args)
        else:
            message = args[0]
        # Check if message is a string class, if not then make it a string
        if isinstance(message, str) == False:
            message = str(message)
        # Check if logging mode is enabled
        if data.logging_mode == True:
            self.displaybox.append(message)
        # Bring cursor to the current message (this is in a QTextEdit not QScintilla)
        cursor = self.displaybox.textCursor()
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        cursor.movePosition(qt.QTextCursor.MoveOperation.StartOfLine)
        self.displaybox.setTextCursor(cursor)
