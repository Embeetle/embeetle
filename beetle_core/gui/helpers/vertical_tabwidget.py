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

# from __future__ import annotations
# from typing import *
# import qt, purefunctions, iconfunctions
# import gui.stylesheets.tabwidget as _tabwidget_stylesheet_
# # Source:
# # https://stackoverflow.com/questions/50578661/how-to-implement-vertical-tabs-in-qt
# import data
# class VTabBar(qt.QTabBar):
#     def __init__(self, *args, **kwargs) -> None:
#         '''
#         '''
#         super().__init__(*args, **kwargs)
#         self.setContextMenuPolicy(qt.Qt.ContextMenuPolicy.CustomContextMenu)
#         return
#     def tabSizeHint(self, index:int) -> qt.QSize:
#         '''
#         '''
#         s = super().tabSizeHint(index)
#         s.transpose()
#         return s
#     def paintEvent(self, event:qt.QPaintEvent) -> None:
#         '''
#         '''
#         painter:qt.QStylePainter = qt.QStylePainter(self)
#         opt:qt.QStyleOptionTab = qt.QStyleOptionTab()
#         for i in range(self.count()):
#             self.initStyleOption(opt, i)
#             painter.drawControl(qt.QStyle.ControlElement.CE_TabBarTabShape, opt)
#             painter.save()
#             s:qt.QSize = opt.rect.size()
#             s.transpose()
#             r:qt.QRect = qt.QRect(qt.QPoint(), s)
#             r.moveCenter(opt.rect.center())
#             opt.rect = r
#             c:qt.QPoint = self.tabRect(i).center()
#             painter.translate(c)
#             painter.rotate(90)
#             painter.translate(-c)
#             painter.drawControl(qt.QStyle.ControlElement.CE_TabBarTabLabel, opt)
#             painter.restore()
#         return
# class VTabWidget(qt.QTabWidget):
#     rightclick_sig           = qt.pyqtSignal(str)
#     tabselection_changed_sig = qt.pyqtSignal(str)
#     def __init__(self, parent:qt.QWidget=None) -> None:
#         '''
#         '''
#         super().__init__(parent)
#         vtabbar = VTabBar()
#         self.setTabBar(vtabbar)
#         self.setTabPosition(qt.QTabWidget.TabPosition.West)
#         vtabbar.customContextMenuRequested.connect(self.__show_context_menu) # type: ignore
#         self.currentChanged.connect(self.__tabselection_changed) # type: ignore
#         self.setContentsMargins(0, 0, 0, 0)
#         self.setStyleSheet(
#             _tabwidget_stylesheet_.get_dynamic_style_vertical()
#         )
#         self.__iconstruct:Dict = {}
#         return
#     def __show_context_menu(self, point:qt.QPoint) -> None:
#         '''
#         Emit the 'rightclick_sig' with the tabname of the tab upon which the user clicked with the
#         right mouse button.
#         '''
#         if point.isNull():
#             return
#         tabindex = self.tabBar().tabAt(point)
#         tabname = self.tabBar().tabWhatsThis(tabindex)
#         self.rightclick_sig.emit(tabname)
#         return
#     def __tabselection_changed(self, tabindex:int) -> None:
#         '''
#         Emit the 'tabselection_changed_sig' with the tabname of the selected tab.
#         '''
#         tabname = self.tabBar().tabWhatsThis(tabindex)
#         self.tabselection_changed_sig.emit(tabname)
#         return
#     def get_current_tabname(self) -> str:
#         '''
#         Get the name of the currently visible tab.
#         '''
#         tabindex = self.currentIndex()
#         tabname = self.tabBar().tabWhatsThis(tabindex)
#         return tabname
#     def focus_tab(self, name:str) -> None:
#         '''
#         Focus the given tab.
#         '''
#         tabindex = self.__get_tabindex(name)
#         if tabindex == -1:
#             return
#         self.setCurrentIndex(tabindex)
#         return
#     def delete_tab(self, name:str) -> None:
#         '''
#         Delete the given tab.
#         '''
#         tabindex = self.__get_tabindex(name)
#         if tabindex == -1:
#             return
#         self.removeTab(tabindex)
#         return
#     def update_icon_size(self) -> None:
#         '''
#         '''
#         try:
#             size = max(
#                 data.get_toplevel_menu_pixelsize(),
#                 data.get_general_icon_pixelsize(),
#                 data.get_custom_tab_pixelsize(),
#             )
#             self.setIconSize(qt.create_qsize(size, size))
#         except:
#             # Sometimes this action causes an error:
#             # AttributeError:
#             #     'NoneType' object has no attribute 'setIconSize'
#             pass
#         self.update()
#         return
#     def addTab(self, # type: ignore
#                name:Optional[str]=None,
#                tooltip:Optional[str]=None,
#                page:Optional[qt.QWidget]=None,
#                iconpath:Optional[str]=None,
#                grayscale:Optional[bool]=None,
#                label:Optional[str]=None,
#                *args,
#                ) -> None:
#         '''
#         Add a tab to this widget.
#         :param name:        Name to recognize the tab later.
#         :param tooltip:     Tooltip when hovering with the mouse over the tab.
#         :param page:        The widget to be shown in the tab.
#         :param iconpath:    Iconpath for the tab.
#         :param grayscale:   True if icon in grayscale.
#         :param label:       Text to be shown as a tab-label.
#         '''
#         new_index = self.count()
#         self.__iconstruct[name] = {
#             'iconpath'  : iconpath,
#             'grayscale' : grayscale,
#         }
#         super().addTab(
#             page,
#             iconfunctions.get_qicon(
#                 iconpath.replace('.png', '(dis).png') if grayscale else iconpath
#             ),
#             label,
#         )
#         self.setTabToolTip(new_index, tooltip)
#         self.setTabWhatsThis(new_index, name)
#         self.update_icon_size()
#         return
#     def insertTab(self, # type: ignore
#                   name:Optional[str]=None,
#                   tooltip:Optional[str]=None,
#                   index:Optional[int]=None,
#                   page:Optional[qt.QWidget]=None,
#                   iconpath:Optional[str]=None,
#                   grayscale:Optional[bool]=None,
#                   label:Optional[str]=None,
#                   *args,
#                   ) -> None:
#         '''
#         Insert a tab in this widget.
#         :param name:        Name to recognize the tab later.
#         :param tooltip:     Tooltip when hovering with the mouse over the tab.
#         :param index:       Index where to insert this tab.
#         :param page:        The widget to be shown in the tab.
#         :param iconpath:    Iconpath for the tab.
#         :param grayscale:   True if icon in grayscale.
#         :param label:       Text to be shown as a tab-label.
#         '''
#         self.__iconstruct[name] = {
#             'iconpath'  : iconpath,
#             'grayscale' : grayscale,
#         }
#         super().insertTab(
#             index,
#             page,
#             iconfunctions.get_qicon(
#                 iconpath.replace('.png', '(dis).png') if grayscale else iconpath
#             ),
#             label,
#         )
#         self.setTabToolTip(index, tooltip)
#         self.setTabWhatsThis(index, name)
#         self.update_icon_size()
#         return
#     def renameTab(self,
#                   oldname:str,
#                   newname:str,
#                   tooltip:str,
#                   label:str,
#                   ) -> None:
#         '''
#         :param oldname:     Old name.
#         :param newname:     Name to recognize the tab later.
#         :param label:       Text to be shown as a tab-label.
#         '''
#         # Obtain the index from the requested tab.
#         index = self.__get_tabindex(oldname)
#         # Apply the new name on this tab, as well as the label to be shown and
#         # the tooltip.
#         self.setTabWhatsThis(index, newname)
#         self.setTabText(index, label)
#         self.setTabToolTip(index, tooltip)
#         # Apply the change also in the stored icon struct.
#         assert oldname in self.__iconstruct
#         assert newname not in self.__iconstruct
#         self.__iconstruct[newname] = {
#             'iconpath'  : self.__iconstruct[oldname]['iconpath'],
#             'grayscale' : self.__iconstruct[oldname]['grayscale'],
#         }
#         del self.__iconstruct[oldname]
#         # Update and quit.
#         self.update()
#         return
#     def modify_icon_grayscale(self,
#                               name:str,
#                               grayscale:bool,
#                               ) -> None:
#         '''
#         :param name:      Tabname.
#         :param grayscale: True if icon in grayscale.
#         :param grayscale: True if icon in grayscale.
#         '''
#         assert name in self.__iconstruct.keys()
#         # Nothing changed
#         if self.__iconstruct[name]['grayscale'] == grayscale:
#             return
#         # Grayscale changed
#         self.__set_icon(
#             name      = name,
#             iconpath  = self.__iconstruct[name]['iconpath'],
#             grayscale = grayscale,
#         )
#         return
#     def modify_icon(self,
#                     name:str,
#                     iconpath:str,
#                     grayscale:Optional[bool]=None,
#                     ) -> None:
#         '''
#         :param name:      Tabname.
#         :param iconpath:  Iconpath for the tab.
#         :param grayscale: True if icon in grayscale. False otherwise. None if it should remain
#                           as-is.
#         '''
#         assert name in self.__iconstruct.keys()
#         # Nothing changed
#         if (self.__iconstruct[name]['iconpath'] == iconpath) and \
#                 (self.__iconstruct[name]['grayscale'] == grayscale):
#             return
#         # Something changed
#         if grayscale is None:
#             grayscale = self.__iconstruct[name]['grayscale']
#         self.__set_icon(
#             name      = name,
#             iconpath  = iconpath,
#             grayscale = grayscale,
#         )
#         return
#     def __set_icon(self,
#                    name:str,
#                    iconpath:str,
#                    grayscale:bool,
#                    ) -> None:
#         '''
#         Simply apply the given icon and grayscale on the tab with the given name. This method
#         doesn't check anything. Only for internal use.
#         '''
#         assert name in self.__iconstruct.keys()
#         self.__iconstruct[name]['iconpath'] = iconpath
#         self.__iconstruct[name]['grayscale'] = grayscale
#         tabindex = self.__get_tabindex(name)
#         if tabindex != -1:
#             self.setTabIcon(
#                 tabindex,
#                 iconfunctions.get_qicon(
#                     iconpath.replace('.png', '(dis).png') if grayscale else iconpath
#                 ),
#             )
#             self.update_icon_size()
#             return
#         purefunctions.printc(
#             f'\nERROR: VTabWidget().__set_icon(\n'
#             f'{name}\n,'
#             f'{iconpath}\n,'
#             f'{grayscale}\n'
#             f')\n'
#             f'could not find the right tab!\n',
#             color='error',
#         )
#         return
#     def __get_tabindex(self,
#                        name:str,
#                        ) -> int:
#         '''
#         Get index from tab with given name.
#         '''
#         for tabindex in range(self.count()):
#             tabname = self.tabBar().tabWhatsThis(tabindex)
#             if tabname == name:
#                 return tabindex
#         return -1
