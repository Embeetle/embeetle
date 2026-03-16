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
import bpathlib.tool_obj as _tool_obj_
import contextmenu.contextmenu as _contextmenu_
import contextmenu.path_contextmenu as _pc_path_

if TYPE_CHECKING:
    import qt
    import tree_widget.items.item as _item_


class NameContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        toolmanObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj) or isinstance(
            toolmanObj, _tool_obj_.ToolpathObj
        ), f"{toolmanObj}"

        #! INFO
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Show more info",
                key="info",
                iconpath="icons/dialog/info.png",
            )
        )
        return


class UniqueIDContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        toolmanObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj) or isinstance(
            toolmanObj, _tool_obj_.ToolpathObj
        ), f"{toolmanObj}"

        #! INFO
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Show more info",
                key="info",
                iconpath="icons/dialog/info.png",
            )
        )
        return


class VersionContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        toolmanObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj) or isinstance(
            toolmanObj, _tool_obj_.ToolpathObj
        ), f"{toolmanObj}"

        #! INFO
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Show more info",
                key="info",
                iconpath="icons/dialog/info.png",
            )
        )
        return


class BuilddateContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        toolmanObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj) or isinstance(
            toolmanObj, _tool_obj_.ToolpathObj
        ), f"{toolmanObj}"

        #! INFO
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Show more info",
                key="info",
                iconpath="icons/dialog/info.png",
            )
        )
        return


class BitnessContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        toolmanObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj) or isinstance(
            toolmanObj, _tool_obj_.ToolpathObj
        ), f"{toolmanObj}"

        #! INFO
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Show more info",
                key="info",
                iconpath="icons/dialog/info.png",
            )
        )
        return


class LocationContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        toolmanObj: Union[_tool_obj_.ToolmanObj, _tool_obj_.ToolpathObj],
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(toolmanObj, _tool_obj_.ToolmanObj) or isinstance(
            toolmanObj, _tool_obj_.ToolpathObj
        ), f"{toolmanObj}"

        #! NAVIGATE
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Navigate to",
                key="navigate",
                iconpath="icons/gen/tree_navigate.png",
            )
        )

        #! SHOW FULL PATH
        self.add_child(
            _pc_path_.PathContextMenu(
                contextmenu_root=self,
                parent=self,
                pathObj=toolmanObj,
            )
        )
        return
