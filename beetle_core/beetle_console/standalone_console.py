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
import threading, os
import qt, data, functions
import beetle_console.console_widget as _console_widget_


class StandaloneConsole(qt.QWidget):
    close_sig = qt.pyqtSignal()

    def __init__(self, title: str) -> None:
        """Create a new StandaloneConsole() widget."""
        super().__init__(parent=None)
        assert threading.current_thread() is threading.main_thread()
        # $ WindowFlags
        self.setWindowFlags(
            self.windowFlags()  # noqa
            | qt.Qt.WindowType.Dialog
            | qt.Qt.WindowType.WindowTitleHint
            | qt.Qt.WindowType.WindowCloseButtonHint
        )
        # $ Geometry
        try:
            w, h = functions.get_screen_size()
        except:
            s = functions.get_screen_size()
            w = s.width()
            h = s.height()
        self.setGeometry(
            int(w * 0.3),
            int(h * 0.2),
            int(w * 0.4),
            int(h * 0.6),
        )
        # $ Stylesheet
        self.setStyleSheet(
            f"""
        QWidget {{
            color         : #2e3436;
            background    : #ffffff;
            font-family   : {data.get_global_font_family()};
            font-size     : {data.get_general_font_pointsize()}pt;
            padding    : 0px;
            margin     : 0px;
        }}
        """
        )
        # $ Title
        self.setWindowTitle(title)
        # $ Layout
        self.__lyt = qt.QVBoxLayout(self)
        self.__lyt.setSpacing(0)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        # $ Console
        self.__console_widg = _console_widget_.ConsoleWidget(
            parent=self,
            readonly=False,
            cwd=os.getcwd(),
            fake_console=True,
            is_serial_monitor=False,
        )
        self.__lyt.addWidget(self.__console_widg)
        self.__progbar_val = 0.0
        self.show()
        return

    @qt.pyqtSlot()
    def close(self) -> bool:
        """Close in a safe way."""
        if qt.sip.isdeleted(self):
            return False
        if threading.current_thread() is not threading.main_thread():
            self.close_sig.emit()
            return False
        return super().close()

    def fill_progbar(self, *args) -> None:
        """"""
        if self.__progbar_val < 100:
            self.__progbar_val += 1
            self.__console_widg.set_progbar_val(self.__progbar_val)
            qt.QTimer.singleShot(10, self.fill_progbar)
            return
        self.__console_widg.close_progbar()
        return
