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
import data, hardware_api, purefunctions
import bpathlib.path_power as _pp_
import project.segments.project_segment as _ps_

# Use typing.TYPE_CHECKING instead of assigning to a variable
if TYPE_CHECKING:
    import tree_widget
    import tree_widget.items
    import tree_widget.items.item
    import dashboard.items.path_items.treepath_items as _trpi_
    import dashboard.items.path_items.toolpath_items as _topi_
    import dashboard.items.item as _da_
    import home_toolbox.items.toolchain_items.toolchain_items as _tm_tci_
    import home_toolbox.items.flash_tool_items.flash_tool_items as _tm_fdsi_
    import home_toolbox.items.build_automation_items.build_automation_items as _tm_bai_
    import home_toolbox.items.item as _tm_
    import hardware_api.treepath_unicum as _treepath_unicum_
    import hardware_api.toolcat_unicum as _toolcat_unicum_
nop = lambda *a, **k: None
q = "'"
dq = '"'


class PathObj(_ps_.ProjectSubsegment):
    def __init__(
        self,
        unicum: Union[
            _treepath_unicum_.TREEPATH_UNIC,
            _toolcat_unicum_.TOOLCAT_UNIC,
            None,
        ],
        rootpath_or_rootid: Optional[str],
        relpath: Optional[str],
    ) -> None:
        # Add dead attribute for tracking object destruction state
        self.dead: bool = False
        """SUMMARY ======= A PathObj()-instance represents one dirpath or
        filepath. It can also have a pointer to an Item() from the project's
        Dashboard or home's Toolbox. ┌───────────┐ │ PathObj() │ └─────┬─────┘
        ┌────────────────┼──────────────────┐ ┌───────┴───────┐
        ┌──────┴────────┐ ┌───────┴──────┐ │ TreepathObj() │ │ ToolpathObj() │ │
        ToolmanObj() │ └───────────────┘ └───────────────┘ └──────────────┘ ⇵ ⇵
        ⇵ TreepathItem()    ToolpathItem() BuildAutomationItem() FlashToolItem()
        ToolchainItem()

        :param unicum:   TREEPATH_UNIC() or TOOLCAT_UNIC()

        :param rootpath_or_rootid: Provide only if rootpath != project root. Otherwise, provide
                                   None.

        :param relpath:  Relative path with respect to 'rootpath'. If 'None', this PathObj() simply
                         represents 'no path'.

        UNICUMS
        =======
        Each PathObj() can have an Unicum() assigned, which defines what the
        PathObj() represents. That Unicum() can be a TREEPATH_UNIC() or a
        TOOLCAT_UNIC().

        Without such unicum, the PathObj() is anonymous and has no icon (cannot
        be on dashboard).

        Depending on the situation, the Unicum()s can be shared amongst several
        PathObj()s:

                     DASHBOARD                             TOOLBOX
        ╔══════════════════════════════════╗  ╔════════════════════════════════╗
        ║ TOOLCAT_UNIC()     ToolpathObj() ║  ║ TOOLCAT_UNIC()    ToolmanObj() ║
        ║ ┌──────────┐       ┌───────────┐ ║  ║ ┌─────────┐       ┌──────────┐ ║
        ║ │ unic_1  <---------> obj_1    │ ║  ║ │ unic_1 <----┬----> obj_1   │ ║
        ║ │ unic_2  <---------> obj_2    │ ║  ║ │             └----> obj_2   │ ║
        ║ │ unic_3  <---------> obj_3    │ ║  ║ │ unic_2 <---------> obj_3   │ ║
        ║ └──────────┘       └───────────┘ ║  ║ └─────────┘       └──────────┘ ║
        ╚══════════════════════════════════╝  ╚════════════════════════════════╝
        TOOLCAT_UNIC()s are mapped one-to-     TOOLCAT_UNIC()s are shared among
        one with ToolpathObj()s                multiple ToolmanObj()s

        NOTE:
        The ToolpathObj() is just a shell. It only stores 'unique_id' and 'cat_
        unicum', and will always look for the matching ToolmanObj() to return
        vital info.
        """
        super().__init__()

        # * Set unicum
        assert (
            (unicum is None)
            or isinstance(unicum, hardware_api.treepath_unicum.TREEPATH_UNIC)
            or isinstance(unicum, hardware_api.toolcat_unicum.TOOLCAT_UNIC)
        ), f"unicum = {unicum}"
        self.__unicum: Union[
            _treepath_unicum_.TREEPATH_UNIC,
            _toolcat_unicum_.TOOLCAT_UNIC,
            None,
        ] = unicum

        # * Set rootpath_or_rootid and relpath
        if (rootpath_or_rootid is None) or (
            rootpath_or_rootid.lower() == "none"
        ):
            # If there is no rootpath defined, the relpath is irrelevant.
            self.__rootpath_or_rootid = None
            self.__relpath = None
        else:
            # Set rootpath_or_rootid
            if rootpath_or_rootid.startswith("<"):
                # It's an id
                self.__rootpath_or_rootid = rootpath_or_rootid
            else:
                # It's an abspath
                self.__rootpath_or_rootid = _pp_.standardize_abspath(
                    rootpath_or_rootid
                )
            # Set relpath
            if (relpath is None) or (relpath.lower() == "none"):
                self.__relpath = None
            else:
                self.__relpath = _pp_.standardize_relpath(relpath)

        # * Declare GUI Item()s
        self._v_dashboardItem: Union[
            _trpi_.TreepathItem,
            _topi_.ToolpathItem,
            None,
        ] = None
        self._v_toolmanItem: Union[
            _tm_tci_.ToolchainItem,
            _tm_fdsi_.FlashToolItem,
            _tm_bai_.BuildAutomationItem,
            None,
        ] = None

        # * Set GUI attributes
        self.__asterisk: bool = False
        self.__relevant: bool = True
        self.__warning: bool = False
        self.__error: bool = False
        self.__info_purple: bool = False
        self.__info_blue: bool = False
        return

    """
    NOTE:
    =====
    The following properties are no longer pushed
    directly to the dashboard TreepathItem() or
    ToolpathItem(), but are stored here:
        - self._asterisk
        - self._relevant
        - self._warning
        - self._error
        - self._info_purple
        - self._info_blue
        - (readonly gets queried from the unicum)
        
    These properties are pulled...
        - TreepathItem().get_state()
        - ToolpathItem().get_state()
    in their sync_state() methods!
    
    REASON:
    =======
    This way, these properies can be 'alive' even
    before the respective dashboard items are created.
    """

    def set_asterisk(self, a: bool) -> None:
        assert isinstance(a, bool)
        self.__asterisk = a
        return

    def has_asterisk(self) -> bool:
        return self.__asterisk

    def set_relevant(self, r: bool) -> None:
        assert isinstance(r, bool)
        self.__relevant = r
        return

    def is_relevant(self) -> bool:
        return self.__relevant

    def is_readonly(self) -> bool:
        if hasattr(self.get_unicum(), "is_readonly"):
            return self.get_unicum().get_dict()["readonly"]
        return False

    def set_warning(self, w: bool) -> None:
        assert isinstance(w, bool)
        self.__warning = w
        return

    def has_warning(self) -> bool:
        return self.__warning

    def set_error(self, e: bool) -> None:
        assert isinstance(e, bool)
        self.__error = e
        return

    def has_error(self) -> bool:
        return self.__error

    def set_info_purple(self, i: bool) -> None:
        assert isinstance(i, bool)
        self.__info_purple = i
        return

    def has_info_purple(self) -> bool:
        return self.__info_purple

    def set_info_blue(self, i: bool) -> None:
        assert isinstance(i, bool)
        self.__info_blue = i
        return

    def has_info_blue(self) -> bool:
        return self.__info_blue

    # ^                                           DASHBOARD                                            ^#
    # % ============================================================================================== %#
    # % Item()s for the Dashboard.                                                                     %#
    # %                                                                                                %#

    def create_dashboardItem(
        self,
        rootItem: Optional[_da_.Root],
        parentItem: Optional[_da_.Folder],
        *args,
        **kwargs,
    ) -> tree_widget.items.item.Item:
        """Redefined in TreepathObj() and ToolpathObj()."""
        raise RuntimeError()

    def delete_dashboardItem(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Delete the Item() in the Dashboard."""
        assert self._v_dashboardItem is not None

        def finish(*args) -> None:
            assert self._v_dashboardItem.is_dead()
            self._v_dashboardItem = None
            if callback is not None:
                callback(callbackArg)
            return

        if self._v_dashboardItem.is_dead():
            finish()
            return
        self._v_dashboardItem.self_destruct(
            killParentLink=True,
            callback=finish,
            callbackArg=None,
        )
        return

    def get_dashboardItem(self) -> Union[
        _trpi_.TreepathItem,
        _topi_.ToolpathItem,
        None,
    ]:
        """Return the Item() from the Dashboard."""
        if self._v_dashboardItem is None:
            return None
        if self._v_dashboardItem.is_dead():
            purefunctions.printc(
                f"WARNING: {self.get_name()}.get_dashboardItem() returns a "
                f"dead item! Return None instead.",
                color="warning",
            )
            self._v_dashboardItem = None
        return self._v_dashboardItem

    # ^                                            TOOLBOX                                             ^#
    # % ============================================================================================== %#
    # % Item()s for the Toolbox.                                                                       %#
    # %                                                                                                %#

    def create_toolmanItem(
        self,
        rootItem: _tm_.Root,
        parentItem: _tm_.Folder,
    ) -> tree_widget.items.item.Item:
        """Redefined in ToolmanObj()."""
        raise RuntimeError()

    def delete_toolmanItem(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Delete the ToolmanItem() in the Toolbox."""

        def finish(*args):
            self._v_toolmanItem = None
            callback(callbackArg) if callback is not None else nop()
            return

        assert self._v_toolmanItem is not None
        self._v_toolmanItem.self_destruct(
            killParentLink=True,
            callback=finish,
            callbackArg=None,
        )
        return

    def get_toolmanItem(self) -> Union[
        _tm_tci_.ToolchainItem,
        _tm_fdsi_.FlashToolItem,
        _tm_bai_.BuildAutomationItem,
        None,
    ]:
        """Return the ToolmanItem() from the Toolbox."""
        if self._v_toolmanItem is None:
            return None
        if self._v_toolmanItem.is_dead():
            purefunctions.printc(
                f"ERROR: {self.get_name()}.get_toolmanItem() returns a "
                f"dead item! Return None instead.",
                color="error",
            )
            self._v_toolmanItem = None
        return self._v_toolmanItem

    # ^                                       GETTERS AND SETTERS                                      ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def get_unicum(self) -> Union[
        _treepath_unicum_.TREEPATH_UNIC,
        _toolcat_unicum_.TOOLCAT_UNIC,
        None,
    ]:
        """Return the Unicum() that defines this PathObj()."""
        return self.__unicum

    def get_name(self) -> Optional[str]:
        """Return the name of said Unicum()."""
        if self.__unicum is None:
            return None
        return self.__unicum.get_name()

    def get_rootpath(self) -> Optional[str]:
        """Get the rootpath belonging to this PathObj()."""
        # Check a few invariants
        assert not self.__relpath == "None"
        assert not self.__rootpath_or_rootid == "None"

        # Return the rootpath
        rootpath = self.__rootpath_or_rootid
        if rootpath is None:
            return "None"
        if rootpath.startswith("<"):
            rootpath = data.current_project.get_rootpath_from_rootid(rootpath)
        return rootpath

    def get_rootid(self) -> Optional[str]:
        """Get the rootid belonging to this PathObj()."""
        # Check a few invariants
        assert not self.__relpath == "None"
        assert not self.__rootpath_or_rootid == "None"

        # Return the rootid
        rootid = self.__rootpath_or_rootid
        if rootid is None:
            return None
        if not rootid.startswith("<"):
            purefunctions.printc(
                f"WARNING: {self.get_name()}.get_rootid() = {rootid}!",
                color="warning",
            )
            return None
        return rootid

    def get_relpath(self) -> Optional[str]:
        """Return the relative path stored in this PathObj().

        Any prefix like '<project>' should already have been stripped off!
        """
        # Check a few invariants
        assert not self.__relpath == "None"
        assert not self.__rootpath_or_rootid == "None"

        # Return the relpath
        if (self.__relpath is None) or (self.__rootpath_or_rootid is None):
            # If there is no rootpath defined, the relpath is irrelevant.
            return "None"
        assert not self.__relpath.startswith("<")
        return self.__relpath

    def get_abspath(self) -> Optional[str]:
        """Return the absolute path from this PathObj().

        It gets joined here on the spot from the rel- path and rootpath.
        """
        # Check a few invariants
        assert not self.__relpath == "None"
        assert not self.__rootpath_or_rootid == "None"

        # Form and return the abspath
        if (self.__relpath is None) or (self.__rootpath_or_rootid is None):
            # Even if the rootpath would be the only relevant element, the relpath should at least
            # be '.'!
            return "None"
        return _pp_.rel_to_abs(
            self.get_rootpath(),
            self.__relpath,
        )

    def get_doublepath(self) -> Tuple[Optional[str], Optional[str]]:
        """Return the rootpath and the relpath as a tuple."""
        return self.__rootpath_or_rootid, self.__relpath

    def get_closedIconpath(self) -> Optional[str]:
        """Return the 'closed' iconpath that belongs to the Unicum()."""
        if self.__unicum is None:
            return None
        return self.__unicum.get_dict()["icon"]

    def get_openIconpath(self) -> Optional[str]:
        """Return the 'open' iconpath that belongs to the Unicum()."""
        if self.__unicum is None:
            return None
        return self.__unicum.get_dict()["icon"].replace("closed", "open")

    def get_default_relpath(self) -> Optional[str]:
        """Get the default relpath from the Unicum()."""
        # Check a few invariants
        assert not self.__relpath == "None"
        assert not self.__rootpath_or_rootid == "None"

        # Return the default relpath
        return self.__unicum.get_default_relpath()

    def get_default_abspath(self) -> Optional[str]:
        """Same as previous, but obtain the abspath."""
        # Check a few invariants
        assert not self.__relpath == "None"
        assert not self.__rootpath_or_rootid == "None"

        # Return the default abspath
        default_relpath = self.__unicum.get_default_relpath()
        if (
            (default_relpath is None)
            or (default_relpath.lower() == "none")
            or self.__rootpath_or_rootid is None
        ):
            # If the root is None, then a (default) abspath doesn't make sense
            # either!
            return "None"
        return _pp_.rel_to_abs(
            self.get_rootpath(),
            self.get_default_relpath(),
        )

    def set_doublepath(
        self,
        doublepath: Optional[Tuple[Optional[str], Optional[str]]],
    ) -> None:
        """Only function to repoint the path!

        Provide a tuple (rootpath, relpath):
            - rootpath_or_rootid: provide a rootpath or a rootid
            - relpath:            relative to rootpath
        """
        if (doublepath is None) or (doublepath == "None"):
            self.__rootpath_or_rootid = None
            self.__relpath = None
            return

        rootpath_or_rootid, relpath = doublepath

        # * Set rootpath_or_rootid and relpath
        # Set these variables in the same way as is done in the constructor.
        if (rootpath_or_rootid is None) or (
            rootpath_or_rootid.lower() == "none"
        ):
            # If there is no rootpath defined, the relpath is irrelevant.
            self.__rootpath_or_rootid = None
            self.__relpath = None
        else:
            # Set rootpath_or_rootid
            if rootpath_or_rootid.startswith("<"):
                # It's an id
                self.__rootpath_or_rootid = rootpath_or_rootid
            else:
                # It's an abspath
                self.__rootpath_or_rootid = _pp_.standardize_abspath(
                    rootpath_or_rootid
                )
            # Set relpath
            if (relpath is None) or (relpath.lower() == "none"):
                self.__relpath = None
            else:
                self.__relpath = _pp_.standardize_relpath(relpath)
        return

    def call_autolocate_func(
        self,
        force: bool,
        adapt: bool,
        history: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        return data.current_project.get_treepath_seg().autolocate(
            self.__unicum,
            force,
            adapt,
            history,
            callback,
            callbackArg,
        )

    # ^                                             DEATH                                              ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this PathObj()-instance and everything that displays it.

        WARNING:
        This method can be invoked from the ToolpathSeg().self_destruct() method, where the toplevel
        _v_rootItem gets killed first. In that case, the dashboard item is already killed. Don't
        kill it twice!
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill PathObj() {q}{self.__relpath}{q} twice!"
                )
            self.dead = True

        # Supercall not needed. Nothing really happens there.
        # super().self_destruct(...)

        def finish(*args) -> None:
            self.__asterisk = None
            self.__relevant = None
            self.__warning = None
            self.__error = None
            self.__info_purple = None
            self.__info_blue = None
            self.__unicum = None
            self.__relpath = None
            self.__rootpath_or_rootid = None
            self._v_dashboardItem = None
            self._v_toolmanItem = None
            if callback is not None:
                callback(callbackArg)
            return

        if self._v_toolmanItem:
            if self._v_toolmanItem.is_dead():
                finish()
                return
            self.delete_toolmanItem(
                callback=finish,
                callbackArg=None,
            )
            return
        if self._v_dashboardItem:
            if self._v_dashboardItem.is_dead():
                finish()
                return
            self.delete_dashboardItem(
                callback=finish,
                callbackArg=None,
            )
            return
        finish()
        return
