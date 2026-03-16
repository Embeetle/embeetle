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
import os, functools, difflib, math, traceback, threading
import qt, data, purefunctions
import hardware_api.file_generator as _file_generator_
import hardware_api.treepath_unicum as _treepath_unicum_
import project_generator.generator.merger as _mg_
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import components.thread_switcher as _sw_
import beetle_console.mini_console as _mini_console_
import components.newfiletreehandler as _newfiletreehandler_
import hardware_api.toolcat_unicum as _toolcat_unicum_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class FileChanger(metaclass=Singleton):
    """DON'T FORGET TO SAVE THE PROJECT AFTER EACH OF THESE OPERATIONS!"""

    def __init__(self) -> None:
        """"""
        super().__init__()
        self.__diff_dialog = None
        self.__mini_console: Optional[_mini_console_.MiniConsole] = None
        return

    # ^                                      CHANGE FILE CONTENT                                       ^#
    # % ============================================================================================== %#
    # % This is the toplevel function to change a file's content (potentially just                     %#
    # % a dry-run to see the effects)                                                                  %#
    # %                                                                                                %#

    def change_file_content(
        self,
        version: Optional[Union[str, int]],
        file_unicum: _treepath_unicum_.TREEPATH_UNIC,
        abspath: str,
        repoints: Optional[Dict],
        dry_run: bool,
        force_new_content: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """SUMMARY ======= Change the file specified by 'file_unicum' and
        located at parameter 'abspath'.

        :param version: Force this version when acquiring new content for the
            file. If None, just take the current version.
        :param file_unicum: Specify the config file.
        :param abspath: Specify location of the config file, whether it exists
            or not. It should not be None.
        :param repoints: Repoints dictionary, to be passed to the new content
            generator.
        :param dry_run: Don't touch anything.
        :param force_new_content: Don't try to merge. Just apply the new
            content. HOW FILE IS CHANGED ==================== New content is
            pulled from the hardware_api/file_generator.py. The new content
            corresponds to all the current(!) settings in the project (possibly
            updated with repoints). RESULT ======= The new (or merged) content
            gets written to the file at the given location. POST-OPERATIONS
            ================ A new file needs to be put in the '.config_orig'
            folder for later use. It must be the con- tent pulled from the
            hardware_api/file_generator.py.
        """
        origthread: qt.QThread = qt.QThread.currentThread()
        assert abspath is not None
        file_data: Dict[str, Union[None, str, bool, int]] = {
            "new_content": None,
            "cur_abspath": abspath,
            "cur_content": None,
            "orig_abspath": None,
            "orig_content": None,
            "res_content": None,
            "has_conflicts": False,
            "diff": 0,
        }

        def merge_completed(
            r_content: Optional[str], has_conflicts: bool, *_args
        ) -> None:
            assert qt.QThread.currentThread() is origthread
            assert not force_new_content
            if r_content is None:
                raise RuntimeError("ERROR: merging files failed")
            file_data["res_content"] = r_content
            file_data["has_conflicts"] = has_conflicts
            finish()
            return

        def finish(*args) -> None:
            assert qt.QThread.currentThread() is origthread
            # & Write resulting content
            # Write the resulting content to the file if this is not a dry-run.
            if not dry_run:
                try:
                    with open(
                        file_data["cur_abspath"],
                        "w",
                        encoding="utf-8",
                        newline="\n",
                    ) as _f:
                        _f.write(file_data["res_content"])
                except Exception as e:
                    purefunctions.printc(
                        f"\n"
                        f'ERROR: Could not write to {q}{file_data["cur_abspath"]}{q}\n'
                        f"\n{traceback.format_exc()}\n",
                        color="error",
                    )

            # & Write new content to 'orig_abspath' for later use
            if not dry_run:
                if not os.path.isfile(file_data["orig_abspath"]):
                    _fp_.make_file(file_data["orig_abspath"])
                with open(
                    file_data["orig_abspath"],
                    "w",
                    encoding="utf-8",
                    newline="\n",
                    errors="replace",
                ) as _f:
                    _f.write(file_data["new_content"])

            # & Compute difference
            diff = 0
            eq = difflib.SequenceMatcher(
                None,
                file_data["cur_content"],
                file_data["res_content"],
            ).ratio()
            if eq == 1.0:
                diff = 0
            else:
                diff = math.ceil(100000 * (1.0 - eq)) / 1000
                if diff == 0:
                    diff = 0.001
            file_data["diff"] = diff

            # & Return results
            if callback is not None:
                callback(file_data, callbackArg)
            return

        # * Start
        # & 1. New content
        new_content: Optional[str] = None
        # $ makefile
        if file_unicum.get_name().upper() == "MAKEFILE":
            new_content = _file_generator_.get_new_makefile(
                boardname=data.current_project.get_board().get_name(),
                chipname=data.current_project.get_chip().get_name(),
                version=version,
            )
        # $ dashboard.mk
        elif file_unicum.get_name().upper() == "DASHBOARD_MK":
            new_content = _file_generator_.get_new_dashboard_mk(
                proj_rootpath=data.current_project.get_proj_rootpath(),
                boardname=data.current_project.get_board().get_name(),
                chipname=data.current_project.get_chip().get_name(),
                probename=data.current_project.get_probe().get_name(),
                toolprefix=data.current_project.get_toolpath_seg().get_compiler_toolchain_prefix(
                    absolute=False
                ),
                flashtool_exename=_toolcat_unicum_.TOOLCAT_UNIC(
                    "FLASHTOOL"
                ).get_flashtool_exename(
                    unique_id=data.current_project.get_toolpath_seg().get_unique_id(
                        "FLASHTOOL"
                    )
                ),
                filepaths={
                    u: (
                        data.current_project.get_treepath_seg().get_abspath(u)
                        if data.current_project.get_treepath_seg().is_relevant(
                            u
                        )
                        else None
                    )
                    for u in data.current_project.get_treepath_seg().get_treepath_unicum_names()
                    if u
                    not in (
                        "BUTTONS_BTL",
                        "MAKEFILE",
                        "DASHBOARD_MK",
                        "FILETREE_MK",
                    )
                },
                repoints=repoints,
                version=version,
            )
        # $ filetree.mk
        elif file_unicum.get_name().upper() == "FILETREE_MK":
            try:
                new_content = data.filetree.api.generate_filetree_mk(
                    template_only=False,
                    version=version,
                )
            except:
                new_content = _newfiletreehandler_.generate_makefile(
                    flat_tree_structure_copy={},
                    project_path=data.current_project.get_proj_rootpath(),
                    external_version=version,
                    template_only=True,
                )
        # $ openocd_chip.cfg
        elif file_unicum.get_name().upper() == "OPENOCD_CHIPFILE":
            new_content = _file_generator_.get_new_openocd_chipcfg_file(
                boardname=data.current_project.get_board().get_name(),
                chipname=data.current_project.get_chip().get_name(),
            )
        # $ openocd_probe.cfg
        elif file_unicum.get_name().upper() == "OPENOCD_PROBEFILE":
            new_content = _file_generator_.get_new_openocd_probecfg_file(
                boardname=data.current_project.get_board().get_name(),
                chipname=data.current_project.get_chip().get_name(),
                probename=data.current_project.get_probe().get_name(),
                transport_protocol_name=data.current_project.get_probe().get_transport_protocol_name(),
            )
        # $ linkerscript.ld
        elif file_unicum.get_name().upper() == "LINKERSCRIPT":
            linkerscript_dict = _file_generator_.get_new_linkerscripts(
                boardname=data.current_project.get_board().get_name(),
                chipname=data.current_project.get_chip().get_name(),
            )
            new_content = linkerscript_dict[list(linkerscript_dict.keys())[0]]
        # $ .gdbinit
        elif file_unicum.get_name().upper() == "GDB_FLASHFILE":
            new_content = _file_generator_.get_new_gdbinit(
                boardname=data.current_project.get_board().get_name(),
                chipname=data.current_project.get_chip().get_name(),
                probename=data.current_project.get_probe().get_name(),
            )
        # $ buttons.btl
        elif file_unicum.get_name().upper() == "BUTTONS_BTL":
            new_content = _file_generator_.get_new_buttonsbtl_file(
                probename=data.current_project.get_probe().get_name(),
            )
        # $ other files
        else:
            raise RuntimeError()
        if new_content is None:
            file_data["new_content"] = ""
        else:
            file_data["new_content"] = new_content.replace("\r\n", "\n")

        # & 2. Current content
        if not os.path.isfile(file_data["cur_abspath"]):
            if not dry_run:
                _fp_.make_file(file_data["cur_abspath"])
            file_data["cur_content"] = ""
        else:
            try:
                with open(
                    file_data["cur_abspath"],
                    "r",
                    encoding="utf-8",
                    newline="\n",
                    errors="replace",
                ) as f:
                    file_data["cur_content"] = f.read().replace("\r\n", "\n")
            except:
                file_data["cur_content"] = ""

        # & 3. Original content
        _orig_abspath = self.__get_original_abspath(file_data["cur_abspath"])
        _orig_content = ""
        if os.path.isfile(_orig_abspath):
            try:
                with open(
                    _orig_abspath,
                    "r",
                    encoding="utf-8",
                    newline="\n",
                    errors="replace",
                ) as f:
                    _orig_content = f.read().replace("\r\n", "\n")
            except:
                _orig_content = ""
        else:
            _orig_content = ""
        file_data["orig_abspath"] = _orig_abspath
        file_data["orig_content"] = _orig_content

        # & 4. Determine case
        # ? ==============[ current and new content are equal ]=============== ?#
        if file_data["cur_content"] == file_data["new_content"]:
            # Do nothing.
            dry_run = True
            file_data["res_content"] = file_data["new_content"]
            finish()
            return

        # ? ======================[ force new content ]======================= ?#
        if force_new_content:
            # Write new content to file if this is not a dry run.
            file_data["res_content"] = file_data["new_content"]
            finish()
            return

        # ? ===================[ current content is empty ]=================== ?#
        if file_data["cur_content"] == "":
            # Write new content to file if this is not a dry run.
            file_data["res_content"] = file_data["new_content"]
            finish()
            return

        # ? =====================[ no original content ]====================== ?#
        if file_data["orig_content"].strip() == "":
            # Write new content to file if this is not a dry run.
            file_data["res_content"] = file_data["new_content"]
            finish()
            return

        # ? ============[ current and original content are equal ]============ ?#
        if file_data["orig_content"] == file_data["cur_content"]:
            # This means the user did not change anything. Simply overwrite file with new content if
            # this is not a dry run.
            file_data["res_content"] = file_data["new_content"]
            finish()
            return

        # ? ============================[ merge ]============================= ?#
        self.__merge_files(
            my_content=file_data["cur_content"],
            ancestor_content=file_data["orig_content"],
            your_content=file_data["new_content"],
            my_title=file_data["cur_abspath"].split("/")[-1]
            + "[current content]",
            ancestor_title=file_data["cur_abspath"].split("/")[-1]
            + "[ancestor content]",
            your_title=file_data["cur_abspath"].split("/")[-1]
            + "[new content]",
            callback=merge_completed,
            callbackArg=None,
        )
        return

    # ^                                      BACKUP CONFIG FOLDER                                      ^#
    # % ============================================================================================== %#
    # % Backup the whole config folder into the .beetle folder.                                        %#
    # %                                                                                                %#

    def get_backup_filename(self) -> str:
        """Get the filename of a backup file that should be next in line."""
        dot_beetle_abspath = _pp_.rel_to_abs(
            rootpath=data.current_project.get_proj_rootpath(),
            relpath=".beetle",
        )
        if not os.path.isdir(dot_beetle_abspath):
            _fp_.make_dir(dot_beetle_abspath)
        assert os.path.isdir(dot_beetle_abspath)
        max_nr = 0
        for name in os.listdir(dot_beetle_abspath):
            if not name.startswith("config_backup"):
                continue
            nr_str = name.replace("config_backup_", "")
            nr_str = nr_str.split(".")[0]
            try:
                nr = int(nr_str)
            except ValueError:
                continue
            if nr > max_nr:
                max_nr = nr
            continue

        return f"config_backup_{max_nr + 1}.7z"

    @_sw_.run_outside_main("make_backup")
    def make_backup(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Backup the 'config' folder in '.beetle'."""
        origthread: qt.QThread = self.make_backup.origthread
        nonmainthread: qt.QThread = self.make_backup.nonmainthread

        # * Obtain paths
        # Obtain and check the paths to all files and folders involved in the
        # backup.
        dot_beetle_abspath = _pp_.rel_to_abs(
            rootpath=data.current_project.get_proj_rootpath(),
            relpath=".beetle",
        )
        config_abspath = _pp_.rel_to_abs(
            rootpath=data.current_project.get_proj_rootpath(), relpath="config"
        )
        backup_name = self.get_backup_filename()
        zip_abspath = _pp_.rel_to_abs(
            rootpath=dot_beetle_abspath,
            relpath=backup_name,
        )
        if not os.path.isdir(dot_beetle_abspath):
            _fp_.make_dir(dot_beetle_abspath)
        if not os.path.isdir(config_abspath):
            purefunctions.printc(
                f"\nERROR: Cannot backup config folder because it doesn{q}t "
                f"exist!\n",
                color="error",
            )
            self.make_backup.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return
        if os.path.exists(zip_abspath):
            purefunctions.printc(
                f"\nERROR: Cannot backup config folder because it there is "
                f"already a backup: {q}{backup_name}{q}!\n",
                color="error",
            )
            self.make_backup.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return
        # At this point, we know that everything is okay: a 'zip_abspath' is
        # determined for the backup and the config folder's location is known.

        def create_miniconsole(*args) -> None:
            "[main thread]"
            assert threading.current_thread() is threading.main_thread()
            if self.__mini_console is not None:
                if qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.close()
                self.__mini_console = None
            self.__mini_console = _mini_console_.MiniConsole(
                "Backup config folder"
            )
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=start_backup,
            )
            return

        def start_backup(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n" "BACKUP CONFIG FOLDER\n" "====================\n",
                "#ad7fa8",
            )
            self.__mini_console.sevenzip_dir_to_file(
                sourcedir_abspath=config_abspath,  # sourcedir_abspath
                targetfile_abspath=zip_abspath,  # targetfile_abspath
                forbidden_dirnames=None,
                forbidden_filenames=None,
                show_prog=True,
                callback=finish,
                callbackArg=None,
                callbackThread=nonmainthread,
            )
            return

        def finish(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                f"\nFinished making backup.\n\n", "#8ae234"
            )

            def delayed_finish(*_args) -> None:
                "[non-main thread]"
                assert qt.QThread.currentThread() is nonmainthread
                self.__mini_console.close()
                self.make_backup.invoke_callback_in_origthread(
                    callback,
                    True,
                    callbackArg,
                )
                return

            qt.QTimer.singleShot(500, delayed_finish)
            return

        # * Start
        assert qt.QThread.currentThread() is nonmainthread
        # Briefly switch to the main thread just to create a MiniConsole()
        # instance there!
        _sw_.switch_thread_modern(
            qthread=_sw_.get_qthread("main"),
            callback=create_miniconsole,
        )
        return

    # ^                                         HELP FUNCTIONS                                         ^#
    # % ============================================================================================== %#
    # % Help functions, especially to merge files.                                                     %#
    # %                                                                                                %#

    def __merge_files(
        self,
        my_content: str,
        ancestor_content: str,
        your_content: str,
        my_title: str,
        ancestor_title: str,
        your_title: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """┌────────────────────────────────────────────────────────┐ │ Merge
        into MINE the changes that would turn ANCESTOR   │ │ into YOURS. │
        └────────────────────────────────────────────────────────┘

        From User's perspective:
            > MINE:     The current file content.
            > ANCESTOR: The content saved in .orig folder.
            > YOURS:    The new generated file content.

        NOTE:
        Only file contents are inputted to and outputted from this function. No actual files are
        being read or written (except from temporary files).

        > callback(r_content, has_conflicts, callbackArg)
        >       r_content:      [str] resulting content
        >       has_conflicts:  [bool] merging failed
        >       callbackArg:    [Any] anything you passed
        """
        assert threading.current_thread() is threading.main_thread()
        if (ancestor_content.strip() == "") or (my_content.strip() == ""):
            callback(
                your_content,
                False,
                callbackArg,
            )
            return

        origthread: qt.QThread = qt.QThread.currentThread()
        mortalthread: qt.QThread = qt.QThread()

        def cleanup_tempfiles(tempfiles: Tuple[str, str, str]) -> None:
            for filepath in tempfiles:
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except OSError as err:
                    print(err)
                    try:
                        if os.path.isfile(filepath):
                            os.unlink(filepath)
                    except OSError as err:
                        print(err)
                        purefunctions.printc(
                            f"\nWARNING: Cannot cleanup merge temp file:\n"
                            f"    > {q}{filepath}{q}\n",
                            color="warning",
                        )
            return

        def try_merge(*args) -> None:
            "[mortal thread]"
            assert qt.QThread.currentThread() is mortalthread
            # $ Sanitize input
            _my_content_: str = my_content.replace("\r\n", "\n")
            _ancestor_content_: str = ancestor_content.replace("\r\n", "\n")
            _your_content_: str = your_content.replace("\r\n", "\n")
            # $ Prepare output
            _r_content_: Optional[str] = None
            _has_conflicts_: bool = False
            _merge_fail_: bool = False
            _tempfiles_: Optional[Tuple[str, str, str]] = None
            # $ Try merge
            try:
                _r_content_, _has_conflicts_, _tempfiles_ = (
                    _mg_.three_way_merge(
                        my_content=_my_content_,
                        ancestor_content=_ancestor_content_,
                        your_content=_your_content_,
                        my_title=my_title,
                        ancestor_title=ancestor_title,
                        your_title=your_title,
                    )
                )
                if _r_content_ is None or not isinstance(_r_content_, str):
                    purefunctions.printc(
                        "\nWARNING: Merging config files failed:\n"
                        "returned content is not a string.\n",
                        color="warning",
                    )
                    _merge_fail_ = True
            except Exception:
                traceback.print_exc()
                purefunctions.printc(
                    "\nWARNING: Merging config files failed.\n",
                    color="warning",
                )
                _merge_fail_ = True
            if _merge_fail_:
                _r_content_ = f"<<<<<<< {my_title}\n"
                _r_content_ += f"{_my_content_}\n"
                _r_content_ += f"=======\n"
                _r_content_ += f"{_your_content_}\n"
                _r_content_ += f">>>>>>> {your_title}"
            # if _has_conflicts_:
            #     print('              THREE-WAY-MERGE WITH CONFLICS!               ')
            #     print('===========================================================')
            #     print('--------------------[ancestor_content]---------------------')
            #     print(_ancestor_content_)
            #     print('')
            #     print('-----------------------[my_content]------------------------')
            #     print(_my_content_)
            #     print('')
            #     print('----------------------[your_content]-----------------------')
            #     print(_your_content_)
            #     print('')
            #     print('-------------------------[result]--------------------------')
            #     print(_r_content_)
            #     print('')
            #     print('===========================================================')
            finish_mt(_r_content_, _merge_fail_ or _has_conflicts_, _tempfiles_)
            return

        def finish_mt(_r_content_, _has_conflicts_, _tempfiles_) -> None:
            "[mortal thread]"
            assert qt.QThread.currentThread() is mortalthread
            _sw_.switch_thread_new(
                qthread=origthread,
                callback=finish_ot,
                args=[_r_content_, _has_conflicts_, _tempfiles_],
            )
            return

        def finish_ot(arg) -> None:
            "[original thread]"
            assert qt.QThread.currentThread() is origthread
            mortalthread.quit()  # Triggers the 'finished' signal.
            _r_content_, _has_conflicts_, _tempfiles_ = arg
            assert isinstance(_r_content_, str), f"_r_content_ = {_r_content_}"
            assert isinstance(_has_conflicts_, bool)
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    cleanup_tempfiles,
                    _tempfiles_,
                ),
            )
            callback(
                _r_content_,
                _has_conflicts_,
                callbackArg,
            )
            return

        def delete_mt(*args) -> None:
            "[original thread]"
            assert qt.QThread.currentThread() is origthread
            assert mortalthread.isFinished()
            _sw_.remove_thread(qthread=mortalthread)
            mortalthread.deleteLater()
            return

        # 'started' signal  => triggered by 'mortalthread.start()'
        # 'finished' signal => triggered by 'mortalthread.quit()'
        # mortalthread.started.connect(
        #     lambda: print('Start mortal thread for merging')
        # )
        mortalthread.finished.connect(delete_mt)  # type: ignore
        mortalthread.start()

        # * 1. Check if 'origthread' is already registered.
        try:
            _sw_.get_name(qthread=origthread)
        except Exception as e:
            if threading.current_thread() is threading.main_thread():
                _sw_.register_thread(name="main", qthread=origthread)
            else:
                purefunctions.printc(
                    "\n"
                    "WARNING: Unknown thread registered at file_changer.py\n"
                    "\n",
                    color="warning",
                )
                _sw_.register_thread(
                    name=f"not_known_thread_{id(origthread)}",
                    qthread=origthread,
                )

        # * 2. Register 'mortalthread'.
        _sw_.register_thread(
            name=f"merge_{id(mortalthread)}",
            qthread=mortalthread,
        )

        # * 3. Start procedure.
        _sw_.switch_thread_new(
            qthread=mortalthread,
            callback=try_merge,
            args=None,
        )
        return

    def __get_original_abspath(self, abspath: str) -> str:
        """Get the abspath to the corresponding config file in the
        '.beetle/.config_orig' folder."""
        assert abspath is not None
        proj_rootpath: str = data.current_project.get_proj_rootpath()
        dot_beetle_dirpath: str = f"{proj_rootpath}/.beetle"
        config_orig_dirpath: Optional[str] = None
        rootpath: Optional[str] = None

        # & Determine root
        if abspath.startswith(proj_rootpath):
            rootpath = proj_rootpath
            config_orig_dirpath = f"{dot_beetle_dirpath}/.config_orig"
        else:
            purefunctions.printc(
                f"\nERROR: __get_original_abspath({q}{abspath}{q}) seems to "
                f"point to a file outside the project folder!\n",
                color="error",
            )
            config_orig_dirpath = f"{dot_beetle_dirpath}/.config_orig"

        # & Create folder
        if not os.path.isdir(config_orig_dirpath):
            try:
                _fp_.make_dir(config_orig_dirpath, catch_err=False)
            except Exception as e:
                purefunctions.printc(
                    f"\nERROR: Cannot create {q}{config_orig_dirpath}{q}\n",
                    color="error",
                )
                traceback.print_exc()
                raise
        assert os.path.isdir(config_orig_dirpath)

        # & Perform path replacement
        if rootpath is not None:
            assert abspath.startswith(rootpath)
            return abspath.replace(rootpath, config_orig_dirpath, 1)
        # No rootpath found. Just use the filename.
        filename = abspath.split("/")[-1]
        return _pp_.rel_to_abs(rootpath=config_orig_dirpath, relpath=filename)

    def delete_corresponding_original(self, abspath: str) -> None:
        """Delete the original config file corresponding to the given one from
        the project."""
        filepath = self.__get_original_abspath(abspath)
        if os.path.isfile(filepath):
            _fp_.delete_file(
                file_abspath=filepath,
                printfunc=print,
                catch_err=False,
            )
        return
