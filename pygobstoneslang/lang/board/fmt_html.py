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

import pygobstoneslang.common.utils as utils
import pygobstoneslang.common.i18n as i18n
import pygobstoneslang.lang.gbs_builtins as gbs_builtins
import basic

class HtmlBoardFormat(basic.BoardFormat):
  # size can be:
  #   - the string 'relative'
  #   - an integer (side of a cell in pixels)
  def gbs_board_style(self, size='relative', board_size=(9, 9)):
    style = """
table.gbs_board {
  border-style: none;
  border: solid black 0px;
  border-spacing: 0;
  border-collapse: collapse;
  font-family: Arial, Helvetica, sans-serif;
  font-size: $FONT_SIZE;
  display: inline-block;
  vertical-align: top;
}
.gbs_board td {
  margin: 0;
  padding: 2px;
  border: solid #888 1px;
  width: $WIDTH;
  height: $HEIGHT;
}
.gbs_board td.gh { /* position of the header in the board */
  margin: 0;
  padding: 2px;
  border: dotted #440 3px;
  background: #dd8;
  width: $WIDTH;
  height: $HEIGHT;
}
.gbs_board td.lv { /* labels at the side */
  text-align: center;
  vertical-align: middle;
  border-style: none;
  border: solid black 0px;
  background: #ddd;
  width: $HALF_WIDTH;
}
.gbs_board td.lh { /* labels at the top / bottom */
  text-align: center;
  vertical-align: middle;
  border-style: none;
  border: solid black 0px;
  background: #ddd;
  height: $HALF_HEIGHT;
}
.gbs_board td.lx { /* corner */
  border-style: none;
  border: solid black 0px;
  background: #ddd;
  width: $HALF_WIDTH;
  height: $HALF_HEIGHT;
}
.gbs_board td.top_left {
  -webkit-border-top-left-radius: 10px;
  -moz-border-top-left-radius: 10px;
  border-top-left-radius: 10px;
}
.gbs_board td.top_right {
  -webkit-border-top-right-radius: 10px;
  -moz-border-top-right-radius: 10px;
  border-top-right-radius: 10px;
}
.gbs_board td.bottom_left {
  -webkit-border-bottom-left-radius: 10px;
  -moz-border-bottom-left-radius: 10px;
  border-bottom-left-radius: 10px;
}
.gbs_board td.bottom_right {
  -webkit-border-bottom-right-radius: 10px;
  -moz-border-bottom-right-radius: 10px;
  border-bottom-right-radius: 10px;
}
.gbs_board table.gc { /* cell table */
  border-style: none;
  border: solid black 0px;
}
.gbs_board .gc tr {
  border-style: none;
  border: 0px;
}
.gbs_board .gc td {
  border-style: none;
  border: solid black 0px;
  width: $HALF_WIDTH;
  height: $HALF_HEIGHT;
  text-align: center;
  color: black;
}
.gbs_board .gc td div {
  line-height: 2;
}
.gbs_board div.A { background: #88f; border: solid 1px #008; }
.gbs_board div.N { background: #aaa; border: solid 1px #222; }
.gbs_board div.R { background: #f88; border: solid 1px #800; }
.gbs_board div.V { background: #8f8; border: solid 1px #080; }
.gbs_board div.O { width: 20px; height: 20px; background: none; } /* empty */
.gbs_stone {
  font-weight: bold;
    font-size: 8pt;
    width: 20px;
    height: 20px;
    -webkit-border-radius: 10px;
    -moz-border-radius: 10px;
    border-radius: 10px;
}"""
    font_size = '9pt'
    if size == 'relative':
      tot_width = 100.0
      tot_height = 100.0
      unit = '%'

      w, h = board_size
      half_width = int(tot_width / (2 * (w + 1)))
      half_height = int(tot_height / (2 * (w + 1)))
      if half_width < 5:
        half_width = 5
      if half_height < 5:
        half_height = 5

    else:
      half_width = size / 2
      half_height = size / 2
      if half_width < 5:
        half_width = 5
      if half_height < 5:
        half_height = 5
      unit = 'px'

    width = '%s' % (2 * half_width,)
    height = '%s' % (2 * half_height,)
    half_width = '%s' % (half_width,)
    half_height = '%s' % (half_height,)
    style = style.replace('$WIDTH', width + unit)
    style = style.replace('$HEIGHT', height + unit)
    style = style.replace('$HALF_WIDTH', half_width + unit)
    style = style.replace('$HALF_HEIGHT', half_height + unit)
    style = style.replace('$FONT_SIZE', font_size)
    return style

  def render(self, board, draw_head=True):
    w, h = board.size
    out = utils.StringIO()

    def row_titles(border):
      out.write('<tr>')
      out.write('<td class="lx ' + border + '_left"></td>')
      for x in range(w):
        out.write('<td class="lh">%u</td>' % (x,))
      out.write('<td class="lx ' + border + '_right"></td>')
      out.write('</tr>\n')

    out.write('<table class="gbs_board">\n')
    row_titles('top')
    for y in utils.seq_reversed(range(h)):
      out.write('  <tr>\n')
      out.write('    <td class="lv">%u</td>\n' % (y,))
      for x in range(w):
        def cell_for(coli):
          cant = board.cells[y][x].num_stones(coli)
          if cant == 0: return '<td><div class="O"></div></td>'
          col = gbs_builtins.Color(coli).name()
          return '<td><div class="gbs_stone %s"><span>%i</span></div></td>' % (col[0], cant)

        if board.head == (y, x) and draw_head:
          out.write('    <td class="gc gh">\n')
        else:
          out.write('    <td class="gc">\n')

        out.write('      <table>\n')
        out.write('        <tr>%s%s</tr>\n' % (cell_for(1), cell_for(0)))
        out.write('        <tr>%s%s</tr>\n' % (cell_for(2), cell_for(3)))
        out.write('      </table>\n')

        out.write('    </td>\n')
      out.write('    <td class="lv">%u</td>\n' % (y,))
      out.write('  </tr>\n')
    row_titles('bottom')
    out.write('</table>\n')
    res = out.getvalue()
    out.close()
    return res

  def dump(self, board, f, **kwargs):
    f.write('<style type="text/css">')
    f.write(self.gbs_board_style(size=30, board_size=board.size))
    f.write('</style>\n\n')
    f.write(self.render(board))

  def load(self, board, f):
    raise basic.BoardFormatException(i18n.i18n('Loading of html boards not supported'))
