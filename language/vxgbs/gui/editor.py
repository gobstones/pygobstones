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
import common.utils

if common.utils.python_major_version() < 3:
    import Tkinter as tkinter
else:
    import tkinter

import common.i18n as i18n
import gui.progress
import gui.config

#### Enriched text box

class EditorException(Exception):
  pass

def signature(text):
  return text

Background_color = 'white'
TAGS = {
  'num': ('red', None),
  'string': ('magenta', None),
  'string_start': ('magenta', None),
  'lowerid': ('black', None),
  'upperid': ('black', None),
  'operator': ('darkgreen', None),
  'keyword': ('purple', None),
  'builtin_function': ('blue', None),
  'builtin_procedure': ('deeppink', None),
  'builtin_constant': ('darkcyan', None),
  'type': ('brown', None),  
  'delim': ('black', None),
  'delim_match': (None, 'cyan'),
  'search_match': (None, 'green'),
  'search_curmatch': (None, 'yellow'),
  'COMMENT': ('red', None),
  'COMMENT_start': ('red', None),
  'ERROR': (None, 'pink'),
}
EPHEMERAL = ['delim_match']

def closing_delimiter(x):
  if x == '(': return ')'
  if x == '{': return '}'
  return ''

Msg_colors = {
  'error': 'pink',
  'check_ok': 'lightgreen',
  'result': 'lightblue',
  'log': 'white',
}

ScrollbarW = 16
MsgBtnH = 16
StatbarH = 20

def tpos(row0, pos):
  return '%s.%s' % (row0 - 1 + pos.row, pos.col - 1)

def pos(row, col=None):
  return '%s.%s' % (row, col)

def index_gt(ind1, ind2):
  r1, c1 = ind1.split('.')
  r2, c2 = ind2.split('.')
  return int(r1) > int(r2) or \
         (int(r1) == int(r2) and int(c1) > int(c2))

