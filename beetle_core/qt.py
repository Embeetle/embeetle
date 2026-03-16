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

import os
from typing import *

import PyQt6  # noqa
import PyQt6.Qsci  # noqa
import PyQt6.QtCore  # noqa
import PyQt6.QtGui  # noqa
import PyQt6.QtTest  # noqa
import PyQt6.QtWidgets  # noqa
from PyQt6 import sip  # noqa
from PyQt6.Qsci import *  # noqa
from PyQt6.QtCore import *  # noqa
from PyQt6.QtGui import *  # type: ignore
from PyQt6.QtTest import *  # noqa
from PyQt6.QtWidgets import *  # noqa

PyQt = PyQt6

# Global timer store (shared across the module)
__timer_store: dict[str, QTimer] = {}

QLoggingCategory.setFilterRules("*.debug=false")


def create_qsize(width, height) -> QSize:
    return QSize(int(width), int(height))


def create_qpoint(x, y) -> QPoint:
    return QPoint(int(x), int(y))


def start_named_qtimer(
    owner: QObject,
    timer_name: str,
    interval_ms: int,
    callback: Callable[[], None],
) -> None:
    """Start or restart a named single-shot QTimer using a global timer store.

    Args:
        owner: The QObject that owns the timer (usually `self`).
        timer_name: Unique name to identify this timer.
        interval_ms: Interval in milliseconds before timeout.
        callback: The function to call when the timer fires.
    """
    global __timer_store

    timer = __timer_store.get(timer_name)

    if timer is None:
        timer = QTimer(owner)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        __timer_store[timer_name] = timer

    # Check if the owner is valid
    if sip.isdeleted(owner):
        print("[QTimer] Parent deleted!")
        del __timer_store[timer_name]
        return

    if timer.isActive():
        timer.stop()

    timer.setInterval(interval_ms)
    timer.start()

def stop_named_qtimer(timer_name: str, remove: bool = False) -> None:
    """Stop a QTimer stored in the global __timer_store by name.

    Args:
        timer_name: The name used to register the timer in __timer_store.
        remove: If True, also delete the timer from the store after stopping it.
    """
    global __timer_store

    timer = __timer_store.get(timer_name)
    if timer is None:
        return
    
    # Check if the owner is valid
    if sip.isdeleted(owner):
        print("[QTimer] Parent deleted!")
        del __timer_store[timer_name]
        return

    if timer.isActive():
        timer.stop()

    if remove:
        del __timer_store[timer_name]
