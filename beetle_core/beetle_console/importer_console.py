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
import threading
import qt, data, iconfunctions
import beetle_console.console_widget as _console_widget_
import gui.templates.baseobject as _baseobject_
import gui.stylesheets.scrollbar as _sb_

if TYPE_CHECKING:
    import gui.forms.mainwindow as _mainwindow_
    import gui.forms.homewindow as _homewindow_
nop = lambda *a, **k: None
q = "'"
dq = '"'


class ImporterConsole(qt.QFrame, _baseobject_.BaseObject):
    """An ImporterConsole()-instance is intended to show importer output. This
    instance is subclassed from both QFrame() and BaseObject() such that it
    nicely fits into an Embeetle QTabWidget().

    The heart of the ImporterConsole() is its ConsoleWidget()-instance. That's a subclassed QPlain-
    TextEdit() widget that behaves more or less like a console. The user can interact with this
    widget - typing and executing commands - but you can also interact programmatically with it.
    """

    def __init__(
        self,
        parent: qt.QTabWidget,
        main_form: Union[_mainwindow_.MainWindow, _homewindow_.HomeWindow],
        name: str,
    ) -> None:
        """
        :param parent:      The QTabWidget() holding this ImporterConsole()-instance.

        :param main_form:   The Project Window or Home Window.

        :param name:        Name for this ImporterConsole()-widget, to be displayed in its tab.
        """
        qt.QFrame.__init__(self)
        _baseobject_.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name=name,
            icon=iconfunctions.get_qicon("icons/console/console.png"),
        )
        self.__parent = parent
        self.__main_form = main_form
        self.__name = name
        self.setStyleSheet(
            """
            QFrame {
                background : transparent;
                border     : none;
                padding    : 0px;
                margin     : 0px;
            }
        """
        )

        # * Layout
        self.__lyt = qt.QVBoxLayout()
        self.__lyt.setSpacing(2)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__lyt)

        # * Console widget
        self.__console_widget = _console_widget_.ConsoleWidget(
            parent=self,
            readonly=True,
            cwd=data.user_directory,
            fake_console=False,
            is_serial_monitor=False,
        )
        self.__lyt.addWidget(self.__console_widget)
        return

    def get_print_func(self) -> Callable:
        """"""
        return self.__console_widget.printout_html

    def rescale_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()

        def rescale_scrollbars(*args) -> None:
            self.__console_widget.verticalScrollBar().setStyleSheet(
                _sb_.get_vertical()
            )
            self.__console_widget.horizontalScrollBar().setStyleSheet(
                _sb_.get_horizontal()
            )
            self.__console_widget.verticalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__console_widget.horizontalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            qt.QTimer.singleShot(20, finish)
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        size = data.get_general_icon_pixelsize()
        self.__console_widget.set_style()
        qt.QTimer.singleShot(20, rescale_scrollbars)
        return
