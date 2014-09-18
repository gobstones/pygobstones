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

import lang.board.basic

try:
  import PIL.Image
  available = True
except ImportError:
  available = False

class PngBoardFormat(lang.board.basic.BoardFormat):
  "Export to RGB image."

  def dump(self, board, f, **kwargs):
    w, h = board.size
    img = PIL.Image.new('RGB', (w, h), (255, 255, 255))
    for x in range(w):
      for y in range(h):
        cell = {}
        for coli in range(4):
          cant = board.cells[y][x].num_stones(coli) 
          if cant == 0: continue
          col = lang.gbs_builtins.Color(coli).name()
          cell[col] = cant
        ref = max(cell.get('Negro', 0), 1)

        def component(x):
          return min(int(float(cell.get(x, 0)) * 255 / ref), 255)

        img.putpixel((x, y), (component('Rojo'), component('Verde'), component('Azul')))
    img.save(f, 'png')

