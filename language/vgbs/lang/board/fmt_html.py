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
import common.i18n as i18n
import lang.gbs_builtins
import lang.board.basic

class HtmlBoardFormat(lang.board.basic.BoardFormat):
  # size can be:
  #   - the string 'relative'
  #   - an integer (side of a cell in pixels)
  def gbs_board_style(self, size='relative', board_size=(9, 9)):
    style = """
table.gbs_board {
  border: black solid 1px;
  border-spacing: 0;
  border-collapse: collapse;
  font-family: Verdana, helvetica;
  font-size: $FONT_SIZE;
}
.gbs_board td {
  margin: 0;
  padding: 2px;
  border: solid #a52a2a 1px;
  background: #ddd;
  width: $WIDTH;
  height: $HEIGHT;
}
.gbs_board td.gh { /* position of the header in the board */
  margin: 0;
  padding: 2px;
  border: dashed #440 3px;
  background: #dd8;
  width: $WIDTH;
  height: $HEIGHT;
}
.gbs_board td.lv { /* labels at the side */
  text-align: center;
  vertical-align: middle;
  border-style: none;
  background: #fff;
  width: $HALF_WIDTH;
}
.gbs_board td.lh { /* labels at the top / bottom */
  text-align: center;
  vertical-align: middle;
  border-style: none;
  background: #fff;
  height: $HALF_HEIGHT;
}
.gbs_board td.lx { /* corner */
  border-style: none;
  background: #fff;
  width: $HALF_WIDTH;
  height: $HALF_HEIGHT;
}
.gbs_board table.gc { /* cell table */
  border: none;
  border-spacing: 2px;
  border-collapse: separate;
}
.gbs_board .gc td {
  border: none;
  width: $HALF_WIDTH;
  height: $HALF_HEIGHT;
  text-align: center;
  vertical-align: middle;
  color: black;
  font-family: Verdana, helvetica;
  font-size: $FONT_SIZE;
}
.gbs_board td.A { background: #88f; border: solid 1px #008; }
.gbs_board td.N { background: #aaa; border: solid 1px #222; }
.gbs_board td.R { background: #f88; border: solid 1px #800; }
.gbs_board td.V { background: #8f8; border: solid 1px #080; }
.gbs_board td.O { background: none; } /* empty */
    """
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
    out = common.utils.StringIO()

    def row_titles():
      out.write('<tr>')
      out.write('<td class="lx">&nbsp;</td>')
      for x in range(w):
        out.write('<td class="lh">%u</td>' % (x,))
      out.write('<td class="lx">&nbsp;</td>')
      out.write('</tr>\n')

    out.write('<table class="gbs_board" cellpadding="0" cellspacing="0">\n')
    row_titles()
    for y in common.utils.seq_reversed(range(h)):
      out.write('  <tr>\n')
      out.write('    <td class="lv">%u</td>\n' % (y,))
      for x in range(w):
        def cell_for(coli):
          cant = board.cells[y][x].num_stones(coli) 
          if cant == 0: return '<td class="O">&nbsp;</td>'
          col = lang.gbs_builtins.Color(coli).name()
          return '<td class="%s">%i</td>' % (col[0], cant)

        if board.head == (y, x) and draw_head:
          out.write('    <td class="gh">\n')
        else:
          out.write('    <td>\n')

        out.write('      <table class="gc">\n')
        out.write('        <tr>%s%s</tr>\n' % (cell_for(1), cell_for(0)))
        out.write('        <tr>%s%s</tr>\n' % (cell_for(2), cell_for(3)))
        out.write('      </table>\n')

        out.write('    </td>\n')
      out.write('    <td class="lv">%u</td>\n' % (y,))
      out.write('  </tr>\n')
    row_titles()
    out.write('</table>\n')
    res = out.getvalue()
    out.close()
    return res

  def dump(self, board, f, **kwargs):
    f.write('<style type="text/css">')
    #f.write(self.gbs_board_style(size=50, board_size=board.size))
    f.write(self.gbs_board_style(size=30, board_size=board.size))
    f.write('</style>\n\n')
    f.write(self.render(board))

  def load(self, board, f):
    raise lang.board.basic.BoardFormatException(i18n.i18n('Loading of html boards not supported'))

