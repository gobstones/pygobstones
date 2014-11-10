# coding:utf-8
#
# Copyright (C) 2011-2013 Pablo Barenbaum <foones@gmail.com>,
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

import sys
import os
import common.utils
import common.messaging
import gui.gobstones_run as gbs_run


if common.utils.python_major_version() < 3:
    import Tkinter as tkinter
    import tkMessageBox
    import tkSimpleDialog
    import tkFileDialog
    import tkFont
    tkinter.messagebox = tkMessageBox
    tkinter.simpledialog = tkSimpleDialog
    tkinter.filedialog = tkFileDialog
    tkinter.font = tkFont
else:
    import tkinter
    import tkinter.messagebox
    import tkinter.simpledialog
    import tkinter.filedialog
    import tkinter.font

import common.threads
from common.tools import tools
import common.i18n as i18n
from common.utils import SourceException
import common.utils
import gui.editor
import gui.viewer
import gui.config
import common.logtools
import logging

import lang.bnf_parser
import lang.board.formats
import gbs
from lang.gbs_io import GobstonesKeys

GBS_KEY_DICT = {'up': GobstonesKeys.ARROW_UP, 
                         'down': GobstonesKeys.ARROW_DOWN,
                         'left': GobstonesKeys.ARROW_LEFT,
                         'right': GobstonesKeys.ARROW_RIGHT}

def map_event_to_gbs_key(event):
    if event.char != "":
        return ord(event.char)
    elif event.keysym.lower() in GBS_KEY_DICT.keys():
        return GBS_KEY_DICT[event.keysym.lower()]            
    else:
        return event.keycode

#### Main window of the Gobstones GUI

def search_underline(name):
    if '&' in name:
        u = name.index('&')
        return name.replace('&', ''), u
    else:
        return name, None

def command_for(shortcut):
    if shortcut[0] == 'F':
        return '<' + shortcut + '>'
    elif shortcut[0] == '#':
        return None
    else:
        c, l = shortcut.split('+')
        assert c == 'Ctrl'
        return '<Control-' + l.lower() + '>'

def build_menu(menu, root, toplevel):
    menu = menu[:]
    m = tkinter.Menu(root)
    while menu != []:
        name = menu.pop(0)
        
        name, underline = search_underline(name)
        if name == '--':
            m.add_separator()
            continue

        submenu = menu.pop(0)
        if isinstance(submenu, list):
            m.add_cascade(
                label=name,
                menu=build_menu(submenu, m, toplevel),
                underline=underline
            )
            continue
        if isinstance(submenu, tuple):
            cmd, shortcut = submenu
            csh = command_for(shortcut)
            shortcut = shortcut.strip('#')
            if csh is not None:
                toplevel.unbind_class('Text', csh)
                toplevel.bind_all(csh, cmd)
        else:
            cmd = submenu
            shortcut = None
        m.add_command(label=name, command=cmd, underline=underline, accelerator=shortcut)
    return m

def menu_font_family(gui):
    def set_to(fam):
        return lambda *args: gui.set_font_family_to('%s' % (fam,), *args)
    menu = []
    submenu = []
    fams = [x for x in tkinter.font.families()
                        if 'a' <= x[0].lower() and x[0].lower() <= 'z']
    fams = common.utils.seq_sorted(fams, key=lambda n: n.lower())
    for i in range(len(fams)):
          fam = fams[i]
          submenu.append(fam)
          submenu.append((set_to(fam), '#'))
          if i > 0 and i % 20 == 0:
              menu.append(submenu)
              submenu = []
    if submenu != []:
        menu.append(submenu)
    for i in range(len(menu) - 1):
        menu[i].append('(&More...)')
        menu[i].append(menu[i + 1])
    return menu[0]

def menu_font_size(gui):
    def set_to(sz):
        return lambda *args: gui.set_font_size_to(sz, *args)
    menu = []
    for i in [8, 9, 10, 12, 14, 16, 18, 20, 24, 36, 72]:
        menu.extend([str(i), set_to(i)])
    return menu

