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

if common.utils.python_major_version() < 3:
    import Tkinter as tkinter
else:
    import tkinter

import common.i18n as i18n
from common.utils import hsv
import math

ProgW = 50
ProgH = 20
Period = 10
PeriodInc = 2
Delay = 100
class ProgressBar(tkinter.Frame):
  def __init__(self, root, onstop, *args, **kwargs):
    tkinter.Frame.__init__(self, root, *args, **kwargs)
    self.bar = tkinter.Canvas(self)
    self.stop = tkinter.Button(self, text=i18n.i18n('Stop'), command=onstop)
    self.bar.place(x=0, y=0, width=ProgW, height=ProgH)
    self.stop.place(x=ProgW, y=0, width=ProgW, height=ProgH)
    self.after(Delay, self.update)
    self.state = 0
  def update(self):
    self.state = (self.state + PeriodInc) % Period
    self.bar.delete(tkinter.ALL)
    for i in range(ProgW):
      s = (self.state + i) % Period
      if s < (Period / 2):
        s = float(s) / (Period / 2)
      else:
        s = float(Period - s) / (Period / 2)
      self.bar.create_line(i, 0, i, ProgH, fill=hsv(.65, 1.0 - s, math.sqrt(.4 + s * .6)))
    self.after(Delay, self.update)

