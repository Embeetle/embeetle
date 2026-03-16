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
import os, re
import qt, data, functions, serverfunctions
import gui.templates.paintedgroupbox
import gui.dialogs.popupdialog
import gui.stylesheets.scrollbar as _scrollbar_style_
import wizards.lib_wizard.lib_const as _lib_const_
import wizards.lib_wizard.gen_widgets.check_linebox as _check_linebox_
import libmanager.libmanager as _json_cruncher_

if TYPE_CHECKING:
    pass


class SearchPathsGroupBox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):
    """"""

    line_toggled_sig = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(
            parent=parent,
            name="search",
            text="Library search locations:",
            info_func=lambda *args: print("info clicked!"),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Maximum,
        )
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(0)

        # * QScrollArea()
        self.__scroll_area = qt.QScrollArea(self)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__scroll_area.setVerticalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__scroll_area.setStyleSheet(
            """
            QObject {
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """
        )
        self.__scroll_area.horizontalScrollBar().setStyleSheet(
            _scrollbar_style_.get_horizontal()
        )
        self.__scroll_area.verticalScrollBar().setStyleSheet(
            _scrollbar_style_.get_vertical()
        )
        self.layout().addWidget(self.__scroll_area)

        # * QFrame() and QVBoxLayout()
        self.__scroll_frm = qt.QFrame(None)
        self.__scroll_lyt = qt.QVBoxLayout(self.__scroll_frm)
        self.__scroll_frm.setStyleSheet(
            f"""
            QFrame {{
                background: transparent;
                border: 1px solid {_lib_const_.CELL_FRAME_COL};
                padding: 0px;
                margin: 0px;
            }}
        """
        )
        self.__scroll_lyt.setSpacing(0)
        self.__scroll_lyt.setContentsMargins(0, 0, 0, 0)
        self.__scroll_area.setWidget(self.__scroll_frm)

        # * Online searchpath items
        # $ Embeetle online searchpath
        self.__embeetle_online_searchpath: _check_linebox_.CheckLineBox = (
            _check_linebox_.CheckLineBox(None)
        )
        self.__embeetle_online_searchpath.set_text(
            "[Embeetle online libraries] "
            f'<a href="{serverfunctions.get_base_url_wfb()}/downloads/libraries/library_index.json" style="color: #729fcf;">'
            f"{serverfunctions.get_base_url_wfb()}/downloads/libraries/library_index.json"
            "</a>"
        )
        self.__embeetle_online_searchpath.set_on(False)
        # $ Arduino online searchpath
        self.__arduino_online_searchpath: _check_linebox_.CheckLineBox = (
            _check_linebox_.CheckLineBox(None)
        )
        self.__arduino_online_searchpath.set_text(
            "[Arduino online libraries] "
            '<a href="https://downloads.arduino.cc/libraries/library_index.json" style="color: #729fcf;">'
            "https://downloads.arduino.cc/libraries/library_index.json"
            "</a>"
        )
        self.__arduino_online_searchpath.set_on(True)

        # * Local searchpath items
        # $ Embeetle local searchpath
        self.__embeetle_local_searchpath: Optional[
            _check_linebox_.CheckLineBox
        ] = None
        if data.is_home:
            self.__embeetle_local_searchpath = _check_linebox_.CheckLineBox(
                None
            )
            if self.__embeetle_local_searchpath is not None:
                txt = _json_cruncher_.LibManager().get_potential_libcollection_folder(
                    "dot_embeetle"
                )
                if isinstance(txt, str):
                    self.__embeetle_local_searchpath.set_text(txt)
                self.__embeetle_local_searchpath.set_on(True)

        # $ Arduino sketchbook searchpath
        self.__arduino_sketchbook_searchpath: _check_linebox_.CheckLineBox = (
            _check_linebox_.CheckLineBox(None)
        )
        if self.__arduino_sketchbook_searchpath is not None:
            txt = (
                _json_cruncher_.LibManager().get_potential_libcollection_folder(
                    "arduino_sketchbook"
                )
            )
            if isinstance(txt, str):
                self.__arduino_sketchbook_searchpath.set_text(txt)
            self.__arduino_sketchbook_searchpath.set_on(True)

        # $ Arduino15 searchpath [Optional]
        self.__arduino15_searchpath: List[_check_linebox_.CheckLineBox] = []
        arduino15_libcollection_list = (
            _json_cruncher_.LibManager().get_potential_libcollection_folder(
                "arduino15"
            )
        )
        if (arduino15_libcollection_list is not None) and isinstance(
            arduino15_libcollection_list, tuple
        ):
            for arduino15_libcollection in arduino15_libcollection_list:
                assert isinstance(arduino15_libcollection, str)
                if os.path.isdir(arduino15_libcollection):
                    self.__arduino15_searchpath.append(
                        _check_linebox_.CheckLineBox(None)
                    )
                    self.__arduino15_searchpath[-1].set_text(
                        arduino15_libcollection
                    )
                    self.__arduino15_searchpath[-1].set_on(False)

        # $ Arduino installdir searchpath [Optional]
        self.__arduino_installdir_searchpath: List[
            _check_linebox_.CheckLineBox
        ] = []
        arduino_installdir_libcollection_list = (
            _json_cruncher_.LibManager().get_potential_libcollection_folder(
                "arduino_installation"
            )
        )
        if (arduino_installdir_libcollection_list is not None) and isinstance(
            arduino_installdir_libcollection_list, tuple
        ):
            for (
                arduino_installdir_libcollection
            ) in arduino_installdir_libcollection_list:
                assert isinstance(arduino_installdir_libcollection, str)
                if os.path.isdir(arduino_installdir_libcollection):
                    self.__arduino_installdir_searchpath.append(
                        _check_linebox_.CheckLineBox(None)
                    )
                    self.__arduino_installdir_searchpath[-1].set_text(
                        arduino_installdir_libcollection
                    )
                    self.__arduino_installdir_searchpath[-1].set_on(True)

        # * Group searchpaths together
        if self.__arduino_installdir_searchpath is None:
            self.__arduino_installdir_searchpath = []
        if self.__arduino15_searchpath is None:
            self.__arduino15_searchpath = []
        self.__searchpath_boxes: List[_check_linebox_.CheckLineBox] = [
            self.__embeetle_online_searchpath,
            self.__arduino_online_searchpath,
            self.__embeetle_local_searchpath,
            self.__arduino_sketchbook_searchpath,
            *self.__arduino_installdir_searchpath,
            *self.__arduino15_searchpath,
        ]

        # * Apply basic stuff
        for n, searchpath in enumerate(self.__searchpath_boxes):
            if searchpath is None:
                continue
            searchpath.get_lineedit().setReadOnly(True)
            searchpath.btn_clicked_sig.connect(lambda k=n: self.line_clicked(k))
            searchpath.lineedit_clicked_sig.connect(
                lambda k=n: self.line_clicked(k)
            )
            self.__scroll_lyt.addWidget(searchpath)
            continue
        return

    def line_clicked(self, n: int) -> None:
        """
        The user clicked one of the searchpath lines - either the line itself or the checkbox.
        """
        if n == 0:
            gui.dialogs.popupdialog.PopupDialog.ok(
                title_text="Embeetle online libraries",
                text="""
                <p>
                    Right now, Embeetle has no online collection of libraries.<br>
                    If you have libraries you'd like to share, please contact<br>
                    us.
                </p>
                """,
                icon_path="icons/logo/beetle_face.png",
            )
            return
        self.__searchpath_boxes[n].toggle()
        self.line_toggled_sig.emit()
        return

    def get_lines(self) -> List[Tuple[str, bool]]:
        """Return all the lines and their check state."""
        lines = []
        for n, searchpath in enumerate(self.__searchpath_boxes):
            if searchpath is None:
                continue
            text = searchpath.get_text()
            p = re.compile(r"\[.*?\]|<.*?>")
            newtext = p.sub("", text)
            newtext = newtext.strip()
            lines.append((newtext, searchpath.is_on()))
        return lines

    def self_destruct(
        self,
        death_already_checked: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill SearchPathsGroupBox() twice!"
                )
            self.dead = True

        # $ Disconnect signals
        try:
            self.line_toggled_sig.disconnect()
        except:
            pass

        # $ Empty scroll layout
        for searchpath in self.__searchpath_boxes:
            if searchpath is None:
                continue
            # Remove child widget from layout
            self.__scroll_lyt.removeWidget(searchpath)
            # Kill and deparent
            searchpath.self_destruct()
            continue
        functions.clean_layout(self.__scroll_lyt)

        # $ Scroll area
        self.__scroll_frm.setParent(None)  # noqa
        self.layout().removeWidget(self.__scroll_area)
        self.__scroll_area.setParent(None)  # noqa

        # $ Kill leftovers
        functions.clean_layout(self.layout())

        # $ Reset variables
        self.__scroll_lyt = None
        self.__scroll_frm = None
        self.__scroll_area = None
        self.__embeetle_online_searchpath = None
        self.__arduino_online_searchpath = None
        self.__embeetle_local_searchpath = None
        self.__arduino_sketchbook_searchpath = None
        self.__arduino15_searchpath = None
        self.__arduino_installdir_searchpath = None
        self.__searchpath_boxes = None

        # $ Deparent oneself
        gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton.self_destruct(
            self, death_already_checked=True
        )
        return
