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
import data, os
import bpathlib.path_power as _pp_
import contextmenu.contextmenu as _contextmenu_
import iconfunctions

if TYPE_CHECKING:
    pass


def get_dropdown_node(text: str) -> Dict:
    """
    Return a dictionary like this:
    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │ # ICONS NODE                                                                                │
    │ {                                                                                           │
    │     'name': 'icons',                                                                        │
    │     'widgets': (                                                                            │
    │         {'icon-path': 'icons/gen/lexers.png', 'type': 'image'},                             │
    │         {'color': 'default', 'text': 'Change icon', 'type': 'text'},                        │
    │     ),                                                                                      │
    │     'subitems': (                                                                           │
    │        ┌# CHIP NODE                                                                         │
    │        │{                                                                                   │
    │        │    'name': 'chip',                                                                 │
    │        │    'widgets': (                                                                    │
    │        │        {'icon-path': 'icons/chip/chip.png', 'type': 'image'},                      │
    │        │        {'color': 'default', 'text': 'microcontrollers', 'type': 'text'},           │
    │        │    ),                                                                              │
    │        │    'subitems': [                                                                   │
    │        │        # GIGA_CHIP.PNG                                                             │
    │        │        {                                                                           │
    │        │            'name': 'icons/chip/giga_chip.png',                                     │
    │        │            'widgets': (                                                            │
    │        │                {'icon-path': 'icons/chip/giga_chip.png', 'type': 'image'},         │
    │        │                {'color': 'default', 'text': 'giga_chip.png', 'type': 'text'},      │
    │        │            ),                                                                      │
    │        │        },                                                                          │
    │        │        # ESPRESSIF_CHIP.PNG                                                        │
    │        │        {                                                                           │
    │        │            'name': 'icons/chip/espressif_chip.png',                                │
    │        │            'widgets': (                                                            │
    │        │                {'icon-path': 'icons/chip/espressif_chip.png', 'type': 'image'},    │
    │        │                {'color': 'default', 'text': 'espressif_chip.png', 'type': 'text'}, │
    │        │            ),                                                                      │
    │        │        },                                                                          │
    │        │        ...                                                                         │
    │        │    ],                                                                              │
    │        │},                                                                                  │
    │        └                                                                                    │
    │        ┌# BOARD NODE                                                                        │
    │        │{                                                                                   │
    │        │    'name': 'board',                                                                │
    │        │    'widgets': (                                                                    │
    │        │        {'icon-path': 'icons/board/custom_board.png', 'type': 'image'},             │
    │        │        {'color': 'default', 'text': 'boards', 'type': 'text'},                     │
    │        │    )                                                                               │
    │        │    'subitems': [...],                                                              │
    │        │},                                                                                  │
    │        └                                                                                    │
    │        ┌# PROBE NODE                                                                        │
    │        │{                                                                                   │
    │        │    'name': 'probe',                                                                │
    │        │    'widgets': (                                                                    │
    │        │        {'icon-path': 'icons/probe/probe.png', 'type': 'image'},                    │
    │        │        {'color': 'default', 'text': 'probes', 'type': 'text'},                     │
    │        │    )                                                                               │
    │        │    'subitems': [...],                                                              │
    │        │}                                                                                   │
    │        └                                                                                    │
    │     ),                                                                                      │
    │ }                                                                                           │
    └─────────────────────────────────────────────────────────────────────────────────────────────┘

    """
    # * FILL LEAFS
    chip_leaves = []
    board_leaves = []
    probe_leaves = []
    text_color = "default"

    for topic in ("chip", "board", "probe"):
        folder = f"{iconfunctions.get_icon_source_folder()}/{topic}"
        for filename in os.listdir(folder):
            if (not filename.endswith(".png")) and (
                not filename.endswith(".svg")
            ):
                continue
            if filename.endswith(
                (
                    "_err.png",
                    "_warn.png",
                    "_dis.png",
                    "_cut.png",
                    "_full.png",
                    "(err).png",
                    "(warn).png",
                    "(dis).png",
                    "(cut).png",
                    "(full).png",
                    "_err.svg",
                    "_warn.svg",
                    "_dis.svg",
                    "_cut.svg",
                    "_full.svg",
                    "(err).svg",
                    "(warn).svg",
                    "(dis).svg",
                    "(cut).svg",
                    "(full).svg",
                )
            ):
                continue
            iconpath = f"icons/{topic}/{filename}"
            leave_item = {
                "name": iconpath,
                "widgets": (
                    {"type": "image", "icon-path": iconpath},
                    {"type": "text", "text": filename, "color": text_color},
                ),
            }
            if topic == "chip":
                chip_leaves.append(leave_item)
            elif topic == "board":
                board_leaves.append(leave_item)
            elif topic == "probe":
                probe_leaves.append(leave_item)
            continue
        continue

    # * ICONS > CHIP
    chip_node = {
        "name": "chip",
        "widgets": (
            {"type": "image", "icon-path": "icons/chip/chip.png"},
            {"type": "text", "text": "microcontrollers", "color": text_color},
        ),
        "subitems": chip_leaves,
    }

    # * ICONS > BOARD
    board_node = {
        "name": "board",
        "widgets": (
            {"type": "image", "icon-path": "icons/board/custom_board.png"},
            {"type": "text", "text": "boards", "color": text_color},
        ),
        "subitems": board_leaves,
    }

    # * ICONS > PROBE
    probe_node = {
        "name": "probe",
        "widgets": (
            {"type": "image", "icon-path": "icons/probe/probe.png"},
            {"type": "text", "text": "probes", "color": text_color},
        ),
        "subitems": probe_leaves,
    }

    #! ICONS
    icon_node = {
        "name": "icons",
        "widgets": (
            {"type": "image", "icon-path": "icons/gen/lexers.png"},
            {"type": "text", "text": text, "color": text_color},
        ),
        "subitems": (
            chip_node,
            board_node,
            probe_node,
        ),
    }
    return icon_node


