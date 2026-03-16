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
import threading, functools
import qt, data, purefunctions
import project.segments.project_segment as _ps_
import project.segments.chip_seg.chip as _chip_
import dashboard.items.board_items.board_items as _da_board_items_
import hardware_api.board_unicum as _board_unicum_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class Board(_ps_.ProjectSegment):
    @classmethod
    def create_default_Board(
        cls,
        board_unicum: _board_unicum_.BOARD,
    ) -> Board:
        """Create a default Board()-object for the given 'board_unicum'."""
        return cls(
            is_fake=False,
            board_unicum=board_unicum,
        )

    @classmethod
    def create_empty_Board(cls) -> Board:
        """Create an empty Board()-object."""
        return cls.create_default_Board(
            board_unicum=_board_unicum_.BOARD("custom"),
        )

    @classmethod
    def load(
        cls,
        configcode: Optional[Dict[str, str]],
        project_report: Dict,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Load Board()-object from the relevant part in the config file.

        NOTE:
        The project_report is not returned, but simply modified here.
        """
        # $ Figure out board name
        board_name: Optional[str] = None
        if configcode is None:
            board_name = "custom"
            purefunctions.printc(
                f"WARNING: Board().load() got configcode parameter None\n",
                color="warning",
            )
        else:
            try:
                board_name = configcode["board_name"]
            except:
                try:
                    board_name = configcode["board"]
                except:
                    board_name = "custom"
                    purefunctions.printc(
                        f"\nWARNING: The {q}dashboard_config.btl{q} file does not define a board\n",
                        color="warning",
                    )
        if (board_name is None) or (board_name.lower() in ("none", "null")):
            board_name = "custom"

        # $ Construct board unicum
        board_unicum = None
        try:
            board_unicum = _board_unicum_.BOARD(board_name)
        except:
            board_unicum = _board_unicum_.BOARD("custom")
            purefunctions.printc(
                f"WARNING: Embeetle does not recognize board {q}{board_name}{q}\n",
                color="warning",
            )
        callback(
            cls(
                is_fake=False,
                board_unicum=board_unicum,
            ),
            callbackArg,
        )
        return

    __slots__ = (
        "__board_unicum",
        "__state_dict",
        "_v_rootItem",
        "_v_deviceItem",
        "__trigger_dashboard_refresh_mutex",
    )

    def __init__(
        self,
        is_fake: bool,
        board_unicum: Optional[_board_unicum_.BOARD],
    ) -> None:
        """Create Board()-instance."""
        super().__init__(is_fake=is_fake)

        # Use a mutex to protect the dashboard refreshing from re-entring.
        self.__trigger_dashboard_refresh_mutex = threading.Lock()

        # $ Variables
        self.__board_unicum: Optional[_board_unicum_.BOARD] = board_unicum
        self.__state_dict = {
            "DEVICE": {
                "error": False,
                "warning": False,
                "asterisk": False,
            },
        }

        # $ History
        if not is_fake:
            self.get_history().register_getters(
                board_unicum=self.get_board_unicum,
            )
            self.get_history().register_setters(
                board_unicum=self.set_board_unicum,
            )
            self.get_history().register_asterisk_setters(
                board_unicum=self.set_board_asterisk,
            )
            self.get_history().register_refreshfunc(
                self.trigger_dashboard_refresh,
            )

        # $ Dashboard
        self._v_rootItem: Optional[_da_board_items_.BoardRootItem] = None
        self._v_deviceItem: Optional[_da_board_items_.BoardDeviceItem] = None
        return

    def get_boardfam_unicum(self) -> _board_unicum_.BOARDFAMILY:
        """Access the BOARDFAMILIY()-Unicum."""
        boardfam_name = self.get_board_dict()["boardfamily"]
        return _board_unicum_.BOARDFAMILY(boardfam_name)

    def get_board_unicum(self) -> _board_unicum_.BOARD:
        """Access the BOARD()-Unicum."""
        return self.__board_unicum

    def set_board_unicum(self, board_unicum: _board_unicum_.BOARD) -> None:
        """Swap the BOARD()-Unicum."""
        assert isinstance(board_unicum, _board_unicum_.BOARD)
        self.__board_unicum = board_unicum
        return

    def get_name(self) -> str:
        """Get the name of the BOARD()-Unicum."""
        return self.__board_unicum.get_name()

    def get_board_dict(self) -> Dict[str, Any]:
        """Access the json-dictionary from the BOARD()-Unicum."""
        return self.__board_unicum.get_board_dict()

    def clone(self, is_fake: bool = True) -> Board:
        """Clone this object."""
        return Board(is_fake=is_fake, board_unicum=self.__board_unicum)

    def show_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Show this Board()-instance on the dashboard.

        Only the toplevel item is shown, but the child items are instantiated
        and added to the toplevel item. They get shown when the user clicks on
        the toplevel one.
        """
        assert not self.is_fake()
        self._v_rootItem = _da_board_items_.BoardRootItem(board=self)
        self._v_deviceItem = _da_board_items_.BoardDeviceItem(
            board=self,
            rootdir=self._v_rootItem,
            parent=self._v_rootItem,
        )
        self._v_rootItem.add_child(
            self._v_deviceItem,
            alpha_order=False,
            show=False,
            callback=None,
            callbackArg=None,
        )
        data.dashboard.add_root(self._v_rootItem)
        if callback is not None:
            callback(callbackArg)
        return

    def show_on_intro_wizard(
        self,
        vlyt: qt.QVBoxLayout,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Display the Board on the Intro Wizard, inside the given vlyt."""
        assert self.is_fake()
        self._v_deviceItem = _da_board_items_.BoardDeviceItem(
            board=self,
            rootdir=None,
            parent=None,
        )
        self._v_deviceItem.get_layout().initialize()
        vlyt.addLayout(self._v_deviceItem.get_layout())
        if callback is not None:
            callback(callbackArg)
        return

    def get_impacted_files(self) -> List[str]:
        """"""
        impacted_files = []
        if self.__state_dict["DEVICE"]["asterisk"]:
            impacted_files.append("DASHBOARD_MK")
            impacted_files.append("OPENOCD_CHIPFILE")
            impacted_files.append("GDB_FLASHFILE")
            impacted_files.append("LINKERSCRIPT")
        return impacted_files

    def get_state(self, obj: str, errtype: str) -> bool:
        """"""
        return self.__state_dict[obj][errtype]

    def update_states(
        self,  # type: ignore[override]
        project_report: Optional[Dict] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """The states no longer get pushed directly to the GUI elements.

        Instead, I store them locally in the Board()-instance. The GUI elements
        pull them when syncing.
        """
        if (self.get_name() is None) or (self.get_name().lower() == "none"):
            self.__state_dict["DEVICE"]["error"] = True
            if project_report is not None:
                project_report["board_report"]["DEVICE"]["error"] = True
        else:
            self.__state_dict["DEVICE"]["error"] = False
            if project_report is not None:
                project_report["board_report"]["DEVICE"]["error"] = False
        if callback is not None:
            callback(callbackArg)
        return

    def trigger_dashboard_refresh(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Applies both on Dashboard and Intro Wizard. It will do:

        - update own states
        - update states of related segments (chip)
        - refresh own's widgets
        """
        if not self.__trigger_dashboard_refresh_mutex.acquire(blocking=False):
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    self.trigger_dashboard_refresh,
                    callback,
                    callbackArg,
                ),
            )
            return
        is_fake = self.is_fake()
        chip: Optional[_chip_.Chip] = None
        if is_fake:
            chip = data.current_project.intro_wiz.get_fake_chip()
        else:
            chip = data.current_project.get_chip()

        def update_chip_states(*args) -> None:
            chip.update_states(
                board=self,
                project_report=None,
                callback=start_refresh,
                callbackArg=None,
            )
            return

        def start_refresh(*args) -> None:
            # Just refresh the device item, but it's not sure it exists.
            if self._v_deviceItem:
                if self._v_deviceItem._v_emitter:
                    self._v_deviceItem._v_emitter.refresh_later_sig.emit(
                        True,
                        False,
                        finish,
                        None,
                    )
                    return
            finish()
            return

        def finish(*args) -> None:
            # $ Dashboard
            if not is_fake:
                if self._v_rootItem is not None:
                    if self._v_rootItem._v_layout is not None:
                        self._v_rootItem._v_emitter.refresh_sig.emit(False)
                if data.dashboard is not None:
                    data.dashboard.check_unsaved_changes()
                self.__trigger_dashboard_refresh_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return
            # $ Intro Wizard
            self.__trigger_dashboard_refresh_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        # * Update own states
        self.update_states(
            callback=update_chip_states,
            callbackArg=None,
        )
        return

    def set_board_asterisk(self, on: bool) -> None:
        """"""
        self.__state_dict["DEVICE"]["asterisk"] = on
        return

    def change_board(
        self,
        board_unicum: Union[_board_unicum_.BOARD, str],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Change board and trigger a dashboard refresh.

        Also the corresponding Chip() segment gets refreshed. Works for both the
        Dashboard and the Intro Wizard.
        """
        is_fake = self.is_fake()
        chip: Optional[_chip_.Chip] = None
        if is_fake:
            chip = data.current_project.intro_wiz.get_fake_chip()
        else:
            chip = data.current_project.get_chip()

        def refresh_self(*args):
            self.trigger_dashboard_refresh(
                callback=refresh_chip,
                callbackArg=None,
            )
            return

        def refresh_chip(*args):
            chip.trigger_dashboard_refresh(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args):
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        assert isinstance(board_unicum, _board_unicum_.BOARD)
        if self.__board_unicum == board_unicum:
            finish()
            return
        if not is_fake:
            self.get_history().push()
        self.__board_unicum = board_unicum
        if not is_fake:
            self.get_history().compare_to_baseline(
                refresh=False,
                callback=refresh_self,
                callbackArg=None,
            )
            return
        refresh_self()
        return

    def printout(self, nr: int, *args, **kwargs) -> str:
        """"""
        super().printout(nr)
        lines = [
            f"# {nr}. Board ",
            f"board_name = {q}{self.__board_unicum.get_name()}{q}",
            f"",
        ]
        return "\n".join(lines)

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this Board()-instance and *all* its representations in the
        Dashboard or Intro Wizard."""
        # TODO: Implement
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill Board() twice!")
            self.dead = True

        super().self_destruct(
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
