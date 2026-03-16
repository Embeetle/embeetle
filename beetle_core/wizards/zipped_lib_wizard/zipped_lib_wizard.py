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
import qt, data, functions, gui
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import wizards.lib_wizard.storage_widgets.proj_storage_groupbox as _proj_storage_groupbox_
import wizards.lib_wizard.storage_widgets.local_storage_groupbox as _local_storage_groupbox_
import wizards.zipped_lib_wizard.zipped_lib_groupbox as _zipped_lib_groupbox_
import libmanager.libmanager as _libmanager_

if TYPE_CHECKING:
    import gui.dialogs.popupdialog

from various.kristofstuff import *


class ZippedLibWizard(_gen_wizard_.GeneralWizard):
    """┌── self.main_layout ──────────────────────────────────────────────────┐
    │                                                                      │ │
    ┌──── self.__zipfile_groupbox ─────────────────────────────────┐    │ │  │ │
    │ │  └──────────────────────────────────────────────────────────────┘ │ │
    ┌──── self.__proj_storage_groupbox ────────────────────────────┐    │ │ │
    │    │ │ └──────────────────────────────────────────────────────────────┘
    │ │ [ CANCEL ]       [ ADD LIBRARY ]                   │
    └──────────────────────────────────────────────────────────────────────┘"""

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        if parent is None:
            parent = data.main_form
        super().__init__(parent)
        self.setWindowTitle(f"Add Library from Zipfile")
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        #! =====================[ SELECT ZIPPED LIBRARY ]=====================!#
        self.__zipfile_groupbox = _zipped_lib_groupbox_.ZippedLibGroupbox(
            parent=self,
        )
        self.main_layout.addWidget(
            self.__zipfile_groupbox,
        )

        #! =====================[ PROJ STORAGE GROUPBOX ]=====================!#
        self.__proj_storage_groupbox: Optional[
            _proj_storage_groupbox_.ProjStorageGroupBox
        ] = None
        self.__local_storage_groupbox: Optional[
            _local_storage_groupbox_.LocalStorageGroupBox
        ] = None
        if not data.is_home:
            self.__proj_storage_groupbox = (
                _proj_storage_groupbox_.ProjStorageGroupBox(
                    parent=self, title="Unzip library to:"
                )
            )
            self.main_layout.addWidget(
                self.__proj_storage_groupbox,
            )
        else:
            self.__local_storage_groupbox = (
                _local_storage_groupbox_.LocalStorageGroupBox(
                    parent=self, title="Unzip library to:"
                )
            )
            self.main_layout.addWidget(
                self.__local_storage_groupbox,
            )

        #! ====================[ CATEGORY WARNING LABEL ]=====================!#
        self.__category_warning_lbl: qt.QLabel = qt.QLabel()
        self.__category_warning_lbl.setStyleSheet(
            """
        QLabel {
            background: transparent;
            color: #2e3436;
            border: none;
        }
        """
        )
        self.__category_warning_lbl.setFont(data.get_general_font())
        self.__category_warning_lbl.setWordWrap(True)
        self.main_layout.addWidget(
            self.__category_warning_lbl,
        )
        self.__category_warning_lbl.hide()

        #! =====================[ CANCEL AND SAVE BTNS ]======================!#
        self.main_layout.addStretch()
        self.add_page_buttons()
        self.next_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.resize_and_center()
        self.repurpose_cancel_next_buttons(
            cancel_name="CANCEL",
            cancel_func=self._cancel_clicked,
            cancel_en=True,
            next_name=" ADD LIBRARY ",
            next_func=self.__final_btn_clicked,
            next_en=True,
        )
        self.resize_and_center()
        return

    def resize_and_center(self, *args) -> None:
        """"""
        self.resize(cast(qt.QSize, self.main_layout.sizeHint() * 1.1))  # type: ignore
        self.center_to_parent()
        # self.adjustSize()
        try:
            w, h = functions.get_screen_size()
        except:
            s = functions.get_screen_size()
            w = s.width()
            h = s.height()
        self.resize(int(w * 0.5), int(h * 0.5))
        return

    def show(self, category_prefill: Optional[str] = None) -> None:
        """Show this LibWizard()-instance and prefill the category, if given."""
        if category_prefill is not None:
            if category_prefill == "Signal Input-Output":
                category_prefill = "Signal Input/Output"
            self.__category_warning_lbl.setText(
                f"WARNING: The unzipped library won{q}t automatically be "
                f"assigned to the {q}{category_prefill}{q} category, unless "
                f"it is defined like that in its "
                f"{q}library.properties{q} file. "
            )
            self.__category_warning_lbl.show()
            super().show()
            return
        self.__category_warning_lbl.hide()
        super().show()
        return

    def _cancel_clicked(self, *args) -> None:
        """"""
        self.close()
        return

    def __final_btn_clicked(self, *args) -> None:
        """Final button to unzip the chosen library to the project is
        clicked."""

        def finish(success, *_args):
            if success:
                self.close()
                return
            return

        self.__unzip_lib_to_project(
            callback=finish,
            callbackArg=None,
        )
        return

    def __unzip_lib_to_project(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        # $ Path to 'my_lib.zip' file
        zipped_libfile = self.__zipfile_groupbox.get_text().replace("\\", "/")

        # $ Path to '<project>/source/libraries'
        # Parent-folder where the user wants to store its
        # library.
        target_libcollection_dir: str = ""
        if self.__proj_storage_groupbox is not None:
            assert self.__local_storage_groupbox is None
            target_libcollection_dir = (
                self.__proj_storage_groupbox.get_text().replace("\\", "/")
            )
            if target_libcollection_dir.startswith("<project>"):
                target_libcollection_dir = target_libcollection_dir.replace(
                    "<project>",
                    data.current_project.get_proj_rootpath(),
                    1,
                )
        else:
            target_libcollection_dir = (
                self.__local_storage_groupbox.get_text().replace("\\", "/")
            )

        # $ Path to '<project>/source/libraries/my_lib'
        # Folder where the chosen library will end up, including
        # the library's name.
        target_libdir: Optional[str] = None

        # $ Path to '~/.embeetle/libraries'
        # Folder where all embeetle libraries get cached.
        # Will be created if needed.
        dot_embeetle_libcollection_dir: Union[
            str, List[str], None
        ] = _libmanager_.LibManager().get_potential_libcollection_folder(
            "dot_embeetle"
        )

        # $ Path to '~/.embeetle/libraries/my_lib'
        # Folder where the chosen library will be cached.
        dot_embeetle_libdir: Optional[str] = None

        # $ Library name
        libname: Optional[str] = None

        def start(*args) -> None:
            "Check if okay"
            err_msg_01: str = ""
            err_msg_02: str = ""
            if not data.is_home:
                err_msg_01 = str(
                    f"Please select a valid library zipfile. The zipfile you<br>"
                    f"select will be unzipped into your project."
                )
                err_msg_02 = str(
                    f"Please select a valid subfolder inside your project<br>"
                    f"to store the unzipped library."
                )
            else:
                err_msg_01 = str(
                    f"Please select a valid library zipfile. The zipfile you<br>"
                    f"select will be unzipped into Embeetle{q}s library cache<br>"
                    f"folder:<br>"
                    f"{q}{dot_embeetle_libcollection_dir}{q}"
                )
                err_msg_02 = str(
                    f"Please check if you have write access to Embeetle{q}s<br>"
                    f"library cache folder:<br>"
                    f"{q}{dot_embeetle_libcollection_dir}{q}"
                )
            # $ Check chosen zipfile
            if self.__zipfile_groupbox.has_error():
                abort(err_msg_01)
                return
            # $ Check chosen target folder
            if (
                self.__proj_storage_groupbox is not None
            ) and self.__proj_storage_groupbox.has_error():
                abort(err_msg_02)
                return
            # By now, both paths should be fine. But recheck them anyhow.
            _libmanager_.LibManager().add_zipped_library(
                zipped_libfile=zipped_libfile,
                target_libcollection_dir=target_libcollection_dir,
                callback=finish,
                callbackArg=None,
            )
            return

        def abort(reason: Optional[str] = None, *args) -> None:
            if reason is not None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="WARNING",
                    text=reason,
                )
            callback(False, callbackArg)
            return

        def finish(success: bool = True, *args) -> None:
            if not success:
                abort()
                return
            callback(True, callbackArg)
            return

        start()
        return
