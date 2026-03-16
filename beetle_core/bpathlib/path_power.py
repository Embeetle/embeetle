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
import os
import fnmatch as _fn_

q = "'"
dq = '"'
"""'' --------------------------------------------------------------------------
---------------------------------------- '' ''  RULES (for abspath and relpath):
'' ''  (1) If a relpath or abspath points to a directory, it does NOT end in
"/", but merely the name of                 '' ''      that directory.
'' ''  (2) The relpath does NOT start with "./", but merely the name of the
first subfolder (if applicable, otherwise    ''.

''      just the name of the file). This rule makes the use of os.path.join(..) much easier.                          ''
''  (3) If the relpath is empty - in other words, the target is simply the root folder - then the relpath             ''
''      is just a dot "."                                                                                             ''
''  (4) If the requested file or folder doesn't exist, both relpath and abspath must be 'None'!                       ''
''                                                                                                                    ''
''  EXAMPLE:                                                                                                          ''
''  > abspath = "C:/Users/Kristof/Dropbox/NUCLEO_F303K8/config/buildConfig/linkerscript.ld"                           ''
''      > rootdir = "C:/Users/Kristof/Dropbox/NUCLEO_F303K8"                                                          ''
''      > relpath = "config/buildConfig/linkerscript.ld"                                                              ''
'' ------------------------------------------------------------------------------------------------------------------ ''
"""


def isfile(abspath: str) -> bool:
    """Check for existence of file."""
    if (
        (abspath is None)
        or (abspath.lower() == "none")
        or (not os.path.isfile(abspath))
    ):
        return False
    return True


def standardize_relpath(relpath: str) -> Optional[str]:
    """
    :param   relpath: Non-standardized relpath
    :return: relpath: Standardized relpath (all rules above applied)
    """
    if (relpath is None) or (relpath.lower() == "none"):
        return None
    relpath = relpath.replace("\\", "/")
    # 1. Standardize START
    if relpath == "" or relpath == "." or relpath == "./":
        relpath = "."
    elif relpath.startswith("./"):
        relpath = relpath.replace("./", "", 1)
    elif relpath.startswith("/"):
        relpath = relpath.replace("/", "", 1)
    else:
        pass
    # 2. Standardize END
    if relpath.endswith("/"):
        relpath = relpath[0:-1]
    return relpath


def standardize_abspath(abspath: Optional[str]) -> Optional[str]:
    """
    :param   abspath: Non-standardized abspath
    :return: abspath: Standardized abspath (all rules above applied)
    """
    if (abspath is None) or (abspath.lower() == "none"):
        return None
    abspath = os.path.realpath(abspath).replace("\\", "/")
    if not os.path.isabs(abspath):
        abspath = os.path.realpath(os.path.abspath(abspath)).replace("\\", "/")
    if abspath.endswith("/"):
        abspath = abspath[0:-1]
    return abspath.replace("//", "/")


def standardize_relpath_list(relpath_list: List[Optional[str]]) -> List[str]:
    """Standardize given paths."""
    new_list: List[str] = []
    for path in relpath_list:
        if path is not None:
            standard_path = standardize_relpath(path)
            if standard_path is not None:
                new_list.append(standard_path)
    return new_list


def abs_to_rel(rootpath: str, abspath: str) -> Optional[str]:
    """Convert absolute path to relative path (with respect to the given root
    directory) :param   rootpath: Toplevel folder.

    :param   abspath: Any absolute path.
    :return: relpath: Standardized relative path.
    """
    # os.path.relpath(abspath, start=rootdir)
    if (abspath is None) or (rootpath is None):
        return None

    if isinstance(abspath, str) and abspath.lower() == "none":
        return None

    if isinstance(rootpath, str) and rootpath.lower() == "none":
        return None

    standardized_abspath = standardize_abspath(abspath)
    if (standardized_abspath is None) or (
        standardized_abspath.lower() == "none"
    ):
        return None
    if not standardized_abspath.startswith(rootpath):
        raise RuntimeError(
            f"\nERROR: abs_to_rel(\n"
            f"    rootpath = {q}{rootpath}{q},\n"
            f"    abspath  = {q}{standardized_abspath}{q},\n"
            f")\n"
        )
    relpath = standardized_abspath.replace(rootpath, "", 1)
    standardized_relpath = standardize_relpath(relpath)
    if standardized_relpath is None:
        return ""
    return standardized_relpath


def rel_to_abs(
    rootpath: str,
    relpath: str,
    name: Optional[str] = None,
) -> Optional[str]:
    """Convert relative path to absolute path (with respect to the given root
    directory) :param   rootpath: Toplevel project folder.

    :param   relpath: Any relative path.
    :return: abspath: Standardized absolute path.
    """
    if (relpath is None) or (rootpath is None):
        return None

    if isinstance(relpath, str) and relpath.lower() == "none":
        return None

    if isinstance(rootpath, str) and rootpath.lower() == "none":
        return None

    std_relpath = standardize_relpath(relpath)
    if std_relpath is None:
        return None

    if std_relpath == "." and name is None:
        return rootpath

    abspath = os.path.join(rootpath, std_relpath)
    if name is not None:
        abspath = os.path.join(abspath, name)

    return standardize_abspath(abspath)


