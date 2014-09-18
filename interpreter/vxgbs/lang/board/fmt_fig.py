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

import math

import common.utils
import common.i18n as i18n
import lang.gbs_builtins
import lang.board.basic

class Polyline(object):
  def __init__(self, points, fill=False, area_fill=20, fill_color=0, pen_color=0, thickness=1, depth=100):
    self.points = points + [points[0]]
    self.fill = fill
    self.fill_color = fill_color
    self.pen_color = pen_color
    self.area_fill = area_fill
    self.depth = depth
    self.thickness = 1
  def write(self, f):
    f.write('%i ' % 2) # object_code (polyline)
    f.write('%i ' % 2) # sub_type (box)
    f.write('%i ' % 0)  # line_style
    f.write('%i ' % self.thickness)  # thickness
    f.write('%i ' % self.pen_color)  # pen_color
    if self.fill:
      f.write('%i ' % self.fill_color)  # fill_color
    else:
      f.write('%i ' % 7)  # fill_color
    f.write('%i ' % self.depth) # depth
    f.write('%i ' % -1) # pen_style (not used)
    if self.fill:
      f.write('%i ' % self.area_fill) # area_fill
    else:
      f.write('%i ' % -1) # area_fill (no fill)
    f.write('%.3f ' % 0.000) # style_val
    f.write('%i ' % 0) # join_style
    f.write('%i ' % 0) # cap_style
    f.write('%i ' % -1) # radius
    f.write('%i ' % 0) # forward_arrow
    f.write('%i ' % 0) # backward_arrow
    f.write('%i' % len(self.points)) # npoints
    f.write('\n')
    for p in self.points:
      f.write('%i %i ' % p)
    f.write('\n')

class Rectangle(Polyline):
  def __init__(self, x0, y0, w, h, *args, **kwargs):
    x1 = x0 + w
    y1 = y0 + h
    Polyline.__init__(self, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], *args, **kwargs)

class Line(Polyline):
  def __init__(self, x0, y0, x1, y1, *args, **kwargs):
    Polyline.__init__(self, [(x0, y0), (x1, y1)], *args, **kwargs)

class Circle(object):
  def __init__(self, x0, y0, r, fill=False, area_fill=20, fill_color=0, thickness=1, depth=50):
    self.x0 = x0
    self.y0 = y0
    self.radius = r
    self.fill = fill
    self.fill_color = fill_color
    self.area_fill = area_fill
    self.thickness = thickness
    self.depth = depth
  def write(self, f):
    ##1 3 0 1 0 7 50 -1 -1 0.000 1 0.0000 2295 810 427 427 2295 810 1890 675
    f.write('%i ' % 1) # object_code (ellipse)
    f.write('%i ' % 3) # sub_type (circle defined by radius)
    f.write('%i ' % 0)  # line_style
    f.write('%i ' % self.thickness)  # thickness
    f.write('%i ' % 0)  # pen_color
    if self.fill:
      f.write('%i ' % self.fill_color)  # fill_color
    else:
      f.write('%i ' % 7)  # fill_color
    f.write('%i ' % self.depth) # depth
    f.write('%i ' % -1) # pen_style (not used)
    if self.fill:
      f.write('%i ' % self.area_fill) # area_fill
    else:
      f.write('%i ' % -1) # area_fill (no fill)
    f.write('%.3f ' % 0.000) # style_val
    f.write('%.i ' % 1) # direction (always 1)
    f.write('%.3f ' % 0.000) # angle (radians)
    center = (self.x0, self.y0)
    #radius = (self.x0, self.y0 + self.radius)
    radius = (self.radius, self.radius)
    f.write('%i %i ' % center) # center
    f.write('%i %i ' % radius) # radius
    f.write('%i %i ' % center) # first point entered
    f.write('%i %i ' % radius) # last point entered
    f.write('\n')

