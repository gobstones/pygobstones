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

import os

import common.i18n as i18n
from common.utils import *

#### Tracking of positions inside source files.
####
#### ProgramElements are elements inside a program, typically
#### tokens or AST nodes.
####
#### ProgramAreas are specific regions of the program, such
#### as the area after a given token.

class ProgramElement(object):
  """Represents an element inside a program. Subclasses should implement:
  pos_begin:     starting position
  pos_end:       final position
  description(): human readable description"""
  def source(self):
    return self.pos_begin.string[self.pos_begin.start:self.pos_end.start]

class Position(object):
  "Represents a position in a source file or string."
  def __init__(self, string, filename='...', start=0, row=1, col=1):
    self.string = string
    self._filename = filename
    self.start = start
    self.row = row
    self.col = col
  def after_reading(self, string):
    """Returns the position that results after reading the characters
in the string."""
    new_start = self.start + len(string)
    newlines = string.count('\n')
    new_row = self.row + newlines
    if newlines == 0:
      new_col = self.col + len(string)
    else:
      new_col = len(string) - string.rindex('\n')
    return Position(self.string, self._filename, new_start, new_row, new_col)
  def __repr__(self):
    return '%s:%s:%s' % (self._filename, self.row, self.col)
  def filename(self):
    return self._filename
  def row_col(self):
    return '%s %s, %s %s' % (i18n.i18n('line'), self.row, i18n.i18n('column'), self.col)
  def file_row_col(self):
    return '%s (%s)' % (self.filename(), self.row_col())
  def file_row(self):
    return '(%s:%s)' % (self.filename(), self.row)
  def line_before(self):
    try:
      r = self.string.rindex('\n', 0, self.start)
      res = self.string[r + 1:self.start]
    except ValueError:
      res = self.string[:self.start]
    return expand_tabs(res)
  def two_lines_after(self):
    try:
      r1 = self.string.index('\n', self.start)
      l1 = self.string[self.start:r1]
      try:
        r2 = self.string.index('\n', r1 + 1)
        l2 = self.string[r1+1:r2]
        res = [l1, l2]
      except ValueError:
        res = [l1]
    except ValueError:
      res = [self.string[self.start:]]
    return [expand_tabs(line) for line in res]

class ProgramArea(object):
  "Represents an area of a program."
  def __repr__(self): return '(...)'

class ProgramAreaNear(ProgramArea):
  """Represents the area of a program that occurs near the beggining of
a given program element."""
  def __init__(self, elem):
    self.elem = elem
  def __repr__(self):
    l1 = '%s\n%s %s' % (self.elem.pos_begin.file_row_col(),
                        i18n.i18n('near'), self.elem.description())
    before = self.elem.pos_begin.line_before()
    after = self.elem.pos_end.two_lines_after()
    ind = ' ' * len(before)
    l2 = ind + '|' + '\n' + ind + 'V'
    src = self.elem.source()
    if len(src) < 50:
      l3 = '%s%s%s' % (before, src, after[0])
      if len(after) > 1: l3 += '\n'
    else:
      l3 = '%s%s' % (before, src[:50])
      if src[-1] != '\n': l3 += '...\n'
    return '\n'.join(['--', l1, l2, l3, '--'])
  def interval(self):
    return self.elem.pos_begin, self.elem.pos_end
  def filename(self):
    return self.elem.pos_begin.filename()

