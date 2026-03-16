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

from . import parse_number


class Frequency(float):
    def __new__(cls, data):
        if isinstance(data, int) or isinstance(data, float):
            value = data
        else:
            value, unit = parse_number.parse_unsigned_float(data)
            if unit and unit.rstrip() != "Hz":
                raise ValueError(f"Invalid frequency {data}")
        if value <= 0:
            raise ValueError(f"Non-positive frequency {data}")
        return super().__new__(cls, value)

    def __str__(self):
        if self >= 1e12:
            scale = "T"
            value = self / 1e12
        elif self >= 1e9:
            scale = "G"
            value = self / 1e9
        elif self >= 1e6:
            scale = "M"
            value = self / 1e6
        elif self >= 1e3:
            scale = "k"
            value = self / 1e3
        else:
            scale = ""
            value = self
        return f"{float(value):g}{scale}Hz"
