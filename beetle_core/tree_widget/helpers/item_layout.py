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
from components.decorators import ref
import time, threading, functools, weakref
import qt, purefunctions, functions
import tree_widget.items.item as _cm_
import tree_widget.helpers.spacer_layout as _sl_
import tree_widget.widgets.item_chbx as _item_chbx_
from various.kristofstuff import *

# ^                                ITEM LAYOUT                                 ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


class ItemLayout(object):

    def __init__(self, item):
        """ItemLayout()-instance is the superclass of FolderLayout() and
        FileLayout()."""
        self._itemRef = weakref.ref(item)
        self._leftSpacerLyt = None
        return

    @ref
    def get_item(self) -> Union[_cm_.Folder, _cm_.File]:
        return self._itemRef  # noqa

    def set_leftSpacerLyt(self, leftSpacerLyt):
        self._leftSpacerLyt = weakref.ref(leftSpacerLyt)
        return

    def clear_leftSpacerLyt(self):
        self._leftSpacerLyt = None

    @ref
    def get_leftSpacerLyt(self) -> _sl_.SpacerLayout:
        return self._leftSpacerLyt

    def get_parentFolderLyt(self) -> FolderLayout:
        parent = self.get_item().get_parent()
        parentLyt = parent.get_layout() if parent is not None else None
        return parentLyt

    def get_own_index(self) -> tuple:
        """Get a tuple (i, n) in which: > i: index of oneself in the parental
        layout. > n: nr of hlyt's in the parental layout.

        ┌─parentFolderLyt──────┐ H_LYT   ⦙   ITEM_LYT     ⦙  RESULT
        │┌────────────────────┐│﹍﹍﹍﹍﹍⦙﹍﹍﹍﹍﹍﹍﹍﹍﹍⦙﹍﹍﹍﹍﹍﹍﹍ ││ 🗀  parent         ││
        hlyt: 0 ⦙                ⦙                 <- hlyts start counting from
        here │└────────────────────┘│         ⦙                ⦙
        │╔═══╦════════════════╗│         ⦙                ⦙ │║ S ║ 🗀  child
        ║│ hlyt: 1 ⦙  itemLyt: 0    ⦙  (0, 2)         <- itemLyts start counting
        from here │╚═══╩════════════════╝│         ⦙                ⦙
        │╔═══╦════════════════╗│         ⦙                ⦙ │║ S ║ 🗋　 child
        ║│ hlyt: 2 ⦙  itemLyt: 1    ⦙  (1, 2) │╚═══╩════════════════╝│         ⦙
        ⦙ └──────────────────────┘
        """
        parentLyt = self.get_parentFolderLyt()
        childLytList = parentLyt.get_itemLytList_children()
        n = len(childLytList)
        i = childLytList.index(self)
        return i, n

    def initialize(self, hlyt: Union[qt.QHBoxLayout, qt.QLayout]) -> None:
        """Called by subclass.

        If subclass.. > FolderLayout()  -> hlyt is one of the many hlyt's spawn
        inside                      FolderLayout() > FileLayout() -> hlyt is the
        FileLayout() itself
        """
        item: Union[_cm_.Folder, _cm_.File] = self._itemRef()
        widgetIter = item.get_widgetIter()
        while True:
            widg = None
            try:
                widg = next(widgetIter)
                if isinstance(widg, _item_chbx_.ItemChbx):
                    widg = widg if item.get_state().showChbx else None
                hlyt.addWidget(widg) if widg is not None else nop()
            except StopIteration:
                break
        return

    def clean(self) -> None:
        functions.clean_layout(self)
        return

    def open_lyt_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Only implemented in FolderLayout()."""
        raise NotImplementedError()

    def close_lyt_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Only implemented in FolderLayout()."""
        raise NotImplementedError()


# ^                                FOLDER LAYOUT                               ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


