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
import qt
import data
import purefunctions, functions
import re
import gui.templates.baseobject
import gui.stylesheets.scrollbar

if TYPE_CHECKING:
    import lexers
    import lexers.baselexer


"""
---------------------------------------------
The foundation for all editors
---------------------------------------------
"""


class BaseEditor(qt.QsciScintilla, gui.templates.baseobject.BaseObject):

    def __init__(self, parent, main_form) -> None:
        """"""
        qt.QsciScintilla.__init__(self, parent)
        gui.templates.baseobject.BaseObject.__init__(
            self, parent, main_form, "", None
        )
        # Hotspot signals
        self.SCN_HOTSPOTCLICK.connect(self.__hotspot_click)
        self.SCN_HOTSPOTDOUBLECLICK.connect(self.__hotspot_doubleclick)
        self.SCN_HOTSPOTRELEASECLICK.connect(self.__hotspot_releaseclick)
        # The filter is prepared in case we ever wish to
        # override the default keyboard shurtcut functionality
        # of QScintilla

    #        self.installEventFilter(self)
    #    def eventFilter(self, object, event):
    #        """
    #        Relevant event type numbers:
    #            2: mouse press
    #            3: mouse release
    #            6: key press
    #            7: key release
    #        """
    #        if event.type() == 7 or \
    #           event.type() == 3:
    #                print("EDITOR-EVENT:", event.type())
    #        return False

    def lexer(self) -> Union[
        lexers.ada.Ada,
        lexers.assembly.Assembly,
        lexers.baselexer.BaseLexer,
        lexers.c.CustomC,
        lexers.cython.Cython,
        lexers.linkerscript.LinkerScript,
        lexers.makefile.CustomMakefile,
        lexers.nim.Nim,
        lexers.oberon.Oberon,
        lexers.python.Python,
        lexers.routeros.RouterOS,
        lexers.text.Text,
        qt.QsciLexer,
    ]:
        """This method is overridden for the sake of proper type hinting."""
        return super().lexer()

    def setEolMode(self, mode: Union[qt.QsciScintilla.EolMode, int]) -> None:
        """
        PyQt6 compatibility:
        In PyQt5, the method 'setEolMode()' seemed to accept integers. In PyQt6 no more. Therefore,
        I have overridden the method to fix the problem.
        """
        if isinstance(mode, int):
            if mode == 0:
                mode = qt.QsciScintilla.EolMode.EolWindows
            elif mode == 1:
                mode = qt.QsciScintilla.EolMode.EolUnix
            elif mode == 2:
                mode = qt.QsciScintilla.EolMode.EolMac
            else:
                mode = qt.QsciScintilla.EolMode.EolUnix
        super().setEolMode(mode)
        return

    def markerDefine(
        self,
        sym: Optional[
            Union[
                int, qt.QsciScintilla.MarkerSymbol, str, qt.QPixmap, qt.QImage
            ]
        ] = None,
        num: Optional[int] = None,
    ) -> int:
        """
        PyQt6 compatibility:
        The first argument 'sym' can be a marker symbol (chosen from an enum), a string, a pixmap or
        an image. If it's a string, pixmap or image, PyQt5 and PyQt6 behave the same. Not so if it
        is a marker symbol. PyQt5 accepts an integer marker symbol, which can be a plain number or
        one of these:
            qt.QsciScintillaBase.SC_MARK_CIRCLE
            qt.QsciScintillaBase.SC_MARK_ROUNDRECT
            qt.QsciScintillaBase.SC_MARK_ARROW
            ...
        which are basically integers too.

        PyQt6 only accepts enums from type 'qt.QsciScintilla.MarkerSymbol'. Therefore, I implemented
        a compatibility table.
        """
        if not isinstance(sym, int):
            return super().markerDefine(sym, num)

        compat_table: Dict[int, qt.QsciScintilla.MarkerSymbol] = {
            qt.QsciScintillaBase.SC_MARK_CIRCLE: (
                qt.QsciScintilla.MarkerSymbol.Circle
            ),
            qt.QsciScintillaBase.SC_MARK_ROUNDRECT: (
                qt.QsciScintilla.MarkerSymbol.Rectangle
            ),
            qt.QsciScintillaBase.SC_MARK_ARROW: (
                qt.QsciScintilla.MarkerSymbol.RightTriangle
            ),
            qt.QsciScintillaBase.SC_MARK_SMALLRECT: (
                qt.QsciScintilla.MarkerSymbol.SmallRectangle
            ),
            qt.QsciScintillaBase.SC_MARK_SHORTARROW: (
                qt.QsciScintilla.MarkerSymbol.RightArrow
            ),
            qt.QsciScintillaBase.SC_MARK_EMPTY: (
                qt.QsciScintilla.MarkerSymbol.Invisible
            ),
            qt.QsciScintillaBase.SC_MARK_ARROWDOWN: (
                qt.QsciScintilla.MarkerSymbol.DownTriangle
            ),
            qt.QsciScintillaBase.SC_MARK_MINUS: (
                qt.QsciScintilla.MarkerSymbol.Minus
            ),
            qt.QsciScintillaBase.SC_MARK_PLUS: (
                qt.QsciScintilla.MarkerSymbol.Plus
            ),
            qt.QsciScintillaBase.SC_MARK_VLINE: (
                qt.QsciScintilla.MarkerSymbol.VerticalLine
            ),
            qt.QsciScintillaBase.SC_MARK_LCORNER: (
                qt.QsciScintilla.MarkerSymbol.BottomLeftCorner
            ),
            qt.QsciScintillaBase.SC_MARK_TCORNER: (
                qt.QsciScintilla.MarkerSymbol.LeftSideSplitter
            ),
            qt.QsciScintillaBase.SC_MARK_BOXPLUS: (
                qt.QsciScintilla.MarkerSymbol.BoxedPlus
            ),
            qt.QsciScintillaBase.SC_MARK_BOXPLUSCONNECTED: (
                qt.QsciScintilla.MarkerSymbol.BoxedPlusConnected
            ),
            qt.QsciScintillaBase.SC_MARK_BOXMINUS: (
                qt.QsciScintilla.MarkerSymbol.BoxedMinus
            ),
            qt.QsciScintillaBase.SC_MARK_BOXMINUSCONNECTED: (
                qt.QsciScintilla.MarkerSymbol.BoxedMinusConnected
            ),
            qt.QsciScintillaBase.SC_MARK_LCORNERCURVE: (
                qt.QsciScintilla.MarkerSymbol.RoundedBottomLeftCorner
            ),
            qt.QsciScintillaBase.SC_MARK_TCORNERCURVE: (
                qt.QsciScintilla.MarkerSymbol.LeftSideRoundedSplitter
            ),
            qt.QsciScintillaBase.SC_MARK_CIRCLEPLUS: (
                qt.QsciScintilla.MarkerSymbol.CircledPlus
            ),
            qt.QsciScintillaBase.SC_MARK_CIRCLEPLUSCONNECTED: (
                qt.QsciScintilla.MarkerSymbol.CircledPlusConnected
            ),
            qt.QsciScintillaBase.SC_MARK_CIRCLEMINUS: (
                qt.QsciScintilla.MarkerSymbol.CircledMinus
            ),
            qt.QsciScintillaBase.SC_MARK_CIRCLEMINUSCONNECTED: (
                qt.QsciScintilla.MarkerSymbol.CircledMinusConnected
            ),
            qt.QsciScintillaBase.SC_MARK_BACKGROUND: (
                qt.QsciScintilla.MarkerSymbol.Background
            ),
            qt.QsciScintillaBase.SC_MARK_DOTDOTDOT: (
                qt.QsciScintilla.MarkerSymbol.ThreeDots
            ),
            qt.QsciScintillaBase.SC_MARK_ARROWS: (
                qt.QsciScintilla.MarkerSymbol.ThreeRightArrows
            ),
            qt.QsciScintillaBase.SC_MARK_FULLRECT: (
                qt.QsciScintilla.MarkerSymbol.FullRectangle
            ),
            qt.QsciScintillaBase.SC_MARK_LEFTRECT: (
                qt.QsciScintilla.MarkerSymbol.LeftRectangle
            ),
            qt.QsciScintillaBase.SC_MARK_UNDERLINE: (
                qt.QsciScintilla.MarkerSymbol.Underline
            ),
            qt.QsciScintillaBase.SC_MARK_BOOKMARK: (
                qt.QsciScintilla.MarkerSymbol.Bookmark
            ),
        }
        compat_table_missing: Dict[int, qt.QsciScintilla.MarkerSymbol] = {
            qt.QsciScintillaBase.SC_MARK_PIXMAP: (
                qt.QsciScintilla.MarkerSymbol.ThreeRightArrows
            ),
            qt.QsciScintillaBase.SC_MARK_AVAILABLE: (
                qt.QsciScintilla.MarkerSymbol.ThreeRightArrows
            ),
            qt.QsciScintillaBase.SC_MARK_RGBAIMAGE: (
                qt.QsciScintilla.MarkerSymbol.ThreeRightArrows
            ),
            qt.QsciScintillaBase.SC_MARK_CHARACTER: (
                qt.QsciScintilla.MarkerSymbol.ThreeRightArrows
            ),
        }
        try:
            return super().markerDefine(compat_table[sym], num)
        except:
            purefunctions.printc(
                f"WARNING: markerDefine({sym}) cannot be displayed in PyQt6!",
                color="warning",
            )
            return super().markerDefine(compat_table_missing[sym], num)

    def markerDeleteAll(self, markerNumber: Optional[int] = None) -> None:
        """PyQt6 compatibility."""
        if markerNumber is None:
            markerNumber = -1
        super().markerDeleteAll(markerNumber)
        return

    def indicatorDefine(
        self,
        style: Union[int, qt.QsciScintilla.IndicatorStyle],
        indicatorNumber: Optional[int] = -1,
    ) -> int:
        """
        PyQt6 compatibility:
        The first argument should be a 'qt.QsciScintilla.IndicatorStyle' in PyQt6, not an integer.
        """
        if not isinstance(style, int):
            return super().indicatorDefine(style, indicatorNumber)
        if indicatorNumber is None:
            indicatorNumber = -1

        compat_table: Dict[int, qt.QsciScintilla.IndicatorStyle] = {
            qt.QsciScintillaBase.INDIC_PLAIN: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC_SQUIGGLE: (
                qt.QsciScintilla.IndicatorStyle.SquiggleIndicator
            ),
            qt.QsciScintillaBase.INDIC_TT: (
                qt.QsciScintilla.IndicatorStyle.TTIndicator
            ),
            qt.QsciScintillaBase.INDIC_DIAGONAL: (
                qt.QsciScintilla.IndicatorStyle.DiagonalIndicator
            ),
            qt.QsciScintillaBase.INDIC_STRIKE: (
                qt.QsciScintilla.IndicatorStyle.StrikeIndicator
            ),
            qt.QsciScintillaBase.INDIC_HIDDEN: (
                qt.QsciScintilla.IndicatorStyle.HiddenIndicator
            ),
            qt.QsciScintillaBase.INDIC_BOX: (
                qt.QsciScintilla.IndicatorStyle.BoxIndicator
            ),
            qt.QsciScintillaBase.INDIC_ROUNDBOX: (
                qt.QsciScintilla.IndicatorStyle.RoundBoxIndicator
            ),
            qt.QsciScintillaBase.INDIC_STRAIGHTBOX: (
                qt.QsciScintilla.IndicatorStyle.StraightBoxIndicator
            ),
            qt.QsciScintillaBase.INDIC_DASH: (
                qt.QsciScintilla.IndicatorStyle.DashesIndicator
            ),
            qt.QsciScintillaBase.INDIC_DOTS: (
                qt.QsciScintilla.IndicatorStyle.DotsIndicator
            ),
            qt.QsciScintillaBase.INDIC_SQUIGGLELOW: (
                qt.QsciScintilla.IndicatorStyle.SquiggleLowIndicator
            ),
            qt.QsciScintillaBase.INDIC_DOTBOX: (
                qt.QsciScintilla.IndicatorStyle.DotBoxIndicator
            ),
            qt.QsciScintillaBase.INDIC_SQUIGGLEPIXMAP: (
                qt.QsciScintilla.IndicatorStyle.SquigglePixmapIndicator
            ),
            qt.QsciScintillaBase.INDIC_COMPOSITIONTHICK: (
                qt.QsciScintilla.IndicatorStyle.ThickCompositionIndicator
            ),
            qt.QsciScintillaBase.INDIC_COMPOSITIONTHIN: (
                qt.QsciScintilla.IndicatorStyle.ThinCompositionIndicator
            ),
            qt.QsciScintillaBase.INDIC_FULLBOX: (
                qt.QsciScintilla.IndicatorStyle.FullBoxIndicator
            ),
            qt.QsciScintillaBase.INDIC_TEXTFORE: (
                qt.QsciScintilla.IndicatorStyle.TextColorIndicator
            ),
        }

        compat_table_missing: Dict[int, qt.QsciScintilla.IndicatorStyle] = {
            qt.QsciScintillaBase.INDIC_POINT: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC_POINTCHARACTER: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC_IME: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC_IME_MAX: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC_CONTAINER: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC_MAX: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC0_MASK: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC1_MASK: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDIC2_MASK: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.INDICS_MASK: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.SC_INDICVALUEBIT: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.SC_INDICVALUEMASK: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
            qt.QsciScintillaBase.SC_INDICFLAG_VALUEBEFORE: (
                qt.QsciScintilla.IndicatorStyle.PlainIndicator
            ),
        }
        try:
            return super().indicatorDefine(compat_table[style], indicatorNumber)
        except:
            purefunctions.printc(
                f"WARNING: indicatorDefine({style}) cannot be displayed in PyQt6!",
                color="warning",
            )
            return super().indicatorDefine(
                compat_table_missing[style], indicatorNumber
            )

    def setParent(self, parent) -> None:
        """"""
        qt.QsciScintilla.setParent(self, parent)
        gui.templates.baseobject.BaseObject.setParent(self, parent)
        return

    def set_style(self) -> None:
        # Disable context menu for scrollbars
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        # Set the horizontal scrollbar to adjust to contents
        self.setScrollWidthTracking(True)
        # Update style
        self.set_theme(data.theme)
        return

    def hide_all_margins(self):
        for i in range(6):
            self.setMarginWidth(i, 0)

    def make_links_clickable(self):
        style_number = 19
        text = bytearray(self.text().lower(), "utf-8").decode("utf-8")
        token_list = []
        start = 0
        for i, c in enumerate(text):
            if c in " \n\r":
                token = "".join(token_list).strip()
                if token.startswith("http://") or token.startswith("https://"):
                    self.setIndicatorForegroundColor(
                        data.theme["indication"]["symbol"], style_number
                    )
                    self.SendScintilla(
                        qt.QsciScintillaBase.SCI_STYLESETHOTSPOT,
                        style_number,
                        True,
                    )
                    self.SendScintilla(
                        qt.QsciScintillaBase.SCI_SETHOTSPOTACTIVEFORE,
                        True,
                        data.theme["indication"]["symbol"],
                    )
                    self.SendScintilla(
                        qt.QsciScintillaBase.SCI_SETHOTSPOTACTIVEUNDERLINE,
                        True,
                    )
                    self.SendScintilla(
                        qt.QsciScintillaBase.SCI_STARTSTYLING,
                        start,
                        style_number,
                    )
                    self.SendScintilla(
                        qt.QsciScintillaBase.SCI_SETSTYLING,
                        len(token),
                        style_number,
                    )
                token_list = []
                start = i + 1

            else:
                token_list.append(c)

    def __hotspot_click(self, position, modifiers):
        pass

    def __hotspot_doubleclick(self, position, modifiers):
        pass

    def __hotspot_releaseclick(self, position, modifiers):
        line = self.SendScintilla(
            qt.QsciScintillaBase.SCI_LINEFROMPOSITION,
            position,
        )
        text = self.text(line)
        links = re.findall(r"(http[s*]?://[^\s]+)", text)
        if len(links) > 0:
            functions.open_url(links[0])
        # QScintilla specific tests

    #        line, index = self.lineIndexFromPosition(position)
    #        word = self.wordAtLineIndex(line, index)
    #        print(word)

    def set_theme(self, theme):
        self.setFoldMarginColors(
            qt.QColor(theme["fold_margin"]["foreground"]),
            qt.QColor(theme["fold_margin"]["background"]),
        )
        self.setSelectionForegroundColor(
            qt.QColor(theme["fonts"]["selection"]["color"])
        )
        self.setSelectionBackgroundColor(
            qt.QColor(theme["fonts"]["selection"]["background"])
        )
        self.setMarginsForegroundColor(
            qt.QColor(theme["line_margin"]["foreground"])
        )
        self.setMarginsBackgroundColor(
            qt.QColor(theme["line_margin"]["background"])
        )
        self.SendScintilla(
            qt.QsciScintillaBase.SCI_STYLESETBACK,
            qt.QsciScintillaBase.STYLE_DEFAULT,
            qt.QColor(theme["fonts"]["default"]["background"]),
        )
        self.SendScintilla(
            qt.QsciScintillaBase.SCI_STYLESETBACK,
            qt.QsciScintillaBase.STYLE_LINENUMBER,
            qt.QColor(theme["line_margin"]["background"]),
        )
        self.SendScintilla(
            qt.QsciScintillaBase.SCI_SETCARETFORE, qt.QColor(theme["cursor"])
        )
        self.setCaretLineBackgroundColor(
            qt.QColor(theme["cursor_line_overlay"])
        )
        self.setStyleSheet(
            """
            QObject {{
                background: {5};
            }}
            
            QFrame {{
                background-color: transparent;
                border: 0px;
            }}
        
            BaseEditor {{
                border: 0px;
                background-color: {0};
                padding: 0px;
                spacing: 0px;
                margin: 0px;
            }}
            QListView {{
                background-color: {0};
                color: {1};
            }}
            QListView::item:selected {{
                background-color: {0};
                color: {1};
            }}
            QListView::item:selected {{
                background-color: {2};
                color: {1};
            }}
            {3}
            {4}
            {5}
            """.format(
                theme["editor_background"],
                theme["fonts"]["default"]["color"],
                theme["indication"]["background_selection"],
                gui.stylesheets.scrollbar.get_horizontal(),
                gui.stylesheets.scrollbar.get_vertical(),
                data.theme["scroll_bar"]["background"],
                data.theme["scroll_bar"]["background"],
                gui.stylesheets.tooltip.get_default(),
            )
        )
