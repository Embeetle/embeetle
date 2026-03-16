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
import qt, data, purefunctions, functions, iconfunctions
import gui.templates.paintedgroupbox
import gui.templates.widgetgenerator
import gui.dialogs.popupdialog
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_

if TYPE_CHECKING:
    pass

from various.kristofstuff import *


class ProjStorageGroupBox(
    gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
):
    """"""

    clicked_or_enter_sig = qt.pyqtSignal()
    lineedit_tab_pressed_sig = qt.pyqtSignal()

    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
        title: Optional[str] = None,
    ) -> None:
        """"""
        if title is None:
            title = "Add new libraries in:"
        super().__init__(
            parent=parent,
            name="projstorage",
            text=title,
            info_func=lambda *args: print("info clicked!"),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Maximum,
        )
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(0)

        # * Error flag
        self.__err_flag = False

        # * Info Label
        # A label above the text field to show info and
        # error messages.
        self.__info_lbl = qt.QLabel()
        self.__info_lbl.setText(" ")
        self.__info_lbl.setStyleSheet(
            """
            QLabel {
                margin: 0px;
                padding: 0px;
                background-color: #00ffffff;
                border-style: none;
                text-align: left;
            }
            QLabel[red = true] {
                color: #cc0000;
            }
        """
        )
        self.__info_lbl.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.__info_lbl.setFont(data.get_general_font())
        self.__info_lbl.setMinimumHeight(data.get_general_icon_pixelsize())
        self.layout().addWidget(self.__info_lbl)
        self.__info_lbl.hide()

        # * Lineedit, folder_btn and checkmark
        hlyt, lineedit, button, checkmark = (
            gui.templates.widgetgenerator.create_directory_selection_line(
                parent=self,
                tool_tip="Select folder",
                start_directory_fallback=data.current_project.get_proj_rootpath(),
                click_func=self.other_storage_selected,
                checkmarkclick_func=self.checkmark_clicked,
                text_change_func=self.other_storage_selected,
                tool_tip_checkmark="Create folder",
            )
        )
        self.__lineedit = lineedit
        self.__folder_btn = button
        self.__checkmark = checkmark
        self.__sub_lyt = hlyt
        cast(qt.QVBoxLayout, self.layout()).addLayout(hlyt)
        del lineedit, button, checkmark, hlyt

        # * Set default location
        default_lib_abspath = None
        root_abspath = data.current_project.get_proj_rootpath()
        # $ 1. Try 'source/libraries'
        default_lib_abspath = _pp_.rel_to_abs(
            rootpath=root_abspath,
            relpath="source/libraries",
        )
        # $ 2. Try 'libraries'
        if not os.path.isdir(default_lib_abspath):
            default_lib_abspath = _pp_.rel_to_abs(
                rootpath=root_abspath,
                relpath="libraries",
            )
        # $ 3. Try 'libs'
        if not os.path.isdir(default_lib_abspath):
            default_lib_abspath = _pp_.rel_to_abs(
                rootpath=root_abspath,
                relpath="libs",
            )
        # $ 4. Try 'lib'
        if not os.path.isdir(default_lib_abspath):
            default_lib_abspath = _pp_.rel_to_abs(
                rootpath=root_abspath,
                relpath="lib",
            )
        # $ 5. Nothing works. Set the default to something reasonable.
        if not os.path.isdir(default_lib_abspath):
            source_abspath = _pp_.rel_to_abs(
                rootpath=root_abspath,
                relpath="source",
            )
            if os.path.isdir(source_abspath):
                # There is a 'source' folder => put it inside
                default_lib_abspath = _pp_.rel_to_abs(
                    rootpath=root_abspath,
                    relpath="source/libraries",
                )
            else:
                # There is no 'source' folder => put it toplevel
                default_lib_abspath = _pp_.rel_to_abs(
                    rootpath=root_abspath,
                    relpath="libraries",
                )

        if os.path.isdir(default_lib_abspath):
            self.__checkmark.setIcon(
                iconfunctions.get_qicon("icons/dialog/checkmark.png")
            )
            self.__checkmark.setToolTip("Folder exists")
        else:
            self.__checkmark.setIcon(
                iconfunctions.get_qicon("icons/folder/closed/new_folder.png")
            )
            self.__checkmark.setToolTip("Create folder")
        default_lib_relpath = default_lib_abspath.replace(root_abspath, "")
        if default_lib_relpath.endswith("/"):
            default_lib_relpath = default_lib_relpath[0:-1]
        if default_lib_relpath.startswith("/"):
            default_lib_relpath = default_lib_relpath[1:]
        self.__lineedit.setText(f"<project>/{default_lib_relpath}")
        return

    def has_error(self) -> bool:
        """Return error state."""
        return self.__err_flag

    def get_text(self) -> str:
        """Return text in the QLineEdit().

        Will never return None.
        """
        txt = self.__lineedit.text()
        if not isinstance(txt, str):
            return ""
        return txt

    def other_storage_selected(self, *args) -> None:
        """The user selected another storage location, by clicking the
        folder_btn and selecting a fol- der.

        OR The user typed a character in the lineedit.
        """

        def set_err_status(err_status: bool) -> None:
            "Set or clear the error status of the QLineEdit()"
            self.__err_flag = err_status
            _selection = self.__lineedit.text()
            _selection = _selection.replace("\\", "/")

            # * ERROR
            if err_status:
                self.__info_lbl.setProperty("red", True)
                self.__info_lbl.style().unpolish(self.__info_lbl)
                self.__info_lbl.style().polish(self.__info_lbl)
                self.__info_lbl.update()
                firstpart = selection.split("/")[0]
                if firstpart.startswith("<") and firstpart.endswith(">"):
                    # It's probably red because the folder doesn't exist.
                    self.__info_lbl.setText("The folder must exist")
                    self.__info_lbl.show()
                    self.__checkmark.setIcon(
                        iconfunctions.get_qicon(
                            "icons/folder/closed/new_folder.png"
                        )
                    )
                    self.__checkmark.setToolTip("Create folder")
                else:
                    if any(
                        _selection.startswith(_rootpath_)
                        for _rootpath_ in data.current_project.get_all_rootpaths()
                    ):
                        self.__info_lbl.setText(" ")
                        self.__info_lbl.hide()
                    else:
                        self.__info_lbl.setText(
                            "Choose a folder within your current project"
                        )
                        self.__info_lbl.show()
                    self.__checkmark.setIcon(
                        iconfunctions.get_qicon("icons/dialog/cross.png")
                    )
                    self.__checkmark.setToolTip(
                        "Choose a folder within your current project"
                    )
                self.__lineedit.setProperty("red", True)
                self.__lineedit.style().unpolish(self.__lineedit)
                self.__lineedit.style().polish(self.__lineedit)
                self.__lineedit.update()
                return

            # * NO ERROR
            self.__info_lbl.setText(" ")
            self.__info_lbl.setProperty("red", False)
            self.__info_lbl.style().unpolish(self.__info_lbl)
            self.__info_lbl.style().polish(self.__info_lbl)
            self.__info_lbl.hide()
            self.__info_lbl.update()
            self.__lineedit.setProperty("red", False)
            self.__lineedit.style().unpolish(self.__lineedit)
            self.__lineedit.style().polish(self.__lineedit)
            self.__lineedit.update()
            self.__checkmark.setIcon(
                iconfunctions.get_qicon("icons/dialog/checkmark.png")
            )
            self.__checkmark.setToolTip("Folder exists")
            return

        selection = self.__lineedit.text().replace("\\", "/")

        # * ----[ Already processed ]---- *#
        # Look for the string '<rootid>' at the start of the lineedit. If it's there, the lineedit
        # was already processed before and '<rootid>' represents one of the project rootfolders.
        projObj = data.current_project
        rootpath_list = projObj.get_all_rootpaths()
        for _rootpath in rootpath_list:
            _rootid = projObj.get_rootid_from_rootpath(
                rootpath=_rootpath,
                double_angle=True,
                html_angles=False,
            )
            if selection.startswith(_rootid):
                abspath = selection.replace(_rootid, _rootpath, 1)
                set_err_status(not os.path.isdir(abspath))
                return

        # * ----[ Not yet processed ]---- *#
        # There's no '<rootid>' string at the start, so the lineedit must contain an absolute path,
        # which typically happens right after the user made his selection through the folder_btn.
        if not any(
            selection.startswith(_rootpath) for _rootpath in rootpath_list
        ):
            # The absolute path doesn't match with any of the known rootpaths.
            set_err_status(True)
            return

        prefixed_relpath = projObj.abspath_to_prefixed_relpath(
            abspath=selection,
            double_angle=True,
            html_angles=False,
        )
        if prefixed_relpath is None:
            # No match with any of the known rootpaths. This is a weird case. It should have been
            # catched in the previous step.
            purefunctions.printc(
                f"\nERROR: Weird case in {q}proj_storage_groupbox.py{q} -> "
                f"other_storage_selected()",
                color="error",
            )
            set_err_status(True)
            return

        self.__lineedit.setText(prefixed_relpath)
        set_err_status(False)
        return

    def get_abspath(self) -> Optional[str]:
        """Try to extract the abspath pointed to by the QLineEdit() widget.

        Right now it doesn't matter if the abspath exists or not.
        """
        # & Check QLineEdit() content
        selection = self.__lineedit.text().replace("\\", "/")
        firstpart = selection.split("/")[0]
        if firstpart.startswith("<") and firstpart.endswith(">"):
            # The content from the QLineEdit() seems to start with a rootid. That's okay.
            pass
        else:
            # There is no rootid present. Quit.
            return None

        # & Parse QLineEdit() content
        rootid: Optional[str] = None
        remainder: Optional[str] = None
        try:
            rootid, remainder = purefunctions.strip_rootid(selection)
        except RuntimeError:
            # Failed to parse to content
            return None
        if (rootid is None) or (remainder is None):
            return None
        rootpath = data.current_project.get_rootpath_from_rootid(rootid)
        if rootpath is None:
            return None

        # & Return the abspath
        return _pp_.rel_to_abs(
            rootpath=rootpath,
            relpath=remainder,
        )

    def checkmark_clicked(self, *args) -> None:
        """The user clicked the checkmark next to the folder icon. Remember that
        this checkmark turns into an 'add folder' button if the chosen folder
        doesn't exist yet!

        This function checks if the chosen folder exists. If not, it checks if the chosen folder is
        in one of the rootpaths. If so - this function asks permission to create the folder.
        """

        def finish(*_args) -> None:
            return

        abspath: Optional[str] = self.get_abspath()
        if abspath is None:
            finish()
            return
        if os.path.isdir(abspath):
            # There's no need to create a new directory. Quit.
            finish()
            return

        # & Ask permission to create new directory
        selection = self.__lineedit.text().replace("\\", "/")
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        green = css["green"]
        end = css["end"]
        selection_html = selection.replace(">", "&#62;").replace("<", "&#60;")
        result, _ = gui.dialogs.popupdialog.PopupDialog.ok_cancel(
            parent=self.parent(),
            icon_path=f"icons/folder/closed/new_folder.png",
            title_text="Create new folder",
            text=str(
                f"Do you want to create this new folder?<br>"
                f"{tab}{green}{selection_html}{end}"
            ),
        )
        if result == qt.QMessageBox.StandardButton.Cancel:
            # User doesn't want
            finish()
            return

        # & Create new directory
        result = _fp_.make_dir(
            dir_abspath=abspath,
            printfunc=print,
            catch_err=True,
            overwr=False,
        )
        if not result:
            gui.dialogs.popupdialog.PopupDialog.ok(
                parent=self.parent(),
                icon_path=f"icons/dialog/stop.png",
                title_text="Cannot create new folder",
                text=str(
                    "Folder creation failed! Please check your file permissions."
                ),
            )
            finish()
            return

        def show_item(*_args) -> None:
            if qt.sip.isdeleted(self):
                return
            data.filetree.goto_path(abspath)
            return

        # & Reformat
        self.other_storage_selected()
        qt.QTimer.singleShot(400, show_item)
        return

    def self_destruct(
        self,
        death_already_checked: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill ProjStorageGroupBox() twice!"
                )
            self.dead = True

        # $ Disconnect signals
        for sig in (
            self.clicked_or_enter_sig,
            self.lineedit_tab_pressed_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Remove child widgets
        self.__sub_lyt.removeWidget(self.__info_lbl)
        self.__sub_lyt.removeWidget(self.__lineedit)
        self.__sub_lyt.removeWidget(self.__folder_btn)
        self.__sub_lyt.removeWidget(self.__checkmark)

        # $ Kill and deparent children
        self.__info_lbl.setParent(None)  # noqa
        self.__lineedit.setParent(None)  # noqa
        self.__folder_btn.setParent(None)  # noqa
        self.__checkmark.setParent(None)  # noqa

        # $ Kill leftovers
        functions.clean_layout(self.__sub_lyt)
        functions.clean_layout(self.layout())

        # $ Reset variables
        self.__err_flag = None
        self.__info_lbl = None
        self.__lineedit = None
        self.__folder_btn = None
        self.__checkmark = None
        self.__sub_lyt = None

        # $ Deparent oneself
        gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton.self_destruct(
            self,
            death_already_checked=True,
        )
        return
