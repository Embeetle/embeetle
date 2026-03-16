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
import threading, os, functools
import qt, data, purefunctions, functions, gui
import gui.helpers.various
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import wizards.lib_wizard.gen_widgets.check_linebox as _check_linebox_
import project_generator.generator.file_changer as _fc_

if TYPE_CHECKING:
    import gui.dialogs.popupdialog
    import bpathlib.treepath_obj as _treepath_obj_
    import project.segments.path_seg.treepath_seg as _treepath_seg_
    import project.segments.version_seg.version_seg as _version_seg_
from various.kristofstuff import *


class UpgradeOrRepairWizard(_gen_wizard_.GeneralWizard):
    """STRUCTURE ========= self.main_layout   # created in superclass.

    ╔══[ self.main_layout ]═════════════════════════════════════════╗
    ║ ┌─ self.__file_lbl ─────────────────────────────────────────┐ ║
    ║ │                                                           │ ║
    ║ └───────────────────────────────────────────────────────────┘ ║
    ║ ┌─ self.__file_box ─────────────────────────────────────────┐ ║
    ║ │ <project>/config/makefile       diff=30.33%               │ ║
    ║ │ <project>/config/linkerscript   diff=2.54%                │ ║
    ║ │ <project>/config/dashboard.mk   diff=3.43%                │ ║
    ║ │ <project>/config/filetree.mk    diff=31.32%               │ ║
    ║ └───────────────────────────────────────────────────────────┘ ║
    ║ ┌─ self.__choice_lbl ───────────────────────────────────────┐ ║
    ║ │                                                           │ ║
    ║ └───────────────────────────────────────────────────────────┘ ║
    ║ ┌─ self.__choice_box ───────────────────────────────────────┐ ║
    ║ │                                                           │ ║
    ║ └───────────────────────────────────────────────────────────┘ ║
    ║                 CANCEL        UPGRADE PROJECT                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """

    def __init__(
        self,
        parent: Optional[qt.QWidget],
        cur_version: int,
        new_version: int,
        role: str,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Create UpgradeOrRepairWizard().

        If this wizard is used to simply repair a project, the 'cur_ version'
        and 'new_version' should be the same.
        """
        super().__init__(parent)
        # MyPy seems unable to figure out the type of 'self.dead' from the superclass. Therefore, I
        # repeat the attribute here after ensuring it actually already existed.
        assert hasattr(self, "dead")
        self.dead: bool = False
        self.__busy_mutex = threading.Lock()
        self.__cur_version = cur_version
        self.__new_version = new_version
        self.__callback = callback
        self.__callbackArg = callbackArg
        self.__role = role
        if role == "upgrade":
            assert cur_version != new_version
        elif role == "repair":
            assert cur_version == new_version
        else:
            assert False
        self.setWindowTitle("Upgrade Project")
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        self.main_layout.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        text_color = data.theme["fonts"]["default"]["color"]
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        blue = css["blue"]
        green = css["green"]
        end = css["end"]

        # * FILE LABEL
        self.__file_lbl = qt.QLabel(self)
        self.__file_lbl.setStyleSheet(
            f"""
            QLabel {{
                text-align: left;
                border: none;
                color: {text_color};
                font-family: {data.get_global_font_family()};
                font-size: {data.get_general_font_pointsize()}pt;
            }}
            """
        )
        v1 = self.__cur_version
        v2 = self.__new_version
        if self.__role == "upgrade":
            self.__file_lbl.setText(
                f"""
            {css['h2']}Upgrade Project{css['/hx']}
            <p align="left">
                Upgrade the project from makefile interface <b>{green}v{v1}{end}</b> 
                to <b>{green}v{v2}{end}</b>. Nothing<br>
                changes in the source code. Only some config files get upgraded:
            </p>
            """
            )
        else:
            self.__file_lbl.setText(
                f"""
            <p align="left">
                {css['h2']}Repair Project{css['/hx']}
                Repair the project according to makefile interface <b>{green}v{v1}{end}</b><br>
                Nothing changes in the source code. Only some config files are repaired:
            </p>
            """
            )
        self.main_layout.addWidget(self.__file_lbl)

        # * FILE BOX
        self.__file_box = qt.QFrame()
        self.__file_box.setContentsMargins(30, 20, 0, 30)
        self.__file_box.setStyleSheet(
            f"""
        QFrame {{
            background: transparent;
            border: none;
        }}
        """
        )
        self.__file_box_lyt = qt.QVBoxLayout()
        self.__file_box.setLayout(self.__file_box_lyt)
        self.__file_box_lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.__file_box_lyt.setContentsMargins(0, 0, 0, 0)
        self.__file_box_lyt.setSpacing(0)
        self.main_layout.addWidget(self.__file_box)

        # * CHOICE LABEL
        self.__choice_lbl = qt.QLabel(self)
        self.__choice_lbl.setStyleSheet(
            f"""
            QLabel {{
                text-align: left;
                border: none;
                color: {text_color};
                font-family: {data.get_global_font_family()};
                font-size: {data.get_general_font_pointsize()}pt;
            }}
            """
        )
        if self.__role == "upgrade":
            self.__choice_lbl.setText(
                f"""
            {css['h2']}Upgrade Settings{css['/hx']}
            <p align="left">
                Select your preferences for this upgrade:
            </p>
            """
            )
        else:
            self.__choice_lbl.setText(
                f"""
            {css['h2']}Repair Settings{css['/hx']}
            <p align="left">
                Select your preferences for this reparation:
            </p>
            """
            )
        self.main_layout.addWidget(self.__choice_lbl)

        # * CHOICE BOX
        self.__choice_box = qt.QFrame()
        self.__choice_box.setContentsMargins(30, 0, 0, 30)
        self.__choice_box.setStyleSheet(
            f"""
            QFrame {{
                background: transparent;
                border: none;
            }}
        """
        )
        self.__choice_box_lyt = qt.QVBoxLayout()
        self.__choice_box.setLayout(self.__choice_box_lyt)
        self.__choice_box_lyt.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.__choice_box_lyt.setContentsMargins(0, 0, 0, 0)
        self.__choice_box_lyt.setSpacing(10)
        self.main_layout.addWidget(self.__choice_box)

        # & Manual mods
        # Only show the manual modifications checkbox if needed.
        self.__manual_mods_checkbox: Optional[_check_linebox_.CheckLineBox] = (
            None
        )
        self.__manual_mods_info_lbl: Optional[qt.QLabel] = None
        if self.__role == "upgrade":
            # $ Checkbox
            self.__manual_mods_checkbox = _check_linebox_.CheckLineBox(
                parent=None,
                thin=True,
            )
            self.__manual_mods_checkbox.get_lineedit().setReadOnly(True)
            self.__manual_mods_checkbox.set_text("Keep my modifications")
            self.__manual_mods_checkbox.set_on(False)
            self.__manual_mods_checkbox.btn_clicked_sig.connect(
                self.__manual_mods_clicked
            )
            self.__manual_mods_checkbox.lineedit_clicked_sig.connect(
                self.__manual_mods_clicked
            )
            self.__choice_box_lyt.addWidget(self.__manual_mods_checkbox)

            # $ Info lbl
            self.__manual_mods_info_lbl = qt.QLabel()
            self.__manual_mods_info_lbl.setStyleSheet(
                f"""
                QLabel {{
                    text-align: left;
                    border: none;
                    color: {text_color};
                    font-family: {data.get_global_font_family()};
                    font-size: {data.get_general_font_pointsize() - 1}pt;
                }}
                """
            )
            self.__manual_mods_info_lbl.setText(
                f"""
                {tab}A three-way-merge will be applied on the config files to pre-<br>
                {tab}serve your modifications. Depending on the modifications you<br>
                {tab}made, this could lead to a malfunctioning project. In that<br>
                {tab}case, you can still repair the project through: Dashboard -&#62;<br>
                {tab}Version -&#62; Repair Project
            """
            )
            self.__choice_box_lyt.addWidget(self.__manual_mods_info_lbl)
            self.__manual_mods_info_lbl.hide()

        # & Make backup
        # $ Checkbox
        self.__make_backup_checkbox = _check_linebox_.CheckLineBox(
            parent=None,
            thin=True,
        )
        self.__make_backup_checkbox.get_lineedit().setReadOnly(True)
        self.__make_backup_checkbox.set_text("Backup config files")
        self.__make_backup_checkbox.set_on(False)
        self.__make_backup_checkbox.btn_clicked_sig.connect(
            self.__backup_clicked
        )
        self.__make_backup_checkbox.lineedit_clicked_sig.connect(
            self.__backup_clicked
        )
        self.__choice_box_lyt.addWidget(self.__make_backup_checkbox)

        # $ Info lbl
        self.__make_backup_info_lbl = qt.QLabel()
        self.__make_backup_info_lbl.setStyleSheet(
            f"""
            QLabel {{
                text-align: left;
                border: none;
                color: {text_color};
                font-family: {data.get_global_font_family()};
                font-size: {data.get_general_font_pointsize() - 1}pt;
            }}
            """
        )
        self.__make_backup_info_lbl.setText(
            f"""
            {tab}Your config files will first be backed up before starting the<br>
            {tab}upgrade. You will find them at:<br>
            {tab}{green}&#60;project&#62;/.beetle/{_fc_.FileChanger().get_backup_filename()}{end}
        """
        )
        self.__choice_box_lyt.addWidget(self.__make_backup_info_lbl)
        self.__make_backup_info_lbl.hide()

        def finish(*args) -> None:
            self.add_page_buttons()
            completion_name = " UPGRADE PROJECT "
            if self.__role == "repair":
                completion_name = " REPAIR PROJECT "
            self.repurpose_cancel_next_buttons(
                cancel_name="CANCEL",
                cancel_func=self._cancel_clicked,
                cancel_en=True,
                next_name=completion_name,
                next_func=self._complete_wizard,
                next_en=True,
            )
            qt.QTimer.singleShot(100, self.__resize_and_center)
            return

        # Fill FILE BOX
        self.__file_data: Dict[
            str, Dict[str, Union[qt.QLabel, _treepath_obj_.TreepathObj, str]]
        ] = {}
        self.__diff_dialog: Optional[gui.helpers.various.DiffDialog] = None
        self.main_layout.addStretch(10)
        self.__fill_file_box(
            final_round=False,
            callback=finish,
            callbackArg=None,
        )
        return

    def __is_project_okay(self) -> bool:
        """Return True if the project has all the files it needs."""
        projObj = data.current_project
        treepath_seg: _treepath_seg_.TreepathSeg = projObj.get_treepath_seg()
        for treepath_obj in treepath_seg.get_treepath_obj_list():
            unicum_name = treepath_obj.get_name()
            if unicum_name in (
                "BUILD_DIR",
                "BIN_FILE",
                "ELF_FILE",
                "BOOTLOADER_FILE",
                "BOOTSWITCH_FILE",
                "PARTITIONS_CSV_FILE",
            ):
                continue
            if not treepath_obj.is_relevant():
                continue
            abspath = treepath_obj.get_abspath()
            if (
                (abspath is None)
                or (abspath.lower() == "none")
                or (not os.path.isfile(abspath))
            ):
                # This is a relevant TreepathObj() and yet its file doesn't exist!
                return False
            continue
        # All TreepathObj()s are checked.
        return True

    def __fill_file_box(
        self,
        final_round: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """SUMMARY ======= Create a data structure 'self.__file_data' and use it
        immediately to fill the FILE BOX with entries.

        :param final_round: The final round is invoked at the very end when the user clicks 'UPGRADE
                            PROJECT'. For this round, the config files must be changed on the hard-
                            drive (no more dry-runs).

        DETAILS
        =======
        First create a data structure like this:
        ┌──────────────────────────────────────────┐
        │ self.__file_data = {                     │  For each relevant file, this data structure
        │     '<project>/config/makefile' : {      │  holds:
        │         'label'        : QLabel(),       │    - a QLabel()
        │         'treepath_obj' : TreepathObj(),  │    - a TreepathObj()
        │         'cur_content'  : '...',          │    - the current content
        │         'res_content'  : '...',          │    - the resulting content
        │     }                                    │
        │     '<project>/config/dashboard.mk' : {  │  with the new content being from the latest
        │         'label'        : QLabel(),       │  version.
        │         'treepath_obj' : TreepathObj(),  │
        │         'cur_content'  : '...',          │
        │         'res_content'  : '...',          │
        │     }                                    │
        │                                          │
        │     ...                                  │
        │ }                                        │
        └──────────────────────────────────────────┘

        NOTE:
        The 'template_only' parameter is False when requesting new content for a file.
        """
        if not self.__busy_mutex.acquire(blocking=False):
            if callback is not None:
                callback(callbackArg)
            return
        projObj = data.current_project

        def get_treepath_obj_data(
            _treepath_obj: _treepath_obj_.TreepathObj,
        ) -> Tuple[str, str]:
            # $ Abspath
            _abspath = _treepath_obj.get_abspath()
            if (_abspath is None) or (_abspath.lower() == "none"):
                # Construct an abspath to a file that can be created later.
                if (_treepath_obj.get_name() == "DASHBOARD_MK") or (
                    _treepath_obj.get_name() == "FILETREE_MK"
                ):
                    _makefile_abspath = projObj.get_treepath_seg().get_abspath(
                        "MAKEFILE"
                    )
                    if (_makefile_abspath is None) or (
                        _makefile_abspath.lower() == "none"
                    ):
                        _makefile_abspath = _pp_.rel_to_abs(
                            rootpath=projObj.get_proj_rootpath(),
                            relpath=projObj.get_treepath_seg()
                            .get_treepathObj("MAKEFILE")
                            .get_default_relpath(),
                        )
                    assert _makefile_abspath is not None
                    assert _makefile_abspath.lower() != "none"
                    _abspath = _pp_.rel_to_abs(
                        rootpath=os.path.dirname(_makefile_abspath),
                        relpath=(
                            "dashboard.mk"
                            if _treepath_obj.get_name() == "DASHBOARD_MK"
                            else "filetree.mk"
                        ),
                    )
                else:
                    _abspath = _pp_.rel_to_abs(
                        rootpath=projObj.get_proj_rootpath(),
                        relpath=_treepath_obj.get_default_relpath(),
                    )
            assert _abspath is not None
            assert _abspath.lower() != "none"

            # $ Prefixed relpath
            _root_id = _treepath_obj.get_rootid()
            if (_root_id is None) or (_root_id.lower() == "none"):
                _root_id = "<project>"
            _relpath = _treepath_obj.get_relpath()
            if (_relpath is None) or (_relpath.lower() == "none"):
                _relpath = _abspath.replace(projObj.get_proj_rootpath(), "", 1)
                if _relpath.startswith("/"):
                    _relpath = _relpath[1:]
            _prefixed_relpath = f"{_root_id}/{_relpath}"

            return _abspath, _prefixed_relpath

        # * Kill old labels
        self.__file_data = {}
        functions.clean_layout(self.__file_box_lyt)

        # * Fill file data structure
        # Fill the data structure will TreepathObj()s. However, if two TreepathObj()s point to the
        # same file, only take one of them. Each TreepathObj() will get its own QLabel() here. There
        # is no point in duplicating the same file.
        font_family = data.get_global_font_family()
        font_pointsize = data.get_general_font_pointsize()
        max_len = 0
        treepath_seg: _treepath_seg_.TreepathSeg = projObj.get_treepath_seg()
        for treepath_obj in treepath_seg.get_treepath_obj_list():
            unicum_name = treepath_obj.get_name()
            if unicum_name in (
                "BUILD_DIR",
                "BIN_FILE",
                "ELF_FILE",
                "BOOTLOADER_FILE",
                "BOOTSWITCH_FILE",
                "PARTITIONS_CSV_FILE",
            ):
                continue
            if not treepath_obj.is_relevant():
                continue
            abspath, prefixed_relpath = get_treepath_obj_data(treepath_obj)
            if prefixed_relpath in self.__file_data.keys():
                # Already processed
                continue
            text_color = data.theme["fonts"]["default"]["color"]
            self.__file_data[prefixed_relpath] = {
                "label": qt.QLabel(
                    f"{prefixed_relpath}".replace("<", "&#60;").replace(
                        ">", "&#62;"
                    )
                ),
                "treepath_obj": treepath_obj,
                "cur_content": None,
                "res_content": None,
            }
            lbl: qt.QLabel = cast(
                qt.QLabel, self.__file_data[prefixed_relpath]["label"]
            )
            lbl.setStyleSheet(
                f"""
                QLabel {{
                    text-align: left;
                    border: none;
                    color: {text_color};
                    font-family: {font_family};
                    font-size: {font_pointsize}pt;
                }}
            """
            )
            btn_len = len(lbl.text())
            if btn_len > max_len:
                max_len = btn_len
            lbl.setOpenExternalLinks(False)
            lbl.setTextFormat(qt.Qt.TextFormat.RichText)
            lbl.setFont(data.get_general_font())
            lbl.linkActivated.connect(  # type: ignore
                functools.partial(self.line_clicked, prefixed_relpath)
            )
            self.__file_box_lyt.addWidget(lbl)
            continue

        def acquire_next_cur_content(
            _treepath_obj_iter: Iterator[_treepath_obj_.TreepathObj],
        ) -> None:
            # Acquire the 'cur_content' from the next relevant file and store it
            # in the file datastruct.
            try:
                _treepath_obj = next(_treepath_obj_iter)
            except StopIteration:
                finish()
                return
            # $ Acquire abspath and prefixed relpath
            # Acquire first the abspath. It should be in the TreepathObj(), but it could be missing
            # there. In that case, construct a default one. Acquire the prefixed relpath. It serves
            # as the key for the file datastructure we're trying to fill.
            _abspath, _prefixed_relpath = get_treepath_obj_data(_treepath_obj)
            if _prefixed_relpath not in self.__file_data.keys():
                raise RuntimeError()

            # $ File exists
            if os.path.isfile(_abspath):
                with open(
                    _abspath,
                    "r",
                    encoding="utf-8",
                    newline="\n",
                    errors="replace",
                ) as f:
                    _cur_content = f.read()
                self.__file_data[_prefixed_relpath][
                    "cur_content"
                ] = _cur_content
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        request_next_res_content,
                        _abspath,
                        _prefixed_relpath,
                        _treepath_obj,
                        _treepath_obj_iter,
                    ),
                )
                return

            # $ File doesn't exist
            self.__file_data[_prefixed_relpath]["cur_content"] = ""
            request_next_res_content(
                _abspath,
                _prefixed_relpath,
                _treepath_obj,
                _treepath_obj_iter,
            )
            return

        def request_next_res_content(
            _abspath: str,
            _prefixed_relpath: str,
            _treepath_obj: _treepath_obj_.TreepathObj,
            _treepath_obj_iter: Iterator[_treepath_obj_.TreepathObj],
        ) -> None:
            # Acquire the 'res_content' from the next relevant file and store it in the file data-
            # struct.
            # NOTE:
            # The given '_abspath' and '_prefixed_relpath' parameters could be extracted or computed
            # from the TreepathObj(). However, that's already done in the previous function. No need
            # to redo that again here.

            # See if new content must be forced, or if a three-way-merge is requested.
            force_new_content: bool = False
            if self.__role == "upgrade":
                assert self.__manual_mods_checkbox is not None
                force_new_content = not self.__manual_mods_checkbox.is_on()
                if _treepath_obj.get_name() == "FILETREE_MK":
                    # Always force new content for 'filetree.mk'.
                    force_new_content = True
            else:
                assert self.__manual_mods_checkbox is None
                force_new_content = True

            # Perform a dry-run to compare the current content with the resulting one. If this is
            # the final round, the run must not be dry! Also, in that case the file will be created
            # at '_abspath' if there is no file at that location.
            _fc_.FileChanger().change_file_content(
                version=self.__new_version,
                file_unicum=_treepath_obj.get_unicum(),
                abspath=_abspath,
                repoints=None,
                dry_run=not final_round,
                force_new_content=force_new_content,
                callback=acquire_next_res_content,
                callbackArg=(
                    _abspath,
                    _prefixed_relpath,
                    _treepath_obj,
                    _treepath_obj_iter,
                ),
            )
            return

        def acquire_next_res_content(
            file_data: Dict,
            arg: Tuple[
                str,
                str,
                _treepath_obj_.TreepathObj,
                Iterator[_treepath_obj_.TreepathObj],
            ],
        ) -> None:
            _abspath, _prefixed_relpath, _treepath_obj, _treepath_obj_iter = arg
            # Store the new content.
            self.__file_data[_prefixed_relpath]["res_content"] = file_data[
                "res_content"
            ]
            diff = file_data["diff"]
            _lbl: qt.QLabel = cast(
                qt.QLabel, self.__file_data[_prefixed_relpath]["label"]
            )
            _lbl_text = _lbl.text().ljust(max_len + 1, "^")
            _lbl_text = _lbl_text.replace("^", "&nbsp;")
            if not final_round:
                _lbl_text += (
                    f' <a href="foo" style="color: #729fcf;">diff={diff}%</a>'
                )
            else:
                css = purefunctions.get_css_tags()
                green = css["green"]
                end = css["end"]
                if self.__role == "upgrade":
                    _lbl_text += f"{green}upgraded{end}"
                else:
                    _lbl_text += f"{green}repaired{end}"
                if _treepath_obj.get_abspath() != _abspath:
                    _rootid = _prefixed_relpath.split("/")[0]
                    _relpath = _prefixed_relpath.replace(_rootid, "", 1)
                    if _relpath.startswith("/"):
                        _relpath = _relpath[1:]
                    _treepath_obj.set_doublepath((_rootid, _relpath))
                assert _treepath_obj.get_abspath() == _abspath
            _lbl.setText(_lbl_text)
            _lbl.update()
            qt.QTimer.singleShot(
                50,
                functools.partial(
                    acquire_next_cur_content,
                    _treepath_obj_iter,
                ),
            )
            return

        def finish(*args) -> None:
            self.__busy_mutex.release()
            if callback is not None:
                callback(callbackArg)
            return

        acquire_next_cur_content(
            iter(
                [
                    _treepath_obj_dict["treepath_obj"]
                    for _relpath, _treepath_obj_dict in self.__file_data.items()
                ]
            )
        )
        return

    @qt.pyqtSlot(str)
    def line_clicked(self, prefixed_relpath: str) -> None:
        """"""
        cur_content = self.__file_data[prefixed_relpath]["cur_content"]
        res_content = self.__file_data[prefixed_relpath]["res_content"]
        self.__diff_dialog = gui.helpers.various.create_standalone_diff(
            parent=self,
            title="FILE DIFFER",
            icon="icons/gen/computer.png",
            text_1=cur_content,
            text_2=res_content,
            text_name_1="Current content",
            text_name_2="New content",
        )
        return

    def __manual_mods_clicked(self, *args) -> None:
        """The user clicked on the checkbox or on the label next to it."""
        if not self.__busy_mutex.acquire(blocking=False):
            return
        self.__manual_mods_checkbox.toggle()
        if self.__manual_mods_checkbox.is_on():
            self.__manual_mods_info_lbl.show()
        else:
            self.__manual_mods_info_lbl.hide()
        self.__busy_mutex.release()
        self.__fill_file_box(
            final_round=False,
            callback=None,
            callbackArg=None,
        )
        return

    def __backup_clicked(self, *args) -> None:
        """The user clicked on the checkbox or on the label next to it."""
        self.__make_backup_checkbox.toggle()
        if self.__make_backup_checkbox.is_on():
            self.__make_backup_info_lbl.show()
        else:
            self.__make_backup_info_lbl.hide()
        qt.QTimer.singleShot(50, self.__resize_and_center)
        return

    def __resize_and_center(self, *args) -> None:
        """Give this wizard a proper size and location."""
        self.resize(cast(qt.QSize, self.main_layout.sizeHint() * 1.1))  # type: ignore
        self.center_to_parent()
        self.adjustSize()
        # w, h = functions.get_screen_size()
        # self.resize(int(w*0.4), int(h*0.4))
        return

    def showEvent(self, e):
        """The show() method is invoked after creating this wizard instance."""
        super().showEvent(e)
        self.update_check_size()
        return

    # ^                              COMPLETE WIZARD                               ^#
    # % ========================================================================== %#
    # % The user clicks 'UPGRADE PROJECT', 'CANCEL' or 'X'.                        %#
    # %                                                                            %#

    def _complete_wizard(self, *args) -> None:
        """The user clicks the 'UPGRADE PROJECT' button."""
        callback = self.__callback
        callbackArg = self.__callbackArg
        if not self.__busy_mutex.acquire(blocking=False):
            # Ignore the click. Just return without doing anything.
            return
        assert self.__busy_mutex.locked()

        def apply_hdd_changes(backup_success, *_args) -> None:
            if not backup_success:
                # Warn the user and return without doing anything.
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="Backup failed",
                    text=str(
                        f"Embeetle was unable to backup your config folder.\n"
                        f"Click {q}CANCEL{q} to go back and backup your project\n"
                        f"manually."
                    ),
                )
                self.__busy_mutex.release()
                return
            # By setting 'final_round = True, this method will apply the changes on the harddrive.
            # Release the mutex first, because this function will claim it.
            self.__busy_mutex.release()
            self.__fill_file_box(
                final_round=True,
                callback=set_next_version,
                callbackArg=None,
            )
            return

        def set_next_version(*_args) -> None:
            # At this point, the changes on the harddrive are completed. Now the new version must be
            # registered in the VersionSeg() from the Project()-instance.
            version_seg: _version_seg_.VersionSeg = (
                data.current_project.get_version_seg()
            )
            version_seg.set_version_nr(self.__new_version)
            version_seg.trigger_dashboard_refresh(
                callback=refresh_next_treepath_seg,
                callbackArg=None,
            )
            return

        def refresh_next_treepath_seg(*_args) -> None:
            treepath_seg = data.current_project.get_treepath_seg()
            treepath_seg.trigger_dashboard_refresh(
                callback=kill_self,
                callbackArg=None,
            )
            return

        def kill_self(*_args) -> None:
            # The whole procedure is completed, including the registration of the new version on
            # the Project()-instance. Kill this Wizard.
            self.self_destruct(
                callback=save_project,
                callbackArg=None,
            )
            return

        def save_project(*_args) -> None:
            data.current_project.save_project(
                save_editor=False,
                save_dashboard=True,
                ask_permissions=True,
                forced_files=[],
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(success: bool, *_args) -> None:
            if not success:
                abort()
                return
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        True,
                        callbackArg,
                    ),
                )
            return

        def abort(*_args) -> None:
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        False,
                        callbackArg,
                    ),
                )
            return

        # * Make backup
        if self.__make_backup_checkbox.is_on():
            _fc_.FileChanger().make_backup(
                callback=apply_hdd_changes,
                callbackArg=None,
            )
            return
        apply_hdd_changes(True)
        return

    def _cancel_clicked(self, *args) -> None:
        """The user pressed 'CANCEL'."""
        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        False,
                        callbackArg,
                    ),
                )
            return

        self.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return

    def reject(self) -> None:
        """The user closes this dialog by clicking the red 'X' in the top-right
        corner."""
        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        False,
                        callbackArg,
                    ),
                )
            return

        self.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return

    def self_destruct(
        self,
        death_already_checked: bool = False,
        additional_clean_list: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Kill this UpgradeOrRepairWizard()-instance.

        NOTE: First hide(), then kill all widgets and finally close() this QDialog(). Invoking
        close() immediately, without first hiding, causes the reject() method to run, which I've
        overridden to invoke this self_destruct() method. That would result in running this self_destruct()
        method more than once!
        Anyway, I've wrapped this self_destruct() method with a safety guard to avoid calling it twice.

        # TODO: The safety guard is now a hard fault!
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(
                    f"Trying to kill UpgradeOrRepairWizard() twice!"
                )
            self.dead = True

        self.hide()
        _gen_wizard_.GeneralWizard.self_destruct(
            self,
            death_already_checked=True,
            additional_clean_list=None,
            callback=None,
            callbackArg=None,
        )
        # functions.clean_layout(self.main_layout) <= Should happen in the 'self_destruct()' supercall

        def finish(*args) -> None:
            self.__busy_mutex = None
            self.__cur_version = None
            self.__new_version = None
            self.__file_lbl = None
            self.__file_box = None
            self.__file_box_lyt = None
            self.__choice_lbl = None
            self.__choice_box = None
            self.__choice_box_lyt = None
            self.__manual_mods_checkbox = None
            self.__manual_mods_info_lbl = None
            self.__make_backup_checkbox = None
            self.__make_backup_info_lbl = None
            self.__file_data = None
            self.__diff_dialog = None
            self.__callback = None
            self.__callbackArg = None
            if callback is not None:
                callback(callbackArg)
            return

        qt.QTimer.singleShot(20, finish)
        return

    def __get_backup_filename(self) -> str:
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
