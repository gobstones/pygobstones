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
import lang.gbs_parser

class GbsModuleHandler(object):

    def __init__(self, source_filename, toplevel_filename=None):
        self._source_filename = source_filename
        self._parse_trees = {}
        self._type_contexts = {}
        self._compiled_code = {}
        if toplevel_filename is None:
            self._toplevel_filename = self._source_filename
        else:
            self._toplevel_filename = toplevel_filename

    def filename_for(self, module_name):
        return os.path.join(os.path.dirname(self._source_filename), module_name + '.gbs')
  
    def module_exists(self, module_name):
        return os.path.exists(self.filename_for(module_name))

    def parse_tree(self, module_name):
        if module_name not in self._parse_trees:
            self._parse_trees[module_name] = lang.gbs_parser.parse_file(
                self.filename_for(module_name)
            )
        return self._parse_trees[module_name]

    def parse_trees(self):
        return self._parse_trees.items()

    def set_type_context(self, mdl_name, ctx):
        self._type_contexts[mdl_name] = ctx

    def set_compiled_code(self, mdl_name, compiled_code):
        self._compiled_code[mdl_name] = compiled_code

    def type_of(self, mdl_name, rtn_name):
        return self._type_contexts[mdl_name][rtn_name]

    def compiled_code_for(self, mdl_name):
        return self._compiled_code[mdl_name]

    def reraise(self, new_class, old_exception, new_msg, new_area):
        if self._source_filename == self._toplevel_filename:
            raise new_class(
                new_msg + '\n' + common.utils.indent(
                    '%s\n%s' % (old_exception.area, old_exception.msg)
                ),
                new_area
            )
        else:
            raise old_exception

