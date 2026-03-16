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

# # """
# """
# from __future__ import annotations
# from typing import *
# import sys, os, inspect, argparse
# import qt
# sys.path.append('..')
# import data
# q = "'"
# dq = '"'
# #* 'icons_directory'
# # Define the 'to_exe_directory' where this file resides, as well as the 'icons_
# # directory' where the icons reside.
# to_exe_directory = os.path.realpath(
#     os.path.dirname(
#         os.path.realpath(
#             inspect.getfile(
#                 inspect.currentframe()
#             )
#         )
#     )
# ).replace('\\', '/')
# icons_directory = os.path.join(
#     os.path.dirname(to_exe_directory),
#     'resources/icons',
# ).replace('\\', '/')
# #* 'foldernames_to_process'
# # List all the foldernames within 'resources/icons/' that should be processed by
# # this file. For each of them, list the requested suffixes.
# folders_to_process = data.icon_folders_to_process
# files_to_process = data.icon_files_to_process
# #* 'suffixes'
# # List all potential suffixes for a .png file. For each suffix, define in which
# # 'round' it should be applied. A suffix in a higher round gets applied later,
# # so it can be on top of those from previous rounds.
# # Also, define those it *can* be put on top of. This way you can allow certain
# # mixes.
# all_suffixes = data.icon_suffixes
# #* Overlay images
# # Declare globals for the overlay images. These globals get their values as soon
# # as the script runs.
# painter:Optional[qt.QPainter] = None
# overlay_img_dict:Dict[str, qt.QImage] = {}
# #^                                  FUNCTIONS                                 ^#
# #% ========================================================================== %#
# #% Functions to process an icon.                                              %#
# #%                                                                            %#
# def pixmap_to_grayscale(pixmap_or_file:Union[qt.QPixmap, str]) -> qt.QPixmap:
#     '''
#     '''
#     image = qt.QImage(pixmap_or_file)
#     for i in range(image.width()):
#         for j in range(image.height()):
#             point = qt.create_qpoint(i, j)
#             color = qt.QColor(image.pixelColor(point))
#             if color.alpha() > 100:
#                 color.setHsl(color.hue(), 10, color.lightness())
#                 image.setPixelColor(point, color)
#     return qt.QPixmap.fromImage(image)
# def pixmap_to_overlayed_pixmap(pixmap_or_file:Union[qt.QPixmap, str],
#                                suffix:str,
#                                ) -> Optional[qt.QPixmap]:
#     '''
#     '''
#     overlay_img:qt.QImage = overlay_img_dict[suffix]
#     scaled_overlay_img:Optional[qt.QImage] = None
#     assert not overlay_img_dict[suffix].isNull()
#     image = qt.QImage(pixmap_or_file)
#     if overlay_img.size().width() != image.size().width() or \
#             overlay_img.size().height() != image.size().height():
#         # scaled_overlay_img = overlay_img.scaled(image.size())
#         return None
#     painter.begin(image)
#     if scaled_overlay_img is not None:
#         painter.drawImage(0, 0, scaled_overlay_img)
#     else:
#         painter.drawImage(0, 0, overlay_img)
#     painter.end()
#     return qt.QPixmap.fromImage(image)
# def __patterns_from_suffixes(suffix_iterable:Iterable[str]) -> Tuple[str, ...]:
#     '''
#     Given an iterable of suffixes like ('dis', 'warn', 'err'), this function re-
#     turns a tuple like:
#     result = (
#         '_dis_', '_dis.png',
#         '_warn_', '_warn.png',
#         '_err_', '_err.png',
#     )
#     '''
#     _temp_1 = [f'_{s}_' for s in suffix_iterable]
#     _temp_2 = [f'_{s}.png' for s in suffix_iterable]
#     return tuple(_temp_1 + _temp_2)
# #^                                    CLEAN                                   ^#
# #% ========================================================================== %#
# #% Clean folders from processed icons.                                        %#
# #%                                                                            %#
# def clean_folder(foldername:str) -> None:
#     '''
#     Clean the given folder from all processed icons.
#     '''
#     folder_abspath = os.path.join(
#         icons_directory,
#         foldername,
#     ).replace('\\', '/')
#     assert os.path.isdir(folder_abspath)
#     print(f'\nClean folder: {q}{foldername}{q}')
#     patterns_to_delete = __patterns_from_suffixes(all_suffixes.keys())
#     for root, dirs, files in os.walk(folder_abspath):
#         for filename in files:
#             if not filename.endswith('.png'):
#                 continue
#             if not any(s in filename for s in patterns_to_delete):
#                 continue
#             filepath = os.path.join(root, filename).replace('\\', '/')
#             print(f'    delete: {q}{filename}{q}')
#             os.remove(filepath)
#             continue
#         continue
#     return
# #^                                   PROCESS                                  ^#
# #% ========================================================================== %#
# #% Add processed icons to folders.                                            %#
# #%                                                                            %#
# def __apply_suffix_on_file(filename:str,
#                            filepath:str,
#                            suffix:str,
#                            ) -> None:
#     '''
#     Apply the given suffix on the file. Save the duplicate.
#     :param filename:    Name of file.
#     :param filepath:    Absolute path to file.
#     :param suffix:      Suffix to apply, eg. 'hid', 'dis', ...
#     WARNING:
#     At this point, the filename should already have been analyzed to see if it
#     must be skipped!
#     '''
#     mod_filename = filename.replace('.png', f'_{suffix}.png')
#     mod_filepath = filepath.replace('.png', f'_{suffix}.png')
#     if os.path.isfile(mod_filepath):
#         filetime = os.path.getmtime(filepath)
#         mod_filetime = os.path.getmtime(mod_filepath)
#         # Modified file is newer => OK
#         if mod_filetime > filetime:
#             print(f'        already done: {q}{filename}{q} => {q}{mod_filename}{q}')
#             return
#         # Modified file is older => Not OK
#         # Delete the modified file and continue to replace it.
#         os.remove(mod_filepath)
#     if suffix == 'dis':
#         pixmap = pixmap_to_grayscale(filepath)
#     else:
#         pixmap = pixmap_to_overlayed_pixmap(filepath, suffix)
#     if pixmap is not None:
#         print(f'        processing: {q}{filename}{q} => {q}{mod_filename}')
#         pixmap.save(mod_filepath)
#     return
# def __process_folder_for_suffix(foldername:str,
#                                 suffix:str,
#                                 suffixes_to_skip:Iterable[str],
#                                 ) -> None:
#     '''
#     Duplicate all icons in the given folder to apply the requested suffix. Icons
#     that already have a suffix from the 'suffixes_to_skip' listing are ignored.
#     :param foldername:          Name of folder to process, must be directly in
#                                 'resources/icons/'.
#     :param suffix:              The suffix to be applied, eg. 'dis', 'err', ...
#     :param suffixes_to_skip:    Ignore icons that already have one of these
#                                 suffixes.
#     '''
#     #* Check and process inputs
#     patterns_to_skip = __patterns_from_suffixes(suffixes_to_skip)
#     folder_abspath = os.path.join(
#         icons_directory,
#         foldername,
#     ).replace('\\', '/')
#     assert os.path.isdir(folder_abspath)
#     #* Print something
#     print(f'    Create {q}{suffix}{q} icons for {q}{foldername}{q}:')
#     #* Start procedure
#     for root, dirs, files in os.walk(folder_abspath):
#         for filename in files:
#             # Check if file should be processed
#             if not filename.endswith('.png'):
#                 continue
#             if any(s in filename for s in patterns_to_skip):
#                 continue
#             filepath = os.path.join(root, filename).replace('\\', '/')
#             # Apply suffix on file
#             __apply_suffix_on_file(
#                 filename = filename,
#                 filepath = filepath,
#                 suffix   = suffix,
#             )
#             continue
#         continue
#     return
# def process_file(file_relpath:str) -> None:
#     '''
#     Process an individual file.
#     '''
#     #* Print something toplevel
#     print(f'\nProcess file {q}{file_relpath}{q}:')
#     #* Process rounds
#     file_list = [file_relpath, ]
#     for r in (1, 2, 3, 4):
#         r_suffixes = [
#             s for s in all_suffixes.keys()
#             if (all_suffixes[s]['round'] == r) and
#                (s in files_to_process[file_relpath])
#         ]
#         print(f'ROUND {r}, SUFFIXES = {r_suffixes}')
#         for s in r_suffixes:
#             # Define for the given suffix which ones are okay to be underneath this
#             # suffix (so this suffix can be 'on top of' them).
#             suffixes_to_allow = all_suffixes[s]['on_top_of']
#             # Now derive from this the suffixes that are not okay to be underneath
#             # the given suffix.
#             suffixes_to_skip = [
#                 _s_ for _s_ in all_suffixes.keys() if _s_ not in suffixes_to_allow
#             ]
#             patterns_to_skip = __patterns_from_suffixes(suffixes_to_skip)
#             temp = []
#             for f in file_list:
#                 filename = f.split('/')[-1]
#                 filepath = os.path.join(icons_directory, f).replace('\\', '/')
#                 assert os.path.isfile(filepath)
#                 if any(sf in filename for sf in patterns_to_skip):
#                     continue
#                 __apply_suffix_on_file(
#                     filename = filename,
#                     filepath = filepath,
#                     suffix = s,
#                 )
#                 mod_f = f.replace('.png', f'_{s}.png')
#                 temp.append(mod_f)
#                 continue
#             file_list += temp
#             continue
#         continue
#     return
# def process_folder(foldername:str) -> None:
#     '''
#     Process the given folder.
#     '''
#     #* Check and process inputs
#     folder_abspath = os.path.join(
#         icons_directory,
#         foldername,
#     ).replace('\\', '/')
#     assert os.path.isdir(folder_abspath)
#     #* Print something toplevel
#     print(f'\nProcess folder {q}{foldername}{q}:')
#     #* Process rounds
#     for r in (1, 2, 3, 4):
#         r_suffixes = [
#             s for s in all_suffixes.keys()
#             if (all_suffixes[s]['round'] == r) and
#                (s in folders_to_process[foldername])
#         ]
#         for s in r_suffixes:
#             # Define for the given suffix which ones are okay to be underneath this
#             # suffix (so this suffix can be 'on top of' them).
#             suffixes_to_allow = all_suffixes[s]['on_top_of']
#             # Now derive from this the suffixes that are not okay to be underneath
#             # the given suffix.
#             suffixes_to_skip = [
#                 _s_ for _s_ in all_suffixes.keys() if _s_ not in suffixes_to_allow
#             ]
#             __process_folder_for_suffix(
#                 foldername       = foldername,
#                 suffix           = s,
#                 suffixes_to_skip = suffixes_to_skip,
#             )
#             continue
#         continue
#     return
# #^                                    MAIN                                    ^#
# #% ========================================================================== %#
# #% Start procedure.                                                           %#
# #%                                                                            %#
# if __name__ == '__main__':
#     #* Check folder existences
#     for _foldername in folders_to_process.keys():
#         folderpath = os.path.join(
#             icons_directory,
#             _foldername,
#         ).replace('\\', '/')
#         assert os.path.isdir(folderpath), str(
#             f'folder {q}{_foldername}{q} not found!'
#         )
#         continue
#     #* Create overlay images
#     app = qt.QApplication(sys.argv)
#     painter = qt.QPainter()
#     for _s in all_suffixes.keys():
#         if _s == 'dis':
#             continue
#         overlay_path = os.path.join(
#             icons_directory,
#             f'overlay/{_s}_overlay.png',
#         ).replace('\\', '/')
#         assert os.path.isfile(overlay_path)
#         overlay_img_dict[_s] = qt.QImage(overlay_path)
#         assert not overlay_img_dict[_s].isNull()
#     #* Parse arguments
#     parser = argparse.ArgumentParser(
#         description = 'Process Embeetle icons',
#         add_help    = True,
#     )
#     parser.add_argument(
#         '-c',
#         '--clean',
#         action   = 'store_true',
#         default  = False,
#         required = False,
#         help     = 'Clean all relevant directories',
#     )
#     args = parser.parse_args()
#     #$ Clean
#     if args.clean:
#         print('\nStart clean operation\n')
#         for _foldername in folders_to_process.keys():
#             clean_folder(_foldername)
#             continue
#         print('\nClean operation completed\n')
#         sys.exit()
#     #$ Process
#     print('\nStart icon operation\n')
#     for _foldername in folders_to_process.keys():
#         process_folder(_foldername)
#         continue
#     for _file_relpath in files_to_process.keys():
#         process_file(_file_relpath)
#         continue
#     print('\nIcon operation completed\n')
#     sys.exit()
