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
import threading
import collections
import random
import qt


class FIFO_Queue(qt.QObject):
    """
    This FIFO Queue is special:
        > It contains several LastUpdatedOrderedDict() sub-queues, which you
          should each give a name in the *args parameter.

        > It stores entries as a (key, value)-pairs.

        > It won't store the same entry twice. The value just updates and the
          entry moves to the back (as if it were a new one).
    """

    entries_available = qt.pyqtSignal()

    def __init__(self, *args) -> None:
        super().__init__()
        self._mutex = threading.Lock()
        self._queues = {key: LastUpdatedOrderedDict() for key in args}
        self._cumulative_len = 0
        return

    def start(self) -> None:
        qt.QTimer.singleShot(55, self.check)
        return

    def clean(self) -> None:
        self._cumulative_len = 0

    @qt.pyqtSlot()
    def check(self) -> None:
        # This used to run in a separate thread. However, it's a lightweight
        # check procedure, so it can equally well run in the main.
        assert threading.current_thread() is threading.main_thread()
        if self.has_entries():
            self.entries_available.emit()
        qt.QTimer.singleShot(random.randint(80, 90), self.check)
        return

    # SIZE
    # -----
    def has_entries(self) -> bool:
        for key, queue in self._queues.items():
            if len(queue) != 0:
                return True
        return False

    def get_queue_len(self, queue_name: str) -> int:
        return len(self._queues[queue_name])

    def get_cumulative_len(self) -> int:
        return self._cumulative_len

    # * =====[ FILL ]===== *#
    def put_entry(
        self,
        queue_name: str,
        key: Any,
        value: Any,
        *args,
    ) -> None:
        """Put entry (key, value) into the LastUpdatedOrderedDict() sub-queue
        with the given name."""
        while not self._mutex.acquire(blocking=False):
            qt.QTest.qWait(random.randint(5, 10))
        if key in self._queues[queue_name]:
            pass
        else:
            self._cumulative_len += 1
        self._queues[queue_name][key] = value
        self._mutex.release()
        return

    # * =====[ EXTRACT ]===== *#
    def pop_first_entry(
        self,
        queue_name: str,
    ) -> Tuple[Any, Any]:
        """Pop the first entry from the sub-queue with the given name.

        The entry is returned as a (key, value) tuple.
        """
        while not self._mutex.acquire(blocking=False):
            qt.QTest.qWait(random.randint(5, 10))
        entry = self._queues[queue_name].pop_first_entry()
        self._mutex.release()
        return entry


class FIFO_OrderedQueue(FIFO_Queue):
    """"""

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self._sorted_queues = {key: [] for key in args}
        return

    # SIZE
    # -----
    def has_entries(self) -> bool:
        for key, queue in self._queues.items():
            if len(queue) != 0:
                return True
        for key, queue in self._sorted_queues.items():
            if len(queue) != 0:
                return True
        return False

    def get_queue_len(self, queue_name: str) -> int:
        return max(
            len(self._queues[queue_name]), len(self._sorted_queues[queue_name])
        )

    # * =====[ FILL ]===== *#
    def sort_queues(self) -> None:
        while not self._mutex.acquire(blocking=False):
            qt.QTest.qWait(random.randint(5, 10))
        # 1. Make sure all sorted queues are already emptied.
        for key, queue in self._sorted_queues.items():
            assert len(queue) == 0
        # 2. Sort the queues.
        for key, queue in self._queues.items():
            sorted_list = sorted(
                queue.items(), key=lambda kv: kv[1], reverse=True
            )
            self._sorted_queues[key] = [e[0] for e in sorted_list]
            assert isinstance(self._sorted_queues[key], list)
            self._queues[key] = None
            self._queues[key] = LastUpdatedOrderedDict()
        self._mutex.release()
        return

    # * =====[ EXTRACT ]===== *#
    def pop_first_entry(self, queue_name: str):
        while not self._mutex.acquire(blocking=False):
            qt.QTest.qWait(random.randint(5, 10))
        entry = None
        try:
            entry = self._sorted_queues[queue_name][0]
            del self._sorted_queues[queue_name][0]
        except IndexError:
            pass
        self._mutex.release()
        return entry


class LastUpdatedOrderedDict(collections.OrderedDict):
    """
    Variant on the standard 'OrderedDict'.
    ---------------------------------------
    This variant remembers the order the keys were last inserted. If a new entry
    overwrites an existing entry, the original insertion position is changed and
    moved to the end.
    See: https://docs.python.org/3/library/collections.html#collections.OrderedDict
    """

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        collections.OrderedDict.__setitem__(self, key, value)
        return

    def pop_first_entry(self) -> Optional[Any, Any]:
        """
        Take the first entry, and remove it from this ordered dictionary. The
        entry is returned as a tuple:

        :return    (key, value)

        If the dict is empty, this function returns 'None'.
        """
        try:
            element = self.popitem(last=False)
        except KeyError:
            return None
        return element

    def pop_last_entry(self):
        """
        Take the last entry, and remove it from this ordered dictionary. The
        entry is returned as a tuple:

        :return    (key, value)

        If the dict is empty, this function returns 'None'.
        """
        try:
            element = self.popitem(last=True)
        except KeyError:
            return None
        return element
