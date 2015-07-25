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
import lang.judge.gbs_judge
import lang.board.formats
import lang.gbs_parser
import lang.gbs_pprint

def html_board(board, draw_head=True):
  return lang.board.formats.AvailableFormats['html']().render(board, draw_head=draw_head)

def html_escape(txt):
  txt = txt.replace('&', '&amp;')
  txt = txt.replace('<', '&lt;')
  txt = txt.replace('>', '&gt;')
  return txt

def pprint(source_code, test_case_name):
  try:
    tree = lang.gbs_parser.parse_string(source_code, filename=test_case_name)
    return lang.gbs_pprint.pretty_print(tree, print_imports=False)
  except common.utils.SourceException as exception:
    return '...'

No_result = '  <tt>&lt;%s&gt;</tt>\n' % (i18n.i18n('No result'),)

class FailedTestReport(object):
  def __init__(self, options, problem, test_case, initial_board, test_source_code, ref_sol, usr_sol):
    self._options = options
    self._problem = problem
    self._test_case = test_case
    self._initial_board = initial_board
    self._source_code = test_source_code
    self._ref_sol = ref_sol
    self._usr_sol = usr_sol

  def render(self):
    tit = i18n.i18n('Test case "%s" failed') % (self._test_case.run_name(),)
    out = common.utils.StringIO()
    out.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
    out.write('<html>\n')
    out.write('  <head>\n')
    out.write('  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n')
    out.write('  <meta name="generator" content="PyGobstones%s">\n' % (common.utils.version_number(),))
    out.write('  <title>%s</title>' % (tit,))
    out.write('  <style type="text/css">\n')
    out.write(lang.board.formats.AvailableFormats['html']().gbs_board_style(32, (9, 9)))
    out.write('  </style>\n')
    out.write('  <style type="text/css">\n')
    out.write('''
    body {
      font-family: Verdana, helvetica;
      font-size: 9pt;
      padding: 10px;
    }
    .info_frame {
      padding: 20px;
      margin: 0;
      width: 80%;
    }
    .returned_vars {
      background:lightblue;
      border: solid black 2px;
      width: 90%;
      padding: 10px;
    }
    ''')
    out.write('  </style>\n')
    out.write('  <script type="text/javascript">\n')
    template = '''
    function show(tab_id) {
      var all_tabs = ['test_case', {EXPECTED} 'obtained_result'];
      for (var i in all_tabs) {
        var elem = document.getElementById(all_tabs[i]);
        var link_elem = document.getElementById('link_' + all_tabs[i]);
        link_elem.style.margin = "0 0 0 10px";
        link_elem.style.padding = "5px 10px";
        link_elem.style.border = "solid gray 1px"
        if (all_tabs[i] == tab_id) {
          elem.style.display = "block";
          link_elem.style.background = elem.style.background;
        } else {
          elem.style.display = "none";
          link_elem.style.background = "white";
        }
      }
    }
    '''
    if self._options['provide_expected_result']:
      template = template.replace('{EXPECTED}', "'expected_result', ")
    else:
      template = template.replace('{EXPECTED}', '')
    out.write(template)
    out.write('  </script>\n')
    out.write('  </head>\n')
    out.write('  <body onload="show(\'test_case\')">\n')

    out.write('  <h1>%s</h1>\n' % (tit,))
    self._tabmenu(out) 
    self._input_board(out)
    if self._options['provide_expected_result']:
      self._expected_result(out)
    self._obtained_result(out)
    out.write('  </body>\n')
    out.write('</html>\n')
    res = out.getvalue()
    out.close()
    return res

  def _tabmenu(self, out):
    out.write('<p>\n')
    out.write('  <input type="submit" class="btn" id="link_test_case" onclick="show(\'test_case\')" value="%s">\n' % (i18n.i18n('Test case'),))
    if self._options['provide_expected_result']:
      out.write('  <input type="submit" class="btn" id="link_expected_result" onclick="show(\'expected_result\')" value="%s">\n' % (i18n.i18n('Expected result'),))
    out.write('  <input type="submit" class="btn" id="link_obtained_result" onclick="show(\'obtained_result\')" value="%s">\n' % (i18n.i18n('Obtained result'),))
    out.write('</p>\n')

  def _input_board(self, out):
    out.write('  <div id="test_case" class="info_frame" style="background:#c0c0c0">\n')

    out.write('  <h3>%s</h3>\n' % (i18n.i18n('Initial board'),))
    input_board = self._initial_board
    out.write(html_board(input_board))

    if self._source_code:
      out.write('  <h3>%s</h3>\n' % (i18n.i18n('Source code'),))
      out.write('<pre>')
      out.write(html_escape(pprint(self._source_code, self._test_case.run_name())))
      out.write('</pre>')

    out.write('  </div>\n')

  def _expected_result(self, out):
    out.write('  <div id="expected_result" class="info_frame" style="background:#c0f0c0">\n')
    if not self._ref_sol:
      out.write(No_result)
    else:
      board, keyvals = self._ref_sol
      head_pos = board.head[1], board.head[0]
      if self._options['provide_expected_result']:
        self._result(i18n.i18n('Expected final board'), out, board, head_pos, keyvals)
    out.write('  </div>\n')

  def _obtained_result(self, out):
    out.write('  <div id="obtained_result" class="info_frame" style="background:#f0c0c0">\n')
    if not self._usr_sol:
      out.write(No_result)
    else:
      board, keyvals = self._usr_sol
      head_pos = board.head[1], board.head[0]
      if not self._options['check_board']:
        board = None
      if self._options['check_board'] or not self._options['check_head']:
        head_pos = None
      if not self._options['check_result']:
        keyvals = None
      self._result(i18n.i18n('Obtained final board'), out, board, head_pos, keyvals)
    out.write('  </div>\n')

  def _result(self, tit, out, board, head_pos, keyvals):
    if board is not None:
      out.write('  <h3>%s</h3>\n' % (tit,))
      out.write(html_board(board, draw_head=self._options['check_head']))
    if self._options['check_result']:
      out.write('  <h3>%s</h3>\n' % (i18n.i18n('Returned variables'),))
      if len(keyvals) == 0:
        out.write('  <tt>&lt;%s&gt;</tt>\n' % (i18n.i18n('No returned variables'),))
      else:
        out.write('  <div class="returned_vars">\n')
        for k, v in keyvals:
          out.write('<p><tt>%s -&gt; %s</tt></p>\n' % (k, v))
        out.write('  </div>\n')

  def display(self):
    common.utils.open_temp_html(self._test_case.run_name(), self.render())