class Editor(tkinter.Text):
  """Represents an editor of Gobstones programs. Features:
- syntax highlighting
- issuing error messages
- status bar with filename and line numbers"""

  def __init__(self, tools, root, expandTabs=True, tabStop=4, autoindent=False, font=gui.config.DefaultFont, *args, **kwargs):

    self._font = font

    tkinter.Text.__init__(self, root, undo=True, background=Background_color, font=self._font, *args, **kwargs)

    self.expandTabs = expandTabs
    self.tabStop = tabStop
    self.autoindent = autoindent

    self.bind('<Control-y>', self.keypress_sync_all)
    self.bind('<KeyPress-Tab>', self.keypress_tab)
    self.bind('<KeyPress-BackSpace>', self.keypress_backspace)
    self.bind('<KeyPress-Home>', self.keypress_home)
    self.bind('<KeyRelease-Return>', self.keyrelease_return)
    self.bind('<KeyRelease>', self.keyrelease)
    self.bind('<KeyPress>', self.keypress)
    self.bind('<ButtonRelease>', self.buttonrelease)
    self.bind('<Configure>', self.refresh_aspect)
    # parent
    self.root = root
    # messages
    self.message = None
    self._last_search_term = None
    # scrollbar
    self.scrollbar = tkinter.Scrollbar(root)
    self.scrollbar.place()
    self.config(yscrollcommand=self.yscroll)
    self.scrollbar.config(command=self.yview)
    # status bar
    self._create_statusbar()

    self.tools = tools

    self.init_tags()
    self.new_file()

    self.place()
    self.refresh_aspect()

  def _create_statusbar(self):
    self.statusbar = tkinter.Frame(self.root)

    self.statusbar_file = tkinter.StringVar()
    self.statusbar_row = tkinter.StringVar()
    self.statusbar_col = tkinter.StringVar()

    sb_file = tkinter.Label(self.statusbar,
       width=30,
       textvariable=self.statusbar_file,
       anchor=tkinter.W,
       justify=tkinter.LEFT)
    sb_file.pack(side=tkinter.LEFT)

    sb_col = tkinter.Label(self.statusbar,
       justify=tkinter.RIGHT,
       width=4,
       textvariable=self.statusbar_col)
    sb_col.pack(side=tkinter.RIGHT)

    sb_row = tkinter.Label(self.statusbar,
       justify=tkinter.RIGHT,
       width=4,
       textvariable=self.statusbar_row)
    sb_row.pack(side=tkinter.RIGHT)
    self.progress_bar = None
    self.statusbar.place()

  def init_tags(self):
    self.reserved = {
      'delim': [
        '{', '}', '(', ')', ';', ',',
      ],      
      'keyword': [
        'if', 'else', 'not', 'case', 'while', 'switch', 'to', 'match', 
        'field', 'record', 'is', 'variant', 'type',
        'repeat', 'foreach', 'in', 'procedure', 'function',
        'return', 'div', 'mod', 'Skip',
        'from', 'import', 'program', 'interactive'
      ],
      'builtin_procedure': [i18n.i18n(name) for name in [
        'THROW_ERROR', 'PutStone', 'TakeStone', 'Move', 'GoToOrigin', 'ClearBoard',
      ]],
      'builtin_function': [i18n.i18n(name) for name in [
        'numStones', 'existStones', 'canMove', 'minBool', 'maxBool',
        'minDir', 'maxDir', 'minColor', 'maxColor', 'next', 'prev',
        'opposite',
      ]],
      'builtin_constant': [i18n.i18n(name) for name in [
        'True', 'False', 'North', 'South', 'East', 'West',
        'Color0', 'Color1', 'Color2', 'Color3',
      ]],
      'type': [i18n.i18n(name) for name in [
        'Color', 'Dir', 'Int', 'Bool',
      ]],
    }
    self.tags = TAGS
    for tag, (fg, bg) in self.tags.items():
      if fg is not None:
        self.tag_config(tag, foreground=fg)
      if bg is not None:
        self.tag_config(tag, background=bg)

  def remove_tags(self, start, end, clean_all):
    if clean_all:
      for tag in self.tags.keys():
        self.tag_remove(tag, start, end)
    else:
      for tag in EPHEMERAL:
        self.tag_remove(tag, start, end)

  def keypress(self, event):
    if event.char == '}':
      self.keypress_rbrace(event)
    elif event.char == '':
      self.clean_screen(clean_all=False)

  def keypress_tab(self, event):
    try:
      # active selection
      if self.index('sel.first'):
        if event.state & 1:
          self.dedent_region() # shift+tab
        else:
          self.indent_region()
        return 'break'
    except tkinter.TclError:
      pass
    if not self.expandTabs: return None
    col = int(self.index(tkinter.INSERT).split('.')[1])
    ts = self.tabStop - col % self.tabStop
    self.insert(tkinter.INSERT, ts * ' ')
    return 'break'

  def indent_region(self, *args):
    try:
      self.index('sel.first')
    except tkinter.TclError:
      return
    ts = self.tabStop
    row0, col0 = [int(x) for x in self.index('sel.first').split('.')]
    row1, col1 = [int(x) for x in self.index('sel.last').split('.')]
    if col1 == 0: row1 -= 1
    for r in range(row0, row1 + 1):
      self.insert(pos(r, 0), ts * ' ')
    self.tag_add('sel', pos(row0, 0), '%s.end' % (row1,))

  def dedent_region(self, *args):
    try:
      self.index('sel.first')
    except tkinter.TclError:
      return
    ts = self.tabStop
    row0, col0 = [int(x) for x in self.index('sel.first').split('.')]
    row1, col1 = [int(x) for x in self.index('sel.last').split('.')]
    if col1 == 0: row1 -= 1
    for r in range(row0, row1 + 1):
      line = self.get(pos(r, 0), '%s.end' % (r,))
      nsp = 0
      while nsp < len(line) and line[nsp] in '\t ':
        nsp += 1
      dedent = min(nsp, ts)
      self.delete(pos(r, 0), pos(r, dedent))
    self.tag_add('sel', pos(row0, 0), '%s.end' % (row1,))

  def keypress_rbrace(self, event):
    if not self.autoindent: return
    current = self.index(tkinter.INSERT)
    start_row = current.split('.')[0]
    start_col = self.sync_screen(clean=True, indent=True)
    start_col = max(0, start_col - self.tabStop)
    start = pos(start_row, start_col)
    spaces = self.get(start, current).strip(' \t')
    if spaces == '':
      self.delete(start, current)
    return 'break'

  def keypress_backspace(self, event):
    try:
      # active selection
      if self.index('sel.first'): return
    except tkinter.TclError:
      pass
    current = self.index(tkinter.INSERT)
    start_row, start_col = current.split('.')
    if int(start_col) == 0: return
    ts = self.tabStop
    if event.state & 4: # ctrl + backspace
      start = pos(start_row, 0)
      erase_len = len(self.get(start, current).split(' ')[-1])
      if erase_len != 0:
        start = pos(start_row, int(start_col) - erase_len)
        self.delete(start, current)
        return 'break'
    start_col = ts * (max(0, int(start_col) - 1) // ts)
    start = pos(start_row, start_col)
    spaces = self.get(start, current).strip(' \t')
    if spaces == '':
      self.delete(start, current)
      return 'break'

  def keypress_home(self, event):
    current = self.index(tkinter.INSERT)
    start_row, start_col = current.split('.')
    start = pos(start_row, 0)
    line = self.get(start, current)
    nsp = 0
    while nsp < len(line) and line[nsp] in ' \t':
      nsp += 1
    if nsp >= int(start_col):
      nsp = 0

    if event.state & 4: # ctrl + home
      new_current = pos(1, 0)
    else:
      new_current = pos(start_row, nsp)

    self.mark_set(tkinter.INSERT, new_current)
    if event.state & 1: # shift + home
      self.tag_add('sel', new_current, current)
    return 'break'

  def keyrelease_return(self, event):
    indent_col = self.sync_screen(clean=True, indent=True)
    if not self.autoindent: return
    current = self.index(tkinter.INSERT)
    start_row, start_col = current.split('.')
    rstart = '%s.0' % (start_row,)
    rend = '%s.end' % (start_row,)
    line = self.get(rstart, rend)
    nsp = 0
    while nsp < len(line):
      if line[nsp] == ' ':
        nsp += 1
      else:
        break
    if nsp < len(line) and line[nsp] == '}':
      indent_col = max(0, indent_col - self.tabStop)
    spend = pos(start_row, nsp)
    self.delete(rstart, spend)
    #if nsp < indent_col:
    #  self.insert(tkinter.INSERT, (indent_col - nsp) * ' ')
    self.insert(tkinter.INSERT, indent_col * ' ')

  def keyrelease(self, event):
    if event.keysym.startswith('Control') or event.keysym == 'y':
      # hack to avoid syncing the line after Control-y
      # (which syncs the whole file)
      return
    elif event.char == '':
      t1 = self.get(tkinter.INSERT)
      r, c = self.index(tkinter.INSERT).split('.')
      t2 = self.get(pos(r, max(0, int(c) - 1)))
      if t1 in '{}' or t2 in '{}':
        self.sync_screen(clean=False)
      elif t1 in '()' or t2 in '()':
        self.sync_line(clean=False)
      else:
        self.clean_screen(clean_all=False)
    elif event.char in '{}':
      self.sync_screen(clean=True)
    else:
      self.sync_line(clean=True)

  def buttonrelease(self, *args):
    #self.sync_screen(clean=True)
    pass

  def refresh_aspect(self, *args, **kwargs):
    if self.message is None:
      self.place(rely=0, relwidth=1, width=-ScrollbarW, relheight=1, height=-StatbarH)
      self.scrollbar.place(relx=1, x=-ScrollbarW, relheight=1, height=-StatbarH)
      self.statusbar.place(relx=0, relwidth=1, rely=1, y=-StatbarH, height=StatbarH)
    elif self.message.relheight:
      relh = self.message.relheight
      self.place(rely=0, relwidth=1, width=-ScrollbarW, relheight=1 - relh)
      self.scrollbar.place(rely=0, relx=1, x=-ScrollbarW, relheight=1 - relh)
      self.message.place(rely=1 - relh, y=-StatbarH, relwidth=1, relheight=relh)
      self.statusbar.place(relx=0, relwidth=1, rely=1, y=-StatbarH, height=StatbarH)
    else:
      absh = self.message.absheight
      self.place(rely=0, relwidth=1, width=-ScrollbarW, relheight=1, height=-absh-StatbarH)
      self.scrollbar.place(rely=0, relx=1, x=-ScrollbarW, relheight=1, height=-absh-StatbarH)
      self.message.place(rely=1, y=-StatbarH-absh, relwidth=1, height=absh)
      self.statusbar.place(relx=0, relwidth=1, rely=1, y=-StatbarH, height=StatbarH)

  def keypress_sync_all(self, *args):
    self.sync_all()
    return 'break'

  def sync_all(self):
    e = int(self.index(tkinter.END).split('.')[0])
    self.sync(1, e + 1)

  def show_rowcol(self):
    row, col = self.index(tkinter.INSERT).split('.')
    col = int(col) + 1
    self.statusbar_row.set('%s' % (row,))
    self.statusbar_col.set('(%s)' % (col,))

  def clean_screen(self, clean_all=True):
    e = int(self.index(tkinter.END).split('.')[0])
    row_from = int(self.index('@0,0').split('.')[0])
    row_to = int(self.index('@0,%s' % self.winfo_height()).split('.')[0])
    row_to = min(row_to, e) + 1
    pos_from = pos(row_from, 0)
    pos_to = pos(row_to, 0)
    self.remove_tags(pos_from, pos_to, clean_all)
    self.show_rowcol()

  def sync_line(self, clean=True):
    e = int(self.index(tkinter.END).split('.')[0])
    crow = int(self.index(tkinter.INSERT).split('.')[0])
    row_from = max(1, crow - 1)
    row_to = min(crow, e) + 1
    self.sync(row_from, row_to, clean, indent=False)
    row, col = self.index(tkinter.INSERT).split('.')
    col = int(col) + 1
    self.statusbar_col.set('(%s)' % (col,))

  def sync_screen(self, clean=True, indent=False):
    e = int(self.index(tkinter.END).split('.')[0])
    row_from = int(self.index('@0,0').split('.')[0])
    row_to = int(self.index('@0,%s' % self.winfo_height()).split('.')[0])
    row_to = min(row_to, e) + 1
    indent_col = self.sync(row_from, row_to, clean, indent)
    self.show_rowcol()
    return indent_col

  def sync(self, row_from, row_to, clean=True, indent=False):
    pos_from = pos(row_from, 0)
    pos_to = pos(row_to, 0)
    string = self.get(pos_from, pos_to)
    self.remove_tags(pos_from, pos_to, clean)

    cursor_index = self.index(tkinter.INSERT)
    opening = []
    indent_col = 0
    for tok in self.tools.tokenize(string):
      s = tok.pos_begin.start
      e = tok.pos_end.start
      tag = tok.type

      # coloring by token type
      for k, v in self.reserved.items():
        if tok.value in v:
          tag = k
          break
      sindex = tpos(row_from, tok.pos_begin)
      eindex = tpos(row_from, tok.pos_end)
      self.tag_add(tag, sindex, eindex)

      # indentation after a newline
      if indent and index_gt(eindex, cursor_index):
        if len(opening) == 0:
          indent_col = 0
        elif opening[-1].value == '(':
          indent_col = opening[-1].pos_begin.col
        elif opening[-1].value == '{':
          indent_col = self.tabStop * len(opening)
        indent = False

      # delimiter matching
      if tok.value in '(){}':
        if tok.value in '({':
           opening.append(tok)
        elif tok.value in ')}' and len(opening) > 0:
           op = opening.pop()
           if closing_delimiter(op.value) == tok.value:
             op_sindex = tpos(row_from, op.pos_begin)
             op_eindex = tpos(row_from, op.pos_end)
             if cursor_index in [sindex, eindex, op_sindex, op_eindex]:
               self.tag_add('delim_match', op_sindex, op_eindex)
               self.tag_add('delim_match', sindex, eindex)
    # after
    return indent_col

  def _set_filename(self, fn):
    self._filename = fn
    if fn is None:
      self.statusbar_file.set(i18n.i18n('Untitled'))
    else:
      self.statusbar_file.set(fn.split('/')[-1])

  def new_file(self):
    self.clear_messages()
    self._set_filename(None)
    self.delete('1.0', tkinter.END)
    self.save_original()
    self.sync_screen(clean=True)

  def open_file(self, fn):
    if not os.path.exists(fn):
      raise EditorException(i18n.i18n('File %s does not exist') % (fn,))
    self.clear_messages()
    self.delete('1.0', tkinter.END)
    self._set_filename(fn)
    f = open(fn, 'r')
    self.insert(tkinter.INSERT, f.read())
    f.close()
    self.save_original()
    self.focus_set()
    self.sync_screen(clean=True)
    self.mark_set(tkinter.INSERT, '1.0')

  def save_file(self, fn):
    self._set_filename(fn)
    f = open(fn, 'w')
    f.write(self.current_text())
    f.close()
    self.save_original()

  def current_text(self):
    return self.get('1.0', tkinter.END)

  def save_original(self):
    self.original = signature(self.current_text())
    self.edit_reset() # disable undo beyond this point
 
  def text_has_changed(self):
    return signature(self.current_text()) != self.original

  def has_filename(self):
    return self._filename is not None

  def filename(self):
    return self._filename

  def print_current_text(self):
    print('<' + self.current_text() + '>')

  def clear_messages(self, *args, **kwargs):
    self.tag_remove('ERROR', '1.0', tkinter.END)
    if self.message is not None:
      self.message.destructor()
      self.message.destroy()
      self.message = None
      self.refresh_aspect()
      self.focus_set()

  def put_message(self, msg_type, text, relheight=0.25):
    self.clear_messages()
    self.message = tkinter.Frame(self.root)
    msg = tkinter.Text(self.message)
    msg.config(background=Msg_colors[msg_type], font=self._font)
    msg.insert(tkinter.INSERT, text)
    msg.config(state=tkinter.DISABLED)
    msg.place(x=0, rely=0, relheight=1, height=-MsgBtnH, relwidth=1)
    btn = tkinter.Button(self.message)
    btn.config(command=self.clear_messages)
    btn.place(x=0, rely=1, y=-MsgBtnH, height=MsgBtnH, relwidth=1)
    def do_nothing(): pass
    self.message._inner_msg = msg
    self.message.destructor = do_nothing
    self.message.absheight = None
    self.message.relheight = relheight
    self.message.place() 
    self.refresh_aspect()
    self.update()

  def show_search_replace_box(self):
    self.clear_messages()
    self.message = tkinter.Frame(self.root)
    var = tkinter.StringVar()
    if self._last_search_term:
      var.set(self._last_search_term)
    self.message.searchbox = tkinter.Entry(self.message, textvariable=var, font=self._font)
    self.message.searchbox.place(x=0, y=0, relwidth=1, width=-ScrollbarW, relheight=1)
    self.message.searchbox.bind('<KeyRelease>', lambda *x: self.search_find(var.get()))
    self.message.searchbox.bind('<Escape>', lambda *x: self.clear_messages())
    self.message.searchbox.bind('<KeyRelease-Return>', lambda *x: self.search_next_match(var.get()))
    self.message.searchbox.select_range(0, tkinter.END)
    self.message.destructor = lambda *x: self.clean_search_match(var.get())
    self.message.relheight = None
    self.message.absheight = 24
    self.message.place() 
    self.refresh_aspect()
    self.update()
    self.message.searchbox.focus_set()

  def clean_search_match(self, text):
    self._last_search_term = text
    self.tag_remove('search_match', '1.0', tkinter.END)
    self.tag_remove('search_curmatch', '1.0', tkinter.END)

  def search_find(self, text):
    self.clean_search_match(text)
    if len(text) == '': return
    start = '1.0'
    while True:
      pos = self.search(text, start, stopindex=tkinter.END, nocase=True)
      if not pos: break
      self.tag_add('search_match', pos, pos + '+%ic' % (len(text),))
      start = pos + '+1c'

  def search_next_match(self, text):
    self.search_find(text)
    pos = self.search(text, tkinter.INSERT + '+1c', nocase=True)
    if pos:
      posend = pos + '+%ic' % (len(text),)
      self.tag_remove('search_match', pos, posend)
      self.tag_add('search_curmatch', pos, posend)
      self.mark_set(tkinter.INSERT, pos)
      self.see(tkinter.INSERT)

  def show_error(self, exception):
    self.put_message('error', exception.msg, relheight=0.25)
    self._mark_error(exception.area)

  def show_raw_error(self, text):
    self.put_message('error', text, relheight=0.25)

  def show_check_ok(self, text):
    self.put_message('check_ok', text, relheight=0.25)

  def show_result(self, text):
    self.put_message('result', text, relheight=0.25)

  def make_logger(self):
    self.put_message('log', '', relheight=0.25)
    def log(text):
      if not self.message: return
      msg = self.message._inner_msg
      msg.config(state=tkinter.NORMAL)
      msg.insert(tkinter.INSERT, text + '\n')
      msg.yview_moveto('1.0')
      msg.config(state=tkinter.DISABLED)
      self.update()
    return log

  def _mark_error(self, area):
    pos_begin, pos_end = area.interval()
    ibegin = tpos(1, pos_begin)
    iend = tpos(1, pos_end)
    self.focus_set()
    self.mark_set(tkinter.INSERT, ibegin)
    self.see(tkinter.INSERT)
    self.tag_add('ERROR', ibegin, iend)

  # clipboard
  def edit_cut(self, *args, **kwargs):
    self.event_generate('<<Cut>>')

  def edit_copy(self, *args, **kwargs):
    self.event_generate('<<Copy>>')

  def edit_paste(self, *args, **kwargs):
    self.event_generate('<<Paste>>')

  def edit_select_all(self, *args, **kwargs):
    self.tag_add('sel', '1.0', tkinter.END)

  def edit_find(self, *args, **kwargs):
    self.show_search_replace_box()

  # auxiliary methods to handle the scrollbar

  def yview(self, *args, **kwargs):
    tkinter.Text.yview(self, *args, **kwargs)
    self.sync_screen(clean=False)

  def yscroll(self, *args, **kwargs):
    self.scrollbar.set(*args, **kwargs)
    self.sync_screen(clean=False)

  def start_run(self, onstop):
    self.end_run()
    self.progress_bar = gui.progress.ProgressBar(self.statusbar, onstop=onstop)
    self.progress_bar.place(x=0, y=0, relwidth=1, relheight=1)

  def end_run(self):
    if self.progress_bar is None: return
    self.progress_bar.destroy()
    self.progress_bar = None

  def options_set_font(self, font):
    self._font = font
    self.config(font=self._font)
    if self.message:
      self.message._inner_msg.config(font=self._font)

  # Workaround to a presentation issue.
  # The "save file" dialog in app.py generates a
  # Return key event when closed. These methods
  # disable/enable the KeyRelease-Return handler
  # to avoid processing it.
  def disable_return(self):
    def ignore(e):
      return 'break'
    self.bind('<KeyRelease-Return>', ignore)
  def enable_return(self):
    def restore():
      self.bind('<KeyRelease-Return>', self.keyrelease_return)
    self.after(500, restore)

