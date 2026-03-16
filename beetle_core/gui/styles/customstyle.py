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
import qt, data, functions, iconfunctions


class CustomStyle(qt.QCommonStyle):
    """Custom style for changing the look of embeetle's menubar and menubar
    submenus."""

    custom_font = None
    custom_font_metrics = None

    def __init__(self, style_name: str, enlarge: float = 1.0) -> None:
        """"""
        super().__init__()
        self._style: Union[qt.QStyle, qt.QProxyStyle] = qt.QStyleFactory.create(
            style_name
        )
        if self._style is None:
            raise Exception(
                f"Style '{style_name}' is not valid on this system!"
            )
        """
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        This needs to happen on CustomStyle initialization,
        otherwise the font's bounding rectangle in not calculated
        correctly!
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """
        if enlarge < 1.0:
            enlarge = 1.0
        self.scale_constant = int(data.get_toplevel_menu_pixelsize() * enlarge)
        self.custom_font = qt.QFont(
            data.get_global_font_family(),
            data.get_toplevel_font_pointsize(),
        )
        self.custom_font_metrics = qt.QFontMetrics(self.custom_font)
        self.close_icon = iconfunctions.get_qpixmap("icons/tab/close.png")
        self.close_icon_hovered = iconfunctions.get_qpixmap(
            "icons/tab/close_hover.png"
        )
        self.close_icon_clicked = iconfunctions.get_qpixmap(
            "icons/tab/close_press.png"
        )
        return

    def drawComplexControl(
        self,
        cc: qt.QStyle.ComplexControl,
        opt: qt.QStyleOptionComplex,
        p: qt.QPainter,
        widget: Optional[qt.QWidget] = None,
    ) -> None:
        """"""
        self._style.drawComplexControl(cc, opt, p, widget)
        return

    def drawControl(
        self,
        ce: qt.QStyle.ControlElement,
        opt: qt.QStyleOption,
        p: qt.QPainter,
        widget: Optional[qt.QWidget] = None,
    ) -> None:
        """"""
        if ce == qt.QStyle.ControlElement.CE_MenuItem:
            # Store the item's pixmap
            pixmap = opt.icon.pixmap(self.scale_constant)
            # Disable the icon from being drawn automatically
            opt.icon = qt.QIcon()
            # Adjust the font
            opt.font = self.custom_font
            # Setup and draw everything except the icon
            opt.maxIconWidth = self.scale_constant
            self._style.drawControl(ce, opt, p, widget)
            if not pixmap.isNull():
                # Manually draw the icon
                alignment = qt.Qt.AlignmentFlag.AlignLeft
                self.drawItemPixmap(p, opt.rect, alignment, pixmap)
        elif ce == qt.QStyle.ControlElement.CE_MenuBarItem:
            text = opt.text.replace("&", "")
            opt.text = ""
            self._style.drawControl(ce, opt, p, widget)
            alignment = qt.Qt.AlignmentFlag.AlignCenter
            p.setFont(self.custom_font)
            self.drawItemText(
                p,
                opt.rect,
                alignment,
                opt.palette,
                opt.state,
                text,
                qt.QPalette.ColorRole.NoRole,
            )
        else:
            self._style.drawControl(ce, opt, p, widget)
        return

    def drawPrimitive(
        self,
        pe: qt.QStyle.PrimitiveElement,
        opt: qt.QStyleOption,
        p: qt.QPainter,
        widget: Optional[qt.QWidget] = None,
    ):
        """
        QStyle.PE_FrameStatusBar: 7
        QStyle.PrimitiveElement.PE_PanelButtonCommand: 13
        QStyle.PrimitiveElement.PE_FrameDefaultButton: 1
        QStyle.PrimitiveElement.PE_PanelButtonBevel: 14
        QStyle.PrimitiveElement.PE_PanelButtonTool: 15
        QStyle.PrimitiveElement.PE_PanelLineEdit: 18
        QStyle.PrimitiveElement.PE_IndicatorButtonDropDown: 24
        QStyle.PrimitiveElement.PE_FrameFocusRect: 3
        QStyle.PrimitiveElement.PE_IndicatorArrowUp: 22
        QStyle.PrimitiveElement.PE_IndicatorArrowDown: 19
        QStyle.PrimitiveElement.PE_IndicatorArrowRight: 21
        QStyle.PrimitiveElement.PE_IndicatorArrowLeft: 20
        QStyle.PrimitiveElement.PE_IndicatorSpinUp: 35
        QStyle.PrimitiveElement.PE_IndicatorSpinDown: 32
        QStyle.PrimitiveElement.PE_IndicatorSpinPlus: 34
        QStyle.PrimitiveElement.PE_IndicatorSpinMinus: 33
        QStyle.PrimitiveElement.PE_IndicatorItemViewItemCheck: 25
        QStyle.PrimitiveElement.PE_IndicatorCheckBox: 26
        QStyle.PrimitiveElement.PE_IndicatorRadioButton: 31
        QStyle.PrimitiveElement.PE_IndicatorDockWidgetResizeHandle: 27
        QStyle.PrimitiveElement.PE_Frame: 0
        QStyle.PrimitiveElement.PE_FrameMenu: 6
        QStyle.PrimitiveElement.PE_PanelMenuBar: 16
        QStyle.PrimitiveElement.PE_PanelScrollAreaCorner: 40
        QStyle.PrimitiveElement.PE_FrameDockWidget: 2
        QStyle.PrimitiveElement.PE_FrameTabWidget: 8
        QStyle.PrimitiveElement.PE_FrameLineEdit: 5
        QStyle.PrimitiveElement.PE_FrameGroupBox: 4
        QStyle.PrimitiveElement.PE_FrameButtonBevel: 10
        QStyle.PrimitiveElement.PE_FrameButtonTool: 11
        QStyle.PrimitiveElement.PE_IndicatorHeaderArrow: 28
        QStyle.PrimitiveElement.PE_FrameStatusBarItem: 7
        QStyle.PrimitiveElement.PE_FrameWindow: 9
        QStyle.PrimitiveElement.PE_IndicatorMenuCheckMark: 29
        QStyle.PrimitiveElement.PE_IndicatorProgressChunk: 30
        QStyle.PrimitiveElement.PE_IndicatorBranch: 23
        QStyle.PrimitiveElement.PE_IndicatorToolBarHandle: 36
        QStyle.PrimitiveElement.PE_IndicatorToolBarSeparator: 37
        QStyle.PrimitiveElement.PE_PanelToolBar: 17
        QStyle.PrimitiveElement.PE_PanelTipLabel: 38
        QStyle.PrimitiveElement.PE_FrameTabBarBase: 12
        QStyle.PrimitiveElement.PE_IndicatorTabTear: 39
        QStyle.PrimitiveElement.PE_IndicatorColumnViewArrow: 42
        QStyle.PrimitiveElement.PE_Widget: 41
        QStyle.PrimitiveElement.PE_CustomBase: 251658240
        QStyle.PrimitiveElement.PE_IndicatorItemViewItemDrop: 43
        QStyle.PrimitiveElement.PE_PanelItemViewItem: 44
        QStyle.PrimitiveElement.PE_PanelItemViewRow: 45
        QStyle.PrimitiveElement.PE_PanelStatusBar: 46
        QStyle.PrimitiveElement.PE_IndicatorTabClose: 47
        QStyle.PrimitiveElement.PE_PanelMenu: 48
        """
        if pe == qt.QStyle.PrimitiveElement.PE_IndicatorTabClose:
            offset = 5
            # Adjust the close button on basic widget tabs
            image_scale_size = qt.create_qsize(
                self.scale_constant - offset, self.scale_constant - offset
            )
            # print(int(opt.state))
            value = int(opt.state)
            if value & 0b001 and value & 0b010:
                # Hovered
                self.close_icon_hovered = self.close_icon_hovered.scaled(
                    image_scale_size
                )
                p.drawPixmap(
                    opt.rect.left() + offset,
                    opt.rect.top() + (offset / 2),
                    self.close_icon_hovered,
                )
            elif value & 0b001 and value & 0b100:
                # Clicked
                self.close_icon_clicked = self.close_icon_clicked.scaled(
                    image_scale_size
                )
                p.drawPixmap(
                    opt.rect.left() + offset,
                    opt.rect.top() + (offset / 2),
                    self.close_icon_clicked,
                )
            else:
                self.close_icon = self.close_icon.scaled(image_scale_size)
                p.drawPixmap(
                    opt.rect.left() + offset,
                    opt.rect.top() + (offset / 2),
                    self.close_icon,
                )
        else:
            self._style.drawPrimitive(pe, opt, p, widget)
        return

    def drawItemPixmap(
        self,
        painter: qt.QPainter,
        rect: qt.QRect,
        alignment: int,
        pixmap: qt.QPixmap,
    ) -> None:
        """"""
        scaled_pixmap = pixmap.scaled(self.scale_constant, self.scale_constant)
        self._style.drawItemPixmap(painter, rect, alignment, scaled_pixmap)
        return

    def drawItemText(
        self,
        painter: qt.QPainter,
        rectangle: qt.QRect,
        alignment: int,
        palette: qt.QPalette,
        enabled: bool,
        text: str,
        textRole: qt.QPalette.ColorRole = qt.QPalette.ColorRole.NoRole,
    ) -> None:
        """"""
        if qt.sip.isdeleted(self._style):
            return
        self._style.drawItemText(
            painter, rectangle, alignment, palette, enabled, text, textRole
        )
        return

    def itemPixmapRect(
        self,
        r: qt.QRect,
        flags: int,
        pixmap: qt.QPixmap,
    ) -> Optional[qt.QRect]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.itemPixmapRect(r, flags, pixmap)

    def itemTextRect(
        self,
        fm: qt.QFontMetrics,
        r: qt.QRect,
        flags: int,
        enabled: bool,
        text: str,
    ) -> Optional[qt.QRect]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.itemTextRect(fm, r, flags, enabled, text)

    def generatedIconPixmap(
        self,
        iconMode: qt.QIcon.Mode,
        pixmap: qt.QPixmap,
        opt: qt.QStyleOption,
    ) -> Optional[qt.QPixmap]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.generatedIconPixmap(iconMode, pixmap, opt)

    def hitTestComplexControl(
        self,
        cc: qt.QStyle.ComplexControl,
        opt: qt.QStyleOptionComplex,
        pt: qt.QPoint,
        widget: Optional[qt.QWidget] = None,
    ) -> Optional[qt.QStyle.SubControl]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.hitTestComplexControl(cc, opt, pt, widget)

    def pixelMetric(
        self,
        m: Union[qt.QStyle.PixelMetric, qt.QStyle.PrimitiveElement],
        option: Optional[qt.QStyleOption] = None,
        widget: Optional[qt.QWidget] = None,
    ) -> int:
        """"""
        if qt.sip.isdeleted(self._style):
            return 0
        if m == qt.QStyle.PixelMetric.PM_SmallIconSize:
            return self.scale_constant
        if m == qt.QStyle.PrimitiveElement.PE_IndicatorProgressChunk:
            # This is the Menubar, don't know why it's called IndicatorProgressChunk?
            return int(self.scale_constant / 6)
        return self._style.pixelMetric(m, option, widget)

    def polish(self, widget: qt.QWidget) -> None:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.polish(widget)

    def sizeFromContents(
        self,
        ct: qt.QStyle.ContentsType,
        opt: qt.QStyleOption,
        contentsSize: qt.QSize,
        widget: Optional[qt.QWidget] = None,
    ) -> qt.QSize:
        """"""
        if ct == qt.QStyle.ContentsType.CT_MenuItem:
            scaled_width = self.scale_constant * 2.0
            # .width() of QFontMetrics has been renamed to .horizontalAdvance()
            resized_width = (
                self.custom_font_metrics.horizontalAdvance(opt.text)
                + scaled_width
            )
            result = qt.create_qsize(resized_width, self.scale_constant)
            return result

        if ct == qt.QStyle.ContentsType.CT_MenuBarItem:
            # .width() of QFontMetrics has been renamed to .horizontalAdvance()
            base_width = self.custom_font_metrics.horizontalAdvance(opt.text)
            scaled_width = self.scale_constant * 2.0
            if base_width < scaled_width:
                result = qt.create_qsize(scaled_width, self.scale_constant)
            else:
                result = qt.create_qsize(base_width, self.scale_constant)
            return result

        return self._style.sizeFromContents(ct, opt, contentsSize, widget)

    def combinedLayoutSpacing(
        self,
        control1: qt.QSizePolicy.ControlType,
        control2: qt.QSizePolicy.ControlType,
        orientation: qt.Qt.Orientation,
        option: Optional[qt.QStyleOption] = None,
        widget: Optional[qt.QWidget] = None,
    ) -> int:
        """"""
        if qt.sip.isdeleted(self._style):
            return 0
        return self._style.combinedLayoutSpacing(
            control1, control2, orientation, option, widget
        )

    def layoutSpacing(
        self,
        control1: qt.QSizePolicy.ControlType,
        control2: qt.QSizePolicy.ControlType,
        orientation: qt.Qt.Orientation,
        option: Optional[qt.QStyleOption] = None,
        widget: Optional[qt.QWidget] = None,
    ) -> int:
        """"""
        if qt.sip.isdeleted(self._style):
            return 0
        return self._style.layoutSpacing(
            control1, control2, orientation, option, widget
        )

    # def layoutSpacingImplementation(self, control1, control2, orientation, option = None, widget = None):
    #     return self._style.layoutSpacingImplementation(control1, control2, orientation, option, widget) if not qt.sip.isdeleted(self._style) else None
    # def standardIconImplementation(self, standardIcon, option=None, widget=None):
    #     return self._style.standardIconImplementation(standardIcon, option, widget) if not qt.sip.isdeleted(self._style) else None

    def standardIcon(
        self,
        standardIcon: qt.QStyle.StandardPixmap,
        option: Optional[qt.QStyleOption] = None,
        widget: Optional[qt.QWidget] = None,
    ) -> Optional[qt.QIcon]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.standardIcon(standardIcon, option, widget)

    def standardPalette(self) -> Optional[qt.QPalette]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.standardPalette()

    def standardPixmap(
        self,
        sp: qt.QStyle.StandardPixmap,
        option: Optional[qt.QStyleOption] = None,
        widget: Optional[qt.QWidget] = None,
    ) -> Optional[qt.QPixmap]:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.standardPixmap(sp, option, widget)

    def styleHint(
        self,
        sh: qt.QStyle.StyleHint,
        option: Optional[qt.QStyleOption] = None,
        widget: Optional[qt.QWidget] = None,
        returnData: Optional[qt.QStyleHintReturn] = None,
    ) -> int:
        """"""
        if qt.sip.isdeleted(self._style):
            return 0
        return self._style.styleHint(sh, option, widget, returnData)

    def subControlRect(
        self,
        cc: qt.QStyle.ComplexControl,
        opt: qt.QStyleOptionComplex,
        sc: qt.QStyle.SubControl,
        widget: Optional[qt.QWidget] = None,
    ) -> qt.QRect:
        """"""
        if qt.sip.isdeleted(self._style):
            return qt.QRect()
        return self._style.subControlRect(cc, opt, sc, widget)

    def subElementRect(
        self,
        e: qt.QStyle.SubElement,
        opt: qt.QStyleOption,
        widget: Optional[qt.QWidget] = None,
    ) -> qt.QRect:
        """"""
        if qt.sip.isdeleted(self._style):
            return qt.QRect()
        return self._style.subElementRect(e, opt, widget)

    def unpolish(self, widget: qt.QWidget) -> None:
        """"""
        if qt.sip.isdeleted(self._style):
            return None
        return self._style.unpolish(widget)
