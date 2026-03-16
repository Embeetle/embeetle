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
import traceback, tempfile, subprocess, os, gc
import purefunctions
import os_checker

q = "'"
dq = '"'


def three_way_merge(
    my_content: str,
    ancestor_content: str,
    your_content: str,
    my_title: str,
    ancestor_title: str,
    your_title: str,
) -> Tuple[Optional[str], bool, Tuple[str, str, str]]:
    """┌────────────────────────────────────────────────────────┐ │ Merge into
    MINE the changes that would turn ANCESTOR   │ │ into YOURS. │
    └────────────────────────────────────────────────────────┘

    NOTE:
    Only file contents are inputted to and outputted from this function. No actual files are being
    read or written (except from temporary files).

    :return:    [str] resulting content
                [bool] has_conflicts
    """
    # * 1. Create temp files with given content
    mine_temp = tempfile.NamedTemporaryFile(delete=False)
    ancestor_temp = tempfile.NamedTemporaryFile(delete=False)
    yours_temp = tempfile.NamedTemporaryFile(delete=False)
    with open(mine_temp.name, "w", encoding="utf-8", newline="\n") as f:
        f.write(my_content)
    with open(ancestor_temp.name, "w", encoding="utf-8", newline="\n") as f:
        f.write(ancestor_content)
    with open(yours_temp.name, "w", encoding="utf-8", newline="\n") as f:
        f.write(your_content)
    my_path = os.path.realpath(mine_temp.name).replace("\\", "/")
    ancestor_path = os.path.realpath(ancestor_temp.name).replace("\\", "/")
    your_path = os.path.realpath(yours_temp.name).replace("\\", "/")

    # * 2. Prepare arguments for GNU 'diff3.exe' tool
    import data

    merge_tool = os.path.join(data.sys_bin, "diff3").replace("\\", "/")
    if os_checker.is_os("windows"):
        merge_tool += ".exe"
    assert os.path.isfile(merge_tool)
    my_env = purefunctions.get_modified_environment(
        [data.sys_lib, data.sys_bin]
    )

    # * 3. Invoke GNU 'diff3.exe' tool
    proc = purefunctions.subprocess_popen(
        [
            merge_tool,
            "-m",
            my_path,
            ancestor_path,
            your_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=my_env,
    )
    try:
        outs, errs = proc.communicate(timeout=15)
    except Exception:
        traceback.print_exc()
        proc.kill()
        outs, errs = proc.communicate()
        return None, True, (my_path, ancestor_path, your_path)

    # * 4. Decode output
    result = outs.decode("utf-8").replace("\r\n", "\n")
    assert isinstance(result, str)
    _result_ = result.replace(my_path, my_title)
    _result_ = _result_.replace(ancestor_path, ancestor_title)
    _result_ = _result_.replace(your_path, your_title)
    del proc
    gc.collect()

    # * 5. Cleanup tempfiles
    try:
        if os.path.isfile(my_path):
            os.remove(my_path)
        if os.path.isfile(ancestor_path):
            os.remove(ancestor_path)
        if os.path.isfile(your_path):
            os.remove(your_path)
    except OSError:
        try:
            if os.path.isfile(my_path):
                os.unlink(my_path)
            if os.path.isfile(ancestor_path):
                os.unlink(ancestor_path)
            if os.path.isfile(your_path):
                os.unlink(your_path)
        except OSError:
            pass
    return _result_, result != _result_, (my_path, ancestor_path, your_path)


# if __name__ == '__main__':
#     # open files a, b, and c (a is the common ancestor)
#     open_success = True
#     # try:
#     #     # note that the merge(ancestor, a, b) function will work on any
#     #     # "list - like" object, including strings and lists. instead of
#     #     # merging the raw strings of characters, we choose to split the
#     #     # text into words and do the merge on that granularity.  this
#     #     # gives more intuitive results.
#     #     a = smart_split(open(sys.argv[1], "r").read())
#     #     c = smart_split(open(sys.argv[2], "r").read())
#     #     b = smart_split(open(sys.argv[3], "r").read())
#     #     open_success = True
#     # except:
#     #     print("error:  unable to open one or more input files")
#     #     open_success = False
#     if open_success:
#         # try to merge
#         try:
#             # since we merged lists of words rather than the raw strings, we
#             # need to join the words back into a string for nice printing
#             #! Use algorithm from Stephan Boyer
#             # print("".join(merge(a, b, c)))
#             #! Use GNU Merge
#             result = three_way_merge(
#                 open(sys.argv[1], "r").read(),
#                 open(sys.argv[2], "r").read(),
#                 open(sys.argv[3], "r").read(),
#             )
#             print(result)
#         # report any conflicts
#         except MergeConflictList as mc:
#             for c in mc.conflicts:
#                 print("conflict:  " + str(c))
