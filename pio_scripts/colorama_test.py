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

# --- 256-color extensions for Colorama (foreground only) --------------------
import typing
from colorama import init, Style
from colorama import Fore as _Fore  # reuse Colorama's Fore instance

# Friendly names -> 256-color palette indices
# (Picked from: https://jonasjacek.github.io/colors)
_EXTRA_256 = {
    "TEAL": 37,  # teal / cyan-blue (#00afaf)
    "SPRINGGREEN": 48,  # spring green (#00ff5f)
    "AQUA": 51,  # bright aqua (#00ffff)
    "INDIGO": 54,  # deep indigo (#5f5fff)
    "STEEL": 67,  # steel blue (#5f87ff)
    "TURQUOISE": 80,  # turquoise (#5fd7d7)
    "PURPLE": 93,  # medium purple (#875fff)
    "SKY": 117,  # sky blue (#87d7ff)
    "LIME": 118,  # bright lime (#87ff00)
    "OLIVE": 142,  # muted olive (#afd787)
    "PLUM": 176,  # plum (#d787d7)
    "GOLD": 178,  # warm gold (#d7af5f)
    "TAN": 180,  # light tan (#d7d7af)
    "PINK": 205,  # hot pink (#ff5faf)
    "ORANGE": 208,  # vivid orange (#ff8700)
    "CORAL": 209,  # soft coral (#ff8787)
    "ROSE": 211,  # dusty rose (#ffafaf)
    "GRAY": 244,  # mid gray (#808080)
}

# Attach new attributes to the existing Fore object
_name = _code = None
for _name, _code in _EXTRA_256.items():
    setattr(_Fore, _name, f"\033[38;5;{_code}m")
del (
    _name,
    _code,
    _EXTRA_256,
)  # keep globals tidy

# --- tell static analysers that `Fore` HAS those attributes -----------------
if typing.TYPE_CHECKING:  # executed only by IDE/type-checker

    class _ForeWith256:
        ORANGE: str
        PINK: str
        PURPLE: str
        TEAL: str
        LIME: str
        GRAY: str
        GOLD: str
        SKY: str
        TURQUOISE: str
        AQUA: str
        SPRINGGREEN: str
        OLIVE: str
        CORAL: str
        ROSE: str
        INDIGO: str
        STEEL: str
        TAN: str
        PLUM: str

    Fore = typing.cast("_ForeWith256", _Fore)  # rebind for type checkers only
else:
    Fore = _Fore  # normal runtime name
# ---------------------------------------------------------------------------


init()

# ---------------------------------------------------------------------------
# Groups are ordered roughly by hue, then by brightness / vividness
# ---------------------------------------------------------------------------
GROUPS: dict[str, list[str]] = {
    "Reds": [
        "RED",
        "LIGHTRED_EX",
        "CORAL",
        "ROSE",
        "PINK",
        "ORANGE",
    ],
    "Greens": [
        "GREEN",
        "LIGHTGREEN_EX",
        "SPRINGGREEN",
        "LIME",
        "TEAL",
    ],
    "Yellows / Browns": [
        "YELLOW",
        "LIGHTYELLOW_EX",
        "GOLD",
        "TAN",
        "OLIVE",
    ],
    "Blues / Purples": [
        "BLUE",
        "LIGHTBLUE_EX",
        "STEEL",
    ],
    "Purples": [
        "MAGENTA",
        "LIGHTMAGENTA_EX",
        "INDIGO",
        "PURPLE",
        "PLUM",
    ],
    "Cyans / Aquas": [
        "CYAN",
        "LIGHTCYAN_EX",
        "AQUA",
        "TURQUOISE",
        "SKY",
    ],
    "Neutrals": [
        "WHITE",
        "LIGHTWHITE_EX",
        "GRAY",
        "RESET",
    ],
}


def print_group(title: str, names: list[str]) -> None:
    # print(f"\n{Style.BRIGHT}{title}:{Style.RESET_ALL}")
    just_table = (
        len("MAGENTA"),
        len("LIGHTMAGENTA_EX"),
        len("SPRINGGREEN"),
        len("TURQUOISE"),
        len("OLIVE"),
        len("ORANGE"),
    )
    for n, rename in enumerate(names):
        color = getattr(Fore, rename)
        print(
            f"{color}{rename.ljust(just_table[n]+1)}{Fore.RESET}",
            end="  ",
        )
    print()  # newline after each group


for heading, colour_names in GROUPS.items():
    print_group(heading, colour_names)
