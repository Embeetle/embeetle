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

from . import load_json
from .model import (
    Clock,
    Expression,
    Field,
    Mapping,
    MappingState,
    Pin,
    Pad,
    PadMode,
    PadType,
    Part,
    Peripheral,
    Register,
    Series,
    SettingKind,
    Setting,
    Signal,
    PeripheralKind,
    ExternalClockMode,
    ExternalClock,
    InternalClock,
    MuxClock,
    MultipliedClock,
    DividedClock,
    Orientation,
    Bus,
    ClockLayout,
    ClockSink,
    AI,
    FI,
    PU,
    PD,
    PP,
    PP_AF,
    OD,
    OD_AF,
)
from .package import Package, PackageType, packages, SIDES2, SIDES4, BGA
from .config import Config
from .codegen import generate_code
from .error import ConfigError
from .expression import ExpressionError
