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


import lang.gbs_parser
import lang.gbs_mexpl
import lang.gbs_lint
import lang.gbs_liveness
import lang.gbs_infer
import lang.gbs_compiler
import lang.gbs_builtins
import lang.gbs_vm
import lang.gbs_board
import lang.board.formats
import common.i18n as i18n
import common.utils

class Tools():
    pass

tools = Tools()
tools.BoardViewerGeometry = "480x480"
tools.DefaultBoardSize = 'random'
tools.tokenize = lang.gbs_parser.token_stream
tools.parse_file = lang.gbs_parser.parse_file
tools.parse_string_try_prelude = lang.gbs_parser.parse_string_try_prelude
tools.mexpl = lang.gbs_mexpl.mexpl
tools.lint = lang.gbs_lint.lint
tools.check_live_variables = lang.gbs_liveness.check_live_variables
tools.typecheck = lang.gbs_infer.typecheck
tools.compile = lang.gbs_compiler.compile_program
tools.interp = lang.gbs_vm.interp
tools.GbsVmInterpreter = lang.gbs_vm.GbsVmInterpreter
#import lang.jit.gbs_jit
#tools.GbsVmInterpreter = lang.jit.gbs_jit.JitInterpreter
tools.Board = lang.gbs_board.Board
tools.board_format = lang.board.formats.AvailableFormats['gbb']()
tools.builtins = lang.gbs_builtins

