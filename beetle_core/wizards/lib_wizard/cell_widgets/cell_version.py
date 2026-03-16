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
import weakref
import qt, data, purefunctions, functions
import gui.helpers.advancedcombobox as _advancedcombobox_
import libmanager.libmanager as _libmanager_
import wizards.lib_wizard.cell_widgets.cell_widget as _cell_widget_

if TYPE_CHECKING:
    import libmanager.libobj as _libobj_
from various.kristofstuff import *


class VersionLabel(_cell_widget_.CellLabel):
    """"""

    def __init__(
        self,
        row: int,
        col: int,
        libobj: _libobj_.LibObj,
        gridlyt: qt.QGridLayout,
        parent: qt.QFrame,
        minwidth: int,
        maxwidth: int,
    ) -> None:
        """"""
        super().__init__(
            row=row,
            col=col,
            libobj=libobj,
            text=libobj.get_version(),
            gridlyt=gridlyt,
            parent=parent,
            minwidth=minwidth,
            maxwidth=maxwidth,
        )
        # self.destroyed.connect(lambda: print(f"[{libname}] destroyed col 0"))
        return

    def has_combobox(self) -> bool:
        """"""
        return False

    def get_libversion(self) -> str:
        """This method from CellWidget() superclass must be overridden here!"""
        # Version remains constant here (otherwise use the combobox).
        return self.get_libobj().get_version()

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill VersionLabel() twice!")
            self.dead = True

        _cell_widget_.CellLabel.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return


class ComboBoxVersionFrm(_cell_widget_.CellFrm):
    """"""

    def __init__(
        self,
        row: int,
        col: int,
        libobj: _libobj_.LibObj,
        versionlist: List[str],
        gridlyt: qt.QGridLayout,
        parent: qt.QFrame,
        minwidth: int,
        maxwidth: int,
    ) -> None:
        """"""
        super().__init__(
            row=row,
            col=col,
            libobj=libobj,
            gridlyt=gridlyt,
            parent=parent,
            minwidth=minwidth,
            maxwidth=maxwidth,
        )
        self.__lyt = qt.QVBoxLayout(self)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setSpacing(0)
        combobox = ComboBoxVersion(
            row=row,
            col=col,
            libobj=libobj,
            versionlist=versionlist,
            gridlyt=gridlyt,
            parent=self,
        )
        self.__lyt.addWidget(combobox)
        self.__combobox_ref: weakref.ReferenceType[ComboBoxVersion] = (
            weakref.ref(combobox)
        )
        # self.destroyed.connect(lambda: print(f"[{libname}] destroyed col 2"))
        return

    def sizeHint(self) -> qt.QSize:
        """Apply the given 'minwidth' and 'maxwidth' parameters on the returned
        size hint."""
        # Take the size from the superclass. These will be the minima.
        size = super().sizeHint()
        w1 = size.width()
        h1 = size.height()
        # Compute the pixel width from the first entry.
        combobox: ComboBoxVersion = self.__combobox_ref()
        w2 = int(
            2.5
            * data.get_general_font_width()
            * len(combobox.get_selected_item_name())
        )
        w = max(w1, w2)
        h = h1
        return qt.create_qsize(w, h)

    def has_combobox(self) -> bool:
        """"""
        return True

    def get_libversion(self) -> str:
        """This method from CellWidget() superclass must be overridden here!"""
        return self.__combobox_ref().get_selected_item_name().strip()

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ComboBoxVersionFrm() twice!"
                )
            self.dead = True

        # $ Disconnect signals
        # No signals

        def finish(*args) -> None:
            # $ Kill leftovers
            functions.clean_layout(self.__lyt)

            # $ Reset variables
            self.__lyt = None

            # $ Deparent oneself
            _cell_widget_.CellFrm.self_destruct(
                self,
                callback=callback,
                callbackArg=callbackArg,
                death_already_checked=True,
            )
            return

        combobox: ComboBoxVersion = self.__combobox_ref()

        # $ Remove child widgets
        self.__lyt.removeWidget(combobox)

        # $ Kill and deparent children
        combobox.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return


class ComboBoxVersion(_advancedcombobox_.AdvancedComboBox):
    """"""

    def __init__(
        self,
        row: int,
        col: int,
        libobj: _libobj_.LibObj,
        versionlist: List[str],
        gridlyt: qt.QGridLayout,
        parent: ComboBoxVersionFrm,
    ) -> None:
        """The versionlist is a list of version-strings and should already be
        sorted from high-to-low (recent-to-old)."""
        size = data.get_libtable_icon_pixelsize()
        super().__init__(
            parent=parent,
            image_size=size,
        )
        # MyPy seems unable to figure out the type of 'self.dead' from the superclass. Therefore, I
        # repeat the attribute here after ensuring it actually already existed.
        assert hasattr(self, "dead")
        self.dead: bool = False
        self.setMouseTracking(True)
        assert len(versionlist) > 0
        for i, v in enumerate(versionlist):
            self.add_version_item(
                libversion=v,
                is_most_recent=(i == 0),
                replace=False,
            )
        self.set_selected_name(versionlist[0])
        # Make the combobox transparent, such that the blue hover color from the frame underneath
        # can shine through.
        self.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                background-color: #00ffffff;
            }}
            QGroupBox:hover {{
                background-color: {data.theme['indication']['hover']};
            }}
            QGroupBox:focus {{
                color: {data.theme['indication']['background_selection']};
            }}
        """
        )
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Ignored,
            qt.QSizePolicy.Policy.Ignored,
        )
        self.selection_changed.connect(self.selection_changed_func)
        return

    def add_version_item(
        self,
        libversion: str,
        is_most_recent: bool,
        replace: bool,
    ) -> None:
        """Add a new entry to this combobox. Required parameters:

        :param libversion: Library version.
        :param is_most_recent: True if most recent version of the library.
        :param replace: True if the entry is already in the combobox and just
            needs a replacement.
        """
        new_item = {
            "name": libversion,
            "widgets": [
                {
                    "type": "text",
                    "text": f"  {libversion}  ",
                    "color": "default",
                },
            ],
        }
        if replace:
            self.change_item(
                name=libversion,
                new_item=new_item,
            )
        else:
            self.add_item(new_item)
        return

    @qt.pyqtSlot()
    def selection_changed_func(self) -> None:
        """Find the new LibObj()-instance from the database that represents the
        chosen version.

        Then apply it on the parent and all its neighbors.
        """
        # $ Extract libname and chosen version
        libname = (
            cast(ComboBoxVersionFrm, self.parent()).get_libobj().get_name()
        )
        libversion = self.get_selected_item_name().strip()
        print(
            f"\nLibrary {q}{libname}{q} switched\n"
            f"to version {q}{libversion}{q}\n"
        )
        # $ Find propdict from json cruncher
        libobj = _libmanager_.LibManager().get_libobj_from_merged_libs(
            libname=libname,
            libversion=libversion,
            origins=["zip_url", "local_abspath"],
        )
        if libobj is None:
            purefunctions.printc(
                f"\nERROR: LibObj() for library {q}{libname}{q}\n"
                f"       with version {q}{libversion}{q} not found!\n",
                color="error",
            )
            return
        # $ Assign libobj to the parent and its neighbors
        cast(ComboBoxVersionFrm, self.parent()).assign_new_libobj(libobj)
        return

    def self_destruct(
        self,
        death_already_checked: bool = False,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        *args,
        **kwargs,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill ComboBoxVersion() twice!")
            self.dead = True

        super().self_destruct(death_already_checked=True)
        if callback is not None:
            callback(callbackArg)
        return
