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

import common.utils
import lang.board.basic
import lang.gbs_builtins

class GbboBoardFormat(lang.board.basic.BoardFormat):
  "Binary board format."
  def __init__(self, nbytes=4):
    self._nbytes = nbytes

  def pack(self, n):
    bs = []
    for i in range(self._nbytes):
      bs.append(chr(n & 0xff))
      n = n >> 8
    return ''.join(bs)

  def unpack(self, s):
    n = 0
    s = common.utils.seq_reversed(s)
    for c in s:
      n = (n << 8) | ord(c)
    return n

  def dump(self, board, f):
    w, h = board.size
    f.write(self.pack(w))
    f.write(self.pack(h))
    y, x = board.head
    f.write(self.pack(x))
    f.write(self.pack(y))
    for y in range(h):
      for x in range(w):
        for coli in range(lang.gbs_builtins.NUM_COLORS):
          cant = board.cells[y][x].num_stones(coli) 
          f.write(self.pack(cant))

  def load(self, board, f):
    s = f.read()
    nb = self._nbytes

    width = self.unpack(s[0:nb])
    height = self.unpack(s[nb:2 * nb])
    board.resize(width, height)

    head_x = self.unpack(s[2 * nb:3 * nb])
    head_y = self.unpack(s[3 * nb:4 * nb])
    board.goto(head_x, head_y)
    
    d = 4 * nb
    for y in range(height):
      for x in range(width):
        for coli in range(lang.gbs_builtins.NUM_COLORS):
          board[x, y][coli] = self.unpack(s[d:d + nb])
          d += nb