def get_icon_node(
    contextmenu_root: _contextmenu_.ContextMenuRoot,
    parent_node: _contextmenu_.ContextMenuNode,
    text: str,
) -> _contextmenu_.ContextMenuNode:
    """Create a ContextMenuNode() to select an icon. The key is always 'icons',
    but the shown text in the context menu is free to choose.

    RESULT
    ======
    In the click-callback of the context menu, first you should strip the top-
    level key:
        key = functions.strip_toplvl_key(key)

    From then on, the key will start with 'icons/', if a leaf in this node was
    selected. Then, you can decypher the key like this.
    """
    #! ICONS
    icon_node = _contextmenu_.ContextMenuNode(
        contextmenu_root=contextmenu_root,
        parent=parent_node,
        text=text,
        key="icons",
        iconpath="icons/gen/lexers.png",
    )

    # * ICONS > CHIP
    icon_node.add_child(
        _contextmenu_.ContextMenuNode(
            contextmenu_root=contextmenu_root,
            parent=icon_node,
            text="microcontrollers",
            key="chip",
            iconpath="icons/chip/chip.png",
        )
    )

    # * ICONS > BOARD
    icon_node.add_child(
        _contextmenu_.ContextMenuNode(
            contextmenu_root=contextmenu_root,
            parent=icon_node,
            text="boards",
            key="board",
            iconpath="icons/board/custom_board.png",
        )
    )

    # * ICONS > PROBE
    icon_node.add_child(
        _contextmenu_.ContextMenuNode(
            contextmenu_root=contextmenu_root,
            parent=icon_node,
            text="probes",
            key="probe",
            iconpath="icons/probe/probe.png",
        )
    )

    # * Fill icon_node
    for topic in ("chip", "board", "probe"):
        folder = f"{iconfunctions.get_icon_source_folder()}/{topic}"
        for filename in os.listdir(folder):
            if (not filename.endswith(".png")) and (
                not filename.endswith(".svg")
            ):
                continue
            if filename.endswith(
                (
                    "_err.png",
                    "_warn.png",
                    "_dis.png",
                    "_cut.png",
                    "_full.png",
                    "(err).png",
                    "(warn).png",
                    "(dis).png",
                    "(cut).png",
                    "(full).png",
                    "_err.svg",
                    "_warn.svg",
                    "_dis.svg",
                    "_cut.svg",
                    "_full.svg",
                    "(err).svg",
                    "(warn).svg",
                    "(dis).svg",
                    "(cut).svg",
                    "(full).svg",
                )
            ):
                continue
            iconpath = f"icons/{topic}/{filename}"
            icon_node.get_child(key=topic).add_child(
                _contextmenu_.ContextMenuLeaf(
                    contextmenu_root=contextmenu_root,
                    parent=icon_node.get_child(key=topic),
                    text=filename,
                    key=filename,
                    iconpath=iconpath,
                )
            )
    return icon_node
