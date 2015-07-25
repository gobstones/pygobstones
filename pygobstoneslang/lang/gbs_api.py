#
# Copyright (C) 2011-2015 Pablo Barenbaum <foones@gmail.com>,
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

from grammar import GbsGrammarFile, XGbsGrammarFile
import gbs_io

""" Gobstones API classes """

class ExecutionAPI(gbs_io.InteractiveApi):
    def log(self, msg):
        pass

class GobstonesOptions(object):
    class LangVersion:
        Gobstones = "Gobstones3.0"
        XGobstones = "XGobstones"
    LINT_MODES = ['lax', 'strict']
    def __init__(self, lang_version=LangVersion.Gobstones, lint_mode="lax", check_liveness=False, check_types=False, jit=False, allow_recursion=False):
        self.lint_mode = lint_mode
        self.check_liveness = check_liveness
        self.check_types = check_types
        self.jit = jit        
        self.lang_version = lang_version
        self.allow_recursion = allow_recursion

    def get_lang_grammar(self):
        if self.lang_version == self.LangVersion.Gobstones:
            return GbsGrammarFile
        else:
            return XGbsGrammarFile

class GobstonesRun(object):
    def __init__(self):
        self.initialize()

    def initialize(self, tree=None, compiled_program=None, initial_board=None, final_board=None, runnable=None, result=[]):
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

    def json(self):
        return json.dumps({
            "initial_board" : JsonBoardFormat().dump_to_dict(self.initial_board),
            "final_board": JsonBoardFormat().dump_to_dict(self.final_board),
            "result" : self.result,
            "compiled_program": repr(self.compiled_program),
        })