class Text(object):
  def __init__(self, x0, y0, msg, font_size=12, align='left', angle=0.0, color=0, depth=50):
    self.x0 = x0
    self.y0 = y0
    self.msg = msg
    self.font_size = font_size
    self.align = align
    self.angle = angle
    self.color = color
    self.depth = depth
  def write(self, f):
    f.write('%i ' % 4) # object_code (polyline)
    align = {'left': 0, 'center': 1, 'right': 2}[self.align]
    f.write('%i ' % align) # sub_type (0=left justified, 1: center justified, 2: right justified)
    f.write('%i ' % self.color)  # color
    f.write('%i ' % self.depth)  # depth
    f.write('%i ' % -1)  # pen_style (not used)
    f.write('%i ' % 4)  # font (4 = sans serif)
    f.write('%.3f ' % self.font_size) # font_size
    f.write('%.3f ' % self.angle) # angle
    f.write('%i ' % 16) # font_flags
    f.write('%.3f ' % 135) # height
    f.write('%.3f ' % 360) # length
    f.write('%i ' % self.x0) # x (LOWER left corner) (lower right corner if right justified)
    f.write('%i ' % self.y0) # y
    f.write('%s\\001' % self.msg) # string
    f.write('\n')

class Color(object):
  def __init__(self, code, rgb=None, hex_color=None):
    self.code = code
    assert rgb is not None or hex_color is not None 
    if hex_color is None:
      self.hex_color = '#%.2x%.2x%.2x' % rgb
    else:
      self.hex_color = hex_color
  def write(self, f):
    f.write('%i ' % 0) # object code (color)
    f.write('%i ' % self.code) # color number
    f.write(self.hex_color) # color value
    f.write('\n')

def write_fig(f, objs):
  f.write("#FIG 3.2  Produced by PyGobstones version %s\n" % (common.utils.version_number(),))
  f.write("Landscape\n")
  f.write("Center\n")
  f.write("Metric\n")
  f.write("A3\n")
  f.write("100.00\n")
  f.write("Single\n")
  f.write("-2\n")
  f.write("1200 2\n")
  for x in objs:
    x.write(f)

VALID_OPTIONS = ['verbose', 'head', 'labels', 'colors', 'color-names']

