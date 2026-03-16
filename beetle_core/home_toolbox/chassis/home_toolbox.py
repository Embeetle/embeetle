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
import functions
import tree_widget.chassis.chassis as _chassis_
import tree_widget.chassis.chassis_body as _chassis_body_
import home_toolbox.chassis.home_toolbox_worker as _dw_

if TYPE_CHECKING:
    import home_toolbox.items.item as _tm_

from various.kristofstuff import *


class ToolboxBody(_chassis_body_.ChassisBody):
    def __init__(self, chassis):
        super().__init__(chassis)
        return


class Toolbox(_chassis_.Chassis):
    def __init__(self, mainwindow, basicwidget):
        """"""
        super().__init__(
            mainwindow=mainwindow,
            basicwidget=basicwidget,
            name="Home Toolmanager",
            iconpath="icons/tools/toolbox.png",
            head=None,
            body=ToolboxBody(self),
        )
        self.__toolmanagerworker = _dw_.ToolmanagerWorker()
        return

    """----------------------------------------------------------------------------"""
    """ 2. TAB BUTTONS                                                             """
    """----------------------------------------------------------------------------"""

    def contextmenuclick_tab_settingsbtn(self, key: str, *args) -> None:
        key = functions.strip_toplvl_key(key)

        def _help(_key):
            print("Toolmanager help")
            return

        funcs = {
            "help": _help,
            "foo": nop,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def leftclick_tab_settingsbtn(self, *args) -> None:
        """User clicked the settings button in the Toolbox tab header.

        Note: there is no such button right now.
        """
        print("Toolmanager().leftclick_tab_settingsbtn()")
        return

    def leftclick_tab_savebtn(self):
        """User clicked the save button in the Toolbox tab header.

        Note: there is no such button right now.
        """
        print("Toolmanager().leftclick_tab_savebtn()")
        return

    """----------------------------------------------------------------------------"""
    """ 3. CLICK ACTIONS                                                           """
    """----------------------------------------------------------------------------"""
    """----------------------------------------------------------------------------"""
    """ 4. HANDLE CHANGES                                                          """
    """----------------------------------------------------------------------------"""

    def refresh_all_recursive(
        self, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """"""
        body: ToolboxBody = self.get_chassis_body()
        body_rootlist: List[_tm_.Root] = body.body_get_rootlist()

        def start():
            nonlocal body_rootlist
            body_rootgen = iter(body_rootlist)
            refresh_root_recursive(body_rootgen)
            return

        def refresh_root_recursive(body_rootgen):
            try:
                root = next(body_rootgen)
            except StopIteration:
                check_unsaved_changes()
                return
            root.refresh_recursive_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=refresh_root_recursive,
                callbackArg=body_rootgen,
            )
            return

        def check_unsaved_changes():
            self.check_unsaved_changes()
            finish()
            return

        def finish():
            callback(callbackArg) if callback is not None else nop()
            return

        start()
        return

    def set_unsaved_changes(self, *args) -> None:
        """Register the presence of unsaved changes.

        Unlike the Dashboard, there is no point in passing a 'tabname' for the
        filetree.
        """
        super().set_unsaved_changes()

    def clear_unsaved_changes(self, *args) -> None:
        """Clear the presence of unsaved changes.

        Unlike the Dashboard, there is no point in passing a 'tabname' for the
        filetree.
        """
        super().clear_unsaved_changes()

    def check_unsaved_changes(self):
        body: ToolboxBody = self.get_chassis_body()
        body_rootlist: List[_tm_.Root] = body.body_get_rootlist()
        for root in body_rootlist:
            if root.get_state().has_asterisk():
                self.set_unsaved_changes()
                self.show_tab_savebutton_sig.emit()
                self.enable_tab_optionundo_signal.emit(True)
                return
        self.hide_tab_savebutton_sig.emit()
        self.clear_unsaved_changes()
        self.enable_tab_optionundo_signal.emit(False)
        return
