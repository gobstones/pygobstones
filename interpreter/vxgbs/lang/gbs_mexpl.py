#
# Copyright (C) 2013 Pablo Barenbaum <foones@gmail.com>, Ary Pablo Batista <arypbatista@gmail.com>
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

import functools
import os
import lang.gbs_def_helper as defhelper
import lang

#### Macro exploding of Gobstones programs.

class GbsMacroExploder(object):
    def _load_implementation(self, implementation_filename, reserved_token_names=None):
        """ Parses a file with the required implementation and replaces the
        reserved token names with user-innaccesible names """
        implementation_program = lang.gbs_parser.parse_file(os.path.join(lang.GbsMacrosDir, implementation_filename))
        for token_name in reserved_token_names:
            defhelper.recursive_replace_token(implementation_program, token_name, "_" + token_name)
        return implementation_program
    
    def explode(self, program_tree):
        entrypoint_tree = defhelper.find_def(program_tree.children[2], defhelper.is_entrypoint_def)
        self.explicit_board = not entrypoint_tree.annotations["varProc"] is None
        """ Explodes program macros """
        self._explode_interactive(program_tree)
    
    def _explode_interactive(self, program_tree):
        """ Replaces interactive macro with it's implementation in the program tree """
        interactive = defhelper.find_def(program_tree.children[2], defhelper.is_interactive_def)
        if interactive != None:
            if self.explicit_board:
                macro_filename = "interactive_program.gbs"
            else:
                macro_filename = "interactive_program_implicit.gbs"
            implementation_program = self._load_implementation(macro_filename, ["lastKey", "read", "Show"])
            interactive_impl = defhelper.find_def(implementation_program.children[2], defhelper.is_entrypoint_def)
            interactive_impl_case = defhelper.recursive_find_node(interactive_impl, functools.partial(defhelper.is_node, 'case'))
            interactive_impl_case.children = [interactive_impl_case.children[0], interactive_impl_case.children[1]]
            interactive_impl_case.children.append(defhelper.get_def_body(interactive))
            defhelper.set_def_body(interactive, defhelper.get_def_body(interactive_impl))
            defhelper.set_def_token_name(interactive, 'program')
  
def mexpl(tree):
    GbsMacroExploder().explode(tree);