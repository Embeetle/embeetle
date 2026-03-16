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
from enum import Enum, auto, global_enum

from .error import validate_name


@global_enum
class PackageType(Enum):
    SIDES2 = auto()
    SIDES4 = auto()
    BGA = auto()


class Package:

    def __init__(
        self, name: str, type: PackageType, nr_of_pins: int, aspect_ratio=None
    ):
        """Create a package.

        - name is the package name

        - type is the package type:

             SIDES2 is a package with two lines of pins, on the left and right
                    edges of the package. The number of pins is always even.

             SIDES4 is a package with four lines of pins, on all four edges
                    of the package. The number of pins is always a multiple of 4.

             BGA is a ball grid array package, with pins arranged in a grid.

        - aspect_ratio is only valid for SIDES2 packages. It is a hint for how
          wide the package is compared to its height: the aspect ratio is the
          width as a percentage of the height.
        """
        validate_name(name)
        self.name = name
        self.type = type
        self.nr_of_pins = nr_of_pins
        self.aspect_ratio = aspect_ratio
        self._pin_names = [str(i) for i in range(1, self.nr_of_pins + 1)]

    @property
    def pin_names(self) -> Iterable[str]:
        """A list of pin names in a well defined order.

        For SIDES2 and SIDES4 packages, pin names are listed in listed in anti-
        clockwise order, starting from the top-left corner of the package, when
        viewing the package from the top.

        For BGA packages, pin names are listed row-by-row, left to right and top
        to bottom, when viewing the package from the top.

        For BGA packages that do not have a pin at each grid position, more
        information wil be added in the future.
        """
        return self._pin_names

    def __str__(self):
        return self.name


packages = {
    package.name: package
    for package in [
        Package(name="SOP8", type=SIDES2, nr_of_pins=8, aspect_ratio=80),
        Package(name="SOP16", type=SIDES2, nr_of_pins=16, aspect_ratio=40),
        Package(name="TSSOP20", type=SIDES2, nr_of_pins=20),
        Package(name="QFN20", type=SIDES4, nr_of_pins=20),
        Package(name="QFN48", type=SIDES4, nr_of_pins=48),
        Package(name="LQFP48", type=SIDES4, nr_of_pins=48),
        Package(name="LQFP64", type=SIDES4, nr_of_pins=64),
        Package(name="LQFP100", type=SIDES4, nr_of_pins=100),
    ]
}
