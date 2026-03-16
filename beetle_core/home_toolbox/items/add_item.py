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
import hardware_api.toolcat_unicum as _toolcat_unicum_
import tree_widget.widgets.item_action_btn as _item_action_btn_
import home_toolbox.items.item as _tm_
import home_toolbox.items.toolchain_items.toolchain_items as _toolchain_items_
import home_toolbox.items.build_automation_items.build_automation_items as _buildautomation_items_
import home_toolbox.items.flash_tool_items.flash_tool_items as _flash_tool_items_

if TYPE_CHECKING:
    import qt
    import wizards.tool_wizard.new_tool_wizard


class AddItem(_tm_.File):
    class Status(_tm_.File.Status):
        __slots__ = ()

        def __init__(self, item: AddItem) -> None:
            """"""
            super().__init__(item=item)
            self.action_iconpath = "icons/dialog/add.png"
            self.action_txt = "add tool"
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
            always!
            """
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ("toolcat", "__toolwiz")

    def __init__(self, rootdir: _tm_.Root) -> None:
        """"""
        super().__init__(
            rootdir=rootdir,
            parent=rootdir,
            name="AddItem",
            state=AddItem.Status(item=self),
            toolObj=None,
        )
        self.__toolwiz: Optional[
            wizards.tool_wizard.new_tool_wizard.NewToolWizard
        ] = None
        if isinstance(rootdir, _toolchain_items_.ToolchainRootItem):
            self.toolcat = _toolcat_unicum_.TOOLCAT_UNIC("COMPILER_TOOLCHAIN")
        elif isinstance(
            rootdir, _buildautomation_items_.BuildAutomationRootItem
        ):
            self.toolcat = _toolcat_unicum_.TOOLCAT_UNIC("BUILD_AUTOMATION")
        elif isinstance(rootdir, _flash_tool_items_.FlashToolRootItem):
            self.toolcat = _toolcat_unicum_.TOOLCAT_UNIC("FLASHTOOL")
        else:
            assert False
        assert isinstance(rootdir, _tm_.Root)
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemActionBtn=_item_action_btn_.ItemActionBtn(owner=self),
        )
        return

    def leftclick_itemActionBtn(self, event: Optional[qt.QEvent]) -> None:
        """"""
        if event is not None:
            super().leftclick_itemActionBtn(event)

        def finish(*args) -> None:
            print("MY TOOLWIZ HAS FINISHED!")
            self.__toolwiz = None
            return

        print("MY TOOLWIZ HAS STARTED!")
        import wizards.tool_wizard.new_tool_wizard as _new_tool_wiz_

        self.__toolwiz = _new_tool_wiz_.NewToolWizard(
            parent=None,
            toolcat=self.toolcat,
            callback=finish,
            callbackArg=None,
        )
        self.__toolwiz.show()
        return

    def rightclick_itemActionBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemActionBtn(event)
        return
