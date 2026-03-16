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
import qt, functions, functools, data, os
import bpathlib.path_power as _pp_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_richlbl as _cm_richbtn_
import dashboard.items.item as _da_
import libmanager.libmanager as _libmanager_
import tree_widget.widgets.item_arrow as _cm_arrow_
import libmanager.libobj as _libobj_

if TYPE_CHECKING:
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
from various.kristofstuff import *


class LibdependenciesItem(_da_.Folder):
    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: LibdependenciesItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = None
            self.openIconpath = None
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

            def start():
                if self.get_item() is None:
                    callback(callbackArg) if callback is not None else nop()
                    return
                if refreshlock:
                    if not self.get_item().acquire_refresh_mutex():
                        qt.QTimer.singleShot(
                            10,
                            functools.partial(
                                self.sync_state,
                                refreshlock,
                                callback,
                                callbackArg,
                            ),
                        )
                        return
                _da_.Folder.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args):
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                if (libobj.get_depends() is None) or (
                    len(libobj.get_depends()) == 0
                ):
                    lbltext = (
                        "dependencies:".ljust(15, "^")
                        + '<span style="color:#888a85;">None</span>'
                    )
                    self.closedIconpath = "icons/tool_cards/card_dependency.png"
                    self.openIconpath = "icons/tool_cards/card_dependency.png"
                else:
                    lbltext = (
                        "dependencies:".ljust(15, "^")
                        + '<a href="foo">[...]</a>'
                    )
                    self.closedIconpath = (
                        "icons/tool_cards/card_dependencies.png"
                    )
                    self.openIconpath = "icons/tool_cards/card_dependencies.png"
                lbltext = lbltext.replace("^", "&nbsp;")
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish():
                (
                    self.get_item().release_refresh_mutex()
                    if refreshlock
                    else nop()
                )
                callback(callbackArg) if callback is not None else nop()
                return

            start()
            return

    __slots__ = ()

    def __init__(
        self,
        libobj: _libobj_.LibObj,
        rootdir: _da_.Root,
        parent: Union[_da_.Folder, _lib_item_shared_.LibItemShared],
    ) -> None:
        """Create a LibdependenciesItem()-instance for the dashboard, to show
        the architectures of a specific library.

        :param libobj: The Lib()-instance that represents the library.
        :param rootdir: The toplevel LIBRARIES dashboard item.
        :param parent: The library item bound to the Lib()-instance: what you
            get when you invoke 'libobj.get_dashboard_item()'
        """
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=f"{libobj.get_name()}_deps",
            state=LibdependenciesItem.Status(item=self),
        )
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
        libobj = self.get_projSegment()
        arrow = None
        if (libobj.get_depends() is None) or (len(libobj.get_depends()) == 0):
            arrow = None
        else:
            arrow = _cm_arrow_.ItemArrow(owner=self)
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=arrow,
            itemRichLbl=_cm_richbtn_.ItemRichLbl(owner=self),
        )

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        super().leftclick_itemBtn(event)
        self.show_dependencies()
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_dependencies()
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return

    def leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemRichLbl(event)
        self.show_dependencies()
        return

    def rightclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemRichLbl(event)
        return

    def show_dependencies(self) -> None:
        """Spawn one LibdependencyItem()-child-instance per dependency and open
        oneself to show them all. Invoked upon a left-mouse-click.

        When called the first time, the method 'refill_children_later()' gets
        invoked to spawn all the LibdependencyItem()-children. Subsequent calls
        don't spawn them again - they just close/open this item to show them.
        Nevertheless, the LibdependencyItem()-children refresh themselves
        through their 'sync_state()' method. They each keep a reference to the
        LibObj() whose dependencies are being listed and store their own depen-
        dency-library-name. In fact, the LibObj()-reference is not actively
        being used (yet). But their dependency-library-name is checked against
        the LibManager()'s database to see if the dependency is being fulfilled
        or not. Hence the icon can be adapted.

        WARNING:
        As this function is only invoked by direct user clicks, it is okay to
        invoke the 'toggle_open()' method, which runs 'open_later()' or 'close_
        later()' with the 'click' parameter set to True. That leads to locking
        the 'data.user_lock' mutex during the open or close action.
        """

        def finish(*args):
            self.toggle_open()
            return

        if len(self.get_childlist()) == 0:
            self.refill_children_later(
                callback=finish,
                callbackArg=None,
            )
            return
        finish()
        return

    def refill_children_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Add the dependency-children."""
        libobj: _libobj_.LibObj = self.get_projSegment()
        rootItem = self.get_rootdir()

        def start(*args):
            "Make sure all origins are initialized"
            origins = _libmanager_.LibManager().get_uninitialized_origins()
            if len(origins) > 0:
                _libmanager_.LibManager().initialize(
                    libtable=None,
                    progbar=None,
                    origins=origins,
                    callback=list_children,
                    callbackArg=None,
                )
                return
            list_children()
            return

        def list_children(*args):
            "List all dependency names"
            assert len(self.get_childlist()) == 0
            if (libobj.get_depends() is None) or (
                len(libobj.get_depends()) == 0
            ):
                finish()
                return
            recursive_list: Optional[
                List[str]
            ] = _libmanager_.LibManager().list_dependencies_recursively(
                libobj=libobj,
                initial_call=True,
            )
            if (recursive_list is None) or (len(recursive_list) == 0):
                finish()
                return
            childlist = []
            for name in recursive_list:
                childlist.append(
                    LibdependencyItem(
                        libobj=libobj,
                        rootdir=rootItem,
                        parent=self,
                        dependency_name=name,
                    )
                )
            add_next(iter(childlist))
            return

        def add_next(childiter):
            "Add next LibdependencyItem()-child"
            try:
                child = next(childiter)
            except StopIteration:
                finish()
                return
            self.add_child(
                child=child,
                alpha_order=False,
                show=True,
                callback=add_next,
                callbackArg=childiter,
            )
            return

        def finish(*args):
            "Complete adding all children"
            callback(callbackArg) if callback is not None else nop()
            return

        start()
        return


class LibdependencyItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: LibdependencyItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = None
            self.openIconpath = None
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

            def start():
                if self.get_item() is None:
                    callback(callbackArg) if callback is not None else nop()
                    return
                if refreshlock:
                    if not self.get_item().acquire_refresh_mutex():
                        qt.QTimer.singleShot(
                            10,
                            functools.partial(
                                self.sync_state,
                                refreshlock,
                                callback,
                                callbackArg,
                            ),
                        )
                        return
                _da_.Folder.Status.sync_state(
                    self,
                    refreshlock=False,
                    callback=sync_self,
                    callbackArg=None,
                )
                return

            def sync_self(*args):
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                dependency_name: str = self.get_item().get_name()
                lbltext = dependency_name
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                libs_in_project = []
                libs_in_cache = []
                if not data.is_home:
                    libs_in_project = (
                        _libmanager_.LibManager().list_proj_libs_names()
                    )
                else:
                    libs_in_cache = (
                        _libmanager_.LibManager().list_cached_libs_names()
                    )
                if (dependency_name in libs_in_project) or (
                    dependency_name in libs_in_cache
                ):
                    self.closedIconpath = "icons/dialog/checkmark.png"
                    self.openIconpath = "icons/dialog/checkmark.png"
                else:
                    self.closedIconpath = "icons/dialog/cross.png"
                    self.openIconpath = "icons/dialog/cross.png"
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish():
                (
                    self.get_item().release_refresh_mutex()
                    if refreshlock
                    else nop()
                )
                callback(callbackArg) if callback is not None else nop()
                return

            start()
            return

    __slots__ = ()

    def __init__(
        self,
        libobj: _libobj_.LibObj,
        rootdir: _da_.Root,
        parent: _da_.Folder,
        dependency_name: str,
    ) -> None:
        """A LibdependencyItem()-instance is a child of the
        LibdependenciesItem()- instance. It represents one dependency.

        :param libobj:  The LibObj()-instance that represents the library whose
                        dependencies are being listed - not the dependent
                        library itself!

        :param rootdir: The toplevel LIBRARIES dashboard item.

        :param parent:  The LibItem() bound to the LibObj()-instance: what you
                        get when invoking 'libobj.get_dashboard_item()'.

        :param dependency_name: The name of the library that the libobj depends
                                on.
        """
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=dependency_name,
            state=LibdependencyItem.Status(item=self),
        )
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def init_guiVars(self) -> None:
        if self._v_layout is not None:
            return
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemRichLbl=_cm_richbtn_.ItemRichLbl(owner=self),
        )

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        super().leftclick_itemBtn(event)
        self.__offer_download()
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.__offer_download()
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return

    def leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemRichLbl(event)
        self.__offer_download()
        return

    def rightclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemRichLbl(event)
        return

    def __offer_download(self) -> None:
        """Ask user if he wants to download the missing dependency."""
        dependency_libobj: Optional[_libobj_.LibObj] = None
        dependency_name: str = self.get_name()
        libs_in_project = []
        libs_in_cache = []
        if not data.is_home:
            libs_in_project = _libmanager_.LibManager().list_proj_libs_names()
        else:
            libs_in_cache = _libmanager_.LibManager().list_cached_libs_names()

        # * Dependency present => navigate
        if dependency_name in libs_in_project:
            assert not data.is_home
            dependency_libobj: (
                _libobj_.LibObj
            ) = _libmanager_.LibManager().get_libobj_from_merged_libs(
                libname=dependency_name,
                libversion=None,
                origins=["proj_relpath"],
            )
        elif dependency_name in libs_in_cache:
            assert data.is_home
            dependency_libobj: (
                _libobj_.LibObj
            ) = _libmanager_.LibManager().get_libobj_from_merged_libs(
                libname=dependency_name,
                libversion=None,
                origins=["local_abspath"],
            )
        if dependency_libobj is not None:
            _libmanager_.LibManager().navigate_to_library(dependency_libobj)
            return

        # * Dependency not present => offer download/copy
        assert dependency_libobj is None
        proj_libcollection_folder: Optional[str] = None
        if not data.is_home:
            # Let the dependency be downloaded next to
            # the library that depends from it.
            libobj: _libobj_.LibObj = self.get_projSegment()
            proj_libcollection_folder = _pp_.standardize_abspath(
                os.path.dirname(libobj.get_proj_abspath())
            )
        _libmanager_.LibManager().offer_to_download(
            libname=dependency_name,
            proj_libcollection_folder=proj_libcollection_folder,
            callback=None,
            callbackArg=None,
        )
        return
