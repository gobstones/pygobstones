#
# Copyright (C) 2011-2015 Pablo Barenbaum <foones@gmail.com>,
#                         Ary Pablo Batista <arypbatista@gmail.com>
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
import json

import pygobstoneslang.common.utils as utils
import pygobstoneslang.common.i18n as i18n
import pygobstoneslang.lang.gbs_builtins as gbs_builtins
import basic

def is_numeric(x):
  return re.match('^[0-9]+$', x)

class JsonBoardFormat(basic.BoardFormat):
  "Simple human-friendly board format."

  def dump(self, board, f=None, style='verbose', **kwargs):
    if style == 'verbose':
      output = self.dump_with_translator(board, self.verbose_translator)
    elif style == 'compact':
      output = self.dump_with_translator(board, self.compact_translator)
    else:
      assert False

    if not f is None:
        f.write(output)
    return json.dumps(output)

  def dump_to_dict(self, board, style='verbose', **kwargs):
    if style == 'verbose':
      output = self.dump_with_translator(board, self.verbose_translator)
    elif style == 'compact':
      output = self.dump_with_translator(board, self.compact_translator)
    else:
      assert False
    return output

  def verbose_translator(self, s):
    return s

  def compact_translator(self, s):
    _dict = {
      'cell': 'o',
      'size': 's',
      'head': 'x',
    }
    if s in _dict:
      return _dict[s]
    else:
      return s[0]

  def dump_with_translator(self, board, translate):
    w, h = board.size
    output = {"size" : board.size}
    cells = {}
    for x in range(w):
      for y in range(h):
        cell = {}
        for coli in range(4):
          cant = board.cells[y][x].num_stones(coli)
          if cant == 0: continue
          col = gbs_builtins.Color(coli).name()
          cell.update({col : cant})
        if cell == {}: continue

        if not x in cells.keys():
            cells[x] = {}
        cells[x][y] = cell
    output.update({"head": board.head})
    output.update({"cells": cells})
    return output

  def load(self, board, f):
      raise Exception("Not implemented")
