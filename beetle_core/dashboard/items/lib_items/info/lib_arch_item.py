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
import qt, functions, functools, data
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_richlbl as _cm_richbtn_
import dashboard.items.item as _da_
import libmanager.libobj as _libobj_
import libmanager.libmanager as _libmanager_

if TYPE_CHECKING:
    import dashboard.items.lib_items.lib_item_shared as _lib_item_shared_
from various.kristofstuff import *


class LibarchItem(_da_.File):
    class Status(_da_.File.Status):
        __slots__ = ()

        def __init__(self, item: LibarchItem) -> None:
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

            def start():
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

            def sync_self(*args):
                libobj: _libobj_.LibObj = self.get_item().get_projSegment()
                archs = libobj.get_architectures()
                archs_shown = ""
                if archs is None:
                    archs_shown = (
                        '<span style="color:#888a85;">unspecified</span>'
                    )
                else:
                    if data.is_home:
                        if _libmanager_.chip_exists_compatible_with_lib_archs(
                            archs
                        ):
                            archs_shown = ", ".join(archs)
                        else:
                            archs_shown = f'<span style="color:#cc0000;">{", ".join(archs)}</span>'
                    else:
                        if _libmanager_.is_chip_compatible_with_lib_archs(
                            chip_unicum=data.current_project.get_chip().get_chip_unicum(),
                            archs=archs,
                        ):
                            archs_shown = ", ".join(archs)
                        else:
                            archs_shown = f'<span style="color:#cc0000;">{", ".join(archs)}</span>'
                lbltext = "architectures:".ljust(15, "^") + archs_shown
                lbltext = lbltext.replace("^", "&nbsp;")
                self.lblTxt = (
                    f"*{lbltext}" if self.has_asterisk() else f"{lbltext} "
                )
                self.closedIconpath = "icons/tool_cards/card_chip.png"
                self.openIconpath = "icons/tool_cards/card_chip.png"
                functions.assign_icon_err_warn_suffix(itemstatus=self)
                finish()
                return

            def finish():
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
        parent: Union[_da_.Folder, _lib_item_shared_.LibItemShared],
    ) -> None:
        """Create a LibarchItem()-instance for the dashboard, to show the archi-
        tectures of a specific library.

        :param libobj: The Lib()-instance that represents the library.
        :param rootdir: The toplevel LIBRARIES dashboard item.
        :param parent: The library item bound to the Lib()-instance: what you
            get when you invoke 'libobj.get_dashboard_item()'
        """
        super().__init__(
            projSegment=libobj,
            rootdir=rootdir,
            parent=parent,
            name=f"{libobj.get_name()}_arch",
            state=LibarchItem.Status(item=self),
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
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        super().rightclick_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemLbl(event)
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemLbl(event)
        return

    def leftclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().leftclick_itemRichLbl(event)
        return

    def rightclick_itemRichLbl(self, event: qt.QEvent) -> None:
        super().rightclick_itemRichLbl(event)
        return
