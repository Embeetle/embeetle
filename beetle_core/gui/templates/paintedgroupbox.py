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

from typing import *
import qt, data, functions
import gui.templates.widgetgenerator

if TYPE_CHECKING:
    import gui.helpers.buttons
    import gui.stylesheets
    import gui.stylesheets.label
    import gui.stylesheets.button


class PaintedGroupBox(qt.QGroupBox):
    def __init__(self, parent: Optional[qt.QObject] = None) -> None:
        """"""
        super().__init__(parent)
        self.dead: bool = False
        return

    def paintEvent(self, e: qt.QPaintEvent) -> None:
        """"""
        qp = qt.QPainter()
        qp.begin(self)
        qp.setPen(qt.QColor(data.theme["button_border"]))
        y_start = data.get_general_font_pointsize()
        point = (0, y_start)
        height = (self.size().height() - y_start) - 1
        size = (self.size().width() - 1, height)
        brush = qt.QBrush(
            qt.QColor(data.theme["fonts"]["default"]["background"])
        )
        qp.fillRect(*point, *size, brush)
        # [Operation remove borders]
        # qp.drawRect(*point, *size)
        qp.end()
        super().paintEvent(e)
        return

    def self_destruct(
        self,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill PaintedGroupBox() twice!")
            self.dead = True

        # Invoke 'clean_layout()' from 'functions.py' to delete all the children in self.layout().
        # These children can be sub-layouts or just widgets.
        functions.clean_layout(self.layout())
        # At this point, 'self.layout()' is clean. However, it still exists, the 'functions.clean_
        # layout()' does not deparent it. I tried to do that here like this:
        #     > lyt = self.layout()
        #     > if lyt is not None:
        #     >     if not qt.sip.isdeleted(lyt):
        #     >         lyt.setParent(None)
        # Unfortunately, that leads to a crash without traceback. I have no idea why. Please help
        # @Matic

        # Now deparent this PaintedGroupBox() widget:
        if not qt.sip.isdeleted(self):
            self.setParent(None)  # noqa
        return


class PaintedGroupBoxWithLayoutAndInfoButton(PaintedGroupBox):
    """
    This class should provide a 'PaintedGroupBox()' instance that you normally would get through the
    static method:
        > 'create_groupbox_with_layout_and_info_button()'

    Reason I made this class:
    While the static method gives a very useful 'PaintedGroupBox()' instance, it cannot be subclas-
    sed. The class I just wrote here is a way for me to enable subclassing.
    """

    def __init__(
        self,
        parent: Optional[qt.QObject],
        name: str,
        text,
        info_func,
        h_size_policy: Union[qt.QSizePolicy, Any],
        v_size_policy: Union[qt.QSizePolicy, Any],
    ) -> None:
        """
        The parameters for the constructor are very similar to the parameters from:
            - The static method 'create_groupbox_with_layout_and_info_button()',
              see below.
            - The method 'create_info_groupbox()' from the GeneralWizard()
              class, see file 'projectcreationdialogs.py'.

        I didn't keep all the parameters though - only those I use regularly.

        :param parent:             Parent widget.
        :param name:               Name of the widget [not sure what it's actually used for]
        :param text:               The title.
        :param info_func:          Function callback for info button click.
        :param h_size_policy:      QSizePolicy enum for horizontal sizing.
        :param v_size_policy:      QSizePolicy enum for vertical sizing.

        """
        super().__init__(parent)
        # Note: the 'self' here corresponds to the 'wrapper_box' in the static
        # method 'create_groupbox_with_layout_and_info_button()'.
        self.setSizePolicy(
            h_size_policy,
            v_size_policy,
        )
        self.setLayout(qt.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # * Groupbox
        margin = data.get_general_icon_pixelsize() * 0.5
        groupbox = gui.templates.widgetgenerator.create_groupbox_with_layout(
            name=f"{name}-groupbox",
            text="",
            vertical=True,
            borderless=False,
            background_color=None,
            spacing=5,
            margins=(margin, margin / 2, margin / 2, margin),
            h_size_policy=h_size_policy,
            v_size_policy=v_size_policy,
            adjust_margins_to_text=False,
            parent=self,
        )

        # * Title
        margin = data.get_general_icon_pixelsize() * 0.3
        title_box = gui.templates.widgetgenerator.create_groupbox_with_layout(
            f"{name}-titlebox",
            vertical=False,
            borderless=True,
            spacing=0,
            margins=(margin, 0, 0, 0),
            parent=self,
            h_size_policy=qt.QSizePolicy.Policy.Fixed,
            v_size_policy=qt.QSizePolicy.Policy.Fixed,
        )
        label = gui.templates.widgetgenerator.create_label(
            text=text,
            bold=True,
            parent=title_box,
        )
        label.setStyleSheet(gui.stylesheets.label.get_title_stylesheet())
        label.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        spacing = data.get_general_icon_pixelsize() * 0.1
        title_box.layout().setSpacing(int(spacing))
        title_box.layout().addWidget(label)

        # * Info button
        if info_func is not None:
            info_size = data.get_general_icon_pixelsize()
            info_button = gui.helpers.buttons.CustomPushButton(
                parent=title_box,
                icon_path="icons/dialog/help.png",
                icon_size=qt.create_qsize(info_size - 4, info_size - 4),
                align_text=None,
                padding="0px",
            )
            info_button.setStyleSheet(
                gui.stylesheets.button.get_simple_toggle_stylesheet()
            )
            info_button.setFixedSize(int(info_size), int(info_size))
            info_button.clicked.connect(info_func)  # type: ignore
            title_box.layout().addWidget(info_button)

        # * Put all in the layout
        self.layout().addWidget(title_box)
        self.layout().addWidget(groupbox)
        self.original_layout = self.layout()
        self.title_box = title_box
        self.group_box = groupbox
        self.layout = lambda: groupbox.layout()
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
                    "Trying to kill PaintedGroupBoxWithLayoutAndInfoButton() twice!"
                )
            self.dead = True

        # Clean up the title_box and
        # deparent it.
        lyt = self.title_box.layout()
        functions.clean_layout(lyt)
        # if lyt is not None:               ┐
        #     if not qt.sip.isdeleted(lyt): │ crashes without traceback
        #         lyt.setParent(None)       ┘
        del lyt
        self.title_box.setParent(None)  # type: ignore
        self.title_box = None

        # Clean up the group_box and
        # deparent it.
        lyt = self.group_box.layout()
        functions.clean_layout(lyt)
        # if lyt is not None:               ┐
        #     if not qt.sip.isdeleted(lyt): │ crashes without traceback
        #         lyt.setParent(None)       ┘
        del lyt
        self.group_box.setParent(None)  # type: ignore
        self.group_box = None

        # Clean up the original layout
        # and deparent oneself
        lyt = self.original_layout
        functions.clean_layout(lyt)
        # if lyt is not None:               ┐
        #     if not qt.sip.isdeleted(lyt): │ crashes without traceback
        #         lyt.setParent(None)       ┘
        del lyt
        self.setParent(None)  # type: ignore
        return
