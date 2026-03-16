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
import os, shutil, time, traceback, subprocess, re
import purefunctions, functions, data
import fnmatch as _fn_
import os_checker

nop = lambda *a, **k: None
q = "'"
dq = '"'
"""File and Directory manipulation functions.
=========================================== :param printfunc:   Print function,
should take a string and a color.

:param reporthook: Only for time-consuming functions.
:param catch_err: True -> Catch all errors (and print them out). False -> Let
errors propagate. Don't print them out.
:param overwr: True -> If destination already exists, clean it and overwrite.
False -> If destination already exists, throw OSError().
:return: True  -> Success. False -> Fail.
"""


def native_printfunc(text: str, color: Optional[str] = None) -> None:
    print(text, end="")
    return


# ^                                 SEVENZIP                                   ^#
# % ========================================================================== %#
# % Functions related to zipping and unzipping.                                %#
# %                                                                            %#

__sevenzip_abspath_cache: Optional[str] = None


def get_sevenzip_abspath() -> str:
    """
    Return absolute path to 7zip executable
    """
    global __sevenzip_abspath_cache
    if __sevenzip_abspath_cache:
        return __sevenzip_abspath_cache
    if os_checker.is_os_with_arch("windows-x86_64"):
        __sevenzip_abspath_cache = os.path.join(
            data.sys_bin,
            "7za.exe",
        ).replace("\\", "/")
    elif os_checker.is_os_with_arch("linux-x86_64"):
        __sevenzip_abspath_cache = os.path.join(
            data.sys_bin,
            "7zzs",
        ).replace("\\", "/")
    elif os_checker.is_os_with_arch("macos-x86_64"):
        __sevenzip_abspath_cache = os.path.join(
            data.sys_bin,
            "7zz",
        ).replace("\\", "/")
    elif os_checker.is_os_with_arch("macos-arm64"):
        __sevenzip_abspath_cache = os.path.join(
            data.sys_bin,
            "7zz",
        ).replace("\\", "/")
    else:
        raise RuntimeError(f"OS not recognized")
    if not os.path.isfile(__sevenzip_abspath_cache):
        raise RuntimeError(f"Cannot find {__sevenzip_abspath_cache}")
    return __sevenzip_abspath_cache


def get_sevenzip_rootfoldername(zipfile_abspath: str) -> Optional[str]:
    """Given a 7z-file, return the name of the toplevel directory in the
    zipfile.

    If not found, return None.
    """
    # $ 7zip executable
    sevenzip_abspath = get_sevenzip_abspath()
    # $ PATH variable
    my_env = purefunctions.get_modified_environment(
        [data.sys_lib, data.sys_bin]
    )
    # $ Command
    try:
        commandlist = [
            sevenzip_abspath,
            "l",
            "-slt",
            "-ba",
            zipfile_abspath,
        ]
        output = purefunctions.subprocess_popen(
            commandlist,
            stdout=subprocess.PIPE,
            shell=False,
            env=my_env,
        ).communicate()[0]
    except:
        purefunctions.printc(
            f"ERROR: Cannot inspect zipfile " f"{q}{zipfile_abspath}{q}",
            color="error",
        )
        traceback.print_exc()
        return None
    if output is None:
        return None
    try:
        if isinstance(output, str):
            text = output
        else:
            text = output.decode("utf-8", errors="ignore")
    except:
        traceback.print_exc()
        purefunctions.printc(
            f"ERROR: Cannot determine rootfolder name of zipfile "
            f"{q}{zipfile_abspath}{q}",
            color="error",
        )
        return None
    if text == "":
        return None
    try:
        if os_checker.is_os("windows"):
            p = re.compile(r"Path\s*=\s*([\w\s\d.-]*)\\")
        else:
            p = re.compile(r"Path\s*=\s*([\w\s\d.-]*)/")
        m = p.search(text)
        if m is None:
            return None
        rootname = m.group(1)
    except:
        traceback.print_exc()
        purefunctions.printc(
            f"ERROR: Cannot determine rootfolder name of zipfile "
            f"{q}{zipfile_abspath}{q}",
            color="error",
        )
        return None
    return rootname


def rename_sevenzip_rootfolder(
    zipfile_abspath: str,
    new_name: str,
    printfunc: Optional[Callable] = None,
) -> bool:
    """Given a 7z-file, rename its internal rootfolder.

    If successful, return True.
    """
    if printfunc is None:
        printfunc = native_printfunc
    if zipfile_abspath.endswith(".7z"):
        pass
    elif zipfile_abspath.endswith(".zip"):
        pass
    else:
        raise OSError(
            f"Zipfile at {zipfile_abspath} should "
            f"end with {q}.7z{q} or {q}.zip{q} "
        )
    rootname = get_sevenzip_rootfoldername(zipfile_abspath)
    if rootname is None:
        printfunc(
            f"\n"
            f"WARNING: Cannot extract rootname from:\n"
            f"{q}{zipfile_abspath}{q}\n"
            f"\n",
            f"#fcaf3e",
        )
        return False
    if rootname == new_name:
        return True

    # $ 7zip executable
    sevenzip_abspath = get_sevenzip_abspath()

    # $ PATH variable
    my_env = purefunctions.get_modified_environment(
        [data.sys_lib, data.sys_bin]
    )

    # $ Command
    try:
        commandlist = [
            sevenzip_abspath,
            "rn",
            zipfile_abspath,
            rootname + os.sep,
            new_name + os.sep,
        ]
        output = purefunctions.subprocess_popen(
            commandlist,
            stdout=subprocess.PIPE,
            shell=False,
            env=my_env,
        ).communicate()[0]
    except Exception as e:
        printfunc(
            f"\n"
            f"WARNING: Cannot rename rootfolder in zipfile:\n"
            f"{q}{zipfile_abspath}{q}\n"
            f"\n",
            f"#fcaf3e",
        )
        traceback.print_exc()
        return False
    rootname = get_sevenzip_rootfoldername(zipfile_abspath)
    if rootname == new_name:
        return True
    printfunc(
        f"\n"
        f"WARNING: Failed to rename rootfolder in zipfile:\n"
        f"{q}{zipfile_abspath}{q}\n"
        f"    detected rootfolder name = {q}{rootname}{q}\n"
        f"    desired rootfolder name = {q}{new_name}{q}\n"
        f"\n",
        f"#fcaf3e",
    )
    return False


