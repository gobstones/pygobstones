#!/usr/bin/python
#
# Copyright (C) 2011, 2012 Pablo Barenbaum <foones@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import encodings.utf_8

import common.utils

if common.utils.python_major_version() < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import gui.app
import gui.judge_app
import lang.board.formats

import multiprocessing

def main():
    multiprocessing.freeze_support()

    Enable_judge = True

    if Enable_judge:
          gui_class = gui.judge_app.JudgeGUI
    else:
          gui_class = gui.app.GUI

    g = gui_class()
    g.geometry("640x480")

    if len(sys.argv) == 2:
          fn = sys.argv[1]
          if lang.board.formats.is_board_filename(fn):
            g.board_load_fn(fn)
          else:
            g.file_open_fn(fn)

    g.mainloop()

if __name__ == '__main__':

    # NOTE: do not remove the __name__ == '__main__' check.
    # It is necessary in Windows for the language not to
    # spawn infinitely many processes.

    main()

