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
import functools, weakref, threading
import qt, data, purefunctions, iconfunctions
import tree_widget.helpers.item_layout as _il_
from various.kristofstuff import *


class SpacerLayout(qt.QVBoxLayout):
    def __init__(
        self,
        parentFolderLyt: _il_.FolderLayout,
        rightItemLyt: _il_.ItemLayout,
    ) -> None:
        """Layout()-instance to hold spacers. The SpacerLayout() can only have
        one T-Spacer or L- spacer, all subsequent ones are I-spacers.
        ┌───┬───────────────┐ │ ├─│🗀 rightFolder │ │ │ │ ├─🗋　         │ │ │ │
        └─🗋　         │ └───┴───────────────┘

        :param parentFolderLyt: FolderLayout() that holds this
            SpacerLayout()-instance in one of its hlyt's.
        :param rightItemLyt: ItemLayout() to the right of this SpacerLayout().
        """
        super().__init__()
        self.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.__spacer_layout_mutex = threading.Lock()
        self.__parentFolderLyt_ref = weakref.ref(parentFolderLyt)
        self.__rightItemLyt_ref = weakref.ref(rightItemLyt)
        self.__superframe_ref = None
        # The rootdir can be None for items in the Intro Wizard
        if rightItemLyt.get_item().get_rootdir() is not None:
            self.__superframe_ref = weakref.ref(
                rightItemLyt.get_item().get_rootdir().get_chassis_body()
            )
        return

    @ref
    def get_parentFolderLyt(self) -> _il_.FolderLayout:
        """Get the FolderLayout() that owns this SpacerLayout() in one of its
        hlyt's.

        ┌─*parentFolderLyt*───────┐
        │┌────────────────────┐│
        ││ 🗀  parent         ││
        │└────────────────────┘│
        │╔═══╦════════════════╗│
        │║ ME║ 🗀  child      ║│
        │╚═══╩════════════════╝│
        │╔═══╦════════════════╗│
        │║   ║ 🗋　 child  　  ║│
        │╚═══╩════════════════╝│
        └──────────────────────┘
        """
        return self.__parentFolderLyt_ref

    @ref
    def get_rightItemLyt(self) -> _il_.ItemLayout:
        """Get the ItemLayout() that sits to the right of this SpacerLayout().

        ┌─parentFolderLyt─────────┐
        │┌────────────────────┐│
        ││ 🗀  parent         ││
        │└────────────────────┘│
        │╔═══╦════════════════╗│
        │║ ME║ 🗀  *child*    ║│
        │╚═══╩════════════════╝│
        │╔═══╦════════════════╗│
        │║   ║ 🗋　 child  　  ║│
        │╚═══╩════════════════╝│
        └──────────────────────┘
        """
        return self.__rightItemLyt_ref

    def set_TSpacer(self) -> None:
        """"""
        if self.count() != 0:
            purefunctions.printc(
                f"ERROR: SpacerLayout().set_TSpacer() was "
                f"{self.count()} before adding TSpacer()",
                color="error",
            )
        if self.__superframe_ref is not None:
            self.addWidget(TSpacer(self.__superframe_ref()))
        else:
            # For items in the intro wizard:
            self.addWidget(TSpacer(None))
        if self.count() != 1:
            purefunctions.printc(
                f"ERROR: SpacerLayout().set_TSpacer() was "
                f"{self.count()} after adding TSpacer()",
                color="error",
            )
        return

    def set_TSpacer_ad(self) -> None:
        """"""
        if self.count() != 0:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().set_TSpacer_ad() was "
                f"{self.count()} before adding TSpacer_ad()\n",
                color="error",
            )
        if self.__superframe_ref is not None:
            self.addWidget(TSpacer_ad(self.__superframe_ref()))
        else:
            # For items in the intro wizard:
            self.addWidget(TSpacer_ad(None))
        if self.count() != 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().set_TSpacer_ad() was "
                f"{self.count()} after adding TSpacer_ad()\n",
                color="error",
            )
        return

    def set_LSpacer(self) -> None:
        """"""
        if self.count() != 0:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().set_LSpacer() was "
                f"{self.count()} before adding LSpacer()\n",
                color="error",
            )
        if self.__superframe_ref is not None:
            self.addWidget(LSpacer(self.__superframe_ref()))
        else:
            # For items in the intro wizard:
            self.addWidget(LSpacer(None))
        if self.count() != 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().set_LSpacer() was "
                f"{self.count()} after adding LSpacer()\n",
                color="error",
            )
        return

    def set_LSpacer_ad(self) -> None:
        """"""
        if self.count() != 0:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().set_LSpacer_ad() was "
                f"{self.count()} before adding LSpacer_ad()\n",
                color="error",
            )
        if self.__superframe_ref is not None:
            self.addWidget(LSpacer_ad(self.__superframe_ref()))
        else:
            # For items in the intro wizard:
            self.addWidget(LSpacer_ad(None))
        if self.count() != 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().set_LSpacer_ad() was "
                f"{self.count()} after adding LSpacer_ad()\n",
                color="error",
            )
        return

    def add_ISpacer(self) -> None:
        """"""
        nr = self.count()
        if nr == 0:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().add_ISpacer() was "
                f"{nr} before adding ISpacer()\n",
                color="error",
            )
        if self.__superframe_ref is not None:
            self.addWidget(ISpacer(self.__superframe_ref()))
        else:
            # For items in the intro wizard:
            self.addWidget(ISpacer(None))
        if self.count() != nr + 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().add_ISpacer() was "
                f"{self.count()} after adding ISpacer() and "
                f"{nr} before\n",
                color="error",
            )
        return

    def remove_ISpacer(self) -> None:
        """"""
        nr = self.count()
        if nr <= 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().remove_ISpacer() was "
                f"{nr} before removing ISpacer()\n",
                color="error",
            )
        l_item = self.itemAt(nr - 1)
        if l_item is None:
            return
        spacer = l_item.widget()
        if not isinstance(spacer, ISpacer):
            purefunctions.printc(
                f"\nERROR: SpacerLayout().removeISpacer() is actually "
                f"removing another type of spacer: {spacer}\n",
                color="error",
            )
        spacer.hide()
        spacer.setParent(None)  # noqa
        spacer.deleteLater()
        if self.count() != nr - 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().remove_ISpacer() was "
                f"{self.count()} after removing ISpacer() and "
                f"{nr} before\n",
                color="error",
            )
        return

    def transform_TSpacer_to_LSpacer(self, ad=False) -> None:
        """Transform the T-spacer into an L-spacer, and remove all I-spacers:

        ┌───┐      ┌───┐ │ ├─│      │ └─│ │ │ │  =>  │   │ │ │ │      │   │
        └───┘      └───┘
        """
        # One T-spacer, perhaps some I-spacers.
        if self.count() < 1:
            purefunctions.printc(
                f"ERROR: SpacerLayout().transform_TSpacer_to_LSpacer() was "
                f"{self.count()} at te start",
                color="error",
            )
        l_item = self.itemAt(0)
        if l_item is None:
            return
        t_spacer = l_item.widget()
        for i in reversed(range(self.count())):
            l_item = self.itemAt(i)
            if l_item is None:
                continue
            spacer = l_item.widget()
            assert isinstance(spacer, Spacer)
            spacer.hide()
            spacer.setParent(None)  # noqa
            spacer.deleteLater()
        if ad:
            self.set_LSpacer_ad()
        else:
            self.set_LSpacer()
        return

    def transform_TSpacer(self, ad: bool) -> None:
        """Transform the current T-spacer into one with/without arrow down."""
        # One T-spacer, perhaps some I-spacers.
        if self.count() < 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().transform_TSpacer() was "
                f"{self.count()} at te start\n",
                color="error",
            )
        l_item = self.itemAt(0)
        if l_item is None:
            return
        t_spacer = l_item.widget()
        t_spacer.hide()
        t_spacer.setParent(None)  # noqa
        t_spacer.deleteLater()
        if ad:
            if self.__superframe_ref is not None:
                self.insertWidget(
                    0,
                    TSpacer_ad(self.__superframe_ref()),
                )
            else:
                # For items in the intro wizard:
                self.insertWidget(
                    0,
                    TSpacer_ad(None),
                )
        else:
            if self.__superframe_ref is not None:
                self.insertWidget(
                    0,
                    TSpacer(self.__superframe_ref()),
                )
            else:
                # For items in the intro wizard:
                self.insertWidget(
                    0,
                    TSpacer(None),
                )
        return

    def transform_LSpacer_to_TSpacer(self, ad=False) -> None:
        """Transform the L-spacer into a T-spacer, and add enough I-spacers:

        ┌───┐      ┌───┐        Note: Nr of I-spacers to add │ └─│      │ ├─│
        depends on the size of │   │  =>  │ │ │              the directory (if
        it is │   │      │ │ │              a directory) on the right. └───┘
        └───┘
        """
        # One L-spacer, no I-spacers possible.
        if self.count() != 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().transform_LSpacer_to_TSpacer() was "
                f"{self.count()} at te start\n",
                color="error",
            )
        l_item = self.itemAt(0)
        if l_item is None:
            return
        l_spacer = l_item.widget()
        l_spacer.hide()
        l_spacer.setParent(None)
        l_spacer.deleteLater()
        if isinstance(self.get_rightItemLyt(), _il_.FileLayout):
            if ad:
                self.set_TSpacer_ad()
            else:
                self.set_TSpacer()
            return
        elif isinstance(self.get_rightItemLyt(), _il_.FolderLayout):
            if ad:
                self.set_TSpacer_ad()
            else:
                self.set_TSpacer()
            nr = self.get_rightItemLyt().calc_nr_items()
            for i in range(nr - 1):
                self.add_ISpacer()
            assert self.count() == nr
            return
        print(
            f"\nself.get_rightItemLyt() has not known type: "
            f"{self.get_rightItemLyt()}\n"
        )
        return

    def transform_LSpacer(self, ad: bool) -> None:
        """Transform the current L-spacer into one with/without arrow down."""
        # One L-spacer, no I-spacers possible.
        if self.count() != 1:
            purefunctions.printc(
                f"\nERROR: SpacerLayout().transform_LSpacer() was "
                f"{self.count()} at te start\n",
                color="error",
            )
        l_item = self.itemAt(0)
        if l_item is None:
            return
        l_spacer = l_item.widget()
        l_spacer.hide()
        l_spacer.setParent(None)  # noqa
        l_spacer.deleteLater()
        if ad:
            self.set_LSpacer_ad()
        else:
            self.set_LSpacer()
        return

    def increase(self) -> None:
        """
        Call this function to increase the size of this SpacerLayout(), by adding an I-spacer. This
        needs to happen if the neighbor - the FolderLayout() on the right - has inserted a child.

        This 'increase()' function propagates upwards to:
            > The SpacerLayout()-instance to the left of the directory owning this SpacerLayout()-
              instance
            > and so forth...

        This propagation happens immediate. I don't believe the GUI will freeze, as most directory
        structures are just a few levels deep.
        """
        assert threading.current_thread() is threading.main_thread()
        # 1. Is right neighbor last element in the list?
        i, n = self.get_rightItemLyt().get_own_index()
        if i == n - 1:
            pass
        else:
            self.add_ISpacer()
        # 2. Propagate
        spacerLyt = self.get_parentFolderLyt().get_leftSpacerLyt()
        spacerLyt.increase() if spacerLyt is not None else nop()
        return

    def decrease(self) -> None:
        """Idem.

        The notification propagates upwards.
        """
        assert threading.current_thread() is threading.main_thread()
        # 1. Is right neighbor last element in the list?
        i, n = self.get_rightItemLyt().get_own_index()
        if i == n - 1:
            pass
        else:
            self.remove_ISpacer()
        # 2. Propagate
        spacerLyt = self.get_parentFolderLyt().get_leftSpacerLyt()
        spacerLyt.decrease() if spacerLyt is not None else nop()
        return

    def rescale(self) -> None:
        """Rescale all spacers in this SpacerLyt() immediately."""
        l_item_list: List[qt.QLayoutItem] = [
            self.itemAt(i) for i in range(self.count())
        ]
        spacer_iter: Generator[Spacer] = (
            l_item.widget() for l_item in l_item_list if l_item is not None
        )  # noqa
        while True:
            try:
                spacer = next(spacer_iter)
            except StopIteration:
                return
            assert isinstance(spacer, Spacer)
            spacer.rescale()
        return

    def rescale_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Rescale all spacers in this SpacerLyt() with some delays."""
        if not self.__spacer_layout_mutex.acquire(blocking=False):
            qt.QTimer.singleShot(
                10,
                functools.partial(
                    self.rescale_later,
                    callback,
                    callbackArg,
                ),
            )
            return

        def rescale_next(_spacer_iter: Generator[Spacer]) -> None:
            try:
                spacer = next(_spacer_iter)
                assert isinstance(spacer, Spacer)
            except StopIteration:
                # * Finish
                self.__spacer_layout_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return
            spacer.rescale()
            qt.QTimer.singleShot(
                5,
                functools.partial(
                    rescale_next,
                    _spacer_iter,
                ),
            )
            return

        l_item_list: List[qt.QLayoutItem] = [
            self.itemAt(i) for i in range(self.count())
        ]
        spacer_iter: Generator[Spacer] = (
            l_item.widget() for l_item in l_item_list if l_item is not None
        )  # noqa
        rescale_next(spacer_iter)
        return

    def clean(self) -> None:
        """Remove all spacers."""
        assert self.count() > 0
        for i in reversed(range(self.count())):
            l_item = self.itemAt(i)
            if l_item is None:
                continue
            spacer = l_item.widget()
            assert isinstance(spacer, Spacer)
            spacer.hide()
            spacer.setParent(None)  # noqa
            spacer.deleteLater()
        assert self.count() == 0


class Spacer(qt.QPushButton):
    def __init__(self, superframe: qt.QFrame, iconpath: str) -> None:
        """Superclass for ISpacer(), TSpacer() and LSpacer()

        :param iconpath: Relative path to icon.
        """
        super().__init__(superframe)
        # self.destroyed.connect(
        #     lambda: print('<<< Spacer() destroyed     >>>')
        # )
        self.setStyleSheet(
            """
            QPushButton {
                margin: 0px;
                padding: 0px;
                background-color: transparent;
            }
        """
        )
        _icon_ = iconfunctions.get_qicon(iconpath)
        if self.icon() is _icon_:
            print("icon already set")
        else:
            self.setIcon(_icon_)
        self.rescale()
        return

    def rescale(self) -> None:
        """"""
        outer_size = data.get_general_icon_pixelsize(is_inner=False) * 1.15
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Fixed,
            qt.QSizePolicy.Policy.Fixed,
        )
        self.setIconSize(qt.create_qsize(outer_size, outer_size))
        return

    def sizeHint(self) -> qt.QSize:
        """"""
        outer_size = data.get_general_icon_pixelsize(is_inner=False) * 1.15
        return qt.create_qsize(outer_size, outer_size)


class ISpacer(Spacer):
    def __init__(self, superframe: Optional[qt.QFrame]) -> None:
        """"""
        super().__init__(
            superframe=superframe,
            # iconpath   = 'icons/arrow/spacer/ISpacer.png' if not data.theme['is_dark'] else 'icons/arrow/spacer/ISpacer_dark.png',
            iconpath="icons/arrow/spacer/ISpacer.png",
        )
        return


class TSpacer(Spacer):
    def __init__(self, superframe: Optional[qt.QFrame]) -> None:
        """"""
        super().__init__(
            superframe=superframe,
            # iconpath   = 'icons/arrow/spacer/TSpacer.png' if not data.theme['is_dark'] else 'icons/arrow/spacer/TSpacer_dark.png',
            iconpath="icons/arrow/spacer/TSpacer.png",
        )
        return


class TSpacer_ad(Spacer):
    def __init__(self, superframe: Optional[qt.QFrame]) -> None:
        """"""
        super().__init__(
            superframe=superframe,
            # iconpath   = 'icons/arrow/spacer/TSpacer_ad.png' if not data.theme['is_dark'] else 'icons/arrow/spacer/TSpacer_ad_dark.png',
            iconpath="icons/arrow/spacer/TSpacer_ad.png",
        )
        return


class LSpacer(Spacer):
    def __init__(self, superframe: Optional[qt.QFrame]) -> None:
        """"""
        super().__init__(
            superframe=superframe,
            # iconpath   = 'icons/arrow/spacer/LSpacer.png' if not data.theme['is_dark'] else 'icons/arrow/spacer/LSpacer_dark.png',
            iconpath="icons/arrow/spacer/LSpacer.png",
        )
        return


class LSpacer_ad(Spacer):
    def __init__(self, superframe: Optional[qt.QFrame]) -> None:
        """"""
        super().__init__(
            superframe=superframe,
            # iconpath   = 'icons/arrow/spacer/LSpacer_ad.png' if not data.theme['is_dark'] else 'icons/arrow/spacer/LSpacer_ad_dark.png',
            iconpath="icons/arrow/spacer/LSpacer_ad.png",
        )
        return
