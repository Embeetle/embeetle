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

##
##  Dialog for adjusting the GUI scaling
##
from __future__ import annotations
from typing import *
import qt
import data
import functions
import iconfunctions
import settings
import gui.stylesheets.slider
import gui.stylesheets.label
import gui.stylesheets
import gui.templates.widgetgenerator
import gui.templates.generaldialog
import components

if TYPE_CHECKING:
    import components.thesquid
    import gui.stylesheets.button
    import gui.helpers
    import gui.helpers.buttons
    import gui.templates.baseslider
import functools

LJUST_LEN = 22


def slider_setvalue(slider, value):
    slider.setValue(int(value))


class ScalingDialog(gui.templates.generaldialog.GeneralDialog):
    MAX_FACTOR = 1000
    MIN_FACTOR = 10

    stored_button_gboxes = None

    def __init__(self, parent):
        """Initialization of widget and background."""
        super().__init__(parent)
        # Add the icon and title
        self.setWindowIcon(iconfunctions.get_qicon("icons/menu_view/zoom.png"))
        self.setWindowTitle("Scaling")

        self.stored_button_gboxes = {}
        self.init_gui()
        # self.setMinimumSize(self.main_groupbox.sizeHint())
        return

    def init_gui(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        margins = layout.contentsMargins()
        layout.setContentsMargins(
            int(margins.left()),
            int(margins.top() + (1.5 * data.get_general_font_pointsize())),
            int(margins.right()),
            int(margins.bottom()),
        )
        # * GROUPBOXES TO CONTAIN THE SLIDERS
        groupbox_01 = self.create_horizontal_box()
        groupbox_01.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(groupbox_01)
        groupbox_02 = self.create_horizontal_box()
        groupbox_02.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(groupbox_02)
        groupbox_03 = self.create_horizontal_box()
        groupbox_03.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(groupbox_03)
        groupbox_04 = self.create_horizontal_box()
        groupbox_04.layout().setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(groupbox_04)

        def _generate_text(text, value, unit="%"):
            return f"{text}: {int(value)}{unit}".ljust(LJUST_LEN)

        #! ===========================[ TOP MENU ]=========================== !#
        def gen_text_menu():
            return _generate_text("Top Menu", data.toplevel_menu_scale)

        def inc_func(group_box, slider):
            data.toplevel_menu_scale += 20
            if data.toplevel_menu_scale > self.MAX_FACTOR:
                data.toplevel_menu_scale = self.MAX_FACTOR
            group_box.setTitle(gen_text_menu())
            slider_setvalue(slider, data.toplevel_menu_scale)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.toplevel_menu_scale -= 20
            if data.toplevel_menu_scale < self.MIN_FACTOR:
                data.toplevel_menu_scale = self.MIN_FACTOR
            group_box.setTitle(gen_text_menu())
            slider_setvalue(slider, data.toplevel_menu_scale)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.toplevel_menu_scale = slider.value()
            group_box.setTitle(gen_text_menu())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.toplevel_menu_scale)
            group_box.setTitle(gen_text_menu())

        menu_scale_groupbox = self.create_slider(
            group_box_name="ScaleMenus",
            group_box_text="Top Menu:",
            textbox_name="MenuScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.toplevel_menu_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_01.layout().addWidget(menu_scale_groupbox)

        #! =========================[ TOPLEVEL FONT ]======================== !#
        def gen_text_toplvlfont():
            return _generate_text("Toplevel font", data.toplevel_font_scale)

        def inc_func(group_box, slider):
            size = data.toplevel_font_scale
            size += 20
            if size > self.MAX_FACTOR:
                size = self.MAX_FACTOR
            slider_setvalue(slider, size)
            data.toplevel_font_scale = size
            group_box.setTitle(gen_text_toplvlfont())
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            size = data.toplevel_font_scale
            size -= 20
            if size < self.MIN_FACTOR:
                size = self.MIN_FACTOR
            slider_setvalue(slider, size)
            data.toplevel_font_scale = size
            group_box.setTitle(gen_text_toplvlfont())
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            size = slider.value()
            data.toplevel_font_scale = size
            group_box.setTitle(gen_text_toplvlfont())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            size = data.toplevel_font_scale
            slider_setvalue(slider, size)
            group_box.setTitle(gen_text_toplvlfont())

        font_scale_groupbox = self.create_slider(
            group_box_name="ScaleFont",
            group_box_text="Toplevel font:",
            textbox_name="FontScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.toplevel_font_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_01.layout().addWidget(font_scale_groupbox)

        #! ==========================[ GENERAL FONT ]======================== !#
        def gen_text_font():
            return _generate_text("General font", data.general_font_scale)

        def inc_func(group_box, slider):
            size = data.general_font_scale
            size += 20
            if size > self.MAX_FACTOR:
                size = self.MAX_FACTOR
            slider_setvalue(slider, size)
            data.general_font_scale = size
            group_box.setTitle(gen_text_font())
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            size = data.general_font_scale
            size -= 20
            if size < self.MIN_FACTOR:
                size = self.MIN_FACTOR
            slider_setvalue(slider, size)
            data.general_font_scale = size
            group_box.setTitle(gen_text_font())
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            size = slider.value()
            data.general_font_scale = size
            group_box.setTitle(gen_text_font())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            size = data.general_font_scale
            slider_setvalue(slider, size)
            group_box.setTitle(gen_text_font())

        font_scale_groupbox = self.create_slider(
            group_box_name="ScaleFont",
            group_box_text="General font:",
            textbox_name="FontScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.general_font_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_01.layout().addWidget(font_scale_groupbox)

        #! ==========================[ TOP TOOLBAR ]========================= !#
        def gen_text_toolbar():
            return _generate_text("Top toolbar", data.toolbar_scale)

        def inc_func(group_box, slider):
            data.toolbar_scale += 20
            if data.toolbar_scale > self.MAX_FACTOR:
                data.toolbar_scale = self.MAX_FACTOR
            group_box.setTitle(gen_text_toolbar())
            slider_setvalue(slider, data.toolbar_scale)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.toolbar_scale -= 20
            if data.toolbar_scale < self.MIN_FACTOR:
                data.toolbar_scale = self.MIN_FACTOR
            group_box.setTitle(gen_text_toolbar())
            slider_setvalue(slider, data.toolbar_scale)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.toolbar_scale = slider.value()
            group_box.setTitle(gen_text_toolbar())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.toolbar_scale)
            group_box.setTitle(gen_text_toolbar())

        toolbar_scale_slider = self.create_slider(
            group_box_name="ScaleToolbar",
            group_box_text="Top toolbar:",
            textbox_name="ToolbarScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.toolbar_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_02.layout().addWidget(toolbar_scale_slider)

        #! ===========================[ TAB ICON ]=========================== !#
        def gen_text_tabicon():
            return _generate_text("Tab icon", data.custom_tab_scale)

        def inc_func(group_box, slider):
            data.custom_tab_scale += 20
            if data.custom_tab_scale > self.MAX_FACTOR:
                data.custom_tab_scale = self.MAX_FACTOR
            group_box.setTitle(gen_text_tabicon())
            slider_setvalue(slider, data.custom_tab_scale)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.custom_tab_scale -= 20
            if data.custom_tab_scale < self.MIN_FACTOR:
                data.custom_tab_scale = self.MIN_FACTOR
            group_box.setTitle(gen_text_tabicon())
            slider_setvalue(slider, data.custom_tab_scale)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.custom_tab_scale = slider.value()
            group_box.setTitle(gen_text_tabicon())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.custom_tab_scale)
            group_box.setTitle(gen_text_tabicon())

        tab_scale_groupbox = self.create_slider(
            group_box_name="TabIconScale",
            group_box_text="Tab icon:",
            textbox_name="TabIconScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.custom_tab_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_02.layout().addWidget(tab_scale_groupbox)

        #! ==========================[ GENERAL ICON ]======================== !#
        def gen_text_dirtree_button():
            return _generate_text("General icon", data.general_icon_scale)

        def inc_func(group_box, slider):
            data.general_icon_scale += 20
            group_box.setTitle(gen_text_dirtree_button())
            slider_setvalue(slider, data.general_icon_scale)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.general_icon_scale -= 20
            group_box.setTitle(gen_text_dirtree_button())
            slider_setvalue(slider, data.general_icon_scale)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.general_icon_scale = slider.value()
            group_box.setTitle(gen_text_dirtree_button())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.general_icon_scale)
            group_box.setTitle(gen_text_dirtree_button())

        dirtree_scale_groupbox = self.create_slider(
            group_box_name="DirtreeButtonScale",
            group_box_text="General icon:",
            textbox_name="DirtreeButtonScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.general_icon_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_02.layout().addWidget(dirtree_scale_groupbox)

        #! ==========================[ SCROLLBAR ]=========================== !#
        def gen_text_scrollbar():
            return _generate_text("Scrollbar", data.scrollbar_zoom)

        def inc_func(group_box, slider):
            data.scrollbar_zoom += 20
            group_box.setTitle(gen_text_scrollbar())
            slider_setvalue(slider, data.scrollbar_zoom)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.scrollbar_zoom -= 20
            group_box.setTitle(gen_text_scrollbar())
            slider_setvalue(slider, data.scrollbar_zoom)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.scrollbar_zoom = slider.value()
            group_box.setTitle(gen_text_scrollbar())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.scrollbar_zoom)
            group_box.setTitle(gen_text_scrollbar())

        scrollbar_scale_groupbox = self.create_slider(
            group_box_name="ScrollBarScale",
            group_box_text="Scrollbar:",
            textbox_name="ScrollBarScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.scrollbar_zoom),
            slider_minimum=self.MIN_FACTOR,
            slider_maximum=self.MAX_FACTOR,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_03.layout().addWidget(scrollbar_scale_groupbox)

        #! =========================[ PROGRESSBAR ]========================== !#
        def gen_text_progressbar():
            return _generate_text("Progressbar", data.progressbar_zoom)

        def inc_func(group_box, slider):
            data.progressbar_zoom += 20
            group_box.setTitle(gen_text_progressbar())
            slider_setvalue(slider, data.progressbar_zoom)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.progressbar_zoom -= 20
            group_box.setTitle(gen_text_progressbar())
            slider_setvalue(slider, data.progressbar_zoom)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.progressbar_zoom = slider.value()
            group_box.setTitle(gen_text_progressbar())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.progressbar_zoom)
            group_box.setTitle(gen_text_progressbar())

        progressbar_scale_groupbox = self.create_slider(
            group_box_name="ProgressBarScale",
            group_box_text="Progressbar:",
            textbox_name="ProgressBarScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.progressbar_zoom),
            slider_minimum=self.MIN_FACTOR,
            slider_maximum=self.MAX_FACTOR,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_03.layout().addWidget(progressbar_scale_groupbox)

        #! ==========================[ HOME WINDOW ]========================= !#
        def gen_text_home_window():
            return _generate_text("Home window", data.home_window_button_scale)

        def inc_func(group_box, slider):
            data.home_window_button_scale += 20
            if data.home_window_button_scale > self.MAX_FACTOR:
                data.home_window_button_scale = self.MAX_FACTOR
            group_box.setTitle(gen_text_home_window())
            slider_setvalue(slider, data.home_window_button_scale)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.home_window_button_scale -= 20
            if data.home_window_button_scale < self.MIN_FACTOR:
                data.home_window_button_scale = self.MIN_FACTOR
            group_box.setTitle(gen_text_home_window())
            slider_setvalue(slider, data.home_window_button_scale)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.home_window_button_scale = slider.value()
            group_box.setTitle(gen_text_home_window())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.home_window_button_scale)
            group_box.setTitle(gen_text_home_window())

        home_window_groupbox = self.create_slider(
            group_box_name="HomeWindowScale",
            group_box_text="Home window:",
            textbox_name="HomeWindowScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.home_window_button_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )
        groupbox_03.layout().addWidget(home_window_groupbox)

        #! ==========================[ EDITOR VIEW ]========================= !#
        def gen_text_editor():
            return _generate_text(
                "Editor view", settings.editor["zoom_factor"], "x"
            )

        def inc_func(group_box, slider):
            settings.editor["zoom_factor"] += 1
            if settings.editor["zoom_factor"] > 30:
                settings.editor["zoom_factor"] = 30
            group_box.setTitle(gen_text_editor())
            slider_setvalue(slider, settings.editor["zoom_factor"])
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            settings.editor["zoom_factor"] -= 1
            if settings.editor["zoom_factor"] < -10:
                settings.editor["zoom_factor"] = -10
            group_box.setTitle(gen_text_editor())
            slider_setvalue(slider, settings.editor["zoom_factor"])
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            settings.editor["zoom_factor"] = slider.value()
            group_box.setTitle(gen_text_editor())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, settings.editor["zoom_factor"])
            group_box.setTitle(gen_text_editor())

        editor_zoom_groupbox = self.create_slider(
            group_box_name="EditorZoom",
            group_box_text="Editor view:",
            textbox_name="EditorZoomBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(settings.editor["zoom_factor"]),
            slider_minimum=-10,
            slider_maximum=30,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="x",
            ticked_slider=True,
            units_per_tick=1,
        )
        groupbox_04.layout().addWidget(editor_zoom_groupbox)

        #! ==========================[ SPLITTER SIZE ]========================= !#
        #        def update_value(*args):
        #            try:
        #                new_value = args[0]
        #                new_int_value = int(new_value)
        #                data.splitter_width = new_int_value
        #                components.thesquid.TheSquid.update_all()
        #            except:
        #                traceback.print_exc()
        #                print("[SCALING-SPLITTER-WIDTH] Wrong width value: ", args)
        #        splitter_width_groupbox = self.create_textbox(
        #            'SplitterWidth',
        #            'Splitter width:',
        #            'SplitterWidthBox',
        #            "12",
        #            update_func=update_value,
        #            ints_only=True,
        #            max_length=2,
        #        )
        #        groupbox_04.layout().addWidget(splitter_width_groupbox)

        def gen_text_splitter_size():
            return _generate_text(
                "Splitter size", data.splitter_pixelsize, unit="px"
            )

        MIN_SPLITTER_SIZE = 1
        MAX_SPLITTER_SIZE = 40

        def inc_func(group_box, slider):
            data.splitter_pixelsize += 1
            if data.splitter_pixelsize > MAX_SPLITTER_SIZE:
                data.splitter_pixelsize = MAX_SPLITTER_SIZE
            group_box.setTitle(gen_text_splitter_size())
            slider_setvalue(slider, data.splitter_pixelsize)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.splitter_pixelsize -= 1
            if data.splitter_pixelsize < MIN_SPLITTER_SIZE:
                data.splitter_pixelsize = MIN_SPLITTER_SIZE
            group_box.setTitle(gen_text_splitter_size())
            slider_setvalue(slider, data.splitter_pixelsize)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action, *args):
            data.splitter_pixelsize = slider.value()
            group_box.setTitle(gen_text_splitter_size())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider, *args):
            slider_setvalue(slider, data.splitter_pixelsize)
            group_box.setTitle(gen_text_splitter_size())

        splitter_size_groupbox = self.create_slider(
            group_box_name="SplitterWidth",
            group_box_text="Splitter size:",
            textbox_name="SplitterWidthBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=data.splitter_pixelsize,
            slider_minimum=MIN_SPLITTER_SIZE,
            slider_maximum=MAX_SPLITTER_SIZE,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="px",
            ticked_slider=True,
            units_per_tick=1,
        )
        groupbox_04.layout().addWidget(splitter_size_groupbox)

        #! ==========================[ SAVE/LOAD ]=========================== !#
        button_gb = gui.templates.widgetgenerator.create_borderless_groupbox()
        button_layout = self._create_horizontal_layout()
        button_gb.setLayout(button_layout)
        button_size = 40 * data.get_global_scale()
        save_load_button_size = data.get_general_icon_pixelsize() * 4
        # Save
        save_button = gui.helpers.buttons.CustomPushButton(
            parent=None,
            text="SAVE",
            bold=True,
            tooltip="Save all settings",
        )
        save_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        save_button.setFixedSize(
            int(save_load_button_size), int(save_load_button_size * 0.4)
        )

        def save_func(*args):
            self.main_form.settings.save()
            self.main_form.send("restyle")

        save_button.set_click_function(save_func)
        button_layout.addWidget(save_button)

        # Load
        def load_func(*args):
            self.main_form.settings.restore()
            self.update_all_values()
            self.main_form.send("restyle")

        load_button = gui.helpers.buttons.CustomPushButton(
            parent=self,
            text="LOAD",
            bold=True,
            tooltip="Restore all settings",
        )
        load_button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        load_button.setFixedSize(
            int(save_load_button_size), int(save_load_button_size * 0.4)
        )
        load_button.set_click_function(load_func)
        button_layout.addWidget(load_button)

        # Expanded fine tuning
        fine_tunning_expanded_groupbox = self._create_groupbox(
            "ScalingGroupbox", "Fine tuning:"
        )
        self._set_fixed_policy(fine_tunning_expanded_groupbox)
        fine_tunning_expanded_groupbox.setLayout(layout)
        fine_tunning_expanded_groupbox.hide()

        # Contracted fine tuning
        fine_tunning_contracted_groupbox = self._create_groupbox(
            "ScalingGroupbox", "Fine tuning:"
        )
        self._set_fixed_policy(fine_tunning_contracted_groupbox)
        small_layout = qt.QHBoxLayout()
        small_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        margins = small_layout.contentsMargins()
        small_layout.setContentsMargins(
            int(margins.left() + 10),
            int(margins.top() + (2.0 * data.get_general_font_pointsize())),
            int(margins.right() + 27),
            int(margins.bottom() + 10),
        )
        small_button = self._create_button(
            "expand",
            button_size * 1.0,
            "Expand fine tune settings",
            "icons/arrow/triangle/triangle_three_right.png",
            None,
        )
        small_layout.addWidget(small_button)
        small_label = gui.templates.widgetgenerator.create_label(
            text="Click to see more ..."
        )
        font = data.get_general_font()
        font.setBold(False)
        small_label.setFont(font)
        small_layout.addWidget(small_label)
        fine_tunning_contracted_groupbox.setLayout(small_layout)

        #! =========================[ GLOBAL SCALE ]========================= !#
        def gen_text_global():
            return _generate_text("Global scale", data.global_scale)

        def inc_func(group_box, slider):
            data.global_scale += 20
            if data.global_scale > self.MAX_FACTOR:
                data.global_scale = self.MAX_FACTOR
            group_box.setTitle(gen_text_global())
            slider_setvalue(slider, data.global_scale)
            components.thesquid.TheSquid.update_all()

        def dec_func(group_box, slider):
            data.global_scale -= 20
            if data.global_scale < self.MIN_FACTOR:
                data.global_scale = self.MIN_FACTOR
            group_box.setTitle(gen_text_global())
            slider_setvalue(slider, data.global_scale)
            components.thesquid.TheSquid.update_all()

        def slider_moved(group_box, slider, action):
            data.global_scale = slider.value()
            group_box.setTitle(gen_text_global())
            components.thesquid.TheSquid.update_all()

        def update_value(group_box, slider):
            slider_setvalue(slider, data.global_scale)
            group_box.setTitle(gen_text_global())

        global_groupbox: qt.QGroupBox = self.create_slider(
            group_box_name="GlobalScale",
            group_box_text="Global scale:",
            textbox_name="GlobalScaleBox",
            inc_func=inc_func,
            dec_func=dec_func,
            slider_func=slider_moved,
            init_value=int(data.global_scale),
            slider_minimum=60,
            slider_maximum=300,
            slider_value=None,  # default to init_value
            update_func=update_value,
            scale_unit="%",
            ticked_slider=True,
            units_per_tick=20,
        )

        #! =========================[ OUTER LAYOUT ]========================= !#
        outer_layout = qt.QVBoxLayout()
        outer_layout.addWidget(global_groupbox)
        outer_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        outer_layout.addWidget(fine_tunning_contracted_groupbox)
        outer_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )

        outer_layout.addWidget(button_gb)
        outer_layout.setAlignment(
            button_gb,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )

        def expand_func():
            self._reset_fixed_size()
            outer_layout.removeWidget(button_gb)
            outer_layout.removeWidget(fine_tunning_contracted_groupbox)
            fine_tunning_contracted_groupbox.hide()
            outer_layout.addWidget(fine_tunning_expanded_groupbox)
            fine_tunning_expanded_groupbox.show()
            outer_layout.addWidget(button_gb)
            outer_layout.setAlignment(
                button_gb,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
            functions.process_events(10)
            self.top_layout.itemAt(0).widget().resize(
                self.main_groupbox.sizeHint()
            )
            self.top_layout.itemAt(0).widget().widget().resize(
                self.main_groupbox.sizeHint()
            )
            self.resize(self.main_groupbox.sizeHint())
            self.center_to_parent()

        small_button.set_click_function(expand_func)
        small_label.click_signal.connect(expand_func)

        outer_layout.setContentsMargins(0, 0, 0, 0)
        self.main_groupbox.setLayout(outer_layout)
        self.main_groupbox.setContentsMargins(2, 0, 2, 2)

    def update_all_values(self):
        for b in self.stored_button_gboxes.keys():
            box = self.stored_button_gboxes[b]
            if hasattr(box, "update_values"):
                box.update_values()

    def create_slider(
        self,
        group_box_name: str,
        group_box_text: str,
        textbox_name: str,
        inc_func: Callable,
        dec_func: Callable,
        slider_func: Callable,
        init_value: int,
        slider_minimum: int = -1,
        slider_maximum: int = -1,
        slider_value: Optional[int] = None,
        update_func: Optional[Callable] = None,
        scale_unit: str = "%",
        ticked_slider: bool = False,
        units_per_tick: int = 10,
    ) -> qt.QGroupBox:
        """"""
        base_scale = 14
        button_size = base_scale * data.get_global_scale()

        group_box = self._create_groupbox(group_box_name, group_box_text)
        group_box.setStyleSheet(
            f"""
        QGroupBox {{
            font-size        : {data.get_general_font_pointsize()}pt;
            color            : {data.theme["fonts"]["default"]["color"]};
            border           : none;
            background-color : transparent;
            margin-left      : 0px;
            margin-top       : 0px;
            margin-bottom    : 0px;
            margin-right     : 0px;
            padding          : 0px;
            spacing          : 0px;
        }}
        """
        )

        inner_layout = qt.QHBoxLayout()
        inner_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        fm = qt.QFontMetrics(data.get_general_font())
        br = fm.boundingRect(group_box_text)
        inner_layout.setContentsMargins(5, int(br.height() * 1.3), 7, 5)
        inner_layout.setSpacing(3)
        group_box.setLayout(inner_layout)

        dec_button = self._create_button(
            "dec",
            button_size,
            "Decrease size",
            "icons/arrow/chevron/chevron_left.png",
            None,
        )
        inner_layout.addWidget(dec_button)

        if ticked_slider:
            slider: gui.templates.baseslider.TickedSlider = (
                self._create_ticked_slider(
                    qt.Qt.Orientation.Horizontal,
                    units_per_tick=units_per_tick,
                )
            )
        else:
            slider: gui.templates.baseslider.BaseSlider = self._create_slider(
                qt.Qt.Orientation.Horizontal
            )
        slider.setSizePolicy(
            qt.QSizePolicy.Policy.Fixed,
            qt.QSizePolicy.Policy.Ignored,
        )
        if slider_minimum == -1 and slider_maximum == -1:
            slider.setMinimum(self.MIN_FACTOR)
            slider.setMaximum(self.MAX_FACTOR)
        else:
            slider.setMinimum(slider_minimum)
            slider.setMaximum(slider_maximum)
        if slider_value is not None:
            slider_setvalue(slider, int(slider_value))
        else:
            slider_setvalue(slider, int(init_value))

        # slider.valueChanged.connect(
        slider.changed.connect(
            functools.partial(slider_func, group_box, slider)
        )
        inner_layout.addWidget(slider)

        group_box.setTitle(
            str(group_box_text + " " + str(int(init_value)) + scale_unit).ljust(
                LJUST_LEN
            )
        )

        inc_button = self._create_button(
            "inc",
            button_size,
            "Increase size",
            "icons/arrow/chevron/chevron_right.png",
            None,
        )
        inner_layout.addWidget(inc_button)

        dec_button.set_click_function(
            functools.partial(dec_func, group_box, slider)
        )
        inc_button.set_click_function(
            functools.partial(inc_func, group_box, slider)
        )

        if callable(update_func):
            group_box.update_values = functools.partial(
                update_func, group_box, slider
            )

        self.stored_button_gboxes[group_box_name] = group_box

        slider.setMinimumWidth(group_box.sizeHint().width())
        slider.setMinimumHeight(int(30 * data.get_global_scale()))
        inc_button.setMinimumSize(
            int(22 * data.get_global_scale()), int(22 * data.get_global_scale())
        )
        dec_button.setMinimumSize(
            int(22 * data.get_global_scale()), int(22 * data.get_global_scale())
        )

        return group_box

    def create_textbox(
        self,
        group_box_name,
        group_box_text,
        textbox_name,
        init_value,
        update_func=None,
        **kwargs,
    ):
        group_box = self._create_groupbox(group_box_name, group_box_text)
        group_box.setStyleSheet(
            f"""
        QGroupBox {{
            font-size        : {data.get_general_font_pointsize()}pt;
            color            : {data.theme["fonts"]["default"]["color"]};
            border           : none;
            background-color : transparent;
            margin-left      : 0px;
            margin-top       : 0px;
            margin-bottom    : 0px;
            margin-right     : 0px;
            padding          : 0px;
            spacing          : 0px;
        }}
        """
        )

        inner_layout = qt.QHBoxLayout()
        inner_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        fm = qt.QFontMetrics(data.get_general_font())
        br = fm.boundingRect(group_box_text)
        inner_layout.setContentsMargins(5, br.height() * 1.3, 7, 5)
        inner_layout.setSpacing(3)
        group_box.setLayout(inner_layout)

        textbox = self._create_textbox(
            textbox_name,
            func=update_func,
            read_only=False,
            enabled=True,
            **kwargs,
        )
        textbox.setText(init_value)
        inner_layout.addWidget(textbox)

        group_box.setTitle(group_box_text)

        if callable(update_func):
            textbox.textEdited.connect(update_func)

        self.stored_button_gboxes[group_box_name] = group_box

        textbox.setMinimumWidth(group_box.sizeHint().width())
        textbox.setMaximumWidth(group_box.sizeHint().width())

        return group_box

    def _create_button(self, name, edge_length, tool_tip, icon_name, parent):
        icon_offset = 6
        button = gui.helpers.buttons.CustomPushButton(
            parent=parent,
            icon_path=icon_name,
            icon_size=qt.create_qsize(
                edge_length - icon_offset, edge_length - icon_offset
            ),
            align_text="center",
        )
        button.setFixedSize(int(edge_length), int(edge_length))
        button.setStyleSheet(
            gui.stylesheets.button.get_simple_toggle_stylesheet()
        )
        button.setToolTip(tool_tip)
        button.enable()
        return button

    def create_horizontal_box(self):
        hor_box = gui.templates.widgetgenerator.create_groupbox_with_layout(
            None,
            None,
            vertical=False,
            borderless=True,
            margins=(5, data.get_general_font_pointsize() / 2, 5, 5),
        )
        return hor_box

    """
    Overridden functions
    """

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        pressed_key = e.key()
        if pressed_key == qt.Qt.Key.Key_Escape:
            self.hide()

    def showEvent(self, event):
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
        )
        self.center_to_parent()

    def closeEvent(self, event):
        super().closeEvent(event)
