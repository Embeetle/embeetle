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
import qt, data, functions, functools
import helpdocs.help_texts as _ht_
import dashboard.items.item as _da_
import project.segments.board_seg.board as _board_
import hardware_api.hardware_api as _hardware_api_
import hardware_api.board_unicum as _board_unicum_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_dropdown as _cm_dropdown_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import dashboard.contextmenus.board_contextmenu as _board_contextmenu_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

# ^                                        BOARD ROOT ITEM                                         ^#
# % ============================================================================================== %#
# % BoardRootItem()                                                                                %#
# %                                                                                                %#


class BoardRootItem(_da_.Root):
    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: BoardRootItem) -> None:
            super().__init__(item=item)
            self.closedIconpath = "icons/board/custom_board.png"
            self.openIconpath = "icons/board/custom_board.png"
            self.lblTxt = "Board "
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION:
            Used to run only if self.get_item()._v_layout is not None, but now it runs always!
            """
            item: BoardRootItem = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return
            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            # * Sync self
            board: _board_.Board = item.get_projSegment()
            if self.has_asterisk():
                self.lblTxt = "*Board"
            else:
                self.lblTxt = "Board "
            self.closedIconpath = board.get_board_dict()["icon"]
            self.openIconpath = board.get_board_dict()["icon"]

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(self, board: _board_.Board) -> None:
        """"""
        super().__init__(
            projSegment=board,
            name="board",
            state=BoardRootItem.Status(item=self),
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
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QMouseEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _toplvl_contextmenu_.ToplvlContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)
        board: _board_.Board = self.get_projSegment()

        def _help(_key):
            _ht_.board_help(board)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                       BOARD DEVICE ITEM                                        ^#
# % ============================================================================================== %#
# % BoardDeviceItem()                                                                              %#
# %                                                                                                %#


class BoardDeviceItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: BoardDeviceItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/chip/chip.png"
            self.openIconpath = "icons/chip/chip.png"
            self.lblTxt = "Device ".ljust(8)
            return

        def __get_dropdown_elements(
            self,
            board: _board_.Board,
            callback: Callable,
        ) -> None:
            """> callback(dropdown_elements, dropdown_selection)"""
            # * Figure out current selection
            dropdown_selection: Optional[str] = None
            if (
                (board.get_name() is None)
                or (board.get_board_unicum() is None)
                or (board.get_board_unicum().get_name() is None)
                or (board.get_board_unicum().get_name().lower() == "none")
            ):
                dropdown_selection = "none"
            elif (board.get_name().lower() == "custom") or (
                board.get_board_unicum().get_name().lower() == "custom"
            ):
                dropdown_selection = "custom"
            else:
                mf = board.get_board_dict()["manufacturer"]
                dropdown_selection = str(
                    f"{mf}/" f"{board.get_board_unicum().get_name()}"
                )

            # * Fill dropdown elements
            dropdown_elements: List[Dict] = []
            text_color = "default"
            for mf in _hardware_api_.HardwareDB().list_manufacturers(
                for_boards=True
            ):
                iconpath = _hardware_api_.HardwareDB().get_manufacturer_dict(
                    mf
                )["icon"]
                dropdown_elements.append(
                    {
                        "name": mf,
                        "widgets": [
                            {
                                "type": "image",
                                "icon-path": iconpath,
                            },
                            {
                                "type": "text",
                                "text": mf,
                                "color": text_color,
                            },
                        ],
                    }
                )
                subitems = []
                for board_unicum in _hardware_api_.HardwareDB().list_boards(
                    boardmf_list=[
                        mf,
                    ],
                    return_unicums=True,
                ):
                    assert isinstance(board_unicum, _board_unicum_.BOARD)
                    subitems.append(
                        {
                            "name": f"{mf}/{board_unicum.get_name()}",
                            "widgets": [
                                {
                                    "type": "image",
                                    "icon-path": board_unicum.get_board_dict()[
                                        "icon"
                                    ],
                                },
                                {
                                    "type": "text",
                                    "text": board_unicum.get_name(),
                                    "color": text_color,
                                },
                            ],
                        }
                    )
                if len(subitems) > 0:
                    dropdown_elements[-1]["subitems"] = subitems
                continue

            # * Add 'custom' element
            dropdown_elements.append(
                {
                    "name": "custom",
                    "widgets": [
                        {
                            "type": "image",
                            "icon-path": (
                                _board_unicum_.BOARD("custom").get_board_dict()[
                                    "icon"
                                ]
                            ),
                        },
                        {
                            "type": "text",
                            "text": "custom",
                            "color": text_color,
                        },
                    ],
                }
            )

            # * Finish
            callback(dropdown_elements, dropdown_selection)
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION:
            Used to run only if self.get_item()._v_layout is not None, but now it runs always!
            """
            item = self.get_item()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
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

            def finish(
                dropdown_elements: List[Dict[str, Any]],
                dropdown_selection: str,
            ) -> None:
                "Finish this function with a dropdown"
                self.dropdownElements = dropdown_elements
                self.dropdownSelection = dropdown_selection
                if refreshlock:
                    item.release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            # * Sync self
            board: _board_.Board = item.get_projSegment()
            self.set_asterisk(board.get_state("DEVICE", "asterisk"))
            if self.has_asterisk():
                self.lblTxt = "*Board".ljust(8)
            else:
                self.lblTxt = "Board ".ljust(8)
            self.closedIconpath = board.get_board_dict()["icon"]
            self.openIconpath = board.get_board_dict()["icon"]
            self.set_error(board.get_state("DEVICE", "error"))
            self.set_warning(board.get_state("DEVICE", "warning"))
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            self.__get_dropdown_elements(
                board=board,
                callback=finish,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        board: _board_.Board,
        rootdir: Optional[BoardRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """"""
        super().__init__(
            projSegment=board,
            rootdir=rootdir,
            parent=parent,
            name="device",
            state=BoardDeviceItem.Status(item=self),
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

        # $ With dropdown
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemDropdown=_cm_dropdown_.ItemDropdown(owner=self),
        )
        dropdown: _cm_dropdown_.ItemDropdown = self.get_widget("itemDropdown")
        dropdown.selection_changed_from_to.connect(
            self.selection_changed_from_to,
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def selection_changed_from_to(
        self,
        from_boardname: str,
        to_boardname: str,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_boardname: Original board name
        :param to_boardname: New board name
        """
        # * Sanitize input
        if (from_boardname is None) or (from_boardname.lower() == "none"):
            from_boardname = "none"
        if (to_boardname is None) or (to_boardname.lower() == "none"):
            to_boardname = "none"
        if from_boardname.lower() == "custom":
            from_boardname = "custom"
        if to_boardname.lower() == "custom":
            to_boardname = "custom"
        old_boardname = from_boardname.split("/")[-1]
        new_boardname = to_boardname.split("/")[-1]
        if old_boardname == new_boardname:
            return

        # * Apply new board
        new_board_unicum = _board_unicum_.BOARD(new_boardname)
        if new_board_unicum is None:
            return
        board: _board_.Board = self.get_projSegment()
        board.change_board(
            board_unicum=new_board_unicum,
            callback=None,
            callbackArg=None,
        )
        return

    def show_contextmenu_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _board_contextmenu_.BoardDeviceContextMenu(
            widg=itemBtn,
            item=self,
            toplvl_key="itemBtn",
            clickfunc=self.contextmenuclick_itemBtn,
        )
        _contextmenu_launcher_.ContextMenuLauncher().launch_contextmenu(
            contextmenu=contextmenu,
            point=functions.get_position(event),
            callback=None,
            callbackArg=None,
        )
        return

    def contextmenuclick_itemBtn(self, key: str, *args) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        board: _board_.Board = cast(_board_.Board, self.get_projSegment())
        if not board.is_fake():
            super().contextmenuclick_itemBtn(key)

        def link(_key: str) -> None:
            board_link = board.get_board_dict()["link"]
            if board_link is not None:
                functions.open_url(board_link)
            return

        def _help(_key: str) -> None:
            _ht_.board_help(board)
            return

        funcs = {
            "link": link,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return
