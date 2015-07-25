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


import pygobstoneslang.lang.gbs_lint as gbs_lint
import pygobstoneslang.lang.gbs_liveness as gbs_liveness
import pygobstoneslang.lang.gbs_infer as gbs_infer
import pygobstoneslang.lang.gbs_compiler as gbs_compiler
import pygobstoneslang.lang.gbs_builtins as gbs_builtins
import pygobstoneslang.lang.gbs_vm as gbs_vm
import pygobstoneslang.lang.gbs_board as gbs_board
import pygobstoneslang.lang.board.formats as formats
import i18n as i18n
import utils

class Tools():
    pass

tools = Tools()
tools.BoardViewerGeometry = "480x480"
tools.DefaultBoardSize = 'random'
tools.lint = gbs_lint.lint
tools.check_live_variables = gbs_liveness.check_live_variables
tools.typecheck = gbs_infer.typecheck
tools.compile = gbs_compiler.compile_program
tools.interp = gbs_vm.interp
tools.GbsVmInterpreter = gbs_vm.GbsVmInterpreter
#import jit.gbs_jit
#tools.GbsVmInterpreter = jit.gbs_jit.JitInterpreter
tools.Board = gbs_board.Board
tools.board_format = formats.AvailableFormats['gbb']()
tools.builtins = gbs_builtins
