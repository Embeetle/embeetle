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
import functools, gc, threading, traceback, sys
import qt, data, purefunctions, functions
import gui.templates.paintedgroupbox
import gui.stylesheets.scrollbar as _scrollbar_style_
import wizards.lib_wizard.cell_widgets.cell_header as _cell_header_
import wizards.lib_wizard.cell_widgets.cell_name as _cell_name_
import wizards.lib_wizard.cell_widgets.cell_author as _cell_author_
import wizards.lib_wizard.cell_widgets.cell_version as _cell_version_
import wizards.lib_wizard.cell_widgets.cell_architecture as _cell_architecture_
import wizards.lib_wizard.cell_widgets.cell_origin as _cell_download_
import wizards.lib_wizard.cell_widgets.cell_sentence as _cell_sentence_
import wizards.lib_wizard.cell_widgets.cell_paragraph as _cell_paragraph_
import wizards.lib_wizard.lib_const as _lib_const_
import wizards.lib_wizard.cell_widgets.cell_widget as _cell_widget_

if TYPE_CHECKING:
    import wizards.lib_wizard.gen_widgets.progbar as _progbar_
    import libmanager.libobj as _libobj_
from various.kristofstuff import *


class LibTableGroupBox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):
    """GROUPBOX holding the LibTable() widget."""

    change_final_btn_sig = qt.pyqtSignal(int)

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(
            parent=parent,
            name="libraries",
            text="Libraries:",
            info_func=lambda *args: print("info clicked!"),
            h_size_policy=qt.QSizePolicy.Policy.Ignored,
            v_size_policy=qt.QSizePolicy.Policy.Ignored,
        )
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Ignored,
            qt.QSizePolicy.Policy.Ignored,
        )
        self.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(20)

        # * LibTable() widget
        self.__libtable = LibTable(parent=self)
        self.layout().addWidget(self.__libtable)
        self.__libtable._set_headers(
            (
                "Name",
                "Author",
                "Version",
                "Architectures",
                "Origin",
                "Summary",
                "Info",
            )
        )
        self.__libtable.change_final_btn_sig.connect(self.change_final_btn_sig)
        self.layout().addWidget(self.__libtable)
        return

    def get_libtable(self) -> LibTable:
        """"""
        return self.__libtable

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
                raise RuntimeError(f"Trying to kill LibTableGroupBox() twice!")
            self.dead = True

        try:
            self.change_final_btn_sig.disconnect()
        except:
            pass

        def finish(*args) -> None:
            print("LibTableGroupBox().self_destruct().finish()")
            self.layout().removeWidget(self.__libtable)
            # functions.clean_layout(self.layout()) <= should happen in method below:
            gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton.self_destruct(
                self,
                death_already_checked=True,
            )
            self.__libtable = None
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        print("LibTableGroupBox().self_destruct().start()")
        self.__libtable.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return


