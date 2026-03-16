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
import traceback
import qt, functions, functools, data, gui
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_richlbl as _cm_richbtn_
import dashboard.items.item as _da_
import libmanager.libobj as _libobj_
import libmanager.libmanager as _libmanager_
import tree_widget.widgets.item_arrow as _cm_arrow_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
from various.kristofstuff import *


class LibSampleNodeItem(_da_.Folder):
    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: LibSampleNodeItem) -> None:
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

            def start(*args) -> None:
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

            def sync_self(*args) -> None:
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                node_name = self.get_item().get_name()
                sketch_dict = self.get_item().get_sketch_dict()
                # * This is the toplevel node
                if node_name.lower() == "topnode":
                    # $ Toplevel node has no children
                    if (sketch_dict is None) or (len(sketch_dict) == 0):
                        lbltext = (
                            "samples:".ljust(15, "^")
                            + '<span style="color:#888a85;">None</span>'
                        )
                        self.closedIconpath = "icons/tool_cards/card_chip.png"
                        self.openIconpath = "icons/tool_cards/card_chip.png"
                    # $ Toplevel node has children
                    else:
                        lbltext = (
                            "samples:".ljust(15, "^")
                            + f'<a href="foobar">[...]</a>'
                        )
                        self.closedIconpath = "icons/tool_cards/card_chips.png"
                        self.openIconpath = "icons/tool_cards/card_chips.png"
                # * This is a sub-node
                else:
                    # $ Sub-node has no children
                    # This is weird - if it has no children, it shouldn't
                    # be a node at all. Or perhaps this node corresponds
                    # to an empty folder.
                    if (sketch_dict is None) or (len(sketch_dict) == 0):
                        lbltext = (
                            f"{node_name}".ljust(15, "^")
                            + '<span style="color:#888a85;">None</span>'
                        )
                        self.closedIconpath = "icons/tool_cards/card_chip.png"
                        self.openIconpath = "icons/tool_cards/card_chip.png"
                    # $ Sub-node has children
                    else:
                        lbltext = (
                            f"{node_name}".ljust(15, "^")
                            + f'<a href="foobar">[...]</a>'
                        )
                        self.closedIconpath = "icons/tool_cards/card_chips.png"
                        self.openIconpath = "icons/tool_cards/card_chips.png"
                lbltext = lbltext.replace("^", "&nbsp;")
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
                if refreshlock:
                    self.get_item().release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            start()
            return

    __slots__ = ("__sketch_dict",)

    def __init__(
        self,
        libobj: _libobj_.LibObj,
        rootdir: _da_.Root,
        parent: Union[_da_.Folder, _lib_item_shared_.LibItemShared],
        sample_folder_name: str,
        sketch_dict: Dict,
    ) -> None:
        """Create a LibSampleNodeItem()-instance for the dashboard/home window,
        to list the sample projects recursively.

        :param libobj: The Lib()-instance that represents the library.
        :param rootdir: The toplevel LIBRARIES dashboard item.
        :param parent: Can be the dashboard/home window item representing the
            library (what you get for 'libobj.get_dashboard_item()') or another
            LibSampleNodeItem()-instance.
        :param sample_folder_name: If this is the toplevel node, name it
            'topnode'. Otherwise, give it the name of the hdd folder
            corresponding to this node.
        :param sketch_dict: The dictionary extracted from
            'list_sample_sketches()' in 'libmanager .py'. If this is the
            topnode, the full dictionary should be given. Otherwise, only a part
            of it.
        """
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=sample_folder_name,
            state=LibSampleNodeItem.Status(item=self),
        )
        self.__sketch_dict: Dict = sketch_dict
        self.get_state().sync_state(
            refreshlock=False,
            callback=None,
            callbackArg=None,
        )
        return

    def get_sketch_dict(self) -> Dict:
        return self.__sketch_dict

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:
            return
        super().init_layout()
        libobj = self.get_projSegment()
        arrow = None
        if (self.__sketch_dict is None) or (len(self.__sketch_dict) == 0):
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
        self.show_samples()
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_samples()
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return

    def leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemRichLbl(event)
        self.show_samples()
        return

    def rightclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemRichLbl(event)
        return

    def show_samples(self) -> None:
        """Investigate one's own sketch_dict. This sketch_dict actually
        represents the folder structure for the sample projects on the
        harddrive. One's own sketch dict represents the part of this folder
        structure that is rele- vant to oneself.

        Spawn one node-child per node in the sketch_dict and one leaf-child per
        string.

        When called the first time, the method 'refill_children_later()' gets
        invoked to spawn all the children. Subsequent calls don't spawn them
        again - they just close/open this item to show them.

        Nevertheless, the children refresh themselves through their
        'sync_state()' method. They each keep a reference to the LibObj() whose
        samples are being listed and store their own harddrive-foldername (if a
        node) or sample-project-name (if a leaf).

        WARNING:
        As this function is only invoked by direct user clicks, it is okay to
        invoke the 'toggle_open()' method, which runs 'open_later()' or 'close_
        later()' with the 'click' parameter set to True. That leads to locking
        the 'data.user_lock' mutex during the open or close action.
        """

        def finish(*args) -> None:
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
        node_name = self.get_name()
        sketch_dict = self.get_sketch_dict()

        def start(*args) -> None:
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

        def list_children(*args) -> None:
            "List all dependency names"
            assert len(self.get_childlist()) == 0
            if (sketch_dict is None) or (len(sketch_dict) == 0):
                finish()
                return
            childlist = []
            for k, v in sketch_dict.items():
                # $ Child is a leaf
                if isinstance(v, str):
                    childlist.append(
                        LibSampleLeafItem(
                            libobj=libobj,
                            rootdir=rootItem,
                            parent=self,
                            sample_name=v,
                        )
                    )
                    continue
                # $ Child is a node
                childlist.append(
                    LibSampleNodeItem(
                        libobj=libobj,
                        rootdir=rootItem,
                        parent=self,
                        sample_folder_name=k,
                        sketch_dict=sketch_dict[k],
                    )
                )
                continue
            add_next(iter(childlist))
            return

        def add_next(childiter) -> None:
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

        def finish(*args) -> None:
            "Complete adding all children"
            callback(callbackArg) if callback is not None else nop()
            return

        start()
        return


class LibSampleLeafItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: LibSampleLeafItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/tool_cards/card_chip.png"
            self.openIconpath = "icons/tool_cards/card_chip.png"
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

            def start(*args) -> None:
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

            def sync_self(*args) -> None:
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                sample_name: str = self.get_item().get_name()
                lbltext = sample_name
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish(*args) -> None:
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
        sample_name: str,
    ) -> None:
        """A LibSampleLeafItem()-instance is a child of the
        LibdependenciesItem()- instance. It represents one dependency.

        :param libobj:  The LibObj()-instance that represents the library whose
                        dependencies are being listed - not the dependent
                        library itself!

        :param rootdir: The toplevel LIBRARIES dashboard item.

        :param parent:  The LibItem() bound to the LibObj()-instance: what you
                        get when invoking 'libobj.get_dashboard_item()'.

        :param sample_name: The name of the sketch file.
        """
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=sample_name,
            state=LibSampleLeafItem.Status(item=self),
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
        self.__launch_sample_project()
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.__launch_sample_project()
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return

    def leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemRichLbl(event)
        self.__launch_sample_project()
        return

    def rightclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemRichLbl(event)
        return

    def __launch_sample_project(self) -> None:
        """Ask user if he wants to download the sample project."""
        sketch_relpath = self.get_relpath()
        try:
            sketch_relpath = sketch_relpath.split("/topnode/")[1]
            sketch_relpath = f"<samples>/{sketch_relpath}"
            import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_

            _lib_item_shared_.launch_sample_project(
                sketch_key=sketch_relpath,
                libobj=self.get_projSegment(),
            )
        except Exception as e:
            err_text = traceback.format_exc()
            print(err_text)
            err_text_printout = err_text.replace("\n", "<br>")
            gui.dialogs.popupdialog.PopupDialog.ok(
                parent=data.main_form,
                title_text="CANNOT FIND SAMPLE PROJECT",
                icon_path="icons/gen/book.png",
                text=str(
                    f"Embeetle could not locate the sample project.<br>"
                    f"Please contact us to report this problem.<br>"
                    f"<br>"
                    f"{err_text_printout}<br>"
                ),
            )
        return
