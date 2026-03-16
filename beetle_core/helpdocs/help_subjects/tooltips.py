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

q = "'"
dq = '"'


def editor_tab(additional_text="") -> str:
    """"""
    if additional_text != "":
        additional_text = f"\n{additional_text}"
    return "\n".join(
        [
            f"Editor tab{additional_text}",
            "Right-click the tab header to display additional options.",
        ]
    )


def filetree_tab(*args) -> str:
    """"""
    return "\n".join(
        [
            "Filetree",
            "This is where the project structure can be adjusted and",
            "special source-analysis options can be set.",
        ]
    )


def messageswindow_tab(*args) -> str:
    """"""
    return "\n".join(
        [
            "Messages window",
            "All system messages (critical and non-critical)",
            "are displayed here.",
        ]
    )


def diagnostics_tab(*args) -> str:
    """"""
    return "\n".join(
        [
            "Diagnostics",
            "All diagnostic messages (errors, warnings, ...)",
            "from the source analysis are displayed here.",
        ]
    )


def symbols_tab(*args) -> str:
    """"""
    return "\n".join(
        [
            "Symbols window",
            "All Symbols (functions, varibles, ...) for the",
            "currently active editor are displayed here.",
            f"If this tab is empty it{q}s either because no editor",
            "was selected or the source analysis is not completed yet.",
        ]
    )


def dashboard_tab(*args) -> str:
    """"""
    return "\n".join(
        [
            "Project dashboard",
            "Project settings (chip options, memory usage, ...)",
            "can be viewed here.",
        ]
    )


def general_console_tab():
    """"""
    return "\n".join(
        [
            "Console",
            "This is a general Console.",
        ]
    )
