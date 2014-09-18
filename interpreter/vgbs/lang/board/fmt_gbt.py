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

import common.utils
import common.i18n as i18n
import lang.gbs_builtins
import lang.board.basic

class GbtBoardFormat(lang.board.basic.BoardFormat):
  "Classic GBT board format inherited from the Haskell implementation."

  def __init__(self, cell_w=9, cell_h=3, max_num_len=3):
    # parameters for ascii output
    self.Cell_w = cell_w
    self.Cell_h = cell_h
    self.Max_num_len = max_num_len

  def load(self, board, f):
    head = None
    contents = list(self._parse_board(f))
    for evt in contents:
      if evt[0] == 'SIZE':
        board.size = evt[2], evt[1]
    w, h = board.size
    for evt in contents:
      if evt[0] == 'HEAD' and evt[1] is not None and evt[2] is not None:
        head = h - evt[1] - 1, evt[2]
    if head is None:
      board.randomize_header()
    else:
      board.head = head
    board._clear_board()
    for evt in contents:
      if evt[0] == 'STONE':
        description = evt[3]
        for d in self._parse_description(description):
          self._put_from_description(board.cells[h - evt[1] - 1][evt[2]], d)
    board.clear_changelog()

  def dump(self, board, f, **kwargs):
    f.write('[\n')
    rows = self.numbered_contents(board)
    i = 0
    for row in rows:
      if i == len(rows) - 1:
        sep = ''
      else:
        sep = ','
      f.write('"%s"%s\n' % (row, sep))
      i += 1
    f.write(']\n')

  def numbered_contents(self, board):
    w, h = board.size
    res = []
    out = self._board_contents(board)
    # vertical numbers
    row_id = h
    i = 0
    for row in out:
      if i % (self.Cell_h + 1) == 2:
        row_id -= 1
        res.append('  %i ' % (row_id,) + ''.join(row) + ' %i ' % (row_id,))
      else:
        res.append('    ' + ''.join(row) + '   ')
      i += 1
    # horizontal numbers
    rf = self.Cell_w // 2
    lf = self.Cell_w - rf
    horiz = ''.join([' ' * lf + '%i' % (i,) + ' ' * rf for i in range(w)])
    horiz = '    ' + horiz + '    '
    res.insert(0, horiz)
    res.append(horiz + '  ')
    return res

  def _board_contents(self, board):
    w, h = board.size
    gw = (self.Cell_w + 1) * w + 1
    gh = (self.Cell_h + 1) * h + 1
    out = [[' ' for i in range(gw)] for j in range(gh)]
    # row borders
    for x in range(w):
      for y in range(h + 1):
        for i in range((self.Cell_w + 1) * x + 1, (self.Cell_w + 1) * (x + 1)):
          out[(self.Cell_h + 1) * y][i] = '-'
    # column borders
    for x in range(w + 1):
      for y in range(h):
        for i in range((self.Cell_h + 1) * y + 1, (self.Cell_h + 1) * (y + 1)):
          out[i][(self.Cell_w + 1) * x] = '|'
    # corners
    for x in range(w + 1):
      for y in range(h + 1):
        out[(self.Cell_h + 1) * y][(self.Cell_w + 1) * x] = '+'
    # head
    y0, x0 = board.head
    y0 = h - y0 - 1
    for y in range(y0, y0 + 2):
      for i in range((self.Cell_w + 1) * x0 + 1, (self.Cell_w + 1) * (x0 + 1)):
        out[(self.Cell_h + 1) * y][i] = 'X'
    for x in range(x0, x0 + 2):
      for i in range((self.Cell_h + 1) * y0 + 1, (self.Cell_h + 1) * (y0 + 1)):
        out[i][(self.Cell_w + 1) * x] = 'X'
    # contents
    for x in range(w):
      for y in range(h):
        cell = self._cell_contents(board.cells[h - y - 1][x])
        for i in range(self.Cell_w):
          for j in range(self.Cell_h):
            out[(self.Cell_h + 1) * y + j + 1][(self.Cell_w + 1) * x + i + 1] = cell[j][i]
    return out

  def _cell_contents(self, cell):
    w, h = self.Cell_w, self.Cell_h
    out = [[' ' for i in range(w)] for j in range(h)]
    for col in range(lang.gbs_builtins.NUM_COLORS):
      count = cell.stones.get(col, 0)
      if count == 0: continue
      if col < 2: 
        y = 0
      else:
        y = self.Cell_h - 1
      if col % 2 == 0: 
        x = self.Cell_w - 2
      else:
        x = self.Max_num_len
      out[y][x] = lang.gbs_builtins.Color(col).name()[0]
      scount = str(count)
      if len(scount) > self.Max_num_len:
        msg = i18n.i18n('Cannot show board, max number allowed is %s') % (
                '9' * self.Max_num_len)
        raise lang.board.basic.BoardFormatException(msg)
      for c in common.utils.seq_reversed(scount):
        x -= 1
        out[y][x] = c
    return out

  def _parse_description(self, description):
    s = ''
    i = 0
    while i < len(description):
      s += description[i]
      if description[i] not in '0123456789':
        if s != '': yield s
        s = ''
      i += 1
    if s != '': yield s

  def _parse_board(self, f):
    width = None
    height = None
    head_row = None
    head_col = None
    # [
    l = f.readline().strip(' \t\r\n')
    if l != '[':
      raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
    def is_separator(l):
      l = re.sub('[X-]', '', l)
      return l == '+' * (width + 1)
    def head_starts_at_row(l):
      return 'X' in l
    def number_header(l):
      l = re.sub(' +', ',', l).split(',')
      if l != [str(i) for i in range(len(l))]:
        raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
      return l
    # number header
    l = f.readline().strip(' \t\r\n",')
    width = len(number_header(l))
    # first horizontal line
    l = f.readline().strip(' \t\r\n",')
    if not is_separator(l):
      raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
    row = 0
    while True:
      # read a board row, consisting of many file lines
      while True:
        l = f.readline()
        if l == '':
          raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
        l1 = l.strip(' \t\r\n",0123456789')
        if is_separator(l1):
          if head_starts_at_row(l1):
            head_row = row
          break
        elif '|' not in l1:
          number_header(l.strip(' \t\r\n"')) # check
          l = f.readline().strip(' \t\r\n')
          if l != ']':
            raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
          yield 'HEAD', head_row, head_col
          yield 'SIZE', row, width
          return
        else:
          l2 = re.sub('[^|X]', '', l1)
          if 'X' in l2:
            head_col = l2.index('X')
          line_contents = l1.replace('X', '|').split('|')
          if line_contents[0] != '' or line_contents[-1] != '':
            raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
          line_contents = line_contents[1:-1]
          col = 0
          for cell in line_contents:
            for elem in cell.split(' '):
              if elem == '': continue
              yield 'STONE', row, col, elem
            col += 1
      row += 1

  def _put_from_description(self, cell, description):
    coli = 0
    for cn in lang.gbs_builtins.COLOR_NAMES:
      if description[-1].lower() == cn[0].lower():
        count = description[:-1]
        for l in count:
          if l not in '0123456789':
            raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))
        cell.put(coli, int(count))
        return
      coli += 1
    raise lang.board.basic.BoardFormatException(i18n.i18n('Malformed board'))

