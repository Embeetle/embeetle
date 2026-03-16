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

import data
import gui.dialogs.popupdialog
import contextmenu.contextmenu as _contextmenu_
import bpathlib.path_obj as _po_


class PathContextMenu(_contextmenu_.ContextMenuNode):
    def __init__(
        self,
        contextmenu_root: _contextmenu_.ContextMenuRoot,
        parent: _contextmenu_.ContextMenuNode,
        pathObj: _po_.PathObj,
    ) -> None:
        """

        :param contextmenu_root: The ContextMenuRoot()-instance at the top. (*Note*)
        :param parent:           The parent ContextMenuNode()-instance.     (*Note*)
        :param pathObj:          PathObj()-instance, passed on to the leaf.

        *Note: Only a weak reference to these parameters gets stored.

        """
        super().__init__(
            contextmenu_root=contextmenu_root,
            parent=parent,
            text="Show full path",
            key="path",
            iconpath="icons/gen/tree_navigate.png",
        )
        assert isinstance(pathObj, _po_.PathObj)
        leaf = PathContextMenuLeaf(
            contextmenu_root=contextmenu_root,
            parent=self,
            pathObj=pathObj,
        )
        self.add_child(leaf)
        self.aboutToShow.connect(leaf.show_path)
        return

    def set_path(self, pathObj: _po_.PathObj) -> None:
        raise NotImplementedError()
        return


class PathContextMenuLeaf(_contextmenu_.ContextMenuLeaf):
    def __init__(
        self,
        contextmenu_root: _contextmenu_.ContextMenuRoot,
        parent: _contextmenu_.ContextMenuNode,
        pathObj: _po_.PathObj,
    ) -> None:
        """

        :param contextmenu_root: The ContextMenuRoot()-instance at the top. (*Note*)
        :param parent:           The parent ContextMenuNode()-instance.     (*Note*)
        :param pathObj:          PathObj()-instance.

        *Note: Only a weak reference to these parameters gets stored.
        """
        super().__init__(
            contextmenu_root=contextmenu_root,
            parent=parent,
            text=" Hover... ",
            key="path_leaf",
            iconpath="icons/gen/zoom.png",
        )
        assert isinstance(pathObj, _po_.PathObj)
        self.triggered.connect(self.copy_path)
        self.__pathObj = pathObj
        return

    def set_path(self, pathObj: _po_.PathObj) -> None:
        self.__pathObj = pathObj
        return

    def show_path(self) -> None:
        if self.__pathObj is None:
            return
        self._lbl.setText(self.__pathObj.get_abspath())
        return

    def copy_path(self) -> None:
        clipboard = data.application.clipboard()
        clipboard.setText(self.__pathObj.get_abspath())
        gui.dialogs.popupdialog.PopupDialog.ok(
            icon_path="icons/gen/tree_navigate.png",
            title_text="Absolute path",
            text=str(
                f'The absolute path<br><font color="#204a87">'
                f"{self.__pathObj.get_abspath()}</font><br>"
                f"has been copied to your clipboard"
            ),
        )
        return
