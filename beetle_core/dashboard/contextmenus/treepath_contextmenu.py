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
import contextmenu.contextmenu as _contextmenu_
import contextmenu.path_contextmenu as menu_path
import bpathlib.treepath_obj as _treepath_obj_

if TYPE_CHECKING:
    import qt
    import tree_widget.items.item as _item_
# POPUP MENUS FOR 'PROJECT_LAYOUT' SECTION IN DASHBOARD


class TreepathContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
        treepathObj: _treepath_obj_.TreepathObj,
    ) -> None:
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        assert isinstance(treepathObj, _treepath_obj_.TreepathObj)

        #! OPEN
        # 'Open' navigates to the file in the FILETREE or in the
        # file explorer from the OS. Don't show this menu for a fake
        # treepathObj (in the Intro Wizard).
        if not treepathObj.is_fake():
            self.add_child(
                _contextmenu_.ContextMenuTopleaf(
                    contextmenu_root=self,
                    parent=self,
                    text="Open",
                    key="navigate",
                    iconpath="icons/gen/tree_navigate.png",
                )
            )

        #! SELECT
        # Select the location manually.
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Select",
                key="select_man",
                iconpath="icons/gen/tree_find.png",
            )
        )

        #! AUTODETECT
        # Autodetect the location.
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Autodetect",
                key="select_auto",
                iconpath="icons/gen/tree_find_auto.png",
            )
        )

        #! CREATE BUILD FOLDER
        # Only for 'BUILD_DIR' entry
        if treepathObj.get_name() == "BUILD_DIR":
            self.add_child(
                _contextmenu_.ContextMenuTopleaf(
                    contextmenu_root=self,
                    parent=self,
                    text="Create build folder",
                    key="create_build_folder",
                    iconpath="icons/folder/closed/build.png",
                )
            )

        #! SHOW FULL PATH
        # Show absolute path to file/folder.
        self.add_child(
            menu_path.PathContextMenu(
                contextmenu_root=self,
                parent=self,
                pathObj=treepathObj,
            )
        )

        #! RESET
        # Only for files: reset the file content.
        if treepathObj.is_file():
            self.add_child(
                _contextmenu_.ContextMenuTopleaf(
                    contextmenu_root=self,
                    parent=self,
                    text="Reset",
                    key="reset",
                    iconpath="icons/dialog/refresh.png",
                )
            )

        #! HELP
        # Show more info on the given file/folder.
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="More info",
                key="help",
                iconpath="icons/dialog/info.png",
            )
        )
        return
