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
from numbers import Number, Integral, Rational
from fractions import Fraction

"""
Representation of values as used for chip configuration.

Values can be integers, fractions, floats or a special value 'undefined'.

Operations on these values include all operators defined for expressions:
bit-select, equality, less, bitwise not, -or, -and and -exor, concatenation, 
addition, unary minus, mutliplication, division, mapping.

"""


class Value:
    def bit_select(self, msb: int, lsb: int):
        return undefined


class IntegerValue(Value):

    def __init__(self, value: int):
        self._value: int = value

    def bit_select(self, msb: int, lsb: int) -> IntegerValue:
        return IntegerValue(self._value >> lsb & ((1 << (msb - lsb + 1)) - 1))

    def __eq__(self, other: Value) -> Value:
        equal = isinstance(other, IntegerValue) and self._value == other._value
        return IntegerValue(1 if equal else 0)

    def __lt__(self, other: Value):
        if isinstance(other, IntegerValue):
            return self._value < other._value
        return NotImplemented

    def __invert__(self):
        return

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return str(self._value)


class RationalValue(Value):
    pass


class FloatingValue(Value):
    pass


class UndefinedValue(Value):
    pass


undefined = UNdefinedValue()
