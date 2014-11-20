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

"""Representation of Gobstones boards."""

import random

import common.utils
import common.i18n as i18n
import lang.board.formats
import lang.board.basic
import lang.gbs_builtins

class SelfDestructionException(Exception):
    """Base exception for board-related errors, such as moving the head
    past the board limits, or attempting to take stones when there are
    no stones."""
    pass

def stone_dist():
    """Return a random number of stones, for populating random boards.
    The distribution is taken from the original Fidel's Gobstones/Haskell
    implementation."""
    num = random.randint(0, 999)
    dist = [(650, 0),
            (800, 1),
            (900, 2), 
            (950, 3),
            (970, 4)]
    for key, val in dist:
        if num < key:
            return val
    return num - 970 + 4

def rand_side():
    """Return a random length for the board sides."""
    side = random.gauss(9, 3)
    side = max(1, min(side, 200))
    return int(side)

class Cell(object):
    "Represents a Gobstones board cell."

    def __init__(self, parent=None):
        self.stones = {}
        self.parent = parent

    def randomize(self):
        """Randomizes the cell, filling it with a random number of
        stones for each color."""
        for i in range(lang.gbs_builtins.NUM_COLORS):
            self.stones[i] = self.stones.get(i, 0) + stone_dist()

    def put(self, coli, count=1):
        """Add `count` stones of the given color index `coli`.
        Note that `coli` is a color index (ord), not an instance of
        lang.gbs_builtins.Color."""
        self.stones[coli] = self.stones.get(coli, 0) + count

    def take(self, coli, count=1):
        """Takes a stone of the given color index `coli`. Note
        that `coli` is a color index (ord), not an instance of
        lang.gbs_builtins.Color. Raise a SelfDestructionException if
        there are no stones of the given color."""
        cnt = self.stones.get(coli, 0)
        if cnt >= count:
            self.stones[coli] = cnt - count
        else:
            if self.parent is None:
                raise SelfDestructionException(i18n.i18n('Cannot take stones'))
            else:
                self.clone_from(self.parent)
                self.parent = None
                cnt = self.stones.get(coli, 0)
                self.stones[coli] = cnt - count

    def set_num_stones(self, coli, count):
        """Set the number of stones of the given color index `coli`
        to `count`. Note that `coli` is a color index (ord), not an instance of
        lang.gbs_builtins.Color."""
        self.stones[coli] = count

    def num_stones(self, coli):
        """Return the number of stones of the given color index `coli`.
        Note that `coli` is a color index (ord), not an instance of
        lang.gbs_builtins.Color."""
        if self.parent is None:
            return self.stones.get(coli, 0)
        else:
            return self.stones.get(coli, 0) + self.parent.num_stones(coli)

    def num_total_stones(self):
        total = 0
        for ci, cn in self.all_stones_count():
            total += cn
        return total

    def clone(self):
        "Return a new cell with the same contents as this one."
        copy = Cell()
        copy.clone_from(self)
        return copy

    def all_stones_count(self):
        """Return a list of tuples (colori, count) describing the amount
        of stones for each color."""
        if self.parent is None:
            return self.stones.items()
        else:
            sum = {}
            for col, count in self.parent.all_stones_count():
                sum[col] = count
            for col, count in self.stones.items():
                sum[col] = sum.get(col,0) + count
            return sum.items()

    def clone_from(self, other):
        """Set the contents of this cell to be equal to the contents of
        the other cell."""
        for col, count in other.all_stones_count():
            self.set_num_stones(col, count)

    def equal_contents(self, other):
        """Return a boolean indicating if this cell has the same contents
        as the other cell."""
        for col, count in self.stones.items():
            if other.num_stones(col) != count:
                return False
        for col, count in other.stones.items():
            if self.num_stones(col) != count:
                return False
        return True

    #### Human-friendly API

    def __repr__(self):
        """Shows the contents of the cell, as a 1x1 board."""
        board = Board((1, 1))
        board[0, 0].clone_from(self)
        return repr(board)

    def __getitem__(self, color_name):
        """Return the number of stones of the given color. For instance:
        >>> cell['Rojo']
        returns the number of red stones in the current cell
        """
        dic = lang.gbs_builtins.COLOR_NAME_TO_INDEX_DICT
        coli = dic[color_name]
        return self.num_stones(coli)

    def __setitem__(self, color_name, count):
        """Set the number of stones of the given color. For instance:
        >>> cell['Rojo'] = 3
        sets the number of red stones in the current cell to 3
        """
        dic = lang.gbs_builtins.COLOR_NAME_TO_INDEX_DICT
        coli = dic[color_name]
        self.set_num_stones(coli, count)

    def init_color_properties(cls):
        """Helper method to initialize the cell properties,
        adding class level getters/setters, so that the contents of
        the cell can be modified by means of attributes:
        >>> cell = Cell()
        >>> cell.Rojo = 1
        >>> cell.Rojo
        1
        """
        def init_col(colname, coli):
            "Initialize the accesors for the given color index."

            def pget(self):
                "Color property getter."
                return self.num_stones(coli)

            def pset(self, num):
                "Color property setter."
                self.set_num_stones(coli, num)

            prop = property(fget=pget, fset=pset)
            setattr(Cell, colname, prop)

        for colname, coli in lang.gbs_builtins.COLOR_NAME_TO_INDEX_DICT.items():
            if not isinstance(colname, str):
                continue
            init_col(colname, coli)

    init_color_properties = classmethod(init_color_properties)

