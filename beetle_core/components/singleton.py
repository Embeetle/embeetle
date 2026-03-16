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
import qt


class Singleton(type):
    """Use 'Singleton' as a metaclass to make sure you can only create a single
    object from the given class.

    Note: design pattern taken from StackOverflow,
          see https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class QSingleton(qt.sip.wrappertype, type):
    """Singletons for Qt."""

    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kw)
        return cls.instance


class Unicum(type):
    """Use 'Unicum' as a metaclass to make sure you can only create a single
    object from the class for each name. Usage Example:

    class CHIP(metaclass=Unicum):
        def __init__(self, name):
            ...

    a = CHIP('foo')
    b = CHIP('foo')
    a is b --> True
    """

    _instances = {}

    def __call__(cls, name):
        extended_name = f"{name}_{cls}"
        if extended_name not in cls._instances:
            cls._instances[extended_name] = super(Unicum, cls).__call__(name)
        return cls._instances[extended_name]

    def get_name(self) -> str:
        raise NotImplementedError()

    @classmethod
    def get_unicum_from_name(mcs, name: str) -> Optional[Unicum]:
        raise NotImplementedError()