class FigBoardFormat(lang.board.basic.BoardFormat):

  def dump(self, board, f, **kwargs):
    options = {}
    for option in VALID_OPTIONS:
      options[option] = True

    if 'style' in kwargs:
      for option in kwargs['style'].split(','):
        value = not option.startswith('no-')
        if not value:
          option = option[3:]
        if option not in options:
          assert False
        options[option] = value

    write_fig(f, self.render(board, options))

  def load(self, board, f):
    raise lang.board.basic.BoardFormatException(i18n.i18n('Loading of fig boards not supported'))

  def render(self, board, options={}):
    Margin = 250
    CellSize = 600
    StoneRadius = 110

    white = 7
    black = 0

    width, height = board.size

    def color_code(x):
      if x == 'head-background':
        if options['colors']:
          return 40
        else:
          return 7
      elif x == 'head':
        if options['colors']:
          return 41
        else:
          return 0
      else:
        if options['colors']:
          return 50 + x
        else:
          return 7
    
    objs = []

    objs.append(Color(color_code('head-background'), hex_color='#e0e0a0'))
    objs.append(Color(color_code('head'), hex_color='#808000'))
    for i in range(lang.gbs_builtins.NUM_COLORS):
      objs.append(Color(50 + i, hex_color=i18n.i18n('I18N_stone_fill%i' % (i,))))

    objs.append(Rectangle(0, 0, 2 * Margin + width * CellSize, 2 * Margin + height * CellSize, pen_color=white, depth=100))

    def pm(b):
      if b:
        return 1
      else:
        return -1

    def cell_for(i, j, coli):
      objs = []
      num = board.cells[j][i].num_stones(coli) 
      col = lang.gbs_builtins.Color(coli).name()
      x0 = Margin + CellSize * i + CellSize // 2
      y0 = Margin + CellSize * (height - j - 1) + CellSize // 2
      x0 += pm(coli % 2 == 0) * CellSize // 4
      y0 += pm(coli >= 2) * CellSize // 4
      if num > 0:
        # stone circle
        objs.append(Circle(x0, y0, StoneRadius, fill=True, fill_color=color_code(coli), depth=10))

        snum = str(num)
        if options['color-names']:
          if len(snum) == 1:
            # number
            objs.append(Text(x0 - int(StoneRadius / 2.5), y0 + 50, snum, align='center', font_size=11, depth=10))
            # color name
            objs.append(Text(x0 + int(StoneRadius / 2.5), y0 + 50, col[0], align='center', font_size=8, depth=10))
          else:
            # number + color name
            objs.append(Text(x0, y0 + 50, snum + col[0], align='center', font_size=8, depth=10))
        else:
          # only number
          objs.append(Text(x0, y0 + 50, snum, align='center', font_size=11, depth=10))
      return objs

    def head(i, j):
      objs = []
      x0 = Margin + CellSize * i
      y0 = Margin + CellSize * (height - j - 1)
      x1 = x0 + CellSize
      y1 = y0 + CellSize

      sm = (x1 - x0) // 10
      smm = max(1, sm // 2)
      a = x0 + ((x1 - x0) % sm) // 2
      objs.append(Rectangle(x0, y0, CellSize, CellSize, fill=True, fill_color=color_code('head-background'), depth=45))
      cc = color_code('head')
      for x in range(a, x1 + 1, sm):
        objs.append(Line(x - smm, y0 - smm, x + smm, y0 + smm, pen_color=cc, thickness=2, depth=40))
        objs.append(Line(x + smm, y0 - smm, x - smm, y0 + smm, pen_color=cc, thickness=2, depth=40))
        objs.append(Line(x - smm, y1 - smm, x + smm, y1 + smm, pen_color=cc, thickness=2, depth=40))
        objs.append(Line(x + smm, y1 - smm, x - smm, y1 + smm, pen_color=cc, thickness=2, depth=40))
      a = y0 + ((y1 - y0) % sm) // 2
      for y in range(a, y1 + 1, sm):
        objs.append(Line(x0 - smm, y - smm, x0 + smm, y + smm, pen_color=cc, thickness=2, depth=40))
        objs.append(Line(x0 - smm, y + smm, x0 + smm, y - smm, pen_color=cc, thickness=2, depth=40))
        objs.append(Line(x1 - smm, y - smm, x1 + smm, y + smm, pen_color=cc, thickness=2, depth=40))
        objs.append(Line(x1 - smm, y + smm, x1 + smm, y - smm, pen_color=cc, thickness=2, depth=40)) 
      return objs

    def label_row(i):
      x0 = Margin // 2
      x1 = Margin + CellSize * width + Margin // 2
      y = Margin + (height - i - 1) * CellSize + CellSize // 2
      objs = []
      for x in [x0, x1]:
        objs.append(Text(x, y + 50, str(i), align='center', font_size=12))
      return objs

    def label_col(j):
      y0 = Margin // 2
      y1 = Margin + CellSize * height + Margin // 2
      x = Margin + j * CellSize + CellSize // 2
      objs = []
      for y in [y0, y1]:
        objs.append(Text(x, y + 50, str(j), align='center', font_size=12))
      return objs

    for i in range(width):
      for j in range(height):
        objs.append(Rectangle(Margin + i * CellSize, Margin + j * CellSize, CellSize, CellSize,
                              pen_color=black, depth=50))
        for coli in range(lang.gbs_builtins.NUM_COLORS):
          objs.extend(cell_for(i, j, coli))

    if options['head']:
      j, i = board.head
      objs.extend(head(i, j))

    if options['labels']:
      for i in range(height):
        objs.extend(label_row(i))
      for j in range(width):
        objs.extend(label_col(j))
    return objs

