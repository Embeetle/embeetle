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
import os
import data
import bpathlib.path_power as _pp_
import contextmenu.contextmenu as _contextmenu_
import libmanager.libmanager as _libmanager_
import libmanager.libobj as _libobj_

if TYPE_CHECKING:
    import qt
    import tree_widget.items.item as _item_
from various.kristofstuff import *


class ToplvlLibContextMenu(_contextmenu_.ContextMenuRoot):
    """Context Menu for toplevel dashboard item 'LIBRARIES' and for toplevel
    category items in the Home Window."""

    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )

        #! DOWNLOAD LIBRARY
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Download Library",
                key="download_library",
                iconpath="icons/gen/download.png",
            )
        )

        #! ADD LIBRARY FROM ZIPFILE
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Add Library from Zipfile",
                key="add_library_from_zipfile",
                iconpath="icons/folder/closed/zip.png",
            )
        )

        #! REFRESH LIBRARY LIST
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Refresh Library List",
                key="refresh",
                iconpath="icons/dialog/refresh.png",
            )
        )

        #! HELP
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Help",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return


class LibContextMenu(_contextmenu_.ContextMenuRoot):
    """
    Context menu for a specific library - both Project and Home Window.
    """

    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )

        if (
            item.get_state().has_error()
            or item.get_state().closedIconpath.endswith("(err).png")
            or item.get_state().closedIconpath.endswith("(warn).png")
        ):
            #! WHAT IS WRONG
            # An error sign can be present despite the item having no
            # error-status. That's because I apply the error icon on
            # libraries without letting it propagate upwards.
            self.add_child(
                _contextmenu_.ContextMenuTopleaf(
                    contextmenu_root=self,
                    parent=self,
                    text=f"What{q}s wrong with this library?",
                    key="wrong",
                    iconpath="icons/dialog/warning.png",
                )
            )

        if not data.is_home:
            #! OPEN IN PROJECT
            self.add_child(
                _contextmenu_.ContextMenuTopleaf(
                    contextmenu_root=self,
                    parent=self,
                    text="Open in project",
                    key="open",
                    iconpath="icons/folder/closed/folder.png",
                )
            )
        else:
            #! OPEN IN FILE EXPLORER
            self.add_child(
                _contextmenu_.ContextMenuTopleaf(
                    contextmenu_root=self,
                    parent=self,
                    text="Open",
                    key="open",
                    iconpath="icons/folder/closed/folder.png",
                )
            )

        #! OPEN WEBSITE
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Open website",
                key="website",
                iconpath="icons/gen/world.png",
            )
        )

        #! CHECK FOR UPDATES
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Check for updates",
                key="check_update",
                iconpath="icons/gen/cloud_reset.png",
            )
        )

        #! SHOW DEPENDENCIES
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Show dependencies",
                key="show_dependencies",
                iconpath="icons/gen/book.png",
            )
        )

        if data.is_home:
            #! SAMPLE PROJECTS
            try:
                libobj: _libobj_.LibObj = item.get_projSegment()
            except AttributeError:
                libobj: _libobj_.LibObj = item.get_libobj()
            self.add_child(
                SampleProjectsNode(
                    contextmenu_root=self,
                    parent=self,
                    libobj=libobj,
                )
            )

        #! DELETE
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Delete",
                key="delete",
                iconpath="icons/gen/trash.png",
            )
        )

        #! HELP
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Help",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return


class LibversionContextMenu(_contextmenu_.ContextMenuRoot):
    """
    Context menu for 'version' item for a library - both Home Window and Project Window.
    """

    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Check for updates",
                key="check_update",
                iconpath="icons/gen/cloud_reset.png",
            )
        )
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Help",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return


class SampleProjectsNode(_contextmenu_.ContextMenuNode):
    """Context menu toplevel node 'Sample Projects'."""

    def __init__(
        self,
        contextmenu_root: _contextmenu_.ContextMenuRoot,
        parent: _contextmenu_.ContextMenuNode,
        libobj: _libobj_.LibObj,
    ) -> None:
        """"""
        super().__init__(
            contextmenu_root=contextmenu_root,
            parent=parent,
            text="Sample Projects",
            key="<samples>",
            iconpath="icons/gen/select.png",
        )

        # Define recursive function to add nodes and leaves to
        # this 'Sample Projects' entry.
        def add_node(_sketch_dict_, _node_):
            if (_sketch_dict_ is None) or (_node_ is None):
                return
            for k, v in _sketch_dict_.items():
                # $ It's a leaf
                if isinstance(v, str):
                    _node_.add_child(
                        _contextmenu_.ContextMenuLeaf(
                            contextmenu_root=self,
                            parent=_node_,
                            text=v,
                            key=v,
                            iconpath="icons/logo/arduino.png",
                        )
                    )
                    continue
                # $ It's a node
                new_node = _contextmenu_.ContextMenuNode(
                    contextmenu_root=self,
                    parent=_node_,
                    text=k,
                    key=k,
                    iconpath="icons/logo/arduino_arrow.png",
                )
                _node_.add_child(new_node)
                add_node(_sketch_dict_[k], new_node)
                continue
            return

        # Launch the recursive function, starting from
        # the toplevel 'Sample Projects' entry.
        if libobj.get_local_abspath() is not None:
            examples_folder = _pp_.rel_to_abs(
                rootpath=libobj.get_local_abspath(),
                relpath="examples",
            )
            if os.path.isdir(examples_folder):
                sample_sketches_dict = (
                    _libmanager_.LibManager().list_sample_sketches(
                        libobj=libobj
                    )
                )
                add_node(
                    _sketch_dict_=sample_sketches_dict,
                    _node_=self,
                )
        return


class LibSamplesContextMenu(_contextmenu_.ContextMenuRoot):
    """Context menu for 'samples' item for a library in the Home Window."""

    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        """"""
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )

        #! SAMPLE PROJECTS
        libobj: _libobj_.LibObj = item.get_projSegment()
        self.add_child(
            SampleProjectsNode(
                contextmenu_root=self,
                parent=self,
                libobj=libobj,
            )
        )

        #! HELP
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Help",
                key="help",
                iconpath="icons/dialog/help.png",
            )
        )
        return


class AddLibContextMenu(_contextmenu_.ContextMenuRoot):
    """Context Menu for 'Add Library' entry in Home Window."""

    def __init__(
        self,
        widg: qt.QWidget,
        item: _item_.Item,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        super().__init__(
            widg=widg,
            item=item,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )

        #! DOWNLOAD LIBRARY
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Download Library",
                key="download_library",
                iconpath="icons/gen/download.png",
            )
        )

        #! ADD LIBRARY FROM ZIPFILE
        self.add_child(
            _contextmenu_.ContextMenuTopleaf(
                contextmenu_root=self,
                parent=self,
                text="Add Library from Zipfile",
                key="add_library_from_zipfile",
                iconpath="icons/folder/closed/zip.png",
            )
        )
        return
