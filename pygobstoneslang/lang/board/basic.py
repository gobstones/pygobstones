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
import pygobstoneslang.lang.gbs_board as gbs_board

class BoardFormat(object):
    def to_string(self, board, **kwargs):
        out = utils.StringIO()
        self.dump(board, out, **kwargs)
        res = out.getvalue()
        out.close()
        return res
    def from_string(self, s, board=None):
        if board is None:
            board = gbs_board.Board()
        f = utils.StringIO(s)
        self.load(board, f)
        f.close()
        return board
