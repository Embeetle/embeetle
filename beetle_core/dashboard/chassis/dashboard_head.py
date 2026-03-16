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
import qt, data, functions, functools
import tree_widget.chassis.chassis_head as _chassis_head_
import gui.stylesheets.button

if TYPE_CHECKING:
    import tree_widget.chassis.chassis as _chassis_


class DashboardHead(_chassis_head_.ChassisHead):
    """"""

    def __init__(self, chassis: _chassis_.Chassis) -> None:
        """"""
        assert data.dashboard is not None
        super().__init__(chassis)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: transparent;
                border: none;
                padding: 0px 0px 0px 0px;
                margin: 0px 0px 0px 0px;
            }}
        """
        )
        self.setLayout(qt.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        size = data.get_general_icon_pixelsize()

        # * 'APPLY CHANGES' banner
        self.__apply_changes_banner = qt.QPushButton("APPLY CHANGES")
        self.__apply_changes_banner.clicked.connect(
            data.dashboard.leftclick_tab_savebtn
        )
        self.__set_apply_changes_banner_style()
        self.layout().addWidget(self.__apply_changes_banner)
        self.__apply_changes_banner.hide()
        self.__apply_changes_banner_shown = False
        return

    def __set_apply_changes_banner_style(self) -> None:
        """"""
        self.__apply_changes_banner.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet("save-banner")
        )
        self.__apply_changes_banner.style().unpolish(
            self.__apply_changes_banner
        )
        self.__apply_changes_banner.style().polish(self.__apply_changes_banner)
        self.__apply_changes_banner.update()
        return

    def show_apply_changes_banner(self) -> None:
        """"""
        self.__apply_changes_banner.show()
        self.__apply_changes_banner_shown = True
        return

    def hide_apply_changes_banner(self) -> None:
        """"""
        if self.__apply_changes_banner_shown:
            self.__apply_changes_banner.hide()
            self.__apply_changes_banner_shown = False
            data.signal_dispatcher.source_analyzer.start_stop_engine_conditionally_sig.emit()
        return

    def head_rescale_recursive(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Rescale all elements from this widget."""
        self.__set_apply_changes_banner_style()
        callback(callbackArg)
        return

    def head_self_destruct(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Kill all GUI elements from this DashboardHead()-instance and delete
        all the attributes."""
        functions.clean_layout(self.layout())
        self.__apply_changes_banner = None
        qt.QTimer.singleShot(
            10,
            functools.partial(
                callback,
                callbackArg,
            ),
        )
        return