class LibTable(qt.QFrame):
    """┌── self, self.__lyt
    ──────────────────────────────────────────────────────┐ │ │ │┌────
    self.__hscroll_area/frm/lyt ──────────────────────────────┐ │ ││ ┌────
    self.__header_frm/lyt ──────────────────────────────┐   │  ██
    self.__vscrollbar ││ │ │   │  ██     │  (coupled to the scroll area) ││ │ │
    │  ██     │ ││ └─────────────────────────────────────────────────────────┘
    │  ██     │ ││ ┌──── self.__vscroll_area/frm/gridlyt ────────────────────┐
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ │                                                         │
    │  ░░     │ ││ └─────────────────────────────────────────────────────────┘
    │  ░░     │
    ││██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ░░     │
    │└───────────────────────────────────────────────────────────────┘         │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    want_more_data = qt.pyqtSignal(object, object)
    change_final_btn_sig = qt.pyqtSignal(int)

    def __init__(self, parent: qt.QWidget) -> None:
        """"""
        super().__init__(parent=parent)
        self.__dead = False

        # $ Mutexes
        self._cleaning_rows_mutex = threading.Lock()

        # $ Outer encapsulation
        # > contains: horizontal scroll area
        # > contains: vertical scrollbar
        self.__lyt = qt.QHBoxLayout(self)
        self.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.MinimumExpanding,
        )

        # $ Horizontal scroll area
        # > contains: header
        # > contains: vertical scroll area
        self.__hscroll_area = HScrollArea(self)
        self.__hscroll_frm = qt.QFrame()
        self.__hscroll_lyt = qt.QVBoxLayout(self.__hscroll_frm)
        # header
        self.__header_frm = qt.QFrame()
        self.__header_lyt = qt.QHBoxLayout(self.__header_frm)
        self.__header_lyt.setContentsMargins(0, 0, 0, 0)
        self.__header_lyt.setSpacing(0)
        self.__header_lyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__header_widgs: List[_cell_header_.HeaderLabel] = []
        self.__min_widths: List[int] = []

        # $ Vertical scroll area
        # > contains: gridlayout
        self.__vscroll_area: VScrollArea = VScrollArea(self)
        self.__vscroll_frm: Optional[qt.QFrame] = None
        self.__vscroll_gridlyt: Optional[qt.QGridLayout] = None
        self.__vscroll_ignore: bool = False
        self.__end_row_added: bool = False

        # $ Vertical scrollbar
        self.__vscrollbar = self.__vscroll_area.verticalScrollBar()
        self.__vscroll_area.verticalScrollBar().valueChanged.connect(  # type: ignore
            self.check_vertical_scrollbar
        )

        def init_hscroll(*args) -> None:
            self.__hscroll_frm.setStyleSheet(
                f"""
                QFrame {{
                    background: #00ffffff;
                    border: 1px solid {_lib_const_.CELL_FRAME_COL};
                    padding: 0px;
                    margin: 0px;
                }}
            """
            )
            self.__hscroll_lyt.setSpacing(0)
            self.__hscroll_lyt.setContentsMargins(0, 0, 0, 0)
            self.__hscroll_area.setWidget(self.__hscroll_frm)
            return

        def init_self(*args) -> None:
            self.setStyleSheet(
                """
                QFrame {
                    background: #00ffffff;
                    border: 0px solid #00ffffff;
                    padding: 0px;
                    margin: 0px;
                }
            """
            )
            self.__lyt.setSpacing(0)
            self.__lyt.setContentsMargins(0, 0, 0, 0)
            self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
            return

        init_hscroll()
        init_self()
        self.__lyt.addWidget(self.__hscroll_area)
        self.__lyt.addWidget(self.__vscrollbar)
        # self.__vscrollbar.valueChanged.connect(lambda v: print(f'moved: {v}'))
        self.__hscroll_lyt.addWidget(self.__header_frm)
        self.__hscroll_lyt.addWidget(self.__vscroll_area)
        return

    @qt.pyqtSlot(int)
    def check_vertical_scrollbar(self, value: int) -> None:
        """This slot is connected to the vertical scrollbar's 'valueChanged'
        signal, to check if ver-

        tical scrollbar is near the bottom and new data is required. If so, the 'want_more_data'
        signal gets emitted to trigger the LibManager() in providing more data - see the 'give_more
        _data()' method from the LibManager().

        PROTECTION MECHANISMS
        1. The LibManager() protects its 'give_more_data()' method with a mutex, such that only one
           invocation can run at any time.
        2. The 'self.__vscroll_ignore' flag is used to ignore the scrollbar for a while. It is set
           at the start of adding new rows and cleared again when finished. It's also set at the
           start of a clean() process.
        """
        if self.__vscroll_ignore:
            return
        if value >= self.__vscroll_area.verticalScrollBar().maximum() - 5:
            self.__vscroll_ignore = True
            self.want_more_data.emit(None, None)
        return

    def __reset_vscroll_frm(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Reset and initialize the 'self.__vscroll_frm'."""

        def finish(*args) -> None:
            assert self.__vscroll_frm is None
            assert self.__vscroll_gridlyt is None
            # $ Create frame
            self.__vscroll_frm = qt.QFrame(None)
            self.__vscroll_frm.setStyleSheet(
                """
                QFrame {
                    background: #00ffffff;
                    border: 0px solid #00ffffff;
                    padding: 0px;
                    margin: 0px;
                }
            """
            )
            # $ Create gridlayout
            self.__vscroll_gridlyt = qt.QGridLayout(self.__vscroll_frm)
            self.__vscroll_gridlyt.setSpacing(0)
            self.__vscroll_gridlyt.setContentsMargins(0, 0, 0, 0)
            self.__vscroll_gridlyt.setColumnStretch(0, 2)  # Name
            self.__vscroll_gridlyt.setColumnStretch(1, 2)  # Author
            self.__vscroll_gridlyt.setColumnStretch(2, 2)  # Version
            self.__vscroll_gridlyt.setColumnStretch(3, 1)  # Origin
            self.__vscroll_gridlyt.setColumnStretch(5, 3)  # Sentence
            self.__vscroll_gridlyt.setColumnStretch(6, 4)  # Paragraph
            # $ Assign frame to scroll area
            self.__vscroll_area.setWidget(self.__vscroll_frm)
            self.__end_row_added = False
            callback(callbackArg)
            return

        if self.__vscroll_frm is not None:
            # Make sure the frame is already cleaned
            assert self.__vscroll_gridlyt.count() == 0
            self.__vscroll_gridlyt.deleteLater()
            self.__vscroll_frm.setParent(None)  # noqa
            self.__vscroll_frm.deleteLater()
            qt.sip.delete(self.__vscroll_gridlyt)
            qt.sip.delete(self.__vscroll_frm)
            self.__vscroll_gridlyt = None
            self.__vscroll_frm = None
            gc.collect()
            qt.QTimer.singleShot(100, finish)
            return
        qt.QTimer.singleShot(10, finish)
        return

    def _set_headers(self, headers: Iterable[str]) -> None:
        """"""
        for n, header in enumerate(headers):
            header_widg = _cell_header_.HeaderLabel(
                parent=self,
                text=header,
            )
            self.__header_widgs.append(header_widg)
            self.__header_lyt.addWidget(header_widg)
            self.__min_widths.append(header_widg.sizeHint().width())
            continue
        return

    def start_adding_rows(self) -> None:
        """Function to be called before adding rows."""
        self.__vscroll_ignore = True
        self.__vscroll_area.verticalScrollBar().setTracking(False)
        self.__hscroll_area.horizontalScrollBar().setTracking(False)
        # self.__vscroll_area.setWidgetResizable(False)
        # self.__hscroll_area.setWidgetResizable(False)
        return

    def finish_adding_rows(self) -> None:
        """Function to be called after adding rows or upon a 'resizeEvent()'
        from the LibraryManager()."""

        def resize(loop: int, *args) -> None:
            if self.__vscroll_frm is not None:
                # Note: seems like rows start counting from 1, columns from 0.
                widgs = [
                    self.__vscroll_gridlyt.itemAtPosition(1, i)
                    for i in range(_lib_const_.NR_OF_COLUMNS)
                ]
                for i, widg in enumerate(widgs):
                    if widg is None:
                        purefunctions.printc(
                            f"WARNING: Cannot size header col = {i}",
                            color="warning",
                        )
                        continue
                    if isinstance(widg.widget(), _cell_widget_.CellWidget):
                        # OK
                        w1 = widg.widget().size().width()
                        w2 = widg.widget().sizeHint().width()
                        w = max(w1, w2)
                        if w == 0:
                            purefunctions.printc(
                                f"WARNING: Widget {widg.widget()} has width 0!",
                                color="warning",
                            )
                            pass
                        else:
                            self.__header_widgs[i].setFixedWidth(w)
                    continue
                # Wait a bit until switching on the scrollbar tracking. Otherwise,
                # Resize action can trigger the scrollbar 'valueChanged' signal!
            if loop < 2:
                qt.QTimer.singleShot(
                    100,
                    functools.partial(
                        resize,
                        loop + 1,
                    ),
                )
                return
            qt.QTimer.singleShot(10, finish)
            return

        def finish(*args) -> None:
            if self.__vscroll_frm is not None:
                self.__vscroll_area.verticalScrollBar().setTracking(True)
                self.__hscroll_area.horizontalScrollBar().setTracking(True)
                self.__vscroll_ignore = False
            return

        self.__vscroll_area.setWidgetResizable(True)
        self.__hscroll_area.setWidgetResizable(True)
        qt.QTimer.singleShot(100, functools.partial(resize, 0))
        return

    def add_row(
        self,
        libobj: _libobj_.LibObj,
        versionlist: Optional[List[str]],
    ) -> None:
        """Add one row to the library table.

        This method is called from the LibManager() its give_more _data()
        method. It pushes around 100 new rows in bursts of 10.
        """
        # Define maximal cell widths. Warning: they are not forcibly imposed, but only applied on
        # the sizeHint() return value!
        MAX_SMALL_CELL_WIDTH = data.get_general_font_width() * 20
        MAX_BIG_CELL_WIDTH = data.get_general_font_width() * 50
        # Determine ROW
        # Note: even at the very start, the value is 1.
        ROW: int = self.__vscroll_gridlyt.rowCount()
        # * 0. Name
        COL: int = 0
        name_item = _cell_name_.NameFrm(
            row=ROW,
            col=COL,
            libobj=libobj,
            gridlyt=self.__vscroll_gridlyt,
            parent=self.__vscroll_frm,
            minwidth=self.__min_widths[COL],
            maxwidth=MAX_SMALL_CELL_WIDTH,
        )
        name_item.row_checked_sig.connect(self.__check_row_request)
        name_item.row_cleared_sig.connect(self.__clear_row_request)
        self.__vscroll_gridlyt.addWidget(
            name_item,
            ROW,
            COL,
        )

        # * 1. Author
        COL = 1
        author_item = _cell_author_.AuthorLabel(
            row=ROW,
            col=COL,
            libobj=libobj,
            gridlyt=self.__vscroll_gridlyt,
            parent=self.__vscroll_frm,
            minwidth=self.__min_widths[COL],
            maxwidth=MAX_SMALL_CELL_WIDTH,
        )
        self.__vscroll_gridlyt.addWidget(
            author_item,
            ROW,
            COL,
        )

        # * 2. Version
        COL = 2
        version_item: Union[
            _cell_version_.ComboBoxVersionFrm, _cell_version_.VersionLabel, None
        ]
        if libobj.get_origin() == "zip_url":
            version_item = _cell_version_.ComboBoxVersionFrm(
                row=ROW,
                col=COL,
                libobj=libobj,
                versionlist=versionlist,
                gridlyt=self.__vscroll_gridlyt,
                parent=self.__vscroll_frm,
                minwidth=self.__min_widths[COL],
                maxwidth=MAX_SMALL_CELL_WIDTH,
            )
            self.__vscroll_gridlyt.addWidget(
                cast(_cell_version_.ComboBoxVersionFrm, version_item),
                ROW,
                COL,
            )
        else:
            assert versionlist is None
            version_item = _cell_version_.VersionLabel(
                row=ROW,
                col=COL,
                libobj=libobj,
                gridlyt=self.__vscroll_gridlyt,
                parent=self.__vscroll_frm,
                minwidth=self.__min_widths[COL],
                maxwidth=MAX_SMALL_CELL_WIDTH,
            )
            self.__vscroll_gridlyt.addWidget(
                cast(_cell_version_.VersionLabel, version_item),
                ROW,
                COL,
            )

        # * 3. Architecture
        COL = 3
        architecture_item = _cell_architecture_.ArchitectureLabel(
            row=ROW,
            col=COL,
            libobj=libobj,
            gridlyt=self.__vscroll_gridlyt,
            parent=self.__vscroll_frm,
            minwidth=self.__min_widths[COL],
            maxwidth=MAX_SMALL_CELL_WIDTH,
        )
        self.__vscroll_gridlyt.addWidget(
            architecture_item,
            ROW,
            COL,
        )

        # * 4. Origin
        COL = 4
        download_item = _cell_download_.OriginButton(
            row=ROW,
            col=COL,
            libobj=libobj,
            gridlyt=self.__vscroll_gridlyt,
            parent=self.__vscroll_frm,
            minwidth=self.__min_widths[COL],
            maxwidth=MAX_SMALL_CELL_WIDTH,
        )
        self.__vscroll_gridlyt.addWidget(
            download_item,
            ROW,
            COL,
        )

        # * 5. Sentence
        COL = 5
        sentence_item = _cell_sentence_.SentenceLabel(
            row=ROW,
            col=COL,
            libobj=libobj,
            gridlyt=self.__vscroll_gridlyt,
            parent=self.__vscroll_frm,
            minwidth=self.__min_widths[COL],
            maxwidth=MAX_SMALL_CELL_WIDTH,
        )
        self.__vscroll_gridlyt.addWidget(
            sentence_item,
            ROW,
            COL,
        )

        # * 6. Paragraph
        COL = 6
        paragraph_item = _cell_paragraph_.ParagraphLabel(
            row=ROW,
            col=COL,
            libobj=libobj,
            gridlyt=self.__vscroll_gridlyt,
            parent=self.__vscroll_frm,
            minwidth=self.__min_widths[COL],
            maxwidth=MAX_BIG_CELL_WIDTH,
        )
        self.__vscroll_gridlyt.addWidget(
            paragraph_item,
            ROW,
            COL,
        )
        return

    def add_end_row(self) -> None:
        """"""
        if self.__end_row_added:
            print("END ROW ALREADY ADDED")
            return
        self.__end_row_added = True
        ROW: int = self.__vscroll_gridlyt.rowCount()
        print(f"ADD END ROW {ROW}")
        final_row_widget = qt.QFrame()
        final_row_widget.setStyleSheet(
            """
            QFrame {
                background: #eeeeec;
                padding: 0px;
                margin: 0px;
            }
        """
        )
        final_row_widget.setMinimumHeight(100)
        self.__vscroll_gridlyt.addWidget(
            final_row_widget,
            ROW,
            0,
            1,
            -1,
        )
        return

    def get_checked_libobjs(self) -> Dict[int, _libobj_.LibObj]:
        """Iterate over all rows and list all checked LibObj()s.

        WARNING: While adding rows or cleaning them, this function is unstable. Always put it in a
        try-except block!
        """
        result_dict = {}
        for r in range(1, self.__vscroll_gridlyt.rowCount()):
            name_item = self.__vscroll_gridlyt.itemAtPosition(r, 0)
            if name_item is None:
                purefunctions.printc(
                    f"WARNING: Found None item at ({r},{0})",
                    color="warning",
                )
                continue
            name_widg = name_item.widget()
            if not isinstance(name_widg, _cell_name_.NameFrm):
                # This is the QFrame() inserted at the
                # end of the gridlayout.
                continue
            if name_widg.is_checked():
                libobj = name_widg.get_libobj()
                result_dict[r] = libobj
        return result_dict

    def __count_selected_rows(self) -> int:
        """Iterate over all rows and count how many are checked."""
        count = 0
        for r in range(1, self.__vscroll_gridlyt.rowCount()):
            name_item = self.__vscroll_gridlyt.itemAtPosition(r, 0)
            if name_item is None:
                purefunctions.printc(
                    f"WARNING: Found None item at ({r},{0})",
                    color="warning",
                )
                continue
            name_widg = name_item.widget()
            if not isinstance(name_widg, _cell_name_.NameFrm):
                # This is the QFrame() inserted at the
                # end of the gridlayout.
                continue
            if name_widg.is_checked():
                count += 1
        return count

    def __unselect_libs_with_same_name(
        self, libname: str, checked_libobjs: Dict[int, _libobj_.LibObj]
    ) -> bool:
        """Iterate over all rows to see if one of them has the same libname and
        is already checked. If so, uncheck that one.

        :param libname: Library name to compare to.
        :param checked_libobjs: List of checked LibObj()s, results from
            self.get_checked_libobjs().
        """
        _libname_ = libname.lower().replace(" ", "_")
        for r, libobj in checked_libobjs.items():
            if libobj.get_name().lower().replace(" ", "_") == _libname_:
                name_item = self.__vscroll_gridlyt.itemAtPosition(r, 0)
                name_widg = cast(_cell_name_.NameFrm, name_item.widget())
                name_widg.clear()
                return True
        return False

    def unselect_all_checked_rows(self, checked_rows: List[int]) -> None:
        """Unselect all libraries.

        This function is called at the end, after downloading and/or copying the
        selected libraries.
        """
        for r in checked_rows:
            if r is None:
                continue
            if r < 0:
                continue
            name_item = self.__vscroll_gridlyt.itemAtPosition(r, 0)
            name_widg = cast(_cell_name_.NameFrm, name_item.widget())
            name_widg.clear(just_downloaded=True)
            continue
        return

    @qt.pyqtSlot(int, str)
    def __check_row_request(self, row, libname, *args) -> None:
        """A request to check the given row has been fired by a NameFrm() widget
        (the first widget in each row that contains the name label and
        checkbox).

        First inspect the other rows to figure out if one of them needs to be unchecked (to avoid
        duplicate libnames). Then fulfill the request.

        Also recompute the nr to be shown in the final button:
        'ADD n LIBS TO PROJECT'
        Fire the 'change_final_btn_sig' to let it take effect.
        """
        try:
            checked_libobjs: Dict[int, _libobj_.LibObj] = (
                self.get_checked_libobjs()
            )
        except Exception as e:
            purefunctions.printc(
                "WARNING: get_checked_libobjs() failed, click ignored.",
                color="warning",
            )
            traceback.print_exc()
            print("")
            return
        n = len(checked_libobjs)
        if self.__unselect_libs_with_same_name(
            libname=libname,
            checked_libobjs=checked_libobjs,
        ):
            # One of the other rows has been cleared.
            n -= 1
        name_item = self.__vscroll_gridlyt.itemAtPosition(row, 0)
        name_widg = cast(_cell_name_.NameFrm, name_item.widget())
        name_widg.check()
        n += 1
        self.change_final_btn_sig.emit(n)
        return

    @qt.pyqtSlot(int, str)
    def __clear_row_request(self, row, libname, *args) -> None:
        """A request to clear the given row has been fired by a NameFrm() widget
        (the first widget in each row that contains the name label and
        checkbox).

        Just fulfill the request (no need to inspect other rows).

        Also recompute the nr to be shown in the final button:
        'ADD n LIBS TO PROJECT'
        Fire the 'change_final_btn_sig' to let it take effect.
        """
        name_item = self.__vscroll_gridlyt.itemAtPosition(row, 0)
        name_widg = cast(_cell_name_.NameFrm, name_item.widget())
        name_widg.clear()
        try:
            n = self.__count_selected_rows()
        except Exception as e:
            purefunctions.printc(
                "\nWARNING: Row inspection failed, click ignored.\n",
                color="warning",
            )
            traceback.print_exc()
            print("")
            return
        self.change_final_btn_sig.emit(n)
        return

    def clean(
        self,
        progbar: Optional[_progbar_.TableProgbar],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        Delete all widgets from this library table: remove all widgets and sublayouts from the
        self.__vscroll_gridlyt.

        General rule: cleanup a layout BEFORE you detach it from its parental layout!

        MUTEX:
        ======
        This function is protected with the '_cleaning_rows_mutex' such that it can't run twice
        simultaneously.
        WARNING: This protection doesn't consider the '_adding_rows_mutex' from the json cruncher!
        External protection for that must be built into the call invocation!
        """
        BURST_LEN = 100
        if not self._cleaning_rows_mutex.acquire(blocking=False):
            purefunctions.printc(
                "ERROR: Attempt to clean table rows twice simultaneously!",
                color="error",
            )
            return

        def kill_next(arg) -> None:
            i, items_to_be_killed_iter = arg
            try:
                item = next(items_to_be_killed_iter)
            except StopIteration:
                # All CellWidget() instances are dead.
                reset_vscroll()
                return
            lyt = item.layout()
            widg = item.widget()
            assert (lyt is None) != (widg is None)
            if lyt is not None:
                # This should normally not happen, as every item
                # in the gridlayout should be a QWidget()!
                raise NotImplementedError(
                    f"\nERROR: Layout detected inside QGridLayout(): "
                    f"{lyt}\n"
                )
            assert lyt is None
            if widg is None:
                purefunctions.printc(
                    f"WARNING: Widget {q}None{q} detected inside QGridLayout()",
                    color="warning",
                )
                kill_next((i, items_to_be_killed_iter))
                return
            assert widg is not None
            if not isinstance(widg, _cell_widget_.CellWidget):
                if isinstance(widg, qt.QFrame):
                    # This is probably the QFrame inserted at the end
                    # of the table
                    widg.hide()
                    widg.setParent(None)  # noqa
                    widg.deleteLater()
                    kill_next((i, items_to_be_killed_iter))
                    return
                raise NotImplementedError(
                    f"\nERROR: Unknown widget detected inside QGridLayout(): "
                    f"{widg}\n"
                )
            # We've got the CellWidget() instance - as expected.
            i += 1
            # Once in a while, increment the progbar and delay the widget self_destruct for a few milli-
            # seconds.
            if i % BURST_LEN == 0:
                if progbar is not None:
                    progbar.inc_progbar_value()
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        widg.self_destruct,
                        kill_next,
                        (i, items_to_be_killed_iter),
                    ),
                )
                return
            widg.self_destruct(
                callback=kill_next,
                callbackArg=(i, items_to_be_killed_iter),
            )
            return

        def reset_vscroll(*args) -> None:
            # Check if the gridlayout is empty.
            if self.__vscroll_gridlyt is not None:
                if self.__vscroll_gridlyt.count() != 0:
                    purefunctions.printc(
                        f"WARNING: GridLayout wasn{q}t empty!",
                        color="warning",
                    )
                    for i in reversed(range(self.__vscroll_gridlyt.count())):
                        x = self.__vscroll_gridlyt.itemAt(i)
                        x_widg = x.widget()
                        if x_widg is not None:
                            self.__vscroll_gridlyt.removeWidget(x_widg)
                            qt.sip.delete(x_widg)
            assert (self.__vscroll_gridlyt is None) or (
                self.__vscroll_gridlyt.count() == 0
            )
            gc.collect()
            if progbar is not None:
                progbar.hide()
            # Don't switch on the scrollbar tracking yet. It would trigger a scrollbar 'valueChan-
            # ged' event! Also, don't clear the 'self.__vscroll_ignore' protection flag - 'value-
            # Changed' events must be avoided now at any cost, because they can pull in old (wrong
            # filtered) data. Note: now it wouldn't matter as much anymore, since I've moved the
            # clean action until after the json data has been reset. However, it's still best to
            # avoid unwanted 'valueChanged' events.
            pass
            # The rowCount() method from the gridlayout isn't reset properly by Qt. So it's best to
            # replace the gridlayout alltogether. Unfortunately, it's not so easy to delete an ex-
            # isting layout. Applying 'setParent(None)' on the gridlayout didn't help. Finally, I
            # decided to just shred the gridlayout and its QFrame() alltogether.
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    self.__reset_vscroll_frm,
                    finish_reset,
                    None,
                ),
            )
            return

        def finish_reset(*args) -> None:
            qt.QTimer.singleShot(10, finish)
            return

        def finish(*args) -> None:
            self._cleaning_rows_mutex.release()
            callback(callbackArg)
            return

        self.__vscroll_ignore = True
        self.__vscroll_area.verticalScrollBar().setTracking(False)
        self.__hscroll_area.horizontalScrollBar().setTracking(False)
        self.__vscroll_area.setWidgetResizable(False)
        self.__hscroll_area.setWidgetResizable(False)
        if self.__vscroll_frm is None:
            # self.__vscroll_frm is None at startup
            reset_vscroll()
            return
        if qt.sip.isdeleted(self.__vscroll_gridlyt):
            finish()
            return
        # Create an iterator yielding the items from the gridlayout in reversed order.
        _items_to_be_killed_iter = (
            self.__vscroll_gridlyt.itemAt(i)
            for i in reversed(range(self.__vscroll_gridlyt.count()))
        )
        if progbar is not None:
            progbar.show()
            progbar.set_progbar_value(0)
            progbar.set_progbar_max(
                int(self.__vscroll_gridlyt.count() / BURST_LEN)
            )
        kill_next((0, _items_to_be_killed_iter))
        return

    def is_dead(self) -> bool:
        """"""
        return self.__dead

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill LibTable() twice!")
            self.__dead = True

        # $ Disconnect signals
        for sig in (
            self.want_more_data,
            self.change_final_btn_sig,
            self.__vscroll_area.verticalScrollBar().valueChanged,
        ):
            try:
                sig.disconnect()  # type: ignore
            except:
                pass

        def _clean_layout(*args) -> None:
            functions.clean_layout((self.__lyt, finish, None))
            return

        def finish(*args) -> None:
            self.__lyt = None
            self._cleaning_rows_mutex = None
            if callback is not None:
                callback(callbackArg)
            return

        self.clean(
            progbar=None,
            callback=finish,
            callbackArg=None,
        )
        return


class HScrollArea(qt.QScrollArea):
    """
    See
    https://forum.qt.io/topic/13374/solved-qscrollarea-vertical-scroll-only/9
    """

    def __init__(self, parent: qt.QWidget) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.setVerticalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setStyleSheet(
            """
            QObject {
                background: #00ffffff;
                padding: 0px;
                margin: 0px;
            }
        """
        )
        self.horizontalScrollBar().setStyleSheet(
            _scrollbar_style_.get_horizontal()
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        return

    def eventFilter(self, o: qt.QObject, e: qt.QEvent) -> bool:
        """"""
        # This works because QScrollArea::setWidget installs an eventFilter on
        # the widget
        if (
            (o is not None)
            and (o == self.widget())
            and (e.type() == qt.QEvent.Type.Resize)
        ):
            self.setMinimumHeight(
                self.widget().minimumSizeHint().height()
                + self.verticalScrollBar().height()
            )
        return super().eventFilter(o, e)


class VScrollArea(qt.QScrollArea):
    """
    See
    https://forum.qt.io/topic/13374/solved-qscrollarea-vertical-scroll-only/9
    """

    def __init__(self, parent: qt.QWidget) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setStyleSheet(
            """
            QObject {
                background: #00ffffff;
                padding: 0px;
                margin: 0px;
            }
        """
        )
        self.verticalScrollBar().setStyleSheet(_scrollbar_style_.get_vertical())
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        return

    def eventFilter(self, o: qt.QObject, e: qt.QEvent) -> bool:
        """"""
        # This works because QScrollArea::setWidget installs an eventFilter on
        # the widget
        if (
            (o is not None)
            and (o == self.widget())
            and (e.type() == qt.QEvent.Type.Resize)
        ):
            self.setMinimumWidth(
                self.widget().minimumSizeHint().width()
                + self.verticalScrollBar().width()
            )
        return super().eventFilter(o, e)
