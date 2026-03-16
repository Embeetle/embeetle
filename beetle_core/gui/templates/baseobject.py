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

from __future__ import annotations
from typing import *
import qt
import data
import purefunctions
import iconfunctions
import components.iconmanipulator

if TYPE_CHECKING:
    import gui.forms.mainwindow
    import gui.forms.homewindow


class BaseObject(qt.QObject):
    # Class variables
    _parent = None  # An underscore is needed, as QObject
    # already has a method 'parent()'
    main_form = None
    name = ""
    savable = data.CanSave.NO
    current_icon = None
    icon_manipulator = None
    context_menu = None

    def __init__(
        self,
        parent: Union[qt.QTabWidget, qt.QFrame, qt.QMainWindow, None],
        main_form: Union[
            gui.forms.mainwindow.MainWindow, gui.forms.homewindow.HomeWindow
        ],
        name: str,
        icon: Union[qt.QIcon, str, None],
    ):
        """Each widget in embeetle has to inherit from this class.

        :param parent: The basic widget you want to put it in (main, upper or
            lower window).
        :param main_form: The MainWindow reference.
        :param name: Can be just an empty string ""
        :param icon: An icon or None
        :return:
        """
        self._parent = parent
        self.main_form = main_form
        self.name = name
        if isinstance(icon, str):
            icon = iconfunctions.get_qicon(icon)
        self.current_icon = icon
        self.icon_manipulator = components.iconmanipulator.IconManipulator(
            self, parent
        )

        self.__tabwidget_module = purefunctions.import_module(
            "gui.forms.tabwidget"
        )

        self.installEventFilter(self)

    def set_saveable(self, saveable=False):
        if saveable == True:
            self.savable = data.CanSave.YES
        else:
            self.savable = data.CanSave.NO

    def eventFilter(self, object, event):
        """
        Relevant event type numbers:
            2: mouse press
            3: mouse release
            6: key press
            7: key release
            207: InputMethodQuery
        """
        if (
            event.type() == qt.QEvent.Type.KeyRelease
            or event.type() == qt.QEvent.Type.MouseButtonRelease
            or event.type() == qt.QEvent.Type.InputMethodQuery
        ):
            self.highlight_parent_tabwidget()
            self.display_widget_statusbar_status()

        return False

    def highlight_parent_tabwidget(self):
        try:
            tabwidget = None
            parent = self.parent
            if callable(parent):
                parent = parent()
            while tabwidget is None:
                if isinstance(parent, self.__tabwidget_module.TabWidget):
                    tabwidget = parent
                else:
                    parent = parent.parent
                    if callable(parent):
                        parent = parent()
            if not tabwidget.indicated:
                self.main_form.view.indicate_window(tabwidget)
        except Exception as ex:
            #            print("[BaseObject] Error in highlighting parent tabwidget!")
            #            print(ex)
            pass

    def display_widget_statusbar_status(self):
        if self.main_form is None:
            return
        elif self.main_form.name != "Main Window":
            return

        name = self.__class__.__name__
        if name == "CustomEditor":
            self.update_statusbar_status()
        else:
            if isinstance(self._parent, self.__tabwidget_module.TabWidget):
                tab_bar = self._parent.tabBar()
                text = tab_bar.tabText(tab_bar.currentIndex())
                self.main_form.display.statusbar_show(text)

    def show_home_window(self):
        self.main_form.open_home_window()

    def send(self, *messages):
        if not all((isinstance(m, str) for m in messages)):
            print("[COMM-BaseObject] All message parameters must be strings!")
            return
        # Send the message using the forms comm system
        self.main_form.send(" ".join(messages))

    @qt.pyqtSlot(str)
    def receive(self, message):
        # Overload to use
        pass
