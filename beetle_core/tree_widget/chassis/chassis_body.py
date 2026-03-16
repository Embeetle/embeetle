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
import weakref, functools, threading
import qt, data, functions
import gui.stylesheets.tree_chassis as _tree_chassis_
import tree_widget.items.item as _cm_
import components.decorators as _dec_

if TYPE_CHECKING:
    import tree_widget.chassis.chassis as _chassis_
    import tree_widget.widgets.item_btn as _item_btn_
    import tree_widget.widgets.item_action_btn as _item_action_btn_
    import tree_widget.widgets.item_lbl as _item_lbl_
from various.kristofstuff import *


class ChassisBody(qt.QFrame):
    def __init__(
        self,
        chassis: _chassis_.Chassis,
        tabname: str = "default",
    ) -> None:
        """The ChassisBody() belongs to a specific 'tabname'."""
        super().__init__()
        self._chassisRef: weakref.ReferenceType[_chassis_.Chassis] = (
            weakref.ref(chassis)
        )
        self.__tabname = tabname
        self._rootlist: List[Union[_cm_.Root, _cm_.Folder]] = []
        self._lyt = qt.QVBoxLayout()
        self._lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self._lyt.setSpacing(0)
        self._lyt.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._lyt)
        self.__prevBtnScale = 0
        self.__prevFontScale = 0
        self.__blinking_items_dict = {}  # { itempath : True/False }
        self.__blinking_items = []  # [ item ]
        self.__go_to_item_mutex = threading.Lock()
        self.setStyleSheet(_tree_chassis_.get_transparent())
        self.setProperty("hexagons", True)
        return

    @_dec_.ref
    def get_chassis(self) -> _chassis_.Chassis:
        """"""
        return self._chassisRef  # noqa

    def get_tabname(self) -> str:
        """"""
        return self.__tabname

    def set_tabname(self, tabname: str) -> None:
        """"""
        self.__tabname = tabname
        return

    def body_add_root(self, rootdir: Union[_cm_.Root, _cm_.Folder]) -> None:
        """Add given 'rootdir' to 'self._rootlist', and connect oneself as the
        chassis-body of the given rootdir."""
        self._rootlist.append(rootdir)
        rootdir.connect_chassis_body(self)
        self._lyt.addLayout(rootdir.get_layout())
        rootdir.get_layout().initialize()
        return

    def body_remove_root(self, rootdir: Union[_cm_.Root, _cm_.Folder]) -> None:
        """Remove the given 'rootdir' from 'self._rootlist'."""
        assert rootdir.is_dead()
        self._rootlist.remove(rootdir)
        return

    def body_get_rootlist(self):
        """"""
        return self._rootlist

    def body_rescale_or_refresh_recursive(
        self,
        action: str,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Rescale this segment, next rescale all roots recursively."""
        if action == "rescale":
            if (data.get_general_icon_pixelsize() == self.__prevBtnScale) and (
                data.get_general_font_pointsize() == self.__prevFontScale
            ):
                if callback is not None:
                    callback(callbackArg)
                return

        def apply_next_root(
            root_iter: Iterator[Union[_cm_.Root, _cm_.Folder]],
        ) -> None:
            try:
                root: Union[_cm_.Root, _cm_.Folder] = next(root_iter)
            except StopIteration:
                if callback is not None:
                    callback(callbackArg)
                return
            if action == "rescale":
                assert not force_stylesheet
                root.rescale_recursive_later(
                    refreshlock=False,
                    callback=apply_next_root,
                    callbackArg=root_iter,
                )
            elif action == "refresh":
                root.refresh_recursive_later(
                    refreshlock=False,
                    force_stylesheet=force_stylesheet,
                    callback=apply_next_root,
                    callbackArg=root_iter,
                )
            else:
                raise RuntimeError()
            return

        # * Start
        if action == "rescale":
            self.__prevBtnScale = data.get_general_icon_pixelsize()
            self.__prevFontScale = data.get_general_font_pointsize()
        apply_next_root(iter(self._rootlist))
        return

    def body_find_item(
        self,
        abspath: Optional[str],
        check: bool,
        update_libraries: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Find item, put it as first argument in the callback.

        :param abspath:          [Optional] Absolute path to the item.
        :param check:            Check each item's childlist while browsing,
                                 do repairs when needed.
        :param update_libraries: While doing repairs, also update the libraries.

        Note: if this is called from a non-main thread, any reparation in the
        childlist won't be shown in the GUI immediately.

            > callback(found_item, callbackArg)
        """
        rootdir_candidates = []
        for _rootdir in self.body_get_rootlist():
            if abspath.startswith(_rootdir.get_abspath()):
                rootdir_candidates.append(_rootdir)

        def try_next_rootdir(rootdir_iter: Iterator[_cm_.Root]) -> None:
            "Start searching in next rootdir"
            try:
                rootdir = next(rootdir_iter)
            except StopIteration:
                abort()
                return
            rootdir.find_item(
                abspath=abspath,
                check=check,
                update_libraries=update_libraries,
                callback=finish_next_rootdir,
                callbackArg=rootdir_iter,
            )
            return

        def finish_next_rootdir(
            found_item: Optional[_cm_.Item],
            rootdir_iter: Iterator[_cm_.Root],
        ) -> None:
            "Finish searching in next rootdir"
            if found_item is not None:
                # Bingo!
                callback(found_item, callbackArg)
                return
            try_next_rootdir(rootdir_iter)
            return

        def abort(*args):
            "Nothing found"
            callback(None, callbackArg)
            return

        try_next_rootdir(iter(rootdir_candidates))
        return

    def body_go_to_item(
        self,
        abspath: str,
        callback1: Optional[Callable],
        callbackArg1: Any,
        callback2: Optional[Callable],
        callbackArg2: Any,
    ) -> None:
        """Go to the item indicated by the given relpath or abspath.

        When you call this function, the 'self.__blinking_items_dict{}' dict
        gets an entry for the given itempath. The entry is set to 'True' and
        stays that way (even after this function has long finished). But, this
        function will first set all the other entries to 'False'.

        While running, this function regularly checks its own entry. If another
        invokation of this function has cleared the flag for this run, the run
        stops.

        I've also implemented a separate list, called 'self.__blinking_items[]'.
        Just before (!) the found item starts to actually blink, it gets added
        to this list. When its done - either by time or force - it removes it-
        self from the list.

        When this function starts, it checks if the list has items, and forces
        them to stop blinking immediately.

        self.__blinking_items_dict = {}     # { itempath : True/False }
        self.__blinking_items = []          # [ item ]

        Why two lists, one with the 'itempath' and another containing the actual
        item-objects? That's because the item-object is not available from the
        start. The 'self.__blinking_items[]' will therefore not reveal other
        runs of this function that are somewhere in the middle... so you can't
        stop them!
        """

        def stop_other_blinks(other_blinks_gen) -> None:
            try:
                other_blink = next(other_blinks_gen)
            except StopIteration:
                wait_for_mutex()
                return
            if other_blink is not None:
                btn: Optional[_item_btn_.ItemBtn] = other_blink.get_widget(
                    "itemBtn"
                )
                action_btn: Optional[_item_action_btn_.ItemActionBtn] = (
                    other_blink.get_widget("itemActionBtn")
                )
                if btn is not None:
                    btn.blink_stop(
                        callback=stop_other_blinks,
                        callbackArg=other_blinks_gen,
                    )
                elif action_btn is not None:
                    action_btn.blink_stop(
                        callback=stop_other_blinks,
                        callbackArg=other_blinks_gen,
                    )
            else:
                stop_other_blinks(other_blinks_gen)
            return

        def wait_for_mutex(*args):
            if self.__blinking_items_dict[abspath] is False:
                go_to_fail(mutex=None)
                return
            if not self.__go_to_item_mutex.acquire(blocking=False):
                qt.QTimer.singleShot(100, wait_for_mutex)
                return
            # Local mutex acquired.
            go_to_start()
            return

        def go_to_start(*args):
            assert (
                self.__go_to_item_mutex.locked()
            ), "Must have local mutex right now."
            rootIter = iter(self.body_get_rootlist())
            get_chain(rootIter)
            return

        def get_chain(rootIter):
            try:
                root = next(rootIter)
            except StopIteration:
                go_to_fail(mutex=self.__go_to_item_mutex)
                return
            root.get_item_chain(
                relpath=None,
                abspath=abspath,
                check=True,
                update_libraries=True,
                callback=test_chain,
                callbackArg=rootIter,
            )
            return

        def test_chain(chain, rootIter):
            if self.__blinking_items_dict[abspath] is False:
                go_to_fail(mutex=self.__go_to_item_mutex)
                return
            if chain is None:
                get_chain(rootIter)
            else:
                try_open_folder((None, chain, 0))
            return

        def try_open_folder(arg):
            if self.__blinking_items_dict[abspath] is False:
                go_to_fail(mutex=self.__go_to_item_mutex)
                return
            item, chain, i = arg
            # Consider the opening a success.
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    go_to_next,
                    (chain, i),
                ),
            )
            return

        def go_to_next(arg):
            if self.__blinking_items_dict[abspath] is False:
                go_to_fail(mutex=self.__go_to_item_mutex)
                return
            chain, i = arg
            item = chain[i]
            i += 1
            if i < len(chain):
                # Somewhere in the middle.
                if isinstance(item, _cm_.Folder):
                    if item.get_state().open:
                        self._chassisRef().ensure_item_visible(item)
                        qt.QTimer.singleShot(
                            3,
                            functools.partial(
                                go_to_next,
                                (chain, i),
                            ),
                        )
                        return
                    else:
                        item.open_later(
                            click=False,
                            callback=try_open_folder,
                            callbackArg=(item, chain, i),
                        )
                        return
                elif isinstance(item, _cm_.File):
                    assert False
                else:
                    assert False
            else:
                # Last item.
                go_to_success(item)
            return

        def go_to_success(
            item: Optional[Union[_cm_.File, _cm_.Folder]],
        ) -> None:
            nonlocal callback1
            if self.__blinking_items_dict[abspath] is False:
                go_to_fail(mutex=self.__go_to_item_mutex)
                return

            if item is None:
                print("item was killed in the meantime -> cannot blink")
                finish(item)
                return

            btn: Optional[_item_btn_.ItemBtn] = item.get_widget("itemBtn")
            lbl: Optional[_item_lbl_.ItemLbl] = item.get_widget("itemLbl")
            action_btn: Optional[_item_action_btn_.ItemActionBtn] = (
                item.get_widget("itemActionBtn")
            )

            if (btn is None) and (action_btn is None):
                print("item was killed in the meantime -> cannot blink")
                finish(item)
                return

            self._chassisRef().ensure_item_visible(item)
            self.__blinking_items.append(item)
            if callback1 is not None:
                callback1(item, callbackArg1)
            callback1 = None

            # $ blink ItemBtn()
            if btn is not None:
                btn.blink(
                    itemlbl=lbl,
                    callback=finish,
                    callbackArg=item,
                )
                return

            # $ blink ItemActionBtn()
            assert action_btn is not None
            action_btn.blink(
                itemlbl=lbl,
                callback=finish,
                callbackArg=item,
            )
            return

        def finish(item: Optional[Union[_cm_.File, _cm_.Folder]]) -> None:
            nonlocal callback1
            nonlocal callback2
            try:
                (
                    self.__blinking_items.remove(item)
                    if item is not None
                    else nop()
                )
            except ValueError:
                # Item was killed in meantime -> cannot blink
                pass
            self.__go_to_item_mutex.release()
            callback1(item, callbackArg1) if callback1 is not None else nop()
            callback2(item, callbackArg2) if callback2 is not None else nop()
            return

        def go_to_fail(mutex):
            mutex.release() if mutex is not None else nop()
            callback1(None, callbackArg1) if callback1 is not None else nop()
            callback2(None, callbackArg2) if callback2 is not None else nop()
            return

        for key in self.__blinking_items_dict:
            self.__blinking_items_dict[key] = False
        self.__blinking_items_dict[abspath] = True
        if not self.__go_to_item_mutex.acquire(blocking=False):
            stop_other_blinks(iter(self.__blinking_items))
            return
        # Local mutex acquired.
        assert len(self.__blinking_items) == 0
        go_to_start()
        return

    def body_self_destruct(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Kill the Root()-objects, and clean the layout. After that, kill all
        attributes.

        WARNING:
        It is possible that all the Root()-instances already died at this point.
        Ignore them in such case.
        """

        def kill_root(_rootIter):
            try:
                root: Union[_cm_.Root, _cm_.Folder] = next(_rootIter)
            except StopIteration:
                # * Clean layout
                functions.clean_layout(self._lyt)
                qt.QTimer.singleShot(
                    5,
                    kill_attributes,
                )
                return
            if root.is_dead():
                kill_root(_rootIter)
                return
            root.self_destruct(
                killParentLink=False,
                callback=kill_root,
                callbackArg=_rootIter,
            )  # For filetree: click is False by default -> no HDD operations.
            return

        def kill_attributes(*args):
            self._lyt = None
            self._rootlist = None
            self._chassisRef = None
            if callback is not None:
                callback(callbackArg)
            return

        rootIter = iter(self._rootlist)
        kill_root(rootIter)
        return