def search_dir(
    searchpath: str,
    dirname: str,
    exception: Optional[List[str]] = None,
) -> Optional[str]:
    """Search for the given folder.

    :param searchpath: Absolute path to directory where searching starts.
    :param dirname:    Name of directory to find, or a Unix shell style pattern.
                       Example: 'build*' will match 'buildFolder'.
                       Case insensitive.

    :return:           Absolute path of the found directory.
                       None if nothing found.
    """
    if searchpath is None or dirname is None:
        return None

    if not os.path.isdir(searchpath):
        return None
    dirname = dirname.lower()
    exception = (
        [e.lower() for e in exception] if exception is not None else None
    )
    for root, dirs, files in os.walk(searchpath):
        for name in dirs:
            if _fn_.fnmatch(name=name.lower(), pat=dirname):
                abspath = os.path.join(root, name)
                abspath = cast(str, standardize_abspath(abspath))
                assert isinstance(abspath, str)
                if exception is None:
                    return abspath
                else:
                    exc = False
                    relpath = cast(
                        str, abs_to_rel(rootpath=searchpath, abspath=abspath)
                    )
                    assert isinstance(relpath, str)
                    for e in exception:
                        if e in relpath.lower():
                            exc = True
                    if not exc:
                        return abspath
    return None


def search_file(
    searchpath: str,
    filename: str,
    exception: Optional[List[str]] = None,
) -> Optional[str]:
    """Search for the given file.

    :param searchpath:    Absolute path to directory where searching starts.
    :param filename:      Name of file to find, or a Unix shell style pattern.
                          Example: '*.mk' will match 'dashboard.mk'
                          Case insensitive.

    :return:              Absolute path of the found file.
                          None if nothing found.
    """
    assert os.path.isdir(searchpath)
    filename = filename.lower()
    exception = (
        [e.lower() for e in exception] if exception is not None else None
    )
    for root, dirs, files in os.walk(searchpath):
        for name in files:
            if _fn_.fnmatch(name=name.lower(), pat=filename):
                abspath = os.path.join(root, name)
                abspath = cast(str, standardize_abspath(abspath))
                assert isinstance(abspath, str)
                if exception is None:
                    return abspath
                else:
                    exc = False
                    relpath = cast(
                        str,
                        abs_to_rel(
                            rootpath=searchpath,
                            abspath=abspath,
                        ),
                    )
                    assert isinstance(relpath, str)
                    for e in exception:
                        if e in relpath.lower():
                            exc = True
                    if not exc:
                        return abspath
    return None


def search_file_list(
    searchpath: str,
    filename: str,
    exception: Optional[List[str]] = None,
) -> Optional[List[str]]:
    """Search for multiple files, all ending in the given suffix.

    :param searchpath:    Absolute path to directory where searching starts.
    :param filename:      Name of file to find, or a Unix shell style pattern.
                          Example: "*.mk" will match "dashboard.mk"
                          Case insensitive.
    :param exception:     If this string is present somewhere in the abspath
                          of a file, the file is ignored.
                          Case insensitive.

    :return:              List of absolute paths to the found files.
                          None if nothing found.
    """
    assert os.path.isdir(searchpath)
    filename = filename.lower()
    exception = (
        [e.lower() for e in exception] if exception is not None else None
    )
    filelist = []
    for root, dirs, files in os.walk(searchpath):
        for name in files:
            if _fn_.fnmatch(name=name.lower(), pat=filename):
                abspath = os.path.join(root, name)
                abspath = cast(str, standardize_abspath(abspath))
                assert isinstance(abspath, str)
                if exception is None:
                    filelist.append(abspath)
                else:
                    exc = False
                    for e in exception:
                        if e in abspath:
                            exc = True
                    if not exc:
                        filelist.append(abspath)
    if len(filelist) > 0:
        return filelist
    return None


def list_filepaths(dirpath: str) -> List[str]:
    """List all files from the given directory.

    Contrary to os.listdir(), this function lists the absolute paths.
    """
    dirpath = cast(str, standardize_abspath(dirpath))
    assert isinstance(dirpath, str)
    assert os.path.isdir(dirpath)
    filepaths = []
    for fname in sorted(os.listdir(dirpath)):
        f = rel_to_abs(
            rootpath=dirpath,
            relpath=fname,
        )
        f = os.path.realpath(f).replace("\\", "/").replace("//", "/")
        if not os.path.isfile(f):
            continue
        filepaths.append(f)
    return filepaths


def list_subdirpaths(dirpath: str) -> List[str]:
    """List all subdirs from the given directory.

    Contrary to os.listdir(), this function lists the absolute paths.
    """
    dirpath = standardize_abspath(dirpath)
    assert os.path.isdir(dirpath)
    subdirpaths = []
    for dname in sorted(os.listdir(dirpath)):
        d = rel_to_abs(
            rootpath=dirpath,
            relpath=dname,
        )
        if not os.path.isdir(d):
            continue
        subdirpaths.append(d)
    return subdirpaths
