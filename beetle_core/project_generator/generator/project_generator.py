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
import threading, os, re
import qt, data, functions, serverfunctions
import components.thread_switcher as _sw_
import beetle_console.mini_console as _mini_console_
import bpathlib.file_power as _fp_
from various.kristofstuff import *


class ProjectDiskGenerator(metaclass=Singleton):
    """STARTING FROM A Project()-INSTANCE, THIS SINGLETON CAN CREATE THE ACTUAL
    PROJECT ON THE HARDDISK."""

    def __init__(self) -> None:
        """"""
        super().__init__()
        assert threading.current_thread() is threading.main_thread()
        _sw_.register_thread(
            name="main",
            qthread=qt.QThread.currentThread(),
        )
        self.__mini_console: Optional[_mini_console_.MiniConsole] = None
        return

    @_sw_.run_outside_main("download_and_unzip")
    def download_and_unzip(
        self,
        urlstr: str,
        target_dirpath: str,
        erase_if_failed: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Create a MiniConsole()-instance and use it to download the given
        file. Unzip the file to the 'target_dirpath'. The 'target_dirpath' will
        be created if doesn't exist yet.

        NOTES:
          - The 'target_dirpath' will be created if it doesn't exist yet.

          - The 'target_dirpath' will be cleaned if it already exists.

          - The unzipped content ends up directly into the 'target_dirpath',
            not in yet another subfolder.

        :param urlstr:          URL to the zipfile.

        :param target_dirpath:  Target directory where the unzipped content will
                                end up.

        :param erase_if_failed: Erase target directory if download failed.

            > callback(success, callbackArg)
        """
        origthread = self.download_and_unzip.origthread
        nonmainthread = self.download_and_unzip.nonmainthread
        assert origthread is _sw_.get_qthread("main")

        def start(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            # Briefly switch to the main thread
            # just to create a MiniConsole() instance
            # there!
            _sw_.switch_thread_modern(
                qthread=origthread,
                callback=create_miniconsole,
            )
            return

        def create_miniconsole(*args):
            "[main thread]"
            assert qt.QThread.currentThread() is origthread
            assert threading.current_thread() is threading.main_thread()
            if self.__mini_console is not None:
                if qt.sip.isdeleted(self.__mini_console):
                    pass
                else:
                    self.__mini_console.close()
                self.__mini_console = None
            self.__mini_console = _mini_console_.MiniConsole("Download")
            _sw_.switch_thread_modern(
                qthread=nonmainthread,
                callback=print_intro,
            )
            return

        def print_intro(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n" "DOWNLOAD\n" "========\n",
                "#ad7fa8",
            )
            clean()
            return

        def clean(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if os.path.isdir(target_dirpath):
                success = _fp_.clean_dir(
                    dir_abspath=target_dirpath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                )
            else:
                success = _fp_.make_dir(
                    dir_abspath=target_dirpath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                    overwr=False,
                )
            if not success:
                abort()
                return
            download()
            return

        def download(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.download_file(
                url=urlstr,
                show_prog=True,
                callback=unzip,
                callbackArg=None,
            )
            return

        def unzip(
            success: bool,
            error_description: Optional[str],
            filepath: str,
            *args,
        ) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if not success:
                abort(error_description)
                return
            protocol = ".7z"
            p = re.compile(r"(.*)\?id=")
            m = p.match(urlstr)
            if m is not None:
                _urlstr = m.group(1)
                if _urlstr.endswith(".zip"):
                    protocol = ".zip"
            self.__mini_console.sevenunzip_file_to_dir(
                spath=filepath,
                dpath=target_dirpath,
                show_prog=True,
                protocol=protocol,
                callback=finish_unzip,
                callbackArg=None,
                callbackThread=nonmainthread,
            )
            return

        def finish_unzip(arg) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            if isinstance(arg, bool):
                success = arg
            else:
                success, _ = arg
            if not success:
                abort()
                return
            finish()
            return

        def abort(error_description: Optional[str] = None, *args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n" "Download failed.\n\n",
                "#ef2929",
            )
            if erase_if_failed:
                _fp_.delete_dir(
                    dir_abspath=target_dirpath,
                    printfunc=self.__mini_console.printout,
                    catch_err=True,
                    allow_rootpath_deletion=True,
                )
            self.__mini_console.printout("\n\n")

            # $ Specific URL error
            if (
                (error_description == "urllib.error.ContentTooShortError")
                or (error_description == "urllib.error.HTTPError")
                or (error_description == "urllib.error.URLError")
            ):
                self.__mini_console.printout(
                    f"The download failed because of the following reason:\n"
                    f"{q}{error_description}{q}\n"
                    f"Maybe our server is down. Please copy the content of this "
                    f"console and mail it to:\n",
                    "#ffffff",
                )
                self.__mini_console.printout(
                    "info@embeetle.com\n",
                    "#729fcf",
                )

            # $ Timeout error
            if error_description == "socket.timeout":
                self.__mini_console.printout(
                    f"The download failed because of a server timeout. This can "
                    f"happen when our server is under heavy load. Please try again. "
                    f"Contact us if the problem persists:\n",
                    "#ffffff",
                )
                self.__mini_console.printout(
                    "info@embeetle.com\n",
                    "#729fcf",
                )

            # $ Unknown error
            if error_description == "other":
                self.__mini_console.printout(
                    f"The download failed for not known reasons. Please copy the "
                    f"content of this console and mail it to:\n",
                    "#ffffff",
                )
                self.__mini_console.printout(
                    "info@embeetle.com\n",
                    "#729fcf",
                )

            self.download_and_unzip.invoke_callback_in_origthread(
                callback,
                False,
                callbackArg,
            )
            return

        def finish(*args) -> None:
            "[non-main thread]"
            assert qt.QThread.currentThread() is nonmainthread
            self.__mini_console.printout(
                "\n\n" "FINISH \n" "=======\n",
                "#fcaf3e",
            )
            self.__mini_console.printout(
                "Congratulations!\n\n",
                "#ffffff",
            )

            def delayed_finish(*_args):
                "[non-main thread]"
                assert qt.QThread.currentThread() is nonmainthread
                self.__mini_console.close()
                self.download_and_unzip.invoke_callback_in_origthread(
                    callback,
                    True,
                    callbackArg,
                )
                return

            qt.QTimer.singleShot(500, delayed_finish)
            return

        start()
        return

    def download_sample_project(
        self,
        serverpath: str,
        project_rootpath: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Download a sample project from the server and unzip it in the project
        rootpath.

        :param serverpath: Relative path to the zipped sample project on the
            server, in the format "<manufacturer>/<boardfamily>/<project-name>"
            eg. "stmicro/nucleo/nucleo-l412kb.7z". (the ".7z" is part of the
            <project-name>)
            The serverpath then gets glued onto the base url which is:
            "https://embeetle.com/downloads/projects_mx/"
            or
            "https://new.embeetle.com/downloads/projects_mx/"

            MIGRATION TO GITHUB:
            The project paths on GitHub have this format:
            "https://github.com/Embeetle/projects/releases/download/<manufacturer>/<project-name>"
            eg.
            "https://github.com/Embeetle/projects/releases/download/wch/ch32v003f4p6-evt-r0-1v1.7z"
            The `serverpath` parameter is used now to construct this URL, but as
            you can see, only the `<manufacturer>` and `<project-name>` parts of
            the parameter are used.

        :param project_rootpath: Absolute path to folder where download must end
                                 up.

        > callback(success, callbackArg)
        """
        # Determine makefile version (deprecated)
        # ==========================
        # To determine the makefile version for the new project, I perform the
        # same procedure here as in 'functions.get_remote_beetle_projlist()',
        # which is the function that Matic calls to get info about the projects
        # on the server.
        # version: Optional[int] = None
        # if data.makefile_version_new_projects is not None:
        #     version = data.makefile_version_new_projects
        # else:
        #     version = functions.get_latest_makefile_interface_version()
        #
        # MIGRATION TO GITHUB:
        # Makefile versions for new projects are deprecated. We only put the
        # projects with the latest makefile version on GitHub.

        # Embeetle Unique Identifier
        # ==========================
        # Glue the Embeetle Unique Identifier to the URL request.
        # Deprecated now, since we migrate to GitHub.
        # guid = functions.get_embeetle_unique_identifier()
        #
        # MIGRATION TO GITHUB:
        # Gluing the Embeetle Unique Identifier to the URL request is irrelevant
        # since the migration to GitHub.

        # Construct URL
        # =============
        # proj_url = f"{serverfunctions.get_base_url_wfb()}/downloads/projects_m{version}/{serverpath}?id={guid}"
        manufacturer, boardfamily, project_name = serverpath.split("/")
        proj_url = f"https://github.com/Embeetle/projects/releases/download/{manufacturer}/{project_name}"

        # Download and Unzip
        # ==================
        self.download_and_unzip(
            urlstr=proj_url,
            target_dirpath=project_rootpath,
            erase_if_failed=True,
            callback=callback,
            callbackArg=callbackArg,
        )
        return