class FolderLayout(ItemLayout, qt.QVBoxLayout):

    def __init__(self, folder: _cm_.Folder) -> None:
        """A FolderLayout()-instance belongs to a specific Folder()."""
        ItemLayout.__init__(self, folder)
        qt.QVBoxLayout.__init__(self)
        self.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        return

    def initialize(self, *args) -> None:
        """FolderLayout().initialize() needs to be called each time this
        Folder()- instance gets displayed again (after it got hidden because the
        parent closed)."""
        assert threading.current_thread() is threading.main_thread()
        assert self.count() == 0
        hlyt = qt.QHBoxLayout()
        hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        hlyt.setSpacing(0)
        hlyt.setContentsMargins(0, 0, 0, 0)
        self.addLayout(hlyt)
        ItemLayout.initialize(self, hlyt=hlyt)
        return

    """ =============================================== """
    """GETTERS."""
    """ =============================================== """

    # NOTE:
    # I added 'qt.QLayout' to all of the return types to avoid type checking er-
    # rors. In reality, the more specific types should be returned.
    def get_hlytList(self) -> List[Union[qt.QLayout, qt.QHBoxLayout]]:
        return [self.itemAt(i).layout() for i in range(self.count())]

    def get_hlytList_children(self) -> List[Union[qt.QLayout, qt.QHBoxLayout]]:
        return [self.itemAt(i).layout() for i in range(1, self.count())]

    def get_hlytList_rev(self) -> List[Union[qt.QLayout, qt.QHBoxLayout]]:
        return [self.itemAt(i).layout() for i in reversed(range(self.count()))]

    def get_hlytList_rev_children(
        self,
    ) -> List[Union[qt.QLayout, qt.QHBoxLayout]]:
        return [
            self.itemAt(i).layout() for i in reversed(range(1, self.count()))
        ]

    def get_hlytGen(self) -> Generator[Union[qt.QLayout, qt.QHBoxLayout]]:
        return (self.itemAt(i).layout() for i in range(self.count()))

    def get_hlytGen_children(
        self,
    ) -> Generator[Union[qt.QLayout, qt.QHBoxLayout]]:
        return (self.itemAt(i).layout() for i in range(1, self.count()))

    def get_hlytGen_rev(self) -> Generator[Union[qt.QLayout, qt.QHBoxLayout]]:
        return (self.itemAt(i).layout() for i in reversed(range(self.count())))

    def get_hlytGen_rev_children(
        self,
    ) -> Generator[Union[qt.QLayout, qt.QHBoxLayout]]:
        return (
            self.itemAt(i).layout() for i in reversed(range(1, self.count()))
        )

    def get_itemLytList_children(
        self,
    ) -> List[Union[ItemLayout, FolderLayout, FileLayout, qt.QLayout]]:
        return [
            self.itemAt(i).layout().itemAt(1).layout()
            for i in range(1, self.count())
        ]

    def get_itemLytList_rev_children(
        self,
    ) -> List[Union[ItemLayout, FolderLayout, FileLayout, qt.QLayout]]:
        return [
            self.itemAt(i).layout().itemAt(1).layout()
            for i in reversed(range(1, self.count()))
        ]

    def get_itemLytGen_children(
        self,
    ) -> Generator[Union[ItemLayout, FolderLayout, FileLayout, qt.QLayout]]:
        return (
            self.itemAt(i).layout().itemAt(1).layout()
            for i in range(1, self.count())
        )

    def get_itemLytGen_rev_children(
        self,
    ) -> Generator[Union[ItemLayout, FolderLayout, FileLayout, qt.QLayout]]:
        return (
            self.itemAt(i).layout().itemAt(1).layout()
            for i in reversed(range(1, self.count()))
        )

    """ =============================================== """
    """OPEN AND CLOSE."""
    """ =============================================== """

    def open_lyt_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Open this FolderLayout(), filling it with the items from the
        correspon- ding Folder()-instance."""
        assert threading.current_thread() is threading.main_thread()
        folder: _cm_.Folder = self.get_item()
        chassis = None
        if folder.get_rootdir() is not None:
            chassis = folder.get_rootdir().get_chassis()
        left_spacer_lyt = (
            self.get_leftSpacerLyt()
        )  # One's own SpacerLayout() on the left
        time_start = time.time()
        time_end = 0
        child_cntr = 0

        def add_next(child_iter: Iterator[_cm_.Item]) -> None:
            assert threading.current_thread() is threading.main_thread()
            nonlocal child_cntr
            try:
                child = next(child_iter)
                if child._v_layout is not None:
                    purefunctions.printc(
                        f"\nWARNING: Child {child.get_name()} is being added to "
                        f"{folder.get_name()}, however, the child already has its "
                        f"_v_layout initialized!\n",
                        color="warning",
                    )
            except StopIteration:
                finish()
                return

            child_lyt = child.get_layout()
            # if childLyt.count() > 0:
            #     print(
            #         f'WARNING: {child.get_name()}.get_layout().count() = {childLyt.count()}\n'
            #         f'Last time this happened when the load() function overrides the state->cfg_spec'
            #     )

            # $ 1. Create hlyt
            hlyt = qt.QHBoxLayout()
            hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
            hlyt.setSpacing(0)
            hlyt.setContentsMargins(0, 0, 0, 0)
            self.addLayout(hlyt)

            # $ 2. Add spacerLyt to hlyt
            spacer_lyt = _sl_.SpacerLayout(
                parentFolderLyt=self,
                rightItemLyt=child_lyt,
            )
            if child_cntr == 0:
                spacer_lyt.set_TSpacer_ad()
            else:
                spacer_lyt.set_TSpacer()
            hlyt.addLayout(spacer_lyt)

            # $ 3. Add childLyt to hlyt
            hlyt.addLayout(child_lyt)
            child_lyt.set_leftSpacerLyt(spacer_lyt)
            child_lyt.initialize()

            # $ 4. Tell left spacerlayout that you increased
            if left_spacer_lyt is not None:
                left_spacer_lyt.increase()

            # $ 5. Ensure child visibility
            child_cntr += 1
            if child_cntr % 20 == 0:
                # Use timer once in a while
                qt.QTimer.singleShot(
                    5,
                    functools.partial(
                        add_next,
                        child_iter,
                    ),
                )
            else:
                add_next(child_iter)
            return

        def finish(*args) -> None:
            # Replace last TSpacer() -> LSpacer()
            nonlocal time_end
            time_end = time.time()
            # print(f'\nOPEN:  {time_end - time_start:.2f} s [{childcntr} items]')
            self.update()
            if self.count() > 1:
                hlyt = self.itemAt(self.count() - 1).layout()
                spacer_lyt: _sl_.SpacerLayout = hlyt.itemAt(0).layout()
                assert (
                    spacer_lyt.count() == 1
                )  # The child on the right should not be opened yet!
                spacer_lyt.transform_TSpacer_to_LSpacer(
                    True if child_cntr == 1 else False
                )
            callback(callbackArg)
            return

        # * Start
        qt.QTimer.singleShot(
            5,
            functools.partial(
                add_next,
                iter(folder.get_childlist()),
            ),
        )
        return

    def close_lyt_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Close this FolderLayout(). By the time this function gets called,
        all.

        subdirs are already closed!
        After the close has finished, all children's guiVars - including their
        ItemLayout() - are destroyed.
        """
        left_spacer_lyt = (
            self.get_leftSpacerLyt()
        )  # One's own SpacerLayout() on the left
        time_start = time.time()
        time_end = None
        child_cntr = 0

        def remove_next_a(hlyt_gen: Generator[qt.QHBoxLayout]) -> None:
            assert threading.current_thread() is threading.main_thread()
            try:
                hlyt: qt.QHBoxLayout = next(hlyt_gen)

                # SpacerLayout() to the left of the child
                child_spacer_lyt: _sl_.SpacerLayout = hlyt.itemAt(
                    0
                ).layout()  # noqa

                # ItemLayout() from the child
                child_item_lyt: ItemLayout = hlyt.itemAt(1).layout()  # noqa

                # The child
                child = child_item_lyt.get_item()

                assert isinstance(hlyt, qt.QHBoxLayout)
                assert isinstance(child_spacer_lyt, _sl_.SpacerLayout)
                assert isinstance(child_item_lyt, ItemLayout)
                assert child.get_layout() is child_item_lyt
            except StopIteration:
                finish()
                return
            assert hlyt.count() == 2

            # $ 1. Clean and destroy SpacerLayout()
            assert (
                child_spacer_lyt.count() == 1
            ), f"""
                While closing [{self.get_item().get_relpath()}], 
                child [{hlyt.itemAt(1).layout().get_item().get_relpath()}]
                (open={hlyt.itemAt(1).layout().get_item()._state.open}) wasn't 
                closed properly: child_spacer_lyt.count() = {child_spacer_lyt.count()}
            """
            child_spacer_lyt.clean()
            child_spacer_lyt.setParent(None)  # noqa
            child_spacer_lyt.deleteLater()

            # $ 2. Clean and destroy child's ItemLayout()
            child.kill_guiVars_later(
                callback=remove_next_b,
                callbackArg=(hlyt, hlyt_gen),
            )
            return

        def remove_next_b(
            arg: Tuple[qt.QHBoxLayout, Generator[qt.QHBoxLayout]],
        ) -> None:
            hlyt, hlyt_gen = arg
            nonlocal child_cntr

            # $ 3. hlyt is now empty. Delete it
            assert hlyt.count() == 0
            hlyt.setParent(None)  # noqa
            hlyt.deleteLater()

            # $ 4. Notify one's own SpacerLayout() on the left about the shrink
            if left_spacer_lyt is not None:
                left_spacer_lyt.decrease()

            # $ 5. Next
            child_cntr += 1
            if child_cntr % 20 == 0:
                # Use timer once in a while
                qt.QTimer.singleShot(
                    5,
                    functools.partial(
                        remove_next_a,
                        hlyt_gen,
                    ),
                )
            else:
                remove_next_a(hlyt_gen)
            return

        def finish(*args) -> None:
            # check: after closing, only one hlyt remains.
            assert self.count() == 1
            assert isinstance(self.itemAt(0).layout(), qt.QHBoxLayout)
            # Check: one's own SpacerLayout() on the left has only one spacer.
            assert (left_spacer_lyt is None) or (left_spacer_lyt.count() == 1)
            nonlocal time_end
            time_end = time.time()
            # print(f'CLOSE: {time_end - time_start:.2f} s [{childcntr} items]\n')
            if callback is not None:
                callback(callbackArg)

        # * Start
        qt.QTimer.singleShot(
            5,
            functools.partial(
                remove_next_a,
                self.get_hlytGen_rev_children(),
            ),
        )
        return

    def calc_nr_items(self) -> int:
        """"""
        nr = 1
        hlytGen = (
            self.itemAt(i).layout() for i in reversed(range(1, self.count()))
        )
        for hlyt in hlytGen:
            childLyt = hlyt.itemAt(1).layout()
            assert isinstance(childLyt, FileLayout) or isinstance(
                childLyt, FolderLayout
            )
            if isinstance(childLyt, FolderLayout):
                nr += childLyt.calc_nr_items()
            elif isinstance(childLyt, FileLayout):
                nr += 1
            else:
                assert False
        return nr

    def insert_one_item(
        self,
        child: _cm_.Item,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Insert the item at a location based on its appearance in the
        childlist.

        NOTE:
        The algorithm won't work if this FolderLayout() contains items that are
        no longer in the childlist!
        """
        assert threading.current_thread() is threading.main_thread()
        folder: _cm_.Folder = self.get_item()
        folder = self.get_item()
        leftSpacerLyt = (
            self.get_leftSpacerLyt()
        )  # One's own SpacerLayout() on the left

        def determine_index(*args) -> None:
            # Example: Insert child_C..
            #  🗀 parent                  🗀 parentLyt
            #   ├─ 🗋　child_A  i = 0       ├─ 🗋　childLyt_A  j = 0
            #   ├─ 🗋　child_B  i = 1       ├─ 🗋　childLyt_B  j = 1
            #   ├─ 🗋　child_C  i = 2       └─ 🗋　childLyt_D  j = 2
            #   └─ 🗋　child_D  i = 3
            #               i   j
            #    child_A: ( 0 , 0    )
            #    child_B: ( 1 , 1    )
            #    child_C: ( 2 , None )
            #    child_D: ( 3 , 2    )
            childlist: List[Union[_cm_.Folder, _cm_.File]] = (
                folder.get_childlist()
            )
            child_lyt_list: List[Union[FolderLayout, FileLayout]] = (
                self.get_itemLytList_children()
            )

            # Check if childLytList is effectively a subset
            for childLyt in child_lyt_list:
                assert childLyt.get_item() in childlist
            assert len(childlist) > len(child_lyt_list)

            # Assign (i,j) numbers
            number_list = []
            i = -1
            j = -1
            for _child_ in childlist:
                i += 1
                if _child_.get_layout() in child_lyt_list:
                    j += 1
                    number_list.append((_child_, i, j))
                else:
                    number_list.append((_child_, i, None))
                if _child_ is child:
                    break
            assert (
                number_list[-1][0] is child
            )  # Child at the end of number_list
            assert number_list[-1][2] is None  # j-index for child is still None

            # Now get the new j-index for this child
            newJ = None
            for numberTuple in reversed(number_list):
                _child_ = numberTuple[0]
                j = numberTuple[2]
                if j is not None:
                    newJ = j + 1
                    break
            newJ = 0 if newJ is None else newJ
            qt.QTimer.singleShot(
                10,
                functools.partial(
                    insert_item,
                    newJ + 1,
                ),
            )
            return

        def insert_item(j) -> None:
            child_lyt = child.get_layout()

            def insert_child(*args):
                nr = self.count()
                # $ 1. Create hlyt
                hlyt = qt.QHBoxLayout()
                hlyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
                hlyt.setSpacing(0)
                hlyt.setContentsMargins(0, 0, 0, 0)

                # $ 2. Add spacerLyt to hlyt
                spacerLyt = _sl_.SpacerLayout(
                    parentFolderLyt=self,
                    rightItemLyt=child_lyt,
                )
                spacerLyt.set_TSpacer()
                hlyt.addLayout(spacerLyt)

                # $ 3. Add childLyt to hlyt
                hlyt.addLayout(child_lyt)
                child_lyt.set_leftSpacerLyt(spacerLyt)
                child_lyt.initialize()

                # $ 4. Add hlyt to oneself - at the right spot!
                self.insertLayout(j, hlyt)
                self.update()
                assert self.count() == nr + 1

                # $ 5. Tell left spacerlayout that you increased
                leftSpacerLyt.increase() if leftSpacerLyt is not None else nop()
                qt.QTimer.singleShot(10, finish)
                return

            child.rescale_later(
                refreshlock=True,
                callback=insert_child,
                callbackArg=None,
            )
            return

        def finish():
            # Acquire the hlyt holding the last child. It's the last hlyt.
            last_hlyt = self.itemAt(self.count() - 1).layout()
            last_childLyt = last_hlyt.itemAt(1).layout()
            if last_childLyt is child.get_layout():
                # The added child was put at the end. Transform its TSpacer()
                # into an LSpacer(). Put an arrow down in the LSpacer() if this
                # added child is actually the only one (so two hlyts).
                last_spacerLyt: _sl_.SpacerLayout = (
                    last_childLyt.get_leftSpacerLyt()
                )
                last_spacerLyt.transform_TSpacer_to_LSpacer(
                    ad=(self.count() == 2)
                )

                if self.count() > 2:
                    # The prelast item - formerly the last - needs its LSpacer()
                    # replaced with a TSpacer().
                    prelast_hlyt = self.itemAt(self.count() - 2).layout()
                    prelast_childLyt: ItemLayout = prelast_hlyt.itemAt(
                        1
                    ).layout()
                    prelast_spacerLyt: _sl_.SpacerLayout = (
                        prelast_childLyt.get_leftSpacerLyt()
                    )
                    assert prelast_spacerLyt is prelast_hlyt.itemAt(0).layout()
                    # Put an arrow-down in the TSpacer() if this prelast item
                    # is actually also the first item. That's the case if there
                    # are now exactly two items (so three hlyts).
                    prelast_spacerLyt.transform_LSpacer_to_TSpacer(
                        ad=(self.count() == 3)
                    )
            # Acquire the hlyt holding the first child. It's not at index 0,
            # because the hlyt at index 0 holds the self (the folder).
            first_hlyt = self.itemAt(1).layout()
            first_childLyt: ItemLayout = first_hlyt.itemAt(1).layout()
            if first_childLyt is child.get_layout():
                # The added child was put at the beginning. Transform its
                # TSpacer() into a TSpacer() with an arrow down. Or its
                # LSpacer() into an LSpacer() with arrow down.
                if self.count() > 2:
                    # Added child is first one, but there are more children af-
                    # ter it.
                    first_spacerLyt: _sl_.SpacerLayout = (
                        first_childLyt.get_leftSpacerLyt()
                    )
                    first_spacerLyt.transform_TSpacer(ad=True)
                else:
                    # Added child is only one.
                    first_spacerLyt = first_childLyt.get_leftSpacerLyt()
                    first_spacerLyt.transform_LSpacer(ad=True)
                if self.count() > 2:
                    # The prefirst item - formerly the first - needs its
                    # T/LSpacer() cleaned from the arrow down.
                    prefirst_hlyt = self.itemAt(2).layout()
                    prefirst_childLyt: ItemLayout = prefirst_hlyt.itemAt(
                        1
                    ).layout()
                    prefirst_spacerLyt: _sl_.SpacerLayout = (
                        prefirst_childLyt.get_leftSpacerLyt()
                    )
                    assert (
                        prefirst_spacerLyt is prefirst_hlyt.itemAt(0).layout()
                    )
                    if self.count() == 3:
                        # This prefirst item is also the last one.
                        prefirst_spacerLyt.transform_LSpacer(ad=False)
                    else:
                        prefirst_spacerLyt.transform_TSpacer(ad=False)
            if callback is not None:
                callback(callbackArg)
            return

        qt.QTimer.singleShot(10, determine_index)
        return

    def remove_one_item(
        self, child: _cm_.Item, callback: Optional[Callable], callbackArg: Any
    ) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()

        # One's own SpacerLayout() on the left
        left_spacer_lyt = self.get_leftSpacerLyt()
        assert self.get_item() is child.get_parent()

        def finish(_hlyt: qt.QHBoxLayout) -> None:
            # $ 3. hlyt is now empty. Delete it
            # Remember, 'hlyt' used to contain the child and its spacers.
            assert _hlyt.count() == 0
            _hlyt.setParent(None)  # noqa
            _hlyt.deleteLater()

            # $ 4. Notify one's own SpacerLayout() on the left about the shrink
            left_spacer_lyt.decrease() if left_spacer_lyt is not None else nop()

            # $ 5. Replace last TSpacer() -> LSpacer()
            # $    Make sure first spacer has an arrow
            if self.count() > 1:
                last_hlyt = self.itemAt(self.count() - 1).layout()
                last_spacerLyt: _sl_.SpacerLayout = last_hlyt.itemAt(0).layout()
                # We're not sure it's a TSpacer though..
                # If the last item is also the only one, make sure its LSpacer()
                # has an arrow down!
                last_spacerLyt.transform_TSpacer_to_LSpacer(
                    ad=(self.count() == 2)
                )
                # Take also care of the first T/LSpacer().
                first_hlyt = self.itemAt(1).layout()
                first_spacerLyt: _sl_.SpacerLayout = first_hlyt.itemAt(
                    0
                ).layout()  # noqa
                if self.count() == 2:
                    # First item is also last.
                    first_spacerLyt.transform_LSpacer(ad=True)
                else:
                    first_spacerLyt.transform_TSpacer(ad=True)

            # $ 6. Callback
            callback(callbackArg) if callback is not None else nop()
            return

        # * Start
        if isinstance(child, _cm_.Folder):
            assert child.get_state().open is False, str(
                "Cannot remove an opened folder from its parental layout."
            )
        # 'i' is the index of the child in the self (parent).
        # 'n' is the number of children the self has.
        i, n = child.get_layout().get_own_index()
        if n != len(self.get_item().get_childlist()):
            # This particular problem happens if you open the home
            # window and immediately navigate into the 'LIBRARIES'
            # section. The Add-item is being removed and re-added
            # in the initialization procedure.
            purefunctions.printc(
                f"\nWARNING: remov_one_item({child.get_name()}) invoked on "
                f"{self.get_item().get_name()} while not all its children "
                f"were already shown. ",
                color="warning",
            )
        # 'hlyt' is the horizontal layout from the self, containing the
        # child and the child its spacers.
        hlyt = self.itemAt(i + 1).layout()
        child_spacer_lyt: _sl_.SpacerLayout = hlyt.itemAt(0).layout()
        child_item_lyt: ItemLayout = hlyt.itemAt(1).layout()
        assert child_item_lyt is child.get_layout()
        assert child is child_item_lyt.get_item()

        # $ 1. Clean and destroy SpacerLayout()
        assert child_spacer_lyt.count() == 1, str(
            f"Removing child "
            f"[{hlyt.itemAt(1).layout().get_item().get_relpath()}] from "
            f"parent [{self.get_item().get_relpath()}], "
            f"but child "
            f"(open={hlyt.itemAt(1).layout().get_item()._state.open}) "
            f"wasn{q}t closed properly: "
            f"childSpacerLyt.count() = {child_spacer_lyt.count()}"
        )
        child_spacer_lyt.clean()
        child_spacer_lyt.setParent(None)  # noqa
        child_spacer_lyt.deleteLater()

        # $ 2. Clean and destroy child's ItemLayout()
        child.kill_guiVars_later(
            callback=finish,
            callbackArg=hlyt,
        )
        return


# ^                                FILE LAYOUT                                 ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


class FileLayout(ItemLayout, qt.QHBoxLayout):

    def __init__(self, file: _cm_.File) -> None:
        """"""
        ItemLayout.__init__(self, file)
        qt.QHBoxLayout.__init__(self)
        self.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        return

    def initialize(self, *args) -> None:
        # assert self.count() == 0
        ItemLayout.initialize(self, hlyt=self)
        return

    # def addWidget(self, *args, **kwargs):
    #     print(f"{self.get_item().get_name()} -> FileLayout.addWidget({args}, {kwargs})")
    #     super().addWidget(*args, **kwargs)

    """ =============================================== """
    """CHECKBOXES."""
    """ =============================================== """

    def open_lyt_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        raise RuntimeError()

    def close_lyt_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        raise RuntimeError()
