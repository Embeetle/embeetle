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

import qt
import data


class ActionFilter(qt.QObject):
    """Object for connecting to the menubar events and filtering the click&drag
    event for the context menu."""

    # Timers
    click_timer = None
    reset_timer = None
    click_drag_action = None

    # Overridden filter method
    def eventFilter(self, receiver, event) -> bool:
        """"""
        if event.type() == qt.QEvent.Type.MouseButtonPress:
            cursor = qt.QCursor.pos()
            cursor = cursor - receiver.pos()
            if receiver.actionAt(cursor) is not None:
                action = receiver.actionAt(cursor)

                # Create the click&drag detect timer
                def click_and_drag():
                    def hide_parents(obj):
                        obj.hide()
                        if obj.parent() is not None and (
                            isinstance(obj.parent(), qt.QMenu)
                        ):
                            hide_parents(obj.parent())
                        return

                    hide_parents(receiver)
                    ActionFilter.click_timer = None
                    if hasattr(action, "pixmap"):
                        data.application.setOverrideCursor(
                            qt.QCursor(action.pixmap)
                        )
                        ActionFilter.click_drag_action = action
                    return

                ActionFilter.click_timer = qt.QTimer(self)
                ActionFilter.click_timer.setInterval(400)
                ActionFilter.click_timer.setSingleShot(True)
                ActionFilter.click_timer.timeout.connect(click_and_drag)
                ActionFilter.click_timer.start()

        elif event.type() == qt.QEvent.Type.MouseButtonRelease:
            ActionFilter.clear_action()
        return super().eventFilter(receiver, event)

    @staticmethod
    def clear_action() -> None:
        """"""
        data.application.restoreOverrideCursor()
        click_timer = ActionFilter.click_timer
        reset_timer = ActionFilter.reset_timer
        if click_timer is not None:
            click_timer.stop()
            click_timer = None
        if reset_timer is not None:
            reset_timer.stop()
            click_drag_action = None
        return