def sevenzip_dir_to_file(
    sourcedir_abspath: str,  # eg. C:/../myfolder
    targetfile_abspath: str,  # eg. C:/../myfolder.7z
    forbidden_dirnames: Optional[
        List[str]
    ] = None,  # List of dirnames that must be ignored.
    forbidden_filenames: Optional[
        List[str]
    ] = None,  # List of filenames that must be ignored.
    printfunc: Optional[Callable] = None,  # Print output.
    catch_err: bool = True,  # Catch errors.
    overwr: bool = False,  # Overwrite existing zip file.
) -> bool:
    """Make a 7z file from the given 'source_dir'."""
    assert (
        targetfile_abspath.endswith(".zip")
        or targetfile_abspath.endswith(".7z")
        or targetfile_abspath.endswith(".tar.gz")
    )
    # * 1. Print info
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Zip folder:   ", "#edd400")
    printfunc(f"{sourcedir_abspath}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{targetfile_abspath}\n", "#ffffff")

    # * 2. Sanity checks
    # $ 2.1 Check sourcedir exists
    if not os.path.isdir(sourcedir_abspath):
        if catch_err:
            printfunc(
                "\n"
                f"ERROR: Folder {sourcedir_abspath} not found.\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            raise OSError(f"Folder {sourcedir_abspath} not found.")
        return False

    # $ 2.2 Clean targetfile if needed
    def clean_targetfile(_targetfile_abspath_):
        if not os.path.isfile(_targetfile_abspath_):
            return True
        if not overwr:
            if catch_err:
                printfunc(
                    "\n"
                    f"ERROR: Targetfile {q}{_targetfile_abspath_}{q} already exists.\n"
                    f"{traceback.format_exc()}"
                    "\n",
                    "#ef2929",
                )
            else:
                raise OSError(
                    f"Targetfile {q}{_targetfile_abspath_}{q} already exists."
                )
            return False
        try:
            _success = delete_file(
                file_abspath=_targetfile_abspath_,
                printfunc=printfunc,
                catch_err=False,
            )
            if not _success:
                raise OSError()
        except Exception as e:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Targetfile {q}{_targetfile_abspath_}{q} already exists, "
                    f"Embeetle failed to delete it.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise
            return False
        assert _success == True
        return True

    if targetfile_abspath.endswith(".tar.gz"):
        # Clean both '.tar' and '.tar.gz'
        r1 = clean_targetfile(targetfile_abspath.replace(".tar.gz", ".tar"))
        r2 = clean_targetfile(targetfile_abspath)
        if not (r1 and r2):
            return False
    else:
        # Clean only targetfile
        r = clean_targetfile(targetfile_abspath)
        if not r:
            return False

    # At this point:
    #   => sourcedir exists
    #   => targetfile doesn't exist
    assert os.path.isdir(sourcedir_abspath)
    assert not os.path.isfile(targetfile_abspath)

    # $ 2.3 Create parentfolder for targetfile if needed
    targetfile_parentdir = os.path.dirname(targetfile_abspath)
    if not os.path.isdir(targetfile_parentdir):
        try:
            success = make_dir(
                dir_abspath=targetfile_parentdir,
                printfunc=printfunc,
                catch_err=False,
                overwr=False,
            )
            if not success:
                raise OSError()
        except Exception as e:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Failed to make folder {targetfile_parentdir}\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise
            return False

    # * 3. Invoke 7zip
    try:
        # $ 7zip executable
        sevenzip_abspath = get_sevenzip_abspath()
        # $ PATH variable
        my_env = purefunctions.get_modified_environment(
            [data.sys_lib, data.sys_bin]
        )
        # $ Command
        atype = None
        if targetfile_abspath.endswith(".7z"):
            atype = "-t7z"
        elif targetfile_abspath.endswith(".zip"):
            atype = "-tzip"
        elif targetfile_abspath.endswith(".tar"):
            atype = "-ttar"
        elif targetfile_abspath.endswith(".gz"):
            atype = "-tgzip"
        else:
            assert False
        # $ -------- [special treatment for '.tar.gz'] -------- ?#
        if targetfile_abspath.endswith(".tar.gz"):
            # Special treatment
            # $ STEP 1: Make .tar file
            commandlist = [
                sevenzip_abspath,
                "a",  # add files to archive
                "-ttar",  # set type of archive
                "-y",  # assume Yes on all queries
                targetfile_abspath.replace(".tar.gz", ".tar"),
                sourcedir_abspath,
            ]
            if forbidden_dirnames is not None:
                for dirname in forbidden_dirnames:
                    commandlist.append(f"-xr!{dirname}")
            if forbidden_filenames is not None:
                for filename in forbidden_filenames:
                    commandlist.append(f"-xr!{filename}")
            output = purefunctions.subprocess_popen(
                commandlist,
                stdout=subprocess.PIPE,
                shell=False,
                env=my_env,
            ).communicate()[0]
            # $ STEP 2: Make .gz file
            commandlist = [
                sevenzip_abspath,
                "a",  # add files to archive
                "-tgzip",  # set type of archive
                "-y",  # assume Yes on all queries
                targetfile_abspath,
                targetfile_abspath.replace(".tar.gz", ".tar"),
            ]
            output = purefunctions.subprocess_popen(
                commandlist,
                stdout=subprocess.PIPE,
                shell=False,
                env=my_env,
            ).communicate()[0]
            # $ STEP 3: Delete .tar file
            success = delete_file(
                file_abspath=targetfile_abspath.replace(".tar.gz", ".tar"),
                printfunc=printfunc,
                catch_err=False,
            )
            if not success:
                return False
        # $ -------- [General] -------- ?#
        else:
            commandlist = [
                sevenzip_abspath,
                "a",  # add files to archive
                atype,  # set type of archive
                "-y",  # assume Yes on all queries
                targetfile_abspath,
                sourcedir_abspath,
            ]
            if forbidden_dirnames is not None:
                for dirname in forbidden_dirnames:
                    commandlist.append(f"-xr!{dirname}")
            if forbidden_filenames is not None:
                for filename in forbidden_filenames:
                    commandlist.append(f"-xr!{filename}")
            output = purefunctions.subprocess_popen(
                commandlist,
                stdout=subprocess.PIPE,
                shell=False,
                env=my_env,
            ).communicate()[0]
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Failed to zip {sourcedir_abspath}.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def sevenunzip_file_to_dir(
    sourcefile_abspath: str,
    targetdir_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
    protocol: str = ".7z",
) -> bool:
    """Unzip given 7z file at 'sourcefile_abspath' to the directory at
    'targetdir_abspath'.

    The zipfile ============     > sourcefile_abspath 'C:/foo/bar/archive.7z'

    The target directory =====================     > targetdir_abspath
    'C:/egg/bacon/spam'     > targetparent_abspath      'C:/egg/bacon'     >
    targetdir_basename        'spam'

    The archive rootname =======================     > archive_rootname
    'archive_root'
    """
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    assert (protocol == ".7z") or (protocol == ".zip")

    def print_error_msg(_msg, errno, *args):
        printfunc(
            f"sevenunzip_file_to_dir(\n"
            f"    sourcefile_abspath = {q}{sourcefile_abspath}{q},\n"
            f"    targetdir_abspath  = {q}{targetdir_abspath}{q},\n"
            f"    printfunc          = {printfunc},\n"
            f"    catch_err          = {catch_err},\n"
            f"    overwr             = {overwr},\n"
            f"    protocol           = {q}{protocol}{q},\n"
            f")\n"
            f"errno: {errno}\n",
            "#ef2929",
        )
        print(
            f"sevenunzip_file_to_dir(\n"
            f"    sourcefile_abspath = {q}{sourcefile_abspath}{q},\n"
            f"    targetdir_abspath  = {q}{targetdir_abspath}{q},\n"
            f"    printfunc          = {printfunc},\n"
            f"    catch_err          = {catch_err},\n"
            f"    overwr             = {overwr},\n"
            f"    protocol           = {q}{protocol}{q},\n"
            f")\n"
            f"errno: {errno}\n",
            "#ef2929",
        )
        printfunc(f"ERROR MESSAGE:\n" f"{_msg}\n")
        purefunctions.printc(
            f"ERROR MESSAGE:\n" f"{_msg}\n",
            color="error",
        )
        return

    #! The zipfile !#
    #! =========== !#
    # Make sure that the sourcefile ends in .7z or .zip
    sourcefile_abspath = os.path.realpath(sourcefile_abspath).replace("\\", "/")
    try:
        if sourcefile_abspath.endswith(".7z"):
            assert protocol == ".7z"
        elif sourcefile_abspath.endswith(".zip"):
            assert protocol == ".zip"
        else:
            success = rename_file(
                sourcefile_abspath=sourcefile_abspath,
                targetname=sourcefile_abspath + protocol,
                printfunc=printfunc,
                catch_err=False,
                overwr=False,
            )
            if not success:
                msg = str(
                    f"Could not rename file such that it ends with {q}.7z{q} or "
                    f"with {q}.zip{q}"
                )
                print_error_msg(msg, 1)
                if not catch_err:
                    raise OSError(msg)
                return False
            sourcefile_abspath += protocol
    except:
        msg = str(
            f"Cannot add {q}{protocol}{q} extension "
            f"to {q}{sourcefile_abspath}{q}\n"
            f"{traceback.format_exc()}\n"
        )
        print_error_msg(msg, 2)
        if not catch_err:
            raise
        return False

    if not (
        sourcefile_abspath.endswith(".7z")
        or sourcefile_abspath.endswith(".zip")
    ):
        msg = str(
            f"Cannot add {q}{protocol}{q} extension "
            f"to {q}{sourcefile_abspath}{q}\n"
            f"{traceback.format_exc()}\n"
        )
        print_error_msg(msg, 3)
        if not catch_err:
            raise OSError(msg)
        return False

    #! The target directory !#
    #! ==================== !#
    targetdir_abspath = os.path.realpath(targetdir_abspath).replace("\\", "/")
    targetparent_abspath = os.path.dirname(targetdir_abspath)
    targetdir_basename = None

    #! The 7zip software !#
    #! ================= !#
    # $ 7zip executable
    try:
        sevenzip_abspath = get_sevenzip_abspath()
    except:
        msg = str(f"Cannot find 7zip executable")
        print_error_msg(msg, 4)
        if not catch_err:
            raise OSError(msg)
        return False
    # $ PATH variable
    my_env = purefunctions.get_modified_environment(
        [data.sys_lib, data.sys_bin]
    )

    #! Start procedure !#
    #! =============== !#
    # * Sanitize input
    if targetdir_abspath.endswith("/"):
        targetdir_abspath = targetdir_abspath[0:-1]
    if targetparent_abspath.endswith("/"):
        targetparent_abspath = targetparent_abspath[0:-1]
    targetdir_basename = targetdir_abspath.split("/")[-1]

    # * Print input
    printfunc(f"Unzip file:   ", "#edd400")
    printfunc(f"{sourcefile_abspath}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{targetdir_abspath}\n", "#ffffff")

    # * Check zipfile => should exist
    if not os.path.isfile(sourcefile_abspath):
        msg = f"Zipfile {q}{sourcefile_abspath}{q} not found.\n"
        print_error_msg(msg, 5)
        if not catch_err:
            raise OSError(msg)
        return False

    # * Check targetdir => should not exist
    if os.path.isdir(targetdir_abspath):
        if not overwr:
            msg = str(
                f"Target directory {q}{targetdir_abspath}{q} already exists.\n"
            )
            print_error_msg(msg, 6)
            if not catch_err:
                raise OSError(msg)
            return False
        try:
            success = delete_dir(
                dir_abspath=targetdir_abspath,
                printfunc=nop,
                catch_err=False,
            )
            if not success:
                msg = str(f"Failed to delete folder {q}{targetdir_abspath}{q}")
                print_error_msg(msg, 7)
                if not catch_err:
                    raise OSError(msg)
                return False
        except Exception as e:
            msg = str(
                f"Target directory {targetdir_abspath} already exists, "
                f"Embeetle failed to delete it.\n"
                f"{traceback.format_exc()}\n"
            )
            print_error_msg(msg, 8)
            if not catch_err:
                raise
            return False

    # * Check targetparent => should exist
    if not os.path.isdir(targetparent_abspath):
        try:
            success = make_dir(
                dir_abspath=targetparent_abspath,
                printfunc=printfunc,
                catch_err=False,
                overwr=False,
            )
            if not success:
                msg = str(
                    f"Failed to create folder {q}{targetparent_abspath}{q}"
                )
                print_error_msg(msg, 9)
                if not catch_err:
                    raise OSError(msg)
                return False
        except Exception as e:
            msg = str(
                f"Failed to create folder {q}{targetparent_abspath}{q}"
                f"{traceback.format_exc()}\n"
            )
            print_error_msg(msg, 10)
            if not catch_err:
                raise
            return False

    assert os.path.isfile(sourcefile_abspath)
    assert os.path.isdir(targetparent_abspath)
    assert not os.path.isdir(targetdir_abspath)

    # * Rename rootfolder
    # The rootfolder name should be the same as the zipfile's basename. If not,
    # try to rename it.
    rootfolder_name_correct = False
    try:
        success = rename_sevenzip_rootfolder(
            zipfile_abspath=sourcefile_abspath,
            new_name=targetdir_basename,
            printfunc=printfunc,
        )
        if not success:
            printfunc(
                f"Continue without renaming rootfolder...\n\n",
                "#ffffff",
            )
        rootfolder_name_correct = success
    except Exception as e:
        msg = str(
            f"Cannot rename rootfolder inside {q}{sourcefile_abspath}{q}.\n"
            f"{traceback.format_exc()}\n"
        )
        print_error_msg(msg, 11)
        printfunc(
            f"Continue without renaming rootfolder...\n\n",
            "#ffffff",
        )

    # * Unzip
    try:
        printfunc(
            "Unzipping, please wait ...\n",
            "#fce94f",
        )
        # We had a problem earlier on D:/ drives on Windows. The `f'-o{targetparent_abspath}'`
        # parameter wouldn't work with forward slashes. The proposed solution was to add quotes
        # around the path: f'-o"{targetparent_abspath}"', but that didn't resolve the issue.
        # Instead, converting forward slashes to backward slashes for Windows paths worked:
        # f'-o{targetparent_abspath.replace('/', '\\\\')}'
        # Let's analyze this approach:
        # 1. On Windows:
        #   - Windows command line tools typically expect paths with backslashes
        #   - Forward slashes sometimes work but can be problematic with certain tools like 7zip
        #     when used with drive letters (e.g., D:/)
        #   - Converting to backslashes ensures Windows tools interpret the path correctly
        #   - We need to escape backslashes in Python strings (hence the quadruple backslashes)
        # 2. On Linux:
        #   - Linux uses forward slashes as the standard path separator
        #   - No conversion is needed since it works as expected with forward slashes
        # This approach handles the platform differences correctly:
        # - For Windows: Convert forward slashes to backslashes
        # - For Linux: Keep forward slashes as is
        # Make sure target parent directory exists
        os.makedirs(targetparent_abspath, exist_ok=True)

        if os_checker.is_os("windows"):
            commandlist = [
                sevenzip_abspath,
                "x",
                "-y",
                f"{sourcefile_abspath}",
                f'-o{targetparent_abspath.replace('/', '\\\\')}',
            ]
        else:
            commandlist = [
                sevenzip_abspath,
                "x",
                "-y",
                f"{sourcefile_abspath}",
                f"-o{targetparent_abspath}",
            ]
        output = purefunctions.subprocess_popen(
            commandlist,
            stdout=subprocess.PIPE,
            shell=False,
            env=my_env,
            verbose=True,
        ).communicate()[0]
        if output is not None:
            printfunc(
                output.decode("utf-8", errors="ignore"),
                "#ffffff",
            )
    except:
        msg = str(
            f"Cannot unzip {q}{sourcefile_abspath}{q}.\n"
            f"{traceback.format_exc()}\n"
        )
        print_error_msg(msg, 12)
        if not catch_err:
            raise
        return False

    # * Check created folder
    # Rootfolder has right name
    if rootfolder_name_correct:
        if os.path.isdir(targetdir_abspath):
            return True
        msg = str(
            f"Unzipping {q}{sourcefile_abspath}{q} failed, "
            f"targetdir_abspath = {q}{targetdir_abspath}{q} not "
            f"found!"
        )
        print_error_msg(msg, 13)
        if not catch_err:
            raise OSError(msg)
        return False
    # Rootfolder has wrong name
    rootfolder_name: Optional[str] = get_sevenzip_rootfoldername(
        sourcefile_abspath
    )
    if rootfolder_name is None:
        msg = str(f"Unzipping {q}{sourcefile_abspath}{q} failed, ")
        print_error_msg(msg, 14)
        if not catch_err:
            raise OSError(msg)
        return False
    rootfolder_abspath = os.path.join(
        targetparent_abspath,
        rootfolder_name,
    ).replace("\\", "/")
    if not os.path.isdir(rootfolder_abspath):
        msg = str(f"Unzipping {q}{sourcefile_abspath}{q} failed, ")
        print_error_msg(msg, 15)
        if not catch_err:
            raise OSError(msg)
        return False
    success = rename_dir(
        sourcedir_abspath=rootfolder_abspath,
        targetname=targetdir_abspath,
        printfunc=printfunc,
        catch_err=catch_err,
        overwr=overwr,
    )
    if success:
        return True
    return False


def make_file(
    file_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Make file at given location 'file_abspath'."""
    # print(f"$$$ make_file({file_abspath})")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Make file:    ", "#edd400")
    printfunc(f"{file_abspath}\n", "#ffffff")

    if os.path.exists(file_abspath):
        if overwr:
            try:
                delete(file_abspath, printfunc=None, catch_err=False)
            except:
                if catch_err:
                    printfunc(
                        f"\n"
                        f"ERROR: Cannot delete existing file {q}{file_abspath}{q}\n"
                        f"{traceback.format_exc()}"
                        f"\n",
                        "#ef2929",
                    )
                else:
                    raise
                return False
        else:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: File {q}{file_abspath}{q} already exists.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise OSError(f"ERROR: File {file_abspath} already exists.")
            return False
    try:
        parentdir = os.path.dirname(file_abspath).replace("\\", "/")
        if not os.path.isdir(parentdir):
            s = make_dir(
                dir_abspath=parentdir,
                printfunc=printfunc,
                catch_err=catch_err,
                overwr=overwr,
            )
            if not s:
                return False
        with open(file_abspath, "w", encoding="utf-8", newline="\n") as f:
            f.write("")
    except:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Cannot make file {q}{file_abspath}{q}\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def make_dir(
    dir_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Make directory at given location 'dir_abspath'."""
    # print(f"$$$ make_dir({dir_abspath})")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Make folder:  ", "#edd400")
    printfunc(f"{dir_abspath}\n", "#ffffff")

    if os.path.exists(dir_abspath):
        if overwr:
            try:
                delete(dir_abspath, printfunc=None, catch_err=False)
            except Exception as e:
                if catch_err:
                    printfunc(
                        f"\n"
                        f"ERROR: Cannot delete existing folder {q}{dir_abspath}{q}\n"
                        f"{traceback.format_exc()}"
                        f"\n",
                        "#ef2929",
                    )
                else:
                    raise
                return False
        else:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Folder {q}{dir_abspath}{q} already exists.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise OSError(
                    f"ERROR: Folder {q}{dir_abspath}{q} already exists."
                )
            return False
    try:
        os.makedirs(dir_abspath)
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Cannot make folder {q}{dir_abspath}{q}\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def clean_dir(
    dir_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
) -> bool:
    """Clean existing directory.

    Note:   If directory doesn't exist, throw OSError().
    """
    # print(f"$$$ clean_dir({dir_abspath})")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Clean folder: ", "#edd400")
    printfunc(f"{dir_abspath}\n", "#ffffff")

    if not os.path.isdir(dir_abspath):
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Folder {q}{dir_abspath}{q} does not exist.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise OSError(
                f"ERROR: Folder {q}{dir_abspath}{q} does not exist.\n"
            )
        return False
    try:
        for e in os.listdir(dir_abspath):
            delete(
                item_abspath=os.path.join(dir_abspath, e).replace("\\", "/"),
                printfunc=None,
                catch_err=False,
            )
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Cannot clean {q}{dir_abspath}{q}\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def move_dir(
    sourcedir_abspath: str,
    targetdir_abspath: str,
    exclusions: Optional[List[str]] = None,
    reporthook: Optional[Callable] = None,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """
    :param exclusions: List of folder- and/or filenames that should be excluded
                       from the copy. Each entry in this list gets fnmatch()-ed
                       against filenames and directory names while traversing
                       the source folder:
                           - filename match   => file gets ignored
                           - foldername match => folder and its content gets
                                                 ignored

    :param reporthook: If reporthook is provided, it gets stuffed with:
                       (i , n)  > i = file nr copied
                                > n = total nr of files

    """
    # print(f"$$$ move_dir({sourcedir_abspath}, {targetdir_abspath})")
    if exclusions is not None:
        raise RuntimeError(
            "providing exclusions to move_dir() function not yet supported."
        )
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Move folder:  ", "#edd400")
    printfunc(f"{sourcedir_abspath}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{targetdir_abspath}\n", "#ffffff")
    if sourcedir_abspath.lower() == targetdir_abspath.lower():
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: The source and destination paths point to the same folder!\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    try:
        success = copy_dir(
            sourcedir_abspath=sourcedir_abspath,
            targetdir_abspath=targetdir_abspath,
            reporthook=reporthook,
            exclusions=exclusions,
            printfunc=None,
            catch_err=False,
            overwr=overwr,
        )
        if not success:
            raise OSError()
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Failed to copy {q}{sourcedir_abspath}{q} to "
                f"{q}{targetdir_abspath}{q}\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    try:
        success = delete_dir(
            dir_abspath=sourcedir_abspath,
            printfunc=None,
            catch_err=False,
        )
        if not success:
            raise OSError()
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Failed to delete {q}{sourcedir_abspath}{q} "
                f"after finishing the copy.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def copy_dir(
    sourcedir_abspath: str,
    targetdir_abspath: str,
    exclusions: Optional[List[str]] = None,
    reporthook: Optional[Callable] = None,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Copy directory.

    :param exclusions: List of folder- and/or filenames that should be excluded
                       from the copy. Each entry in this list gets fnmatch()-ed
                       against filenames and directory names while traversing
                       the source folder:
                           - filename match   => file gets ignored
                           - foldername match => folder and its content gets
                                                 ignored

    :param reporthook: If reporthook is provided, it gets stuffed with:
                       (i , n)  > i = file nr copied
                                > n = total nr of files
    """
    # * Print operation
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Copy folder:  ", "#edd400")
    printfunc(f"{q}{sourcedir_abspath}{q}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{q}{targetdir_abspath}{q}\n", "#ffffff")
    if os_checker.is_os("linux"):
        sourcedir_abspath = os.path.expanduser(sourcedir_abspath).replace(
            "\\", "/"
        )
        targetdir_abspath = os.path.expanduser(targetdir_abspath).replace(
            "\\", "/"
        )

    def normal_copy():
        """Run this function if reporthook is None."""
        if exclusions is not None:
            raise RuntimeError(
                "Providing exclusions to copy_dir() function "
                "without reporthook not yet supported."
            )
        # $ Target folder exists
        if os.path.exists(targetdir_abspath):
            if overwr:
                try:
                    delete(
                        item_abspath=targetdir_abspath,
                        printfunc=None,
                        catch_err=False,
                    )
                except Exception as e:
                    if catch_err:
                        printfunc(
                            f"\n"
                            f"ERROR: Cannot delete existing folder "
                            f"{q}{targetdir_abspath}{q}\n"
                            f"{traceback.format_exc()}"
                            f"\n",
                            "#ef2929",
                        )
                    else:
                        raise
                    return False
            else:
                if catch_err:
                    printfunc(
                        f"\n"
                        f"ERROR: Folder {q}{targetdir_abspath}{q} already exists.\n"
                        f"{traceback.format_exc()}"
                        f"\n",
                        "#ef2929",
                    )
                else:
                    raise OSError(
                        f"ERROR: Folder {q}{targetdir_abspath}{q} already exists."
                    )
                return False
        # $ Copy operation
        try:
            shutil.copytree(
                src=sourcedir_abspath,
                dst=targetdir_abspath,
                symlinks=True,
            )
        except Exception as e:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Failed to copy {sourcedir_abspath} to "
                    f"{q}{targetdir_abspath}{q}.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise
            return False
        return True

    def report_copy():
        """Run this function if `reporthook is not None`."""
        # $ Target folder exists
        if os.path.isdir(targetdir_abspath):
            if overwr:
                try:
                    clean_dir(
                        dir_abspath=targetdir_abspath,
                        printfunc=None,
                        catch_err=False,
                    )
                except Exception as e:
                    if catch_err:
                        printfunc(
                            f"\n"
                            f"ERROR: Cannot clean existing folder "
                            f"{q}{targetdir_abspath}{q}\n"
                            f"{traceback.format_exc()}"
                            f"\n",
                            "#ef2929",
                        )
                    else:
                        raise
                    return False
            else:
                if catch_err:
                    printfunc(
                        f"\n"
                        f"ERROR: Folder {q}{targetdir_abspath}{q} already "
                        f"exists.\n"
                        f"{traceback.format_exc()}"
                        f"\n",
                        "#ef2929",
                    )
                else:
                    raise OSError(
                        f"ERROR: Folder {q}{targetdir_abspath}{q} already "
                        f"exists."
                    )
                return False
        # $ Copy operation
        try:
            if exclusions is not None:
                n = 0
                for dirpath, dirs, files in os.walk(sourcedir_abspath):
                    dirs[:] = [
                        d
                        for d in dirs
                        if not any(
                            _fn_.fnmatch(name=d, pat=p) for p in exclusions
                        )
                    ]
                    files[:] = [
                        f
                        for f in files
                        if not any(
                            _fn_.fnmatch(name=f, pat=p) for p in exclusions
                        )
                    ]
                    n += len(files)
            else:
                n = sum([len(f) for r, d, f in os.walk(sourcedir_abspath)])
            i = 0
            for dirpath, dirs, files in os.walk(sourcedir_abspath):
                if exclusions is not None:
                    dirs[:] = [
                        d
                        for d in dirs
                        if not any(
                            _fn_.fnmatch(name=d, pat=p) for p in exclusions
                        )
                    ]
                    files[:] = [
                        f
                        for f in files
                        if not any(
                            _fn_.fnmatch(name=f, pat=p) for p in exclusions
                        )
                    ]
                sourcedirpath = dirpath.replace("\\", "/")
                targetdirpath = sourcedirpath.replace(
                    sourcedir_abspath,
                    targetdir_abspath,
                    1,
                )
                elist = targetdirpath.split("/")
                epath = elist[0]
                if epath.endswith(":"):
                    epath += "/"
                del elist[0]
                if epath == "":
                    epath = elist[0]
                    del elist[0]
                    epath = "/" + epath
                for folder_name in elist:
                    epath = os.path.join(epath, folder_name).replace("\\", "/")
                    if not os.path.isdir(epath):
                        make_dir(
                            dir_abspath=epath,
                            printfunc=None,
                            catch_err=False,
                        )
                for f in files:
                    sourcefilepath = os.path.join(sourcedirpath, f).replace(
                        "\\", "/"
                    )
                    targetfilepath = os.path.join(targetdirpath, f).replace(
                        "\\", "/"
                    )
                    copy_file(
                        sourcefile_abspath=sourcefilepath,
                        targetfile_abspath=targetfilepath,
                        printfunc=None,
                        catch_err=False,
                    )
                    i += 1
                    reporthook(i, n)
        except Exception as e:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Failed to copy {q}{sourcedir_abspath}{q} to "
                    f"{q}{targetdir_abspath}{q}.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise
            return False
        return True

    if reporthook is None:
        return normal_copy()
    return report_copy()


def move_file(
    sourcefile_abspath: str,
    targetfile_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """"""
    # print(f"$$$ move_file({sourcefile_abspath}, {targetfile_abspath})")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Move file:  ", "#edd400")
    printfunc(f"{q}{sourcefile_abspath}{q}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{q}{targetfile_abspath}{q}\n", "#ffffff")
    if sourcefile_abspath.lower() == targetfile_abspath.lower():
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: The source and destination paths "
                f"point to the same file!\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    try:
        success = copy_file(
            sourcefile_abspath=sourcefile_abspath,
            targetfile_abspath=targetfile_abspath,
            printfunc=None,
            catch_err=False,
            overwr=overwr,
        )
        if not success:
            raise OSError()
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Failed to copy {q}{sourcefile_abspath}{q} to "
                f"{q}{targetfile_abspath}{q}\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            raise
        return False
    try:
        success = delete_file(
            file_abspath=sourcefile_abspath,
            printfunc=None,
            catch_err=False,
        )
        if not success:
            raise OSError()
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Failed to delete {q}{sourcefile_abspath}{q} after "
                f"finishing the copy.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def copy_file(
    sourcefile_abspath: str,
    targetfile_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Copy file, source and destination are both given as complete and absolute
    filepaths."""
    # print(f"$$$ copy_file({sourcefile_abspath}, {targetfile_abspath})")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Copy file:    ", "#edd400")
    printfunc(f"{sourcefile_abspath}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{targetfile_abspath}\n", "#ffffff")

    if os.path.exists(targetfile_abspath):
        if overwr:
            try:
                delete(targetfile_abspath, printfunc=None, catch_err=False)
            except Exception as e:
                if catch_err:
                    printfunc(
                        f"\n"
                        f"ERROR: Cannot delete existing file "
                        f"{q}{targetfile_abspath}{q}\n"
                        f"{traceback.format_exc()}"
                        f"\n",
                        "#ef2929",
                    )
                else:
                    raise
                return False
        else:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: File {q}{targetfile_abspath}{q} already exists.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise OSError(
                    f"File {q}{targetfile_abspath}{q} already exists."
                )
            return False

    targetparent = os.path.dirname(targetfile_abspath)
    if not os.path.isdir(targetparent):
        try:
            success = make_dir(
                targetparent,
                printfunc=None,
                catch_err=False,
                overwr=False,
            )
            if not success:
                raise OSError()
        except Exception as e:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Cannot create parent directory "
                    f"{q}{targetparent}{q}\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise OSError(
                    f"Cannot create parent directory {q}{targetparent}{q}\n"
                )
            return False

    try:
        shutil.copy2(sourcefile_abspath, targetfile_abspath)
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Failed to copy {q}{sourcefile_abspath}{q} to "
                f"{q}{targetfile_abspath}{q}.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def copy_file_into_dir(
    sourcefile_abspath: str,
    targetdir_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Copy file, source location is a complete and absolute filepath.

    Destination location is an absolute directory path. The name of the copy is
    taken from the source file.
    """
    # print(f"$$$ copy_file_into_dir({sourcefile_abspath}, {targetdir_abspath})")
    sourcefile_abspath = sourcefile_abspath.replace("\\", "/")
    targetdir_abspath = targetdir_abspath.replace("\\", "/")
    targetfile_abspath = os.path.join(
        targetdir_abspath, sourcefile_abspath.split("/")[-1]
    ).replace("\\", "/")
    return copy_file(
        sourcefile_abspath=sourcefile_abspath,
        targetfile_abspath=targetfile_abspath,
        printfunc=printfunc,
        catch_err=catch_err,
        overwr=overwr,
    )


def rename_file(
    sourcefile_abspath: str,
    targetname: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Rename file, 'targetname' can be just the filename or a full path."""
    # print(f"$$$ rename_file({sourcefile_abspath})")
    sourcefile_abspath = sourcefile_abspath.replace("\\", "/")
    targetname = targetname.replace("\\", "/")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Rename file:  ", "#edd400")
    printfunc(f"{sourcefile_abspath}\n", "#ffffff")
    printfunc(f"To:           ", "#edd400")
    printfunc(f"{targetname}\n", "#ffffff")
    if not os.path.isfile(sourcefile_abspath):
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: File {q}{sourcefile_abspath}{q} does not exist.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise OSError(
                f"ERROR: File {q}{sourcefile_abspath}{q} does not exist.\n"
            )
        return False
    targetfile_abspath = None
    if "/" in targetname:
        targetfile_abspath = targetname
    else:
        targetfile_abspath = os.path.join(
            os.path.dirname(sourcefile_abspath), targetname
        ).replace("\\", "/")
    if os.path.exists(targetfile_abspath):
        if overwr:
            try:
                delete(targetfile_abspath, printfunc=None, catch_err=False)
            except Exception as e:
                if catch_err:
                    printfunc(
                        "\n"
                        f"ERROR: Cannot delete existing file "
                        f"{q}{targetfile_abspath}{q}\n"
                        f"{traceback.format_exc()}"
                        "\n",
                        "#ef2929",
                    )
                else:
                    raise
                return False
        else:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: File {q}{targetfile_abspath}{q} already exists.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                raise OSError(
                    f"ERROR: File {q}{targetfile_abspath}{q} already exists."
                )
            return False
    try:
        os.rename(sourcefile_abspath, targetfile_abspath)
    except Exception as e:
        if catch_err:
            printfunc(
                "\n"
                f"ERROR: Cannot rename file {q}{sourcefile_abspath}{q} into "
                f"{q}{targetfile_abspath}{q}\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def rename_dir(
    sourcedir_abspath: str,
    targetname: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    overwr: bool = False,
) -> bool:
    """Rename directory at 'sourcedir_abspath'.

    :param sourcedir_abspath:   Absolute path to directory that must be renamed.

    :param targetname:          New name for the directory. This parameter can
                                simply be the name, but you can also pass an
                                absolute path.

    :param printfunc:           Pass a function that can printout stuff. Default
                                value is None, so nothing is printed.

    :param catch_err:           True -> Errors will be catched, and an their
                                        error messages are printed out through
                                        the printfunc you passed (if any). There
                                        is no error propagation.

                                False -> Errors are not catched. They are left
                                         to propagate to the calling function.

    :param overwr:              If the target directory (the directory that will
                                exist after the renaming) already exists, then
                                it will be cleaned if (overwr == True).
                                If (overwr == False), an error is thrown.

    Note:   Set the CWD to one directory level up, because Python locks
            the CWD (at least on Windows), which prevents renaming!
            Afterwards, attempt to set CWD back.
    """
    # print(f"$$$ rename_dir({sourcedir_abspath}, {targetname})")
    sourcedir_abspath = sourcedir_abspath.replace("\\", "/")
    targetname = targetname.replace("\\", "/")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Rename folder: ", "#edd400")
    printfunc(f"{q}{sourcedir_abspath}{q}\n", "#ffffff")
    printfunc(f"To:            ", "#edd400")
    printfunc(f"{q}{targetname}{q}\n", "#ffffff")
    if not os.path.isdir(sourcedir_abspath):
        if catch_err:
            printfunc(
                "\n"
                f"ERROR: Folder {q}{sourcedir_abspath}{q} does not exist.\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            raise OSError(
                f"ERROR: Folder {q}{sourcedir_abspath}{q} does not exist.\n"
            )
        return False
    cwd = os.getcwd()
    os.chdir(functions.unixify_path_join(sourcedir_abspath, ".."))
    targetdir_abspath = None
    if "/" in targetname:
        targetdir_abspath = targetname
    else:
        targetdir_abspath = os.path.join(
            os.path.dirname(sourcedir_abspath),
            targetname,
        ).replace("\\", "/")
    if os.path.exists(targetdir_abspath):
        if overwr:
            try:
                delete(
                    item_abspath=targetdir_abspath,
                    printfunc=None,
                    catch_err=False,
                )
            except Exception as e:
                if catch_err:
                    printfunc(
                        f"\n"
                        f"ERROR: Cannot delete existing folder "
                        f"{q}{targetdir_abspath}{q}\n"
                        f"{traceback.format_exc()}"
                        f"\n",
                        "#ef2929",
                    )
                else:
                    if os.path.isdir(cwd):
                        os.chdir(functions.unixify_path(cwd))
                    raise
                (
                    os.chdir(functions.unixify_path(cwd))
                    if os.path.isdir(cwd)
                    else nop()
                )
                return False
        else:
            if catch_err:
                printfunc(
                    f"\n"
                    f"ERROR: Folder {q}{targetdir_abspath}{q} already exists.\n"
                    f"{traceback.format_exc()}"
                    f"\n",
                    "#ef2929",
                )
            else:
                if os.path.isdir(cwd):
                    os.chdir(functions.unixify_path(cwd))
                raise OSError(
                    f"ERROR: Folder {q}{targetdir_abspath}{q} already exists."
                )
            if os.path.isdir(cwd):
                os.chdir(functions.unixify_path(cwd))
            return False
    try:
        os.rename(sourcedir_abspath, targetdir_abspath)
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Cannot rename folder {q}{sourcedir_abspath}{q} "
                f"into {q}{targetdir_abspath}{q}\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            if os.path.isdir(cwd):
                os.chdir(functions.unixify_path(cwd))
            raise
        if os.path.isdir(cwd):
            os.chdir(functions.unixify_path(cwd))
        return False
    if os.path.isdir(cwd):
        os.chdir(functions.unixify_path(cwd))
    return True


def delete_dir(
    dir_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
    allow_rootpath_deletion: bool = False,
) -> bool:
    """Delete directory.

    Note:   Set the CWD to one directory level up, because Python locks
            the CWD (at least on Windows), which prevents renaming!
            Afterwards, attempt to set CWD back.
    """
    dir_abspath = dir_abspath.replace("\\", "/")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Delete folder: ", "#edd400")
    printfunc(f"{q}{dir_abspath}{q}\n", "#ffffff")

    if not functions.allowed_to_delete_folder(
        abspath=dir_abspath,
        allow_rootpath_deletion=allow_rootpath_deletion,
    ):
        if catch_err:
            printfunc(
                "\n"
                f"ERROR: Folder {q}{dir_abspath}{q} is too important to delete.\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            raise OSError(
                f"ERROR: Folder {q}{dir_abspath}{q} is too important to delete.\n"
            )
        return False
    if not os.path.isdir(dir_abspath):
        if catch_err:
            printfunc(
                "\n"
                f"ERROR: Folder {q}{dir_abspath}{q} does not exist.\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            raise OSError(
                f"ERROR: Folder {q}{dir_abspath}{q} does not exist.\n"
            )
        return False
    cwd = os.getcwd()
    os.chdir(functions.unixify_path_join(dir_abspath, ".."))
    try:
        shutil.rmtree(dir_abspath)
    except Exception as e:
        if catch_err:
            printfunc(
                "\n"
                f"ERROR: Cannot delete folder {q}{dir_abspath}{q}\n"
                f"{traceback.format_exc()}"
                "\n",
                "#ef2929",
            )
        else:
            if os.path.isdir(cwd):
                os.chdir(functions.unixify_path(cwd))
            raise
        if os.path.isdir(cwd):
            os.chdir(functions.unixify_path(cwd))
        return False
    if os.path.isdir(cwd):
        os.chdir(functions.unixify_path(cwd))
    return True


def delete_file(
    file_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
) -> bool:
    """Delete file."""
    # print(f"$$$ delete_file({file_abspath})")
    file_abspath = file_abspath.replace("\\", "/")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    printfunc(f"Delete file:   ", "#edd400")
    printfunc(f"{q}{file_abspath}{q}\n", "#ffffff")

    if not os.path.isfile(file_abspath):
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: File {file_abspath} does not exist.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise OSError(f"ERROR: File {q}{file_abspath}{q} does not exist.\n")
        return False
    try:
        os.remove(file_abspath)
    except Exception as e:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Cannot delete file {file_abspath}\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise
        return False
    return True


def delete(
    item_abspath, printfunc: Optional[Callable] = None, catch_err: bool = True
) -> bool:
    """Delete file or folder at 'item_abspath'."""
    # print(f"$$$ delete({item_abspath})")
    item_abspath = item_abspath.replace("\\", "/")
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    if os.path.isfile(item_abspath):
        return delete_file(
            item_abspath, printfunc=printfunc, catch_err=catch_err
        )
    elif os.path.isdir(item_abspath):
        return delete_dir(
            item_abspath, printfunc=printfunc, catch_err=catch_err
        )
    else:
        if catch_err:
            printfunc(
                f"\n"
                f"ERROR: Item {q}{item_abspath}{q} does not exist.\n"
                f"{traceback.format_exc()}"
                f"\n",
                "#ef2929",
            )
        else:
            raise OSError(f"ERROR: Item {q}{item_abspath}{q} does not exist.\n")
        return False
    assert False


def print_dir_content(abspath: str) -> None:
    """Print contents of a directory with formatting."""
    print(f"    >>> ")
    print(f"    >>> CONTENTS OF DIRECTORY [{abspath}]:")
    itemList = os.listdir(abspath)
    for item in itemList:
        itempath = os.path.join(abspath, item).replace("\\", "/")
        itemtime = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(itempath))
        )
        itemtype = ""
        if os.path.isfile(itempath):
            itemtype = "<FILE>"
        else:
            itemtype = "<DIR>"
        itemtime = itemtime.ljust(22)
        itemtype = itemtype.ljust(8)
        print("    >>>    -> " + itemtime + "   " + itemtype + "   " + item)
    print("    >>> ")
    return


