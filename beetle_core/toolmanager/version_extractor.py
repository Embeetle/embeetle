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
from components.singleton import Singleton
import qt
import os
import gui
import re
import subprocess
import datetime
import traceback
import purefunctions
import bpathlib.path_power as _pp_
import fnmatch as _fn_
import os_checker

nop = lambda *a, **k: None
if os_checker.is_os("windows"):
    import win32file  # noqa
if TYPE_CHECKING:
    import gui.dialogs.popupdialog
from various.kristofstuff import *


class VersionExtractor(metaclass=Singleton):
    def __init__(self) -> None:
        super().__init__()
        return

    def is_64bit(self, exepath: str) -> bool:
        """Check bitness of given executable."""
        # & WINDOWS
        if os_checker.is_os("windows"):
            return win32file.GetBinaryType(exepath) == 6
        # & LINUX
        # $ For OpenOCD, also the lib folder must get executable rights!
        if "openocd" in exepath.lower():
            libfolder = None
            binfolder = os.path.dirname(exepath).replace("\\", "/")
            if binfolder.endswith("/"):
                binfolder = binfolder[0:-1]
            if binfolder.endswith("/bin"):
                libfolder = f"{binfolder[0:-3]}lib"
            if libfolder is not None:
                exepath_new = exepath.replace(binfolder, libfolder)
                if os.path.isfile(exepath_new):
                    exepath = exepath_new
        with open(exepath, "rb") as f:
            return f.read(5)[-1] == 2

    def get_patterns(self, toolkind: str) -> List[str]:
        """The pattern for a new tool must be added below, but also in
        'resources/hardware/tool-categories/toolcats.json5'."""
        if toolkind == "COMPILER_TOOLCHAIN":
            return [
                "*gnu*arm*",
                "*arm*gnu*",
                "*gcc*arm*",
                "*arm*gcc*",
                "*clang*arm*",
                "*llvm*arm*",
                "*riscv*",
                "*mips*mti*",
                "*gnu*avr*",
                "*avr*gcc*",
                "*gnu*xtensa*",
                "*xc8*",
                "*xc16*",
                "*xc32*",
                "*xpack*gcc*",
            ]
        if toolkind == "FLASHTOOL":
            return [
                "*openocd*",
                "*pyocd*",
                "*esptool*",
                "*bossac*",
                "*avrdude*",
                "*wchisp*",
                "*pymcuprog*",
                "*flash*prog*",
            ]
        if toolkind == "BUILD_AUTOMATION":
            return [
                "*make*",
            ]
        raise RuntimeError()

    def extract_toolprefix(self, exepath: str) -> Optional[str]:
        """
        Extract TOOLPREFIX such as:
        C:/foobar/arm-none-eabi-
        """
        try:
            p = re.compile(r"([\w-]+)(gcc|cpp|c\+\+)")
            exename = exepath.split("/")[-1]
            m = p.match(exename)
            nameprefix = m.group(1)
            toolprefix = _pp_.rel_to_abs(
                rootpath=os.path.dirname(exepath),
                relpath=nameprefix,
            )
            return toolprefix
        except:
            try:
                p = re.compile(r"([\w-]+)(cc|c\+\+)")
                exename = exepath.split("/")[-1]
                m = p.match(exename)
                nameprefix = m.group(1)
                toolprefix = _pp_.rel_to_abs(
                    rootpath=os.path.dirname(exepath),
                    relpath=nameprefix,
                )
                return toolprefix
            except:
                pass
        return None

    def __filter_toolchain(
        self,
        filename: str,
        filepath: str,
        known_exes: List[str],
    ) -> bool:
        """Return True if the given executable should be ignored."""
        # $ Ignore standard linux gcc compilers
        if _fn_.fnmatch(name=filename, pat="x86_64-linux-gnu-gcc*"):
            return True

        # $ Ignore standard linux gcc compilers
        if filepath in (
            "/usr/bin/c99-gcc",
            "/bin/c99-gcc",
            "/usr/bin/gcc",
            "/bin/gcc",
            "/usr/bin/c89-gcc",
            "/bin/c89-gcc",
        ):
            return True

        # $ Ignore mingw64 compilers on Windows
        if filepath.endswith(
            (
                "mingw64/bin/gcc.exe",
                "mingw64/bin/x86_64-w64-mingw32-gcc.exe",
                "mingw64/bin/cc.exe",
                "yacc.exe",
            )
        ):
            return True

        # $ Ignore yacc and others
        if filepath.replace(".exe", "").endswith(
            (
                "yacc",
                "icc",
            )
        ):
            return True

        # $ Ignore executables that are already found
        if filepath in known_exes:
            return True

        # All filters passed
        return False

    def __try_toolchain(
        self,
        dirpath: str,
        exename: Optional[str],
        known_exes: List[str],
    ) -> Optional[str]:
        """"""
        if not os.path.isdir(dirpath):
            return None
        if exename is None:
            _exename_ = "gcc.exe" if os_checker.is_os("windows") else "gcc"
        else:
            _exename_ = exename.replace(".exe", "")
            _exename_ = (
                f"{_exename_}.exe" if os_checker.is_os("windows") else _exename_
            )
        for prog in os.listdir(dirpath):
            if not prog.endswith(_exename_):
                continue
            filepath = _pp_.rel_to_abs(rootpath=dirpath, relpath=prog)
            if not os.path.isfile(filepath):
                continue
            filename = filepath.split("/")[-1]
            if self.__filter_toolchain(filename, filepath, known_exes):
                continue
            # All filters passed. Return the filepath
            return filepath

        # At this point, nothing was found. If the given exename is 'gcc.exe' (which is the de-
        # fault), then also try 'cc.exe'. Compilers like the Microchip XC8 compiler don't have 'gcc'
        # in the name.
        if _exename_ in ("gcc.exe", "gcc"):
            _exename_ = "cc.exe" if os_checker.is_os("windows") else "cc"
            for prog in os.listdir(dirpath):
                if not prog.endswith(_exename_):
                    continue
                filepath = _pp_.rel_to_abs(rootpath=dirpath, relpath=prog)
                if not os.path.isfile(filepath):
                    continue
                filename = filepath.split("/")[-1]
                if self.__filter_toolchain(filename, filepath, known_exes):
                    continue
                # All filters passed. Return the filepath
                return filepath
        return None

    def extract_executable(
        self,
        dirpath: str,
        exename: Optional[str] = None,
        known_exes: Optional[List[str]] = None,
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """Given a directory, this function tries to find the main executable
        and its kind.

        :param dirpath: The directory to search in.
        :param exename: The name of the executable to search for. This only gets
            used if looking for a compiler toolchain, where several kinds of
            executables are valid choices.
        :param known_exes: A list of full paths to known executables. If the
            found executable is in this list, it gets ignored because it has
            already been extracted and added to Embeetle before.
        :return: (exekind, exepath) with exekind = 'COMPILER_TOOLCHAIN'
            'BUILD_AUTOMATION' 'FLASHTOOL'
        """
        if known_exes is None:
            known_exes = []
        if os.path.isfile(dirpath):
            return None, None
        if not os.path.isdir(dirpath):
            return None, None
        dirpath = _pp_.standardize_abspath(dirpath)
        exepath = None

        def try_relpath(relpath: str) -> Optional[str]:
            # Try relpath as-is
            filepath = _pp_.rel_to_abs(
                rootpath=dirpath,
                relpath=relpath,
            )
            if os_checker.is_os("windows"):
                filepath = f"{filepath}.exe"
            if os.path.isfile(filepath):
                return filepath if filepath not in known_exes else None
            # Try relpath with '-' replaced by '_'
            if "-" in relpath:
                filepath = _pp_.rel_to_abs(
                    rootpath=dirpath,
                    relpath=relpath.replace("-", "_"),
                )
                if os_checker.is_os("windows"):
                    filepath = f"{filepath}.exe"
                if os.path.isfile(filepath):
                    return filepath if filepath not in known_exes else None
            # Try relpath with '_' replaced by '-'
            if "_" in relpath:
                filepath = _pp_.rel_to_abs(
                    rootpath=dirpath,
                    relpath=relpath.replace("_", "-"),
                )
                if os_checker.is_os("windows"):
                    filepath = f"{filepath}.exe"
                if os.path.isfile(filepath):
                    return filepath if filepath not in known_exes else None
            # Nothing found
            return None

        # * FLASHTOOL
        # $ Try 'bin/openocd.exe'
        exepath = try_relpath("bin/openocd")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'openocd.exe'
        exepath = try_relpath("openocd")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'bin/pyocd.exe'
        exepath = try_relpath("bin/pyocd")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'pyocd.exe'
        exepath = try_relpath("pyocd")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'esptool.exe'
        exepath = try_relpath("esptool")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'bin/esptool.exe'
        exepath = try_relpath("bin/esptool")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'avrdude.exe'
        # Try avrdude *after* trying the avr-gcc compiler toolchain. Otherwise,
        # the compiler toolchain is seen as a flashtool!
        # $ Try 'wchisp.exe'
        exepath = try_relpath("wchisp")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'bossac.exe'
        exepath = try_relpath("bossac")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'bin/bossac.exe'
        exepath = try_relpath("bin/bossac")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'pymcuprog.exe'
        exepath = try_relpath("pymcuprog")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'bin/pymcuprog.exe'
        exepath = try_relpath("bin/pymcuprog")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'flash_prog.exe', 'flashprog.exe' and 'fermionic-flash-prog.exe'
        exepath = try_relpath("flash_prog")
        if exepath is not None:
            return "FLASHTOOL", exepath
        exepath = try_relpath("flashprog")
        if exepath is not None:
            return "FLASHTOOL", exepath
        exepath = try_relpath("fermionic-flash-prog")
        if exepath is not None:
            return "FLASHTOOL", exepath
        assert exepath is None

        # * COMPILER_TOOLCHAIN
        # $ 1. Try 'dirpath'
        exepath = self.__try_toolchain(
            dirpath=dirpath,
            exename=exename,
            known_exes=known_exes,
        )
        if exepath is not None:
            return "COMPILER_TOOLCHAIN", exepath

        # $ 2. Try 'dirpath/bin'
        if not (dirpath.endswith("bin") or dirpath.endswith("bin/")):
            exepath = self.__try_toolchain(
                dirpath=_pp_.rel_to_abs(rootpath=dirpath, relpath="bin"),
                exename=exename,
                known_exes=known_exes,
            )
        if exepath is not None:
            return "COMPILER_TOOLCHAIN", exepath
        assert exepath is None

        # * AVRDUDE
        # $ Try 'avrdude.exe'
        exepath = try_relpath("avrdude")
        if exepath is not None:
            return "FLASHTOOL", exepath
        # $ Try 'bin/avrdude.exe'
        exepath = try_relpath("bin/avrdude")
        if exepath is not None:
            return "FLASHTOOL", exepath

        # * BUILD AUTOMATION
        # $ 1. Try 'bin/make.exe'
        exepath = try_relpath("bin/make")
        if exepath is not None:
            return "BUILD_AUTOMATION", exepath
        # $ 2. Try 'make.exe'
        exepath = try_relpath("make")
        if exepath is not None:
            return "BUILD_AUTOMATION", exepath
        assert exepath is None
        return None, None

    def extract_toolversion(
        self,
        exepath: str,
        callback: Optional[Callable],
    ) -> None:
        """Run the executable at 'exepath' with --version flag and extract all
        version info from the stdout and stderr pipes.

        OpenOCD ======= vdict = {     'name'      : 'openocd_nuvoton',
        'unique_id' : 'openocd_0.10.0_dev00973_32b'     'version'   : '0.10.0',
        'suffix'    : '00973',     'bitness'   : '32b',     'date'      :
        datetime.datetime(2018, 11, 27, 0, 0), }
        """

        def finish(
            vdict: Dict[str, Union[str, datetime.datetime, None]],
        ) -> None:
            if vdict is None:
                abort()
                return
            unique_id: Optional[str] = None
            _name: Optional[str] = cast(str, vdict["name"])
            _version: Optional[str] = cast(str, vdict["version"])
            _bitness: Optional[str] = cast(str, vdict["bitness"])
            _suffix: Optional[str] = cast(str, vdict["suffix"])
            if (
                (_name is None)
                or (_name.lower() == "none")
                or (_version is None)
                or (_version.lower() == "none")
                or (_bitness is None)
                or (_bitness.lower() == "none")
            ):
                # Impossible to create unique_id
                pass
            else:
                if (_suffix is None) or (_suffix == "none"):
                    unique_id = f"{_name}_{_version}_{_bitness}"
                else:
                    unique_id = f"{_name}_{_version}_{_suffix}_{_bitness}"
            vdict["unique_id"] = unique_id
            callback(vdict)
            return

        def abort(*args) -> None:
            name = None
            if (exepath is not None) and ("/" in exepath):
                name = exepath.split("/")[-1]
            vdict = {
                "name": name,
                "unique_id": None,
                "version": None,
                "suffix": None,
                "bitness": None,
                "date": None,
            }
            callback(vdict)
            return

        # * Start
        if not os.path.isfile(exepath):
            abort()
            return
        version_output: Optional[str] = None
        version_flag: Optional[str] = None
        if exepath.endswith("esptool") or exepath.endswith("esptool.exe"):
            version_flag = "version"
        elif exepath.endswith("bossac") or exepath.endswith("bossac.exe"):
            version_flag = "--help"
        elif exepath.endswith("avrdude") or exepath.endswith("avrdude.exe"):
            version_flag = "-?"
        elif exepath.endswith("pymcuprog") or exepath.endswith("pymcuprog.exe"):
            version_flag = "-V"
        else:
            version_flag = "--version"

        def get_raw_output() -> str:
            # Obtain the raw output string from the given executable.
            # NOTE:
            # Some executables can only run if the libraries (.dll or .so files) in the executable-
            # directory get loaded. On Windows, that happens automatically. On Linux, one needs to
            # add the executable-directory to the 'LD_LIBRARY_PATH' environment variable. Therefore,
            # I try first to launch the executable as-is. If that fails, I try to launch it with
            # an addition to 'LD_LIBRARY_PATH'.
            # $ WINDOWS
            if os_checker.is_os("windows"):
                output_tuple = purefunctions.subprocess_popen(
                    [exepath, version_flag],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                ).communicate()
                output_str = output_tuple[0].decode("utf-8", errors="ignore")
                if output_str == "":
                    output_str = output_tuple[1].decode(
                        "utf-8", errors="ignore"
                    )
                return output_str
            # $ LINUX
            # output_tuple = purefunctions.subprocess_popen(
            #     [exepath, version_flag],
            #     stdout = subprocess.PIPE,
            #     stderr = subprocess.PIPE,
            #     shell  = False,
            # ).communicate()
            # output_str = output_tuple[0].decode('utf-8', errors='ignore')
            # if output_str == '':
            #     output_str = output_tuple[1].decode('utf-8', errors='ignore')
            # if ('error while loading shared libraries' not in output_str) and \
            #         ('cannot open shared object' not in output_str):
            #     return output_str
            env = dict(os.environ)
            if "LD_LIBRARY_PATH" in env:
                env["LD_LIBRARY_PATH"] = (
                    os.path.dirname(exepath) + ":" + env["LD_LIBRARY_PATH"]
                )
            else:
                env["LD_LIBRARY_PATH"] = os.path.dirname(exepath)
            output_tuple = purefunctions.subprocess_popen(
                [exepath, version_flag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                env=env,
            ).communicate()
            output_str = output_tuple[0].decode("utf-8", errors="ignore")
            if output_str == "":
                output_str = output_tuple[1].decode("utf-8", errors="ignore")
            return output_str

        try:
            # & WINDOWS
            if os_checker.is_os("windows"):
                version_output = get_raw_output()

            # & LINUX
            else:
                try:
                    version_output = get_raw_output()
                except:
                    traceback.print_exc()
                    reply = gui.dialogs.popupdialog.PopupDialog.question(
                        title_text="File permission error",
                        icon_path="icons/gen/lock.png",
                        text=str(
                            f"You don{q}t have execute-permission on this file:<br>"
                            f"<span style={dq}color:{q}#3465a4{q}{dq}>"
                            f"{q}{exepath}{q}</span><br>"
                            f"Do you want to change the file permissions?<br>"
                        ),
                    )
                    if reply == qt.QMessageBox.StandardButton.Yes:
                        try:
                            purefunctions.chmod_recursive(
                                dirpath=os.path.dirname(exepath),
                                mode=0o775,
                            )
                            # $ For OpenOCD, also the lib folder must get executable rights!
                            if "openocd" in exepath.lower():
                                binfolder = os.path.dirname(exepath).replace(
                                    "\\", "/"
                                )
                                if binfolder.endswith("/"):
                                    binfolder = binfolder[0:-1]
                                if binfolder.endswith("/bin"):
                                    libfolder = f"{binfolder[0:-3]}lib"
                                    if os.path.isdir(libfolder):
                                        purefunctions.chmod_recursive(
                                            dirpath=libfolder,
                                            mode=0o775,
                                        )
                            version_output = get_raw_output()
                        except Exception as e:
                            msg = str(e).replace("\n", "<br>")
                            gui.dialogs.popupdialog.PopupDialog.ok(
                                title_text="Cannot run executable",
                                icon_path="icons/dialog/warning.png",
                                text=str(
                                    f"Setting the execute-permission on this file failed:<br>"
                                    f"<span style={dq}color:{q}#3465a4{q}{dq}>"
                                    f"{q}{exepath}{q}</span><br>"
                                    f"<br>"
                                    f"{msg}"
                                    f"<br>"
                                ),
                            )
                            abort()
                            return
                    else:
                        abort()
                        return
        except:
            purefunctions.printc(
                f"\nERROR: Cannot run \n"
                f"    {q}{exepath}{q}\n"
                f"    -> cannot extract toolversion!\n",
                color="error",
            )
            abort()
            return
        if (
            (version_output == "")
            or (version_output is None)
            or (version_output.lower() == "none")
        ):
            abort()
            return

        # * Extract
        assert isinstance(version_output, str)
        # $ PYOCD
        if ("pyocd" in exepath.lower()) or ("pyocd" in version_output.lower()):
            finish(self.__extract_pyocd_version(exepath, version_output))
            return

        # $ OPENOCD
        if (
            ("openocd" in exepath.lower())
            or ("open on-chip" in version_output.lower())
            or ("on-chip debugger" in version_output.lower())
            or ("openocd" in version_output.lower())
        ):
            finish(self.__extract_openocd_version(exepath, version_output))
            return

        # $ AVRDUDE
        if "avrdude" in exepath.lower():
            finish(self.__extract_avrdude_version(exepath, version_output))
            return

        # $ WCHISP
        if "wchisp" in exepath.lower():
            finish(self.__extract_wchisp_version(exepath, version_output))
            return

        # $ BOSSAC
        if "bossac" in exepath.lower():
            finish(self.__extract_bossac_version(exepath, version_output))
            return

        # $ PYMCUPROG
        if "pymcuprog" in exepath.lower():
            finish(self.__extract_pymcuprog_version(exepath, version_output))
            return

        # $ FERMIONIC-FLASH-PROG
        if (
            ("flash_prog" in exepath.lower())
            or ("flashprog" in exepath.lower())
            or ("fermionic-flash-prog" in exepath.lower())
        ):
            finish(
                self.__extract_fermionic_flashprog_version(
                    exepath, version_output
                )
            )
            return

        # $ ESPTOOL
        if "esptool" in exepath.lower():
            finish(self.__extract_esptool_version(exepath, version_output))
            return

        # $ MAKE
        if "make" in exepath.lower():
            finish(self.__extract_make_version(exepath, version_output))
            return

        # $ ARM-NONE-EABI
        if ("arm" in exepath.lower()) and ("gcc" in exepath.lower()):
            finish(
                self.__extract_arm_toolchain_version(exepath, version_output)
            )
            return

        # $ GNU RISCV
        if ("riscv" in exepath.lower()) and ("gcc" in exepath.lower()):
            finish(
                self.__extract_riscv_toolchain_version(exepath, version_output)
            )
            return

        # $ XC8
        if ("xc8" in exepath.lower()) and ("cc" in exepath.lower()):
            finish(
                self.__extract_xc_toolchain_version(
                    "xc8", exepath, version_output
                )
            )
            return

        # $ XC16
        if ("xc16" in exepath.lower()) and ("gcc" in exepath.lower()):
            finish(
                self.__extract_xc_toolchain_version(
                    "xc16", exepath, version_output
                )
            )
            return

        # $ XC32
        if ("xc32" in exepath.lower()) and ("gcc" in exepath.lower()):
            finish(
                self.__extract_xc_toolchain_version(
                    "xc32", exepath, version_output
                )
            )
            return

        # $ MIPS-MTI
        if ("mips" in exepath.lower()) and ("mti" in exepath.lower()):
            finish(
                self.__extract_mips_mti_toolchain_version(
                    exepath, version_output
                )
            )
            return

        # $ GNU XTENSA ESP32
        if ("xtensa" in exepath.lower()) and ("esp32" in exepath.lower()):
            finish(
                self.__extract_esp32_toolchain_version(exepath, version_output)
            )
            return

        # $ GNU AVR
        if ("avr" in exepath.lower()) and ("gcc" in exepath.lower()):
            finish(
                self.__extract_avr_toolchain_version(exepath, version_output)
            )
            return

        abort()
        return

    def __extract_openocd_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "openocd"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        if "openocd_giga_longan" in exepath.lower().replace("-", "_"):
            name = "openocd_giga_longan"
        elif "openocd_giga" in exepath.lower().replace("-", "_"):
            name = "openocd_giga"
        elif "openocd_nuvoton" in exepath.lower().replace("-", "_"):
            name = "openocd_nuvoton"
        elif "openocd_riscv" in exepath.lower().replace("-", "_"):
            name = "openocd_riscv"
        elif "openocd_atmosic" in exepath.lower().replace("-", "_"):
            name = "openocd_atmosic"
        elif "openocd_wch" in exepath.lower().replace("-", "_"):
            name = "openocd_wch"
        elif "openocd_hpmicro" in exepath.lower().replace("-", "_"):
            name = "openocd_hpmicro"
        elif "openocd_cip" in exepath.lower().replace("-", "_"):
            name = "openocd_cip"
        elif "openocd_geehy" in exepath.lower().replace("-", "_"):
            name = "openocd_geehy"
        elif "openocd_synwit" in exepath.lower().replace("-", "_"):
            name = "openocd_synwit"

        # & Version
        def get_version() -> Optional[str]:
            # This works for strings like:
            # xPack OpenOCD, i386 Open On-Chip Debugger 0.10.0+dev-00002-gf1a0b8e47
            # xPack OpenOCD x86_64 Open On-Chip Debugger 0.11.0-3+dev1.0.2-dirty
            # xPack Open On-Chip Debugger 0.12.0-01004-g9ea7f3d64-dirty
            p = re.compile(r"\d+\.\d+\.\d+")
            m = p.search(version_output)
            if m is None:
                return None
            return m.group(0)

        try:
            version = get_version()
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        if version is None:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )

        # & Suffix
        def get_suffix() -> Optional[str]:
            # Note:
            # The string 'dev' is never included in the suffix returned by this subfunction. It gets
            # added later on.
            # xPack OpenOCD, i386 Open On-Chip Debugger 0.10.0+dev-00002-gf1a0b8e47
            # dev = group 3
            p = re.compile(r"(\d+\.\d+\.\d+)[+-](dev-(\d+))")
            m = p.search(version_output)
            if m is not None:
                if m.group(3) is not None:
                    return m.group(3)
            # Open On-Chip Debugger 0.12.0-rc2+dev-00019-g9d925776b-dirty
            # dev = group 3
            p = re.compile(r"(\d+\.\d+\.\d+)[+-]rc.*(dev-(\d+))")
            m = p.search(version_output)
            if m is not None:
                if m.group(3) is not None:
                    return m.group(3)
            # xPack OpenOCD x86_64 Open On-Chip Debugger 0.11.0-3+dev1.0.2-dirty
            # dev = group 2
            p = re.compile(r"(\d+\.\d+\.\d+).*dev(\d+\.\d+\.\d+)")
            m = p.search(version_output)
            if m is not None:
                if m.group(2) is not None:
                    return m.group(2)
            # xPack Open On-Chip Debugger 0.12.0-01004-g9ea7f3d64-dirty
            # dev = group 2
            p = re.compile(r"(\d+\.\d+\.\d+)[+-](\d\d\d+)")
            m = p.search(version_output)
            if m is not None:
                if m.group(2) is not None:
                    return m.group(2)
            # xPack Open On-Chip Debugger 0.12.0+dev-gd0e757444-dirty (2023-10-26-14:20)
            # xPack OpenOCD x86_64 Open On-Chip Debugger 0.11.0+dev (2022-09-01-17:58)
            return None

        try:
            suffix = get_suffix()
            if suffix is not None:
                suffix = f"dev{suffix}"
        except:
            pass
        if suffix is None:
            # Use the date as suffix
            pass

        # & Bitness
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # & Date
        try:
            p = re.compile(r"(20\d\d)-(\d\d)-(\d\d)")
            m = p.search(version_output)
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract build-date from {q}{exepath}{q}",
                color="warning",
            )
        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
            if suffix is None:
                suffix = f"dev{year}{month}{day}"
        else:
            date = None

        # & Dirty hack
        # For HPMicro, the Windows and Linux OpenOCD version suffixes differ. To get around this
        # issue, I will tweak the returned Linux version suffix for now.
        if "hpmicro" in name:
            if suffix == "dev202388":
                suffix = "dev202239"

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_avrdude_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "avrdude"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"version\s*(\d+\.\d+\.?\d*)")
            m = p.search(version_output)
            version = m.group(1)
            # If the version is only a number like '6.3', transform it into
            # three digits like '6.3.0'
            if version.count(".") == 1:
                version += ".0"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # $ Date
        try:
            p = re.compile(r"(20\d\d)(\d\d)(\d\d)")
            m = p.search(version_output)
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
        except:
            # Date and hash are omitted for release versions of avrdude.
            pass

        # $ Suffix (hash nr)
        try:
            p = re.compile(r"(20\d\d\d\d\d\d)\s*(\([\d\w]+\))")
            m = p.search(version_output)
            suffix = m.group(2)
            suffix = suffix.replace("(", "").replace(")", "")
        except:
            # In Johan's build, the date is omitted but hash nr is present. The hash nr is 7 chars.
            try:
                p = re.compile(r"\([\d\w]{7}\)")
                m = p.search(version_output)
                suffix = m.group(0)
                suffix = suffix.replace("(", "").replace(")", "")
            except:
                # Date and hash are omitted for release versions of avrdude.
                pass

        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_wchisp_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "wchisp"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"\d+\.\d+\.\d+")
            m = p.search(version_output)
            version = m.group(0)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # $ Date
        pass

        # $ Suffix (hash nr)
        pass

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_bossac_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "bossac"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"Version\s*(\d\.\d\.\d)")
            m = p.search(version_output)
            version = m.group(1)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        try:
            p = re.compile(r"(20\d\d)-(20\d\d)")
            m = p.search(version_output)
            year = int(m.group(2))
            month = 1
            day = 1
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract build-date from {q}{exepath}{q}",
                color="warning",
            )
        if (year is not None) and (month is not None) and (day is not None):
            try:
                date = datetime.datetime(
                    year=year,
                    month=month,
                    day=day,
                )
            except:
                purefunctions.printc(
                    f"\nWARNING: Invalid build-date: {q}{day}/{month}/{year}{q}",
                    color="warning",
                )
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_pymcuprog_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "pymcuprog"
        version = None
        suffix = None
        bitness = None
        date = None
        try:
            p = re.compile(r"(\d+)(\.\d+)(\.\d+)?(\.\d+)?")
            m = p.search(version_output)
            version = m.group(0)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_fermionic_flashprog_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "fermionic-flash-prog"
        version = None
        suffix = None
        bitness = None
        date = None
        try:
            p = re.compile(r"(\d+)(\.\d+)(\.\d+)?(\.\d+)?")
            m = p.search(version_output)
            version = m.group(0)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_pyocd_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "pyocd"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"(\d+\.\d+\.\d+)([+-.](dev-?(\d+)))?")
            m = p.search(version_output)
            version = m.group(1)
            try:
                suffix = f"dev{m.group(4)}"
            except:
                purefunctions.printc(
                    f"\nWARNING: Cannot extract suffix from: {q}{exepath}{q}",
                    color="warning",
                )
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        try:
            p = re.compile(r"(20\d\d)-(\d\d)-(\d\d)")
            m = p.search(version_output)
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
        except:
            pass
            # print(f"\nWARNING: Cannot extract build-date from '{exepath}'")
        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_esptool_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "esptool"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"(\d+\.\d+)(-(dev(\d*)))?")
            m = p.search(version_output)
            version = m.group(1)
            try:
                suffix = m.group(3)
            except:
                # Perhaps there just is no '-dev' suffix
                pass
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_make_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "gnu_make"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"\d+\.\d+\.\d+")
            m = p.search(version_output)
            version = m.group(0)
            suffix = None
        except:
            try:
                p = re.compile(r"gnu.make.(\d\.\d+)")
                m = p.search(version_output.lower())
                version = m.group(1)
                version = f"{version}.0"
            except:
                purefunctions.printc(
                    f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                    color="warning",
                )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        try:
            p = re.compile(r"19\d\d\w*-\w*(20\d\d)")
            m = p.search(version_output)
            year = int(m.group(1))
            month = 1
            day = 1
        except:
            try:
                p = re.compile(r"20\d\d")
                m = p.search(version_output)
                year = int(m.group(0))
                month = 1
                day = 1
            except:
                purefunctions.printc(
                    f"\nWARNING: Cannot extract build-date from {q}{exepath}{q}",
                    color="warning",
                )
        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(year=year, month=month, day=day)
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_arm_toolchain_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "gnu_arm_toolchain"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            # Determine basic version no, like '9.3.1'
            p = re.compile(r"\d+\.\d+\.\d+")
            m = p.search(version_output)
            version = m.group(0)
            try:
                # Determine suffix like '9-2020-q2-update'
                p = re.compile(r"\d+-20\d+-q\d-\w+")
                m = p.search(version_output)
                suffix = m.group(0)
            except:
                try:
                    # Determine suffix like '20140228'
                    p = re.compile(r"20\d\d\d\d\d\d")
                    m = p.search(version_output)
                    suffix = m.group(0)
                except:
                    purefunctions.printc(
                        f"\nWARNING: Cannot extract suffix from: {q}{exepath}{q}",
                        color="warning",
                    )
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )
        try:
            p = re.compile(r"(20\d\d)[-.]?(\d\d)[-.]?(\d\d)")
            m = p.search(version_output)
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract build-date from {q}{exepath}{q}",
                color="warning",
            )
        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_riscv_toolchain_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """
        Note: date is hardcoded here per version nr.
        """
        name = None
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        source = "other"
        if ("xpack" in exepath.lower()) or ("xpack" in version_output.lower()):
            source = "xpack"
        elif ("sifive" in exepath.lower()) or (
            "sifive" in version_output.lower()
        ):
            source = "sifive"

        # * xPack
        if source == "xpack":
            # $ Hardcoded suffixes and dates
            # For each main version of the RISCV-toolchain, there is also a suffix. Unfortunately,
            # the xPack doesn't show them in the '--version' output. I've compiled a dictionary be-
            # low with only the latest suffixes shown. It should be a step towards a better solut-
            # ion.
            hardcoded_suffixes_and_dates = {
                "8.2.0": {
                    "suffix": "3.1",
                    "date": datetime.datetime(
                        year=2019,
                        month=7,
                        day=31,
                    ),
                },
                "8.3.0": {
                    "suffix": "2.3",
                    "date": datetime.datetime(
                        year=2020,
                        month=10,
                        day=25,
                    ),
                },
                "10.1.0": {
                    "suffix": "1.2",
                    "date": datetime.datetime(
                        year=2021,
                        month=11,
                        day=4,
                    ),
                },
                "10.2.0": {
                    "suffix": "1.2",
                    "date": datetime.datetime(
                        year=2021,
                        month=11,
                        day=11,
                    ),
                },
                "11.3.0": {
                    "suffix": "1",
                    "date": datetime.datetime(
                        year=2022,
                        month=5,
                        day=14,
                    ),
                },
                "12.1.0": {
                    "suffix": "2",
                    "date": datetime.datetime(
                        year=2022,
                        month=5,
                        day=18,
                    ),
                },
                "12.2.0": {
                    "suffix": "3",
                    "date": datetime.datetime(
                        year=2023,
                        month=2,
                        day=5,
                    ),
                },
            }

            # $ Name
            name = "gnu_riscv_xpack_toolchain"

            # $ Version
            try:
                p = re.compile(r"\d+\.\d+\.\d+")
                m = p.search(version_output)
                version = m.group(0)
            except:
                version = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                    color="warning",
                )

            # $ Suffix
            try:
                suffix = hardcoded_suffixes_and_dates[version]["suffix"]
            except:
                suffix = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract suffix from: {q}{exepath}{q}",
                    color="warning",
                )

            # $ Bitness
            try:
                bitness = "64b" if self.is_64bit(exepath) else "32b"
            except:
                bitness = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                    color="warning",
                )

            # $ Date
            try:
                date = hardcoded_suffixes_and_dates[version]["date"]
            except:
                date = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract date from: {q}{exepath}{q}",
                    color="warning",
                )

        # * SiFive
        elif source == "sifive":
            # $ Name
            name = "gnu_riscv_sifive_toolchain"

            # $ Version
            try:
                p = re.compile(r"(\d+\.\d+\.\d+)-?((20\d+)\.(\d+)\.(\d+))?")
                m = p.search(version_output)
                version = m.group(1)
            except:
                version = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                    color="warning",
                )

            # $ Suffix
            suffix = None

            # $ Bitness
            try:
                bitness = "64b" if self.is_64bit(exepath) else "32b"
            except:
                purefunctions.printc(
                    f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                    color="warning",
                )

            # $ Date
            try:
                p = re.compile(r"(20\d+)\.(\d+)\.(\d+)")
                m = p.search(version_output)
                year = int(m.group(1))
                month = int(m.group(2))
                day = int(m.group(3))
                day = 1 if day == 0 else day
                date = datetime.datetime(
                    year=year,
                    month=month,
                    day=day,
                )
            except:
                date = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract date from: {q}{exepath}{q}",
                    color="warning",
                )

        # * Other
        elif source == "other":
            # $ Name
            name = "gnu_riscv_toolchain"

            # $ Version
            try:
                p = re.compile(r"(\d+\.\d+\.\d+)")
                m = p.search(version_output)
                version = m.group(1)
            except:
                version = None
                purefunctions.printc(
                    f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                    color="warning",
                )

            # $ Suffix
            suffix = None

            # $ Bitness
            try:
                bitness = "64b" if self.is_64bit(exepath) else "32b"
            except:
                purefunctions.printc(
                    f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                    color="warning",
                )

            # $ Date
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_xc_toolchain_version(
        self,
        xc: str,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "xc8_toolchain"
        if xc == "xc8":
            name = "xc8_toolchain"
        elif xc == "xc16":
            name = "xc16_toolchain"
        elif xc == "xc32":
            name = "xc32_toolchain"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None

        def month_to_num(_month_str: str) -> Optional[int]:
            return {
                "jan": 1,
                "feb": 2,
                "mar": 3,
                "apr": 4,
                "may": 5,
                "jun": 6,
                "jul": 7,
                "aug": 8,
                "sep": 9,
                "oct": 10,
                "nov": 11,
                "dec": 12,
            }.get(_month_str, None)

        # $ Version
        try:
            p = re.compile(r"v(\d+\.\d+)")
            m = p.search(version_output.lower())
            version = m.group(1)
        except:
            version = None
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )

        # $ Suffix
        # No suffix for this compiler

        # $ Bitness
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            bitness = None
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # $ Date
        try:
            p = re.compile(r"Build date:\s(\w+)\s*(\d+)\s*(\d+)")
            m = p.search(version_output)
            month = month_to_num(m.group(1).lower())
            day = int(m.group(2))
            day = 1 if day == 0 else day
            year = int(m.group(3))
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract build date from {q}{exepath}{q}",
                color="warning",
            )
        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_mips_mti_toolchain_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "mips_mti_toolchain"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None

        # & Version nr
        try:
            p = re.compile(r"\d+\.\d+\.\d+")
            m = p.search(version_output)
            version = m.group(0)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract suffix from: {q}{exepath}{q}",
                color="warning",
            )

        # & Bitness
        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # & Date
        try:
            p = re.compile(r"(20\d\d)[-.]?(\d\d)[-.]?(\d\d)")
            m = p.search(version_output)
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract build-date from {q}{exepath}{q}",
                color="warning",
            )
        if (year is not None) and (month is not None) and (day is not None):
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
        else:
            date = None

        # & Suffix
        # Suffixes don't match on Windows vs Linux, so it's better to leave them out.

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_avr_toolchain_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "gnu_avr_toolchain"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"(\d+\.\d+\.\d+)")
            m = p.search(version_output)
            version = m.group(1)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )

        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # $ date only contains the year
        try:
            p = re.compile(r"(20\d\d)\s")
            m = p.search(version_output)
            year = int(m.group(1))
            month = 1
            day = 1
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract build-date from: {q}{exepath}{q}",
                color="warning",
            )
        if year is not None:
            date = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )
        else:
            date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }

    def __extract_esp32_toolchain_version(
        self,
        exepath: str,
        version_output: str,
    ) -> Dict[str, Union[str, datetime.datetime]]:
        """"""
        name = "gnu_xtensa_esp32_toolchain"
        version = None
        suffix = None
        bitness = None
        date = None
        year, month, day = None, None, None
        try:
            p = re.compile(r"(\d+\.\d+\.\d+)(?!-)")
            m = p.search(version_output)
            version = m.group(1)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract version from: {q}{exepath}{q}",
                color="warning",
            )

        try:
            p = re.compile(r"crosstool-ng-([.\-\w]+)")
            m = p.search(version_output)
            suffix = m.group(1)
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract suffix from: {q}{exepath}{q}",
                color="warning",
            )

        try:
            bitness = "64b" if self.is_64bit(exepath) else "32b"
        except:
            purefunctions.printc(
                f"\nWARNING: Cannot extract bitness from {q}{exepath}{q}",
                color="warning",
            )

        # $ date not known
        date = None

        return {
            "name": name,
            "version": version,
            "suffix": suffix,
            "bitness": bitness,
            "date": date,
        }
