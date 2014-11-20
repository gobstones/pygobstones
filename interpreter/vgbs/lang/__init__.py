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

import os

dirname = os.path.dirname(__file__)
GbsGrammarFile = os.path.join(dirname, 'gbs_grammar.bnf')
GbsMacrosDir = os.path.join(dirname, 'macros')

import common.i18n as i18n

import lang.gbs_io
import lang.gbs_parser
import lang.gbs_mexpl
import lang.gbs_lint
import lang.gbs_liveness
import lang.gbs_vm
import lang.jit.gbs_jit
import lang.gbs_pprint
import lang.gbs_infer
import lang.gbs_compiler
import lang.gbs_board

""" Gobstones API classes """

class ExecutionAPI(lang.gbs_io.InteractiveApi):
    def log(self, msg):
        pass
    
class DefaultExecutionAPI(lang.gbs_vm.NullInteractiveAPI, ExecutionAPI):
    pass

class GobstonesOptions(object):
    LINT_MODES = ['lax', 'strict']
    def __init__(self, lint_mode="lax", check_liveness=False, check_types=False, jit=False):
        self.lint_mode = lint_mode
        self.check_liveness = check_liveness
        self.check_types = check_types
        self.jit = jit
    
class GobstonesRun(object):
    def __init__(self):
        self.initialize()
    def initialize(self, tree=None, compiled_program=None, initial_board=None, final_board=None, runnable=None, result=None):
        self.initial_board = initial_board
        self.final_board = final_board
        self.tree = tree
        self.compiled_program = compiled_program
        self.runnable = runnable
        self.result = result
        return self
    def merge(self, other):
        return GobstonesRun().initialize(self.tree or other.tree, 
                            self.compiled_program or other.compiled_program,
                            self.initial_board or other.initial_board, 
                            self.final_board or other.final_board,
                            self.runnable or other.runnable, 
                            self.result or other.result)
        
class Gobstones(object):
    def __init__(self, options=GobstonesOptions(), api=DefaultExecutionAPI()):
        self.api = api
        self.options = options
        # Compiler pipeline methods
        self.explode_macros = lang.gbs_mexpl.mexpl
        self.parse = lang.gbs_parser.parse_string_try_prelude
        self.lint = lang.gbs_lint.lint
        self.check_live_variables = lang.gbs_liveness.check_live_variables
        self.typecheck = lang.gbs_infer.typecheck
        self.compile_program = lang.gbs_compiler.compile_program
        if self.options.jit:
            self.make_runnable = lang.jit.gbs_jit.JitCompiledRunnable            
        else:
            self.make_runnable = lang.gbs_vm.VmCompiledRunnable
    @classmethod
    def random_board(cls, size=None):
        if size is None:
            board = lang.gbs_board.Board()
            board.randomize_full()
        else:
            board = lang.gbs_board.Board(size)
            board.randomize_contents()
        return board
    def check(self, tree):
        # Check semantics
        self.api.log(i18n.i18n('Performing semantic checks.'))
        self.lint(tree, strictness=self.options.lint_mode)
        # Check liveness
        if self.options.check_liveness:
            self.check_live_variables(tree)
        # Check types
        if self.options.check_types:
            self.typecheck(tree)
    def compile(self, filename, program_text):
        # Parse gobstones script
        self.api.log(i18n.i18n('Parsing.'))
        tree = self.parse(program_text, filename)            
        assert tree
        # Explode macros
        self.api.log(i18n.i18n('Exploding program macros.'))            
        self.explode_macros(tree)
        # Check semantics, liveness and types
        self.check(tree)
        # Compile program
        self.api.log(i18n.i18n('Compiling.'))
        compiled_program = self.compile_program(tree)
        return GobstonesRun().initialize(tree, compiled_program)
    def run_object_code(self, compiled_program, initial_board):
        # Make runnable            
        runnable = self.make_runnable(compiled_program)
        # Run
        self.api.log(i18n.i18n('Starting program execution.'))
        final_board = initial_board.clone()
        result = runnable.run(final_board, self.api)
        gbs_run = GobstonesRun().initialize(None, compiled_program, initial_board, final_board, runnable, result)
        return gbs_run 
    def run(self, filename, program_text, initial_board):
        gbs_run = self.compile(filename, program_text)
        return gbs_run.merge(self.run_object_code(gbs_run.compiled_program, initial_board))


""" Utilities """

GbsVmInterpreter = lang.gbs_vm.GbsVmInterpreter
Board = lang.gbs_board.Board
pretty_print = lang.gbs_pprint.pretty_print