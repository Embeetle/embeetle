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

import os
import platform
import shutil
import sys
import traceback
from pathlib import Path
from typing import *
import chardet
import os, traceback, sys, shutil, chardet
import purefunctions
import os_checker

if TYPE_CHECKING:
    try:
        from _hashlib import HASH as Hash
    except:
        from hashlib import HASH as Hash  # noqa
q = ""
dq = ""

image_extensions = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".psd",
    ".svg",
    ".raw",
    ".ico",
    ".heif",
    ".heic",
    ".jfif",
    ".webp",
    ".ai",
    ".eps",
    ".indd",
    ".pdf",
    ".svgz",
    ".mp4",
)
binary_extensions = (
    ".exe",
    ".dll",
    ".bin",
    ".dat",
    ".so",
    ".dylib",
    ".jar",
    ".class",
    ".lib",
    ".a",
    ".obj",
    ".o",
    ".d",
    ".ko",
    ".elf",
    ".img",
    ".iso",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".zip",
    ".hex",
    ".eep",
    ".pyc",
    ".cyclo",
    ".su",
    ".chm",
    ".crf",
    ".xlsx",
)
other_extensions = (
    ".ttf",
    ".woff",
    ".gitmodules",
)
text_and_source_extensions = (
    ".c",
    ".cpp",
    ".c++",
    ".h",
    ".hpp",
    ".h++",
    ".s",
    ".S",
    ".asm",
    ".inc",
    ".src",
    ".ld",
    ".icf",
    ".list",
    ".lst",
    ".map",
    ".sh",
    ".cmd",
    ".bat",
    ".mk",
    ".cfg",
    ".txt",
    ".md",
    ".btl",
    ".gdb",
    ".json",
    ".json5",
    ".xml",
    ".yml",
    ".yaml",
    ".py",
    ".ioc",
    ".html",
    ".css",
    ".cmake",
    ".toml",
    ".ino",
    ".ini",
    ".rst",
    ".eww",
    ".ewp",
    ".uvprojx",
    ".uvguix",
    ".uvmpw",
    ".uvoptx",
    ".uvopt",
    ".properties",
    ".cproject",
    ".mxproject",
    ".cproject_org",
    ".gitignore",
    ".project",
    ".project_org",
    ".launch",
    ".editorconfig",
    "readme",
    "makefile",
    "license",
    "kconfig",
    "doxyfile",
    ".svd",
    ".scvd",
    ".eclipse.cdt.codan.core.prefs",
    ".eclipse.cdt.core.prefs",
)


def fail_exit(
    msg: str,
    printfunc: Optional[Callable] = None,
) -> None:
    """Show the error message and quit the program."""
    if printfunc is None:
        printfunc = purefunctions.printc
    printfunc(msg, color="error")
    sys.exit(1)
    return


# ^                                 FILE AND FOLDER MANIPULATIONS                                  ^#
# % ============================================================================================== %#
# % Functions to deal with files and folders.                                                      %#
# %                                                                                                %#


