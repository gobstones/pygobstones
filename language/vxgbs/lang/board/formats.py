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


import lang.board.fmt_gbt
import lang.board.fmt_tex
import lang.board.fmt_gbb
import lang.board.fmt_html
import lang.board.fmt_gbbo
import lang.board.fmt_png
import lang.board.fmt_fig

AvailableFormats = {
  'gbt': lang.board.fmt_gbt.GbtBoardFormat,
  'tex': lang.board.fmt_tex.TexBoardFormat,
  'gbb': lang.board.fmt_gbb.GbbBoardFormat,
  'html': lang.board.fmt_html.HtmlBoardFormat,
  'gbbo': lang.board.fmt_gbbo.GbboBoardFormat,
  'fig': lang.board.fmt_fig.FigBoardFormat,
}

if lang.board.fmt_png.available:
  AvailableFormats['png'] = lang.board.fmt_png.PngBoardFormat

DefaultFormat = 'gbb'

def is_board_filename(filename):
  return filename.lower().split('.')[-1] in AvailableFormats

def format_for(filename):
  fmt = filename.lower().split('.')[-1] 
  if fmt in AvailableFormats:
    return fmt
  else:
    return DefaultFormat