## Initialize color properties for cells
Cell.init_color_properties()
##

class Board(object):
    """Represents a Gobstones board."""
    MAX_RECURSION_DEPTH = 10

    def __init__(self, size=(1,1), parent=None):
        self.size = size
        self.parent = parent
        self.changed = False
        if self.parent is None:
            self.recursion_depth = 0
        else:
            self.recursion_depth = self.parent.recursion_depth + 1
        self.head = (0, 0)
        self.cells = None
        self._clear_board()
        self.invalid = False

    def resize(self, width, height):
        "Change the size of the board to width x height."
        self.clone_from(Board((width, height)))

    def go_to_origin(self):
        "Move the head to the origin (0, 0)."
        head_pos = self.head
        self.head = (0, 0)

    def go_to_boundary(self, direction):
        "Move the head to specified boundary."
        head_pos = self.head
        width, height = self.size
        y, x = self.head
        delta_y, delta_x = direction.delta()        
        
        if delta_y > 0:
            y = height-1
        elif delta_y < 0:
            y = 0
        
        if delta_x > 0:
            x = width-1
        elif delta_x < 0:
            x = 0
        
        self.head = y, x

    def _clear_board(self):
        "Clear the contents of this board, parent remains unmodified."
        width, height = self.size
        if self.parent is None:
            self.cells = [[Cell() for _ in range(width)] for _ in range(height)]
        else:
            self.cells = [[Cell(self.parent.cells[y][x]) for x in range(width)] for y in range(height)]

    def clear_board(self):
        """Clear the contents of the board"""
        self._clear_board()
        
    def hard_clear_board(self):
        "Fully clear the contents of the board."
        width, height = self.size
        self.parent = None
        self.cells = [[Cell() for _ in range(width)] for _ in range(height)]

    def put_stone(self, color, count=1):
        """Put a stone of the given color in the current cell."""
        y, x = self.head
        self.cells[y][x].put(color.ord(), count)
        self.changed = True

    def take_stone(self, color, count=1):
        """Take a stone of the given color from the current cell."""
        y, x = self.head
        self.cells[y][x].take(color.ord(), count)
        self.changed = True

    def move(self, direction, count=1):
        """Move the head to the given direction.
        Raise a SelfDestructionException if the head falls out of the
        board limits."""
        delta_y, delta_x = direction.delta()
        delta_y *= count
        delta_x *= count
        width, height = self.size
        y, x = self.head
        x += delta_x
        y += delta_y
        if 0 <= y and y < height and 0 <= x and x < width:
            self.head = y, x
        else:
            raise SelfDestructionException(i18n.i18n('Cannot move'))

    def num_stones(self, color):
        """Return the number of stones of the given color in the current
        cell."""
        y, x = self.head
        return self.cells[y][x].num_stones(color.ord())

    def exist_stones(self, color):
        """Return True iff there are stones of the given color in the
        current cell."""
        y, x = self.head
        return self.cells[y][x].num_stones(color.ord()) > 0

    def can_move(self, direction, count=1):
        """Return True iff the head can move in the given direction
        without falling off the board."""
        delta_y, delta_x = direction.delta()
        delta_y *= count
        delta_x *= count
        width, height = self.size
        y, x = self.head
        x += delta_x
        y += delta_y
        return 0 <= y and y < height and 0 <= x and x < width

    def randomize_header(self):
        """Move the head to a random position inside the board."""
        width, height = self.size
        self.head = (
            random.randint(0, height - 1),
            random.randint(0, width - 1))

    def randomize_full(self):
        """Randomize the board size, contents and head position."""
        self.size = rand_side(), rand_side()
        self.randomize_contents()

    def randomize_contents(self):
        """Randomize the board contents and head position.
        Keep the original size."""
        self._clear_board()
        width, height = self.size
        self.randomize_header()
        num_nonempty = random.randint(0, height * width)
        for _ in range(num_nonempty):
            i = random.randint(0, width - 1)
            j = random.randint(0, height - 1)
            self.cells[j][i].randomize()

    def randomize(self):
        "Randomize the board."
        self.randomize_contents()

    def dump(self, f, fmt=lang.board.formats.DefaultFormat, **kwargs):
        "Dump the board to the file handle `f` in the given format."
        if fmt in lang.board.formats.AvailableFormats:
            lang.board.formats.AvailableFormats[fmt]().dump(self, f, **kwargs)
        else:
            raise lang.board.basic.BoardFormatException(
                'Board file format unrecognized: %s' % (fmt,))

    def load(self, f, fmt=lang.board.formats.DefaultFormat):
        "Load the board from the file handle `f` in the given format."
        if fmt in lang.board.formats.AvailableFormats:
            lang.board.formats.AvailableFormats[fmt]().load(self, f)
        else:
            raise lang.board.basic.BoardFormatException(
                'Board file format unrecognized: %s' % (fmt,))

    def clone(self):
        "Return a copy of this board."
        if self.recursion_depth == Board.MAX_RECURSION_DEPTH:
            copy = Board(self.size)
            copy.clone_from(self)
            return copy
        else:
            if self.changed or self.parent is None:
                parent = Board(self.size)
                parent.clone_from(self)
                self.parent = parent
                self.clear_board()
            else:
                parent = self.parent
            
            other_child = Board(self.size, parent)
            other_child.head = self.head
            return other_child
            
    def clone_from(self, other):
        """Set the contents of this board to the contents of the other board."""
        self._restore_from(other)

    def _restore_from(self, other):
        "Set the contents of this board to the contents of the other board."
        self.size = other.size
        self._clear_board()
        assert self.size == other.size
        width, height = other.size
        self.head = other.head
        for x in range(width):
            for y in range(height):
                self.cells[y][x] = other.cells[y][x].clone()

    def __repr__(self):
        gbt_format = lang.board.formats.AvailableFormats['gbt']()
        out = gbt_format.numbered_contents(self)
        return '\n'.join(out)

    def equal_contents(self, other):
        """Return True iff the contents of the board are equal to the
        contents of the other board."""
        if self.size != other.size:
            return False
        width, height = self.size
        for x in range(width):
            for y in range(height):
                if not self.cells[y][x].equal_contents(other.cells[y][x]):
                    return False
        return True

    #### Human-friendly API

    def __getitem__(self, xy):
        x, y = xy
        return self.cells[y][x]

    def goto(self, x, y):
        "Move the head to the position (x, y)."
        width, height = self.size
        assert 0 <= x and x < width
        assert 0 <= y and y < height
        self.head = y, x

def load_board_from(filename):
    """Load the board from the given filename, attempting to
    recognize the format by the file extension."""
    fmt = lang.board.formats.format_for(filename)
    board = Board((1, 1))
    f = open(filename, 'r')
    board.load(f, fmt)
    f.close()
    return board

def dump_board_to(board, filename, style='verbose'):
    """Dump the board into the given filename, attempting to
    recognize the format by the file extension."""
    fmt = lang.board.formats.format_for(filename)
    f = open(filename, 'w')
    board.dump(f, fmt, style=style)
    f.close()

