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
import qt, data, gui, functools, functions
import hardware_api.hardware_api as _hardware_api_
import dashboard.items.item as _da_
import project.segments.chip_seg.chip as _chip_
import hardware_api.chip_unicum as _chip_unicum_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import tree_widget.widgets.item_dropdown as _cm_dropdown_
import tree_widget.widgets.item_lineedit as _cm_lineedit_
import tree_widget.widgets.item_progbar as _cm_progbar_
import dashboard.contextmenus.toplvl_contextmenu as _toplvl_contextmenu_
import dashboard.contextmenus.chip_contextmenu as _chip_contextmenu_
import helpdocs.help_texts as _ht_
import contextmenu.contextmenu_launcher as _contextmenu_launcher_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import project.segments.board_seg.board as _board_
from various.kristofstuff import *

# ^                                         CHIP ROOT ITEM                                         ^#
# % ============================================================================================== %#
# % ChipRootItem()                                                                                 %#
# %                                                                                                %#


class ChipRootItem(_da_.Root):
    class Status(_da_.Folder.Status):
        __slots__ = ()

        def __init__(self, item: ChipRootItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/chip/chip.png"
            self.openIconpath = "icons/chip/chip.png"
            self.lblTxt = "Microcontroller "
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION: Used to run only if self.get_item()._v_layout is not None,
            but now it runs always!
            """
            item: ChipRootItem = self.get_item()
            chip: _chip_.Chip = item.get_projSegment()

            # * Start
            if item is None:
                if callback is not None:
                    callback(callbackArg)
                return

            if refreshlock:
                if not item.acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        30,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return

            if self.has_asterisk():
                self.lblTxt = "*Microcontroller"
            else:
                self.lblTxt = "Microcontroller "
            self.closedIconpath = chip.get_chip_dict(board=None)["icon"]
            self.openIconpath = chip.get_chip_dict(board=None)["icon"]
            functions.assign_icon_err_warn_suffix(itemstatus=self)

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(self, chip: _chip_.Chip) -> None:
        """"""
        super().__init__(
            projSegment=chip,
            name="chip",
            state=ChipRootItem.Status(item=self),
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

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        if len(self.get_childlist()) > 0:
            self.toggle_open()
            return
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
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
        chip: _chip_.Chip = self.get_projSegment()

        def _help(_key):
            _ht_.chip_help(chip)
            return

        funcs = {
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                        CHIP DEVICE ITEM                                        ^#
# % ============================================================================================== %#
# % ChipDeviceItem()                                                                               %#
# %                                                                                                %#


class ChipDeviceItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: ChipDeviceItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/chip/chip.png"
            self.openIconpath = "icons/chip/chip.png"
            self.lblTxt = "Device ".ljust(8)
            return

        def __get_dropdown_elements(
            self,
            chip: _chip_.Chip,
            is_fake: bool,
            callback: Callable,
        ) -> None:
            """> callback(dropdown_elements, dropdown_selection)"""
            board: Optional[_board_.Board] = None
            if is_fake:
                board = data.current_project.intro_wiz.get_fake_board()
            else:
                board = data.current_project.get_board()

            # * Figure out current selection
            dropdown_selection: Optional[str] = None
            if (
                (chip.get_name() is None)
                or (chip.get_chip_unicum() is None)
                or (chip.get_chip_unicum().get_name() is None)
                or (chip.get_chip_unicum().get_name().lower() == "none")
            ):
                dropdown_selection = "NONE"
            else:
                dropdown_selection = str(
                    f'{chip.get_chip_dict(board=None)["manufacturer"]}/'
                    f"{chip.get_chip_unicum().get_name()}"
                )
            # * Fill dropdown elements
            dropdown_elements: List[Dict] = []
            default_color = "default"
            red_color = "red"
            text_color = default_color
            for mf in _hardware_api_.HardwareDB().list_manufacturers(
                for_chips=True
            ):
                if "other" in mf:
                    continue
                # $ Compare with board manufacturer (if any)
                board_mf = board.get_board_dict()["manufacturer"]
                if (board_mf is None) or (board_mf.lower() == "none"):
                    text_color = default_color
                else:
                    if board_mf.lower() == mf.lower():
                        text_color = default_color
                    else:
                        text_color = red_color

                # $ Construct element
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
                for chip_unicum in _hardware_api_.HardwareDB().list_chips(
                    chipmf_list=[
                        mf,
                    ],
                    return_unicums=True,
                ):
                    assert isinstance(chip_unicum, _chip_unicum_.CHIP)
                    if board.get_name().lower() == "custom":
                        text_color = default_color
                    elif (
                        board.get_board_dict()["chip"] == chip_unicum.get_name()
                    ):
                        text_color = default_color
                    else:
                        text_color = red_color
                    subitems.append(
                        {
                            "name": f"{mf}/{chip_unicum.get_name()}",
                            "widgets": [
                                {
                                    "type": "image",
                                    "icon-path": chip_unicum.get_chip_dict(
                                        board=None
                                    )["icon"],
                                },
                                {
                                    "type": "text",
                                    "text": chip_unicum.get_name(),
                                    "color": text_color,
                                },
                            ],
                        }
                    )
                if len(subitems) > 0:
                    dropdown_elements[-1]["subitems"] = subitems
                continue

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

            def finish(dropdown_elements, dropdown_selection):
                self.dropdownElements = dropdown_elements
                self.dropdownSelection = dropdown_selection
                if refreshlock:
                    item.release_refresh_mutex()
                if callback is not None:
                    callback(callbackArg)
                return

            # * Sync self
            chip: _chip_.Chip = item.get_projSegment()
            self.set_asterisk(chip.get_state("DEVICE", "asterisk"))
            if self.has_asterisk():
                self.lblTxt = "*Device".ljust(8)
            else:
                self.lblTxt = "Device ".ljust(8)
            self.closedIconpath = chip.get_chip_dict(board=None)["icon"]
            self.openIconpath = chip.get_chip_dict(board=None)["icon"]
            self.set_error(chip.get_state("DEVICE", "error"))
            self.set_warning(chip.get_state("DEVICE", "warning"))
            functions.assign_icon_err_warn_suffix(itemstatus=self)
            self.__get_dropdown_elements(
                chip=chip,
                is_fake=chip.is_fake(),
                callback=finish,
            )
            return

    __slots__ = ()

    def __init__(
        self,
        chip: _chip_.Chip,
        rootdir: Optional[ChipRootItem],
        parent: Optional[_da_.Folder],
    ) -> None:
        """"""
        super().__init__(
            projSegment=chip,
            rootdir=rootdir,
            parent=parent,
            name="device",
            state=ChipDeviceItem.Status(item=self),
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
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemDropdown=_cm_dropdown_.ItemDropdown(owner=self),
        )
        dropdown: _cm_dropdown_.ItemDropdown = self.get_widget("itemDropdown")
        dropdown.selection_changed_from_to.connect(
            self.selection_changed_from_to,
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def selection_changed_from_to(
        self,
        from_chipname: str,
        to_chipname: str,
    ) -> None:
        """Invoked when user changes selection in the ItemDropdown()-widget.

        :param from_chipname: Original chip name
        :param to_chipname: New chip name
        """
        # * Sanitize input
        if (
            (from_chipname is None)
            or (from_chipname.lower() == "none")
            or (from_chipname.lower() == "empty")
        ):
            from_chipname = "NONE"
        if (
            (to_chipname is None)
            or (to_chipname.lower() == "none")
            or (to_chipname.lower() == "empty")
        ):
            to_chipname = "NONE"
        old_chipname = from_chipname.split("/")[-1]
        new_chipname = to_chipname.split("/")[-1]
        if old_chipname == new_chipname:
            return

        # * Apply new chip
        new_chip_unicum = _chip_unicum_.CHIP(new_chipname)
        if new_chip_unicum is None:
            return
        chip: _chip_.Chip = self.get_projSegment()
        result: Optional[str] = None

        # $ Intro wizard
        # The Chip()-instance from this ChipDeviceItem() is not even part of the project. Compare it
        # with the active one to know if an actual change is needed and if the user must be warned
        # about the consequences.
        if chip.is_fake():
            active_chip = data.current_project.get_chip()
            active_chip_unicum = active_chip.get_chip_unicum()
            if active_chip_unicum.get_name() == new_chip_unicum.get_name():
                # Selected chip is same as currently active one.
                result = "continue"
            elif (active_chip_unicum.get_name() is None) or (
                active_chip_unicum.get_name().lower() == "none"
            ):
                # Active chip is 'NONE'. Just continue without asking quest-
                # ions.
                result = "continue"
            else:
                # Active chip is not 'NONE' and selected one differs from it.
                # Warn user about the implications of changing the chip.
                if self.get_state().has_asterisk():
                    # No need to ask again
                    result = "continue"
                else:
                    result = _ht_.chip_swap_warning()

        # $ Dashboard
        # The Chip()-instance from this ChipDeviceItem() is part of the project. Check if the user
        # must be warned about changing chip.
        else:
            current_chip_unicum = chip.get_chip_unicum()
            if current_chip_unicum.get_name() == new_chip_unicum.get_name():
                # Selected chip is same as currently active one. No need to
                # change anything. This case should actually already have been
                # catched at the start. Just continue, it won't hurt.
                result = "continue"
            elif (current_chip_unicum.get_name() is None) or (
                current_chip_unicum.get_name().lower() == "none"
            ):
                # Current chip is 'NONE'. Just continue without asking quest-
                # ions.
                result = "continue"
            else:
                # Current chip is not 'NONE' and selected one differs from it.
                # Warn user about the implications of changing the chip.
                if self.get_state().has_asterisk():
                    # No need to ask again
                    result = "continue"
                else:
                    result = _ht_.chip_swap_warning()

        # $ Apply
        if result == "continue":
            chip.change_chip(
                chip_unicum=new_chip_unicum,
                callback=None,
                callbackArg=None,
            )
        else:
            # Reset dropdown to its original value.
            dropdown: _cm_dropdown_.ItemDropdown = self.get_widget(
                "itemDropdown"
            )
            dropdown.set_selected_name(from_chipname)
        return

    def show_contextmenu_itemBtn(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _chip_contextmenu_.ChipDeviceContextMenu(
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
        chip: _chip_.Chip = cast(_chip_.Chip, self.get_projSegment())
        if not chip.is_fake():
            super().contextmenuclick_itemBtn(key)

        def link(_key: str) -> None:
            chip_link = chip.get_chip_dict(board=None)["link"]
            if chip_link is not None:
                functions.open_url(chip_link)
            return

        def _help(_key: str) -> None:
            _ht_.chip_help(chip)
            return

        funcs = {
            "link": link,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return


# ^                                        CHIP MEMORY ITEM                                        ^#
# % ============================================================================================== %#
# % ChipMemoryItem()                                                                               %#
# %                                                                                                %#


class ChipMemoryItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: ChipMemoryItem) -> None:
            """"""
            super().__init__(item=item)
            self.closedIconpath = "icons/dialog/help.png"
            self.openIconpath = "icons/dialog/help.png"
            self.progbarForm = "%vKb"
            self.progbarMax = 100
            self.progbarVal = 0
            return

        def sync_state(
            self,
            refreshlock: bool,
            callback: Optional[Callable],
            callbackArg: Any,
        ) -> None:
            """
            ATTENTION:
            Used to run only if self.get_item()._v_layout is not None, but now
            it runs always!
            """
            item: ChipMemoryItem = self.get_item()

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
            root_item: ChipRootItem = item.get_rootdir()
            chip: _chip_.Chip = root_item.get_projSegment()
            memregion_list: List[_chip_.MemRegion] = chip.get_memregion_list()

            # $ Observe all memregions to know how wide their names are
            # First make sure to find the Chip()-instance that belongs to this
            # ChipMemoryItem.Status().
            max_len = 7
            for memregion in memregion_list:
                max_len = max(max_len, len(memregion.get_name()))

            # $ Observe now only the memregion for this Item()-instance
            memregion: _chip_.MemRegion = item.get_projSegment()
            self.lblTxt = memregion.get_name().ljust(
                max_len + 1
            )  # Warning: the actual relpath remains unchanged!
            if memregion.get_memtype() == _chip_unicum_.MEMTYPE.RAM:
                self.closedIconpath = "icons/memory/memory_green.png"
                self.openIconpath = "icons/memory/memory_green_many.png"
                self.progbarCol = "green"
            else:
                self.closedIconpath = "icons/memory/memory_orange.png"
                self.openIconpath = "icons/memory/memory_orange_many.png"
                self.progbarCol = "orange"
            if memregion.get_usage("kb") < 2:
                if memregion.get_length("kb") < 2:
                    self.progbarForm = f"{memregion.get_usage()} bytes / {memregion.get_length()} bytes"
                else:
                    self.progbarForm = f"{memregion.get_usage()} bytes / {memregion.get_length('kb')} K"
            else:
                self.progbarForm = f"{memregion.get_usage('kb')} K / {memregion.get_length('kb')} K"
            self.progbarMax = memregion.get_length()
            self.progbarVal = memregion.get_usage()

            # * Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

    __slots__ = ()

    def __init__(
        self,
        memregion: _chip_.MemRegion,
        rootdir: ChipRootItem,
        parent: _da_.Folder,
    ) -> None:
        """"""
        super().__init__(
            projSegment=memregion,
            rootdir=rootdir,
            parent=parent,
            name=memregion.get_name(),
            state=ChipMemoryItem.Status(item=self),
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
        memregion: _chip_.MemRegion = self.get_projSegment()
        color = (
            "green"
            if memregion.get_memtype() == _chip_unicum_.MEMTYPE.RAM
            else "orange"
        )
        super().init_layout()
        super().bind_guiVars(
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
            itemProgbar=_cm_progbar_.ItemProgbar(owner=self, color=color),
        )
        return

    def leftclick_itemBtn(self, event: qt.QMouseEvent) -> None:
        """"""
        super().leftclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemBtn(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemLbl(event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemProgbar(self, event: qt.QEvent) -> None:
        """"""
        super().leftclick_itemProgbar(event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemProgbar(self, event: qt.QEvent) -> None:
        """"""
        super().rightclick_itemProgbar(event)
        self.show_contextmenu_itemBtn(event)
        return

    def show_contextmenu_itemBtn(
        self, event: Union[qt.QMouseEvent, qt.QEvent]
    ) -> None:
        """"""
        itemBtn = self.get_widget(key="itemBtn")
        contextmenu = _chip_contextmenu_.ChipMemoryContextMenu(
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

    def contextmenuclick_itemBtn(self, key: str, *args):
        """"""
        key = functions.strip_toplvl_key(key)
        super().contextmenuclick_itemBtn(key)

        def select(_key):
            _key = _key.split("/")[-1]
            if _key == "select":
                return
            memsec_name = _key.strip()
            memregion = self.get_projSegment()
            assert isinstance(memregion, _chip_.MemRegion)
            memsection = memregion.get_memsection(name=memsec_name)
            if memsection is None:
                gui.dialogs.popupdialog.PopupDialog.error(
                    title_text="Memory section error",
                    text=f"Memory section {memsec_name} not found!",
                )
                return
            attribute_text = f'__attribute__((section("{memsec_name}")))'
            clipboard = data.application.clipboard()
            clipboard.setText(attribute_text)
            _ht_.memsection_to_clipboard(
                memsection=memsection,
                memregion=memregion,
                attribute_text=attribute_text,
            )
            print(_key)
            return

        def _help(_key):
            memregion = self.get_projSegment()
            _ht_.memregion_help(memregion)
            return

        funcs = {
            "select": select,
            "help": _help,
            "foo": nop,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def self_destruct(
        self,
        killParentLink: bool = True,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill Item {q}{self._name}{q} twice!"
                )
            self.dead = True
        super().self_destruct(
            killParentLink=killParentLink,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
