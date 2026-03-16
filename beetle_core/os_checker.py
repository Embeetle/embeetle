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

from typing import Optional
import os

__os_name_cache: Optional[str] = None
__arch_name_cache: Optional[str] = None


def get_os() -> str:
    """
    Return:
      - "windows"
      - "linux"
      - "macos"
    """
    global __os_name_cache
    if __os_name_cache:
        return __os_name_cache
    import platform

    # Determine normalized platform:
    # "windows", "linux" or "macos"
    __pf = platform.system().lower()
    if __pf == "windows":
        __os_name_cache = "windows"
    elif __pf == "linux":
        __os_name_cache = "linux"
    elif __pf == "darwin":
        __os_name_cache = "macos"
    else:
        raise RuntimeError(f"OS not supported: {__pf}")
    return __os_name_cache


def get_arch() -> str:
    """
    Return:
      - "x86_64"
      - "arm64"
    """
    global __arch_name_cache
    if __arch_name_cache:
        return __arch_name_cache
    import platform

    # Determine normalized architecture:
    # "x86_64" or "arm64"
    __arch = platform.machine().lower()
    if __arch in ("amd64", "x86_64", "x86-64", "x64"):
        __arch_name_cache = "x86_64"
    elif __arch in ("i386", "i686", "x86"):
        __arch_name_cache = "x86"
        raise RuntimeError("32-bit architecture not supported")
    elif __arch in ("arm64", "aarch64"):
        __arch_name_cache = "arm64"
    else:
        raise RuntimeError(f"Architecture not supported: {__arch}")
    return __arch_name_cache


def get_os_with_arch() -> str:
    """
    Return:
      - "windows-x86_64"
      - "linux-x86_64"
      - "macos-x86_64"
      - "macos-arm64"
    """
    return f"{get_os()}-{get_arch()}"


def is_os(os_name: str) -> bool:
    """
    Return True if provided OS name matches
    """
    assert "-" not in os_name
    return os_name == get_os()


def is_os_with_arch(os_arch_name: str) -> bool:
    """
    Return True if provided <os>-<arch> matches
    """
    assert "-" in os_arch_name
    return os_arch_name == get_os_with_arch()


def is_solaris() -> bool:
    """ """
    import sys

    # Solaris uses internal __fork_pty(). All others use pty.fork().
    _is_solaris = sys.platform.lower().startswith(
        "solaris"
    ) or sys.platform.lower().startswith("sunos")
    return _is_solaris


# def fill_in_os(path_str: str) -> str:
#     """
#     Given a path like "C:/Users/krist/embeetle/sys/<os>/bin/", this function
#     will extract the token "<os>" and replace it with the actual OS name, like
#     "windows-x86_64", "linux-x86_64", ...
#     The function first tries to replace the token with the full name of the OS
#     (including the architecture). If there's no match on the harddrive, then
#     it falls back to the simple OS name.
#
#     Add ".exe" at the end if needed.
#     """
#     path_str = path_str.replace("\\", "/")
#     assert "<os>" in path_str
#     # Try with 'get_os_with_arch()'
#     resolved_path: str = path_str.replace("<os>", get_os_with_arch())
#     if os.path.exists(resolved_path):
#         return resolved_path
#     resolved_path = f"{resolved_path}.exe"
#     if os.path.exists(resolved_path):
#         return resolved_path
#
#     # Try with 'get_os()'
#     resolved_path = path_str.replace("<os>", get_os())
#     if os.path.exists(resolved_path):
#         return resolved_path
#     resolved_path = f"{resolved_path}.exe"
#     if os.path.exists(resolved_path):
#         return resolved_path
#     print(
#         f"WARNING: Cannot find\n"
#         f"    '{path_str.replace('<os>', get_os_with_arch())}'\n"
#     )
#     # raise RuntimeError()
#     return resolved_path
