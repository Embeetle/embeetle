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
import components
import themes

"""
-----------------------------------------------------------------------------------
ExCo Information Widget for displaying the license, used languages and libraries, ...
-----------------------------------------------------------------------------------
"""


class ExCoInfo(qt.QDialog):
    # Class variables
    name = "embeetle Info"
    savable = data.CanSave.NO

    # Class functions(methods)
    def __init__(self, parent, app_dir=""):
        """Initialization routine."""
        # Initialize superclass, from which the current class is inherited,
        # THIS MUST BE DONE SO THAT THE SUPERCLASS EXECUTES ITS __init__ !!!!!!
        super().__init__()
        # Setup the window
        self.setWindowTitle("About embeetle")
        #        self.setWindowFlags(qt.Qt.WindowType.WindowStaysOnTopHint)
        # Setup the picture
        exco_picture = qt.QPixmap(data.about_image)
        self.picture = qt.QLabel(self)
        self.picture.setPixmap(exco_picture)
        self.picture.setGeometry(self.frameGeometry())
        self.picture.setScaledContents(True)
        # Assign events
        self.picture.mousePressEvent = self._close
        self.picture.mouseDoubleClickEvent = self._close
        # Initialize layout
        self.layout = qt.QGridLayout()
        self.layout.addWidget(self.picture)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(qt.QMargins(0, 0, 0, 0))
        self.setLayout(self.layout)
        # Set the log window icon
        if os.path.isfile(data.application_icon_abspath):
            self.setWindowIcon(qt.QIcon(data.application_icon_abspath))
        # Save the info window geometry, the values were gotten by showing a dialog with the label containing
        # the ExCo info image with the size set to (50, 50), so it would automatically resize to the label image size
        my_width = 610
        my_height = 620
        # Set the info window position
        parent_left = parent.geometry().left()
        parent_top = parent.geometry().top()
        parent_width = parent.geometry().width()
        parent_height = parent.geometry().height()
        my_left = parent_left + (parent_width / 2) - (my_width / 2)
        my_top = parent_top + (parent_height / 2) - (my_height / 2)
        self.setGeometry(
            qt.QRect(int(my_left), int(my_top), int(my_width), int(my_height))
        )
        self.setFixedSize(my_width, my_height)

    #        self.setStyleSheet("background-color:transparent;")
    #        self.setWindowFlags(qt.Qt.WindowType.WindowStaysOnTopHint | qt.Qt.WindowType.Dialog | qt.Qt.WindowType.FramelessWindowHint)
    #        self.setAttribute(qt.Qt.WidgetAttribute.WA_TranslucentBackground)

    def _close(self, event):
        """Close the widget."""
        self.picture.setParent(None)
        self.picture = None
        self.layout = None
        self.close()