def get_file_line_endings(file_abspath) -> str:
    """Return either '\r\n', '\r' or '\n'."""
    if file_abspath.endswith(".a"):
        purefunctions.printc(
            "\nWARNING: file_power.py => Attempt to "
            "read line endings from archive file!\n",
            color="warning",
        )
        return "\n"
    with open(file_abspath, "rb") as file:
        content = file.read()
    if b"\r\n" in content:
        return "\r\n"
    if b"\r" in content:
        return "\r"
    return "\n"


def unixify_line_endings(
    file_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
) -> None:
    """Unixify line endings in given file.

    Binary Mode
    ------------
    We need to make sure that we open the file both times
    in binary mode (mode='rb' and mode='wb') for the conversion
    to work.
    When opening files in text mode (mode='r' or mode='w' without b),
    the platform's native line endings (\r\n on Windows and \r on old
    Mac OS versions) are automatically converted to Python's Unix-style
    line endings: \n. So the call to content.replace() couldn't find any
    \r\n line endings to replace.
    In binary mode, no such conversion is done. Therefore the call to
    str.replace() can do its work.


    Binary Strings
    ---------------
    In Python 3, if not declared otherwise, strings are stored as
    Unicode (UTF-8). But we open our files in binary mode - therefore
    we need to add b in front of our replacement strings to tell Python
    to handle those strings as binary, too.
    """
    if file_abspath.endswith(".a"):
        purefunctions.printc(
            "WARNING: Attempt to unixify line endings in archive file!",
            color="warning",
        )
        return
    # replacement strings
    WINDOWS_LINE_ENDING = b"\r\n"
    UNIX_LINE_ENDING = b"\n"
    with open(file_abspath, "rb") as open_file:
        content = open_file.read()
    content = content.replace(
        WINDOWS_LINE_ENDING,
        UNIX_LINE_ENDING,
    )
    with open(file_abspath, "wb") as open_file:
        open_file.write(content)
    return


def unixify_line_endings_recursively(
    targetdir_abspath: str,
    printfunc: Optional[Callable] = None,
    catch_err: bool = True,
) -> None:
    """Recursively navigate through the given folder and unixify all line
    endings."""
    printfunc = nop if printfunc is None else printfunc
    printfunc = native_printfunc if printfunc is print else printfunc
    for dirpath, subdirs, files in os.walk(targetdir_abspath):
        for f in files:
            if any(
                f.endswith(s) for s in (".a", ".bin", ".hex", ".elf", ".eep")
            ):
                continue
            filepath = os.path.join(dirpath, f).replace("\\", "/")
            if get_file_line_endings(filepath) != "\n":
                unixify_line_endings(filepath)
                printfunc(
                    f"UNIXIFY: {filepath}\n",
                    "#e9b96e",
                )
    return