def makedirs(
    folderpath: str,
    mode=0o777,
    exist_ok: bool = False,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param folderpath:   Absolute path to the directory.
    :param mode:         Access rights.
    :param exist_ok:     Is it okay if the directory already exists
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success

    Super-mkdir; create a leaf directory and all intermediate ones. Works like mkdir, except that
    any intermediate path segment (not just the rightmost) will be created if it does not exist. If
    the target directory already exists, raise an OSError if exist_ok is False. Otherwise no excep-
    tion is raised. This is recursive.
    """
    folderpath = folderpath.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Check
    # if not os.path.isabs(folderpath)
    #     msg = str(
    #         f'ERROR {q}filefunctions.makedirs(){q} expects an absolute path, but got\n'
    #         f'{q}{folderpath}{q}\n'
    #         f'{traceback.format_exc()}\n'
    #     )
    #     if exit_on_fail
    #         fail_exit(msg)
    #     printfunc(msg, color='error')
    #     return False

    # & Print
    if verbose:
        printfunc("Create folder ", end="", color="yellow")
        printfunc(f"{q}{folderpath}{q}")

    # & Action
    try:
        os.makedirs(folderpath, mode, exist_ok)
    except:
        if exit_on_fail:
            fail_exit(traceback.format_exc(), printfunc=printfunc)
        printfunc(traceback.format_exc(), color="error")
        raise
        return False
    return True


def clean(
    folderpath: str,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param folderpath:   Absolute path to the folder to be cleaned.
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success
    """
    folderpath = folderpath.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc
    delete(
        abspath=folderpath,
        verbose=verbose,
        exit_on_fail=exit_on_fail,
        printfunc=printfunc,
    )
    if os.path.exists(folderpath):
        # Deletion failed
        return False
    # Deletion succeeded
    return makedirs(
        folderpath=folderpath,
        verbose=verbose,
        exit_on_fail=exit_on_fail,
        printfunc=printfunc,
    )


def delete(
    abspath: str,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param abspath:      Absolute path to the file or folder to be deleted.
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success
    """
    abspath = abspath.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Check
    # if not os.path.isabs(abspath)
    #     msg = str(
    #         f'ERROR {q}filefunctions.delete(){q} expects an absolute path, but got\n'
    #         f'{q}{abspath}{q}\n'
    #         f'{traceback.format_exc()}\n'
    #     )
    #     if exit_on_fail
    #         fail_exit(msg)
    #     printfunc(msg, color='error')
    #     return False

    # & Print
    if verbose:
        if os.path.isdir(abspath):
            printfunc("Delete folder ", end="", color="yellow")
        else:
            printfunc("Delete file ", end="", color="yellow")
        printfunc(f"{q}{abspath}{q}")

    # & Action
    try:
        # $ Folder
        if os.path.isdir(abspath):
            try:
                shutil.rmtree(abspath)
            except:
                if verbose:
                    printfunc(
                        f"Can{q}t delete folder completely!", color="error"
                    )
                # Try to delete the folder in other ways
                # o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*
                # First use 'shutil.rmtree()' again but ignore the errors. This should already
                # delete most stuff.
                shutil.rmtree(abspath, ignore_errors=True)
                # Next, try to nuke the directory. Delete the files one-by-one and chmod them first.
                if os.path.isdir(abspath):

                    def nukedir(_folderpath):
                        _folderpath = _folderpath.replace("\\", "/")
                        if _folderpath.endswith("/"):
                            _folderpath = _folderpath[:-1]
                        for _e in os.listdir(_folderpath):
                            if _e == "." or _e == "..":
                                continue
                            _p = _folderpath + "/" + _e
                            if os.path.isdir(_p):
                                nukedir(_p)
                            else:
                                try:
                                    os.chmod(_p, 0o777)
                                    os.remove(_p)
                                    printfunc(
                                        f"    Deleted file: ",
                                        end="",
                                        color="error",
                                    )
                                    printfunc(f"{q}{_p}{q}")
                                except:
                                    printfunc(
                                        f"    Can{q}t delete file: ",
                                        end="",
                                        color="error",
                                    )
                                    printfunc(f"{q}{_p}{q}")
                            continue
                        try:
                            os.rmdir(_folderpath)
                        except:
                            printfunc(
                                f"    Can{q}t delete folder: ",
                                end="",
                                color="error",
                            )
                            printfunc(f"{q}{_folderpath}{q}")

                    printfunc(f"Nuke folder: ", end="", color="error")
                    printfunc(f"{q}{abspath}{q}")
                    nukedir(abspath)
                # o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*o*

        # $ File
        else:
            try:
                os.remove(abspath)
            except:
                os.chmod(abspath, 0o777)
                os.remove(abspath)
    except:
        pass

    # & Check success
    if os.path.exists(abspath):
        if exit_on_fail:
            fail_exit(traceback.format_exc(), printfunc=printfunc)
        printfunc(traceback.format_exc(), color="error")
        return False
    return True


def rename(
    src: str,
    dst: str,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param src:          Absolute path to the source file or directory.
    :param dst:          Absolute path to the destination file or directory.
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success
    """
    src = src.replace("\\", "/")
    dst = dst.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Check
    # if (not os.path.isabs(src)) or (not os.path.isabs(dst))
    #     msg = str(
    #         f'ERROR {q}filefunctions.rename(){q} expects an absolute path, but got\n'
    #         f'{q}{src}{q} and\n'
    #         f'{q}{dst}{q}\n'
    #         f'{traceback.format_exc()}\n'
    #     )
    #     if exit_on_fail
    #         fail_exit(msg)
    #     printfunc(msg, color='error')
    #     return False

    # & Print
    if verbose:
        if os.path.isfile(src):
            printfunc("Rename file ", end="", color="yellow")
        else:
            printfunc("Rename folder ", end="", color="yellow")
        printfunc(f"{q}{src}{q}")

    # & Action
    try:
        try:
            os.rename(src, dst)
        except:
            os.chmod(src, 0o777)
            os.rename(src, dst)
    except:
        if exit_on_fail:
            fail_exit(traceback.format_exc(), printfunc=printfunc)
        printfunc(traceback.format_exc(), color="error")
        return False
    return True


def copy(
    src: str,
    dst: str,
    os_aware: bool = False,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param src:          Absolute path to the source file or directory.
    :param dst:          Absolute path to the destination file or directory.
    :param os_aware:     Keep the os in mind. Don't copy windows stuff on linux and vice versa.
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success
    """
    src = src.replace("\\", "/")
    dst = dst.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Check
    # if (not os.path.isabs(src)) or (not os.path.isabs(dst))
    #     msg = str(
    #         f'ERROR {q}filefunctions.copy(){q} expects an absolute path, but got\n'
    #         f'{q}{src}{q} and\n'
    #         f'{q}{dst}{q}\n'
    #         f'{traceback.format_exc()}\n'
    #     )
    #     if exit_on_fail
    #         fail_exit(msg)
    #     printfunc(msg, color='error')
    #     return False

    if os.path.exists(dst):
        msg = str(
            f"ERROR {q}filefunctions.copy(){q} expects the destination not yet to exist\n"
            f"{q}{dst}{q}\n"
            f"{traceback.format_exc()}\n"
        )
        if exit_on_fail:
            fail_exit(msg, printfunc=printfunc)
        printfunc(msg, color="error")
        return False

    # & Print
    if verbose:
        if os.path.isfile(src):
            printfunc("Copy file ", end="", color="yellow")
        else:
            printfunc("Copy folder ", end="", color="yellow")
        printfunc(f"{q}{src}{q}")
        printfunc(f"to ", end="", color="yellow")
        printfunc(f"{q}{dst}{q}")

    # & Action
    try:
        # $ First check if the destination parental folder exists
        parent_folder = os.path.dirname(dst).replace("\\", "/")
        if not os.path.exists(parent_folder):
            makedirs(
                folderpath=parent_folder,
                verbose=verbose,
                exit_on_fail=exit_on_fail,
                printfunc=printfunc,
            )
        # $ It's a file
        if os.path.isfile(src):
            shutil.copy2(
                src=src,
                dst=dst,
                follow_symlinks=True,
            )
        # $ It's a folder
        else:
            # Just copy the whole folder
            if not os_aware:
                shutil.copytree(
                    src=src,
                    dst=dst,
                    symlinks=True,
                )

            # Only copy os-relevant stuff from the src folder into the dst folder. Loop over the
            # individual elements and decide what needs to be copied.
            else:
                # First create the destination folder.
                makedirs(
                    folderpath=dst,
                    verbose=False,
                    exit_on_fail=exit_on_fail,
                    printfunc=printfunc,
                )
                # Now loop over the elements in the source folder, and copy them
                # one-by-one into the destination folder. Check os-compliance.
                for name in os.listdir(src):
                    src_element = f"{src}/{name}"
                    dst_element = f"{dst}/{name}"
                    # Check if element should be skipped
                    if (
                        ("linux" in name.lower())
                        and (os_checker.is_os("windows"))
                    ) or (
                        ("windows" in name.lower())
                        and (os_checker.is_os("linux"))
                    ):
                        if verbose:
                            printfunc("Skip ", end="", color="yellow")
                            printfunc(f"{q}{src_element}{q}")
                        continue
                    # The element should be copied and is a folder
                    if os.path.isdir(src_element):
                        shutil.copytree(
                            src=src_element,
                            dst=dst_element,
                            symlinks=True,
                        )
                        continue
                    # The element should be copied and is a file
                    assert os.path.isfile(src_element)
                    shutil.copy2(
                        src=src_element,
                        dst=dst_element,
                        follow_symlinks=True,
                    )
                    continue
    except:
        if exit_on_fail:
            fail_exit(traceback.format_exc(), printfunc=printfunc)
        printfunc(traceback.format_exc(), color="error")
        return False
    return True


def move_contents(
    src: str,
    dst: str,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """Move the content from one folder into another.

    :param src: Absolute path to the source directory.
    :param dst: Absolute path to the destination directory.
    :param verbose: Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success
    """
    src = src.replace("\\", "/")
    dst = dst.replace("\\", "/")
    if src.endswith("/"):
        src = src[:-1]
    if dst.endswith("/"):
        dst = dst[:-1]
    assert os.path.isdir(src)
    assert os.path.isdir(dst)
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Print
    if verbose:
        printfunc("Move content from ", end="", color="yellow")
        printfunc(f"{q}{src}{q}")
        printfunc("into ", end="", color="yellow")
        printfunc(f"{q}{dst}{q}")

    # & Action
    success = True
    for e in os.listdir(src):
        if e == "." or e == "..":
            continue
        try:
            shutil.move(src + "/" + e, dst)
        except:
            try:
                os.chmod(src + "/" + e, 0o777)
                shutil.move(src + "/" + e, dst)
            except:
                if exit_on_fail:
                    fail_exit(traceback.format_exc(), printfunc=printfunc)
                printfunc(traceback.format_exc(), color="error")
                success = False
        continue
    if verbose:
        if not success:
            printfunc("ERROR: Not all content has been moved!", color="error")
    return success


def move(
    src: str,
    dst: str,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param src:          Absolute path to the source file or directory.
    :param dst:          Absolute path to the destination file or directory.
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success

    If the destination is a folder, the source (either a file or folder itself) will be moved into
    the destination folder.
    """
    src = src.replace("\\", "/")
    dst = dst.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Check
    # if (not os.path.isabs(src)) or (not os.path.isabs(dst))
    #     msg = str(
    #         f'ERROR {q}filefunctions.move(){q} expects an absolute path, but got\n'
    #         f'{q}{src}{q} and\n'
    #         f'{q}{dst}{q}\n'
    #         f'{traceback.format_exc()}\n'
    #     )
    #     if exit_on_fail
    #         fail_exit(msg)
    #     printfunc(msg, color='error')
    #     return False

    # & Print
    if verbose:
        if os.path.isfile(src):
            printfunc("Move file ", end="", color="yellow")
        else:
            printfunc("Move folder ", end="", color="yellow")
        printfunc(f"{q}{src}{q}")
        printfunc(f"to ", end="", color="yellow")
        if os.path.isdir(dst):
            # The move target is an existing folder. The source - be it a file or folder - will
            # move into that target.
            src_name = src.split("/")[-1]  # noqa
            printfunc(f"{q}{dst}/{src_name}{q}")
        else:
            printfunc(f"{q}{dst}{q}")

    # & Action
    # $ First check if the destination parental folder exists
    parent_folder = os.path.dirname(dst).replace("\\", "/")
    if not os.path.exists(parent_folder):
        makedirs(
            folderpath=parent_folder,
            verbose=verbose,
            exit_on_fail=exit_on_fail,
            printfunc=printfunc,
        )
    # $ Move the file or folder
    try:
        shutil.move(src, dst)
    except:
        if exit_on_fail:
            fail_exit(traceback.format_exc(), printfunc=printfunc)
        printfunc(traceback.format_exc(), color="error")
        return False
    return True


def chmod_file(
    filepath: str,
    mode=0o775,
    verbose: bool = True,
    exit_on_fail: bool = True,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param filepath:     Absolute path to the file.
    :param mode:         Access mode.
    :param verbose:      Print the actions to the console.
    :param exit_on_fail: Exit the program if this function fails.
    :return: success
    """
    filepath = filepath.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Check
    # if not os.path.isabs(filepath)
    #     msg = str(
    #         f'ERROR {q}filefunctions.chmod_file(){q} expects an absolute path, but got\n'
    #         f'{q}{filepath}{q}\n'
    #         f'{traceback.format_exc()}\n'
    #     )
    #     if exit_on_fail
    #         fail_exit(msg)
    #     printfunc(msg, color='error')
    #     return False

    if not os.path.isfile(filepath):
        msg = str(
            f"ERROR {q}filefunctions.chmod_file(){q} expects an existing file, but got\n"
            f"{q}{filepath}{q}\n"
            f"{traceback.format_exc()}\n"
        )
        if exit_on_fail:
            fail_exit(msg, printfunc=printfunc)
        printfunc(msg, color="error")
        return False

    # & Print
    if verbose:
        printfunc("Change access mode for file ", end="", color="yellow")
        printfunc(f"{q}{filepath}{q}")
        printfunc("to ", end="", color="yellow")
        printfunc(f"{mode}")

    # & Action
    try:
        os.chmod(filepath, mode)
    except:
        if exit_on_fail:
            fail_exit(traceback.format_exc(), printfunc=printfunc)
        printfunc(traceback.format_exc(), color="error")
        return False
    return True


def convert_file_encodings_recursively(
    target_abspath: str,
    verbose: bool = False,
    miniverbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> None:
    """
    :param target_abspath: Absolute path to folder whose files need recursive re-encoding.
    :param verbose:        Print the actions to the console.
    :param miniverbose:    Print only a dot per file.
    :param printfunc:      [Optional] Function to print the actions.

    Recursively convert the file encodings to utf-8
    """
    target_abspath = target_abspath.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc

    # & Action
    for dirpath, subdirs, files in os.walk(target_abspath):
        # $ Skip the `.git` directory
        subdirs[:] = [d for d in subdirs if d != ".git"]
        for f in files:
            # $ Ignore files that are binaries or images
            if any(
                f.lower().endswith(s)
                for s in binary_extensions + image_extensions + other_extensions
            ):
                continue
            # $ Convert source- and textfiles
            if any(f.lower().endswith(s) for s in text_and_source_extensions):
                # Check the file encoding and re-encode if needed
                if miniverbose:
                    printfunc(".", end="")
                filepath = os.path.join(dirpath, f).replace("\\", "/")
                source_encoding, confidence = get_file_encoding(
                    file_abspath=filepath,
                    verbose=verbose,
                    printfunc=printfunc,
                )
                if (source_encoding is not None) and (
                    source_encoding.lower() in ("utf-8", "ascii")
                ):
                    pass
                else:
                    convert_file_encoding_to_utf8(
                        file_abspath=filepath,
                        source_encoding=source_encoding,
                        verbose=verbose,
                        printfunc=printfunc,
                    )
                continue
            # $ Report unknown extensions
            printfunc(f"\nUnknown file extension: {f}\n{dirpath}/{f}\n")
            # input('Press any key to continue...')
            continue
        continue
    return


def convert_file_encoding_to_utf8(
    file_abspath: str,
    source_encoding: Optional[str] = None,
    verbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> None:
    """
    :param file_abspath:    Absolute path to file that needs re-encoding.
    :param source_encoding: [Optional] Current encoding of the given file. Can be detected in this
                            function if not provided.
    :param verbose:         Print the actions to the console.
    :param printfunc:       [Optional] Function to print the actions.

    Convert the given file to utf-8
    """
    file_abspath = file_abspath.replace("\\", "/")

    # $ Step 1: Detect the current encoding
    if source_encoding is None:
        source_encoding, confidence = get_file_encoding(
            file_abspath=file_abspath,
            verbose=verbose,
            printfunc=printfunc,
        )
    if (source_encoding is not None) and (
        source_encoding.lower() in ("utf-8", "ascii")
    ):
        # Already in correct encoding. ASCII is valid subset of 'utf-8'.
        return

    # $ Step 2: Read the content using the detected encoding
    with open(
        file_abspath, "r", encoding=source_encoding, errors="replace"
    ) as f:
        content = f.read()

    # $ Step 3: Write the content back to the file using the target encoding
    with open(file_abspath, "w", encoding="utf-8") as file:
        file.write(content)

    if verbose:
        if printfunc is None:
            printfunc = purefunctions.printc
        printfunc(f"RE-ENCODE: {q}{file_abspath}{q}")
    return


def get_file_encoding(
    file_abspath: str,
    verbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> Tuple[Optional[str], int]:
    """
    :param file_abspath: Absolute path to file.

    Return the encoding for the given file and the confidence in percentage.
    """
    assert os.path.isfile(file_abspath)
    if verbose:
        if printfunc is None:
            printfunc = purefunctions.printc
        printfunc(f"CHECK ENCODING: {q}{file_abspath}{q}")
    with open(file_abspath, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        source_encoding = result["encoding"]
        confidence = result["confidence"]
    return source_encoding, int(confidence * 100)


def unixify_line_endings_recursively(
    target_abspath: str,
    verbose: bool = False,
    miniverbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> None:
    """
    :param target_abspath: Absolute path to folder whose files need recursive unixification.
    :param verbose:        Print the actions to the console.
    :param miniverbose:    Print only a dot per file.
    :param printfunc:      [Optional] Function to print the actions.

    Recursively navigate through the given folder and unixify all line endings.
    """
    target_abspath = target_abspath.replace("\\", "/")
    if printfunc is None:
        printfunc = purefunctions.printc
    for dirpath, subdirs, files in os.walk(target_abspath):
        # $ Skip the `.git` directory
        subdirs[:] = [d for d in subdirs if d != ".git"]
        for f in files:
            # $ Ignore files that are binaries or images
            if any(
                f.lower().endswith(s)
                for s in binary_extensions + image_extensions + other_extensions
            ):
                continue
            # $ Convert source- and textfiles
            if any(f.lower().endswith(s) for s in text_and_source_extensions):
                # Check the line ending and unixify if needed
                if miniverbose:
                    printfunc(".", end="")
                filepath = os.path.join(dirpath, f).replace("\\", "/")
                eol = get_file_line_endings(
                    file_abspath=filepath,
                    verbose=verbose,
                    printfunc=printfunc,
                )
                if eol != "\n":
                    unixify_line_endings(
                        file_abspath=filepath,
                        verbose=verbose,
                        printfunc=printfunc,
                    )
                continue
            # $ Report unknown extensions
            printfunc(f"\nUnknown file extension: {f}\n{dirpath}/{f}\n")
            # input('Press any key to continue...')
            continue
        continue
    return


def unixify_line_endings(
    file_abspath: str,
    verbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> None:
    """Unixify line endings in given file.

    Binary Mode
    ------------
    We need to make sure that we open the file both times in binary mode (mode='rb' and mode='wb')
    for the conversion to work.
    When opening files in text mode (mode='r' or mode='w' without b), the platform's native line
    endings (\r\n on Windows and \r on old Mac OS versions) are automatically converted to Python's
    Unix-style line endings \n. So the call to content.replace() couldn't find any \r\n line en-
    dings to replace. In binary mode, no such conversion is done. Therefore the call to
    str.replace() can do its work.

    Binary Strings
    ---------------
    In Python 3, if not declared otherwise, strings are stored as Unicode (UTF-8). But we open our
    files in binary mode - therefore we need to add b in front of our replacement strings to tell
    Python to handle those strings as binary, too.
    """
    if verbose:
        if printfunc is None:
            printfunc = purefunctions.printc
        printfunc(f"UNIXIFY: {q}{file_abspath}{q}")
    WINDOWS_LINE_ENDING = b"\r\n"
    UNIX_LINE_ENDING = b"\n"
    with open(file_abspath, "rb") as open_file:
        content = open_file.read()
    content = content.replace(
        WINDOWS_LINE_ENDING,
        UNIX_LINE_ENDING,
    )
    try:
        with open(file_abspath, "wb") as open_file:
            open_file.write(content)
    except:
        pass
    return


def get_file_line_endings(
    file_abspath: str,
    verbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> str:
    """Return either '\r\n', '\r' or '\n'."""
    if verbose:
        if printfunc is None:
            printfunc = purefunctions.printc
        printfunc(f"CHECK EOL: {q}{file_abspath}{q}")
    try:
        with open(file_abspath, "rb") as file:
            content = file.read()
    except:
        return "\n"
    if b"\r\n" in content:
        return "\r\n"
    if b"\r" in content:
        return "\r"
    return "\n"


# ^                                   RETRIEVE IMPORTANT PATHS                                     ^#
# % ============================================================================================== %#
# % Functions to obtain absolute paths to important locations such as the user profile folder      %#
# % (generally represented as '~'), the Documents folder, cloud folders, etc.                      %#
# %                                                                                                %#

# TERMINOLOGY
# ===========
# curuser_profile_folder:   Folder belonging to the current user,
#                           like 'C:/Users/krist'
# user_profile_folder:      Folder belonging to a given user,
#                           like 'C:/Users/olivi'

# curuser_documents_folder: Documents folder belonging to the current user,
#                           like 'C:/Users/krist/Documents'
# user_documents_folder:    Documents folder belonging to a given user,
#                           like 'C:/Users/olivi/Documents'

# cloud_documents_folder:   Documents folder belonging to a cloud service,
#                           like 'C:/Users/krist/OneDrive/Documenten'

documents_folder_name_candidates = [
    "Documents",
    "Belgeler",
    "檔案",
    "Dokumentarni",
    "फाईलें",
    "ಫೈಲ್ಗಳು",
    "Akten",
    "Dokümanlar",
    "파일",
    "書類",
    "Dogfennau",
    "Papíry",
    "Prilohy",
    "Documente",
    "Skjöl",
    "ឯកសារ",
    "Raksts",
    "Plikai",
    "文件夾",
    "Papucsok",
    "கோப்புகள்",
    "Scriosánna",
    "Документы",
    "Документтер",
    "Skjøl",
    "ഫയലുകൾ",
    "ದಾಖಲೆಗಳು",
    "फ़ाइलें",
    "파일들",
    "ਫਾਈਲਾਂ",
    "രേഖകൾ",
    "Dokumenty",
    "Tài liệu",
    "Arkiv",
    "დოკუმენტები",
    "Dokumentojn",
    "ເອກະສານ",
    "Dokumentuak",
    "Փաստաթղթեր",
    "档案",
    "ଫାଇଲ୍",
    "Dokumenter",
    "文件",
    "Papki",
    "Dokumenti",
    "ファイル",
    "दस्तावेज़",
    "Documenten",
    "Документи",
    "ලේඛන",
    "ගොනු",
    "Mappor",
    "Papiers",
    "Papka",
    "เอกสาร",
    "Dokumentai",
    "Documenti",
    "文档",
    "Klasörler",
    "문서",
    "Tiedostot",
    "Dokumentoj",
    "فایل ها",
    "Dokumentumok",
    "Folderët",
    "Ficheiros",
    "Papeles",
    "Zibsnis",
    "ፋይሎች",
    "ডকুমেন্টস",
    "ملفات",
    "Documentos",
    "Hujjatlar",
    "ფაილები",
    "Dokumentit",
    "Faili",
    "Papirer",
    "Kansiot",
    "Fitxategiak",
    "Dastavez",
    "Cac tai lieu",
    "Hồ sơ",
    "Evraklar",
    "Fichiers",
    "Mappes",
    "Mappen",
    "Asiakirjat",
    "ఫైల్స్",
    "Dokumente",
    "Fayly",
    "ફાઈલો",
    "ข้อมูล",
    "מסמכים",
    "Mape",
]


def __get_registry_value(key: str, subkey: str, value: str) -> Optional[str]:
    """Retrieve a value from the Windows registry."""
    try:
        import winreg

        with winreg.OpenKey(key, subkey) as regkey:  # noqa
            return winreg.QueryValueEx(regkey, value)[0]
    except FileNotFoundError:
        pass
    return None


__curuser_profile_folder_cache: Optional[str] = None


def get_curuser_profile_folder() -> Optional[str]:
    """Return the absolute path to the current user's profile folder.

    For Windows, it's like 'C:/Users/username'. For Linux, it's like
    '/home/username'.
    """
    global __curuser_profile_folder_cache
    if __curuser_profile_folder_cache:
        return __curuser_profile_folder_cache

    if os_checker.is_os("windows"):
        # Find current user profile folder in the environment variables.
        # Use os.path.expanduser('~') as a fallback solution.
        curuser_profile_folder = os.environ.get(
            "USERPROFILE", os.path.expanduser("~")
        )
        if curuser_profile_folder:
            # Just to be sure, expand any variables in this path
            curuser_profile_folder = os.path.expandvars(curuser_profile_folder)
            # Take care of the slashes
            curuser_profile_folder = curuser_profile_folder.replace(
                "\\", "/"
            ).rstrip("/")
    else:
        # For Linux and other Unix-like systems
        curuser_profile_folder = (
            os.path.expanduser("~").replace("\\", "/").rstrip("/")
        )

    __curuser_profile_folder_cache = curuser_profile_folder
    return curuser_profile_folder


__user_profile_folders_cache: Optional[List[str]] = None


def list_user_profile_folders() -> List[str]:
    """List all the user profile folders.

    On Windows, this excludes special system and service profile folders. On
    Linux, this includes directories under '/home' and any user defined in
    '/etc/passwd'.
    """
    global __user_profile_folders_cache
    if __user_profile_folders_cache:
        return __user_profile_folders_cache

    user_profile_folders: List[str] = []

    # & WINDOWS
    if os_checker.is_os("windows"):
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList",
            ) as key:
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    try:
                        sub_key_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, sub_key_name) as sub_key:
                            user_profile_folder, _ = winreg.QueryValueEx(
                                sub_key, "ProfileImagePath"
                            )
                            if user_profile_folder:
                                user_profile_folders.append(
                                    user_profile_folder.replace("\\", "/")
                                )
                    except Exception as e:
                        print(f"Error accessing registry subkey: {e}")
        except Exception as e:
            print(f"Error accessing Windows registry: {e}")

        # Filter the special system and service profile folders to keep only the user profile
        # folders.
        user_profile_folders = [
            p for p in user_profile_folders if not p.startswith("%systemroot%")
        ]

    # & LINUX
    else:
        try:
            import pwd

            user_profile_folders = [
                user_info.pw_dir
                for user_info in pwd.getpwall()
                if os.path.isdir(user_info.pw_dir)
                and user_info.pw_dir.startswith("/home/")
            ]
        except Exception as e:
            print(f"Error accessing user information: {e}")

    # & FILTERING
    # Make sure each path has only forward slashes and no trailing slash, and filter out duplicates
    user_profile_folders = sorted(
        set(p.replace("\\", "/").rstrip("/") for p in user_profile_folders)
    )

    # Make sure the current user profile folder is part of the list. Also make sure it is in the
    # front.
    curuser_profile_folder = get_curuser_profile_folder()
    if curuser_profile_folder:
        if curuser_profile_folder not in user_profile_folders:
            user_profile_folders.insert(0, curuser_profile_folder)
        else:
            user_profile_folders.remove(curuser_profile_folder)
            user_profile_folders.insert(0, curuser_profile_folder)

    # Filter out those that no longer exist
    try:
        user_profile_folders = [
            p for p in user_profile_folders if os.path.isdir(p)
        ]
    except:
        # An error occured while checking 'os.path.isdir()'. Try again in a more prudent way.
        temp = []
        for p in user_profile_folders:
            try:
                if os.path.isdir(p):
                    temp.append(p)
            except Exception as e:
                print(f"Error while checking if {p} is a directory: {e}")
            continue
        user_profile_folders = temp

    # Return the list
    __user_profile_folders_cache = user_profile_folders
    return user_profile_folders


__curuser_documents_folder_cache: Optional[str] = None


def get_curuser_documents_folder() -> Optional[str]:
    """Return the absolute path to the current user's Documents folder, eg.

    'C:/Users/krist/Documents'.
    """
    global __curuser_documents_folder_cache
    if __curuser_documents_folder_cache:
        return __curuser_documents_folder_cache

    # The current user's Document folder path will go into this variable. It gets reset to None
    # at the start of every method that attempts to find it.
    curuser_documents_folder: Optional[str] = None

    # & WINDOWS
    if os_checker.is_os("windows"):
        try:
            import ctypes
            import ctypes.wintypes

            # $ Windows API approach 1
            # Use the 'SHGetFolderPathW()' function to retrieve the path of a special folder, in
            # this case the Documents folder.
            curuser_documents_folder = None
            try:
                CSIDL_PERSONAL = 5  # My Documents
                SHGFP_TYPE_CURRENT = 0  # Get current, not default value
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                result = ctypes.windll.shell32.SHGetFolderPathW(
                    None,
                    CSIDL_PERSONAL,
                    None,
                    SHGFP_TYPE_CURRENT,
                    buf,
                )
                if result == 0:  # S_OK
                    curuser_documents_folder = buf.value
                    if curuser_documents_folder and os.path.isdir(
                        curuser_documents_folder
                    ):
                        curuser_documents_folder = (
                            curuser_documents_folder.replace("\\", "/").rstrip(
                                "/"
                            )
                        )
                        __curuser_documents_folder_cache = (
                            curuser_documents_folder
                        )
                        return curuser_documents_folder
            except Exception as e:
                print(
                    f"Error finding Documents folder using the SHGetFolderPathW() approach: {e}"
                )

            # $ Windows API approach 2
            # If the previous approach failed, or it resulted in the value 'None', then try this new
            # Windows API approach that works on Windows Vista and above. This approach uses the
            # function 'SHGetKnownFolderPath()', which is more current than 'SHGetFolderPathW()'.
            # The function 'SHGetKnownFolderPath()' is part of the Shell32.dll and is used to get
            # the path of known folders defined in 'KNOWNFOLDERID'.
            curuser_documents_folder = None
            try:

                class GUID(ctypes.Structure):
                    _fields_ = [
                        ("Data1", ctypes.wintypes.DWORD),
                        ("Data2", ctypes.wintypes.WORD),
                        ("Data3", ctypes.wintypes.WORD),
                        ("Data4", ctypes.wintypes.BYTE * 8),  # noqa
                    ]

                    def __init__(self, guid_str):
                        super(GUID, self).__init__()
                        parts = guid_str.split("-")
                        self.Data1 = int(parts[0], 16)
                        self.Data2 = int(parts[1], 16)
                        self.Data3 = int(parts[2], 16)
                        data4_bytes = bytearray.fromhex(
                            "".join(parts[3:5]) + "".join(parts[5:])
                        )
                        self.Data4 = (ctypes.wintypes.BYTE * 8)(
                            *data4_bytes
                        )  # noqa

                # GUID for the Documents folder
                # The GUID {FDD39AD0-238F-46AF-ADB4-6C85480369C7} represents the Documents folder.
                # This is used by SHGetKnownFolderPath to identify which folder's path we want.
                FOLDERID_Documents = GUID(
                    "FDD39AD0-238F-46AF-ADB4-6C85480369C7"
                )

                # ctypes wrapper for SHGetKnownFolderPath
                SHGetKnownFolderPath = (
                    ctypes.windll.shell32.SHGetKnownFolderPath
                )
                SHGetKnownFolderPath.argtypes = [
                    ctypes.POINTER(GUID),
                    ctypes.wintypes.DWORD,
                    ctypes.wintypes.HANDLE,
                    ctypes.POINTER(ctypes.POINTER(ctypes.wintypes.WCHAR)),
                ]
                path_ptr = ctypes.POINTER(ctypes.wintypes.WCHAR)()

                # Call the function
                result = SHGetKnownFolderPath(
                    ctypes.byref(FOLDERID_Documents),
                    0,
                    None,
                    ctypes.byref(path_ptr),
                )
                if result == 0:  # S_OK
                    # Dereference the path pointer
                    path = ctypes.wstring_at(path_ptr)
                    ctypes.windll.ole32.CoTaskMemFree(path_ptr)
                    curuser_documents_folder = path
                    if curuser_documents_folder and os.path.isdir(
                        curuser_documents_folder
                    ):
                        curuser_documents_folder = (
                            curuser_documents_folder.replace("\\", "/").rstrip(
                                "/"
                            )
                        )
                        __curuser_documents_folder_cache = (
                            curuser_documents_folder
                        )
                        return curuser_documents_folder
                else:
                    raise ctypes.WinError(result)
            except Exception as e:
                print(
                    f"Error finding Documents folder using the SHGetKnownFolderPath() approach: {e}"
                )
        except Exception as e:
            print(
                f"Failed to access the Windows API. Probably something went wrong when importing "
                f"ctypes: {e}"
            )

    # & LINUX
    else:

        def get_xdg_user_dir(default: Optional[str]) -> Optional[str]:
            # Attempt to get an XDG user directory. If not found, return the default.
            xdg_config_path: str = os.path.join(
                os.path.expanduser("~"), ".config", "user-dirs.dirs"
            )
            if os.path.exists(xdg_config_path):
                with open(xdg_config_path, "r") as file:
                    for line in file:
                        if line.startswith("XDG_DOCUMENTS_DIR"):
                            p = line.split('"')[1]
                            return os.path.expanduser(p)
            return default

        # $ Method 1: XDG User Directories
        try:
            curuser_documents_folder = get_xdg_user_dir(None)
            if curuser_documents_folder and os.path.isdir(
                curuser_documents_folder
            ):
                curuser_documents_folder = curuser_documents_folder.replace(
                    "\\", "/"
                ).rstrip("/")
                __curuser_documents_folder_cache = curuser_documents_folder
                return curuser_documents_folder
        except Exception as e:
            print(f"Error while checking the XDG User Directories: {e}")

        # $ Method 2: Environment Variables
        try:
            curuser_documents_folder = os.environ.get("XDG_DOCUMENTS_DIR")
            if curuser_documents_folder and os.path.isdir(
                curuser_documents_folder
            ):
                curuser_documents_folder = curuser_documents_folder.replace(
                    "\\", "/"
                ).rstrip("/")
                __curuser_documents_folder_cache = curuser_documents_folder
                return curuser_documents_folder
        except Exception as e:
            print(
                f"Error while checking the environment variable XDG_DOCUMENTS_DIR: {e}"
            )

    # $ Fallback method
    # If the previous approaches failed then try this fallback method
    curuser_documents_folder = None
    try:
        curuser_profile_folder = get_curuser_profile_folder()
        for name in documents_folder_name_candidates:
            curuser_documents_folder = (
                os.path.join(
                    curuser_profile_folder,
                    name,
                )
                .replace("\\", "/")
                .rstrip("/")
            )
            try:
                if os.path.isdir(curuser_documents_folder):
                    __curuser_documents_folder_cache = curuser_documents_folder
                    return curuser_documents_folder
            except Exception as e:
                print(
                    f"Error while checking existence of {curuser_documents_folder}: {e}"
                )
            continue
    except Exception as e:
        print(f"Error finding Documents folder using the fallback method: {e}")

    # $ Not found
    return None


__curuser_documents_folder_name_cache: Optional[str] = None


def get_curuser_documents_folder_name() -> Optional[str]:
    """The name of the 'Documents' folder on a Windows or Linux system can be
    language-dependent."""
    global __curuser_documents_folder_name_cache
    if __curuser_documents_folder_name_cache:
        return __curuser_documents_folder_name_cache

    curuser_documents_folder = get_curuser_documents_folder()
    if curuser_documents_folder is None:
        return None
    name = (
        curuser_documents_folder.replace("\\", "/").rstrip("/").split("/")[-1]
    )
    __curuser_documents_folder_name_cache = name
    return name


__user_documents_folder_cache: Optional[Dict[str, Optional[str]]] = {}


def get_user_documents_folder(user_profile_folder: str) -> Optional[str]:
    """Return the Documents folder path for the given user profile folder.

    For example, return 'C:/Users/krist/Documents' if the user profile folder
    'C:/Users/krist' is given. This function should also work on non-English
    systems. Return None if the Documents folder doesn't exist.
    """
    if user_profile_folder in __user_documents_folder_cache.keys():
        return __user_documents_folder_cache[user_profile_folder]

    user_profile_folder = user_profile_folder.replace("\\", "/").rstrip("/")
    curuser_profile_folder = get_curuser_profile_folder()

    # $ Special treatment for current user
    # Check if the given 'user_profile_folder' corresponds to the current user. If that's the case,
    # then simply invoke 'get_curuser_documents_folder()'.
    if user_profile_folder == curuser_profile_folder:
        result = get_curuser_documents_folder()
        __user_documents_folder_cache[user_profile_folder] = result
        return result

    # $ Check default location
    # Look into the default location where one would expect the Documents folder to be for the given
    # user profile. Loop over all possible names for this folder, starting with the most likely one.
    user_documents_folder: Optional[str] = None
    names = [
        get_curuser_documents_folder_name(),
    ] + documents_folder_name_candidates
    for name in names:
        user_documents_folder = (
            os.path.join(
                user_profile_folder,
                name,
            )
            .replace("\\", "/")
            .rstrip("/")
        )
        if os.path.isdir(user_documents_folder):
            break
        continue
    else:
        # No Documents folder found!
        __user_documents_folder_cache[user_profile_folder] = None
        return None
    __user_documents_folder_cache[user_profile_folder] = user_documents_folder
    return user_documents_folder


__user_documents_folders_cache: Optional[List[str]] = None


def list_user_documents_folders() -> List[str]:
    """List all the user Documents folders on this computer.

    Normally that would be one per user. The Documents folder belonging to the
    current user will be at the front of the list.
    """
    global __user_documents_folders_cache
    if __user_documents_folders_cache:
        return __user_documents_folders_cache

    # Construct the list of Documents folders by looping over all the found user profiles and
    # determining the Documents folder for each of them.
    user_documents_folders: List[str] = []
    for user_profile_folder in list_user_profile_folders():
        if user_profile_folder is None:
            continue
        if not os.path.isdir(user_profile_folder):
            continue
        user_documents_folder = get_user_documents_folder(user_profile_folder)
        if user_documents_folder is None:
            continue
        if not os.path.isdir(user_documents_folder):
            continue
        user_documents_folders.append(user_documents_folder)
        continue

    # Avoid duplication, meanwhile making sure that the list order is preserved. Then return the
    # de-duplicated list.
    seen = set()
    result = [
        p for p in user_documents_folders if not (p in seen or seen.add(p))
    ]
    __user_documents_folders_cache = result
    return result


__cloud_folders_cache: Optional[List[str]] = None


def list_cloud_folders() -> List[str]:
    """List all the cloud folders on this computer, eg.

    ['C:/Users/robby/OneDrive', ].
    """
    global __cloud_folders_cache
    if __cloud_folders_cache:
        return __cloud_folders_cache

    def list_cloud_folders_for_user(_user_profile_folder: str) -> List[str]:
        _folders: List[str] = []
        # $ List cloud service paths
        # Construct a dictionary with the default paths and registry locations for some cloud
        # services. On Windows, the registry locations will be checked first in an attempt to
        # extract the path. On Linux the registry locations are ignored, because there is no
        # registry. The default path is used on both platforms as fallback.
        hkey_current_user: Optional[int] = None
        if os_checker.is_os("windows"):
            import winreg

            hkey_current_user = winreg.HKEY_CURRENT_USER

        cloud_service_info = {
            "Dropbox": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "Dropbox"),
                ],
                "registry": (
                    hkey_current_user,
                    r"Software\Dropbox\Dropbox",
                    "Path",
                ),
            },
            "Google Drive": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "Google Drive"),
                    os.path.join(_user_profile_folder, "GoogleDrive"),
                    os.path.join(_user_profile_folder, "GDrive"),
                ],
                "registry": (
                    hkey_current_user,
                    r"Software\Google\DriveFS",
                    "MountPointPath",
                ),
            },
            "OneDrive": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "OneDrive"),
                ],
                "registry": (
                    hkey_current_user,
                    r"Software\Microsoft\OneDrive",
                    "UserFolder",
                ),
            },
            "iCloud": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "iCloud"),
                    os.path.join(_user_profile_folder, "iCloudDrive"),
                ],
                "registry": (
                    None  # iCloud Drive may not have a straightforward registry key
                ),
            },
            "pCloud": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "pCloud"),
                    os.path.join(_user_profile_folder, "pCloudDrive"),
                ],
                "registry": (
                    None  # pCloud may not have a straightforward registry key
                ),
            },
            "Box": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "Box"),
                ],
                "registry": (
                    None
                ),  # Box may not have a straightforward registry key
            },
            "Mega": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "Mega"),
                ],
                "registry": (
                    None
                ),  # Mega may not have a straightforward registry key
            },
            "Yandex": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "YandexDisk"),
                    os.path.join(_user_profile_folder, "Yandex Disk"),
                ],
                "registry": (
                    hkey_current_user,
                    r"Software\Yandex\YandexDisk",
                    "Path",
                ),
            },
            "Amazon Drive": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "AmazonDrive"),
                    os.path.join(_user_profile_folder, "Amazon Drive"),
                ],
                "registry": (
                    None  # Amazon Drive may not have a straightforward registry key
                ),
            },
            "SpiderOak": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "SpiderOak"),
                    os.path.join(_user_profile_folder, "SpiderOakHive"),
                    os.path.join(_user_profile_folder, "SpiderOak Hive"),
                ],
                "registry": (
                    None  # SpiderOak may not have a straightforward registry key
                ),
            },
            "Tresorit": {
                "default_paths": [
                    os.path.join(_user_profile_folder, "Tresorit"),
                    os.path.join(_user_profile_folder, "TresoritDrive"),
                    os.path.join(_user_profile_folder, "Tresorit Drive"),
                ],
                "registry": (
                    None  # Tresorit may not have a straightforward registry key
                ),
            },
        }
        # $ Check each cloud service
        for service_name, info in cloud_service_info.items():
            # Try registry (Windows only)
            if info["registry"] and os_checker.is_os("windows"):
                try:
                    reg_path: Optional[str] = __get_registry_value(
                        *info["registry"]
                    )
                    if reg_path and os.path.isdir(reg_path):
                        _folders.append(reg_path.replace("\\", "/").rstrip("/"))
                        continue
                except Exception as _e:
                    print(
                        f"Error while looking for the cloud folder from {service_name}: {_e}"
                    )
            # Try all default paths
            for default_path in info["default_paths"]:
                try:
                    if os.path.isdir(default_path):
                        _folders.append(
                            default_path.replace("\\", "/").rstrip("/")
                        )
                except Exception as _e:
                    print(f"Error while checking {default_path}: {_e}")
            continue
        return _folders

    # Construct the list of cloud folders by looping over all the found user profiles and
    # determining the cloud folder for each of them.
    cloud_folders: List[str] = []
    for user_profile_folder in list_user_profile_folders():
        if user_profile_folder is None:
            continue
        try:
            if not os.path.isdir(user_profile_folder):
                continue
            folders = list_cloud_folders_for_user(user_profile_folder)
            cloud_folders.extend(folders)
        except Exception as e:
            print(
                f"Error while checking {user_profile_folder} for cloud folders: {e}"
            )
        continue

    # Avoid duplication, meanwhile make sure that the list order is preserved. Then return the de-
    # duplicated list.
    seen = set()
    cloud_folders = [p for p in cloud_folders if not (p in seen or seen.add(p))]

    # Filtering out the folders that don't exist is no longer needed here. That check already
    # happens in the nested function 'list_cloud_folders_for_user()'. Now return the list of cloud
    # Documents folders
    __cloud_folders_cache = cloud_folders
    return cloud_folders


__cloud_documents_folders_cache: Optional[List[str]] = None


def list_cloud_documents_folders() -> List[str]:
    """Most cloud services have a Documents folder.

    Loop over all the cloud folders on this computer and list all the Documents
    folders in there, eg. ['C:/Users/robby/OneDrive/Tiedostot', ]
    """
    global __cloud_documents_folders_cache
    if __cloud_documents_folders_cache:
        return __cloud_documents_folders_cache

    # Use the previous function 'list_cloud_folders()' to list all the cloud folders. Then
    # use that information to figure out the Documents folders in them. Return that here in this
    # function.
    cloud_documents_folders: List[str] = []
    names: List[str] = [
        get_curuser_documents_folder_name(),
    ] + documents_folder_name_candidates
    for cloud_folder in list_cloud_folders():
        for name in names:
            folder = (
                os.path.join(cloud_folder, name).replace("\\", "/").rstrip("/")
            )
            if os.path.isdir(folder):
                cloud_documents_folders.append(folder)
            continue
        continue

    # Return result
    __cloud_documents_folders_cache = cloud_documents_folders
    return cloud_documents_folders


def list_all_documents_folders() -> List[str]:
    """List all Documents folders, both from the user profile folders as from
    the cloud folders."""
    return list_user_documents_folders() + list_cloud_documents_folders()


def is_binary_file(filepath: str | bytes | os.PathLike) -> bool:
    """Fast and accurate binary file detection."""
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(1024)
            if not chunk:  # Empty file
                return False
            if b"\x00" in chunk:  # Fast path - definitely binary
                return True

            # Fallback: check character distribution
            text_chars = bytearray(
                {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F}
            )
            non_text = chunk.translate(None, text_chars)
            return len(non_text) > 30  # More than 30 non-text chars in 1KB
    except (OSError, IOError):
        return False


def is_binary_by_extension(file_path: Union[str, Path]) -> Optional[bool]:
    """
    Check if a file is binary based on its extension.

    Args:
        file_path: Path to the file (string or Path object)

    Returns:
        True if binary, False if text, None if unknown
    """

    # Get the file extension (lowercase, without the dot)
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip(".")

    # Common text file extensions
    text_extensions = {
        # Programming & Markup
        "txt",
        "md",
        "rst",
        "log",
        "csv",
        "tsv",
        "json",
        "xml",
        "yaml",
        "yml",
        "html",
        "htm",
        "css",
        "scss",
        "sass",
        "less",
        "js",
        "jsx",
        "ts",
        "tsx",
        "py",
        "java",
        "c",
        "cpp",
        "h",
        "hpp",
        "cs",
        "php",
        "rb",
        "go",
        "rs",
        "swift",
        "kt",
        "scala",
        "sh",
        "bash",
        "pl",
        "r",
        "lua",
        "sql",
        "vim",
        "el",
        "clj",
        "erl",
        "ex",
        "exs",
        # Config & Data
        "ini",
        "cfg",
        "conf",
        "config",
        "toml",
        "env",
        "properties",
        "gitignore",
        "dockerignore",
        "editorconfig",
        # Documentation
        "tex",
        "latex",
        "bib",
        "org",
        "adoc",
        "asciidoc",
        # Other text formats
        "diff",
        "patch",
        "cmake",
        "makefile",
        "gradle",
    }

    # Common binary file extensions
    binary_extensions = {
        # Images
        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "ico",
        "tiff",
        "tif",
        "webp",
        "svg",
        "psd",
        "ai",
        "raw",
        "cr2",
        "nef",
        "heic",
        # Video
        "mp4",
        "avi",
        "mov",
        "wmv",
        "flv",
        "mkv",
        "webm",
        "m4v",
        "mpg",
        "mpeg",
        # Audio
        "mp3",
        "wav",
        "flac",
        "aac",
        "ogg",
        "wma",
        "m4a",
        "opus",
        # Archives
        "zip",
        "tar",
        "gz",
        "bz2",
        "xz",
        "7z",
        "rar",
        "iso",
        # Executables
        "exe",
        "dll",
        "so",
        "dylib",
        "bin",
        "app",
        "deb",
        "rpm",
        # Documents
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "odt",
        "ods",
        "odp",
        # Databases
        "db",
        "sqlite",
        "sqlite3",
        "mdb",
        # Compiled/Binary
        "pyc",
        "pyo",
        "class",
        "o",
        "obj",
        "wasm",
        # Fonts
        "ttf",
        "otf",
        "woff",
        "woff2",
        "eot",
        # Other binary
        "pkl",
        "pickle",
        "npy",
        "npz",
        "h5",
        "hdf5",
        "parquet",
    }

    if ext in text_extensions:
        return False
    elif ext in binary_extensions:
        return True
    else:
        return None  # Unknown extension


if __name__ == "__main__":
    print(f"Current user profile folder:\n    {get_curuser_profile_folder()}\n")
    print(f"All user profile folders:\n    {list_user_profile_folders()}\n")
    print(
        f"Current user Documents folder:\n    {get_curuser_documents_folder()}\n"
    )
    print(f"All user Documents folders:\n    {list_user_documents_folders()}\n")
    print(f"All cloud folders:\n    {list_cloud_folders()}\n")
    print(
        f"All cloud Documents folders:\n    {list_cloud_documents_folders()}\n"
    )
    print(f"All Documents folders:\n    {list_all_documents_folders()}")
    exit(0)
