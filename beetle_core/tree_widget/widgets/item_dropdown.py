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
import threading, functools, traceback
import qt, data, purefunctions
import tree_widget.widgets.item_widget as _cm_widget_
import gui.helpers.advancedcombobox as _advanced_combobox_

if TYPE_CHECKING:
    import tree_widget.items.item as _cm_
from various.kristofstuff import *


class ItemDropdown(
    _cm_widget_.ItemWidget, _advanced_combobox_.AdvancedComboBox
):
    leftclick_signal = qt.pyqtSignal(str, object)  # (key, event)
    ctrl_leftclick_signal = qt.pyqtSignal(str, object)  # (key, event)
    rightclick_signal = qt.pyqtSignal(str, object)  # (key, event)
    dragstart_signal = qt.pyqtSignal(str, object, str)  # (key, event, mimetxt)
    dragenter_signal = qt.pyqtSignal(str, object, str)  # (key, event, mimetxt)
    dragleave_signal = qt.pyqtSignal(str, object)  # (key, event)
    dragdrop_signal = qt.pyqtSignal(str, object, str)  # (key, event, mimetxt)

    keypress_signal = qt.pyqtSignal(str, object)  # (key, event)
    keyrelease_signal = qt.pyqtSignal(str, object)  # (key, event)
    focusin_signal = qt.pyqtSignal(str, object)  # (key, event)
    focusout_signal = qt.pyqtSignal(str, object)  # (key, event)

    def __init__(self, owner: _cm_.Item) -> None:
        """"""
        try:
            _advanced_combobox_.AdvancedComboBox.__init__(
                self,
                parent=owner.get_rootdir().get_chassis_body(),
                image_size=data.get_general_icon_pixelsize(),
                contents_margins=(2, 2, 2, 2),
                spacing=4,
            )
        except Exception as e:
            _advanced_combobox_.AdvancedComboBox.__init__(
                self,
                parent=None,
                image_size=data.get_general_icon_pixelsize(),
                contents_margins=(2, 2, 2, 2),
                spacing=4,
            )
        _cm_widget_.ItemWidget.__init__(
            self,
            key="itemDropdown",
            owner=owner,
        )
        # WARNING: The mouse event overrides in 'item_widget.py' don't run for
        # an AdvancedComboBox() widget. Therefore, the 'bind_guiVars()' method
        # in beetle_core/tree_widget/items/item.py has no use. The signals being
        # connected there won't fire anyway.
        # That's why the Item() holding this widget (eg. a ToolpathItem()) needs
        # to connect the following signals manually:
        #   - activated
        #   - selection_changed
        #   - selection_changed_from_to
        self.sync_widg(
            refreshlock=False,
            force_stylesheet=False,
            callback=None,
            callbackArg=None,
        )
        self.setCursor(qt.QCursor(qt.Qt.CursorShape.PointingHandCursor))
        return

    def set_normal_stylesheet(self) -> None:
        """"""
        _advanced_combobox_.AdvancedComboBox.update_style(self)
        return

    def sync_widg(
        self,
        refreshlock: bool,
        force_stylesheet: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        item = self.get_item()
        if (
            (item is None)
            or (item.is_dead())
            or (item._v_layout is None)
            or qt.sip.isdeleted(self)
        ):
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        assert threading.current_thread() is threading.main_thread()
        if refreshlock:
            if not self.get_item().acquire_refresh_mutex():
                qt.QTimer.singleShot(
                    10,
                    functools.partial(
                        self.sync_widg,
                        refreshlock,
                        force_stylesheet,
                        callback,
                        callbackArg,
                    ),
                )
                return

        # * Sync self
        if qt.sip.isdeleted(self):
            # Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        state = self.get_item().get_state()
        if state.dropdownSelection == "@externally_refreshed":
            # Finish
            if refreshlock:
                item.release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        # $ 1. Force stylesheet
        if force_stylesheet:
            self.set_normal_stylesheet()
            self.style().unpolish(self)
            self.style().polish(self)

        # $ 2. Delete all
        self.clear()

        # $ 3. Set elements
        elements = state.dropdownElements
        selected_element = state.dropdownSelection
        added_element_names = []
        for e in elements:
            name = e["name"]
            if name in added_element_names:
                purefunctions.printc(
                    f"WARNING: cannot add element {q}{name}{q} twice!",
                    color="warning",
                )
            else:
                added_element_names.append(name)
                try:
                    self.add_item(
                        item=e,
                        do_update=False,
                    )
                except Exception as e:
                    traceback.print_exc()
                    pass
        if selected_element is not None:
            try:
                self.set_selected_name(selected_element)
            except Exception as e:
                pass

        # $ 4. Set size
        self.set_minimum_height(
            max(
                data.get_general_font_height(),
                data.get_general_icon_pixelsize(is_inner=False),
            )
        )
        self.adjust_size()

        # * Finish
        if refreshlock:
            item.release_refresh_mutex()
        if callback is not None:
            callback(callbackArg)
        return

    """-------------------------------------------------------------------"""
    """ 3. DEATH                                                          """
    """-------------------------------------------------------------------"""

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
                raise RuntimeError(
                    f"Trying to kill ItemDropdown() {q}{self._key}{q} twice!"
                )
            self.dead = True

        _advanced_combobox_.AdvancedComboBox.self_destruct(
            self,
            death_already_checked=True,
        )
        _cm_widget_.ItemWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