class InputDialog(tkinter.Toplevel):
    CTRL_D = 4
    def __init__(self, parent):
        tkinter.Toplevel.__init__(self, parent)
        self.value_holder = tkinter.IntVar(0)        
        self.label = tkinter.Label(self, text="Press a key!")
        self.bind("<Destroy>", self._destroy)
    def read_key(self):
        self.label.pack()
        self.handler_id = self.bind("<Key>", self.key_pressed)
        self.master.wait_variable(self.value_holder)
        return self.value_holder.get()
    def _destroy(self, event):
        self.value_holder.set(InputDialog.CTRL_D)
    def key_pressed(self, event):
        self.value_holder.set(map_event_to_gbs_key(event))
        self.unbind("<Key>", self.handler_id)
        self.label.pack_forget()
        if self.value_holder.get() == InputDialog.CTRL_D:
            self.destroy()
        

class GUI(tkinter.Tk):

    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        lang.setGrammar(lang.GobstonesOptions.LangVersion.XGobstones)

        self._font = gui.config.DefaultFont
        self.tools = tools

        eframe = tkinter.Frame(self)
        self.editor = gui.editor.Editor(self.tools, eframe, font=self._font)
        eframe.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)

        self.viewer = None
        self.input_dialog = None

        self.menu = self._menubar()
        
        self.unbind_class('Text', '<Control-plus>')
        self.bind_all('<Control-plus>', self.inc_font_size)
        self.unbind_class('Text', '<Control-minus>')
        self.bind_all('<Control-minus>', self.dec_font_size)

        self._init_filetypes()

        self.bind_all('<Escape>', self.editor.clear_messages)

        self.file_new()
        menubar = build_menu(self.menu, self, self)
        self.config(menu=menubar)

        self._running = False
        self._prepare_for_next_run()
        self._last_alarm_id = None
        self._last_directory = None

        self.editor.focus_set()

    def _running_start(self):
        self._running = True
        self._last_alarm_id = None

    def _running_end(self):
        self._running = False
        if self._last_alarm_id:
            self.after_cancel(self._last_alarm_id)
        self._last_alarm_id = None

    def _menubar(self):
        return [
            i18n.i18n('&File'), [
                i18n.i18n('&New'), (self.file_new, 'Ctrl+N'),
                i18n.i18n('&Open'), (self.file_open, 'Ctrl+O'),
                i18n.i18n('&Save'), (self.file_save, 'Ctrl+S'),
                i18n.i18n('Save &as...'), self.file_save_as,
                '--',
                i18n.i18n('&Quit'), (self.file_quit, 'Ctrl+Q'),
            ],
            i18n.i18n('&Edit'), [
                i18n.i18n('&Undo'), (self.editor.edit_undo, '#Ctrl+Z'),
                i18n.i18n('&Redo'), (self.editor.edit_redo, '#Ctrl+Shift+Z'),
                '--',
                i18n.i18n('Cu&t'), (self.editor.edit_cut, '#Ctrl+X'),
                i18n.i18n('&Copy'), (self.editor.edit_copy, '#Ctrl+C'),
                i18n.i18n('&Paste'), (self.editor.edit_paste, '#Ctrl+V'),
                i18n.i18n('Select &All'), (self.editor.edit_select_all, 'Ctrl+A'),
                '--',
                i18n.i18n('&Find'), (self.editor.edit_find, 'Ctrl+F'),
                '--',
                i18n.i18n('&Indent region'), (self.editor.indent_region, 'Ctrl+L'),
                i18n.i18n('&Dedent region'), (self.editor.dedent_region, 'Ctrl+H'),
                '--',
                i18n.i18n('&Font family'), menu_font_family(self),
                i18n.i18n('Font &size'), menu_font_size(self),
            ],
            i18n.i18n('&Gobstones'), [
                i18n.i18n('&Run'), (self.gobstones_start_run, 'F5'),
                i18n.i18n('&Check'), (self.gobstones_check, 'F10'),
            ],
            i18n.i18n('&Board'), [
                i18n.i18n('&Empty board'), (self.board_empty, 'Ctrl+E'),
                i18n.i18n('&Random board'), (lambda *args: self.board_random_contents(), 'Ctrl+R'),
                '--',
                i18n.i18n('&Random board size'), (lambda *args: self.board_random_full(), 'Ctrl+I'),
                i18n.i18n('&Change size'), (self.board_change_size, 'Ctrl+T'),
                '--',
                i18n.i18n('&Load board'), (lambda *args: self.board_load(), 'Ctrl+B'),
                i18n.i18n('&Save board'), (lambda *args: self.board_save(), 'Ctrl+G'),
            ],
            '--',
            i18n.i18n('&Help'), [
                i18n.i18n('&Manual'), self.manual,
                i18n.i18n('&Version'), self.version,
                i18n.i18n('&License'), self.license,
            ],
        ]

    def _init_filetypes(self):
        self.filetypes = {
            'gbs': [
                (i18n.i18n('Gobstones source'), '*.gbs', 'TEXT'),
                (i18n.i18n('All files'), '*'),
            ],
        }
        self.filetypes['board_load'] = [
                (i18n.i18n('Gobstones board'), '*.gbb', 'TEXT'),
                (i18n.i18n('Gobstones board (old format)'), '*.gbt', 'TEXT'),
                (i18n.i18n('TeX/LaTeX file'), '*.tex', 'TEXT'),
        ]
        self.filetypes['board_save'] = self.filetypes['board_load'][:]
        self.filetypes['board_save'].append(
                (i18n.i18n('HTML file'), '*.html', 'TEXT')
        )
        self.filetypes['board_save'].append(
                (i18n.i18n('FIG image file'), '*.fig', 'TEXT')
        )
        self.filetypes['board_load'].append(
                (i18n.i18n('All files'), '*'),
        )
        self.filetypes['board_save'].append(
                (i18n.i18n('All files'), '*'),
        )

    def _file_close(self):
        if self.editor.text_has_changed():
            ans = tkinter.messagebox.askyesnocancel(
                i18n.i18n('File not saved'),
                i18n.i18n('File has not been saved.\nSave it now?'))
            if ans is None: return False
            if ans == True:
                if not self.file_save(): return False
        self.editor.new_file()    
        return True

    def file_new(self, *args):
        if not self._file_close(): return
        self._fn_title(i18n.i18n('Untitled'))

    def file_open(self, *args):
        fn = tkinter.filedialog.askopenfilename(parent=self,
                        title=i18n.i18n('Open file'),
                        filetypes=self.filetypes['gbs'],
                        initialdir=self._last_directory)
        self.file_open_fn(fn)

    def file_open_fn(self, fn):
        if fn is None or fn == (): return
        if os.path.exists(fn):
            self._last_directory = os.path.dirname(fn)
            if not self._file_close(): return
            self.editor.open_file(fn)
            self._fn_title(fn)

    def file_quit(self, *args):
        if not self._file_close(): return
        self.destroy()

    def file_save(self, *args):
        if self.editor.has_filename():
            self.editor.save_file(self.editor.filename())
            return True
        else:
            return self.file_save_as()

    def file_save_as(self, *args):
        self.editor.disable_return()
        fn = tkinter.filedialog.asksaveasfilename(parent=self,
                        title=i18n.i18n('Save file'),
                        filetypes=self.filetypes['gbs'],
                        initialdir=self._last_directory)
        self.editor.enable_return()
        if fn is None or fn == (): return False
        fn = fn.strip(' ')
        if fn == '': return False
        if '.' not in fn:
            fn += '.gbs'
        self._last_directory = os.path.dirname(fn)
        self.editor.save_file(fn)
        self._fn_title(fn)
        return True

    def force_file_save(self, *args):
        if self.editor.has_filename():
            self.editor.save_file(self.editor.filename())
            return True
        else:
            ans = tkinter.messagebox.askyesno(
                i18n.i18n('Source must be saved'),
                i18n.i18n('Source must be saved.\nOk to save?'))
            if ans == True:
                return self.file_save_as()
            else:
                return False

    def _fn_title(self, fn):
        self.title('Gobstones - ' + fn)

    def _filename_or_untitled(self):
        if self.editor.has_filename():
            return self.editor.filename()
        else:
            return i18n.i18n('Untitled')

    def gobstones_success(self, board_repr, result):
        self.tools.board_format.from_string(board_repr, self.viewer.board1)
        self.gobstones_end_run(result)

    def gobstones_partial(self, board_repr):    
        self.tools.board_format.from_string(board_repr, self.viewer.board1)
        self.viewer.revalidate()
        if self.viewer.visible_board != 1:
            self.viewer.show_board1()
        self.viewer.refresh()

    class ValueHolder(object):
        def __init__(self, value=None):
            self.value = value
    
    def gobstones_read_input(self):
        if not self.input_dialog:
            self.input_dialog = InputDialog(self)
        return self.input_dialog.read_key()

    def _prepare_for_next_run(self):        
        handler = gbs_run.GobstonesRunHandler(self.gobstones_success, self.gobstones_fail_run, 
                                              self.editor.make_logger(), self.gobstones_partial, 
                                              self.gobstones_read_input)
        self._run = gbs_run.GobstonesRun(handler)

    def gobstones_check(self, *args):
        self.editor.clear_messages()
        try:
            gobstones = lang.Gobstones(lang.GobstonesOptions("strict"))            
            tree = gobstones.parse(self.editor.current_text(), self._filename_or_untitled())
            gobstones.explode_macros(tree)
            gobstones.check(tree)
            self.editor.show_check_ok(i18n.i18n('All checks ok'))
        except SourceException as exception:
            self.editor.show_error(exception)

    def gobstones_start_run(self, *args):
        if self._running:
            return
        
        if self.input_dialog:
            self.input_dialog.destroy()
            self.input_dialog = None
            
        self._running_start()

        self.editor.start_run(onstop=self._run.abort)
        self.open_viewer()
        self.viewer.prepare_for_run()
        self.viewer.invalidate()

        if self._run.running:
            self._prepare_for_next_run()

        self._run.start(self._filename_or_untitled(), self.editor.current_text(), self.tools.board_format.to_string(self.viewer.board1))

        self._last_alarm_id = self.after(gui.config.TickDelay, self.gobstones_continue_run)

    def gobstones_continue_run(self):
        if not self._run.running: return
        try:
            self._run.continue_run()
        except common.threads.queue_empty as e:
            self._last_alarm_id = self.after(gui.config.TickDelay, self.gobstones_continue_run)

    def gobstones_end_run(self, result):
        self._run.handler.log(i18n.i18n('Program execution finished.'))
        self._prepare_for_next_run()
        self.editor.end_run()
        self.viewer.revalidate()
        if len(result) > 0:
            result_msg = ['%s -> %s\n' % (var, val) for var, val in result]
            self.editor.show_result(''.join(result_msg))
        else:
            self.editor.clear_messages()
        if self.viewer:
            self.viewer.refresh()
            self.viewer.show_board1()
        self._running_end()

    def gobstones_fail_run(self, exception):
        self._prepare_for_next_run()
        self.editor.end_run()
        self.editor.show_error(exception)
        if self.viewer:
            if isinstance(exception, common.utils.DynamicException):
                self.viewer.show_dynamic_error()
            else:
                self.viewer.show_static_error()
        self._running_end()

    def open_viewer(self):
        if not self.viewer:
            self.viewer = gui.viewer.BoardViewer(self.tools, parent_gui=self, font=self._font)
            self.viewer.geometry(self.tools.BoardViewerGeometry)
            self.viewer.protocol("WM_DELETE_WINDOW", self.close_viewer)

    def close_viewer(self):
        if not self.viewer: return
        self.viewer.destroy()
        self.viewer = None

    def board_empty(self, *args):
        if not self.viewer:
            self.open_viewer()
        self.viewer.clear()
        self.viewer.show_board0()

    def board_random_contents(self):
        if not self.viewer:
            self.open_viewer()
        self.viewer.randomize()
        self.viewer.show_board0()

    def board_random_full(self):
        if not self.viewer:
            self.open_viewer()
        self.tools.DefaultBoardSize = 'random'
        self.viewer.randomize()
        self.viewer.show_board0()

    def board_change_size(self, *args):
        if self.tools.DefaultBoardSize == 'random':
            w, h = 9, 9
        else:
            w, h = self.tools.DefaultBoardSize

        # ask for size
        msg = i18n.i18n('Invalid board size')
        nw = tkinter.simpledialog.askstring(
                      i18n.i18n('Change board size'),
                      i18n.i18n('Width:'),
                      initialvalue='%s' % (w,))
        nh = tkinter.simpledialog.askstring(
                      i18n.i18n('Change board size'),
                      i18n.i18n('Height:'),
                      initialvalue='%s' % (h,))

        if not common.utils.is_int(nw) or not common.utils.is_int(nh):
            return self.show_string_error(msg)
        w, h = int(nw), int(nh)
        if w == 0 or h == 0 or w > 200 or h > 200:
            return self.show_string_error(msg)

        self.tools.DefaultBoardSize = w, h
        # resize board
        if not self.viewer:
            self.open_viewer()
        self.viewer.randomize()
        self.viewer.show_board0()

    def board_load(self):
        fn = tkinter.filedialog.askopenfilename(parent=self,
                        title=i18n.i18n('Open file'),
                        filetypes=self.filetypes['board_load'],
                        initialdir=self._last_directory)
        self.board_load_fn(fn)

    def board_load_fn(self, fn):
        if fn is None: return
        if not os.path.exists(fn):
            return
        self._last_directory = os.path.dirname(fn)
        if not self.viewer:
            self.open_viewer()
        fmt = lang.board.formats.format_for(fn)
        if self.viewer.open_file(fn, fmt):
            self.viewer.show_board0()

    def board_save(self):
        if not self.viewer:
            self.open_viewer()
        num = self.viewer.visible_board
        if num is None: num = 0

        self.editor.disable_return()
        fn = tkinter.filedialog.asksaveasfilename(parent=self,
                        title=i18n.i18n('Save file'),
                        filetypes=self.filetypes['board_save'],
                        initialdir=self._last_directory)
        self.editor.enable_return()

        if fn is None or fn == (): return False
        fn = fn.strip(' ')
        if fn == '': return False
        if '.' not in fn:
            fn += '.gbb'
        self._last_directory = os.path.dirname(fn)
        fmt = lang.board.formats.format_for(fn)
        self.viewer.save_board(fn, num, fmt)

    def destroy(self):
        self.close_viewer()
        tkinter.Tk.destroy(self)
        self._end_worker()

    def _end_worker(self):
        if self._run is not None:
            self._run.end()

    def version(self, *args):
        vn = common.utils.version_number()
        tkinter.messagebox.showinfo(
                i18n.i18n('Gobstones version') + ' ' + vn,
                i18n.i18n('I18N_gbs_version(%s)') % (vn,))

    def license(self, *args):
        common.utils.open_html(common.LicenseFile)

    def manual(self, *args):
        common.utils.open_html('http://pygobstones.wordpress.com/manual')

    def set_font_family_to(self, family, *args):
        self._font = (family, self._font[1])
        self.set_font()

    def set_font_size_to(self, size, *args):
        self._font = (self._font[0], size)
        self.set_font()

    def inc_font_size(self, *args):
        if self._font[1] < 100:
            self._font = (self._font[0], self._font[1] + 1)
            self.set_font()

    def dec_font_size(self, *args):
        if self._font[1] > 8:
            self._font = (self._font[0], self._font[1] - 1)
            self.set_font()

    def set_font(self):
        font = self._font
        self.editor.options_set_font(font)
        if self.viewer:
            self.viewer.set_font(font)

    def show_string_error(self, msg):
        self.editor.show_error(
            common.utils.SourceException(
                msg,
                lang.bnf_parser.fake_bof()))

