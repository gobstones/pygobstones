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
import gui.config

Colors = {
    'board_bg': 'white',
    'board_bg_readonly': 'lightgray',
    'grid': 'brown',
    'header': 'orange',
    'header_back': 'lightyellow',

    'stone_border0': 'I18N_stone_border0',
    'stone_border1': 'I18N_stone_border1',
    'stone_border2': 'I18N_stone_border2',
    'stone_border3': 'I18N_stone_border3',

    'stone_fill0': 'I18N_stone_fill0',
    'stone_fill1': 'I18N_stone_fill1',
    'stone_fill2': 'I18N_stone_fill2',
    'stone_fill3': 'I18N_stone_fill3',

    'mark0': 'I18N_mark0',
    'mark1': 'I18N_mark1',
    'mark2': 'I18N_mark2',
    'mark3': 'I18N_mark3',
}

class Mark(object):
    def __init__(self, item, x, y, color):
        self.item = item
        self.x = int(x)
        self.y = int(y)
        self.color = color

class CoordinateTranslator(object):
    def __init__(self, board, hscroll, vscroll):
        self._xmargin = 30
        self._ymargin = 30
        self._board = board
        self._zoom_x0 = 0
        self._zoom_y0 = 0
        self._zoom_x1 = 9
        self._zoom_y1 = 9
        self._container_size = None
        self._h_scroll = hscroll
        self._v_scroll = vscroll

    def container_size(self, size):
        self._container_size = size

    def cell_pixel_width(self):
        return (self._container_size[0] - 2 * self._xmargin) // (self._zoom_x1 - self._zoom_x0)

    def cell_pixel_height(self):
        return (self._container_size[1] - 2 * self._ymargin) // (self._zoom_y1 - self._zoom_y0)

    def cell_side(self):
        return max(min(self.cell_pixel_width(), self.cell_pixel_height()), 10)

    def bottom(self):
        x0, y0, x1, y1 = self.visible_cells()
        side = self.cell_side()
        return self._ymargin + (y1 - y0) * side

    def visible_cells(self):
        bw, bh = self._board.size
        bw = min(self._zoom_x1, bw)
        bh = min(self._zoom_y1, bh)
        return [self._zoom_x0, self._zoom_y0, bw, bh]

    def vertical_lines(self):
        w, h = self._board.size
        x0, y0, x1, y1 = self.visible_cells()
        px = self._xmargin
        side = self.cell_side()
        py0 = self.bottom()
        py1 = py0 - (y1 - y0) * side
        for ln in range(x0, x1 + 1):
            dashed = False
            if (ln == x0 and x0 != 0) or (ln == x1 and x1 != w):
                dashed = True
            yield [px, py0, px, py1, dashed]
            px += side

    def horizontal_lines(self):
        w, h = self._board.size
        x0, y0, x1, y1 = self.visible_cells()
        py = self.bottom()
        side = self.cell_side()
        px0 = self._xmargin
        px1 = px0 + (x1 - x0) * side
        for ln in range(y0, y1 + 1):
            dashed = False
            if (ln == y0 and y0 != 0) or (ln == y1 and y1 != h):
                dashed = True
            yield [px0, py, px1, py, dashed]
            py -= side

    def is_visible(self, x, y):
        x0, y0, x1, y1 = self.visible_cells()
        return x0 <= x and x < x1 and \
                      y0 <= y and y < y1

    def cell_box(self, x, y):
        side = self.cell_side()
        x0, y0, x1, y1 = self.visible_cells()
        px0 = self._xmargin + (x - x0) * side
        px1 = px0 + side
        py0 = self.bottom() - (y - y0) * side
        py1 = py0 - side
        return [min(px0, px1), min(py0, py1),
                        max(px0, px1), max(py0, py1)]

    def row_labels(self):
        x0, y0, x1, y1 = self.visible_cells()
        for y in range(y0, y1):
            sign = -1
            for x in [x0, x1]:
                px0, py0, px1, py1 = self.cell_box(x, y)
                xx = px0 + sign * self._xmargin // 2
                yy = (py0 + py1) // 2
                sign = -sign
                yield str(y), xx, yy

    def column_labels(self):
        x0, y0, x1, y1 = self.visible_cells()
        for x in range(x0, x1):
            sign = 1
            for y in [y0, y1]:
                px0, py0, px1, py1 = self.cell_box(x, y)
                xx = (px0 + px1) // 2
                yy = py1 + sign * self._ymargin // 2
                sign = -sign
                yield str(x), xx, yy

    def inverse(self, px, py):
        x0, y0, x1, y1 = self.visible_cells()
        side = self.cell_side()
        mx = px - self._xmargin
        my = self.bottom() - py
        x = mx // side + x0
        y = my // side + y0
        half_x = mx <= side * (x - x0 + 0.5)
        half_y = my <= side * (y - y0 + 0.5)
        if self.is_visible(x, y):
            return x, y, half_x, half_y
        else:
            return None

    def zoom_in(self):
        xok = self._zoom_x1 > self._zoom_x0 + 1
        yok = self._zoom_y1 > self._zoom_y0 + 1
        if xok:
            self._zoom_x1 -= 1
        if yok:
            self._zoom_y1 -= 1
        self.center_head()

    def zoom_out(self):
        w, h = self._board.size
        distx = self._zoom_x1 - self._zoom_x0
        disty = self._zoom_y1 - self._zoom_y0
        xok = distx < 20
        yok = disty < 20
        if xok:
            if self._zoom_x1 < w:
                self._zoom_x1 += 1
            elif self._zoom_x0 > 0:
                self._zoom_x0 -= 1
        if yok:
            if self._zoom_y1 < h:
                self._zoom_y1 += 1
            elif self._zoom_y0 > 0:
                self._zoom_y0 -= 1
        self.center_head()

    def center_head(self):
        y, x = self._board.head
        distx = self._zoom_x1 - self._zoom_x0
        disty = self._zoom_y1 - self._zoom_y0
        self._place_viewport(x - distx // 2, y - disty // 2)

    def scroll(self, dx, dy):
        self._place_viewport(self._zoom_x0 + dx, self._zoom_y0 + dy)

    def move_to(self, orientation, place):
        w, h = self._board.size
        x0, y0 = self._zoom_x0, self._zoom_y0 
        if orientation == 'h':
            x0 = int(w * place)
        elif orientation == 'v':
            disty = self._zoom_y1 - self._zoom_y0
            y0 = int(h - disty - h * place)
        self._place_viewport(x0, y0)

    def _place_viewport(self, x, y):
        w, h = self._board.size
        distx = self._zoom_x1 - self._zoom_x0
        disty = self._zoom_y1 - self._zoom_y0
        self._zoom_x0 = max(0, min(x, w - distx))
        self._zoom_y0 = max(0, min(y, h - disty))
        self._zoom_x1 = self._zoom_x0 + distx
        self._zoom_y1 = self._zoom_y0 + disty
        self._update_scrollbars()

    def _update_scrollbars(self):
        w, h = self._board.size
        x0, y0, x1, y1 = self.visible_cells()
        self._h_scroll.set(float(x0) / w, float(x1) / w)
        self._v_scroll.set(1.0 - float(y1) / h, 1.0 - float(y0) / h)

    def zoom_copy_from(self, other):
        self._zoom_x0 = other._zoom_x0
        self._zoom_x1 = other._zoom_x1
        self._zoom_y0 = other._zoom_y0
        self._zoom_y1 = other._zoom_y1

    def autoadjust(self):
        w, h = self._board.size
        self._zoom_x0 = 0
        self._zoom_x1 = min(w, 20)
        self._zoom_y0 = 0
        self._zoom_y1 = min(h, 20)
        self.center_head()

class BoardFrame(tkinter.Canvas):

    def __init__(self, tools, board, readonly, font, h_scroll, v_scroll, *args, **kwargs):
        if 'on_change' in kwargs:
            self.on_change = kwargs['on_change']
            del kwargs['on_change']
        else:
            self.on_change = None

        tkinter.Canvas.__init__(self, *args, **kwargs)
        self.tools = tools
        self.board = board
        if readonly:
            self.config(bg=Colors['board_bg_readonly'])
        else:
            self.config(bg=Colors['board_bg'])
        self.bind('<Configure>', self.refresh_aspect)
        self.bind('<Motion>', self.mouse_move)
        self.bind('<Button-1>', self.mouse_button1) # left
        self.bind('<Button-2>', self.mouse_button2) # middle
        self.bind('<Button-3>', self.mouse_button3) # right
        self.mark = None
        self.readonly = readonly
        self.has_changed = False
        self._font = font

        self._coordtran = CoordinateTranslator(self.board, h_scroll, v_scroll)

    def refresh_aspect(self, *args):
        self.delete(tkinter.ALL)

        if self.board.invalid: return

        self._coordtran.container_size((self.winfo_width(), self.winfo_height()))

        def dashed_if(d):
          if d:
              return {'fill': 'gray', 'dash': (2, 2)}
          else:
              return {'fill': Colors['grid']}

        # vertical lines
        for x0, y0, x1, y1, d in self._coordtran.vertical_lines():
              self.create_line(x0, y0, x1, y1,
                  width=2, **dashed_if(d))

        # horizontal lines
        for x0, y0, x1, y1, d in self._coordtran.horizontal_lines():
              self.create_line(x0, y0, x1, y1,
                  width=2, **dashed_if(d))

        # head
        hy, hx = self.board.head
        if self._coordtran.is_visible(hx, hy):
            self.draw_head(*self._coordtran.cell_box(hx, hy))

        # cell contents
        x0, y0, x1, y1 = self._coordtran.visible_cells()
        for x in range(x0, x1):
            for y in range(y0, y1):
                self.draw_cell(self.board.cells[y][x],
                               *self._coordtran.cell_box(x, y))
        self._draw_labels()

    def _draw_labels(self):
        w, h = self.board.size
        for lab, x, y in self._coordtran.column_labels():
            self.create_text(x, y, text=lab, font=self._font, justify=tkinter.CENTER)
        for lab, x, y in self._coordtran.row_labels():
            self.create_text(x, y, text=lab, font=self._font, justify=tkinter.CENTER)

    def submit_change(self):
        self.has_changed = True
        if self.on_change:
            self.on_change()

    def mouse_move(self, event):
        if self.board.invalid: return
        w, h = self.board.size
        xy = self._coordtran.inverse(event.x, event.y)
        if xy is None:
            self.clear_mark()
        else:
            x, y, half_x, half_y = xy
            col = 0
            if half_x:
                col += 1
            if half_y:
                col += 2
            self.add_mark(x, y, col)

    def mouse_button1(self, event):
        # left button: put stones
        if not self.mark: return
        if event.state & 7:
            self.mouse_button3(event)
            return
        x, y, col = self.mark.x, self.mark.y, self.mark.color
        self.board.cells[y][x].put(col)
        self.submit_change()
        self.refresh_aspect()
        self.add_mark(x, y, col)

    def mouse_button2(self, event):
        # middle button: move head
        if not self.mark: return
        if event.state & 7:
            self.mouse_button3(event)
            return
        x, y, col = self.mark.x, self.mark.y, self.mark.color
        self.board.head = (y, x)
        self.refresh_aspect()
        self.add_mark(x, y, col)
        self.submit_change()

    def mouse_button3(self, event):
        # right button: take stones
        if not self.mark: return
        x, y, col = self.mark.x, self.mark.y, self.mark.color
        n = self.board.cells[y][x].num_stones(col)
        if n > 0:
            self.board.cells[y][x].take(col)
            self.submit_change()
        self.refresh_aspect()
        self.add_mark(x, y, col)

    def keypress(self, event):
        if self.readonly: return
        if event.char == '': return
        if self.mark:
            x, y, col = self.mark.x, self.mark.y, self.mark.color
        else:
            y, x = self.board.head
            col = None
        if event.char in '0123456789' and col is not None:
            n = int(event.char)
            self.board.cells[y][x].set_num_stones(col, n)
            self.submit_change()
            self.refresh_aspect()
            self.add_mark(x, y, col)
        elif event.char == ' ':
            if col is not None:
                self.board.cells[y][x].set_num_stones(col, 0)
            else:
                for i in range(4):
                    self.board.cells[y][x].set_num_stones(i, 0)
            self.submit_change()
            self.refresh_aspect()
            if col is not None:
                self.add_mark(x, y, col)
        elif event.char == '+' and col is not None:
            self.mouse_button1(event)
        elif event.char == '-' and col is not None:
            self.mouse_button3(event)
        elif event.char in 'hH' and col is not None:
            self.board.head = (y, x)
            self.refresh_aspect()
            self.add_mark(x, y, col)
            self.submit_change()
        else:
            cs = self.tools.builtins.COLORS_BY_INITIAL
            cs_names = ''.join(cs.keys())
            if event.char.lower() in cs_names:
                col = cs[event.char.lower()]
                y, x = self.board.head
                if event.char.lower() == event.char:
                    self.board.put_stone(col)
                elif self.board.exist_stones(col):
                    self.board.take_stone(col)
                self.submit_change()
                self.refresh_aspect()
                self.add_mark(x, y, col.ord())

    def keypress_cursor(self, direction, event):
        if self.readonly: return
        if self.board.can_move(direction):
            self.board.move(direction)
            self.submit_change()
            self.clear_mark()
            self.refresh_aspect()

    def grandmove(self, kw):
        if self.readonly: return
        w, h = self.board.size
        y, x = self.board.head
        if kw == 'home':
            pos = (0, y)
        elif kw == 'end':
            pos = (w - 1, y)
        if kw == 'up':
            pos = (x, h - 1)
        elif kw == 'down':
            pos = (x, 0)
        self.board.goto(*pos)
        self.submit_change()
        self.clear_mark()
        self.refresh_aspect()

    def clear_mark(self):
        if self.mark:
            self.delete(self.mark.item)
            self.mark = None

    def add_mark(self, x, y, col):
        if self.readonly: return
        self.clear_mark()
        fill = i18n.i18n(Colors['mark%i' % (col,)])
        mx0, my0, mx1, my1 = self._coordtran.cell_box(x, y)
        if col < 2: 
            my1 = (my0 + my1) // 2
        else:
            my0 = (my0 + my1) // 2
        if col % 2 == 0: 
            mx0 = (mx0 + mx1) // 2
        else:
            mx1 = (mx0 + mx1) // 2
        item = self.create_rectangle(mx0, my0, mx1, my1,
                          outline=fill, fill=fill)
        self.tag_lower(item)
        self.tag_lower(self.item_head)
        self.mark = Mark(item, x, y, col)

    def draw_cell(self, cell, x0, y0, x1, y1):
        for col, count in cell.stones.items():
            assert col in [0, 1, 2, 3]
            sx0 = x0
            sx1 = x1
            sy0 = y0
            sy1 = y1
            if col < 2: 
                sy1 = (y0 + y1) // 2
            else:
                sy0 = (y0 + y1) // 2
            if col % 2 == 0: 
                sx0 = (x0 + x1) // 2
            else:
                sx1 = (x0 + x1) // 2
            self.draw_stone(sx0, sy0, sx1, sy1, col, count)

    def draw_stone(self, x0, y0, x1, y1, col, count):
        if count == 0: return
        sm = (x1 - x0) // 8
        fill = i18n.i18n(Colors['stone_fill%i' % (col,)])
        outline = i18n.i18n(Colors['stone_border%i' % (col,)])
        self.create_oval(x0 + sm, y0 + sm, x1 - sm, y1 - sm,
                                          outline=outline, fill=fill, width=1)
        self.create_text((x0 + x1) // 2, (y0 + y1) // 2,
                                          font=self._font,
                                          text=str(count), justify=tkinter.CENTER)

    def draw_head(self, x0, y0, x1, y1):
        sm = (x1 - x0) // 10
        smm = max(1, sm // 2)
        a = x0 + ((x1 - x0) % sm) // 2
        self.item_head = self.create_rectangle(x0, y0, x1, y1, fill=Colors['header_back'], width=2)
        self.tag_lower(self.item_head)
        for x in range(a, x1 + 1, sm):
            self.create_line(x - smm, y0 - smm, x + smm, y0 + smm, fill=Colors['header'], width=2)
            self.create_line(x + smm, y0 - smm, x - smm, y0 + smm, fill=Colors['header'], width=2)
            self.create_line(x - smm, y1 - smm, x + smm, y1 + smm, fill=Colors['header'], width=2)
            self.create_line(x + smm, y1 - smm, x - smm, y1 + smm, fill=Colors['header'], width=2)
        a = y0 + ((y1 - y0) % sm) // 2
        for y in range(a, y1 + 1, sm):
            self.create_line(x0 - smm, y - smm, x0 + smm, y + smm, fill=Colors['header'], width=2)
            self.create_line(x0 - smm, y + smm, x0 + smm, y - smm, fill=Colors['header'], width=2)
            self.create_line(x1 - smm, y - smm, x1 + smm, y + smm, fill=Colors['header'], width=2)
            self.create_line(x1 - smm, y + smm, x1 + smm, y - smm, fill=Colors['header'], width=2)

    def set_font(self, font):
        self._font = font

    def zoom_in(self):
        self._coordtran.zoom_in()

    def zoom_out(self):
        self._coordtran.zoom_out()

    def zoom_copy_from(self, other):
        self._coordtran.zoom_copy_from(other._coordtran)

    def scroll(self, dx, dy):
        self._coordtran.scroll(dx, dy)

    def move_to(self, orientation, place):
        self._coordtran.move_to(orientation, place)

    def center_head(self):
        self._coordtran.center_head()

    def autoadjust(self):
        self._coordtran.autoadjust()

class SpriteBoardFrame(BoardFrame):
    def __init__(self, *args, **kwargs):
        BoardFrame.__init__(self, *args, **kwargs)
        self._image_table = {}

    def draw_stone(self, x0, y0, x1, y1, col, count):
#        col_initial = self.tools.builtins.Color(col).name()[0]
#        identifier = '%s%s' % (count, col_initial)
#        filename = '%s.gif' % (identifier,)
#        if identifier in self._image_table or os.path.exists(filename):
#            if identifier not in self._image_table:
#                #self._image_table[identifier] = tkinter.PhotoImage(self, file=filename)
#                #self._image_table[identifier] = tkinter.PhotoImage(file=filename)
#                self._image_table[identifier] = tkinter.PhotoImage(file=filename)
#            image = self._image_table[identifier]
#            self.create_image(x0, y0, image=image)
#        else:
#            BoardFrame.draw_stone(self, x0, y0, x1, y1, col, count)
        BoardFrame.draw_stone(self, x0, y0, x1, y1, col, count)

class BoardViewer(tkinter.Tk):

    def __init__(self, tools, parent_gui=None, font=gui.config.DefaultFont, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.tools = tools
        self.parent_gui = parent_gui
        self._font = font

        bframe = tkinter.Frame(self)
        ti = i18n.i18n('Initial board')
        tf = i18n.i18n('Final board')
        self.button0 = tkinter.Button(bframe, text=ti, command=self.show_board0)
        self.button1 = tkinter.Button(bframe, text=tf, command=self.show_board1)
        self.button0.pack(side=tkinter.LEFT)
        self.button1.pack(side=tkinter.LEFT)

        self.bind_all('<KeyPress>', self.keypress)
        self.bind_all('<z>', self.board_zoom_out)
        self.bind_all('<x>', self.board_zoom_in)
        self.bind_all('<KeyPress-Up>',
            lambda ev: self.keypress_cursor(self.tools.builtins.NORTH, ev))
        self.bind_all('<KeyPress-Down>',
            lambda ev: self.keypress_cursor(self.tools.builtins.SOUTH, ev))
        self.bind_all('<KeyPress-Left>',
            lambda ev: self.keypress_cursor(self.tools.builtins.WEST, ev))
        self.bind_all('<KeyPress-Right>',
            lambda ev: self.keypress_cursor(self.tools.builtins.EAST, ev))
        self.bind_all('<Home>', lambda ev: self.grandmove('home'))
        self.bind_all('<End>', lambda ev: self.grandmove('end'))
        self.bind_all('<Prior>', lambda ev: self.grandmove('up'))
        self.bind_all('<Next>', lambda ev: self.grandmove('down'))
        bframe.pack(side=tkinter.TOP, fill=tkinter.X)

        self.board0 = self.tools.Board((1, 1))
        self.board0.randomize_full()

        self.board1 = self.tools.Board((1, 1))
        self.reset_board1()

        self._build_scrolled_board_frame()
        self.err_frame = None

        self.show_board0()
        self.visible_board = None

        self.filename = None

        if self.parent_gui:
            self.bind_all('<Control-e>', self.parent_gui.board_empty)
            self.bind_all('<Control-i>', lambda *args: self.parent_gui.board_random_full())
            self.bind_all('<Control-r>', lambda *args: self.parent_gui.board_random_contents())
            self.bind_all('<Control-t>', self.parent_gui.board_change_size)
            self.bind_all('<Control-b>', lambda *args: self.parent_gui.board_load())
            self.bind_all('<Control-g>', lambda *args: self.parent_gui.board_save())
            self.bind_all('<Control-n>', self.parent_gui.file_new)
            self.bind_all('<Control-o>', self.parent_gui.file_open)
            self.bind_all('<Control-s>', self.parent_gui.file_save)
            self.bind_all('<F5>', self.parent_gui.gobstones_start_run)
            self.bind_all('<F10>', self.parent_gui.gobstones_check)

    def _fn_title(self, fn):
        self.title(i18n.i18n('Board viewer') + ' - ' + fn)

    def _build_scrolled_board_frame(self):
        self.scrolled_board_frame = tkinter.Frame(self)
        self.scrolled_board_frame.grid_rowconfigure(0, weight=1)
        self.scrolled_board_frame.grid_columnconfigure(0, weight=1)

        self.v_scroll = tkinter.Scrollbar(self.scrolled_board_frame)
        self.v_scroll.grid(row=0, column=1, sticky=tkinter.N + tkinter.S)

        self.h_scroll = tkinter.Scrollbar(self.scrolled_board_frame, orient=tkinter.HORIZONTAL)
        self.h_scroll.grid(row=1, column=0, sticky=tkinter.E + tkinter.W)

        self.board_frame = tkinter.Frame(self.scrolled_board_frame)
        self.board1_frame = SpriteBoardFrame(
            self.tools, self.board1, True, self._font,
            self.h_scroll, self.v_scroll,
            self.board_frame
        )
        self.board0_frame = SpriteBoardFrame(
            self.tools, self.board0, False,  self._font,
            self.h_scroll, self.v_scroll,
            self.board_frame,
            on_change=self.invalidate
        )

        self.board_frame.grid(row=0, column=0, sticky=tkinter.N + tkinter.E + tkinter.S + tkinter.W)

        self.v_scroll.config(command=lambda *args: self._scroll_move('v', *args))
        self.h_scroll.config(command=lambda *args: self._scroll_move('h', *args))

        self.scrolled_board_frame.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def _scroll_move(self, h_v, *args):
        if args[0] == 'scroll' and len(args) == 3:
            if h_v == 'v':
                sig = -1
            else:
                sig = 1
            _, amount, type_ = args
            if amount == '-1':
                sig *= -1
            if type_ == 'units':
                mag = sig
            elif type_ == 'pages':
                mag = 10 * sig

            if h_v == 'v':
                self.board_scroll(0, mag)
            else:
                self.board_scroll(mag, 0)

        elif args[0] == 'moveto' and len(args) == 2:
            place = float(args[1]) 
            #if 0 <= place and place <= 1:
            if h_v == 'v':
                self.board_move_to('v', place)
            else:
                self.board_move_to('h', place)

    def clear(self):
        self._fn_title(i18n.i18n('Untitled'))
        self.board0.randomize_header()
        self.board0.clear_board()
        self.filename = None
        self.board0_frame.submit_change()
        self.board0_frame.autoadjust()
        self.board1_frame.zoom_copy_from(self.board0_frame)
        self.reset_board1()
        self.invalidate()

    def randomize(self, full_contents='full'):
        self._fn_title(i18n.i18n('Untitled'))
        if self.tools.DefaultBoardSize == 'random':
            self.board0.randomize_full()
        else:
            self.board0.clone_from(self.tools.Board(self.tools.DefaultBoardSize))
            self.board0.randomize_contents()
        self.filename = None
        self.board0_frame.has_changed = False
        self.board0_frame.autoadjust()
        self.board1_frame.zoom_copy_from(self.board0_frame)
        self.reset_board1()
        self.invalidate()

    def open_file(self, fn, fmt='gbb'):
        f = open(fn, 'r')
        try:
            self.board0.load(f, fmt)
        except Exception as e:
            self.show_error(e)
            f.close()
            return False
        f.close()
        self.filename = fn
        self.board0_frame.has_changed = False
        self.board0_frame.autoadjust()
        self.reset_board1()
        self.board1_frame.zoom_copy_from(self.board0_frame)
        self.invalidate()
        self._fn_title(fn)
        return True

    def clone_board0(self, board):
        self._fn_title(i18n.i18n('Untitled'))
        self.board0.clone_from(board)
        self.filename = None
        self.board0_frame.has_changed = True
        self.reset_board1()
        self.invalidate()
        self.show_board0()

    def save_board(self, fn, num, fmt='gbb'):
        f = open(fn, 'w')
        try:
            if num == 0:
                self.board0.dump(f, fmt)
            elif not self.board1.invalid:
                self.board1.dump(f, fmt)
            else:
                raise Exception(i18n.i18n('There is no board to save.'))
        except Exception as e:
            self.show_error(e)
            f.close()
            return
        f.close()
        self.filename = fn
        if num == 0:
            self.board0_frame.has_changed = False
        self._fn_title(fn)

    def prepare_for_run(self):
        if self.filename is None and not self.board0_frame.has_changed:
            self.randomize()
        else:
            self.reset_board1()

    def reset_board1(self):
        self.board1.invalid = False
        self.board1.clone_from(self.board0)

    def invalidate(self):
        self.board1.invalid = True

    def revalidate(self):
        self.board1.invalid = False

    def refresh(self):
        if self.visible_board == 0:
            self.board0_frame.refresh_aspect()
        elif self.visible_board == 1:
            self.board1_frame.refresh_aspect()

    def show_board0(self):
        self.visible_board = 0
        self.close_errors()
        self.board0_frame.pack(expand=tkinter.YES, fill=tkinter.BOTH)
        self.board1_frame.pack_forget()
        self.button0.config(relief=tkinter.SUNKEN)
        self.button1.config(relief=tkinter.RAISED)
        self.board0_frame.refresh_aspect()

    def show_board1(self):
        self.visible_board = 1
        self.close_errors()
        self.board0_frame.pack_forget()
        self.board1_frame.pack(expand=tkinter.YES, fill=tkinter.BOTH)
        self.button0.config(relief=tkinter.RAISED)
        self.button1.config(relief=tkinter.SUNKEN)
        self.board1_frame.refresh_aspect()

    def close_errors(self):
        if self.err_frame:
            self.err_frame.pack_forget()
            self.err_frame = None

    def _prepare_for_error(self):
        self.close_errors()
        self.board0_frame.pack_forget()
        self.board1_frame.pack_forget()
        # do not show anything in the result board after an error
        self.invalidate()
        # no board is selected
        self.button0.config(relief=tkinter.RAISED)
        self.button1.config(relief=tkinter.RAISED)

    def show_error(self, exception):
        self._prepare_for_error()
        self.err_frame = tkinter.Text(self.board_frame, bg='pink', font=self._font)
        self.err_frame.pack(expand=tkinter.YES, fill=tkinter.BOTH)
        self.err_frame.insert('1.0', '%s' % (exception,))
        self.err_frame.config(state=tkinter.DISABLED)

    def show_static_error(self):
        self.invalidate()
        self.refresh()

    def show_dynamic_error(self):
        self._prepare_for_error()
        self.err_frame = Boom(self.board_frame)

    def keypress(self, event):
        if self.visible_board == 0:
            self.board0_frame.keypress(event)
        elif self.visible_board == 1:
            self.board1_frame.keypress(event)

    def keypress_cursor(self, direction, event):
        self.move_head(direction, event)

    def set_font(self, font):
        self._font = font
        self.board0_frame.set_font(font)
        self.board1_frame.set_font(font)
        self.refresh()
        if self.err_frame:
            self.err_frame.config(font=font)

    def move_head(self, direction, event):
        b0 = self.board0_frame
        b1 = self.board1_frame
        if self.visible_board == 1:
            b0, b1 = b1, b0
        b0.keypress_cursor(direction, event)
        b0.center_head()
        b1.zoom_copy_from(b0)
        self.refresh()

    def grandmove(self, kw):
        b0 = self.board0_frame
        b1 = self.board1_frame
        if self.visible_board == 1:
            b0, b1 = b1, b0
        b0.grandmove(kw)
        b0.center_head()
        b1.zoom_copy_from(b0)
        self.refresh()

    def board_zoom_out(self, *args):
        self.board0_frame.zoom_out()
        self.board1_frame.zoom_out()
        self.refresh()

    def board_zoom_in(self, *args):
        self.board0_frame.zoom_in()
        self.board1_frame.zoom_in()
        self.refresh()

    def board_scroll(self, dx, dy):
        self.board0_frame.scroll(dx, dy)
        self.board1_frame.zoom_copy_from(self.board0_frame)
        self.refresh()

    def board_move_to(self, orientation, place):
        self.board0_frame.move_to(orientation, place)
        self.board1_frame.zoom_copy_from(self.board0_frame)
        self.refresh()

# Class to draw the boom message

import random

class Boom(tkinter.Canvas):
    def __init__(self, root, *args, **kwargs):
        tkinter.Canvas.__init__(self, root, bg='black', *args, **kwargs)
        self.pack(expand=tkinter.YES, fill=tkinter.BOTH)
        w, h = root.winfo_width(), root.winfo_height()
        dx = w // 11
        dy = h // 11
        for i, col in zip(range(6), ['yellow', 'orange', 'red']):
            self.draw_zig_zag_box([i * dx, i * dy, w - i * dx, h - i * dy], col, i)
        rhs = [random.randint(0, 40) - 20 for i in range(4)]
        for let, delta, rh in zip('BOOM', range(4), rhs):
            for siz, col in [(110, 'black'), (130, 'black'), (120, 'white')]:
                if col == 'black':
                    dhs = range(-5, 5)
                else:
                    dhs = [0]
                for dh in dhs:
                    self.create_text((delta + 1) * w // 5, (delta + 1) * h // 5 + rh + dh, text=let,
                                                      font=('helvetica', siz), fill=col)

    def draw_zig_zag_box(self, bbox, color, var):
        x0, y0, x1, y1 = bbox
        dx = (x1 - x0) // 5
        dy = (y1 - y0) // 5
        def rdx(): return random.randint(0, 2 * dx) - dx
        def rdy(): return random.randint(0, 2 * dy) - dy
        verts = []
        N = 100
        for i in range(N): verts.append((x0 + i * float(x1 - x0) / N, y0))
        for i in range(N): verts.append((x1, y0 + i * float(y1 - y0) / N))
        for i in range(N): verts.append((x1 - i * float(x1 - x0) / N, y1))
        for i in range(N): verts.append((x0, y1 - i * float(y1 - y0) / N))
        verts = [(int(x[0] + rdx()), int(x[1] + rdy())) for x in verts]
        self.create_polygon(verts, fill=color, outline='black', width=5)
  
