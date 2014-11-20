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

import re

import common.i18n as i18n
import lang.gbs_builtins
import lang.board.basic

class TexBoardFormat(lang.board.basic.BoardFormat):
  "LaTeX board format."

  def dump(self, board, f, **kwargs):
    w, h = board.size
    f.write('\\documentclass{article}\n')
    f.write('\\usepackage{Gobstones}\n\n')
    f.write('\\GbstnTamanho{%i}{%i}\n' % (w, h))
    f.write('\\begin{document}\n')
    f.write('\\begin{GbstnTablero}\n')
    for x in range(w):
      for y in range(h):
        for coli in range(4):
          cant = board.cells[y][x].num_stones(coli) 
          if cant == 0: continue
          col = lang.gbs_builtins.Color(coli).name()
          f.write('  \\Gbstn%s{%i}{%i}{%i}\n' % (col, x, y, cant))
    y, x = board.head
    f.write('  \\GbstnCabezal{%i}{%i}\n' % (x, y))
    f.write('\\end{GbstnTablero}\n')
    f.write('\\end{document}\n')

  def load(self, board, f):
    contents = f.read()
    sizes = list(re.findall('\\GbstnTamanho{([0-9]+)}{([0-9]+)}', contents))
    if len(sizes) != 1:
      raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed tex board'))
    width, height = board.size = int(sizes[0][0]), int(sizes[0][1])
    board.head = (0, 0)
    board._clear_board()
    for coli in range(4):
      col = lang.gbs_builtins.Color(coli).name()
      col_stones = re.findall('\\Gbstn' + col + '{([0-9]+)}{([0-9]+)}{([0-9]+)}' % (), contents)
      for x, y, count in col_stones:
        x, y, count = int(x), int(y), int(count)
        if x >= width or y >= height:
          raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed tex board'))
        board.cells[y][x].set_num_stones(coli, count)
    headers = list(re.findall('\\GbstnCabezal{([0-9]+)}{([0-9]+)}', contents))
    if len(headers) > 1:
      raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed tex board'))
    elif len(headers) == 1:
      x, y = int(headers[0][0]), int(headers[0][1])
      if x >= width or y >= height:
        raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed tex board'))

      board.head = y, x
    board.clear_changelog()

