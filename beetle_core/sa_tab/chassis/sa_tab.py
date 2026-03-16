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
import qt, data, functions
import gui.stylesheets.scrollbar as _sb_
import tree_widget.chassis.chassis as _chassis_
import tree_widget.chassis.chassis_body as _chassis_body_

if TYPE_CHECKING:
    import sa_tab.items.item as _sa_tab_items_


class SATabBody(_chassis_body_.ChassisBody):
    def __init__(self, chassis: SATab):
        """"""
        super().__init__(chassis)
        self.__msg_log: List[str] = []
        self.__log_space: Optional[qt.QPlainTextEdit] = None
        if data.debug_mode:
            self.__log_space = qt.QPlainTextEdit()
            self.__log_space.setStyleSheet(
                f"""
            QPlainTextEdit {{
                color         : #ffffff;
                background    : #000000;
                border-width  : 1px;
                border-color  : #2e3436;
                border-style  : solid;
                padding       : 0px;
                margin        : 0px;
                font-family   : {data.get_global_font_family()};
                font-size     : {data.get_general_font_pointsize()}pt;
            }}
            """
            )
            self.__log_space.setFont(data.get_general_font())
            self.__log_space.setReadOnly(True)
            self.__log_space.verticalScrollBar().setStyleSheet(
                _sb_.get_vertical()
            )
            self.__log_space.horizontalScrollBar().setStyleSheet(
                _sb_.get_horizontal()
            )
            self.__log_space.verticalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__log_space.horizontalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            self.__log_space.setHorizontalScrollBarPolicy(
                qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.__log_space.setVerticalScrollBarPolicy(
                qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
            )
            self.__log_space.setSizePolicy(
                qt.QSizePolicy.Policy.Expanding,
                qt.QSizePolicy.Policy.Expanding,
            )
            self.__log_space.setLineWrapMode(
                qt.QPlainTextEdit.LineWrapMode.NoWrap
            )
        return

    def init_sa_tab_body(self) -> None:
        """"""
        if not data.debug_mode:
            return
        self._lyt.addWidget(self.__log_space)
        return

    def display_message(self, msg: str, indent: int = 0) -> None:
        """"""
        if not data.debug_mode:
            return
        if indent > 0:
            tab = "&nbsp;&nbsp;&nbsp;&nbsp;"
            msg = tab * indent + f"\n{tab*indent}".join(
                msg.replace("<br>", "\n").splitlines()
            )
        msg = msg.replace("\n", "<br>")
        if self.__log_space is None:
            self.__msg_log.append(msg)
            return
        elif len(self.__msg_log) > 0:
            self.__msg_log.append(msg)
            self.__log_space.appendHtml("<br>".join(self.__msg_log))
            self.__msg_log = []
            return
        else:
            self.__log_space.appendHtml(f"{msg}<br>")
        return


class SATab(_chassis_.Chassis):
    def __init__(self, mainwindow, basicwidget):
        """"""
        super().__init__(
            mainwindow=mainwindow,
            basicwidget=basicwidget,
            name="SATab",
            iconpath="icons/gen/source_analyzer.png",
            head=None,
            body=None,
        )
        super().set_page(
            head=None,
            body=SATabBody(self),
            add_stretch=False,
        )
        self.mainwindow = mainwindow
        data.sa_tab = self
        return

    def display_message(self, msg: str, indent: int = 0) -> None:
        """"""
        if not data.debug_mode:
            return
        body: SATabBody = self.get_chassis_body()
        body.display_message(msg, indent)
        return

    def contextmenuclick_tab_settingsbtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)

        def _help(_key):
            print("SA Tab help")
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def leftclick_tab_settingsbtn(self, *args) -> None:
        """User clicked the settings button in the SATab tab header.

        NOTE:
        There is no such button right now.
        """
        print("SATab().leftclick_tab_settingsbtn()")
        return

    def leftclick_tab_savebtn(self):
        """User clicked the save button in the SATab tab header.

        NOTE:
        There is no such button right now.
        """
        print("SATab().leftclick_tab_savebtn()")
        return

    def refresh_all_recursive(
        self, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """"""
        body: SATabBody = self.get_chassis_body()
        body_rootlist = body.body_get_rootlist()

        def refresh_root_recursive(
            root_iter: Iterator[_sa_tab_items_.Root],
        ) -> None:
            try:
                root = next(root_iter)
            except StopIteration:
                # Finish
                self.check_unsaved_changes()
                if callback is not None:
                    callback(callbackArg)
                return
            root.refresh_recursive_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=refresh_root_recursive,
                callbackArg=root_iter,
            )
            return

        # * Start
        refresh_root_recursive(iter(body_rootlist))
        return

    def set_unsaved_changes(self, *args) -> None:
        """Register the presence of unsaved changes.

        Unlike the Dashboard, there is no point in passing a 'tabname' for the
        SA Tab.
        """
        super().set_unsaved_changes()

    def clear_unsaved_changes(self, *args) -> None:
        """Clear the presence of unsaved changes.

        Unlike the Dashboard, there is no point in passing a 'tabname' for the
        SA Tab.
        """
        super().clear_unsaved_changes()

    def check_unsaved_changes(self):
        """"""
        body: SATabBody = self.get_chassis_body()
        body_rootlist: List[_sa_tab_items_.Root] = body.body_get_rootlist()
        for root in body_rootlist:
            if root.get_state().has_asterisk():
                self.show_tab_savebutton_sig.emit()
                self.set_unsaved_changes()
                self.enable_tab_optionundo_signal.emit(True)
                return
        self.hide_tab_savebutton_sig.emit()
        self.clear_unsaved_changes()
        self.enable_tab_optionundo_signal.emit(False)
        return
