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
import functools
import warnings
import qt


def call_once(method):
    """
    Decorator that lets an **instance method run only once** for the
    lifetime of the object.

    - The first (outermost) call executes the method and marks the instance
      as "done".

    - Later external calls are skipped and emit a `RuntimeWarning`.

    - Re-entrant calls triggered by `super()` in cooperative multiple
      inheritance are detected and allowed to pass through, so the full
      MRO chain still runs exactly one time.

    Signature and return value of the original method are preserved.
    """
    flag = f"__{method.__name__}_called"  # per-instance "done" flag
    reentrant_attr = (
        f"__{method.__name__}_in_progress"  # per-instance "I'm inside" flag
    )

    @functools.wraps(method)
    def wrapper(self, *args, **kw):
        # 1. Was the public entry already executed (outermost call)?
        if getattr(self, flag, False) and not getattr(
            self, reentrant_attr, False
        ):
            warnings.warn(
                f"{method.__name__} already called",
                RuntimeWarning,
                stacklevel=2,
            )
            return

        # 2. Are we *already* somewhere deeper in the same call-chain?
        if getattr(self, reentrant_attr, False):  # <- "re-entrant" guard
            return method(
                self, *args, **kw
            )  # call *original* method, skip bookkeeping

        # 3. First (outermost) call -> mark *in progress*
        setattr(self, reentrant_attr, True)
        try:
            result = method(self, *args, **kw)  # run the real body
            setattr(self, flag, True)  # mark "done" once body finished
            return result
        finally:
            setattr(
                self, reentrant_attr, False
            )  # clear "in progress" flag no matter what

    return wrapper


class WidgetCleaner:
    """
    Mix-in that gives a robust, idempotent `self_destruct()`.

    Put **WidgetCleaner first** in the base-class list so its method
    overrides Qt's, e.g.:

        class MyWidget(WidgetCleaner, qt.QFrame):
            ...

    The method:
    - Runs exactly once per instance (decorated with `@call_once`).
    - Recursively cleans layouts, attributes, and containers.
    - De-parents and `deleteLater`'s itself.
    """

    @call_once
    def self_destruct(self) -> None:
        """Properly destroy this widget. First destroy all its child widgets,
        then destroy this widget itself (by deparenting it).
        """
        if qt.sip.isdeleted(self):
            return

        processed_widgets: set[int] = set()

        def _handle(obj: Any) -> bool:
            """Return True if *obj* held a Qt widget (customised or not)."""
            if id(obj) in processed_widgets:
                return True  # already dealt with

            try:
                if qt.sip.isdeleted(obj):
                    return True
            except:
                pass

            # Customised widget?
            if callable(getattr(obj, "self_destruct", None)):
                processed_widgets.add(id(obj))
                obj.self_destruct()
                return True

            # Plain Qt widget?
            if isinstance(obj, qt.QWidget):
                processed_widgets.add(id(obj))
                if not qt.sip.isdeleted(obj):
                    obj.setParent(None)
                    obj.deleteLater()
                return True

            # Container holding potential widgets?
            if isinstance(obj, (list, tuple, set, frozenset)):
                for o in list(obj):
                    _handle(o)
                return True
            if isinstance(obj, dict):
                for o in list(obj.values()):
                    _handle(o)
                return True

            return False  # Leave everything else untouched

        # 1. CLEAN LAYOUT
        # ---------------
        # Clean all child widgets that can be found in the layout. Every found
        # child widget is handed over to the `_handle()` function to be
        # destroyed properly:
        # - If it is a general QT widget, the `_handle()` function simply
        #   deparents it.
        # - If it is a custom widget that has its own `self_destruct()` method,
        #   then that method is called on the widget.
        layout = self.layout()
        if layout is not None:
            # iterate back-to-front so indices stay valid
            for i in reversed(range(layout.count())):
                # takeAt(i) removes the item from the layout, avoiding dangling
                # pointers on the C++ side.
                item = layout.takeAt(i)
                child = item.widget()  # None for spacers
                if child is not None:
                    _handle(child)
                # Delete the QLayoutItem wrapper. Deleting the QLayoutItem
                # mirrors the normal Qt parent/ownership pattern and eliminates
                # a small leak.
                qt.sip.delete(item)
                continue

        # 2. CLEAN ATTRIBUTES
        # -------------------
        # It is possible that this widget has child widgets that are not (yet)
        # added to its layout, but held in some attribute (or container). Clean
        # them up here.
        for attr, value in list(self.__dict__.items()):
            if _handle(value):
                setattr(self, attr, None)
            continue

        # 3. DISCONNECT SIGNALS
        # ---------------------
        # Break every Qt connection in which *this* object participates. PyQt6
        # lets you call `self.disconnect()` with no arguments; PySide6 still
        # exposes the static variant  QObject.disconnect(obj).
        # This severs all signal-slot connections that involve the object - both
        # as sender and receiver - so no stray callbacks can fire after
        # deletion.
        try:
            self.disconnect()  # PyQt-style
        except (AttributeError, TypeError):
            qt.QObject.disconnect(self)  # PySide fallback

        # 4. DEPARENT ONESELF
        # -------------------
        # After cleaning up (destroying) all the children, it's time to destroy
        # oneself. First double check if it hasn't happened already by the GC.
        # Note: it's not harmful if deparenting and the `deleteLater()` call
        # are duplicated in the superclass call.
        if qt.sip.isdeleted(self):
            return
        self.setParent(None)
        self.deleteLater()

        # 5. CALL SUPERCLASS SELF_DESTRUCT() METHOD
        # -----------------------------------------
        next_destruct = getattr(super(), "self_destruct", None)
        if next_destruct:
            next_destruct()
        return
