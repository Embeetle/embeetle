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

if TYPE_CHECKING:
    pass


def create_default_project_report():
    """"""
    default_report = {
        "dot_beetle_report": {
            "first_opening": False,
        },
        "board_report": {
            "DEVICE": {"error": False, "warning": False},
        },
        "chip_report": {
            "DEVICE": {"error": False, "warning": False},
        },
        "probe_report": {
            "DEVICE": {"error": False, "warning": False},
            "TRANSPORT_PROTOCOL": {"error": False, "warning": False},
        },
        "treepath_report": {
            "BUILD_DIR": {
                "error": False,
                "warning": False,
            },
            "BIN_FILE": {
                "error": False,
                "warning": False,
            },
            "ELF_FILE": {
                "error": False,
                "warning": False,
            },
            "BOOTLOADER_FILE": {
                "error": False,
                "warning": False,
            },
            "BOOTSWITCH_FILE": {
                "error": False,
                "warning": False,
            },
            "PARTITIONS_CSV_FILE": {
                "error": False,
                "warning": False,
            },
            "LINKERSCRIPT": {
                "error": False,
                "warning": False,
            },
            "MAKEFILE": {
                "error": False,
                "warning": False,
            },
            "DASHBOARD_MK": {
                "error": False,
                "warning": False,
            },
            "FILETREE_MK": {
                "error": False,
                "warning": False,
            },
            "GDB_FLASHFILE": {
                "error": False,
                "warning": False,
            },
            "OPENOCD_CHIPFILE": {
                "error": False,
                "warning": False,
            },
            "OPENOCD_PROBEFILE": {
                "error": False,
                "warning": False,
            },
            "PACKPATH": {
                "error": False,
                "warning": False,
            },
            "BUTTONS_BTL": {
                "error": False,
                "warning": False,
            },
        },
        "toolpath_report": {
            "COMPILER_TOOLCHAIN": {
                "proj_uid": None,
                "toolman_uid": None,
                "remote_uid": None,
                "error": False,
                "warning": False,
            },
            "BUILD_AUTOMATION": {
                "proj_uid": None,
                "toolman_uid": None,
                "remote_uid": None,
                "error": False,
                "warning": False,
            },
            "FLASHTOOL": {
                "proj_uid": None,
                "toolman_uid": None,
                "remote_uid": None,
                "error": False,
                "warning": False,
            },
        },
        "connection_report": {
            "connection_failed": False,
        },
        "remote_toollist": None,
    }
    return default_report
